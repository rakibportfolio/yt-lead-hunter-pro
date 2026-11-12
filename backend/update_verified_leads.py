import sqlite3

conn = sqlite3.connect("backend/zentic_data.db")
c = conn.cursor()
c.execute("UPDATE leads SET email = 'info@studiogta.ca' WHERE name LIKE '%GTA%' OR handle LIKE '%StudioGTA%'")
conn.commit()

c.execute("SELECT id, name, handle, email FROM leads WHERE name LIKE '%GTA%' OR handle LIKE '%StudioGTA%'")
for r in c.fetchall():
    print(f"GTA lead: ID {r[0]} | Name: {r[1]} | Handle: {r[2]} | Email: {r[3]}")

conn.close()
