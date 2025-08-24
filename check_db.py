#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('../data/ascend.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', [t[0] for t in tables])
conn.close()