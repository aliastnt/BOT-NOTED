# Minimal Docker Deploy

- Uses `python:3.11-slim`
- No `apt-get` step (avoids Debian mirror issues)
- Installs `pandas_ta==0.3.14b0` **from PyPI** (no git needed)

## Steps
1) Ensure Railway uses **Dockerfile** build method.
2) Upload this repo or push to GitHub.
3) Set envs from `.env.example`.
4) Deploy.
