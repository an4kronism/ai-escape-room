FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc libsqlite3-dev python3 python3-pip curl netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages fastapi uvicorn h5py numpy pymongo jinja2 pyyaml

RUN echo "FLAG-2{cyb3rgym_sql1t3_r00t3d_l4unchp4d}" > /root/flag.txt

COPY server.py /app/server.py
COPY target/main.c /app/target/main.c

WORKDIR /app
RUN gcc /app/target/main.c -o /app/target/target -lsqlite3

EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "warning"]
