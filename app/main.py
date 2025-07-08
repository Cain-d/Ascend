from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import UserCreate, UserLogin, Food
from app import queries

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Ascend API is running"}

@app.post("/create_user")
def create_user(user: UserCreate):
    success = queries.create_user(user.email, user.password)
    if not success:
        raise HTTPException(status_code=400, detail="Email already in use")
    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserLogin):
    if queries.login_user(user.email, user.password):
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/foods")
def list_foods():
    return queries.get_all_foods()

@app.post("/food")
def add_food(food: Food):
    queries.insert_food(food)
    return {"message": "Food added"}
