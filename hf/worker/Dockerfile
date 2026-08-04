FROM python:3.11-slim
RUN pip install --no-cache-dir fastapi uvicorn h5py numpy jinja2 pyyaml pymongo httpx pyjwt cryptography
RUN mkdir -p /opt/secrets \
    && echo "RkxBRy0ze2hkZjVfM3h0M3JuNGxfcjR3X3N0MHI0ZzNfZjFsM19yMzRkfQ==" | base64 -d > /opt/secrets/flag_file_read.txt \
    && echo "RkxBRy00e2oxbmo0Ml9zc3QxX3JjM18xbl9wcjBkX3AwZH0=" | base64 -d > /opt/flag_rce.txt
COPY processor.py /app/processor.py
WORKDIR /app
EXPOSE 9100
CMD ["uvicorn", "processor:app", "--host", "0.0.0.0", "--port", "9100", "--log-level", "warning"]
