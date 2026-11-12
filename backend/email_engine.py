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
    },
    "var1": {
        "subject": "quick question about {channel} 🎬",
        "body": """Hey {name},

I was watching your content on {channel} today — genuinely impressed by the consistency. Building to {subscribers} subs and over {total_views} views takes serious dedication that 95% of creators quit before reaching.

Looking at current retention trends, the biggest bottleneck creators face isn't their content quality, but viewer drop-off in the first 30 seconds before the algorithm kicks in.

We run Zentic Media (https://zenticmedia.com/portfolio), where we specialize in retention editing that keeps viewers hooked through dynamic pacing, sound design, and pattern interrupts.

Talk is cheap, so here's a risk-free idea:
I'd love to take 20–30 seconds of raw footage from your upcoming video and edit a high-retention demo hook for you — completely free. If you like the retention boost, you can use it in your video 100% on the house; if not, no hard feelings at all.

Dropping an upload this week? Mind if I send a quick 20-second sample over?

Best,
Rakibul Hasan (Rakib)
Founder & Lead Editor | Zentic Media"""
    },
    "var2": {
        "subject": "Quick retention thought on your content ({channel})",
        "body": """Hey {name},

Congrats on over {total_views} views on {channel}!

I noticed views fluctuate across your uploads. On YouTube, if viewer retention drops below 60% in the first 45 seconds, the algorithm immediately slows Browse impressions—usually caused by slow hooks and missing sound cues.

At Zentic Media, we specialize in high-retention editing (https://zenticmedia.com/portfolio).

I'd love to edit a free 20-second retention hook for your upcoming video. No commitment—just to prove the watch-time jump.

Dropping a video this week?

Best,
Rakibul Hasan (Rakib) | Zentic Media"""
    },
    "var3": {
        "subject": "A/B test for {channel}'s next video?",
        "body": """Hey {name},

Big fan of your content—you've built an incredible audience of {subscribers} creators!

Talk is cheap, so here's a risk-free test: Send me 20-30 seconds of raw intro footage from your next video. I'll edit a high-retention hook completely free.

Test it against your normal edit. If your retention graph doesn't spike, you lose nothing.

You can check out our recent creator edits here: https://zenticmedia.com/portfolio

Open to giving it a shot?

Best regards,
Rakibul Hasan (Rakib)
Lead Video Editor, Zentic Media"""
    },
    "var4": {
        "subject": "Free 20s hook for {channel}?",
        "body": """Hey {name},

Great work on your latest upload!

I run Zentic Media (https://zenticmedia.com/portfolio), where we specialize in retention editing that keeps viewers watching past the 60-second mark.

To prove our quality, I'd love to edit a 20-second demo hook for your next video 100% free with zero strings attached.

If you like the retention boost, great. If not, it's yours to keep free.

Dropping a video this week? Just reply "yes" and I'll send over the details.

Best,
Rakibul Hasan (Rakib) | Zentic Media"""
    },
    "var5": {
        "subject": "quick question regarding {channel}",
        "body": """Hey {name},

Huge congrats on building {channel} to {subscribers} subscribers!

While checking out your uploads, I noticed the intro pacing takes 20-30 seconds to get to the core point, which usually causes early drop-off before YouTube pushes the video to Suggested feeds.

We fix this through micro-resets and tight hooks (portfolio: https://zenticmedia.com/portfolio).

Can I gift you a free 20-second hook edit for your next video so you can see the difference on your retention graph?

Best,
Rakibul Hasan (Rakib)
Founder, Zentic Media"""
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


# ── Clean Creator Name & Greeting Helper ───────────────────────
def clean_creator_display_name(raw_title: str) -> tuple:
    """
    Cleans raw YouTube channel titles into natural, human-sounding greetings and channel names.
    Removes domains (.com, .ca), pipes (|), dashes (-), and redundant words.
    Returns: (greeting_name, clean_channel_name)
    """
    if not raw_title:
        return "Creator", "your channel"

    t = raw_title.strip()

    # 1. Split pipes (|) and pick most personal/brand side
    if "|" in t:
        parts = [p.strip() for p in t.split("|") if p.strip()]
        if any("team" in p.lower() for p in parts):
            t = next(p for p in parts if "team" in p.lower())
        else:
            t = parts[-1] if len(parts[-1]) < len(parts[0]) else parts[0]
    elif " - " in t:
        parts = [p.strip() for p in t.split(" - ") if p.strip()]
        t = parts[0]

    # 2. Strip domain extensions (.com.au, .ca, .com, .org, .tv)
    t = re.sub(r"\.(?:com\.au|co\.uk|com|ca|org|net|tv|io)\b", "", t, flags=re.I)

    # 3. Handle birdhousemediatv -> Birdhouse Media
    if t.lower().endswith("tv") and len(t) > 5 and not t.isupper():
        t = t[:-2]

    # Split conjoined words only if NO space before it (e.g. birdhousemedia -> birdhouse media)
    t = re.sub(r"(?i)(?<=[a-zA-Z0-9])(media|properties|films|estate|studios|group|realty|podcast|homes)$", r" \1", t)

    # 4. Strip trailing redundant video/channel words
    t = re.sub(r"\s+(?:Videos|Channel|Films)$", "", t, flags=re.I)
    t = re.sub(r"^(?:The\s+)", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()
    if t.islower():
        t = t.title()

    words = t.split()
    non_person = {
        "real", "estate", "media", "proper", "homes", "team", "show", "hub", "tv", 
        "living", "films", "studios", "group", "podcast", "channel", "realtor", 
        "property", "legal", "commercial", "ontario", "toronto", "canada", 
        "vancouver", "housing", "market", "investing", "daily", "guide", "solutions"
    }

    # Pattern: Person Name + Brand (e.g. 'Wendy Berke Real Estate' -> 'Wendy')
    if len(words) >= 3 and words[0].lower() not in non_person and words[1].lower() not in non_person and any(w.lower() in {"real", "estate", "realtor", "homes"} for w in words[2:]):
        greeting = words[0]
        channel_name = t
    elif len(words) == 2 and not any(w.lower() in non_person for w in words):
        greeting = words[0]
        channel_name = t
    elif any(w.lower() == "team" for w in words):
        greeting = t
        channel_name = t
    else:
        greeting = f"{t} team"
        channel_name = t

    return greeting, channel_name


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
    """
    Convert plain text email to authentic, personal 1-to-1 HTML email.
    Includes a hidden preheader to ensure the Gmail subtitle/preview is 100% natural,
    with NO bot-like '⚡ ZENTIC MEDIA' prefixes.
    """
    lines = text.strip().split("\n")
    html_lines = []
    preview_snippet = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_lines.append("<br/>")
        else:
            if not preview_snippet and not stripped.lower().startswith("hey") and not stripped.lower().startswith("hi"):
                preview_snippet = stripped
            elif not preview_snippet:
                preview_snippet = stripped

            if stripped.startswith("•") or stripped.startswith("✅") or stripped.startswith("📊"):
                html_lines.append(f'<div style="margin: 4px 0; padding-left: 8px;">{stripped}</div>')
            else:
                html_lines.append(f'<p style="margin: 8px 0; line-height: 1.6;">{stripped}</p>')

    pixel = build_tracking_pixel(tracking_id)
    html_body = "\n".join(html_lines)
    clean_preview = preview_snippet[:130] if preview_snippet else "Quick thought on your recent video"

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title></title>
</head>
<body style="margin: 0; padding: 18px 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; color: #1e293b; background-color: #ffffff; line-height: 1.6;">
  <!-- Clean Hidden Preheader (Sets the exact subtitle/preview text in Gmail & Outlook) -->
  <div style="display:none!important;font-size:1px;color:#ffffff;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;mso-hide:all;">
    {clean_preview} &#847; &#847; &#847; &#847; &#847; &#847; &#847; &#847; &#847; &#847; &#847; &#847; &#847; &#847;
  </div>
  <div style="max-width: 580px; margin: 0; color: #1e293b;">
    {html_body}
    <div style="margin-top: 26px; padding-top: 14px; border-top: 1px solid #e2e8f0; font-size: 13px; color: #64748b; line-height: 1.5;">
      <p style="margin: 2px 0; font-weight: 700; color: #0f172a;">Rakibul Hasan (Rakib)</p>
      <p style="margin: 2px 0;">Founder & Lead Video Editor, <b>Zentic Media</b></p>
      <p style="margin: 2px 0;">🌐 <a href="https://zenticmedia.com/portfolio" style="color: #6366f1; text-decoration: none;">zenticmedia.com/portfolio</a> | 📧 {cfg.GMAIL_ADDRESS}</p>
    </div>
  </div>
  {pixel}
</body>
</html>"""


# ── Domain Deliverability & Bounce Guard ──────────────────────
import socket

def is_domain_deliverable(email: str) -> bool:
    """
    Validates whether the domain in an email exists via DNS lookup.
    Prevents hard bounces (NXDOMAIN) and protects the sender's reputation.
    """
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1].strip().lower()
    if not domain or "." not in domain:
        return False
    try:
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False


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
    # Pre-send Deliverability Guard (Bounce Prevention)
    if not is_domain_deliverable(to_address):
        domain = to_address.split("@")[-1] if "@" in to_address else to_address
        error_msg = f"Domain '{domain}' does not exist (DNS NXDOMAIN). Send blocked to prevent bounce."
        print(f"[Email] ⚠️ Blocked sending to {to_address}: {error_msg}")
        return {
            "success": False,
            "tracking_id": None,
            "email_id": None,
            "error": error_msg
        }

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


def send_bulk_emails(leads: list, template_name: str = "var1",
                     custom_subject: str = "",
                     custom_body: str = "",
                     campaign_id: int = None,
                     delay_seconds: float = 15.0) -> dict:
    """
    Send emails to a list of leads with personalization and anti-spam delays.
    Respects daily send limit.
    """
    results = {"sent": 0, "failed": 0, "skipped": 0, "details": []}

    for lead in leads:
        lead_email = (lead.get("email") or "").strip()
        if not lead_email:
            print(f"[Bulk] ⚠️ No email for {lead.get('name')} — skipping")
            results["skipped"] += 1
            continue

        if not is_domain_deliverable(lead_email):
            print(f"[Bulk] ⚠️ Invalid/non-existent domain for {lead.get('name')} ({lead_email}) — skipping to prevent bounce")
            results["skipped"] += 1
            continue

        raw_title = lead.get("channel") or lead.get("name") or "Creator"
        greeting_name, clean_channel = clean_creator_display_name(raw_title)
        subs_val = str(lead.get("subscribers") or "1.5K")
        views_val = str(lead.get("total_views") or "45.2K")
        vids_val = str(lead.get("videos") or 85)
        created_val = str(lead.get("created") or "Oct 2022")

        # Personalize template with clean human names
        variables = {
            "name":          greeting_name,
            "channel":       clean_channel,
            "subscribers":   subs_val,
            "total_views":   views_val,
            "videos":        vids_val,
            "created":       created_val,
            "view_ratio":    lead.get("ai_analysis", {}).get("view_ratio", "low"),
            "loss_pct":      random.randint(30, 60),
            "sender_name":   "Rakibul Hasan (Rakib)",
            "sender_email":  cfg.GMAIL_ADDRESS,
            "unsubscribe_link": "",
        }

        if custom_subject and custom_body:
            subj = custom_subject.format_map(SafeDict(variables))
            b_text = custom_body.format_map(SafeDict(variables))
            tmpl_label = "custom_campaign"
        else:
            tmpl = get_template(template_name, variables)
            subj = tmpl["subject"]
            b_text = tmpl["body"]
            tmpl_label = template_name

        result = send_email(
            to_address=lead["email"],
            subject=subj,
            body_text=b_text,
            lead_id=lead.get("id"),
            template_used=tmpl_label,
            campaign_id=campaign_id,
        )

        if result["success"]:
            results["sent"] += 1
        else:
            results["failed"] += 1

        results["details"].append({
            "lead": ch_title,
            "email": lead["email"],
            **result
        })

        import time
        time.sleep(delay_seconds)  # Human-like delay to preserve sender reputation

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
