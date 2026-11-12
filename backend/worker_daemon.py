# ============================================================
# ZENTIC MEDIA — 24/7 AUTONOMOUS VPS LEAD HUNTER DAEMON
# Runs continuously 24/7/365 on VPS without requiring PC
# Monitors Facebook Groups + Reddit + RemoteOK in infinite loop
# ============================================================

import os
import sys
import time
import json
import traceback
from datetime import datetime
from typing import List, Dict, Any

# Ensure backend directory is in python path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from config import cfg
from database import (
    get_all_fb_groups, insert_fb_alert, is_fb_post_seen,
    update_fb_group_scan_stats, get_db, generate_fb_post_id
)
from fb_group_monitor import (
    scrape_facebook_group_posts, classify_fb_post_with_ai,
    is_post_fresh
)
from multi_platform_hunter import (
    scrape_reddit_subreddits, scrape_remoteok_video_jobs,
    alert_international_job
)
from telegram_bot import alert_fb_hiring_post, send_telegram

# ── Global Worker Stats ──────────────────────────────────────
WORKER_STATE = {
    "is_running": False,
    "start_time": None,
    "last_cycle_time": None,
    "cycles_completed": 0,
    "total_posts_scanned": 0,
    "total_hiring_leads_found": 0,
    "total_telegram_sent": 0,
    "last_error": None
}

def get_worker_status() -> dict:
    """Returns current status of 24/7 background worker."""
    st = dict(WORKER_STATE)
    if st["start_time"]:
        uptime_secs = (datetime.now() - st["start_time"]).total_seconds()
        st["uptime_human"] = f"{int(uptime_secs // 3600)}h {int((uptime_secs % 3600) // 60)}m"
    else:
        st["uptime_human"] = "Not started"
    return st


def run_single_hunter_cycle():
    """
    Executes one complete hunting cycle across all platforms:
    1. Top VIP & Active Facebook Groups
    2. Creator Reddit Subreddits
    3. RemoteOK & Global Creative Job Boards
    """
    WORKER_STATE["last_cycle_time"] = datetime.now().isoformat()
    WORKER_STATE["cycles_completed"] += 1
    cycle_num = WORKER_STATE["cycles_completed"]

    print(f"\n{'='*60}")
    print(f"🚀 [24/7 VPS HUNTER] Starting Cycle #{cycle_num} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # ──────────────────────────────────────────────────────────
    # 1. FACEBOOK GROUPS HUNTING
    # ──────────────────────────────────────────────────────────
    try:
        conn = get_db()
        c = conn.cursor()
        # Scan priority groups first, max 20 per cycle to avoid high load
        c.execute("""
            SELECT id, name, url, priority 
            FROM fb_monitored_groups 
            WHERE active = 1 
            ORDER BY priority DESC, id ASC 
            LIMIT 20
        """)
        groups = [dict(r) for r in c.fetchall()]
        conn.close()

        print(f"[Cycle #{cycle_num}] Scanning {len(groups)} top Facebook groups...")

        for g in groups:
            gid = g["id"]
            gname = g["name"]
            gurl = g["url"]

            try:
                # Limit 6 posts per group for fast, lightweight incremental scraping
                posts = scrape_facebook_group_posts(gurl, limit=6)
                WORKER_STATE["total_posts_scanned"] += len(posts)
                update_fb_group_scan_stats(gid, len(posts))

                for p in posts:
                    txt = p["content"]
                    pid = p["post_id"]
                    purl = p["post_url"]

                    # De-duplication check: Skip if already seen
                    if is_fb_post_seen(pid, txt, purl):
                        continue

                    # Strict 5-hour freshness filter for hiring alerts
                    fresh_5h = is_post_fresh(txt, max_hours=5)

                    # Strict AI intent classification (buyer vs freelancer self-promo)
                    ai_res = classify_fb_post_with_ai(txt, p["author_name"], gname)
                    is_hiring = 1 if (fresh_5h and ai_res.get("is_hiring")) else 0

                    alert_data = {
                        "group_id": gid,
                        "group_name": gname,
                        "post_id": pid,
                        "author_name": p["author_name"],
                        "author_url": p.get("author_url", ""),
                        "post_url": purl,
                        "content": txt,
                        "image_url": p.get("image_url", ""),
                        "is_hiring": is_hiring,
                        "client_name": ai_res.get("client_name", p["author_name"]) if is_hiring else p["author_name"],
                        "job_type": ai_res.get("job_type", "Video Editor") if is_hiring else "Community Post",
                        "budget": ai_res.get("budget", "Negotiable") if is_hiring else "",
                        "contact_phone": ai_res.get("contact_phone", "") if is_hiring else "",
                        "contact_email": ai_res.get("contact_email", "") if is_hiring else "",
                        "contact_whatsapp": ai_res.get("contact_whatsapp", "") if is_hiring else "",
                        "contact_telegram": ai_res.get("contact_telegram", "") if is_hiring else "",
                        "confidence_score": ai_res.get("confidence_score", 95) if is_hiring else 0,
                        "ai_summary": ai_res.get("ai_summary", txt[:200]),
                        "telegram_sent": 0,
                        "telegram_sent_at": None,
                        "platform": "facebook"
                    }

                    if is_hiring:
                        sent_ok = alert_fb_hiring_post(alert_data)
                        if sent_ok:
                            alert_data["telegram_sent"] = 1
                            alert_data["telegram_sent_at"] = datetime.now().isoformat()
                            WORKER_STATE["total_telegram_sent"] += 1
                        WORKER_STATE["total_hiring_leads_found"] += 1
                        print(f"  🎯 [FB HIRING ALERT SENT]: {alert_data['client_name']} ({alert_data['job_type']}) - {gname}")

                    insert_fb_alert(alert_data)

            except Exception as ge:
                print(f"[Cycle #{cycle_num}] Error scanning FB group {gname}: {ge}")

            # 2 second pause between groups
            time.sleep(2)

    except Exception as fe:
        print(f"[Cycle #{cycle_num}] Facebook scan step error: {fe}")

    # ──────────────────────────────────────────────────────────
    # 2. REDDIT SUBREDDITS HUNTING
    # ──────────────────────────────────────────────────────────
    try:
        print(f"\n[Cycle #{cycle_num}] Scanning creator Reddit subreddits...")
        reddit_posts = scrape_reddit_subreddits(max_posts_per_sub=8)
        WORKER_STATE["total_posts_scanned"] += len(reddit_posts)

        for p in reddit_posts:
            p_url = p["post_url"]
            content = p["content"]
            auth = p["author_name"]
            grp = p["group_name"]

            if is_fb_post_seen("", content, p_url):
                continue

            fresh = is_post_fresh(content, max_hours=12)
            ai_res = classify_fb_post_with_ai(content, auth, grp)
            is_h = 1 if (fresh and ai_res.get("is_hiring")) else 0

            alert_data = {
                "group_id": None,
                "group_name": grp,
                "post_id": generate_fb_post_id(p_url, content),
                "author_name": auth,
                "author_url": p.get("author_url", ""),
                "post_url": p_url,
                "content": content,
                "image_url": "",
                "is_hiring": is_h,
                "client_name": auth,
                "job_type": ai_res.get("job_type", "Video Editor"),
                "budget": ai_res.get("budget", "Negotiable (USD)"),
                "contact_phone": "",
                "contact_email": "",
                "contact_whatsapp": "",
                "contact_telegram": "",
                "confidence_score": 95 if is_h else 20,
                "ai_summary": content[:220],
                "telegram_sent": 0,
                "telegram_sent_at": None,
                "platform": "reddit"
            }

            if is_h:
                sent_ok = alert_international_job(alert_data)
                if sent_ok:
                    alert_data["telegram_sent"] = 1
                    alert_data["telegram_sent_at"] = datetime.now().isoformat()
                    WORKER_STATE["total_telegram_sent"] += 1
                WORKER_STATE["total_hiring_leads_found"] += 1
                print(f"  🎯 [REDDIT HIRING ALERT SENT]: {auth} ({alert_data['job_type']}) - {grp}")

            insert_fb_alert(alert_data)

    except Exception as re:
        print(f"[Cycle #{cycle_num}] Reddit scan step error: {re}")

    # ──────────────────────────────────────────────────────────
    # 3. REMOTEOK GLOBAL JOBS HUNTING
    # ──────────────────────────────────────────────────────────
    try:
        print(f"\n[Cycle #{cycle_num}] Checking RemoteOK for video editor jobs...")
        remote_posts = scrape_remoteok_video_jobs(limit=10)
        WORKER_STATE["total_posts_scanned"] += len(remote_posts)

        for p in remote_posts:
            p_url = p["post_url"]
            content = p["content"]
            company = p["author_name"]
            grp = p["group_name"]

            if is_fb_post_seen("", content, p_url):
                continue

            alert_data = {
                "group_id": None,
                "group_name": grp,
                "post_id": generate_fb_post_id(p_url, content),
                "author_name": company,
                "author_url": p.get("author_url", ""),
                "post_url": p_url,
                "content": content,
                "image_url": "",
                "is_hiring": 1,
                "client_name": company,
                "job_type": "Video Editor",
                "budget": p.get("budget", "Negotiable (USD)"),
                "contact_phone": "",
                "contact_email": "",
                "contact_whatsapp": "",
                "contact_telegram": "",
                "confidence_score": 98,
                "ai_summary": content[:220],
                "telegram_sent": 0,
                "telegram_sent_at": None,
                "platform": "remoteok"
            }

            sent_ok = alert_international_job(alert_data)
            if sent_ok:
                alert_data["telegram_sent"] = 1
                alert_data["telegram_sent_at"] = datetime.now().isoformat()
                WORKER_STATE["total_telegram_sent"] += 1
            WORKER_STATE["total_hiring_leads_found"] += 1
            print(f"  🎯 [REMOTEOK HIRING ALERT SENT]: {company}")

            insert_fb_alert(alert_data)

    except Exception as ro_err:
        print(f"[Cycle #{cycle_num}] RemoteOK scan step error: {ro_err}")

    print(f"\n[Cycle #{cycle_num} Complete] Total leads found so far: {WORKER_STATE['total_hiring_leads_found']} | Telegram alerts sent: {WORKER_STATE['total_telegram_sent']}")


def start_autonomous_worker_loop():
    """
    Infinite 24/7 loop. Never terminates. Recovers automatically from any exception.
    """
    WORKER_STATE["is_running"] = True
    WORKER_STATE["start_time"] = datetime.now()

    print("\n" + "=" * 60)
    print("🤖 24/7 AUTONOMOUS VPS LEAD HUNTER DAEMON INITIALIZED")
    print(f"Start Time: {WORKER_STATE['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Initial boot notification to Telegram
    try:
        send_telegram("🟢 <b>[24/7 VPS Hunter Active]</b> Zentic Lead Hunter is now running 24/7 on your VPS without needing your PC! You will receive instant alerts for Facebook, Reddit & Remote hiring posts.")
    except Exception:
        pass

    while True:
        try:
            run_single_hunter_cycle()
        except Exception as e:
            WORKER_STATE["last_error"] = str(e)
            print(f"[Worker Exception] Unexpected crash in cycle: {e}")
            traceback.print_exc()

        # Sleep for 5 minutes (300 seconds) before running next full hunt cycle
        print("\n⏳ Sleeping for 5 minutes before next hunting cycle...")
        for _ in range(30):
            time.sleep(10)


if __name__ == "__main__":
    start_autonomous_worker_loop()

