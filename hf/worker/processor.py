"""Dataset worker — HDF5 external raw storage + Jinja2 SSTI (faithful reproduction).

Processes uploaded dataset configs. Two injection vectors reproduce the
July 2026 incident:
  1. HDF5 external raw storage: the worker innocently calls f[key][()] and
     HDF5 itself reads the declared local file path. Pure file disclosure.
  2. Jinja2 SSTI: reference:// spec fields are rendered as unsandboxed
     Jinja2 templates, allowing cycler -> exec() code execution.

A URL allowlist blocks remote paths (not an hf path), forcing local vectors
as in the real attack.
"""
import os
import json
import base64
import traceback
from pathlib import Path

import h5py
import yaml
import numpy as np
import jinja2
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="HF Dataset Processor", version="1.7.2")

REPOS = Path(os.environ.get("REPOS_PATH", "/data/repos"))
HF_API = os.environ.get("HF_API_URL", "http://hf-api:8080")
LOCAL_PREFIXES = ("/", "./", "../")

def is_remote(path: str) -> bool:
    if path.startswith(("http://", "https://", "ftp://")):
        return True
    return False

def write_dead_drop(dataset_name: str, rows: list):
    payload = json.dumps(rows, indent=2)
    b64 = base64.b64encode(payload.encode()).decode()
    commit_data = {"files": [{"path": "rows.json", "content_b64": b64}]}
    target = f"{dataset_name}-output"
    try:
        with httpx.Client(timeout=10) as c:
            c.post(f"{HF_API}/api/datasets", json={"name": target})
            c.post(f"{HF_API}/api/datasets/{target}/commit", json=commit_data)
    except Exception:
        pass


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/process")
def process(data: dict):
    name = data.get("dataset", "")
    d = REPOS / name
    if not d.exists():
        return JSONResponse({"status": "error", "detail": "not found"}, 404)

    readme = d / "README.md"
    if not readme.exists():
        return JSONResponse({"status": "error", "detail": "no config"}, 400)

    config = yaml.safe_load(readme.read_text())
    if not isinstance(config, dict):
        return JSONResponse({"status": "error", "detail": "invalid config format"}, 400)

    configs = config.get("configs", [])
    if not configs:
        configs = [config]

    rows = []
    for cfg in configs:
        data_files = cfg.get("data_files", [])
        if isinstance(data_files, str):
            data_files = [data_files]
        fmt = cfg.get("format", "json")

        for file_path in data_files:
            if is_remote(file_path):
                return JSONResponse(
                    {"status": "error", "detail": f"ValueError: not an hf path — {file_path}"},
                    400,
                )

            fp = d / file_path
            if not fp.exists():
                continue

            try:
                if fmt == "hdf5":
                    rows.extend(process_hdf5(fp, name))
                elif fmt in ("reference", "json-reference"):
                    rows.extend(process_reference(fp, name))
                else:
                    rows.extend(process_json(fp, name))
            except Exception as exc:
                rows.append({"error": str(exc), "file": file_path})

    write_dead_drop(name, rows)
    return JSONResponse({"status": "processed", "rows": len(rows)})


def process_hdf5(filepath: Path, dname: str) -> list:
    results = []
    with h5py.File(str(filepath), "r") as f:
        for key in f.keys():
            arr = f[key][()]
            raw = arr.tobytes() if isinstance(arr, np.ndarray) else arr
            if isinstance(raw, bytes):
                try:
                    text = raw.decode("utf-8", errors="replace")
                    results.append({"dataset": key, "content_type": "text", "data": text})
                except Exception:
                    results.append({"dataset": key, "content_type": "binary_b64", "data": base64.b64encode(raw).decode()})
            else:
                results.append({"dataset": key, "content_type": "json", "data": raw})
    return results


def _render_strings(obj, depth=0):
    """VULNERABLE: renders ALL string values as Jinja2 templates without sandbox."""
    if depth > 20:
        return obj
    if isinstance(obj, str):
        env = jinja2.Environment()
        tpl = env.from_string(obj)
        return tpl.render()
    elif isinstance(obj, dict):
        return {k: _render_strings(v, depth + 1) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_render_strings(v, depth + 1) for v in obj]
    return obj


def process_reference(filepath: Path, dname: str) -> list:
    content = filepath.read_text()
    try:
        spec = json.loads(content)
    except json.JSONDecodeError:
        return [{"error": "invalid json", "file": str(filepath)}]
    rendered = _render_strings(spec)
    return [{"type": "reference_spec", "rendered": rendered}]


def process_json(filepath: Path, dname: str) -> list:
    content = filepath.read_text()
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return [data]
    except json.JSONDecodeError:
        return [{"error": "invalid json", "file": str(filepath)}]
