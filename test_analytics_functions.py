#!/usr/bin/env python3
"""
Unit tests for analytics functions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.analytics import AnalyticsService
from app.predictions import PredictionService

def test_analytics_service():
    """Test analytics service initialization and basic methods"""
    print("Testing Analytics Service")
    print("=" * 30)
    
    try:
        # Test service initialization
        analytics = AnalyticsService()
        print("✅ AnalyticsService initialized successfully")
        
        # Test with non-existent user (should handle gracefully)
        result = analytics.calculate_weight_trends("nonexistent@test.com", 30)
        print(f"✅ Weight trends for non-existent user: {result}")
        
        result = analytics.analyze_macro_patterns("nonexistent@test.com", 30)
        print(f"✅ Macro patterns for non-existent user: {result}")
        
        result = analytics.correlate_nutrition_performance("nonexistent@test.com", 60)
        print(f"✅ Correlations for non-existent user: {type(result).__name__}")
        
    except Exception as e:
        print(f"❌ Analytics service error: {e}")

def test_prediction_service():
    """Test prediction service initialization and basic methods"""
    print("\nTesting Prediction Service")
    print("=" * 30)
    
    try:
        # Test service initialization
        predictions = PredictionService()
        print("✅ PredictionService initialized successfully")
        
        # Test with non-existent user (should handle gracefully)
        result = predictions.predict_workout_performance("nonexistent@test.com")
        print(f"✅ Performance prediction for non-existent user: {result}")
        
        result = predictions.recommend_macro_targets("nonexistent@test.com")
        print(f"✅ Macro recommendations for non-existent user: {result}")
        
        result = predictions.generate_intervention_suggestions("nonexistent@test.com")
        print(f"✅ Intervention suggestions for non-existent user: {len(result)} suggestions")
        
    except Exception as e:
        print(f"❌ Prediction service error: {e}")

def test_database_connection():
    """Test database connection and table existence"""
    print("\nTesting Database Connection")
    print("=" * 30)
    
    try:
        from app.db import get_db_connection, AnalyticsDB
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if analytics tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='analytics_cache' OR name='prediction_accuracy')")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            if 'analytics_cache' in table_names:
                print("✅ analytics_cache table exists")
            else:
                print("❌ analytics_cache table missing")
                
            if 'prediction_accuracy' in table_names:
                print("✅ prediction_accuracy table exists")
            else:
                print("❌ prediction_accuracy table missing")
        
        # Test AnalyticsDB methods
        analytics_db = AnalyticsDB()
        
        # Test cache operations (should not fail)
        result = analytics_db.get_cached_analysis("test@test.com", "test_type", 30)
        print(f"✅ Cache retrieval works: {result}")
        
        # Test accuracy stats (should not fail)
        stats = analytics_db.get_prediction_accuracy_stats("test@test.com")
        print(f"✅ Accuracy stats work: {stats}")
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")

if __name__ == "__main__":
    test_analytics_service()
    test_prediction_service()
    test_database_connection()
    print("\n" + "=" * 50)
    print("Analytics functions test completed!")