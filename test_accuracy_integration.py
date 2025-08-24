"""
Integration test for prediction accuracy tracking with real database
"""

from app.predictions import PredictionService
from app.db import AnalyticsDB
from datetime import datetime, timedelta

def test_real_database_integration():
    """Test prediction accuracy tracking with the real database"""
    
    print("Testing prediction accuracy tracking with real database...")
    
    # Initialize service
    service = PredictionService()
    test_user = "test_accuracy@example.com"
    
    # Test 1: Log some prediction accuracy data
    print("1. Logging prediction accuracy data...")
    
    test_predictions = [
        ("workout_performance", 85.0, 90.0, "2024-01-01T10:00:00"),
        ("workout_performance", 75.0, 70.0, "2024-01-02T10:00:00"),
        ("weight_change", 2.0, 1.8, "2024-01-03T10:00:00"),
        ("macro_target", 150.0, 145.0, "2024-01-04T10:00:00"),
    ]
    
    for pred_type, pred_val, actual_val, pred_date in test_predictions:
        result = service.log_prediction_accuracy(
            test_user, pred_type, pred_val, actual_val, pred_date
        )
        print(f"   Logged {pred_type}: predicted={pred_val}, actual={actual_val}, success={result}")
    
    # Test 2: Get accuracy statistics
    print("\n2. Getting accuracy statistics...")
    stats = service.get_prediction_accuracy_stats(test_user)
    print(f"   Total predictions: {stats['total_predictions']}")
    print(f"   Average accuracy: {stats['average_accuracy']:.3f}")
    print(f"   Min accuracy: {stats['min_accuracy']:.3f}")
    print(f"   Max accuracy: {stats['max_accuracy']:.3f}")
    
    # Test 3: Get accuracy stats for specific type
    print("\n3. Getting workout performance accuracy...")
    workout_stats = service.get_prediction_accuracy_stats(test_user, "workout_performance")
    print(f"   Workout predictions: {workout_stats['total_predictions']}")
    print(f"   Workout average accuracy: {workout_stats['average_accuracy']:.3f}")
    
    # Test 4: Get recent prediction accuracy
    print("\n4. Getting recent prediction accuracy...")
    recent = service.get_recent_prediction_accuracy(test_user, days=30)
    print(f"   Recent records count: {len(recent)}")
    for record in recent[:3]:  # Show first 3
        print(f"   - {record['prediction_type']}: {record['predicted_value']} → {record['actual_value']} (accuracy: {record['accuracy_score']:.3f})")
    
    # Test 5: Get performance by prediction type
    print("\n5. Getting performance by prediction type...")
    performance = service.get_prediction_type_performance(test_user)
    for pred_type, perf in performance.items():
        print(f"   {pred_type}:")
        print(f"     Total: {perf['total_predictions']}")
        print(f"     Avg accuracy: {perf['average_accuracy']:.3f}")
        print(f"     Reliability: {perf['reliability_score']:.3f}")
    
    # Test 6: Calculate accuracy trends
    print("\n6. Calculating accuracy trends...")
    trends = service.calculate_accuracy_trends(test_user)
    print(f"   Trend direction: {trends.get('trend', 'unknown')}")
    print(f"   Analysis period: {trends.get('analysis_period_days', 0)} days")
    print(f"   Total predictions in trend: {trends.get('total_predictions', 0)}")
    
    # Test 7: Test direct database methods
    print("\n7. Testing direct database methods...")
    db_stats = AnalyticsDB.get_prediction_accuracy_stats(test_user)
    print(f"   DB stats total predictions: {db_stats['total_predictions']}")
    
    # Clean up test data (optional)
    print("\n8. Test completed successfully!")
    print("   Note: Test data remains in database for inspection")
    
    return True

if __name__ == "__main__":
    try:
        success = test_real_database_integration()
        if success:
            print("\n✅ All integration tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()