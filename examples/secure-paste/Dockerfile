
FROM python:3.11-slim

WORKDIR /app
RUN pip install fastapi uvicorn bcrypt cryptography

COPY app/main.py .
COPY app/static/index.html static/index.html

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
