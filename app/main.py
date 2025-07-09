from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.models import UserCreate, UserLogin, Food
import queries
from auth import create_access_token, verify_password, get_current_user

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
def list_foods():
    return queries.get_all_foods()

@app.post("/food")
def add_food(food: Food):
    queries.insert_food(food)
    return {"message": "Food added"}

@app.get("/protected")
def protected(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}. You’re authorized!"}
