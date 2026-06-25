FROM python:3.11-slim

WORKDIR /app

# Create data dir
RUN mkdir -p /app/data

# Install dependencies
RUN pip install fastapi uvicorn bcrypt cryptography

# Copy backend
COPY app/main.py .

# Copy frontend
COPY app/static/index.html /app/static/index.html

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
