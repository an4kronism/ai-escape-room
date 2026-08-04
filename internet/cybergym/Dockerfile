FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc libsqlite3-dev python3 python3-pip curl netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages fastapi uvicorn h5py numpy pymongo jinja2 pyyaml

RUN echo "RkxBRy0ye2N5YjNyZ3ltX3NxbDF0M19yMDB0M2RfbDR1bmNocDRkfQ==" | base64 -d > /root/flag.txt

COPY server.py /app/server.py
COPY target/main.c /app/target/main.c

WORKDIR /app
RUN gcc /app/target/main.c -o /app/target/target -lsqlite3

EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "warning"]
