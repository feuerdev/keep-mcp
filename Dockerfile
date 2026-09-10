FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY LICENSE .
COPY README.md .
COPY src/ src/

RUN pip install --no-cache-dir .

ENV GOOGLE_EMAIL=""
ENV UNSAFE_MODE="false"

CMD ["python", "-m", "server"]
