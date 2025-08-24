from pydantic import BaseModel
from typing import Dict, List, Any


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


# Analytics Data Models


class TrendAnalysis(BaseModel):
    metric_name: str
    time_period: int  # days
    trend_direction: str  # "increasing", "decreasing", "stable"
    rate_of_change: float
    confidence_level: float
    data_points: int
    start_date: str
    end_date: str


class PerformancePrediction(BaseModel):
    workout_type: str
    predicted_performance: Dict[str, float]  # {"reps": 12, "weight": 185}
    confidence_interval: Dict[str, float]  # {"lower": 0.8, "upper": 1.2}
    factors_considered: List[str]
    prediction_date: str
    confidence_score: float


class NutritionRecommendation(BaseModel):
    target_calories: float
    target_protein: float
    target_carbs: float
    target_fat: float
    rationale: str
    confidence_score: float
    valid_until: str
    recommendation_type: str  # "maintenance", "cutting", "bulking"


class AnalysisResult(BaseModel):
    user_email: str
    analysis_type: str
    time_period: int
    result_data: Dict[str, Any]
    created_at: str
    expires_at: str
    confidence_level: float


class TrendInsight(BaseModel):
    insight_type: str  # "weight_trend", "macro_pattern", "performance_correlation"
    title: str
    description: str
    significance_level: float
    actionable_recommendations: List[str]
    data_period: Dict[str, str]  # {"start": "2024-01-01", "end": "2024-01-31"}


class PredictionAccuracy(BaseModel):
    prediction_type: str
    predicted_value: float
    actual_value: float
    prediction_date: str
    actual_date: str
    accuracy_score: float
    user_email: str
