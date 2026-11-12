"""
reply_monitor.py — Automated Gmail Inbox Monitor using mailsuite.
Detects when a YouTube creator/lead replies to an outreach email,
automatically advances their CRM pipeline stage to 'replied',
logs the interaction, and sends a notification.
"""

import email
from email.header import decode_header
import logging
import re
from datetime import datetime
from typing import Dict, List, Any

from config import Config
from database import get_db, mark_email_replied

logger = logging.getLogger("reply_monitor")


def _decode_str(val: str) -> str:
    """Decode RFC 2047 encoded email header string."""
    if not val:
        return ""
    try:
        decoded_parts = decode_header(val)
        result = []
        for part, enc in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(enc or 'utf-8', errors='ignore'))
            else:
                result.append(str(part))
        return "".join(result)
    except Exception:
        return str(val)


def _extract_email_addr(from_header: str) -> str:
    """Extract bare email address from header e.g. 'John Doe <john@gmail.com>' -> 'john@gmail.com'."""
    if not from_header:
        return ""
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1).strip().lower()
    return from_header.strip().lower()


def check_inbox_replies(limit: int = 50) -> Dict[str, Any]:
    """
    Connects to Gmail via mailsuite IMAPClient, quickly inspects recent email headers,
    matches senders against leads in the emails table, and advances matched leads to 'replied'.
    """
    if not Config.GMAIL_ADDRESS or not Config.GMAIL_PASSWORD:
        return {"ok": False, "error": "Gmail credentials not configured in settings"}

    try:
        from mailsuite.imap import IMAPClient
        from mailsuite.utils import parse_email
    except ImportError as e:
        logger.error(f"mailsuite import error: {e}")
        return {"ok": False, "error": f"mailsuite not installed: {e}"}

    matched_replies = []

    try:
        with IMAPClient(
            host="imap.gmail.com",
            username=Config.GMAIL_ADDRESS,
            password=Config.GMAIL_PASSWORD,
            ssl=True
        ) as client:
            client.select_folder("INBOX", readonly=True)
            msg_ids = client.search()
            if not msg_ids:
                return {"ok": True, "checked": 0, "replies_found": 0, "leads_updated": []}

            recent_ids = msg_ids[-limit:] if len(msg_ids) > limit else msg_ids

            db = get_db()
            # Fetch all sent/opened leads to match against
            active_leads = db.execute("""
                SELECT e.id as email_id, e.lead_id, e.to_address, e.subject as outreach_subject,
                       e.tracking_id, e.status as email_status,
                       l.channel, l.name, l.pipeline_stage
                FROM emails e
                JOIN leads l ON e.lead_id = l.id
                WHERE e.status IN ('sent', 'opened', 'delivered')
            """).fetchall()

            outreach_lookup = {}
            for r in active_leads:
                addr = (r["to_address"] or "").strip().lower()
                if addr:
                    outreach_lookup[addr] = dict(r)

            if not outreach_lookup:
                return {"ok": True, "checked": len(recent_ids), "replies_found": 0, "leads_updated": []}

            # Fast header fetch for all recent messages in one batch
            fetch_res = client.fetch(recent_ids, ['BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)]'])

            for uid, data in fetch_res.items():
                try:
                    raw_header = data.get(b'BODY[HEADER.FIELDS (FROM SUBJECT DATE)]', b'').decode(errors='ignore')
                    msg = email.message_from_string(raw_header)
                    from_hdr = _decode_str(msg.get('From', ''))
                    sender_email = _extract_email_addr(from_hdr)
                    subject_hdr = _decode_str(msg.get('Subject', 'No Subject'))

                    if not sender_email or sender_email == Config.GMAIL_ADDRESS.strip().lower():
                        continue
                    if any(bot in sender_email for bot in ["no-reply", "noreply", "mailer-daemon", "google.com"]):
                        continue

                    if sender_email in outreach_lookup:
                        lead_info = outreach_lookup[sender_email]
                        lead_id = lead_info["lead_id"]
                        tracking_id = lead_info["tracking_id"]
                        channel_name = lead_info["channel"] or lead_info["name"] or sender_email

                        # Fetch full message body for this matched reply
                        snippet = ""
                        try:
                            full_raw = client.fetch_message(uid)
                            parsed = parse_email(full_raw)
                            snippet = (parsed.get("body_markdown") or parsed.get("body") or "")[:500]
                        except Exception:
                            snippet = subject_hdr

                        now_iso = datetime.now().isoformat()
                        # Advance status in DB
                        if tracking_id:
                            mark_email_replied(tracking_id)
                        else:
                            db.execute("""
                                UPDATE leads
                                SET status = 'replied', pipeline_stage = 'replied', updated_at = ?
                                WHERE id = ?
                            """, (now_iso, lead_id))
                            db.execute("""
                                UPDATE emails SET status='replied', replied_at=? WHERE id=?
                            """, (now_iso, lead_info["email_id"]))
                            db.commit()

                        # Add activity log
                        try:
                            db.execute("""
                                INSERT INTO lead_activity (lead_id, activity_type, description, created_at)
                                VALUES (?, 'email_replied', ?, ?)
                            """, (lead_id, f"Replied: '{subject_hdr}' — {snippet[:120]}...", now_iso))
                            db.commit()
                        except Exception:
                            pass

                        matched_replies.append({
                            "lead_id": lead_id,
                            "channel": channel_name,
                            "email": sender_email,
                            "subject": subject_hdr,
                            "snippet": snippet[:100]
                        })

                        # Remove from lookup to avoid duplicates
                        del outreach_lookup[sender_email]

                except Exception as inner_e:
                    logger.warning(f"Error checking message UID {uid}: {inner_e}")
                    continue

    except Exception as e:
        logger.error(f"Error during IMAP check: {e}")
        return {"ok": False, "error": str(e)}

    return {
        "ok": True,
        "checked": len(recent_ids),
        "replies_found": len(matched_replies),
        "leads_updated": matched_replies
    }


if __name__ == "__main__":
    import json
    import time
    t0 = time.time()
    res = check_inbox_replies(limit=35)
    print(f"Completed in {time.time()-t0:.2f}s:")
    print(json.dumps(res, indent=2))
