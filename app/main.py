from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.models import UserCreate, UserLogin, Food, ExerciseLog
from app import queries
# Import ExerciseLog from queries if needed for conversion
# from app.queries import ExerciseLog as QueriesExerciseLog
from app.auth import create_access_token, verify_password, get_current_user
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models import Workout
from app.queries import insert_workout, get_workouts_by_user

app = FastAPI()

# CORS setup (dev only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Ascend API is running"}

@app.get("/secure-data")
def secure_data(user_email: str = Depends(get_current_user)):
    return {"message": f"Hello, {user_email}. This is protected data!"}

@app.get("/me")
def get_profile(user_email: str = Depends(get_current_user)):
    return {"email": user_email}

@app.post("/create_user")
def create_user(user: UserCreate):
    success = queries.create_user(user.email, user.password)
    if not success:
        raise HTTPException(status_code=400, detail="Email already in use")
    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserLogin):
    user_row = queries.get_user_by_email(user.email)
    if user_row and verify_password(user.password, user_row["password"]):
        token = create_access_token({"sub": user.email})
        return JSONResponse(content={"access_token": token, "token_type": "bearer"})
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/foods")
def get_foods(date: Optional[str] = None, user_email: str = Depends(get_current_user)):
    return queries.get_foods_by_user(user_email)



@app.post("/foods")
def create_food(food: Food, user_email: str = Depends(get_current_user)):
    queries.insert_food(food, user_email)
    return {"message": "Food entry created"}


@app.get("/protected")
def protected(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}. You’re authorized!"}


class WeightEntry(BaseModel):
    date: str  # ISO format like '2025-07-09'
    weight: float

@app.post("/weights")
def add_weight(entry: WeightEntry, user_email: str = Depends(get_current_user)):
    queries.insert_weight(user_email, entry.date, entry.weight)
    return {"message": "Weight logged successfully"}

@app.get("/summary")
def get_summary(user_email: str = Depends(get_current_user)):
    today = datetime.today().strftime("%Y-%m-%d")
    return queries.get_summary(user_email, today)

@app.delete("/foods/{food_id}")
def delete_food(food_id: int, user_email: str = Depends(get_current_user)):
    queries.delete_food(food_id, user_email)
@app.post("/exercise_logs")
def add_exercise_log(log: ExerciseLog, user_email: str = Depends(get_current_user)):
    # Convert app.models.ExerciseLog to app.queries.ExerciseLog
    queries_log = queries.ExerciseLog(**log.dict())
    queries.insert_exercise_log(user_email, queries_log)
    return {"message": "Exercise log added successfully"}

@app.get("/exercises")
def list_exercises(user_email: str = Depends(get_current_user)):
    return queries.get_exercises_by_user(user_email)



@app.post("/workouts")
def create_workout(workout: Workout, user_email: str = Depends(get_current_user)):
    insert_workout(user_email, workout)
    return {"message": "Workout added successfully"}

@app.get("/workouts")
def list_workouts(user_email: str = Depends(get_current_user)):
    return get_workouts_by_user(user_email)
