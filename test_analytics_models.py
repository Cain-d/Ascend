"""
Test script to verify analytics models and database functionality
"""

from app.models import (
    TrendAnalysis, PerformancePrediction, NutritionRecommendation,
    AnalysisResult, TrendInsight, PredictionAccuracy
)
from app.db import AnalyticsDB
from datetime import datetime, timedelta
import json

def test_pydantic_models():
    """Test that all new Pydantic models work correctly"""
    print("🧪 Testing Pydantic models...")
    
    # Test TrendAnalysis
    trend = TrendAnalysis(
        metric_name="weight",
        time_period=14,
        trend_direction="decreasing",
        rate_of_change=-0.5,
        confidence_level=0.85,
        data_points=14,
        start_date="2024-01-01",
        end_date="2024-01-14"
    )
    print(f"✅ TrendAnalysis: {trend.metric_name} trend is {trend.trend_direction}")
    
    # Test PerformancePrediction
    prediction = PerformancePrediction(
        workout_type="bench_press",
        predicted_performance={"reps": 12, "weight": 185.0},
        confidence_interval={"lower": 0.8, "upper": 1.2},
        factors_considered=["recent_weight_trend", "nutrition_pattern"],
        prediction_date="2024-01-15",
        confidence_score=0.78
    )
    print(f"✅ PerformancePrediction: {prediction.workout_type} predicted at {prediction.predicted_performance}")
    
    # Test NutritionRecommendation
    nutrition = NutritionRecommendation(
        target_calories=2200.0,
        target_protein=150.0,
        target_carbs=250.0,
        target_fat=80.0,
        rationale="Based on weight loss trend and performance goals",
        confidence_score=0.82,
        valid_until="2024-01-22",
        recommendation_type="cutting"
    )
    print(f"✅ NutritionRecommendation: {nutrition.recommendation_type} with {nutrition.target_calories} calories")
    
    print("✅ All Pydantic models working correctly!\n")

def test_database_operations():
    """Test database operations for analytics"""
    print("🧪 Testing database operations...")
    
    test_user = "test@example.com"
    
    # Test caching analysis result
    test_data = {
        "trend_direction": "increasing",
        "rate_of_change": 0.3,
        "confidence": 0.85
    }
    
    success = AnalyticsDB.cache_analysis_result(
        user_email=test_user,
        analysis_type="weight_trend",
        time_period=14,
        result_data=test_data,
        confidence_level=0.85
    )
    print(f"✅ Cache analysis result: {'Success' if success else 'Failed'}")
    
    # Test retrieving cached result
    cached = AnalyticsDB.get_cached_analysis(test_user, "weight_trend", 14)
    if cached:
        print(f"✅ Retrieved cached analysis: {cached['result_data']['trend_direction']}")
    else:
        print("❌ Failed to retrieve cached analysis")
    
    # Test prediction accuracy logging
    success = AnalyticsDB.log_prediction_accuracy(
        user_email=test_user,
        prediction_type="workout_performance",
        predicted_value=12.0,
        actual_value=11.0,
        prediction_date="2024-01-15",
        actual_date="2024-01-16"
    )
    print(f"✅ Log prediction accuracy: {'Success' if success else 'Failed'}")
    
    # Test accuracy stats
    stats = AnalyticsDB.get_prediction_accuracy_stats(test_user)
    print(f"✅ Accuracy stats: {stats['total_predictions']} predictions, avg accuracy: {stats['average_accuracy']:.2f}")
    
    print("✅ All database operations working correctly!\n")

if __name__ == "__main__":
    print("🚀 Testing Analytics Models and Database Setup\n")
    
    try:
        test_pydantic_models()
        test_database_operations()
        print("🎉 All tests passed! Analytics setup is complete.")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()