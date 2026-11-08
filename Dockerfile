FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN useradd -m -u 1000 appuser

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

USER appuser

EXPOSE 8000

CMD ["keep-mcp", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
