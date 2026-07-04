FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

USER appuser

EXPOSE 5000

CMD [ "gunicorn", "--workers=4", "--bind=0.0.0.0:5000","--timeout=30", "--access-logfile=-","app:app" ]

