# ============================================================
# ZENTIC MEDIA — CLIENT HUNTING AUTOMATION
# database.py — SQLite DB with all tables
# ============================================================

import os
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
            country     TEXT DEFAULT '',
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

    # Ensure country column exists if table was previously created
    for col, col_type in [
        ("country", "TEXT DEFAULT ''"),
        ("avatar", "TEXT DEFAULT ''"),
        ("handle", "TEXT DEFAULT ''"),
        ("channel_url", "TEXT DEFAULT ''"),
        ("total_views", "TEXT DEFAULT ''"),
        ("videos", "INTEGER DEFAULT 0"),
        ("avg_views", "TEXT DEFAULT ''"),
        ("last_upload", "TEXT DEFAULT 'Recently'"),
        ("upload_freq", "TEXT DEFAULT '2x/week'"),
        ("created", "TEXT DEFAULT 'Oct 2022'"),
        ("description", "TEXT DEFAULT ''"),
    ]:
        try:
            c.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type}")
        except Exception:
            pass

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

    try:
        c.execute("ALTER TABLE fb_job_alerts ADD COLUMN author_url TEXT")
    except Exception:
        pass

    try:
        c.execute("ALTER TABLE fb_job_alerts ADD COLUMN platform TEXT DEFAULT 'facebook'")
    except Exception:
        pass

    # ── User Profile Table ───────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL,
            nickname            TEXT DEFAULT 'Rakib',
            location            TEXT DEFAULT 'Kalai, Joypurhat, Bangladesh',
            education           TEXT,
            role                TEXT,
            agency_name         TEXT DEFAULT 'Zentic Media',
            agency_former_name  TEXT DEFAULT 'Max Grow Up',
            website             TEXT DEFAULT 'https://zenticmedia.com',
            team_members        TEXT,
            services            TEXT,
            tools_stack         TEXT,
            active_projects     TEXT,
            galaxy_roles        TEXT,
            bio_raw             TEXT,
            updated_at          TEXT DEFAULT (datetime('now'))
        )
    """)

    # Seed or update user profile with Rakibul Hasan's official details
    c.execute("SELECT COUNT(*) FROM user_profile")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO user_profile (
                name, nickname, location, education, role, agency_name, agency_former_name,
                website, team_members, services, tools_stack, active_projects, galaxy_roles, bio_raw
            ) VALUES (
                :name, :nickname, :location, :education, :role, :agency_name, :agency_former_name,
                :website, :team_members, :services, :tools_stack, :active_projects, :galaxy_roles, :bio_raw
            )
        """, {
            "name": "রাকিবুল হাসান (রাকিব)",
            "nickname": "Rakib",
            "location": "কালাই, জয়পুরহাট, বাংলাদেশ (Kalai, Joypurhat, Bangladesh)",
            "education": "সরকারি সাঈদ আলতাফুন্নেছা কলেজ থেকে ২০২৫ সালে এইচএসসি সম্পন্ন করে বর্তমানে বি.এ. (অনার্স) প্রথম বর্ষে অধ্যয়নরত",
            "role": "Founder, CEO & Lead Video Editor (Adobe After Effects & Premiere Pro Specialist)",
            "agency_name": "জেন্টিক মিডিয়া (Zentic Media)",
            "agency_former_name": "Max Grow Up",
            "website": "https://zenticmedia.com",
            "team_members": "ফয়সাল আহমেদ নাফিজসহ দক্ষ টিম মেম্বাররা (কঠোর জিরো-ডেডলাইন পলিসি ও অরিজিনাল পোর্টফোলিও কম্পিলেশন স্ট্যান্ডার্ড)",
            "services": "ভিডিও পোস্ট-প্রোডাকশন ও মোশন ডিজাইন, ওয়েব ডেভেলপমেন্ট ও ডিজাইন, বিজনেস অটোমেশন সলিউশনস (n8n এবং কাস্টম পাইথন স্ক্রিপ্টিং)",
            "tools_stack": "ভিএস কোড (VS Code), কার্সর আইডি (Cursor IDE - OpenRouter API), Adobe After Effects, Adobe Premiere Pro, Shadow Studio 3, FX Console, Presetify, JerryFlow V2, Motion Bro",
            "active_projects": "১. গ্যালাক্সি এআই (Galaxy AI): React, Electron এবং SQLite আর্কিটেকচারের ডেস্কটপ অ্যাসিস্ট্যান্ট ও সিস্টেম ড্যাশবোর্ড। ২. অটোমেশন: n8n এবং HTTP Request দিয়ে রিয়েল-টাইম ফেসবুক-টু-টেলিগ্রাম ভিডিও এডিটর হায়ারিং স্ক্র্যাপার।",
            "galaxy_roles": "ওয়েব ডিজাইন, ম্যানেজমেন্ট এবং এআই অটোমেশন Specialist (গ্যালাক্সি টিভি এবং গ্যালাক্সি ল্যাবরেটরিজ ইউনানী)",
            "bio_raw": """১. আপনার পরিচয় ও মূল পেশা (Personal Profile)
নাম: রাকিবুল হাসান (রাকিব)
বাসস্থান: কালাই, জয়পুরহাট, বাংলাদেশ
শিক্ষা: সরকারি সাঈদ আলতাফুন্নেছা কলেজ থেকে ২০২৫ সালে এইচএসসি সম্পন্ন করে বর্তমানে বি.এ. (অনার্স) প্রথম বর্ষে অধ্যয়নরত।
মূল পেশা ও দক্ষতা:
আপনি জেন্টিক মিডিয়া (Zentic Media)-এর প্রতিষ্ঠাতা, প্রধান নির্বাহী কর্মকর্তা (CEO) এবং লিড ভিডিও এডিটর। ভিডিও এডিটিংয়ের ক্ষেত্রে আপনি মূলত Adobe After Effects এবং Adobe Premiere Pro ব্যবহার করে থাকেন।
পাশাপাশি, আপনি গ্যালাক্সি টিভি এবং গ্যালাক্সি ল্যাবরেটরিজ (ইউনানী)-এ ওয়েব ডিজাইন, ম্যানেজমেন্ট এবং এআই অটোমেশন Specialist হিসেবে কাজ করছেন।
২. আপনার এজেন্সি: জেন্টিক মিডিয়া (Zentic Media)
আপনার ক্রিয়েটিভ এজেন্সিটির নাম জেন্টিক মিডিয়া (পূর্বে এটি Max Grow Up নামে পরিচিত ছিল)। এটি একটি পূর্ণাঙ্গ ডিজিটাল সলিউশন ও ক্রিয়েটিভ এজেন্সি।
অফিসিয়াল ওয়েবসাইট: https://zenticmedia.com
এজেন্সি টিম ও কোলাবরেশন: আপনার এই এজেন্সিতে ফয়সাল আহমেদ নাফিজসহ দক্ষ টিম মেম্বাররা কাজ করেন। ডিরেক্টরি ম্যানেজমেন্ট, জিরো-ডেডলাইন পলিসি এবং অরিজিনাল পোর্টফোলিও কম্পিলেশনের ক্ষেত্রে আপনারা অত্যন্ত কঠোর ও সুশৃঙ্খল নিয়ম বজায় রাখেন।
এজেন্সির প্রধান সেবাসমূহ:
ভিডিও পোস্ট-প্রোডাকশন ও মোশন ডিজাইন
ওয়েব ডেভেলপমেন্ট ও ডিজাইন
বিজনেস অটোমেশন সলিউশনস (n8n এবং কাস্টম পাইথন স্ক্রিপ্টিংয়ের মাধ্যমে অটোমেশন ওয়ার্কফ্লো তৈরি)
৩. প্রযুক্তিগত ও অটোমেশন কর্মযজ্ঞ (Workflows & Projects)
টুলস ও টেক স্ট্যাক: কাজের জন্য আপনি ভিএস কোড (VS Code), কার্সর আইডি (Cursor IDE - কাস্টম ওপেনরাউটার এপিআই ইন্টিগ্রেশনসহ), এবং বিভিন্ন আফটার ইফেক্টস এক্সটেনশন ও প্লাগইন (যেমন: Shadow Studio 3, FX Console, Presetify, JerryFlow V2, Motion Bro ইত্যাদি) ব্যবহার করেন।
চলমান প্রজেক্টসমূহ:
গ্যালাক্সি এআই (Galaxy AI): React, Electron এবং SQLite আর্কিটেকচারের ওপর ভিত্তি করে একটি কাস্টম ডেস্কটপ অ্যাসিস্ট্যান্ট ও সিস্টেম ড্যাশবোর্ড তৈরির কাজ করছেন, যা লোকাল ফাইল ইনডেক্সিং এবং ব্রাউজার ম্যানিপুলেশন হ্যান্ডেল করবে।
অটোমেশন ও স্ক্রিপ্টিং: n8n এবং HTTP Request নোড ব্যবহার করে রিয়েল-টাইম ফেসবুক-টু-টেলিগ্রাম স্ক্র্যাপিং স্ক্রিপ্ট তৈরি করছেন, যা টার্গেটেড কমিউনিটি গ্রুপ থেকে ভিডিও এডিটর হারিং পোস্টগুলো ফিল্টার করে সংগ্রহ করে।"""
        })

    # Seed curated Facebook video editing groups automatically
    DEFAULT_GROUPS = [
        # ── USER REQUESTED VIP HIGH PRIORITY GROUPS (Priority 10) ─────
        ("BD Freelancers Community", "https://www.facebook.com/groups/bdfreelancerscommunity/", 10),
        ("Video Editor Jobs Worldwide", "https://www.facebook.com/groups/videoeditorjobs/", 10),
        ("Video Editing BD Hub #563", "https://www.facebook.com/groups/563297302882280/", 10),
        ("Freelance Editors BD #786", "https://www.facebook.com/groups/786509760938079/", 10),
        ("Video Editors & Animators BD #131", "https://www.facebook.com/groups/1319176705676218/", 10),
        ("Video Editors Community #470", "https://www.facebook.com/groups/470532055541674/", 10),
        ("Creative Editors Network #497", "https://www.facebook.com/groups/497041285819747/", 10),
        ("Video Editing Zone #337", "https://www.facebook.com/groups/337481355732194/", 10),
        ("Video Creators Hub #838", "https://www.facebook.com/groups/838048813733900/", 10),
        ("Video Editing Jobs #158", "https://www.facebook.com/groups/1585573421895994/", 10),
        ("I Need a Video Editor", "https://www.facebook.com/groups/ineedavideoeditor/", 10),
        ("EditVerse Freelance Hub", "https://www.facebook.com/groups/editverse.freelancehub/", 10),
        ("Free Video Editor Group", "https://www.facebook.com/groups/freevideoeditorgroup/", 10),
        ("Freelance Video Editors #153", "https://www.facebook.com/groups/1535727757545719/", 10),
        ("Video Editor Hiring BD #132", "https://www.facebook.com/groups/1326223411530920/", 10),
        ("Billi4You Video Editors", "https://www.facebook.com/groups/billi4you.video.editors/", 10),
        ("VIP: Video Editors Bangladesh BD", "https://www.facebook.com/groups/VideoEditorsBangladesh.BD/", 10),
        ("EvokeVerse Video Editors", "https://www.facebook.com/groups/evokeverse/", 10),
        ("Video Editors Global #162", "https://www.facebook.com/groups/1624224204424600/", 10),
        ("Video Editing Jobs Hub #241", "https://www.facebook.com/groups/2417162128540008/", 10),
        ("Freelance Video Editor", "https://www.facebook.com/groups/freelancevideoeditor/", 10),
        ("Video Creators & Editors #729", "https://www.facebook.com/groups/729888311361914/", 10),
        ("Video Editors Community #632", "https://www.facebook.com/groups/6320719404694598/", 10),
        ("Premiere & AE Editors #594", "https://www.facebook.com/groups/594778777333016/", 10),
        ("Freelance Video Editors Worldwide", "https://www.facebook.com/groups/freelancevideoeditors/", 10),
        ("Video Editing Hub BD #947", "https://www.facebook.com/groups/947928056999454/", 10),
        ("Video Editors Network #386", "https://www.facebook.com/groups/386403410983677/", 10),
        ("Professional Video Editors Global", "https://www.facebook.com/groups/ProfessionalVideoEditors/", 10),
        ("Video Editing Masterclass BD #112", "https://www.facebook.com/groups/1126963997314568/", 10),
        # ── 4 VIP TOP PRIORITY GROUPS (Always Scanned First) ──────
        ("VIP: Video Editing Bangladesh", "https://www.facebook.com/groups/bangladeshyoututbeandfacebookcommunity/", 10),
        ("VIP: Video Editor - VFX Bangladesh", "https://www.facebook.com/groups/videoeditorhire/", 10),
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
        clean_no_slash = clean.rstrip('/')
        c.execute("""
            INSERT INTO fb_monitored_groups (name, url, active, check_interval_min, priority)
            VALUES (?, ?, 1, 1, ?)
            ON CONFLICT(url) DO UPDATE SET priority=excluded.priority, name=excluded.name
        """, (g_name, clean, prio))
        c.execute("""
            UPDATE fb_monitored_groups 
            SET priority = MAX(priority, ?), name = ?
            WHERE url = ? OR url = ?
        """, (prio, g_name, clean, clean_no_slash))

    # Pre-seed active hiring and community posts so dashboard always has posts for every group
    c.execute("SELECT COUNT(*) FROM fb_job_alerts")
    current_count = c.fetchone()[0]
    seed_json_path = os.path.join(os.path.dirname(__file__), "seed_fb_alerts.json")
    if current_count < 100 and os.path.exists(seed_json_path):
        try:
            with open(seed_json_path, "r", encoding="utf-8") as f:
                seed_data = json.load(f)

            # Build group id lookup map
            groups_rows = c.execute("SELECT id, name, url FROM fb_monitored_groups").fetchall()
            name_to_gid = {r[1].lower().strip(): r[0] for r in groups_rows if r[1]}

            for a in seed_data:
                gid = a.get("group_id")
                if not gid:
                    gn = (a.get("group_name") or "").lower().strip()
                    if gn in name_to_gid:
                        gid = name_to_gid[gn]
                    else:
                        for g_name_low, g_id in name_to_gid.items():
                            if g_name_low in gn or gn in g_name_low:
                                gid = g_id
                                break

                c.execute("""
                    INSERT OR IGNORE INTO fb_job_alerts (
                        group_id, group_name, post_id, author_name, author_url, post_url, content, image_url,
                        is_hiring, client_name, job_type, budget, contact_phone, contact_email,
                        contact_whatsapp, contact_telegram, confidence_score, ai_summary,
                        telegram_sent, telegram_sent_at, created_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?
                    )
                """, (
                    gid, a.get("group_name"), a.get("post_id"), a.get("author_name", "Facebook User"),
                    a.get("author_url", ""), a.get("post_url", ""), a.get("content", ""), a.get("image_url", ""),
                    a.get("is_hiring", 0), a.get("client_name", a.get("author_name")), a.get("job_type", "Video Editor"),
                    a.get("budget", ""), a.get("contact_phone", ""), a.get("contact_email", ""),
                    a.get("contact_whatsapp", ""), a.get("contact_telegram", ""), a.get("confidence_score", 90),
                    a.get("ai_summary", a.get("content", "")[:200]), a.get("telegram_sent", 0),
                    a.get("telegram_sent_at"), a.get("created_at") or datetime.now().isoformat()
                ))
            print(f"[DB] Seeded {len(seed_data)} FB posts across groups.")
        except Exception as e:
            print(f"[DB] Error seeding alerts from json: {e}")

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")


# ── Lead Operations ──────────────────────────────────────────
def insert_lead(lead: dict) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO leads (name, channel, platform, subscribers, email, website, country,
                           social_json, ai_score, lead_type, status, ai_analysis,
                           avatar, handle, channel_url, total_views, videos, avg_views,
                           last_upload, upload_freq, created, description)
        VALUES (:name, :channel, :platform, :subscribers, :email, :website, :country,
                :social_json, :ai_score, :lead_type, :status, :ai_analysis,
                :avatar, :handle, :channel_url, :total_views, :videos, :avg_views,
                :last_upload, :upload_freq, :created, :description)
    """, {
        "name":        lead.get("name", ""),
        "channel":     lead.get("channel", ""),
        "platform":    lead.get("platform", "YouTube"),
        "subscribers": str(lead.get("subscribers", "")),
        "email":       lead.get("email", ""),
        "website":     lead.get("website", ""),
        "country":     lead.get("country", ""),
        "social_json": json.dumps(lead.get("social", {})),
        "ai_score":    int(lead.get("ai_score", 0) or 0),
        "lead_type":   lead.get("lead_type", "warm"),
        "status":      lead.get("status", "new"),
        "ai_analysis": json.dumps(lead.get("ai_analysis", {})),
        "avatar":      lead.get("avatar", ""),
        "handle":      lead.get("handle", ""),
        "channel_url": lead.get("channel_url", lead.get("website", "")),
        "total_views": str(lead.get("total_views", "")),
        "videos":      int(lead.get("videos", 0) or 0),
        "avg_views":   str(lead.get("avg_views", "")),
        "last_upload": lead.get("last_upload", "Recently"),
        "upload_freq": lead.get("upload_freq", "2x/week"),
        "created":     lead.get("created", "Oct 2022"),
        "description": lead.get("description", "")
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
    leads = []
    for r in rows:
        d = dict(r)
        if "social_json" in d and d["social_json"]:
            try:
                d["social"] = json.loads(d["social_json"])
            except Exception:
                d["social"] = {}
        else:
            d["social"] = {}
        if "ai_analysis" in d and isinstance(d["ai_analysis"], str) and d["ai_analysis"]:
            try:
                d["ai_analysis"] = json.loads(d["ai_analysis"])
            except Exception:
                pass
        leads.append(d)
    return leads


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

def get_fb_alerts(limit: int = 1000, platform: str = None, is_hiring: int = None) -> list:
    conn = get_db()
    query = "SELECT * FROM fb_job_alerts WHERE 1=1"
    params = []
    if platform and platform != "all":
        query += " AND platform = ?"
        params.append(platform)
    if is_hiring is not None:
        query += " AND is_hiring = ?"
        params.append(is_hiring)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def generate_fb_post_id(post_url: str = "", content: str = "") -> str:
    """
    Generates a 100% deterministic, permanent post ID.
    Never uses Python's non-deterministic hash().
    """
    import hashlib, re
    # 1. If direct post URL has numeric FB ID, use that
    if post_url:
        m = re.search(r'/(?:posts|permalink|videos)/(\d+)', post_url)
        if m:
            return f"fb_num_{m.group(1)}"
        m2 = re.search(r'story_fbid=(\d+)', post_url)
        if m2:
            return f"fb_num_{m2.group(1)}"

    # 2. Deterministic hash of normalized content
    norm_txt = " ".join((content or "").strip().lower().split())
    if len(norm_txt) > 20:
        md5_sig = hashlib.md5(norm_txt.encode('utf-8')).hexdigest()[:16]
        return f"fb_{md5_sig}"

    # 3. Fallback to clean URL hash
    clean_u = (post_url or "").split("?")[0].rstrip("/").lower()
    return f"fb_url_{hashlib.md5(clean_u.encode('utf-8')).hexdigest()[:16]}"


def is_fb_post_seen(post_id: str = "", content: str = "", post_url: str = "") -> bool:
    """
    Multi-layer check to ensure identical posts or comments are NEVER considered new:
    1. By deterministic post_id
    2. By clean direct post URL (/posts/123/ or /permalink/123/)
    3. By normalized content prefix
    """
    conn = get_db()
    c = conn.cursor()

    # Check 1: Exact post_id
    if post_id:
        row = c.execute("SELECT id FROM fb_job_alerts WHERE post_id = ?", (post_id,)).fetchone()
        if row:
            conn.close()
            return True

    # Check 2: Direct Post URL (without query params)
    clean_purl = (post_url or "").split("?")[0].rstrip("/")
    if clean_purl and any(x in clean_purl for x in ["/posts/", "/permalink/", "story_fbid="]):
        row = c.execute("SELECT id FROM fb_job_alerts WHERE post_url LIKE ?", (f"{clean_purl}%",)).fetchone()
        if row:
            conn.close()
            return True

    # Check 3: Content exact or high-similarity match
    if content and len(content.strip()) > 25:
        norm_txt = " ".join(content.strip().split())
        prefix = norm_txt[:80]
        row = c.execute("SELECT id FROM fb_job_alerts WHERE content LIKE ?", (f"%{prefix}%",)).fetchone()
        if row:
            conn.close()
            return True

    conn.close()
    return False


def insert_fb_alert(data: dict) -> int:
    conn = get_db()
    c = conn.cursor()
    if "author_url" not in data:
        data["author_url"] = ""
    if "platform" not in data:
        data["platform"] = "facebook"

    # Generate deterministic post_id if missing or non-deterministic
    pid = data.get("post_id", "")
    content = data.get("content", "")
    post_url = data.get("post_url", "")
    if not pid or (len(pid) < 5 or not any(pid.startswith(p) for p in ["fb_num_", "fb_url_", "fb_", "rd_", "ro_"])):
        pid = generate_fb_post_id(post_url, content)
        data["post_id"] = pid

    # Hard de-duplication guard: if seen, return existing ID without duplicate insert
    clean_purl = (post_url or "").split("?")[0].rstrip("/")
    is_direct = bool(clean_purl and any(x in clean_purl for x in ["/posts/", "/permalink/", "story_fbid=", "/comments/", "/remote-jobs/"]))

    if is_direct:
        existing = c.execute("SELECT id FROM fb_job_alerts WHERE post_url LIKE ?", (f"{clean_purl}%",)).fetchone()
        if existing:
            conn.close()
            return existing[0]

    if content and len(content.strip()) > 30:
        prefix = " ".join(content.strip().split())[:80]
        existing = c.execute("SELECT id FROM fb_job_alerts WHERE content LIKE ?", (f"%{prefix}%",)).fetchone()
        if existing:
            conn.close()
            return existing[0]

    if pid:
        existing = c.execute("SELECT id FROM fb_job_alerts WHERE post_id = ?", (pid,)).fetchone()
        if existing:
            conn.close()
            return existing[0]

    c.execute("""
        INSERT INTO fb_job_alerts (
            group_id, group_name, post_id, author_name, author_url, post_url, content, image_url,
            is_hiring, client_name, job_type, budget, contact_phone, contact_email,
            contact_whatsapp, contact_telegram, confidence_score, ai_summary,
            telegram_sent, telegram_sent_at, platform
        ) VALUES (
            :group_id, :group_name, :post_id, :author_name, :author_url, :post_url, :content, :image_url,
            :is_hiring, :client_name, :job_type, :budget, :contact_phone, :contact_email,
            :contact_whatsapp, :contact_telegram, :confidence_score, :ai_summary,
            :telegram_sent, :telegram_sent_at, :platform
        )
    """, data)
    aid = c.lastrowid
    # Increment total_jobs_found on group if hiring
    if data.get('group_id') and data.get('is_hiring') == 1:
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


# ── User Profile Operations ──────────────────────────────────
def get_user_profile() -> dict:
    """Retrieve Rakibul Hasan's profile from database."""
    conn = get_db()
    c = conn.cursor()
    row = c.execute("SELECT * FROM user_profile ORDER BY id ASC LIMIT 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return {}


def update_user_profile(data: dict) -> bool:
    """Update user profile in database."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE user_profile SET
            name = :name,
            nickname = :nickname,
            location = :location,
            education = :education,
            role = :role,
            agency_name = :agency_name,
            agency_former_name = :agency_former_name,
            website = :website,
            team_members = :team_members,
            services = :services,
            tools_stack = :tools_stack,
            active_projects = :active_projects,
            galaxy_roles = :galaxy_roles,
            bio_raw = :bio_raw,
            updated_at = datetime('now')
        WHERE id = 1
    """, data)
    conn.commit()
    conn.close()
    return True
