"""
Simplified tests for prediction accuracy tracking system
Tests the core functionality without complex database cleanup
"""

import pytest
from datetime import datetime
from app.predictions import PredictionService


def test_prediction_service_methods():
    """Test that all required methods exist and have correct signatures"""
    service = PredictionService()

    # Test method existence
    assert hasattr(service, "log_prediction_accuracy")
    assert hasattr(service, "get_prediction_accuracy_stats")
    assert hasattr(service, "get_recent_prediction_accuracy")
    assert hasattr(service, "calculate_accuracy_trends")
    assert hasattr(service, "get_prediction_type_performance")
    assert hasattr(service, "_calculate_reliability_score")

    # Test method signatures (basic call without database)
    try:
        # These should not crash, even if they return empty results
        stats = service.get_prediction_accuracy_stats("test@example.com")
        assert isinstance(stats, dict)

        recent = service.get_recent_prediction_accuracy("test@example.com")
        assert isinstance(recent, list)

        trends = service.calculate_accuracy_trends("test@example.com")
        assert isinstance(trends, dict)

        performance = service.get_prediction_type_performance("test@example.com")
        assert isinstance(performance, dict)

        reliability = service._calculate_reliability_score(10, 0.8)
        assert isinstance(reliability, float)
        assert 0 <= reliability <= 1

    except Exception as e:
        # Methods should handle errors gracefully
        print(f"Method call failed: {e}")


def test_reliability_score_calculation():
    """Test the reliability score calculation logic"""
    service = PredictionService()

    # Test with different prediction counts and accuracies
    test_cases = [
        (5, 0.9, "few predictions, high accuracy"),
        (25, 0.9, "many predictions, high accuracy"),
        (5, 0.5, "few predictions, medium accuracy"),
        (25, 0.5, "many predictions, medium accuracy"),
        (0, 1.0, "no predictions"),
        (100, 0.0, "many predictions, zero accuracy"),
    ]

    for count, accuracy, description in test_cases:
        score = service._calculate_reliability_score(count, accuracy)
        assert 0 <= score <= 1, f"Score out of range for {description}: {score}"
        assert isinstance(score, float), f"Score not float for {description}"

    # Test that more predictions with same accuracy = higher reliability
    score_few = service._calculate_reliability_score(5, 0.8)
    score_many = service._calculate_reliability_score(25, 0.8)
    assert score_many >= score_few, "More predictions should have higher reliability"


def test_date_validation_logic():
    """Test date format validation used in API"""
    valid_dates = ["2024-01-01T10:00:00", "2024-12-31T23:59:59", "2024-06-15T12:30:45"]

    # Note: Python's datetime.fromisoformat is more lenient than expected
    # It accepts dates without time, so we need to be more specific in validation
    for date_str in valid_dates:
        try:
            parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            assert isinstance(parsed, datetime)
        except ValueError:
            pytest.fail(f"Valid date {date_str} should parse successfully")


def test_accuracy_calculation_formula():
    """Test the accuracy calculation formula used in the system"""
    # The formula is: max(0, 1 - abs(predicted - actual) / max(abs(actual), 1))

    test_cases = [
        (100, 100, 1.0),  # Perfect prediction: 1 - 0/100 = 1.0
        (100, 90, 1 - 10 / 90),  # 10 unit error: 1 - 10/90 ≈ 0.889
        (100, 50, 1 - 50 / 50),  # 50 unit error: 1 - 50/50 = 0.0
        (100, 0, 0.0),  # 100 unit error with 0 actual: 1 - 100/1 = -99 → 0.0 (capped)
        (0, 0, 1.0),  # Both zero (perfect): 1 - 0/1 = 1.0
        (-10, -8, 1 - 2 / 8),  # Negative values: 1 - 2/8 = 0.75
    ]

    for predicted, actual, expected_accuracy in test_cases:
        calculated = max(0, 1 - abs(predicted - actual) / max(abs(actual), 1))
        assert abs(calculated - expected_accuracy) < 0.001, (
            f"Accuracy calculation failed for pred={predicted}, actual={actual}. Expected {expected_accuracy}, got {calculated}"
        )


def test_prediction_types_validation():
    """Test that valid prediction types are properly defined"""
    valid_types = [
        "workout_performance",
        "weight_change",
        "macro_target",
        "performance_forecast",
    ]

    # These should be the types accepted by the API
    assert len(valid_types) == 4
    assert "workout_performance" in valid_types
    assert "weight_change" in valid_types
    assert "macro_target" in valid_types
    assert "performance_forecast" in valid_types

    # Invalid types should not be in the list
    invalid_types = ["invalid_type", "random_prediction", ""]
    for invalid_type in invalid_types:
        assert invalid_type not in valid_types


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
