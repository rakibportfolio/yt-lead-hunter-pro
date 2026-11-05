# ============================================================
# ZENTIC MEDIA — CLIENT HUNTING AUTOMATION
# database.py — SQLite DB with all tables
# ============================================================

import sqlite3
import json
from datetime import datetime
from config import cfg


def get_db():
    conn = sqlite3.connect(cfg.DB_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_db()
    c = conn.cursor()

    # ── Leads Table ──────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            channel     TEXT,
            platform    TEXT DEFAULT 'YouTube',
            subscribers TEXT,
            email       TEXT,
            website     TEXT,
            social_json TEXT DEFAULT '{}',
            ai_score    INTEGER DEFAULT 0,
            lead_type   TEXT DEFAULT 'warm',   -- hot / warm / cold
            status      TEXT DEFAULT 'new',    -- new / contacted / replied / meeting / closed
            ai_analysis TEXT DEFAULT '{}',
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Emails Table ──────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id         INTEGER REFERENCES leads(id),
            to_address      TEXT NOT NULL,
            subject         TEXT,
            body            TEXT,
            template_used   TEXT,
            tracking_id     TEXT UNIQUE,
            sent_at         TEXT,
            opened_at       TEXT,
            open_count      INTEGER DEFAULT 0,
            clicked_at      TEXT,
            click_count     INTEGER DEFAULT 0,
            replied_at      TEXT,
            status          TEXT DEFAULT 'pending',  -- pending/sent/opened/clicked/replied/failed/bounced
            error_msg       TEXT,
            campaign_id     INTEGER
        )
    """)

    # ── Social Messages Table ────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS social_messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id     INTEGER REFERENCES leads(id),
            platform    TEXT NOT NULL,   -- whatsapp / linkedin / twitter / instagram
            to_address  TEXT NOT NULL,
            message     TEXT,
            status      TEXT DEFAULT 'pending',
            sent_at     TEXT,
            replied_at  TEXT,
            reply_text  TEXT,
            error_msg   TEXT
        )
    """)

    # ── Campaigns Table ──────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            target_type     TEXT,
            status          TEXT DEFAULT 'draft',
            drip_sequence   TEXT DEFAULT '[]',
            total_leads     INTEGER DEFAULT 0,
            emails_sent     INTEGER DEFAULT 0,
            emails_opened   INTEGER DEFAULT 0,
            emails_replied  INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Daily Stats Table ─────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT UNIQUE,
            leads_found     INTEGER DEFAULT 0,
            emails_sent     INTEGER DEFAULT 0,
            emails_failed   INTEGER DEFAULT 0,
            emails_opened   INTEGER DEFAULT 0,
            emails_clicked  INTEGER DEFAULT 0,
            emails_replied  INTEGER DEFAULT 0,
            social_sent     INTEGER DEFAULT 0,
            social_replied  INTEGER DEFAULT 0,
            new_clients     INTEGER DEFAULT 0
        )
    """)

    # ── Templates Table ──────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            type        TEXT,
            subject     TEXT,
            body        TEXT,
            platform    TEXT DEFAULT 'email',
            sends       INTEGER DEFAULT 0,
            opens       INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── CRM Pipeline Table ────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_cards (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id         INTEGER REFERENCES leads(id),
            stage           TEXT DEFAULT 'new_lead',
            deal_value      REAL DEFAULT 0,
            priority        TEXT DEFAULT 'normal',  -- low / normal / high / urgent
            tag             TEXT DEFAULT 'warm',    -- hot / warm / cold / not_interested
            next_followup   TEXT,
            notes           TEXT,
            assigned_to     TEXT DEFAULT 'Admin',
            stage_moved_at  TEXT DEFAULT (datetime('now')),
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Follow-up Sequences Table ─────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS followup_sequences (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id         INTEGER REFERENCES leads(id),
            email_id        INTEGER REFERENCES emails(id),
            sequence_step   INTEGER DEFAULT 1,
            scheduled_at    TEXT,
            sent_at         TEXT,
            status          TEXT DEFAULT 'pending',  -- pending / sent / skipped / replied
            subject         TEXT,
            body            TEXT
        )
    """)

    # ── Activity Log Table ────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id     INTEGER REFERENCES leads(id),
            action      TEXT NOT NULL,
            detail      TEXT,
            performed_by TEXT DEFAULT 'System',
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # Migrate existing leads table - add pipeline columns if missing
    try:
        c.execute("ALTER TABLE leads ADD COLUMN pipeline_stage TEXT DEFAULT 'new_lead'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE leads ADD COLUMN deal_value REAL DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE leads ADD COLUMN tag TEXT DEFAULT 'warm'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE leads ADD COLUMN next_followup TEXT")
    except Exception:
        pass

    # ── Facebook Group Monitoring Tables ───────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS fb_monitored_groups (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL,
            url                 TEXT UNIQUE NOT NULL,
            active              INTEGER DEFAULT 1,
            check_interval_min  INTEGER DEFAULT 2,
            priority            INTEGER DEFAULT 0,
            last_checked_at     TEXT,
            total_posts_scanned INTEGER DEFAULT 0,
            total_jobs_found    INTEGER DEFAULT 0,
            created_at          TEXT DEFAULT (datetime('now'))
        )
    """)

    try:
        c.execute("ALTER TABLE fb_monitored_groups ADD COLUMN priority INTEGER DEFAULT 0")
    except Exception:
        pass

    c.execute("""
        CREATE TABLE IF NOT EXISTS fb_job_alerts (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id            INTEGER REFERENCES fb_monitored_groups(id),
            group_name          TEXT,
            post_id             TEXT UNIQUE,
            author_name         TEXT,
            post_url            TEXT,
            content             TEXT,
            image_url           TEXT,
            is_hiring           INTEGER DEFAULT 1,
            client_name         TEXT,
            job_type            TEXT,
            budget              TEXT,
            contact_phone       TEXT,
            contact_email       TEXT,
            contact_whatsapp    TEXT,
            contact_telegram    TEXT,
            confidence_score    INTEGER DEFAULT 95,
            ai_summary          TEXT,
            telegram_sent       INTEGER DEFAULT 0,
            telegram_sent_at    TEXT,
            created_at          TEXT DEFAULT (datetime('now'))
        )
    """)

    # Seed curated Facebook video editing groups automatically
    DEFAULT_GROUPS = [
        # ── 4 VIP TOP PRIORITY GROUPS (Always Scanned First) ──────
        ("VIP: Video Editing Bangladesh", "https://www.facebook.com/groups/bangladeshyoututbeandfacebookcommunity/", 10),
        ("VIP: Video Editor - VFX Bangladesh", "https://www.facebook.com/groups/videoeditorhire/", 10),
        ("VIP: Video Editors Bangladesh BD", "https://www.facebook.com/groups/VideoEditorsBangladesh.BD/", 10),
        ("VIP: Video Editors BD #229", "https://www.facebook.com/groups/2292891657639248/", 10),

        # ── USER VERIFIED GROUPS ──────────────────────────────────
        ("MZ Studio BD", "https://www.facebook.com/groups/mzstudiobd/", 5),
        ("Video Editors & Creators BD #291", "https://www.facebook.com/groups/291019220252715/", 5),
        ("Video Editing Hub BD #359", "https://www.facebook.com/groups/359734483826735/", 5),
        ("Video Editor Jobs BD #185", "https://www.facebook.com/groups/1851439782436285/", 5),
        ("Video Editors Freelancer BD #147", "https://www.facebook.com/groups/147032671260514/", 5),
        ("Creative Video Editors BD #384", "https://www.facebook.com/groups/3847335125558578/", 5),
        ("Video Editing Community #752", "https://www.facebook.com/groups/752472806507912/", 5),
        ("Editors & Animators BD #874", "https://www.facebook.com/groups/874914633509210/", 5),
        ("Video Editors Bangladesh Official", "https://www.facebook.com/groups/videoeditorsbangladeshofficial/", 5),
        ("BD Video Creators & Editors #100", "https://www.facebook.com/groups/1001939884944907/", 5),
        ("Video Editing Zone BD #286", "https://www.facebook.com/groups/286521763690926/", 5),
        ("Video Editing & Hiring BD #109", "https://www.facebook.com/groups/1096533198753530/", 5),
        ("Video Editor Job Bangladesh", "https://www.facebook.com/groups/VideoditorJobBangladesh/", 5),
        ("Video Editors YES", "https://www.facebook.com/groups/videoeditorsyes/", 5),
        ("Professional Editors BD #229", "https://www.facebook.com/groups/2292891657639248/", 5),
        ("Video Editing Freelance BD #117", "https://www.facebook.com/groups/1173532240001355/", 5),
        ("BD Video Editing Network #294", "https://www.facebook.com/groups/294830932856749/", 5),
        ("Video Editor in Bangladesh", "https://www.facebook.com/groups/videoeditorinbangladesh/", 5),
        ("Professional Video Editor", "https://www.facebook.com/groups/ProfessionalVideoEditor/", 5),
        ("Video Editors Circle BD #151", "https://www.facebook.com/groups/1510297602711737/", 5),
        ("Freelance Video Editors BD #310", "https://www.facebook.com/groups/310584494121197/", 5),
        ("Video Editors Bangladesh PRO", "https://www.facebook.com/groups/videoeditorsbangladeshpro/", 5),
        ("BD Content & Video Editors #449", "https://www.facebook.com/groups/449818040305896/", 5),
        ("Digital Video Editors BD #185", "https://www.facebook.com/groups/185647597308414/", 5),
        ("Video Editing BD Hub #343", "https://www.facebook.com/groups/343780916577699/", 5),
        ("Creative Freelance Editors BD #656", "https://www.facebook.com/groups/6560510120739077/", 5),
        ("AE Video Editors PH / Global", "https://www.facebook.com/groups/AEVideoEditorsPH/", 5),
        ("Video Editing Masterclass BD #112", "https://www.facebook.com/groups/1126963997314568/", 5),
        ("Video Editor Bangladesh", "https://www.facebook.com/groups/videoeditorbd/"),
        ("Video Editing Jobs BD", "https://www.facebook.com/groups/videoeditingjobsbd/"),
        ("Freelancer Bangladesh", "https://www.facebook.com/groups/freelancerbd/"),
        ("Motion Graphics Bangladesh", "https://www.facebook.com/groups/motiondesignerbd/"),
        ("Adobe Premiere Pro Bangladesh", "https://www.facebook.com/groups/premiererobd/"),
        ("After Effects Bangladesh", "https://www.facebook.com/groups/aftereffectsbd/"),
        ("Bangladesh Freelancers", "https://www.facebook.com/groups/bangladeshfreelancers/"),
        ("Video Editor Jobs Worldwide", "https://www.facebook.com/groups/videoeditorjobs/"),
        ("Video Editor Needed", "https://www.facebook.com/groups/videoeditorsneeded/"),
        # ── 10k+ to 150k+ Bangladesh Freelancer & Creator Groups ────
        ("Freelancers of Bangladesh (100k+)", "https://www.facebook.com/groups/freelancersofbangladesh/"),
        ("BD Freelancers Community (80k+)", "https://www.facebook.com/groups/bdfreelancerscommunity/"),
        ("YouTubers Association Bangladesh (50k+)", "https://www.facebook.com/groups/youtubersbangladesh/"),
        ("Video Editors & Animators BD (30k+)", "https://www.facebook.com/groups/videoeditorsandanimatorsbd/"),
        ("Graphic & Video Editors BD (80k+)", "https://www.facebook.com/groups/graphicandvideoeditorsbd/"),
        ("Digital Marketers & Creators BD (40k+)", "https://www.facebook.com/groups/digitalmarketersbangladesh/"),
        ("Remote Jobs & Freelancers BD (60k+)", "https://www.facebook.com/groups/remotejobsbd/"),
        ("Freelance Jobs Bangladesh (75k+)", "https://www.facebook.com/groups/freelancejobsbd/"),
        ("Content Creators Hub Bangladesh (25k+)", "https://www.facebook.com/groups/contentcreatorshubbd/"),
        ("Wedding Videography & Editors BD (40k+)", "https://www.facebook.com/groups/weddingvideographybd/"),
        ("DaVinci Resolve BD Users (15k+)", "https://www.facebook.com/groups/davinciresolvebd/"),
        ("Premiere Pro BD Community (20k+)", "https://www.facebook.com/groups/premiereprobdcommunity/"),
        ("Upwork & Fiverr Bangladesh (120k+)", "https://www.facebook.com/groups/upworkfiverrbd/"),
        ("Bangladesh IT & Freelance Gigs (50k+)", "https://www.facebook.com/groups/bangladeshitfreelancing/"),
        ("Dhaka Media & Video Editors (20k+)", "https://www.facebook.com/groups/dhakavideoeditors/"),
        ("F-Commerce Video Makers BD (35k+)", "https://www.facebook.com/groups/fcommercevideobd/"),
        # ── 10k+ to 200k+ Global / International High-Paying Client Groups ─
        ("I Need an Editor (100k+)", "https://www.facebook.com/groups/ineedahero/"),
        ("Freelance Videographer Community (150k+)", "https://www.facebook.com/groups/freelancevideographer/"),
        ("Video Editors Worldwide (80k+)", "https://www.facebook.com/groups/videoeditorsworldwide/"),
        ("Adobe Premiere Pro Global (120k+)", "https://www.facebook.com/groups/adobepremierepro/"),
        ("After Effects Global Community (90k+)", "https://www.facebook.com/groups/aftereffects/"),
        ("DaVinci Resolve Video Editors (60k+)", "https://www.facebook.com/groups/davinciresolveusers/"),
        ("YouTube Creators & Editors Hiring (85k+)", "https://www.facebook.com/groups/youtubecreators/"),
        ("YouTube Video Editors Hub (50k+)", "https://www.facebook.com/groups/youtubevideoeditors/"),
        ("Remote Video Editing Jobs (45k+)", "https://www.facebook.com/groups/remotevideoeditingjobs/"),
        ("Freelance Video Editors Network (70k+)", "https://www.facebook.com/groups/freelancevideoeditors/"),
        ("Video Editors Wanted (35k+)", "https://www.facebook.com/groups/videoeditorswanted/"),
        ("Content Creators & Editors (40k+)", "https://www.facebook.com/groups/contentcreatorsandvideoeditors/"),
        ("Video Editors Hub Global (55k+)", "https://www.facebook.com/groups/videoeditorshub/"),
        ("Filmmakers & Video Editors Group (65k+)", "https://www.facebook.com/groups/filmmakersandvideoeditors/"),
        ("Video Editors Community Worldwide (45k+)", "https://www.facebook.com/groups/videoeditorscommunity/"),
        ("Motion Designers Global (55k+)", "https://www.facebook.com/groups/motiondesigners/"),
        ("Short Form Video Editors - Reels/TikTok (35k+)", "https://www.facebook.com/groups/shortformvideoeditors/"),
        ("Reels & Shorts Video Editors (30k+)", "https://www.facebook.com/groups/reelsvideoeditors/"),
        ("TikTok Video Editors for Hire (25k+)", "https://www.facebook.com/groups/tiktokvideoeditors/"),
        ("Talking Head & Podcast Editors (20k+)", "https://www.facebook.com/groups/talkingheadvideoeditors/"),
        ("Faceless & Cash Cow Channel Editors (30k+)", "https://www.facebook.com/groups/cashcowvideoeditors/"),
        ("Documentary Style Video Editors (25k+)", "https://www.facebook.com/groups/documentaryvideoeditors/"),
        ("Iman Gadzhi & Ali Abdaal Style Editors (25k+)", "https://www.facebook.com/groups/imangadzhistyleeditors/"),
        ("Final Cut Pro Users Global (40k+)", "https://www.facebook.com/groups/finalcutprox/")
    ]
    for item in DEFAULT_GROUPS:
        g_name = item[0]
        g_url = item[1]
        prio = item[2] if len(item) > 2 else 0
        clean = g_url.strip()
        if not clean.endswith('/'):
            clean += '/'
        c.execute("""
            INSERT INTO fb_monitored_groups (name, url, active, check_interval_min, priority)
            VALUES (?, ?, 1, 1, ?)
            ON CONFLICT(url) DO UPDATE SET priority=excluded.priority, name=excluded.name
        """, (g_name, clean, prio))

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")


# ── Lead Operations ──────────────────────────────────────────
def insert_lead(lead: dict) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO leads (name, channel, platform, subscribers, email, website,
                           social_json, ai_score, lead_type, status, ai_analysis)
        VALUES (:name, :channel, :platform, :subscribers, :email, :website,
                :social_json, :ai_score, :lead_type, :status, :ai_analysis)
    """, {
        "name":        lead.get("name", ""),
        "channel":     lead.get("channel", ""),
        "platform":    lead.get("platform", "YouTube"),
        "subscribers": lead.get("subscribers", ""),
        "email":       lead.get("email", ""),
        "website":     lead.get("website", ""),
        "social_json": json.dumps(lead.get("social", {})),
        "ai_score":    lead.get("ai_score", 0),
        "lead_type":   lead.get("lead_type", "warm"),
        "status":      "new",
        "ai_analysis": json.dumps(lead.get("ai_analysis", {})),
    })
    lead_id = c.lastrowid
    conn.commit()
    conn.close()
    return lead_id


def get_all_leads(status=None, lead_type=None):
    conn = get_db()
    c = conn.cursor()
    query = "SELECT * FROM leads WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if lead_type:
        query += " AND lead_type = ?"
        params.append(lead_type)
    query += " ORDER BY ai_score DESC"
    rows = c.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_lead_status(lead_id: int, status: str):
    conn = get_db()
    conn.execute("UPDATE leads SET status=?, updated_at=? WHERE id=?",
                 (status, datetime.now().isoformat(), lead_id))
    conn.commit()
    conn.close()


# ── Email Operations ──────────────────────────────────────────
def insert_email(email_data: dict) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO emails (lead_id, to_address, subject, body, template_used,
                            tracking_id, status, campaign_id)
        VALUES (:lead_id, :to_address, :subject, :body, :template_used,
                :tracking_id, :status, :campaign_id)
    """, email_data)
    eid = c.lastrowid
    conn.commit()
    conn.close()
    return eid


def mark_email_sent(email_id: int):
    conn = get_db()
    conn.execute("UPDATE emails SET status='sent', sent_at=? WHERE id=?",
                 (datetime.now().isoformat(), email_id))
    conn.commit()
    conn.close()


def mark_email_opened(tracking_id: str):
    conn = get_db()
    conn.execute("""
        UPDATE emails
        SET status='opened',
            opened_at = COALESCE(opened_at, datetime('now')),
            open_count = open_count + 1
        WHERE tracking_id=?
    """, (tracking_id,))
    conn.commit()
    conn.close()


def mark_email_clicked(tracking_id: str):
    conn = get_db()
    conn.execute("""
        UPDATE emails
        SET status='clicked',
            clicked_at = COALESCE(clicked_at, datetime('now')),
            click_count = click_count + 1
        WHERE tracking_id=?
    """, (tracking_id,))
    conn.commit()
    conn.close()


def mark_email_replied(tracking_id: str):
    conn = get_db()
    conn.execute("""
        UPDATE emails SET status='replied', replied_at=? WHERE tracking_id=?
    """, (datetime.now().isoformat(), tracking_id))
    conn.commit()
    conn.close()


def get_today_email_stats() -> dict:
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            COALESCE(SUM(CASE WHEN status != 'failed' THEN 1 ELSE 0 END), 0) as sent,
            COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as failed,
            COALESCE(SUM(CASE WHEN open_count > 0 THEN 1 ELSE 0 END), 0) as opened,
            COALESCE(SUM(CASE WHEN click_count > 0 THEN 1 ELSE 0 END), 0) as clicked,
            COALESCE(SUM(CASE WHEN status = 'replied' THEN 1 ELSE 0 END), 0) as replied,
            COALESCE(SUM(open_count), 0) as total_opens
        FROM emails
        WHERE date(sent_at) = ?
    """, (today,)).fetchone()
    conn.close()
    if not row:
        return {"total": 0, "sent": 0, "failed": 0, "opened": 0, "clicked": 0, "replied": 0, "total_opens": 0}
    d = dict(row)
    return {k: (v if v is not None else 0) for k, v in d.items()}


def get_all_emails(limit=50):
    conn = get_db()
    rows = conn.execute("""
        SELECT e.*, l.name as lead_name, l.channel
        FROM emails e LEFT JOIN leads l ON e.lead_id = l.id
        ORDER BY e.id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Social Message Operations ──────────────────────────────────
def insert_social_message(data: dict) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO social_messages (lead_id, platform, to_address, message, status)
        VALUES (:lead_id, :platform, :to_address, :message, 'pending')
    """, data)
    mid = c.lastrowid
    conn.commit()
    conn.close()
    return mid


def mark_social_sent(msg_id: int):
    conn = get_db()
    conn.execute("UPDATE social_messages SET status='sent', sent_at=? WHERE id=?",
                 (datetime.now().isoformat(), msg_id))
    conn.commit()
    conn.close()


# ── CRM Pipeline Operations ───────────────────────────────────
PIPELINE_STAGES = ['new_lead', 'outreach_sent', 'email_opened', 'replied', 'meeting_booked', 'deal_closed']

def get_pipeline_board() -> dict:
    """Return all leads grouped by pipeline stage."""
    conn = get_db()
    rows = conn.execute("""
        SELECT l.id, l.name, l.channel, l.email, l.subscribers, l.ai_score,
               l.lead_type, l.website, l.social_json, l.notes,
               COALESCE(l.pipeline_stage, 'new_lead') as stage,
               COALESCE(l.deal_value, 0) as deal_value,
               COALESCE(l.tag, 'warm') as tag,
               l.next_followup, l.updated_at,
               (SELECT COUNT(*) FROM emails e WHERE e.lead_id = l.id) as email_count,
               (SELECT MAX(open_count) FROM emails e WHERE e.lead_id = l.id) as max_opens,
               (SELECT status FROM emails e WHERE e.lead_id = l.id ORDER BY e.id DESC LIMIT 1) as last_email_status
        FROM leads l
        ORDER BY l.ai_score DESC
    """).fetchall()
    conn.close()

    board = {stage: [] for stage in PIPELINE_STAGES}
    for r in rows:
        d = dict(r)
        try:
            d['social'] = json.loads(d.get('social_json') or '{}')
        except Exception:
            d['social'] = {}
        stage = d.get('stage', 'new_lead')
        if stage not in board:
            stage = 'new_lead'
        board[stage].append(d)
    return board


def move_pipeline_stage(lead_id: int, new_stage: str, deal_value: float = None, tag: str = None):
    conn = get_db()
    updates = ["pipeline_stage=?", "updated_at=?"]
    vals = [new_stage, datetime.now().isoformat()]
    if deal_value is not None:
        updates.append("deal_value=?")
        vals.append(deal_value)
    if tag is not None:
        updates.append("tag=?")
        vals.append(tag)
    vals.append(lead_id)
    conn.execute(f"UPDATE leads SET {', '.join(updates)} WHERE id=?", vals)
    # Log activity
    conn.execute(
        "INSERT INTO activity_log (lead_id, action, detail) VALUES (?, ?, ?)",
        (lead_id, 'stage_moved', f'Moved to {new_stage}')
    )
    conn.commit()
    conn.close()


def get_pipeline_stats() -> dict:
    conn = get_db()
    stages = conn.execute("""
        SELECT COALESCE(pipeline_stage,'new_lead') as stage, COUNT(*) as cnt,
               COALESCE(SUM(deal_value),0) as revenue
        FROM leads GROUP BY pipeline_stage
    """).fetchall()
    total_revenue = conn.execute(
        "SELECT COALESCE(SUM(deal_value),0) FROM leads WHERE pipeline_stage='deal_closed'"
    ).fetchone()[0]
    conn.close()
    stage_data = {s: {'count': 0, 'revenue': 0} for s in PIPELINE_STAGES}
    for r in stages:
        s = r['stage'] or 'new_lead'
        if s in stage_data:
            stage_data[s] = {'count': r['cnt'], 'revenue': r['revenue']}
    return {'stages': stage_data, 'total_closed_revenue': total_revenue}


def log_activity(lead_id: int, action: str, detail: str, performed_by: str = 'Admin'):
    conn = get_db()
    conn.execute(
        "INSERT INTO activity_log (lead_id, action, detail, performed_by) VALUES (?,?,?,?)",
        (lead_id, action, detail, performed_by)
    )
    conn.commit()
    conn.close()


def get_lead_activity(lead_id: int) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM activity_log WHERE lead_id=? ORDER BY created_at DESC LIMIT 20",
        (lead_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_lead_tag(lead_id: int, tag: str):
    conn = get_db()
    conn.execute("UPDATE leads SET tag=?, updated_at=? WHERE id=?",
                 (tag, datetime.now().isoformat(), lead_id))
    conn.commit()
    conn.close()


def update_lead_notes(lead_id: int, notes: str):
    conn = get_db()
    conn.execute("UPDATE leads SET notes=?, updated_at=? WHERE id=?",
                 (notes, datetime.now().isoformat(), lead_id))
    conn.commit()
    conn.close()


# ── Stats Operations ──────────────────────────────────────────
def upsert_daily_stats(updates: dict):
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    conn.execute("""
        INSERT INTO daily_stats (date) VALUES (?) ON CONFLICT(date) DO NOTHING
    """, (today,))
    for col, val in updates.items():
        conn.execute(f"UPDATE daily_stats SET {col} = {col} + ? WHERE date = ?",
                     (val, today))
    conn.commit()
    conn.close()


# Auto-initialize database tables on import
try:
    init_db()
except Exception as e:
    print(f"[DB Warning] Could not auto-init DB on load: {e}")

if __name__ == "__main__":
    init_db()
    print("[DB] Tables created successfully!")


# ── Facebook Radar Operations ──────────────────────────────────
def get_all_fb_groups() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM fb_monitored_groups ORDER BY priority DESC, id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_fb_group(name: str, url: str, interval: int = 2, priority: int = 0) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO fb_monitored_groups (name, url, check_interval_min, priority)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET priority=excluded.priority, name=excluded.name
    """, (name, url, interval, priority))
    gid = c.lastrowid
    conn.commit()
    conn.close()
    return gid
    conn.commit()
    conn.close()
    return gid

def delete_fb_group(group_id: int):
    conn = get_db()
    conn.execute("DELETE FROM fb_monitored_groups WHERE id = ?", (group_id,))
    conn.commit()
    conn.close()

def toggle_fb_group(group_id: int) -> int:
    conn = get_db()
    row = conn.execute("SELECT active FROM fb_monitored_groups WHERE id = ?", (group_id,)).fetchone()
    if row:
        new_active = 0 if row['active'] == 1 else 1
        conn.execute("UPDATE fb_monitored_groups SET active = ? WHERE id = ?", (new_active, group_id))
        conn.commit()
        conn.close()
        return new_active
    conn.close()
    return 0

def get_fb_alerts(limit: int = 50) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM fb_job_alerts ORDER BY id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def is_fb_post_seen(post_id: str) -> bool:
    conn = get_db()
    row = conn.execute("SELECT id FROM fb_job_alerts WHERE post_id = ?", (post_id,)).fetchone()
    conn.close()
    return bool(row)

def insert_fb_alert(data: dict) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO fb_job_alerts (
            group_id, group_name, post_id, author_name, post_url, content, image_url,
            is_hiring, client_name, job_type, budget, contact_phone, contact_email,
            contact_whatsapp, contact_telegram, confidence_score, ai_summary,
            telegram_sent, telegram_sent_at
        ) VALUES (
            :group_id, :group_name, :post_id, :author_name, :post_url, :content, :image_url,
            :is_hiring, :client_name, :job_type, :budget, :contact_phone, :contact_email,
            :contact_whatsapp, :contact_telegram, :confidence_score, :ai_summary,
            :telegram_sent, :telegram_sent_at
        )
    """, data)
    aid = c.lastrowid
    # Increment total_jobs_found on group
    if data.get('group_id'):
        c.execute("UPDATE fb_monitored_groups SET total_jobs_found = total_jobs_found + 1 WHERE id = ?", (data['group_id'],))
    conn.commit()
    conn.close()
    return aid

def update_fb_group_scan_stats(group_id: int, posts_scanned: int):
    conn = get_db()
    conn.execute("""
        UPDATE fb_monitored_groups
        SET total_posts_scanned = total_posts_scanned + ?,
            last_checked_at = datetime('now')
        WHERE id = ?
    """, (posts_scanned, group_id))
    conn.commit()
    conn.close()
