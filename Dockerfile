FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt /app/

# Prefer wheels; no system packages needed
RUN python -m pip install --upgrade pip && pip install --prefer-binary -r requirements.txt

COPY . /app

CMD ["python", "scanner.py"]
