# MEXC Micro-cap Scanner — Dockerized

This repo includes a **Dockerfile** pinned to **Python 3.11** to avoid build issues on Railway/Nixpacks.

## Deploy on Railway (Docker flow)
1. Create a new Railway project → **Deploy from GitHub** (recommended) or **Upload** this zip.
2. In **Settings → Deployment Method**, ensure it's using **Dockerfile** (not Nixpacks).
3. Add environment variables in **Variables** (copy from `.env.example`).
4. Deploy. Railway will build the image via the Dockerfile and start with `python scanner.py`.

### Local run (Docker)
```bash
docker build -t mexc-scanner .
docker run --env-file .env mexc-scanner
```

If you prefer Nixpacks without Dockerfile, set Python version to 3.11 and tighten requirements (numpy>=2.0 for Python 3.12) and keep a **Start Command**: `python scanner.py`.
