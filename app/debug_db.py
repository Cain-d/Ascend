import sqlite3

conn = sqlite3.connect("data/ascend.db")
cursor = conn.cursor()

cursor.execute("SELECT id, email, password FROM users")
users = cursor.fetchall()

print("📋 Users in DB:")
for user in users:
    print(user)


conn.close()


