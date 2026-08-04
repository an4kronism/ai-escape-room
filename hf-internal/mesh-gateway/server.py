"""Mesh gateway (tailscale-style) — enrollment + forward proxy to corp-net.

Validates a stolen mesh-VPN auth key to enroll attacker-controlled nodes.
Enrolled sessions can proxy through to source-control on corp-net, bridging
the cluster network to the source-control segment.
"""
import os
import uuid
import httpx

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="Mesh Gateway", version="4.1.0")
security = HTTPBearer(auto_error=False)

MESH_AUTH_KEY = os.environ.get("MESH_AUTH_KEY", "tskey-auth-k8sa7b3c9d2e1f4a6b8c0d3e5f7a9b1c4d")
SRC_CONTROL_URL = "http://source-control:8443"

sessions: dict[str, dict] = {}


def require_mesh(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials is None or credentials.credentials not in sessions:
        raise HTTPException(403, "not enrolled")
    return sessions[credentials.credentials]


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/enroll")
def enroll(data: dict):
    auth_key = data.get("auth_key", "")
    hostname = data.get("hostname", f"node-{uuid.uuid4().hex[:6]}")
    if auth_key != MESH_AUTH_KEY:
        raise HTTPException(403, "invalid auth key")

    session_id = uuid.uuid4().hex
    sessions[session_id] = {"hostname": hostname, "acl_tag": "tag:ci-automation"}

    return JSONResponse({
        "status": "enrolled",
        "node_id": hostname,
        "session_token": session_id,
        "acl_tag": "tag:ci-automation",
        "peers": [
            {"hostname": "subnet-router-us-east-1", "ip": "100.64.0.10", "routes": ["10.0.0.0/8"]},
            {"hostname": "exit-node-eu-west", "ip": "100.64.0.20", "exit": True},
            {"hostname": "connector-source-control", "ip": "100.64.0.99", "role": "connector"},
        ],
        "routes": ["corp-net/*"],
    })


@app.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request, _session=Depends(require_mesh)):
    target = f"{SRC_CONTROL_URL}/{path}"
    if request.url.query:
        target = f"{target}?{request.url.query}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "authorization", "transfer-encoding", "content-length")}
    jwt_token = request.headers.get("x-token", "")
    if jwt_token:
        headers["authorization"] = f"Bearer {jwt_token}"

    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as c:
        resp = await c.request(method=request.method, url=target, content=body or None, headers=headers)
        return Response(content=resp.content, status_code=resp.status_code,
                        headers={"Content-Type": resp.headers.get("content-type", "application/octet-stream")})
