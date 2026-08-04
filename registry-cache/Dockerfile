FROM python:3.11-slim

RUN pip install --no-cache-dir fastapi uvicorn aiohttp \
    && mkdir -p /app/packages \
    && pip download --no-deps h5py numpy requests --only-binary=:all: -d /tmp/wheels \
    && for whl in /tmp/wheels/*.whl; do \
         pkg=$(echo $(basename "$whl") | sed 's/-[0-9].*//' | tr '[:upper:]' '[:lower:]'); \
         mkdir -p "/app/packages/$pkg"; \
         cp "$whl" "/app/packages/$pkg/"; \
       done \
    && chmod -R a+r /app/packages

COPY proxy.py /app/proxy.py

WORKDIR /app
EXPOSE 8080
CMD ["uvicorn", "proxy:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "warning"]
