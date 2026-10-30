FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    TRANSPORT=sse

# Copy metadata and source files
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Install dependencies and the keep-mcp package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

EXPOSE 8080

CMD ["python", "-m", "server.web"]
