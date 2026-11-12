FROM python:3.11-slim

WORKDIR /app

# Install system dependencies & required Chromium shared libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libglib2.0-0 \
    fonts-liberation \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for caching
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir playwright && playwright install chromium

# Copy all project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

ENV PORT=8000
ENV DEBUG=false
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app/backend:/app"
ENV GEMINI_API_KEY=""
ENV TELEGRAM_BOT_TOKEN="8874694866:AAEmdXxd3DP3B8J4L2sHS0pIxVR98HV9vqI"
ENV TELEGRAM_CHAT_ID="8279465535"
ENV FB_COOKIES="c_user=61596189753927; xs=10%3A7PDqH_pgyfvaYg%3A2%3A1793872866%3A-1%3A-1%3A%3AAc13S0OyRBF97oQgiYi5h6VVjV-ukklOAr0-jbJ6jw; datr=HFPsam-TCd_zqJqyJj5z_EUP; fr=1kTTEA8FDCKBEY8CG.AWe7PlK5aYABxOPONIm-yfAqOfz2wee-5JZTMaHH0AZ4tJUtE34.Bq7HAR..AAA.0.0.Bq7HyO.AWcuTG8ZLFDxfxICZUvOnTRgDjw; sb=UsxtatoCptXE8jKBsA-hWEps; ps_l=1; ps_n=1; locale=en_GB; wd=1920x911"

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Start with entrypoint script (runs both 24/7 worker & web server)
CMD ["/app/entrypoint.sh"]

