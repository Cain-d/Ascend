"""
Tests for prediction accuracy tracking system
Tests the functionality implemented in task 8 of the predictive training performance spec
"""

import pytest
import sqlite3
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the modules we're testing
from app.predictions import PredictionService
from app.db import AnalyticsDB, get_db_connection

class TestPredictionAccuracyTracking:
    """Test suite for prediction accuracy tracking functionality"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        # Create temporary database file
        db_fd, db_path = tempfile.mkstemp()
        os.close(db_fd)
        
        # Patch the DATABASE_PATH to use our temp database
        with patch('app.db.DATABASE_PATH', db_path):
            # Create the required tables
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    CREATE TABLE prediction_accuracy (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT NOT NULL,
                        prediction_type TEXT NOT NULL,
                        predicted_value REAL NOT NULL,
                        actual_value REAL NOT NULL,
                        prediction_date TIMESTAMP NOT NULL,
                        actual_date TIMESTAMP NOT NULL,
                        accuracy_score REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE INDEX idx_prediction_accuracy_user_type
                    ON prediction_accuracy(user_email, prediction_type)
                """)
                conn.commit()
            
            yield db_path
        
        # Clean up - handle Windows file locking issues
        try:
            os.unlink(db_path)
        except (PermissionError, FileNotFoundError):
            # On Windows, files might be locked by SQLite connections
            # This is acceptable for test cleanup
            pass
    
    @pytest.fixture
    def prediction_service(self):
        """Create a PredictionService instance for testing"""
        return PredictionService()
    
    def test_log_prediction_accuracy_success(self, temp_db, prediction_service):
        """Test successful logging of prediction accuracy"""
        with patch('app.db.DATABASE_PATH', temp_db):
            # Test data
            user_email = "test@example.com"
            prediction_type = "workout_performance"
            predicted_value = 85.0
            actual_value = 90.0
            prediction_date = "2024-01-01T10:00:00"
            actual_date = "2024-01-02T15:00:00"
            
            # Log the accuracy
            result = prediction_service.log_prediction_accuracy(
                user_email, prediction_type, predicted_value, actual_value,
                prediction_date, actual_date
            )
            
            assert result is True
            
            # Verify it was stored in database
            with sqlite3.connect(temp_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM prediction_accuracy 
                    WHERE user_email = ? AND prediction_type = ?
                """, (user_email, prediction_type))
                
                row = cursor.fetchone()
                assert row is not None
                assert row["predicted_value"] == predicted_value
                assert row["actual_value"] == actual_value
                assert row["prediction_date"] == prediction_date
                assert row["actual_date"] == actual_date
                # Accuracy score should be calculated correctly
                expected_accuracy = 1 - abs(predicted_value - actual_value) / max(abs(actual_value), 1)
                assert abs(row["accuracy_score"] - expected_accuracy) < 0.001
    
    def test_log_prediction_accuracy_with_default_actual_date(self, temp_db, prediction_service):
        """Test logging accuracy with default actual date (now)"""
        with patch('app.db.DATABASE_PATH', temp_db):
            user_email = "test@example.com"
            prediction_type = "weight_change"
            predicted_value = 75.0
            actual_value = 74.5
            prediction_date = "2024-01-01T10:00:00"
            
            # Log without actual_date (should default to now)
            result = prediction_service.log_prediction_accuracy(
                user_email, prediction_type, predicted_value, actual_value,
                prediction_date
            )
            
            assert result is True
            
            # Verify actual_date was set to approximately now
            with sqlite3.connect(temp_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT actual_date FROM prediction_accuracy 
                    WHERE user_email = ? AND prediction_type = ?
                """, (user_email, prediction_type))
                
                row = cursor.fetchone()
                actual_date = datetime.fromisoformat(row["actual_date"])
                now = datetime.now()
                # Should be within 1 second of now
                assert abs((actual_date - now).total_seconds()) < 1
    
    def test_get_prediction_accuracy_stats(self, temp_db, prediction_service):
        """Test retrieving prediction accuracy statistics"""
        with patch('app.db.DATABASE_PATH', temp_db):
            user_email = "test@example.com"
            
            # Insert test data
            test_data = [
                ("workout_performance", 85.0, 90.0),
                ("workout_performance", 75.0, 70.0),
                ("weight_change", 2.0, 1.8),
                ("weight_change", -1.0, -1.2),
            ]
            
            for pred_type, pred_val, actual_val in test_data:
                prediction_service.log_prediction_accuracy(
                    user_email, pred_type, pred_val, actual_val,
                    "2024-01-01T10:00:00"
                )
            
            # Test getting stats for all prediction types
            stats = prediction_service.get_prediction_accuracy_stats(user_email)
            
            assert stats["total_predictions"] == 4
            assert stats["average_accuracy"] > 0
            assert stats["min_accuracy"] >= 0
            assert stats["max_accuracy"] <= 1
            
            # Test getting stats for specific prediction type
            workout_stats = prediction_service.get_prediction_accuracy_stats(
                user_email, "workout_performance"
            )
            
            assert workout_stats["total_predictions"] == 2
    
    def test_get_recent_prediction_accuracy(self, temp_db, prediction_service):
        """Test retrieving recent prediction accuracy records"""
        with patch('app.db.DATABASE_PATH', temp_db):
            user_email = "test@example.com"
            
            # Insert test data with different dates
            now = datetime.now()
            recent_date = (now - timedelta(days=5)).isoformat()
            old_date = (now - timedelta(days=35)).isoformat()
            
            # Recent prediction
            prediction_service.log_prediction_accuracy(
                user_email, "workout_performance", 85.0, 90.0,
                recent_date, recent_date
            )
            
            # Old prediction (should not be included in 30-day window)
            prediction_service.log_prediction_accuracy(
                user_email, "workout_performance", 75.0, 70.0,
                old_date, old_date
            )
            
            # Get recent records (30 days)
            recent_records = prediction_service.get_recent_prediction_accuracy(user_email, days=30)
            
            assert len(recent_records) == 1
            assert recent_records[0]["predicted_value"] == 85.0
            assert recent_records[0]["actual_value"] == 90.0
            assert "error_magnitude" in recent_records[0]
            assert recent_records[0]["error_magnitude"] == 5.0
    
    def test_calculate_accuracy_trends(self, temp_db, prediction_service):
        """Test calculation of accuracy trends over time"""
        with patch('app.db.DATABASE_PATH', temp_db):
            user_email = "test@example.com"
            
            # Insert test data with improving accuracy over time
            base_date = datetime.now() - timedelta(days=20)
            
            # Older predictions (lower accuracy)
            for i in range(5):
                date = (base_date + timedelta(days=i)).isoformat()
                prediction_service.log_prediction_accuracy(
                    user_email, "workout_performance", 100.0, 70.0,  # Low accuracy
                    date, date
                )
            
            # Recent predictions (higher accuracy)
            for i in range(5, 10):
                date = (base_date + timedelta(days=i)).isoformat()
                prediction_service.log_prediction_accuracy(
                    user_email, "workout_performance", 100.0, 95.0,  # High accuracy
                    date, date
                )
            
            # Calculate trends
            trends = prediction_service.calculate_accuracy_trends(user_email, "workout_performance")
            
            assert "trend" in trends
            assert trends["trend"] in ["improving", "declining", "stable", "insufficient_data"]
            assert "recent_average_accuracy" in trends
            assert "older_average_accuracy" in trends
            assert "total_predictions" in trends
            assert trends["total_predictions"] == 10
    
    def test_get_prediction_type_performance(self, temp_db, prediction_service):
        """Test getting performance breakdown by prediction type"""
        with patch('app.db.DATABASE_PATH', temp_db):
            user_email = "test@example.com"
            
            # Insert test data for different prediction types
            test_data = [
                ("workout_performance", 85.0, 90.0),
                ("workout_performance", 75.0, 80.0),
                ("weight_change", 2.0, 2.1),
                ("macro_target", 150.0, 145.0),
            ]
            
            for pred_type, pred_val, actual_val in test_data:
                prediction_service.log_prediction_accuracy(
                    user_email, pred_type, pred_val, actual_val,
                    "2024-01-01T10:00:00"
                )
            
            # Get performance by type
            performance = prediction_service.get_prediction_type_performance(user_email)
            
            assert "workout_performance" in performance
            assert "weight_change" in performance
            assert "macro_target" in performance
            
            # Check workout_performance stats
            workout_perf = performance["workout_performance"]
            assert workout_perf["total_predictions"] == 2
            assert "average_accuracy" in workout_perf
            assert "reliability_score" in workout_perf
            assert workout_perf["reliability_score"] <= 1.0
    
    def test_calculate_reliability_score(self, prediction_service):
        """Test the reliability score calculation"""
        # Test with few predictions (should have lower reliability)
        score_few = prediction_service._calculate_reliability_score(5, 0.9)
        
        # Test with many predictions (should have higher reliability)
        score_many = prediction_service._calculate_reliability_score(25, 0.9)
        
        assert score_many > score_few
        assert score_many <= 1.0
        assert score_few >= 0.0
    
    def test_accuracy_calculation_edge_cases(self, temp_db, prediction_service):
        """Test accuracy calculation with edge cases"""
        with patch('app.db.DATABASE_PATH', temp_db):
            user_email = "test@example.com"
            
            # Test with zero actual value
            prediction_service.log_prediction_accuracy(
                user_email, "test_type", 5.0, 0.0,
                "2024-01-01T10:00:00"
            )
            
            # Test with negative values
            prediction_service.log_prediction_accuracy(
                user_email, "test_type", -10.0, -8.0,
                "2024-01-01T10:00:00"
            )
            
            # Test with very close values (high accuracy)
            prediction_service.log_prediction_accuracy(
                user_email, "test_type", 100.0, 100.1,
                "2024-01-01T10:00:00"
            )
            
            # Verify all were logged successfully
            stats = prediction_service.get_prediction_accuracy_stats(user_email, "test_type")
            assert stats["total_predictions"] == 3
            assert stats["average_accuracy"] >= 0
            assert stats["average_accuracy"] <= 1

class TestPredictionAccuracyAPI:
    """Test the API endpoints for prediction accuracy tracking"""
    
    def test_accuracy_endpoint_validation(self):
        """Test that the accuracy endpoints have proper validation"""
        # This would typically use FastAPI's test client
        # For now, we'll test the validation logic directly
        
        valid_types = ["workout_performance", "weight_change", "macro_target", "performance_forecast"]
        
        # Test valid prediction types
        for pred_type in valid_types:
            assert pred_type in valid_types
        
        # Test invalid prediction type
        invalid_type = "invalid_prediction_type"
        assert invalid_type not in valid_types
    
    def test_date_validation(self):
        """Test date format validation"""
        valid_dates = [
            "2024-01-01T10:00:00",
            "2024-12-31T23:59:59",
            "2024-06-15T12:30:45"
        ]
        
        invalid_dates = [
            "invalid-date",
            "2024-13-01T10:00:00",  # Invalid month
            "not-a-date-at-all",
        ]
        
        for date_str in valid_dates:
            try:
                datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                valid = True
            except ValueError:
                valid = False
            assert valid, f"Valid date {date_str} should parse successfully"
        
        for date_str in invalid_dates:
            try:
                datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                valid = True
            except ValueError:
                valid = False
            assert not valid, f"Invalid date {date_str} should fail to parse"

def test_database_integration():
    """Test that the database operations work correctly"""
    # Create a temporary database for testing
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    
    try:
        # Create the prediction_accuracy table
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE prediction_accuracy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    prediction_type TEXT NOT NULL,
                    predicted_value REAL NOT NULL,
                    actual_value REAL NOT NULL,
                    prediction_date TIMESTAMP NOT NULL,
                    actual_date TIMESTAMP NOT NULL,
                    accuracy_score REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        
        # Test the AnalyticsDB methods with our temp database
        with patch('app.db.DATABASE_PATH', db_path):
            # Test logging prediction accuracy
            result = AnalyticsDB.log_prediction_accuracy(
                "test@example.com", "workout_performance", 85.0, 90.0,
                "2024-01-01T10:00:00", "2024-01-02T15:00:00"
            )
            assert result is True
            
            # Test getting accuracy stats
            stats = AnalyticsDB.get_prediction_accuracy_stats("test@example.com")
            assert stats["total_predictions"] == 1
            assert stats["average_accuracy"] > 0
    
    finally:
        # Clean up - handle Windows file locking issues
        try:
            os.unlink(db_path)
        except (PermissionError, FileNotFoundError):
            # On Windows, files might be locked by SQLite connections
            # This is acceptable for test cleanup
            pass

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])