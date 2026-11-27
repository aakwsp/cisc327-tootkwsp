FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY run.py .
COPY notification_service.py .

EXPOSE 5000

CMD ["python", "-m", "flask", "--app", "run:app", "run", "--host=0.0.0.0", "--port=5000"]
