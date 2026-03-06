import gkeepapi
import os
import requests
from dotenv import load_dotenv

KEEP_MCP_LABEL = "keep-mcp"

_keep_client = None


def _read_secret(env_var: str, secret_name: str) -> str | None:
    secret_path = f"/run/secrets/{secret_name}"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    return os.getenv(env_var)

def get_client():
    """
    Get or initialize the Google Keep client.
    This ensures we only authenticate once and reuse the client.
    
    Returns:
        gkeepapi.Keep: Authenticated Keep client
    """
    global _keep_client
    
    if _keep_client is not None:
        return _keep_client
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables or secret files
    email = os.getenv('GOOGLE_EMAIL')
    master_token = _read_secret('GOOGLE_MASTER_TOKEN', 'google_master_token')
    
    if not email or not master_token:
        raise ValueError("Missing Google Keep credentials. Please set GOOGLE_EMAIL and GOOGLE_MASTER_TOKEN environment variables.")
    
    # Initialize the Keep API
    keep = gkeepapi.Keep()
    
    # Authenticate
    try:
        keep.authenticate(email, master_token)
    except requests.exceptions.JSONDecodeError as exc:
        raise RuntimeError(
            "Google Keep API returned a non-JSON response during authentication. "
            "This usually means the unofficial Keep API (notes/v1) is inaccessible "
            "from this environment (HTTP 403/4xx). "
            "Check that your GOOGLE_MASTER_TOKEN is valid and that the Keep API "
            "is reachable from this network."
        ) from exc
    except gkeepapi.exception.LoginException as exc:
        raise RuntimeError(
            f"Google Keep login failed: {exc}. "
            "Verify that GOOGLE_EMAIL and GOOGLE_MASTER_TOKEN are correct."
        ) from exc
    
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
    payload = {
        'id': note.id,
        'title': note.title,
        'text': note.text,
        'type': note.type.value,
        'pinned': note.pinned,
        'archived': note.archived,
        'trashed': note.trashed,
        'color': note.color.value if note.color else None,
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
