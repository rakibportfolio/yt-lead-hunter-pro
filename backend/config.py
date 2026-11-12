# ============================================================
# ZENTIC MEDIA — CLIENT HUNTING AUTOMATION
# config.py — All settings in one place
# ============================================================

import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)
load_dotenv()

def _clean_val(val: str) -> str:
    if not val:
        return ""
    v = val.strip()
    if v.startswith("your_") or "your_app_password" in v or v == "your@gmail.com":
        return ""
    return v

class Config:
    # ── App ──────────────────────────────────────────────────
    APP_NAME    = "Zentic Media Client Hunter"
    VERSION     = "1.0.0"
    DEBUG       = os.getenv("DEBUG", "true").lower() == "true"

    # ── Database ─────────────────────────────────────────────
    _DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zentic_data.db")
    DB_PATH     = os.getenv("DB_PATH", _DEFAULT_DB)
    if not os.path.isabs(DB_PATH):
        DB_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_PATH))

    # ── Gmail / Email ─────────────────────────────────────────
    GMAIL_ADDRESS   = _clean_val(os.getenv("GMAIL_ADDRESS", ""))
    GMAIL_PASSWORD  = _clean_val(os.getenv("GMAIL_PASSWORD", ""))   # App Password
    SMTP_HOST       = "smtp.gmail.com"
    SMTP_PORT       = 587
    DAILY_SEND_LIMIT = int(os.getenv("DAILY_SEND_LIMIT", "200"))

    # Email tracking — your server URL (where pixel lives)
    TRACKING_BASE_URL = os.getenv("TRACKING_BASE_URL", "http://localhost:8000")

    # ── YouTube API ───────────────────────────────────────────
    YOUTUBE_API_KEY = _clean_val(os.getenv("YOUTUBE_API_KEY", ""))
    YOUTUBE_QUOTA_LIMIT = 10000   # daily

    # ── Bright Data YouTube Datasets ──────────────────────────
    BRIGHT_DATA_API_KEY = _clean_val(os.getenv("BRIGHT_DATA_API_KEY", ""))
    BRIGHT_DATA_VIDEOS_DATASET = "gd_lk56epmy2i5g7lzu0k"
    BRIGHT_DATA_CHANNELS_DATASET = "gd_lk538t2k2p1k3oos71"
    BRIGHT_DATA_BASE_URL = "https://api.brightdata.com/datasets/v3"

    # ── Gemini AI ─────────────────────────────────────────────
    GEMINI_API_KEY = _clean_val(os.getenv("GEMINI_API_KEY", ""))

    # ── Facebook Session Cookies ─────────────────────────────
    FB_COOKIES = os.getenv("FB_COOKIES", "c_user=61596189753927; xs=10%3A7PDqH_pgyfvaYg%3A2%3A1793872866%3A-1%3A-1%3A%3AAc13S0OyRBF97oQgiYi5h6VVjV-ukklOAr0-jbJ6jw; datr=HFPsam-TCd_zqJqyJj5z_EUP; fr=1kTTEA8FDCKBEY8CG.AWe7PlK5aYABxOPONIm-yfAqOfz2wee-5JZTMaHH0AZ4tJUtE34.Bq7HAR..AAA.0.0.Bq7HyO.AWcuTG8ZLFDxfxICZUvOnTRgDjw; sb=UsxtatoCptXE8jKBsA-hWEps; ps_l=1; ps_n=1; locale=en_GB; wd=1920x911")

    # ── Telegram Bot ──────────────────────────────────────────
    TELEGRAM_BOT_TOKEN = _clean_val(os.getenv("TELEGRAM_BOT_TOKEN", "8874694866:AAEmdXxd3DP3B8J4L2sHS0pIxVR98HV9vqI"))
    TELEGRAM_CHAT_ID   = _clean_val(os.getenv("TELEGRAM_CHAT_ID", "8279465535"))
    DAILY_REPORT_TIME  = os.getenv("DAILY_REPORT_TIME", "23:00")

    # ── WhatsApp ──────────────────────────────────────────────
    WHATSAPP_TOKEN       = _clean_val(os.getenv("WHATSAPP_TOKEN", ""))
    WHATSAPP_PHONE_ID    = _clean_val(os.getenv("WHATSAPP_PHONE_ID", ""))

    # ── Links ─────────────────────────────────────────────────
    PORTFOLIO_LINK       = os.getenv("PORTFOLIO_LINK", "https://zenticmedia.com/portfolio")
    CALENDLY_LINK        = os.getenv("CALENDLY_LINK", "https://calendly.com/zenticmedia")
    AGENCY_NAME          = "Zentic Media"
    WEBSITE_LINK         = "https://zenticmedia.com"
    FOUNDER_NAME         = "Rakibul Hasan (Rakib)"
    FOUNDER_TITLE        = "Founder, CEO & Lead Video Editor"

    # ── Social APIs ───────────────────────────────────────────
    TWITTER_BEARER_TOKEN = _clean_val(os.getenv("TWITTER_BEARER_TOKEN", ""))
    LINKEDIN_CLIENT_ID   = _clean_val(os.getenv("LINKEDIN_CLIENT_ID", ""))
    LINKEDIN_CLIENT_SECRET = _clean_val(os.getenv("LINKEDIN_CLIENT_SECRET", ""))

cfg = Config()
