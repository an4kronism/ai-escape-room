"""Request-capture — single-use capture service (C2/exfil)."""
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()
captures: dict[str, list[dict]] = {}

@app.post("/{uid:path}")
async def capture_post(uid: str, request: Request):
    body = (await request.body()).decode("utf-8", errors="replace")
    key = uid.strip("/") or uuid.uuid4().hex
    if key not in captures:
        captures[key] = []
    captures[key].append({"ts": time.time(), "method": "POST", "body": body})
    return {"id": key, "stored": True}

@app.get("/{uid}")
async def capture_get(uid: str):
    key = uid.strip("/")
    entries = captures.get(key, [])
    result = entries[-1]["body"] if entries else ""
    captures.pop(key, None)
    return JSONResponse({"id": key, "body": result} if entries else {"id": key, "empty": True})
