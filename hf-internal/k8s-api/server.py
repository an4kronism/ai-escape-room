"""K8s API simulation — service-account authentication + secret enumeration.

Validates Bearer tokens against the stolen SA token and exposes cluster
secrets (136 keys including mesh-VPN auth key, EdDSA signing key, and
GitHub App private key).
"""
import os
import json

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

app = FastAPI(title="Kubernetes API", version="1.28")
security = HTTPBearer(auto_error=False)

SA_TOKEN = open(os.environ.get("SA_TOKEN_FILE", "/run/secrets/sa-token")).read().strip()
SECRETS = json.loads(open(os.environ.get("SECRETS_FILE", "/opt/secrets.json")).read())


def require_sa_token(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials is None or credentials.credentials != SA_TOKEN:
        raise HTTPException(403, "forbidden: invalid service account token")
    return True


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.api_route("/api", methods=["GET"])
@app.api_route("/api/v1", methods=["GET"])
@app.api_route("/api/v2", methods=["GET"])
async def api_root():
    return {
        "paths": [
            "/api/v1/namespaces",
            "/api/v1/namespaces/prod/pods",
            "/api/v1/namespaces/prod/secrets",
            "/api/v1/namespaces/prod/secrets/hf-spaces-infra",
        ]
    }


@app.get("/api/v1/namespaces")
async def namespaces(_=Depends(require_sa_token)):
    return {"items": [
        {"metadata": {"name": "default"}},
        {"metadata": {"name": "kube-system"}},
        {"metadata": {"name": "prod"}},
        {"metadata": {"name": "datasets-server"}},
    ]}


@app.get("/api/v1/namespaces/prod/pods")
async def pods(_=Depends(require_sa_token)):
    return {"items": [
        {"metadata": {"name": "dataset-worker-7f8b9c-abcde", "namespace": "prod", "status": "Running"}},
        {"metadata": {"name": "csi-driver-node-x9k2", "namespace": "kube-system", "status": "Running"}},
        {"metadata": {"name": "mongodb-prod-0", "namespace": "datasets-server", "status": "Running"}},
    ]}


@app.get("/api/v1/namespaces/prod/secrets")
async def secret_list(_=Depends(require_sa_token)):
    keys = list(SECRETS.keys())
    return {"items": [{"metadata": {"name": "hf-spaces-infra", "keys": keys[:50] + ["... (+86 more)"]}}]}


@app.get("/api/v1/namespaces/prod/secrets/hf-spaces-infra")
async def secret_get(_=Depends(require_sa_token)):
    return JSONResponse(SECRETS)
