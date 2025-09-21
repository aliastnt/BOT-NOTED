# Deploy Guide (Railway + Dockerfile)

This package uses a Dockerfile pinned to Python 3.11 and installs `pandas_ta` from GitHub:

- `requirements.txt`: `pandas_ta @ git+https://github.com/twopirllc/pandas-ta@0.3.14b0`
- `Dockerfile`: installs `git` so pip can fetch from GitHub
- Start command: `python scanner.py`

## Railway steps
1) Create project → choose **Deploy from GitHub** (or upload this ZIP).
2) In Settings, ensure **Build from Dockerfile** (not Nixpacks).
3) Add envs from `.env.example` in Variables.
4) Deploy.
