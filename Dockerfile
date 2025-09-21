FROM python:3.11-slim

# System deps (optional but good for pip/ssl/timezones)
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     ca-certificates     && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/

# Upgrade pip and install deps
RUN python -m pip install --upgrade pip &&     pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . /app

# Default command
CMD ["python", "scanner.py"]
