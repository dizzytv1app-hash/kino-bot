FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Baza va loglar shu papkalarda saqlanadi: ularni volume (doimiy disk) ga ulang
VOLUME ["/app/data", "/app/logs"]

CMD ["python", "main.py"]
