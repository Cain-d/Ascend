import sqlite3
import os

# Ensure the data folder exists
os.makedirs("data", exist_ok=True)

conn = sqlite3.connect("data/ascend.db")
cursor = conn.cursor()

# USERS table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# FOODS table
cursor.execute("""
CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    calories REAL,
    protein REAL,
    carbs REAL,
    fat REAL,
    fiber REAL,
    sugar REAL
)
""")

# MEALS table
cursor.execute("""
CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    timestamp TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# MEAL ITEMS table (many-to-many)
cursor.execute("""
CREATE TABLE IF NOT EXISTS meal_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_id INTEGER,
    food_id INTEGER,
    quantity REAL,
    FOREIGN KEY(meal_id) REFERENCES meals(id),
    FOREIGN KEY(food_id) REFERENCES foods(id)
)
""")

conn.commit()
conn.close()
print("✅ Database initialized successfully.")
