# ============================================================
# ZENTIC MEDIA — CLIENT HUNTING AUTOMATION
# telegram_bot.py — Daily Reports + Real-time Alerts
# ============================================================

import asyncio
import requests
from datetime import datetime
from config import cfg
from database import get_today_email_stats, get_all_leads, get_all_emails

# ── Core Telegram Sender ──────────────────────────────────────
def send_telegram(message: str, parse_mode: str = "Markdown") -> bool:
    """Send a message to Telegram chat."""
    if not cfg.TELEGRAM_BOT_TOKEN or not cfg.TELEGRAM_CHAT_ID:
        # Silently skip printing raw markdown in demo mode to avoid terminal encoding issues
        print("[Telegram] Demo mode: No credentials configured.")
        return False

    url = f"https://api.telegram.org/bot{cfg.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":    cfg.TELEGRAM_CHAT_ID,
        "text":       message,
        "parse_mode": parse_mode,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        print("[Telegram] Message sent successfully.")
        return True
    except Exception as e:
        print(f"[Telegram] Error sending message: {e}")
        return False


def send_telegram_html(message: str) -> bool:
    """Send HTML formatted message."""
    return send_telegram(message, parse_mode="HTML")


# ── Alert Messages ────────────────────────────────────────────
def alert_email_opened(lead_name: str, email_subject: str, open_count: int):
    """Alert when someone opens an email."""
    emoji = "🔥" if open_count >= 3 else "👁️"
    advice = f"⚡ _They have opened it {open_count} times - CALL THEM NOW!_" if open_count >= 3 else "_Follow up if they don't reply soon._"
    msg = f"""{emoji} *EMAIL OPENED*

👤 *Lead:* {lead_name}
📧 *Subject:* {email_subject}
🔢 *Times Opened:* {open_count}
⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}

{advice}"""
    send_telegram(msg)


def alert_email_replied(lead_name: str, email: str, subject: str):
    """Alert when someone replies to an email."""
    msg = f"""✅ *REPLY RECEIVED!*

👤 *Lead:* {lead_name}
📧 *Email:* {email}
💬 *Subject:* {subject}
⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}

_🎯 Check your inbox and reply ASAP!_"""
    send_telegram(msg)


def alert_email_clicked(lead_name: str, url: str):
    """Alert when someone clicks a link."""
    msg = f"""🔗 *LINK CLICKED!*

👤 *Lead:* {lead_name}
🌐 *Link:* {url[:60]}...
⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}

_They're interested! Follow up now._"""
    send_telegram(msg)


def alert_new_leads_found(count: int, keyword: str, hot_count: int):
    """Alert when a YouTube scan finds leads."""
    msg = f"""🔍 *NEW LEADS FOUND!*

🎯 *Keyword:* `{keyword}`
📊 *Total Found:* {count}
🔥 *Hot Leads:* {hot_count}
⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}

_Go to dashboard to start outreach!_"""
    send_telegram(msg)


def alert_social_reply(platform: str, lead_name: str, message_preview: str):
    """Alert when someone replies on social media."""
    icons = {
        "whatsapp": "💬",
        "linkedin": "💼",
        "twitter":  "🐦",
        "instagram": "📸"
    }
    icon = icons.get(platform, "📱")
    msg = f"""{icon} *{platform.upper()} REPLY!*

👤 *Lead:* {lead_name}
💬 *Message:* _{message_preview[:100]}_
⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}

_Reply them on {platform}!_"""
    send_telegram(msg)


# ── Daily Report ──────────────────────────────────────────────
def build_daily_report() -> str:
    """Build the full daily report message."""
    today = datetime.now().strftime("%d %B %Y")
    stats = get_today_email_stats()

    # Lead counts
    all_leads = get_all_leads()
    today_leads = len([l for l in all_leads if
                       l.get("created_at", "").startswith(datetime.now().strftime("%Y-%m-%d"))])
    hot_leads  = len([l for l in all_leads if l.get("lead_type") == "hot"])
    warm_leads = len([l for l in all_leads if l.get("lead_type") == "warm"])

    # Email stats
    sent    = stats.get("sent", 0)
    failed  = stats.get("failed", 0)
    opened  = stats.get("opened", 0)
    clicked = stats.get("clicked", 0)
    replied = stats.get("replied", 0)
    total   = stats.get("total", 0)

    open_rate   = f"{(opened/max(sent,1)*100):.1f}%" if sent > 0 else "0%"
    reply_rate  = f"{(replied/max(sent,1)*100):.1f}%" if sent > 0 else "0%"
    click_rate  = f"{(clicked/max(sent,1)*100):.1f}%" if sent > 0 else "0%"

    # Hot leads for alerts
    hot_lead_list = [l for l in all_leads if l.get("lead_type") == "hot"][:3]
    hot_str = ""
    for l in hot_lead_list:
        hot_str += f"\n   🔥 *{l['name']}* — Score: {l['ai_score']}"

    report = f"""
📊 *ZENTIC MEDIA — DAILY REPORT*
📅 *{today}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 *LEADS TODAY*
   • YouTube/Google মিলিয়ে:  *{today_leads}* জন
   • 🔥 Hot Leads মোট:       *{hot_leads}* জন
   • 🟡 Warm Leads মোট:      *{warm_leads}* জন

📧 *EMAIL STATS*
   • পাঠানো হয়েছে:           *{sent}* টি ✅
   • পাঠানো যায়নি:           *{failed}* টি ❌
   • Open হয়েছে:            *{opened}* টি 👁️ ({open_rate})
   • Open হয়নি:             *{max(sent-opened, 0)}* টি 😴
   • Click হয়েছে:           *{clicked}* টি 🔗 ({click_rate})
   • Reply এসেছে:            *{replied}* টি ↩️ ({reply_rate})

📱 *TOP HOT LEADS*{hot_str if hot_str else chr(10) + '   No hot leads today.'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 _Go to dashboard for full details_
🌐 zentic.media
"""
    return report.strip()


def send_daily_report():
    """Send the daily report to Telegram."""
    report = build_daily_report()
    success = send_telegram(report)
    if success:
        print("[Telegram] Daily report sent successfully.")
    return success


# ── Report Scheduler ──────────────────────────────────────────
def schedule_daily_report():
    """
    Run in background — sends report at configured time every day.
    Call this once at startup.
    """
    import schedule
    import time

    report_time = cfg.DAILY_REPORT_TIME  # e.g. "23:00"
    print(f"[Telegram] Daily report scheduled at {report_time}")

    schedule.every().day.at(report_time).do(send_daily_report)

    while True:
        schedule.run_pending()
        time.sleep(30)


# ── Webhook Receiver (for Telegram Bot commands) ───────────────
TELEGRAM_COMMANDS = {}

def handle_telegram_update(update: dict):
    """Process incoming Telegram bot commands."""
    message = update.get("message", {})
    text    = message.get("text", "").strip()
    chat_id = str(message.get("chat", {}).get("id", ""))

    responses = {
        "/start":   "👋 Zentic Media Bot active!\n\nCommands:\n/report — Daily stats\n/leads — Hot leads\n/status — System status",
        "/report":  build_daily_report(),
        "/leads":   build_hot_leads_summary(),
        "/status":  build_system_status(),
        "/help":    "📖 Commands:\n/report — Send daily report\n/leads — Show hot leads\n/status — System status",
    }

    reply = responses.get(text, f"Unknown command: {text}\n\nType /help")
    send_telegram(reply)


def build_hot_leads_summary() -> str:
    leads = get_all_leads(lead_type="hot")[:5]
    if not leads:
        return "🔍 No hot leads found. Run a YouTube scan first!"

    msg = "🔥 *TOP HOT LEADS*\n━━━━━━━━━━━━━━━━\n"
    for lead in leads:
        msg += f"\n👤 *{lead['name']}*"
        msg += f"\n   📧 {lead.get('email', 'no email')}"
        msg += f"\n   📊 Score: {lead.get('ai_score', 0)}"
        msg += f"\n   📺 Subs: {lead.get('subscribers', 'N/A')}"
        msg += "\n"
    return msg


def build_system_status() -> str:
    stats = get_today_email_stats()
    return f"""⚙️ *SYSTEM STATUS*

🟢 Email Engine: Active
🟢 Database: Connected
🟢 Telegram Bot: Online
📧 Emails today: {stats.get('sent', 0)}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
📅 Date: {datetime.now().strftime('%d %b %Y')}"""


if __name__ == "__main__":
    # Test: send a test message + daily report
    send_telegram("🚀 *Zentic Media Bot Started!*\n\nAutomation system is online.")
    send_daily_report()


def send_telegram_photo(caption: str, photo_url: str = None, reply_markup: dict = None) -> bool:
    """Send photo with caption to Telegram chat, fallback to message."""
    if not cfg.TELEGRAM_BOT_TOKEN or not cfg.TELEGRAM_CHAT_ID:
        print("[Telegram] Demo mode: No credentials configured.")
        return False

    if photo_url and (photo_url.startswith("http://") or photo_url.startswith("https://")):
        url = f"https://api.telegram.org/bot{cfg.TELEGRAM_BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": cfg.TELEGRAM_CHAT_ID,
            "photo": photo_url,
            "caption": caption[:1024],  # Telegram caption limit
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                print("[Telegram] Photo sent successfully.")
                return True
        except Exception as e:
            print(f"[Telegram] Failed to send photo, falling back to text: {e}")

    # Fallback to sendMessage
    url = f"https://api.telegram.org/bot{cfg.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": cfg.TELEGRAM_CHAT_ID,
        "text": caption,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        print("[Telegram] HTML message sent successfully.")
        return True
    except Exception as e:
        print(f"[Telegram] Error sending message: {e}")
        return False


def alert_fb_hiring_post(job: dict) -> bool:
    """Send instant high-priority alert for a Facebook Video Editor hiring post."""
    group_name = job.get("group_name", "Facebook Group")
    author_name = job.get("author_name", "Client")
    author_url = job.get("author_url", "")
    client_name = job.get("client_name") or author_name
    job_type = job.get("job_type", "Video Editor")
    budget = job.get("budget", "Negotiable / Not specified")
    post_url = job.get("post_url", "")
    image_url = job.get("image_url", "")
    summary = job.get("ai_summary", job.get("content", ""))[:350]
    
    phone = job.get("contact_phone", "")
    whatsapp = job.get("contact_whatsapp", "") or phone
    email = job.get("contact_email", "")

    # Clean whatsapp digits
    clean_wa = "".join(c for c in whatsapp if c.isdigit())
    if clean_wa.startswith("01") and len(clean_wa) == 11:
        clean_wa = "88" + clean_wa  # Bangladesh country code helper

    caption = f"""🚨 <b>NEW VIDEO EDITOR HIRING POST!</b> 🎯
━━━━━━━━━━━━━━━━━━━━
🏢 <b>Group:</b> {group_name}
👤 <b>Client:</b> {client_name}
"""
    if author_url:
        caption += f"🔗 <b>FB Profile / ID:</b> <a href='{author_url}'>{author_url}</a>\n"
    elif post_url:
        caption += f"🔗 <b>FB Post & ID:</b> <a href='{post_url}'>Click to View & Message Poster</a>\n"

    caption += f"""💼 <b>Need:</b> {job_type}
💰 <b>Budget:</b> {budget}

📋 <b>Post Summary:</b>
<i>"{summary}"</i>
"""
    if phone or email:
        caption += "\n📞 <b>Contact Info Extracted:</b>\n"
        if phone:
            caption += f"• <b>Phone:</b> {phone}\n"
        if email:
            caption += f"• <b>Email:</b> {email}\n"

    caption += f"""
━━━━━━━━━━━━━━━━━━━━
⚡ <b>React fast to secure this deal before other editors!</b>"""

    # Build inline buttons (WhatsApp + Direct FB Profile/Post)
    inline_keyboard = []
    btn_row = []
    if clean_wa:
        btn_row.append({"text": "💬 WhatsApp Chat", "url": f"https://wa.me/{clean_wa}"})
    if author_url:
        btn_row.append({"text": "👤 Message on FB", "url": author_url})
    elif post_url:
        btn_row.append({"text": "🔗 Open FB Post", "url": post_url})
    if btn_row:
        inline_keyboard.append(btn_row)

    if post_url and author_url:
        inline_keyboard.append([{"text": "🔗 View Full FB Post", "url": post_url}])

    reply_markup = {"inline_keyboard": inline_keyboard} if inline_keyboard else None

    return send_telegram_photo(caption=caption, photo_url=image_url, reply_markup=reply_markup)
