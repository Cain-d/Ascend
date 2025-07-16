from datetime import datetime, date

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth import (
    create_access_token,
    verify_password,
    get_current_user,
)
from app.models import (
    UserCreate,
    UserLogin,
    Food,
    ExerciseLog,
    Workout,
)
from app import queries

app = FastAPI()

# ---------- CORS (dev) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Public ----------
@app.get("/")
def root():
    return {"message": "Ascend API is running"}

@app.post("/create_user")
def create_user(user: UserCreate):
    if not queries.create_user(user.email, user.password):
        raise HTTPException(status_code=400, detail="Email already in use")
    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserLogin):
    row = queries.get_user_by_email(user.email)
    if not row or not verify_password(user.password, row["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})
    return JSONResponse({"access_token": token, "token_type": "bearer"})

# ---------- Auth helpers ----------
CurrentUser = Depends(get_current_user)

# ---------- Foods ----------
@app.post("/foods")
def create_food(food: Food, user_email: str = CurrentUser):
    queries.insert_food(food, user_email)
    return {"message": "Food entry created"}

@app.get("/foods")
def list_foods(user_email: str = CurrentUser):
    return queries.get_foods_by_user(user_email)

@app.delete("/foods/{food_id}")
def delete_food(food_id: int, user_email: str = CurrentUser):
    queries.delete_food(food_id, user_email)
    return {"message": "Food deleted"}

# ---------- Daily macros ----------
@app.get("/daily_macros")
def daily_macros(user_email: str = CurrentUser):
    """Return summed calories/protein/carbs/fat for *today*."""
    return queries.get_macros_for_user_today(user_email, date.today().isoformat())

# ---------- Weights ----------
from pydantic import BaseModel
class WeightEntry(BaseModel):
    date: str
    weight: float

@app.post("/weights")
def add_weight(entry: WeightEntry, user_email: str = CurrentUser):
    queries.insert_weight(user_email, entry.date, entry.weight)
    return {"message": "Weight logged"}

# ---------- Summary (kept for compatibility) ----------
@app.get("/summary")
def get_summary(user_email: str = CurrentUser):
    today = datetime.today().strftime("%Y-%m-%d")
    return queries.get_summary(user_email, today)

# ---------- Exercise / Workouts ----------
@app.post("/exercise_logs")
def add_exercise_log(log: ExerciseLog, user_email: str = CurrentUser):
    queries_log = queries.ExerciseLog(**log.dict())
    queries.insert_exercise_log(user_email, queries_log)
    return {"message": "Exercise log added"}

@app.post("/workouts")
def create_workout(workout: Workout, user_email: str = CurrentUser):
    queries.insert_workout(user_email, workout)
    return {"message": "Workout added"}

@app.get("/workouts")
def list_workouts(user_email: str = CurrentUser):
    return queries.get_workouts_by_user(user_email)

# ---------- Analytics Endpoints ----------
from app.analytics import AnalyticsService

analytics_service = AnalyticsService()

# Import PredictionService with error handling
try:
    from app.predictions import PredictionService
    prediction_service = PredictionService()
except ImportError as e:
    print(f"Warning: Could not import PredictionService: {e}")
    # Create a minimal prediction service for testing
    class MinimalPredictionService:
        def predict_workout_performance(self, user_email, workout_type="general"):
            return None
        def recommend_macro_targets(self, user_email, goal_type="maintenance"):
            return None
        def generate_intervention_suggestions(self, user_email):
            return []
    prediction_service = MinimalPredictionService()

@app.get("/analytics/trends")
def get_analytics_trends(days: int = 30, user_email: str = CurrentUser):
    """Get weight and nutrition trend analysis"""
    try:
        # Get weight trends
        weight_trends = analytics_service.calculate_weight_trends(user_email, days)
        
        # Get macro pattern trends
        macro_trends = analytics_service.analyze_macro_patterns(user_email, days)
        
        # Check if we have sufficient data
        if not weight_trends and not macro_trends:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "insufficient_data",
                    "message": f"Need at least 7 days of data for trend analysis. Please log more weight and nutrition data.",
                    "required_data_points": 7,
                    "suggestions": [
                        "Continue logging weight daily",
                        "Log your meals and nutrition intake",
                        f"Come back after logging data for {7 - days if days < 7 else 'a few more'} days"
                    ]
                }
            )
        
        return {
            "weight_trends": weight_trends.dict() if weight_trends else None,
            "macro_trends": {k: v.dict() for k, v in macro_trends.items()} if macro_trends else {},
            "analysis_period_days": days,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "analysis_error",
                "message": "Unable to generate trend analysis",
                "details": str(e)
            }
        )

@app.get("/analytics/predictions")
def get_analytics_predictions(workout_type: str = "general", user_email: str = CurrentUser):
    """Get performance forecasts and predictions"""
    try:
        # Generate performance prediction
        performance_prediction = prediction_service.predict_workout_performance(user_email, workout_type)
        
        if not performance_prediction:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "insufficient_data",
                    "message": "Need at least 21 days of combined weight, nutrition, and workout data for performance predictions",
                    "required_data_points": 21,
                    "requirements": {
                        "minimum_workout_days": 13,
                        "minimum_nutrition_days": 13,
                        "minimum_total_days": 21
                    },
                    "suggestions": [
                        "Continue logging workouts regularly",
                        "Track your nutrition intake daily",
                        "Log your body weight consistently",
                        "Return after 2-3 weeks of consistent data logging"
                    ]
                }
            )
        
        return {
            "performance_prediction": performance_prediction.dict(),
            "prediction_type": workout_type,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "prediction_error",
                "message": "Unable to generate performance predictions",
                "details": str(e)
            }
        )

@app.get("/analytics/recommendations")
def get_analytics_recommendations(goal_type: str = "maintenance", user_email: str = CurrentUser):
    """Get personalized nutrition and training recommendations"""
    try:
        # Validate goal type
        valid_goals = ["maintenance", "cutting", "bulking"]
        if goal_type not in valid_goals:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_goal",
                    "message": f"Goal type must be one of: {', '.join(valid_goals)}",
                    "provided_goal": goal_type
                }
            )
        
        # Generate macro recommendations
        macro_recommendations = prediction_service.recommend_macro_targets(user_email, goal_type)
        
        # Generate intervention suggestions
        intervention_suggestions = prediction_service.generate_intervention_suggestions(user_email)
        
        if not macro_recommendations and not intervention_suggestions:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "insufficient_data",
                    "message": "Need at least 14 days of nutrition data and some workout history for personalized recommendations",
                    "required_data": {
                        "minimum_nutrition_days": 14,
                        "minimum_workout_sessions": 5
                    },
                    "suggestions": [
                        "Log your meals and nutrition intake for at least 2 weeks",
                        "Complete several workout sessions",
                        "Track your body weight regularly",
                        "Return after building more data history"
                    ]
                }
            )
        
        return {
            "macro_recommendations": macro_recommendations.dict() if macro_recommendations else None,
            "intervention_suggestions": [insight.dict() for insight in intervention_suggestions],
            "goal_type": goal_type,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "recommendation_error",
                "message": "Unable to generate recommendations",
                "details": str(e)
            }
        )

@app.get("/analytics/insights")
def get_analytics_insights(user_email: str = CurrentUser):
    """Get comprehensive analytics dashboard data"""
    try:
        # Get all analytics components
        weight_trends = analytics_service.calculate_weight_trends(user_email, 30)
        macro_trends = analytics_service.analyze_macro_patterns(user_email, 30)
        correlations = analytics_service.correlate_nutrition_performance(user_email, 60)
        
        # Get predictions
        performance_prediction = prediction_service.predict_workout_performance(user_email)
        macro_recommendations = prediction_service.recommend_macro_targets(user_email)
        intervention_suggestions = prediction_service.generate_intervention_suggestions(user_email)
        
        # Check if we have any meaningful data
        has_trends = weight_trends or macro_trends
        has_correlations = correlations and "error" not in correlations
        has_predictions = performance_prediction is not None
        has_recommendations = macro_recommendations is not None or intervention_suggestions
        
        if not (has_trends or has_correlations or has_predictions or has_recommendations):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "insufficient_data",
                    "message": "Need more data to generate meaningful insights",
                    "requirements": {
                        "for_trends": "At least 7 days of weight and nutrition data",
                        "for_correlations": "At least 14 days of nutrition and workout data",
                        "for_predictions": "At least 21 days of combined data",
                        "for_recommendations": "At least 14 days of nutrition data"
                    },
                    "suggestions": [
                        "Start by logging your daily weight",
                        "Track your meals and nutrition intake",
                        "Record your workout sessions",
                        "Be consistent with data logging for best results",
                        "Check back after 1-2 weeks of consistent logging"
                    ]
                }
            )
        
        # Build comprehensive insights response
        insights_data = {
            "summary": {
                "has_weight_trends": weight_trends is not None,
                "has_macro_trends": bool(macro_trends),
                "has_correlations": has_correlations,
                "has_predictions": has_predictions,
                "has_recommendations": has_recommendations,
                "data_quality_score": _calculate_data_quality_score(
                    weight_trends, macro_trends, correlations, performance_prediction
                )
            },
            "trends": {
                "weight": weight_trends.dict() if weight_trends else None,
                "macros": {k: v.dict() for k, v in macro_trends.items()} if macro_trends else {}
            },
            "correlations": correlations if has_correlations else None,
            "predictions": {
                "performance": performance_prediction.dict() if performance_prediction else None,
                "nutrition": macro_recommendations.dict() if macro_recommendations else None
            },
            "insights": [insight.dict() for insight in intervention_suggestions],
            "generated_at": datetime.now().isoformat(),
            "analysis_period": {
                "trends_days": 30,
                "correlations_days": 60,
                "predictions_days": 21
            }
        }
        
        return insights_data
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "insights_error",
                "message": "Unable to generate comprehensive insights",
                "details": str(e)
            }
        )

def _calculate_data_quality_score(weight_trends, macro_trends, correlations, performance_prediction) -> float:
    """Calculate a data quality score from 0 to 1"""
    score = 0.0
    
    # Weight trends contribute 25%
    if weight_trends and weight_trends.confidence_level > 0.5:
        score += 0.25 * weight_trends.confidence_level
    
    # Macro trends contribute 25%
    if macro_trends:
        avg_macro_confidence = sum(t.confidence_level for t in macro_trends.values()) / len(macro_trends)
        score += 0.25 * avg_macro_confidence
    
    # Correlations contribute 25%
    if correlations and "metadata" in correlations:
        data_points = correlations["metadata"]["data_points"]
        correlation_score = min(1.0, data_points / 30)  # Full score at 30+ data points
        score += 0.25 * correlation_score
    
    # Predictions contribute 25%
    if performance_prediction:
        score += 0.25 * performance_prediction.confidence_score
    
    return round(score, 2)
