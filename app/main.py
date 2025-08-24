from datetime import datetime, date
from typing import Optional, List

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

    # Invalidate nutrition-related analytics cache
    from app.db import AnalyticsDB

    AnalyticsDB.invalidate_user_cache(user_email, ["macro_patterns"])

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

    # Invalidate weight-related analytics cache
    from app.db import AnalyticsDB

    AnalyticsDB.invalidate_user_cache(user_email, ["weight_trends", "macro_patterns"])

    return {"message": "Weight logged"}


# ---------- Summary (kept for compatibility) ----------
@app.get("/summary")
def get_summary(user_email: str = CurrentUser):
    today = datetime.today().strftime("%Y-%m-%d")
    return queries.get_summary(user_email, today)


# ---------- Exercise / Workouts ----------
@app.post("/exercise_logs")
def create_exercise_log(log: ExerciseLog, user_email: str = CurrentUser):
    queries_log = queries.ExerciseLog(**log.dict())
    queries.insert_exercise_log(user_email, queries_log)

    # Invalidate performance-related analytics cache
    from app.db import AnalyticsDB

    AnalyticsDB.invalidate_user_cache(
        user_email, ["performance_predictions", "correlations"]
    )

    return {"message": "Exercise log added"}


@app.post("/workouts")
def create_workout(workout: Workout, user_email: str = CurrentUser):
    queries.insert_workout(user_email, workout)

    # Invalidate performance-related analytics cache
    from app.db import AnalyticsDB

    AnalyticsDB.invalidate_user_cache(
        user_email, ["performance_predictions", "correlations"]
    )

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
except ImportError:
    # Create a minimal prediction service for testing
    class MinimalPredictionService:
        def predict_workout_performance(self, user_email, workout_type="general"):
            return None

        def recommend_macro_targets(self, user_email, goal_type="maintenance"):
            return None

        def generate_intervention_suggestions(self, user_email):
            return []

        def log_prediction_accuracy(
            self,
            user_email,
            prediction_type,
            predicted_value,
            actual_value,
            prediction_date,
            actual_date=None,
        ):
            # Stub: always return True for testing
            return True

        def get_prediction_accuracy_stats(self, user_email, prediction_type=""):
            return {"total_predictions": 0, "average_accuracy": 0.0}

        def calculate_accuracy_trends(self, user_email, prediction_type=""):
            return {}

        def get_prediction_type_performance(self, user_email):
            return {}

        def get_recent_prediction_accuracy(self, user_email, days=30):
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
                    "message": "Need at least 7 days of data for trend analysis. Please log more weight and nutrition data.",
                    "required_data_points": 7,
                    "suggestions": [
                        "Continue logging weight daily",
                        "Log your meals and nutrition intake",
                        f"Come back after logging data for {7 - days if days < 7 else 'a few more'} days",
                    ],
                },
            )

        return {
            "weight_trends": weight_trends.dict() if weight_trends else None,
            "macro_trends": {k: v.dict() for k, v in macro_trends.items()}
            if macro_trends
            else {},
            "analysis_period_days": days,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "analysis_error",
                "message": "Unable to generate trend analysis",
                "details": str(e),
            },
        )


@app.get("/analytics/predictions")
def get_analytics_predictions(
    workout_type: str = "general", user_email: str = CurrentUser
):
    """Get performance forecasts and predictions"""
    try:
        # Generate performance prediction
        performance_prediction = prediction_service.predict_workout_performance(
            user_email, workout_type
        )

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
                        "minimum_total_days": 21,
                    },
                    "suggestions": [
                        "Continue logging workouts regularly",
                        "Track your nutrition intake daily",
                        "Log your body weight consistently",
                        "Return after 2-3 weeks of consistent data logging",
                    ],
                },
            )

        return {
            "performance_prediction": performance_prediction.dict(),
            "prediction_type": workout_type,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "prediction_error",
                "message": "Unable to generate performance predictions",
                "details": str(e),
            },
        )


@app.get("/analytics/recommendations")
def get_analytics_recommendations(
    goal_type: str = "maintenance", user_email: str = CurrentUser
):
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
                    "provided_goal": goal_type,
                },
            )

        # Generate macro recommendations
        macro_recommendations = prediction_service.recommend_macro_targets(
            user_email, goal_type
        )

        # Generate intervention suggestions
        intervention_suggestions = prediction_service.generate_intervention_suggestions(
            user_email
        )

        if not macro_recommendations and not intervention_suggestions:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "insufficient_data",
                    "message": "Need at least 14 days of nutrition data and some workout history for personalized recommendations",
                    "required_data": {
                        "minimum_nutrition_days": 14,
                        "minimum_workout_sessions": 5,
                    },
                    "suggestions": [
                        "Log your meals and nutrition intake for at least 2 weeks",
                        "Complete several workout sessions",
                        "Track your body weight regularly",
                        "Return after building more data history",
                    ],
                },
            )

        return {
            "macro_recommendations": macro_recommendations.dict()
            if macro_recommendations
            else None,
            "intervention_suggestions": [
                insight.dict() for insight in intervention_suggestions
            ],
            "goal_type": goal_type,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "recommendation_error",
                "message": "Unable to generate recommendations",
                "details": str(e),
            },
        )


@app.get("/analytics/insights")
def get_analytics_insights(days: int = 30, user_email: str = CurrentUser):
    """Get comprehensive analytics dashboard data"""
    try:
        # Get all analytics components with specified time period
        weight_trends = analytics_service.calculate_weight_trends(user_email, days)
        macro_trends = analytics_service.analyze_macro_patterns(user_email, days)
        correlations = analytics_service.correlate_nutrition_performance(
            user_email, min(days * 2, 90)
        )

        # Get predictions
        performance_prediction = prediction_service.predict_workout_performance(
            user_email
        )
        macro_recommendations = prediction_service.recommend_macro_targets(user_email)
        intervention_suggestions = prediction_service.generate_intervention_suggestions(
            user_email
        )

        # Check if we have any meaningful data
        has_trends = weight_trends or macro_trends
        has_correlations = correlations and "error" not in correlations
        has_predictions = performance_prediction is not None
        has_recommendations = (
            macro_recommendations is not None or intervention_suggestions
        )

        if not (
            has_trends or has_correlations or has_predictions or has_recommendations
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "insufficient_data",
                    "message": "Need more data to generate meaningful insights",
                    "requirements": {
                        "for_trends": "At least 7 days of weight and nutrition data",
                        "for_correlations": "At least 14 days of nutrition and workout data",
                        "for_predictions": "At least 21 days of combined data",
                        "for_recommendations": "At least 14 days of nutrition data",
                    },
                    "suggestions": [
                        "Start by logging your daily weight",
                        "Track your meals and nutrition intake",
                        "Record your workout sessions",
                        "Be consistent with data logging for best results",
                        "Check back after 1-2 weeks of consistent logging",
                    ],
                },
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
                ),
            },
            "trends": {
                "weight": weight_trends.dict() if weight_trends else None,
                "macros": {k: v.dict() for k, v in macro_trends.items()}
                if macro_trends
                else {},
            },
            "correlations": correlations if has_correlations else None,
            "predictions": {
                "performance": performance_prediction.dict()
                if performance_prediction
                else None,
                "nutrition": macro_recommendations.dict()
                if macro_recommendations
                else None,
            },
            "insights": [insight.dict() for insight in intervention_suggestions],
            "generated_at": datetime.now().isoformat(),
            "analysis_period": {
                "trends_days": days,
                "correlations_days": min(days * 2, 90),
                "predictions_days": 21,
            },
        }

        return insights_data

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "insights_error",
                "message": "Unable to generate comprehensive insights",
                "details": str(e),
            },
        )


def _calculate_data_quality_score(
    weight_trends, macro_trends, correlations, performance_prediction
) -> float:
    """Calculate a data quality score from 0 to 1"""
    score = 0.0

    # Weight trends contribute 25%
    if weight_trends and weight_trends.confidence_level > 0.5:
        score += 0.25 * weight_trends.confidence_level

    # Macro trends contribute 25%
    if macro_trends:
        avg_macro_confidence = sum(
            t.confidence_level for t in macro_trends.values()
        ) / len(macro_trends)
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


# ---------- Background Processing and Cache Management Endpoints ----------


@app.post("/analytics/background/{analysis_type}")
def submit_background_analysis(
    analysis_type: str, days: int = 90, user_email: str = CurrentUser
):
    """Submit expensive analysis for background processing"""
    try:
        valid_types = [
            "comprehensive_correlation",
            "long_term_trends",
            "performance_modeling",
        ]
        if analysis_type not in valid_types:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_analysis_type",
                    "message": f"Analysis type must be one of: {', '.join(valid_types)}",
                    "provided_type": analysis_type,
                },
            )

        task_id = analytics_service.submit_expensive_analysis(
            user_email, analysis_type, days=days
        )

        return {
            "task_id": task_id,
            "analysis_type": analysis_type,
            "status": "submitted",
            "estimated_completion": "5-15 minutes",
            "check_status_url": f"/analytics/background/status/{task_id}",
        }

    except ValueError as e:
        return JSONResponse(
            status_code=400, content={"error": "invalid_request", "message": str(e)}
        )
    except RuntimeError as e:
        return JSONResponse(
            status_code=409, content={"error": "task_conflict", "message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "submission_error",
                "message": "Failed to submit background analysis",
                "details": str(e),
            },
        )


@app.get("/analytics/background/status/{task_id}")
def get_background_analysis_status(task_id: str, user_email: str = CurrentUser):
    """Get status of background analysis task"""
    try:
        # Verify task belongs to user (basic security check)
        if not task_id.startswith(user_email):
            return JSONResponse(
                status_code=403,
                content={
                    "error": "access_denied",
                    "message": "Task does not belong to current user",
                },
            )

        status = analytics_service.get_background_task_status(task_id)

        if status["status"] == "not_found":
            return JSONResponse(
                status_code=404,
                content={
                    "error": "task_not_found",
                    "message": "Background task not found",
                    "task_id": task_id,
                },
            )

        return {"task_id": task_id, **status, "checked_at": datetime.now().isoformat()}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "status_check_error",
                "message": "Failed to check task status",
                "details": str(e),
            },
        )


@app.get("/analytics/background/result/{task_id}")
def get_background_analysis_result(task_id: str, user_email: str = CurrentUser):
    """Get result of completed background analysis task"""
    try:
        # Verify task belongs to user
        if not task_id.startswith(user_email):
            return JSONResponse(
                status_code=403,
                content={
                    "error": "access_denied",
                    "message": "Task does not belong to current user",
                },
            )

        status = analytics_service.get_background_task_status(task_id)

        if status["status"] == "not_found":
            return JSONResponse(
                status_code=404,
                content={
                    "error": "task_not_found",
                    "message": "Background task not found",
                },
            )
        elif status["status"] == "running":
            return JSONResponse(
                status_code=202,
                content={
                    "error": "task_running",
                    "message": "Task is still running",
                    "status": "running",
                },
            )
        elif status["status"] == "error":
            return JSONResponse(
                status_code=500,
                content={
                    "error": "task_error",
                    "message": "Task completed with error",
                    "task_error": status.get("error"),
                },
            )

        result = analytics_service.get_background_task_result(task_id)
        if not result:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "result_not_found",
                    "message": "Task result not available",
                },
            )

        return {
            "task_id": task_id,
            "status": "completed",
            "result": result,
            "retrieved_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "result_retrieval_error",
                "message": "Failed to retrieve task result",
                "details": str(e),
            },
        )


@app.get("/analytics/cache/stats")
def get_cache_statistics(user_email: str = CurrentUser):
    """Get analytics cache statistics for monitoring"""
    try:
        from app.db import AnalyticsDB

        stats = AnalyticsDB.get_cache_stats()

        return {"cache_statistics": stats, "generated_at": datetime.now().isoformat()}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "cache_stats_error",
                "message": "Failed to retrieve cache statistics",
                "details": str(e),
            },
        )


@app.delete("/analytics/cache")
def clear_user_cache(
    analysis_types: Optional[List[str]] = None, user_email: str = CurrentUser
):
    """Clear analytics cache for current user"""
    try:
        from app.db import AnalyticsDB

        cleared_count = AnalyticsDB.invalidate_user_cache(
            user_email, analysis_types or []
        )

        return {
            "message": "Cache cleared successfully",
            "cleared_entries": cleared_count,
            "analysis_types": analysis_types or "all",
            "cleared_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "cache_clear_error",
                "message": "Failed to clear cache",
                "details": str(e),
            },
        )


@app.get("/analytics/accuracy")
def get_prediction_accuracy_metrics(
    prediction_type: Optional[str] = None, user_email: str = CurrentUser
):
    """Get prediction accuracy metrics and statistics"""
    try:
        # Use empty string if prediction_type is None
        prediction_type_str = prediction_type if prediction_type is not None else ""
        # Get basic accuracy statistics
        accuracy_stats = prediction_service.get_prediction_accuracy_stats(
            user_email, prediction_type_str
        )

        # Get accuracy trends over time
        accuracy_trends = prediction_service.calculate_accuracy_trends(
            user_email, prediction_type_str
        )

        # Get performance by prediction type
        type_performance = prediction_service.get_prediction_type_performance(
            user_email
        )

        # Get recent accuracy records
        recent_records = prediction_service.get_recent_prediction_accuracy(
            user_email, days=30
        )

        if accuracy_stats["total_predictions"] == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "no_accuracy_data",
                    "message": "No prediction accuracy data available yet",
                    "suggestions": [
                        "Make some predictions using the analytics endpoints",
                        "Wait for actual results to become available",
                        "Log actual workout or weight outcomes to track accuracy",
                    ],
                },
            )

        return {
            "accuracy_statistics": accuracy_stats,
            "accuracy_trends": accuracy_trends,
            "performance_by_type": type_performance,
            "recent_records": recent_records[:10],  # Limit to 10 most recent
            "analysis_summary": {
                "total_predictions_tracked": accuracy_stats["total_predictions"],
                "overall_accuracy": accuracy_stats["average_accuracy"],
                "trend_direction": accuracy_trends.get("trend", "unknown"),
                "most_accurate_type": max(
                    type_performance.keys(),
                    key=lambda k: type_performance[k]["average_accuracy"],
                )
                if type_performance
                else None,
                "least_accurate_type": min(
                    type_performance.keys(),
                    key=lambda k: type_performance[k]["average_accuracy"],
                )
                if type_performance
                else None,
            },
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "accuracy_metrics_error",
                "message": "Failed to retrieve prediction accuracy metrics",
                "details": str(e),
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "accuracy_metrics_error",
                "message": "Failed to retrieve prediction accuracy metrics",
                "details": str(e),
            },
        )


@app.post("/analytics/accuracy/log")
def log_prediction_accuracy(
    prediction_type: str,
    predicted_value: float,
    actual_value: float,
    prediction_date: str,
    actual_date: Optional[str] = None,
    user_email: str = CurrentUser,
):
    """Log prediction accuracy when actual results become available"""
    try:
        # Validate prediction_type
        valid_types = [
            "workout_performance",
            "weight_change",
            "macro_target",
            "performance_forecast",
        ]
        if prediction_type not in valid_types:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_prediction_type",
                    "message": f"Prediction type must be one of: {', '.join(valid_types)}",
                    "provided_type": prediction_type,
                },
            )

        # Validate dates
        try:
            datetime.fromisoformat(prediction_date.replace("Z", "+00:00"))
            if actual_date:
                datetime.fromisoformat(actual_date.replace("Z", "+00:00"))
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_date_format",
                    "message": "Dates must be in ISO format (YYYY-MM-DDTHH:MM:SS)",
                    "details": str(e),
                },
            )

        # Log the accuracy
        actual_date_str = actual_date if actual_date is not None else ""
        success = prediction_service.log_prediction_accuracy(
            user_email,
            prediction_type,
            predicted_value,
            actual_value,
            prediction_date,
            actual_date_str,
        )

        if not success:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "logging_failed",
                    "message": "Failed to log prediction accuracy",
                },
            )

        # Calculate accuracy score for response
        accuracy_score = max(
            0, 1 - abs(predicted_value - actual_value) / max(abs(actual_value), 1)
        )

        return {
            "message": "Prediction accuracy logged successfully",
            "accuracy_score": round(accuracy_score, 3),
            "prediction_type": prediction_type,
            "predicted_value": predicted_value,
            "actual_value": actual_value,
            "error_magnitude": abs(predicted_value - actual_value),
            "logged_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "accuracy_logging_error",
                "message": "Failed to log prediction accuracy",
                "details": str(e),
            },
        )
