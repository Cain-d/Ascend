from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Food(BaseModel):
    name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    sugar: float

class Meal(BaseModel):
    user_id: int
    timestamp: str  # ISO format
    foods: list[int]  # list of food IDs

class ExerciseLog(BaseModel):
    workout_id: int
    exercise_id: int
    set_number: int
    reps: int
    weight: float

class Workout(BaseModel):
    date: str
    name: str


