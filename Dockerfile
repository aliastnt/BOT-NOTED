FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git ca-certificates \ && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /app
CMD ["python", "scanner.py"]
