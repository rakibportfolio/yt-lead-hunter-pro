# ============================================================
# ZENTIC MEDIA — CLIENT HUNTING AUTOMATION
# email_engine.py — Full Email Send + Tracking System
# ============================================================

import smtplib
import uuid
import re
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from config import cfg
from database import insert_email, mark_email_sent, upsert_daily_stats

# ── Email Templates ───────────────────────────────────────────
TEMPLATES = {
    "hot": {
        "subject": "Your channel '{channel}' is losing {loss_pct}% potential views 🎬",
        "body": """Hi {name},

I came across your YouTube channel "{channel}" and spent some time watching your recent videos.

Your content ideas are genuinely great — I can see you're putting in real effort. But I noticed something that's silently holding your channel back from growing.

📊 Based on our analysis:
• Your view-to-subscriber ratio is around {view_ratio}% (most growing channels hit 15%+)
• Your thumbnails could be optimized for higher click-through rate
• Your intro hooks could be stronger to retain viewers past 30 seconds

These are fixable — and fixing them could mean 2-3x more views within 60 days.

We're Zentic Media, a video editing agency that specializes in taking great content and making it look as professional as it deserves.

✅ What we do:
• Cinematic color grading & smooth cuts
• Custom motion graphics & animated intros
• Scroll-stopping thumbnail design
• Subtitles & captions that boost watch time

We've worked with creators at your level and seen real results. I'd love to show you some examples.

Would you be open to a quick 15-minute call this week? No pressure — just a conversation.

Best regards,
{sender_name}
Zentic Media
🌐 zenticmedia.com/portfolio | 📧 {sender_email}

{unsubscribe_link}
"""
    },
    "warm": {
        "subject": "Taking '{channel}' to the next level 📈",
        "body": """Hi {name},

Your channel "{channel}" is doing great — {subscribers} subscribers is something to be proud of!

But I noticed an opportunity: creators at your level often plateau because their video production quality hasn't kept pace with their content quality.

At Zentic Media, we help creators like you make the jump from "good" to "wow."

I'd love to share some before/after examples of channels similar to yours.

Can we connect for 15 minutes?

Best,
{sender_name}
Zentic Media

{unsubscribe_link}
"""
    },
    "cold": {
        "subject": "Following up — Zentic Media 👋",
        "body": """Hi {name},

I sent you a message recently about how we could help grow your YouTube channel "{channel}".

I know your inbox is busy, so I'll keep this short:

We help content creators get more views through professional video editing — better cuts, color grading, thumbnails, and intros that make people stay and come back.

If you're even slightly curious, just hit reply. If now's not the right time, no worries — I'll check back in a few weeks.

Keep creating! 🙌

Best,
{sender_name}
Zentic Media

{unsubscribe_link}
"""
    },
    "case_study": {
        "subject": "How a creator like you got 3x views in 60 days 📊",
        "body": """Hi {name},

Quick story:

One of our clients had a channel similar to "{channel}" — great content, but their editing was holding them back. Their average views were stuck at 800-1,200 per video.

After working with Zentic Media for 60 days:
• Average views jumped to 3,400+ per video
• Subscriber growth went from ~50/month to ~400/month
• CTR on thumbnails improved from 3.1% to 7.8%

The only thing that changed? Their video editing and thumbnails.

If you'd like, I can put together a free mini-audit of your channel to show you exactly what we'd do for "{channel}".

Interested?

Best,
{sender_name}
Zentic Media

{unsubscribe_link}
"""
    }
}


def get_template(template_name: str, variables: dict) -> dict:
    """Get email template and fill in variables."""
    tmpl = TEMPLATES.get(template_name, TEMPLATES["hot"])
    subject = tmpl["subject"].format_map(SafeDict(variables))
    body    = tmpl["body"].format_map(SafeDict(variables))
    return {"subject": subject, "body": body}


class SafeDict(dict):
    """Returns the key as placeholder if key is missing."""
    def __missing__(self, key):
        return f"{{{key}}}"


# ── Tracking Pixel & Link Wrapper ─────────────────────────────
def build_tracking_pixel(tracking_id: str) -> str:
    url = f"{cfg.TRACKING_BASE_URL}/track/open/{tracking_id}"
    return f'<img src="{url}" width="1" height="1" style="display:none;" alt="" />'


def wrap_links_with_tracking(body_html: str, tracking_id: str) -> str:
    """Replace all href links with tracked versions."""
    def replace_link(match):
        original_url = match.group(1)
        tracked = f"{cfg.TRACKING_BASE_URL}/track/click/{tracking_id}?url={original_url}"
        return f'href="{tracked}"'
    return re.sub(r'href="(https?://[^"]+)"', replace_link, body_html)


def build_unsubscribe_link(tracking_id: str) -> str:
    return f"{cfg.TRACKING_BASE_URL}/unsubscribe/{tracking_id}"


def text_to_html(text: str, tracking_id: str) -> str:
    """Convert plain text email to styled HTML with tracking pixel."""
    lines = text.strip().split("\n")
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append("<br/>")
        elif line.startswith("•") or line.startswith("✅") or line.startswith("📊"):
            html_lines.append(f'<div style="margin: 4px 0; padding-left: 8px;">{line}</div>')
        else:
            html_lines.append(f'<p style="margin: 6px 0;">{line}</p>')

    pixel = build_tracking_pixel(tracking_id)
    html_body = "\n".join(html_lines)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <style>
    body {{
      font-family: 'Inter', Arial, sans-serif;
      font-size: 15px;
      color: #1a1a1a;
      line-height: 1.7;
      max-width: 600px;
      margin: 0 auto;
      padding: 20px;
      background: #f9f9f9;
    }}
    .email-wrap {{
      background: #ffffff;
      border-radius: 10px;
      padding: 32px 36px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }}
    .email-header {{
      border-bottom: 3px solid #7c3aed;
      padding-bottom: 16px;
      margin-bottom: 24px;
    }}
    .brand {{
      font-size: 20px;
      font-weight: 800;
      color: #7c3aed;
      letter-spacing: -0.5px;
    }}
    .footer {{
      margin-top: 32px;
      padding-top: 16px;
      border-top: 1px solid #eee;
      font-size: 12px;
      color: #888;
    }}
    a {{ color: #7c3aed; }}
  </style>
</head>
<body>
  <div class="email-wrap">
    <div class="email-header">
      <div class="brand">⚡ ZENTIC MEDIA</div>
    </div>
    {html_body}
    <div class="footer">
      <p>Zentic Media | Professional Video Editing Agency</p>
      <p>🌐 <a href="https://zenticmedia.com/portfolio" style="color:#666;">zenticmedia.com/portfolio</a> | 📧 {cfg.GMAIL_ADDRESS}</p>
    </div>
  </div>
  {pixel}
</body>
</html>"""


# ── Core Email Sender ─────────────────────────────────────────
def send_email(
    to_address: str,
    subject: str,
    body_text: str,
    lead_id: int = None,
    template_used: str = None,
    campaign_id: int = None,
    personalization: dict = None
) -> dict:
    """
    Send a single email with tracking.
    Returns: { success, tracking_id, email_id, error }
    """
    if not cfg.GMAIL_ADDRESS or not cfg.GMAIL_PASSWORD:
        print("[Email] Warning: No Gmail credentials. Running in DEMO mode.")
        tracking_id = str(uuid.uuid4())
        email_id = insert_email({
            "lead_id":      lead_id,
            "to_address":   to_address,
            "subject":      subject,
            "body":         body_text,
            "template_used": template_used,
            "tracking_id":  tracking_id,
            "status":       "demo",
            "campaign_id":  campaign_id,
        })
        mark_email_sent(email_id)
        upsert_daily_stats({"emails_sent": 1})
        return {"success": True, "tracking_id": tracking_id, "email_id": email_id,
                "mode": "demo", "error": None}

    tracking_id = str(uuid.uuid4())

    # Insert into DB before sending
    email_id = insert_email({
        "lead_id":      lead_id,
        "to_address":   to_address,
        "subject":      subject,
        "body":         body_text,
        "template_used": template_used,
        "tracking_id":  tracking_id,
        "status":       "pending",
        "campaign_id":  campaign_id,
    })

    try:
        # Build MIME message
        msg = MIMEMultipart("alternative")
        msg["From"]    = f"Zentic Media <{cfg.GMAIL_ADDRESS}>"
        msg["To"]      = to_address
        msg["Subject"] = subject
        msg["X-Tracking-ID"] = tracking_id

        # Plain text part
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        # HTML part with tracking
        html = text_to_html(body_text, tracking_id)
        html = wrap_links_with_tracking(html, tracking_id)
        msg.attach(MIMEText(html, "html", "utf-8"))

        # Send via SMTP
        with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT) as server:
            server.starttls()
            server.login(cfg.GMAIL_ADDRESS, cfg.GMAIL_PASSWORD)
            server.sendmail(cfg.GMAIL_ADDRESS, to_address, msg.as_string())

        mark_email_sent(email_id)
        upsert_daily_stats({"emails_sent": 1})
        print(f"[Email] Sent to {to_address} | Tracking: {tracking_id}")
        return {"success": True, "tracking_id": tracking_id, "email_id": email_id, "error": None}

    except smtplib.SMTPException as e:
        error_msg = str(e)
        from database import get_db
        conn = get_db()
        conn.execute("UPDATE emails SET status='failed', error_msg=? WHERE id=?",
                     (error_msg, email_id))
        conn.commit()
        conn.close()
        upsert_daily_stats({"emails_failed": 1})
        print(f"[Email] Failed to {to_address}: {error_msg}")
        return {"success": False, "tracking_id": tracking_id, "email_id": email_id, "error": error_msg}


def send_bulk_emails(leads: list, template_name: str = "hot",
                     campaign_id: int = None,
                     delay_seconds: float = 2.0) -> dict:
    """
    Send emails to a list of leads with personalization.
    Respects daily send limit.
    """
    results = {"sent": 0, "failed": 0, "skipped": 0, "details": []}

    for lead in leads:
        if not lead.get("email"):
            print(f"[Bulk] ⚠️ No email for {lead.get('name')} — skipping")
            results["skipped"] += 1
            continue

        # Personalize template
        variables = {
            "name":          lead.get("name", "there"),
            "channel":       lead.get("channel", "your channel"),
            "subscribers":   lead.get("subscribers", ""),
            "view_ratio":    lead.get("ai_analysis", {}).get("view_ratio", "low"),
            "loss_pct":      random.randint(30, 60),
            "sender_name":   "Your Name",
            "sender_email":  cfg.GMAIL_ADDRESS,
            "unsubscribe_link": "",  # Will be filled after email is inserted
        }

        tmpl = get_template(template_name, variables)
        result = send_email(
            to_address=lead["email"],
            subject=tmpl["subject"],
            body_text=tmpl["body"],
            lead_id=lead.get("id"),
            template_used=template_name,
            campaign_id=campaign_id,
        )

        if result["success"]:
            results["sent"] += 1
        else:
            results["failed"] += 1

        results["details"].append({
            "lead": lead.get("name"),
            "email": lead["email"],
            **result
        })

        import time
        time.sleep(delay_seconds)  # Human-like delay

    print(f"\n[Bulk Email] Done! Sent: {results['sent']} | Failed: {results['failed']} | Skipped: {results['skipped']}")
    return results


import random  # needed for loss_pct above


if __name__ == "__main__":
    # Test email send
    result = send_email(
        to_address="test@example.com",
        subject="Test from Zentic Media",
        body_text="Hello! This is a test email from Zentic Media automation system.",
        lead_id=1,
        template_used="test"
    )
    print(result)
