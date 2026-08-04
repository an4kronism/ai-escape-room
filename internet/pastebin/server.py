"""Pastebin — simple text store."""
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()
pastes: dict[str, str] = {}

@app.post("/api/paste")
async def create(request: Request):
    body = (await request.body()).decode("utf-8", errors="replace")
    pid = uuid.uuid4().hex[:12]
    pastes[pid] = body
    return {"id": pid}

@app.get("/raw/{pid}")
async def get(pid: str):
    text = pastes.get(pid, "")
    return Response(content=text, media_type="text/plain")
