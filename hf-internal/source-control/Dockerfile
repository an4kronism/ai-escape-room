FROM python:3.11-slim
RUN pip install --no-cache-dir fastapi uvicorn pyjwt cryptography
COPY server.py /app/server.py
COPY ed25519_public.pem /app/ed25519_public.pem
COPY repos/ /app/repos/
WORKDIR /app
EXPOSE 8443
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8443", "--log-level", "warning"]
