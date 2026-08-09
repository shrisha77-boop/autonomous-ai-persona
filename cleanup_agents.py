import sqlite3

DB = "signalforge.db"

KEEP_AGENT = "26ba8ec8-d72e-4a79-bf00-a398bc8868d8"

conn = sqlite3.connect(DB)

cursor = conn.cursor()

cursor.execute(
    """
    UPDATE agents
    SET is_active = 0
    WHERE name = 'Ada'
      AND id != ?
    """,
    (KEEP_AGENT,),
)

conn.commit()

print(f"Deactivated {cursor.rowcount} duplicate Ada agents.")

rows = cursor.execute(
    """
    SELECT id, name, domain, is_active
    FROM agents
    WHERE name = 'Ada'
    """
).fetchall()

print("\nCurrent Ada agents:")
for row in rows:
    print(row)

conn.close()