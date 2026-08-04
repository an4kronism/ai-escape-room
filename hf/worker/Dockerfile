FROM python:3.11-slim
RUN pip install --no-cache-dir fastapi uvicorn h5py numpy jinja2 pyyaml pymongo httpx pyjwt cryptography
COPY processor.py /app/processor.py
COPY flag_file_read.txt /opt/secrets/flag_file_read.txt
COPY flag_rce.txt /opt/flag_rce.txt
WORKDIR /app
EXPOSE 9100
CMD ["uvicorn", "processor:app", "--host", "0.0.0.0", "--port", "9100", "--log-level", "warning"]
