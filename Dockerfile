# Central server (device registry) as a container image. Day 4.
# Build:  docker build -t device-registry:0.2.0 .
# Run:    docker run -d --name registry -p 8000:8000 -e DATA_DIR=/data -v /srv/registry-data:/data device-registry:0.2.0
FROM python:3.12-slim

# No .pyc files in the image, log lines appear at once in `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first: this layer is reused as long as requirements.txt does not change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY simulator ./simulator

# Run as an ordinary user, not root. UID 10001 must be able to write the mounted data directory.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin registry \
    && mkdir /data && chown registry /data
USER registry

ENV DATA_DIR=/data
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
