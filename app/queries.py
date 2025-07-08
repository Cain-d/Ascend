import sqlite3
from passlib.hash import bcrypt

DB_NAME = "data/ascend.db"

def create_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hashed_pw = bcrypt.hash(password)
    try:
        print(f"🔧 Creating user: {email}")
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_pw))
        conn.commit()
        print("✅ User created successfully")
        return True
    except sqlite3.IntegrityError as e:
        print("❌ IntegrityError:", e)
        return False
    except Exception as e:
        print("❌ Other error:", e)
        return False
    finally:
        conn.close()

def login_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    print(f"🔍 Email lookup: {email}")
    print(f"🔍 Row from DB: {row}")
    if row:
        return bcrypt.verify(password, row[0])
    return False

def insert_food(food):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO foods (name, calories, protein, carbs, fat, fiber, sugar)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (food.name, food.calories, food.protein, food.carbs, food.fat, food.fiber, food.sugar))
    conn.commit()
    conn.close()

def get_all_foods():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM foods")
    results = cursor.fetchall()
    conn.close()
    return results
