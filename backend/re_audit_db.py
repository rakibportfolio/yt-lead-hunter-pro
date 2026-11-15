import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fb_group_monitor import classify_fb_post_heuristic

conn = sqlite3.connect('backend/zentic_data.db')
c = conn.cursor()

rows = c.execute('SELECT id, group_name, author_name, post_url, content, is_hiring, platform FROM fb_job_alerts WHERE is_hiring = 1').fetchall()
print(f"Auditing {len(rows)} leads currently marked is_hiring=1...")

fake_count = 0
true_count = 0

for r in rows:
    rid, gname, aname, purl, content, cur_hiring, plat = r
    # Non-FB platform
    if (plat and plat.lower() != 'facebook') or ('reddit.com' in (purl or '').lower()) or ('remoteok' in (purl or '').lower()):
        c.execute('UPDATE fb_job_alerts SET is_hiring = 0 WHERE id = ?', (rid,))
        fake_count += 1
        print(f"Set ID {rid} to is_hiring=0 (Non-FB: {plat} | {purl[:40]})")
        continue

    res = classify_fb_post_heuristic(content, aname)
    if not res.get('is_hiring'):
        c.execute('UPDATE fb_job_alerts SET is_hiring = 0 WHERE id = ?', (rid,))
        fake_count += 1
        print(f"Set ID {rid} to is_hiring=0 (False post: {aname} | {content[:60]}...)")
    else:
        true_count += 1
        print(f"✅ KEPT ID {rid} as TRUE CLIENT HIRING: {aname} | {res.get('job_type')} | {content[:60]}...")

conn.commit()
conn.close()
print(f"\nAudit complete! Removed {fake_count} false positives. Retained {true_count} genuine client jobs.")
