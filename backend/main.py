import sys
import os

# Ensure backend directory is in sys.path for direct imports
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fb_group_monitor import (
    start_fb_monitor, stop_fb_monitor, process_single_fb_group, send_test_fb_hiring_alert,
    is_post_fresh, classify_fb_post_with_ai
)
# ============================================================
# ZENTIC MEDIA — CLIENT HUNTING AUTOMATION
# main.py — FastAPI Backend Server
# Connects Dashboard ↔ Python Engine
# ============================================================

import os
import uuid
import json
import threading
from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, HTMLResponse, RedirectResponse, FileResponse
import requests
from pydantic import BaseModel
from typing import Optional, List

from config import cfg
from database import (
    get_all_fb_groups, insert_fb_group, delete_fb_group, toggle_fb_group, get_fb_alerts,
    init_db, get_all_leads, get_all_emails, get_today_email_stats,
    insert_lead, update_lead_status, mark_email_opened, mark_email_clicked,
    mark_email_replied, insert_social_message, mark_social_sent,
    upsert_daily_stats, get_db,
    get_pipeline_board, move_pipeline_stage, get_pipeline_stats,
    log_activity, get_lead_activity, update_lead_tag, update_lead_notes
)
from email_engine import send_email, send_bulk_emails, get_template, TEMPLATES
from youtube_scraper import scan_youtube, generate_channel_pitch, scrape_channel_recent_videos
from telegram_bot import (
    send_telegram, send_daily_report, alert_email_opened,
    alert_email_replied, alert_email_clicked, alert_new_leads_found,
    build_daily_report, handle_telegram_update
)

# ── App Init ─────────────────────────────────────────────────
app = FastAPI(title="Zentic Media Client Hunter", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
def startup():
    init_db()
    try:
        start_fb_monitor()
    except Exception as e:
        print(f"[Startup Warning] Could not start FB monitor: {e}")
    print(f"\n{'='*50}")
    print("  [ZENTIC MEDIA] Client Hunter Backend")
    print(f"  Running at: http://localhost:8000")
    print(f"  Gmail: {cfg.GMAIL_ADDRESS or 'NOT SET'}")
    print(f"  Telegram: {'SET' if cfg.TELEGRAM_BOT_TOKEN else 'NOT SET'}")
    print(f"  YouTube API: {'SET' if cfg.YOUTUBE_API_KEY else 'NOT SET'}")
    print(f"{'='*50}\n")
    try:
        send_telegram("Zentic Media Backend Started! All systems online.")
    except Exception:
        pass


# ── Scan progress store (in-memory) ──────────────────────────
scan_progress_store = {}


# ═══════════════════════════════════════════════════════════════
# TRACKING ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/track/open/{tracking_id}")
async def track_open(tracking_id: str, background_tasks: BackgroundTasks):
    """Tracking pixel endpoint — fires when email is opened."""
    background_tasks.add_task(_process_open, tracking_id)
    # Return 1x1 transparent GIF
    gif = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    return Response(content=gif, media_type="image/gif",
                    headers={"Cache-Control": "no-cache, no-store"})


def _process_open(tracking_id: str):
    mark_email_opened(tracking_id)
    upsert_daily_stats({"emails_opened": 1})
    # Get lead info for Telegram alert
    conn = get_db()
    row = conn.execute("""
        SELECT e.subject, e.open_count, l.name
        FROM emails e LEFT JOIN leads l ON e.lead_id = l.id
        WHERE e.tracking_id = ?
    """, (tracking_id,)).fetchone()
    conn.close()
    if row:
        alert_email_opened(row["name"] or "Unknown", row["subject"] or "", row["open_count"])


@app.get("/track/click/{tracking_id}")
async def track_click(tracking_id: str, url: str = "", background_tasks: BackgroundTasks = None):
    """Redirect to original URL and track the click."""
    mark_email_clicked(tracking_id)
    upsert_daily_stats({"emails_clicked": 1})
    # Alert Telegram
    conn = get_db()
    row = conn.execute("SELECT l.name FROM emails e LEFT JOIN leads l ON e.lead_id=l.id WHERE e.tracking_id=?",
                       (tracking_id,)).fetchone()
    conn.close()
    if row:
        alert_email_clicked(row["name"] or "Unknown", url)
    if url:
        return RedirectResponse(url=url, status_code=302)
    return JSONResponse({"tracked": True})


@app.get("/unsubscribe/{tracking_id}")
async def unsubscribe(tracking_id: str):
    """Handle unsubscribe requests."""
    conn = get_db()
    conn.execute("UPDATE emails SET status='unsubscribed' WHERE tracking_id=?", (tracking_id,))
    conn.commit()
    conn.close()
    return HTMLResponse("""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px">
    <h2>✅ You've been unsubscribed.</h2>
    <p>You won't receive any more emails from Zentic Media.</p>
    </body></html>
    """)


# ═══════════════════════════════════════════════════════════════
# LEADS API
# ═══════════════════════════════════════════════════════════════

@app.get("/api/leads")
def api_get_leads(status: Optional[str] = None, lead_type: Optional[str] = None):
    leads = get_all_leads(status=status, lead_type=lead_type)
    return {"leads": leads, "count": len(leads)}


class LeadCreate(BaseModel):
    name: str
    channel: Optional[str] = ""
    platform: Optional[str] = "Manual"
    subscribers: Optional[str] = ""
    email: Optional[str] = ""
    website: Optional[str] = ""
    social: Optional[dict] = {}
    ai_score: Optional[int] = 50
    lead_type: Optional[str] = "warm"

@app.post("/api/leads")
def api_create_lead(lead: LeadCreate):
    lead_id = insert_lead(lead.dict())
    return {"success": True, "lead_id": lead_id}


@app.patch("/api/leads/{lead_id}/status")
def api_update_lead_status(lead_id: int, body: dict):
    update_lead_status(lead_id, body.get("status", "new"))
    return {"success": True}


@app.post("/api/leads/{lead_id}/generate-pitch")
def api_generate_pitch(lead_id: int):
    conn = get_db()
    lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    conn.close()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead_dict = dict(lead)
    pitch = generate_channel_pitch(lead_dict)
    return {"success": True, **pitch}


@app.post("/api/leads/generate-custom-pitch")
def api_generate_custom_pitch(body: dict):
    pitch = generate_channel_pitch(body)
    return {"success": True, **pitch}


# ═══════════════════════════════════════════════════════════════
# YOUTUBE SCANNER API
# ═══════════════════════════════════════════════════════════════

class ScanRequest(BaseModel):
    keyword: str
    min_subs: Optional[int] = 1000
    max_subs: Optional[int] = 500000
    max_results: Optional[int] = 20
    engine: Optional[str] = "auto"   # "auto", "bright_data", "youtube_standard"

@app.post("/api/scan/youtube")
def api_scan_youtube(req: ScanRequest, background_tasks: BackgroundTasks):
    """Start a YouTube scan in the background."""
    scan_id = str(uuid.uuid4())[:8]
    scan_progress_store[scan_id] = {
        "status": "running",
        "progress": 0,
        "step": "Starting...",
        "leads": [],
        "found": 0,
    }

    def run_scan():
        def progress_cb(event_type, value, msg=""):
            if event_type == "progress":
                scan_progress_store[scan_id]["progress"] = value
                scan_progress_store[scan_id]["step"] = msg
            elif event_type == "step":
                scan_progress_store[scan_id]["step"] = value
            elif event_type == "done":
                scan_progress_store[scan_id]["status"] = "done"
                scan_progress_store[scan_id]["progress"] = 100

        leads = scan_youtube(
            keyword=req.keyword,
            min_subs=req.min_subs,
            max_subs=req.max_subs,
            max_results=req.max_results,
            progress_callback=progress_cb,
            engine=req.engine
        )
        scan_progress_store[scan_id]["leads"] = leads
        scan_progress_store[scan_id]["found"]  = len(leads)
        scan_progress_store[scan_id]["status"] = "done"

        # Telegram alert
        hot = len([l for l in leads if l.get("lead_type") == "hot"])
        alert_new_leads_found(len(leads), req.keyword, hot)

    background_tasks.add_task(run_scan)
    return {"scan_id": scan_id, "status": "started"}


@app.get("/api/scan/progress/{scan_id}")
def api_scan_progress(scan_id: str):
    """Poll scan progress."""
    data = scan_progress_store.get(scan_id, {"status": "not_found"})
    return data


# ═══════════════════════════════════════════════════════════════
# EMAIL API
# ═══════════════════════════════════════════════════════════════

class EmailSendRequest(BaseModel):
    to_address: str
    subject: str
    body: str
    lead_id: Optional[int] = None
    template_used: Optional[str] = None
    campaign_id: Optional[int] = None

@app.post("/api/email/send")
def api_send_email(req: EmailSendRequest):
    result = send_email(
        to_address=req.to_address,
        subject=req.subject,
        body_text=req.body,
        lead_id=req.lead_id,
        template_used=req.template_used,
        campaign_id=req.campaign_id,
    )
    return result


class BulkEmailRequest(BaseModel):
    lead_ids: List[int]
    template_name: str = "hot"
    campaign_id: Optional[int] = None
    delay_seconds: float = 2.0

@app.post("/api/email/bulk")
def api_bulk_email(req: BulkEmailRequest, background_tasks: BackgroundTasks):
    all_leads = get_all_leads()
    target_leads = [l for l in all_leads if l["id"] in req.lead_ids]
    if not target_leads:
        raise HTTPException(404, "No matching leads found")

    def run_bulk():
        results = send_bulk_emails(
            leads=target_leads,
            template_name=req.template_name,
            campaign_id=req.campaign_id,
            delay_seconds=req.delay_seconds
        )
        send_telegram(f"📧 *Bulk Email Done!*\n✅ Sent: {results['sent']}\n❌ Failed: {results['failed']}")

    background_tasks.add_task(run_bulk)
    return {"status": "started", "lead_count": len(target_leads)}


@app.get("/api/emails")
def api_get_emails(limit: int = 50):
    emails = get_all_emails(limit=limit)
    return {"emails": emails, "count": len(emails)}


@app.get("/api/email/stats")
def api_email_stats():
    return get_today_email_stats()


class TemplateRequest(BaseModel):
    template_name: str
    variables: dict

@app.post("/api/email/preview")
def api_email_preview(req: TemplateRequest):
    tmpl = get_template(req.template_name, req.variables)
    return tmpl


# ═══════════════════════════════════════════════════════════════
# SOCIAL MEDIA API
# ═══════════════════════════════════════════════════════════════

class WhatsAppRequest(BaseModel):
    to_number: str   # e.g. "+8801XXXXXXXXX"
    message: str
    lead_id: Optional[int] = None

@app.post("/api/social/whatsapp")
def api_send_whatsapp(req: WhatsAppRequest):
    """Send WhatsApp message via WhatsApp Business Cloud API."""
    if not cfg.WHATSAPP_TOKEN or not cfg.WHATSAPP_PHONE_ID:
        msg_id = insert_social_message({
            "lead_id": req.lead_id, "platform": "whatsapp",
            "to_address": req.to_number, "message": req.message
        })
        mark_social_sent(msg_id)
        upsert_daily_stats({"social_sent": 1})
        return {"success": True, "mode": "demo", "msg_id": msg_id}

    url = f"https://graph.facebook.com/v18.0/{cfg.WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {cfg.WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": req.to_number.replace("+", ""),
        "type": "text",
        "text": {"body": req.message}
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        msg_id = insert_social_message({
            "lead_id": req.lead_id, "platform": "whatsapp",
            "to_address": req.to_number, "message": req.message
        })
        mark_social_sent(msg_id)
        upsert_daily_stats({"social_sent": 1})
        return {"success": True, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


class TwitterDMRequest(BaseModel):
    to_user_id: str
    message: str
    lead_id: Optional[int] = None

@app.post("/api/social/twitter")
def api_send_twitter_dm(req: TwitterDMRequest):
    """Send Twitter/X DM via API v2."""
    if not cfg.TWITTER_BEARER_TOKEN:
        msg_id = insert_social_message({
            "lead_id": req.lead_id, "platform": "twitter",
            "to_address": req.to_user_id, "message": req.message
        })
        mark_social_sent(msg_id)
        return {"success": True, "mode": "demo"}

    url = "https://api.twitter.com/2/dm_conversations/with/:participant_id/messages"
    url = url.replace(":participant_id", req.to_user_id)
    headers = {"Authorization": f"Bearer {cfg.TWITTER_BEARER_TOKEN}", "Content-Type": "application/json"}
    payload = {"text": req.message}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        msg_id = insert_social_message({
            "lead_id": req.lead_id, "platform": "twitter",
            "to_address": req.to_user_id, "message": req.message
        })
        mark_social_sent(msg_id)
        upsert_daily_stats({"social_sent": 1})
        return {"success": True, "data": r.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# PITCH GENERATION API
# ═══════════════════════════════════════════════════════════════

class PitchRequest(BaseModel):
    channel: Optional[str] = ""
    name:    Optional[str] = ""
    handle:  Optional[str] = ""
    subs:    Optional[str] = ""
    email:   Optional[str] = ""
    channel_url: Optional[str] = ""

@app.post("/api/leads/generate-pitch")
def api_generate_pitch(req: PitchRequest):
    """
    Generate a hyper-personalized cold email pitch for any lead.
    Fetches the creator's last 7 videos, analyses retention metrics,
    and constructs a structured pitch:
    Channel Info -> Problem (retention/algorithm) -> Solution ->
    Portfolio -> Risk-Free Offer (free 20-30s hook) -> CTA
    """
    lead_dict = req.dict()
    # Fallback: derive handle from channel_url if not provided
    if not lead_dict.get("handle") and lead_dict.get("channel_url"):
        lead_dict["handle"] = lead_dict["channel_url"].rstrip("/").split("/")[-1]
    try:
        pitch = generate_channel_pitch(lead_dict)
        return {
            "success": True,
            "subject": pitch.get("subject", ""),
            "body":    pitch.get("body", ""),
            "audit":   pitch.get("audit", {}),
            "mode":    pitch.get("mode", "dynamic_smart"),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# TELEGRAM API
# ═══════════════════════════════════════════════════════════════

@app.post("/api/telegram/test")
def api_telegram_test():
    success = send_telegram("🧪 *Test from Zentic Media Dashboard!*\n\nTelegram is connected ✅")
    return {"success": success}


@app.post("/api/telegram/report")
def api_telegram_report():
    success = send_daily_report()
    return {"success": success, "report": build_daily_report()}


@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Receive Telegram bot updates (webhook mode)."""
    update = await request.json()
    handle_telegram_update(update)
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════
# DASHBOARD STATS API
# ═══════════════════════════════════════════════════════════════

@app.get("/api/stats/dashboard")
def api_dashboard_stats():
    """Get all stats for the dashboard."""
    email_stats = get_today_email_stats()
    all_leads   = get_all_leads()
    today_str   = datetime.now().strftime("%Y-%m-%d")
    today_leads = [l for l in all_leads if l.get("created_at", "").startswith(today_str)]

    sent = int(email_stats.get("sent") or 0)
    opened = int(email_stats.get("opened") or 0)
    failed = int(email_stats.get("failed") or 0)
    clicked = int(email_stats.get("clicked") or 0)
    replied = int(email_stats.get("replied") or 0)
    open_rate = f"{(opened / max(sent, 1) * 100):.1f}%" if sent > 0 else "0.0%"

    return {
        "leads_today":    len(today_leads),
        "leads_total":    len(all_leads),
        "hot_leads":      len([l for l in all_leads if l.get("lead_type") == "hot"]),
        "warm_leads":     len([l for l in all_leads if l.get("lead_type") == "warm"]),
        "emails_sent":    sent,
        "emails_failed":  failed,
        "emails_opened":  opened,
        "emails_clicked": clicked,
        "emails_replied": replied,
        "open_rate":      open_rate,
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "gmail": bool(cfg.GMAIL_ADDRESS),
        "telegram": bool(cfg.TELEGRAM_BOT_TOKEN),
        "youtube_api": bool(cfg.YOUTUBE_API_KEY),
        "bright_data": bool(cfg.BRIGHT_DATA_API_KEY),
        "gemini": bool(cfg.GEMINI_API_KEY),
    }


# ═══════════════════════════════════════════════════════════════
# CRM PIPELINE ENDPOINTS  (DjangoCRM-inspired)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/pipeline/board")
def api_pipeline_board():
    """Return full Kanban board grouped by stage."""
    try:
        board = get_pipeline_board()
        return {"ok": True, "board": board}
    except Exception as e:
        return {"ok": False, "error": str(e), "board": {}}


@app.get("/api/pipeline/stats")
def api_pipeline_stats():
    """Revenue + conversion stats per stage."""
    try:
        stats = get_pipeline_stats()
        return {"ok": True, **stats}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class PipelineMoveRequest(BaseModel):
    lead_id: int
    stage: str
    deal_value: Optional[float] = None
    tag: Optional[str] = None


@app.post("/api/pipeline/move")
def api_pipeline_move(req: PipelineMoveRequest):
    """Move a lead to a new pipeline stage."""
    valid = ['new_lead', 'outreach_sent', 'email_opened', 'replied', 'meeting_booked', 'deal_closed']
    if req.stage not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Use one of: {valid}")
    try:
        move_pipeline_stage(req.lead_id, req.stage, req.deal_value, req.tag)
        # Also sync the status column
        status_map = {
            'new_lead': 'new', 'outreach_sent': 'contacted',
            'email_opened': 'contacted', 'replied': 'replied',
            'meeting_booked': 'meeting', 'deal_closed': 'closed'
        }
        update_lead_status(req.lead_id, status_map.get(req.stage, 'new'))
        return {"ok": True, "message": f"Lead moved to {req.stage}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LeadTagRequest(BaseModel):
    tag: str   # hot / warm / cold / not_interested

@app.patch("/api/pipeline/{lead_id}/tag")
def api_update_tag(lead_id: int, req: LeadTagRequest):
    update_lead_tag(lead_id, req.tag)
    log_activity(lead_id, 'tag_changed', f'Tag set to {req.tag}')
    return {"ok": True}


class LeadNotesRequest(BaseModel):
    notes: str

@app.patch("/api/pipeline/{lead_id}/notes")
def api_update_notes(lead_id: int, req: LeadNotesRequest):
    update_lead_notes(lead_id, req.notes)
    log_activity(lead_id, 'notes_updated', 'Notes updated')
    return {"ok": True}


@app.get("/api/pipeline/{lead_id}/activity")
def api_lead_activity(lead_id: int):
    activities = get_lead_activity(lead_id)
    return {"ok": True, "activities": activities}


# ═══════════════════════════════════════════════════════════════
# BRIGHT DATA & OUTREACH EXPORT ENDPOINTS
# ═══════════════════════════════════════════════════════════════

class BrightDataSettings(BaseModel):
    api_key: str

@app.post("/api/settings/brightdata")
def api_save_brightdata_settings(body: BrightDataSettings):
    """Save Bright Data API Key to config and .env file."""
    cfg.BRIGHT_DATA_API_KEY = body.api_key.strip()
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        lines = []
        found = False
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if line.startswith("BRIGHT_DATA_API_KEY="):
                    lines[i] = f"BRIGHT_DATA_API_KEY={body.api_key.strip()}\n"
                    found = True
                    break
        if not found:
            lines.append(f"\nBRIGHT_DATA_API_KEY={body.api_key.strip()}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"[Settings] Error writing .env: {e}")
    return {"success": True, "connected": bool(cfg.BRIGHT_DATA_API_KEY)}


@app.get("/api/export/outreach-csv")
def export_outreach_csv():
    """
    Export leads in exact Google Sheet format for apps_script.gs:
    Columns: channel_name, email, subscribers, subject, body, status
    """
    import io
    import csv
    leads = get_all_leads()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["channel_name", "email", "subscribers", "subject", "body", "status"])

    for l in leads:
        ch_name = l.get("channel") or l.get("name") or "Creator"
        email = l.get("email") or ""
        subs = l.get("subscribers") or ""
        # Auto draft pitch subject & body if not already contacted
        subject = f"Quick question regarding your channel, {ch_name}"
        body = f"Hey {ch_name},\n\nLoved your recent videos! I noticed potential to 2x-3x your retention with tighter pacing, dynamic hooks, and sound design.\n\nWe would love to edit a 20-30s demo hook for your next video 100% free with zero risk.\n\nLet me know if you are dropping a video this week!\n\nBest,\nZentic Media Team"
        status = "" if email else "NO EMAIL"
        writer.writerow([ch_name, email, subs, subject, body, status])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=youtube_outreach_leads.csv"}
    )


# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# FACEBOOK GROUP HIRING RADAR ENDPOINTS
# ═══════════════════════════════════════════════════════════════

class FBGroupCreate(BaseModel):
    name: str
    url: str
    interval_min: Optional[int] = 2

@app.get("/api/fb/groups")
def api_get_fb_groups():
    return {"ok": True, "groups": get_all_fb_groups()}

@app.post("/api/fb/groups")
def api_add_fb_group(group: FBGroupCreate):
    url = group.url.strip()
    name = group.name.strip() or url.split('/')[-1] or "Facebook Group"
    try:
        gid = insert_fb_group(name=name, url=url, interval=group.interval_min or 2)
        return {"ok": True, "id": gid, "message": "Group added to radar"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add group: {e}")

@app.delete("/api/fb/groups/{group_id}")
def api_delete_fb_group(group_id: int):
    delete_fb_group(group_id)
    return {"ok": True, "message": "Group removed"}

@app.patch("/api/fb/groups/{group_id}/toggle")
def api_toggle_fb_group(group_id: int):
    active = toggle_fb_group(group_id)
    return {"ok": True, "active": active}

@app.get("/api/fb/alerts")
def api_get_fb_alerts(limit: int = 1000):
    alerts = get_fb_alerts(limit)
    return {"ok": True, "alerts": alerts}

@app.post("/api/fb/test-alert")
def api_test_fb_alert():
    result = send_test_fb_hiring_alert()
    return result

@app.post("/api/fb/scan-now")
def api_scan_fb_groups(background_tasks: BackgroundTasks):
    groups = [g for g in get_all_fb_groups() if g.get("active") == 1]
    def run_all():
        for g in groups:
            process_single_fb_group(g)
    background_tasks.add_task(run_all)
    return {"ok": True, "message": f"Scanning {len(groups)} active groups in background"}

@app.post("/api/fb/scan-group/{group_id}")
def api_scan_single_fb_group(group_id: int):
    all_groups = get_all_fb_groups()
    matched = [g for g in all_groups if g.get("id") == group_id]
    if not matched:
        raise HTTPException(status_code=404, detail="Group not found")
    g = matched[0]
    new_jobs = process_single_fb_group(g)
    alerts = get_fb_alerts(1000)
    return {
        "ok": True,
        "jobs_found": new_jobs,
        "message": f"Scanned {g['name']}! Found {new_jobs} new hiring leads.",
        "alerts": alerts
    }


class IngestPostItem(BaseModel):
    content: str
    author_name: Optional[str] = "Facebook User"
    post_url: Optional[str] = ""
    group_name: Optional[str] = "Facebook Group"
    image_url: Optional[str] = ""

class IngestBatch(BaseModel):
    posts: List[IngestPostItem]

@app.post("/api/fb/ingest")
def api_ingest_fb_posts(batch: IngestBatch):
    """
    Ingest live posts directly from Chrome browser / Extension / scraper.
    Applies STRICT 3-hour freshness filter + AI intent classification.
    Sends INSTANT Telegram alerts for qualified hiring posts!
    """
    from database import is_fb_post_seen, insert_fb_alert
    from telegram_bot import alert_fb_hiring_post
    from datetime import datetime

    dispatched = 0
    skipped_old = 0
    skipped_not_hiring = 0
    alerts_created = []

    for item in batch.posts:
        content = item.content.strip()
        if len(content) < 25:
            continue

        # 1. STRICT FRESHNESS CHECK (Max 3 Hours)
        if not is_post_fresh(content, max_hours=3):
            skipped_old += 1
            continue

        pid = f"fb_{abs(hash(content[:80]))}"
        if is_fb_post_seen(pid):
            continue

        ai_res = classify_fb_post_with_ai(content, item.author_name or "Client", item.group_name or "Facebook Group")
        if ai_res.get("is_hiring"):
            alert_data = {
                "group_id": None,
                "group_name": item.group_name or "Facebook Group",
                "post_id": pid,
                "author_name": item.author_name or "Client",
                "post_url": item.post_url or "https://facebook.com",
                "content": content,
                "image_url": item.image_url or "",
                "is_hiring": 1,
                "client_name": ai_res.get("client_name", item.author_name or "Client"),
                "job_type": ai_res.get("job_type", "Video Editor"),
                "budget": ai_res.get("budget", "Negotiable"),
                "contact_phone": ai_res.get("contact_phone", ""),
                "contact_email": ai_res.get("contact_email", ""),
                "contact_whatsapp": ai_res.get("contact_whatsapp", ""),
                "contact_telegram": ai_res.get("contact_telegram", ""),
                "confidence_score": ai_res.get("confidence_score", 95),
                "ai_summary": ai_res.get("ai_summary", content[:200]),
                "telegram_sent": 0,
                "telegram_sent_at": None
            }
            sent_ok = alert_fb_hiring_post(alert_data)
            if sent_ok:
                alert_data["telegram_sent"] = 1
                alert_data["telegram_sent_at"] = datetime.now().isoformat()
            insert_fb_alert(alert_data)
            alerts_created.append(alert_data)
            dispatched += 1
        else:
            skipped_not_hiring += 1

    return {
        "ok": True,
        "dispatched_to_telegram": dispatched,
        "skipped_old": skipped_old,
        "skipped_not_hiring": skipped_not_hiring,
        "alerts": alerts_created
    }

class TelegramSettings(BaseModel):
    bot_token: str
    chat_id: str

@app.post("/api/settings/telegram")
def api_save_telegram_settings(body: TelegramSettings):
    cfg.TELEGRAM_BOT_TOKEN = body.bot_token.strip()
    cfg.TELEGRAM_CHAT_ID = body.chat_id.strip()
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        token_found, chat_found = False, False
        for i, line in enumerate(lines):
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                lines[i] = f"TELEGRAM_BOT_TOKEN={body.bot_token.strip()}\n"
                token_found = True
            elif line.startswith("TELEGRAM_CHAT_ID="):
                lines[i] = f"TELEGRAM_CHAT_ID={body.chat_id.strip()}\n"
                chat_found = True
        
        if not token_found:
            lines.append(f"TELEGRAM_BOT_TOKEN={body.bot_token.strip()}\n")
        if not chat_found:
            lines.append(f"TELEGRAM_CHAT_ID={body.chat_id.strip()}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return {"ok": True, "message": "Telegram credentials saved and activated!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# SERVE FRONTEND DIRECTLY (Turnkey Dashboard at http://localhost:8000)
# ═══════════════════════════════════════════════════════════════

FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.get("/")
def serve_dashboard():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(
            index_path,
            media_type="text/html; charset=utf-8",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
    return HTMLResponse("<h2>Zentic Media Backend Running</h2>")

@app.get("/styles.css")
def serve_css():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "styles.css"),
        media_type="text/css; charset=utf-8",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

@app.get("/app.js")
def serve_js():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "app.js"),
        media_type="application/javascript; charset=utf-8",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
