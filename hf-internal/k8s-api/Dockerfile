FROM python:3.11-slim
RUN pip install --no-cache-dir fastapi uvicorn
COPY server.py /app/server.py
COPY secrets.json /opt/secrets.json
COPY sa-token /run/secrets/sa-token
WORKDIR /app
EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "warning"]
