import sqlite3

conn = sqlite3.connect("backend/zentic_data.db")
c = conn.cursor()

# 1. Backfill all sent emails into outreach_sent
c.execute("""
    UPDATE leads 
    SET status = 'sent', pipeline_stage = 'outreach_sent'
    WHERE id IN (SELECT lead_id FROM emails WHERE status = 'sent' AND lead_id IS NOT NULL)
""")
print(f"Updated {c.rowcount} leads to 'outreach_sent' stage!")

# 2. Backfill opened emails into email_opened
c.execute("""
    UPDATE leads 
    SET pipeline_stage = 'email_opened'
    WHERE id IN (SELECT lead_id FROM emails WHERE status = 'opened' AND lead_id IS NOT NULL)
""")
print(f"Updated {c.rowcount} leads to 'email_opened' stage!")

conn.commit()

# Breakdown
c.execute("SELECT pipeline_stage, COUNT(id) FROM leads GROUP BY pipeline_stage")
print("Pipeline breakdown:", c.fetchall())

c.execute("SELECT id, name, status, pipeline_stage FROM leads WHERE id IN (555, 837, 879, 941, 1131, 1167, 1378)")
for r in c.fetchall():
    print("  ", r)

conn.close()
