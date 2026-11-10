import os
import sys
import time
import json
import sqlite3
import requests
from datetime import datetime

# Set up paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from config import cfg
from database import (
    get_all_fb_groups, insert_fb_alert, is_fb_post_seen,
    update_fb_group_scan_stats, get_db
)
from fb_group_monitor import scrape_facebook_group_posts, classify_fb_post_with_ai, is_post_fresh
from telegram_bot import alert_fb_hiring_post

COOLIFY_URL = "http://hodtnxhpc2hnghdsc1hdkdfz.187.127.185.67.sslip.io"

def run_live_scrape(max_groups=15):
    print("=" * 60)
    print("🚀 STARTING LIVE FB SCRAPE FOR LAST 5 HOURS POSTS")
    print("=" * 60)

    # 1. Fetch VIP & priority groups
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, url, priority 
        FROM fb_monitored_groups 
        WHERE active = 1 
        ORDER BY priority DESC, id ASC 
        LIMIT ?
    """, (max_groups,))
    groups = [dict(r) for r in c.fetchall()]
    conn.close()

    print(f"Loaded {len(groups)} top priority Facebook groups to scan.")

    total_scraped = 0
    total_saved = 0
    total_hiring = 0
    scraped_alerts_batch = []

    for i, g in enumerate(groups, 1):
        gid = g["id"]
        gname = g["name"]
        gurl = g["url"]

        print(f"\n[{i}/{len(groups)}] Scanning '{gname}'...")
        try:
            posts = scrape_facebook_group_posts(gurl, limit=8)
            print(f" -> Found {len(posts)} raw posts in feed.")
            update_fb_group_scan_stats(gid, len(posts))
            total_scraped += len(posts)

            for p in posts:
                txt = p["content"]
                pid = p["post_id"]

                # Freshness: accept posts up to 5 hours
                fresh_5h = is_post_fresh(txt, max_hours=5)

                # AI classification
                ai_res = classify_fb_post_with_ai(txt, p["author_name"], gname)
                is_hiring = 1 if (fresh_5h and ai_res.get("is_hiring")) else 0

                # Check if seen
                if is_fb_post_seen(pid):
                    if is_hiring:
                        conn = get_db()
                        row = conn.execute("SELECT id, telegram_sent FROM fb_job_alerts WHERE post_id = ?", (pid,)).fetchone()
                        conn.close()
                        if row and row["telegram_sent"] == 0:
                            alert_data = {
                                "group_id": gid,
                                "group_name": gname,
                                "post_id": pid,
                                "author_name": p["author_name"],
                                "author_url": p.get("author_url", ""),
                                "post_url": p["post_url"],
                                "content": txt,
                                "job_type": ai_res.get("job_type", "Video Editor"),
                                "budget": ai_res.get("budget", ""),
                                "ai_summary": ai_res.get("ai_summary", txt[:200]),
                                "contact_whatsapp": ai_res.get("contact_whatsapp", ""),
                                "contact_phone": ai_res.get("contact_phone", ""),
                                "contact_email": ai_res.get("contact_email", ""),
                            }
                            sent_ok = alert_fb_hiring_post(alert_data)
                            if sent_ok:
                                conn = get_db()
                                conn.execute("UPDATE fb_job_alerts SET telegram_sent = 1, telegram_sent_at = datetime('now') WHERE id = ?", (row["id"],))
                                conn.commit()
                                conn.close()
                                total_hiring += 1
                                print(f"    🎯 SENT PENDING HIRING LEAD TO TELEGRAM: {alert_data['job_type']}")
                    continue

                alert_data = {
                    "group_id": gid,
                    "group_name": gname,
                    "post_id": pid,
                    "author_name": p["author_name"],
                    "author_url": p.get("author_url", ""),
                    "post_url": p["post_url"],
                    "content": txt,
                    "image_url": p.get("image_url", ""),
                    "is_hiring": is_hiring,
                    "client_name": ai_res.get("client_name", p["author_name"]) if is_hiring else p["author_name"],
                    "job_type": ai_res.get("job_type", "Video Editor") if is_hiring else "Group Post",
                    "budget": ai_res.get("budget", "") if is_hiring else "",
                    "contact_phone": ai_res.get("contact_phone", ""),
                    "contact_email": ai_res.get("contact_email", ""),
                    "contact_whatsapp": ai_res.get("contact_whatsapp", ""),
                    "contact_telegram": ai_res.get("contact_telegram", ""),
                    "confidence_score": ai_res.get("confidence_score", 90) if is_hiring else 0,
                    "ai_summary": ai_res.get("ai_summary", txt[:200]),
                    "telegram_sent": 0,
                    "telegram_sent_at": None
                }

                # If hiring & fresh, send instant Telegram alert!
                if is_hiring:
                    sent_ok = alert_fb_hiring_post(alert_data)
                    if sent_ok:
                        alert_data["telegram_sent"] = 1
                        alert_data["telegram_sent_at"] = datetime.now().isoformat()
                    total_hiring += 1
                    print(f"    🎯 NEW HIRING LEAD: {alert_data['job_type']} (Telegram sent: {sent_ok})")
                else:
                    print(f"    💬 Community post saved: {p['author_name']} ({txt[:50]}...)")

                insert_fb_alert(alert_data)
                total_saved += 1
                scraped_alerts_batch.append(alert_data)

        except Exception as e:
            print(f" ❌ Error scanning {gname}: {e}")

        # Sleep a couple seconds between groups
        time.sleep(2)

    print("\n" + "=" * 60)
    print(f"🎉 SCAN COMPLETED!")
    print(f"Total raw posts found: {total_scraped}")
    print(f"Total new posts saved to dashboard: {total_saved}")
    print(f"Total hiring leads sent to Telegram: {total_hiring}")
    print("=" * 60)

    # Sync to Coolify
    if scraped_alerts_batch:
        print(f"\n🔄 Syncing {len(scraped_alerts_batch)} new posts to Coolify ({COOLIFY_URL})...")
        try:
            ingest_url = f"{COOLIFY_URL}/api/fb/ingest"
            posts_payload = [
                {
                    "content": a["content"],
                    "author_name": a["author_name"],
                    "author_url": a["author_url"],
                    "post_url": a["post_url"],
                    "group_name": a["group_name"],
                    "image_url": a["image_url"]
                }
                for a in scraped_alerts_batch
            ]
            resp = requests.post(ingest_url, json={"posts": posts_payload}, timeout=15)
            print(f"Coolify sync response: {resp.status_code} - {resp.text[:150]}")
        except Exception as ce:
            print(f"Coolify sync note: {ce}")

if __name__ == "__main__":
    run_live_scrape(max_groups=25)

