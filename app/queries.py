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

def insert_food(food, user_email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO foods (name, calories, protein, carbs, fat, fiber, sugar, user_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (food.name, food.calories, food.protein, food.carbs,
         food.fat, food.fiber, food.sugar, user_email)
    )
    conn.commit()
    conn.close()


def get_foods_by_user_and_date(user_email, date=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if date:
        cursor.execute("SELECT * FROM foods WHERE user_email = ? AND date = ?", (user_email, date))
    else:
        cursor.execute("SELECT * FROM foods WHERE user_email = ?", (user_email,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_foods_by_user(user_email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM foods WHERE user_email = ?", (user_email,))
    rows = cursor.fetchall()
    conn.close()

    foods = []
    for row in rows:
        foods.append({
            "id": row[0],
            "name": row[1],
            "calories": row[2],
            "protein": row[3],
            "carbs": row[4],
            "fat": row[5],
            "fiber": row[6],
            "sugar": row[7],
            "user_email": row[8]
        })

    return foods



def get_user_by_email(email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"id": row[0], "email": row[1], "password": row[2]}
    return None

def insert_weight(user_email, date, weight):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO weights (user_email, date, weight) VALUES (?, ?, ?)",
        (user_email, date, weight)
    )
    conn.commit()
    conn.close()

def get_summary(user_email, date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            SUM(calories), SUM(protein), SUM(carbs), 
            SUM(fat), SUM(fiber), SUM(sugar)
        FROM foods
        WHERE user_email = ? AND date = ?
    """, (user_email, date))
    food_totals = cursor.fetchone()

    cursor.execute(
        "SELECT weight FROM weights WHERE user_email = ? AND date = ?",
        (user_email, date)
    )
    weight_row = cursor.fetchone()
    conn.close()

    return {
        "calories": food_totals[0] or 0,
        "protein": food_totals[1] or 0,
        "carbs": food_totals[2] or 0,
        "fat": food_totals[3] or 0,
        "fiber": food_totals[4] or 0,
        "sugar": food_totals[5] or 0,
        "weight": weight_row[0] if weight_row else None
    }

# queries.py
def delete_food(food_id, user_email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM foods WHERE id = ? AND user_email = ?", (food_id, user_email))
    conn.commit()
    conn.close()

class Exercise:
    def __init__(self, name, category, unit):
        self.name = name
        self.category = category
        self.unit = unit

class ExerciseLog:
    def __init__(self, workout_id, exercise_id, set_number, reps, weight):
        self.workout_id = workout_id
        self.exercise_id = exercise_id
        self.set_number = set_number
        self.reps = reps
        self.weight = weight

def insert_exercise_log(user_email: str, log: ExerciseLog):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO exercise_logs (workout_id, exercise_id, set_number, reps, weight)
        VALUES (?, ?, ?, ?, ?)
        """,
        (log.workout_id, log.exercise_id, log.set_number, log.reps, log.weight)
    )
    conn.commit()
    conn.close()

def get_exercises_by_user(user_email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, unit FROM exercises WHERE user_email = ?", (user_email,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "unit": row[3]
        }
        for row in rows
    ]

def insert_workout(user_email: str, workout):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workouts (user_email, date, name)
        VALUES (?, ?, ?)
        """,
        (user_email, workout.date, workout.name)
    )
    conn.commit()
def get_workouts_by_user(user_email: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, date, name
        FROM workouts
        WHERE user_email = ?
        ORDER BY date DESC
        """,
        (user_email,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row[0], "date": row[1], "name": row[2]}
        for row in rows
    ]
