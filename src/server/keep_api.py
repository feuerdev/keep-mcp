import os
from functools import wraps
from threading import RLock

import gkeepapi
import requests
from dotenv import load_dotenv

KEEP_MCP_LABEL = "keep-mcp"

_keep_client = None
_client_lock = RLock()


def credential_configuration():
    """Read local configuration without connecting or returning credential values."""
    load_dotenv()
    missing = [name for name in ('GOOGLE_EMAIL', 'GOOGLE_MASTER_TOKEN')
               if not (os.getenv(name) or '').strip()]
    return {'missing': missing, 'write_mode': 'unsafe' if is_unsafe_mode() else 'label_guarded'}


def keep_operation(func):
    """Serialize access to the shared Keep tree, including mutation and sync."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        global _keep_client
        with _client_lock:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.JSONDecodeError:
                _keep_client = None
                raise RuntimeError(
                    "Google Keep returned a non-JSON response. Check network/API access; "
                    "no operation was automatically retried."
                ) from None
            except requests.RequestException:
                _keep_client = None
                raise requests.ConnectionError(
                    "Google Keep network request failed. Check connectivity, then read "
                    "the authoritative note state before retrying a write; its remote outcome may be unknown."
                ) from None
            except gkeepapi.exception.LoginException:
                _keep_client = None
                raise RuntimeError(
                    "Google Keep login failed. Verify GOOGLE_EMAIL and GOOGLE_MASTER_TOKEN "
                    "locally using the documented authentication flow."
                ) from None
            except (gkeepapi.exception.APIException, gkeepapi.exception.SyncException):
                _keep_client = None
                raise RuntimeError(
                    "Google Keep sync/API failed. Check account and API access, then read "
                    "the authoritative note state before retrying a write; its remote outcome may be unknown."
                ) from None
            except Exception:
                # A failed operation can leave unsaved or prematurely cleaned
                # mutations in memory. Reload remote state on the next call.
                _keep_client = None
                raise
    return wrapped


@keep_operation
def get_client():
    """
    Get a freshly synced Google Keep client.
    Reuse the authenticated client until an operation fails.
    
    Returns:
        gkeepapi.Keep: Authenticated Keep client
    """
    global _keep_client
    
    if _keep_client is not None:
        _keep_client.sync()
        return _keep_client
    
    configuration = credential_configuration()
    if configuration['missing']:
        raise ValueError("Missing Google Keep credentials: " + ', '.join(configuration['missing']))

    keep = gkeepapi.Keep()
    keep.authenticate(os.getenv('GOOGLE_EMAIL'), os.getenv('GOOGLE_MASTER_TOKEN'))

    # Store the client for reuse
    _keep_client = keep
    
    return keep

def serialize_label(label):
    return {'id': label.id, 'name': label.name}


def serialize_list_item(item):
    return {
        'id': item.id,
        'text': item.text,
        'checked': item.checked,
        'parent_item_id': item.parent_item.id if item.parent_item else None,
    }


def serialize_note(note):
    """
    Serialize a Google Keep note into a dictionary.
    
    Args:
        note: A Google Keep note object
        
    Returns:
        dict: A dictionary containing the note's id, title, text, pinned status, color and labels
    """
    timestamps = getattr(note, 'timestamps', None)
    created = getattr(timestamps, 'created', None)
    updated = getattr(timestamps, 'updated', None)

    payload = {
        'id': note.id,
        'title': note.title,
        'text': note.text,
        'type': note.type.value,
        'pinned': note.pinned,
        'archived': note.archived,
        'trashed': note.trashed,
        'color': note.color.value if note.color else None,
        'created': created.isoformat() if created else None,
        'updated': updated.isoformat() if updated else None,
        'labels': [serialize_label(label) for label in note.labels.all()],
        'collaborators': list(note.collaborators.all()),
    }

    if hasattr(note, 'items'):
        payload['items'] = [serialize_list_item(item) for item in note.items]

    payload['media'] = [
        {
            'blob_id': blob.id,
            'type': blob.blob.type.value if blob.blob and blob.blob.type else None,
        }
        for blob in note.blobs
    ]

    return payload

_MEDIA_EXTENSIONS = {
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'audio/3gpp': '.3gp',
    'audio/amr': '.amr',
    'audio/mpeg': '.mp3',
}


def media_extension(content_type):
    """
    Map a media response Content-Type to a file extension.

    Args:
        content_type: The Content-Type header value (may carry parameters)

    Returns:
        str: A dotted extension, '.bin' when the type is unknown or missing
    """
    if not content_type:
        return '.bin'
    return _MEDIA_EXTENSIONS.get(content_type.split(';')[0].strip().lower(), '.bin')


def fetch_blob_bytes(keep, blob):
    """
    Download a media blob through the authenticated Keep session.

    The links returned by getMediaLink() require Google authentication and
    answer 403 to plain HTTP clients, so the download rides the same session
    and credentials the server is already authenticated with.

    Args:
        keep: Authenticated gkeepapi.Keep client
        blob: A note media blob node

    Returns:
        tuple: (bytes, content_type) of the downloaded media
    """
    url = keep.getMediaLink(blob)
    media_api = keep._media_api
    response = media_api._send(url=url, method='GET')
    if response.status_code in (400, 401, 403):
        # Some media endpoints reject the OAuth header; retry bare on the same session.
        response = media_api._session.get(url)
    response.raise_for_status()
    return response.content, response.headers.get('Content-Type')


def is_unsafe_mode() -> bool:
    return os.getenv('UNSAFE_MODE', '').lower() == 'true'


def can_modify_note(note):
    """
    Check if a note can be modified based on label and environment settings.

    Args:
        note: A Google Keep note object

    Returns:
        bool: True if the note can be modified, False otherwise
    """
    return is_unsafe_mode() or has_keep_mcp_label(note)


def has_keep_mcp_label(note):
    """
    Check if a note has the keep-mcp label.

    Args:
        note: A Google Keep note object

    Returns:
        bool: True if the note has the keep-mcp label, False otherwise
    """
    return any(label.name == KEEP_MCP_LABEL for label in note.labels.all())
