from pydantic import BaseModel

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
