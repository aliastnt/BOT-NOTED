FROM python:3.11-slim
ENV PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt /app/
# In ra để chắc chắn Railway đang dùng file mới, KHÔNG còn main.zip
RUN echo "=== REQUIREMENTS ===" \
 && cat /app/requirements.txt \
 && python -m pip install --upgrade pip \
 && pip install --prefer-binary -r requirements.txt

COPY . /app
CMD ["python", "scanner.py"]
