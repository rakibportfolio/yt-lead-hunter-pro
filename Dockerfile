FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for caching
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir playwright && playwright install --with-deps chromium || true

# Copy all project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

ENV PORT=8000
ENV DEBUG=false
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app/backend:/app"
ENV GEMINI_API_KEY=""
ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_CHAT_ID=""

# Start FastAPI backend
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

