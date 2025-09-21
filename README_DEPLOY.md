# Quick Fix: Railway build error with pandas-ta

Use this repo which pins Python 3.11 and **pandas_ta** (underscore) package:

- `Dockerfile` base: `python:3.11-slim`
- `requirements.txt`: uses `pandas_ta==0.5.25b0`

Deploy steps:
1. In Railway, ensure **Dockerfile** build method.
2. Add ENV from `.env.example`.
3. Deploy.
