"""
Unit tests for analytics service statistical functions
Tests trend analysis, correlation calculations, and statistical measures with known datasets
"""

import unittest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.analytics import AnalyticsService, DataPoint, MacroData
from app.models import TrendAnalysis


class TestAnalyticsService(unittest.TestCase):
    """Test cases for AnalyticsService statistical functions"""
    
    def setUp(self):
        """Set up test environment"""
        self.analytics_service = AnalyticsService()
        
        # Create test data points for known statistical properties
        self.linear_increasing_data = [
            DataPoint("2024-01-01", 70.0),
            DataPoint("2024-01-02", 70.5),
            DataPoint("2024-01-03", 71.0),
            DataPoint("2024-01-04", 71.5),
            DataPoint("2024-01-05", 72.0),
            DataPoint("2024-01-06", 72.5),
            DataPoint("2024-01-07", 73.0)
        ]
        
        self.linear_decreasing_data = [
            DataPoint("2024-01-01", 80.0),
            DataPoint("2024-01-02", 79.5),
            DataPoint("2024-01-03", 79.0),
            DataPoint("2024-01-04", 78.5),
            DataPoint("2024-01-05", 78.0),
            DataPoint("2024-01-06", 77.5),
            DataPoint("2024-01-07", 77.0)
        ]
        
        self.stable_data = [
            DataPoint("2024-01-01", 75.0),
            DataPoint("2024-01-02", 75.1),
            DataPoint("2024-01-03", 74.9),
            DataPoint("2024-01-04", 75.0),
            DataPoint("2024-01-05", 75.1),
            DataPoint("2024-01-06", 74.9),
            DataPoint("2024-01-07", 75.0)
        ]
        
        self.noisy_data = [
            DataPoint("2024-01-01", 70.0),
            DataPoint("2024-01-02", 72.0),
            DataPoint("2024-01-03", 69.0),
            DataPoint("2024-01-04", 73.0),
            DataPoint("2024-01-05", 68.0),
            DataPoint("2024-01-06", 74.0),
            DataPoint("2024-01-07", 67.0)
        ]
    
    def test_calculate_linear_slope_increasing(self):
        """Test linear slope calculation with increasing data"""
        slope = self.analytics_service._calculate_linear_slope(self.linear_increasing_data)
        
        # Expected slope is 0.5 per day
        self.assertAlmostEqual(slope, 0.5, places=2)
    
    def test_calculate_linear_slope_decreasing(self):
        """Test linear slope calculation with decreasing data"""
        slope = self.analytics_service._calculate_linear_slope(self.linear_decreasing_data)
        
        # Expected slope is -0.5 per day
        self.assertAlmostEqual(slope, -0.5, places=2)
    
    def test_calculate_linear_slope_stable(self):
        """Test linear slope calculation with stable data"""
        slope = self.analytics_service._calculate_linear_slope(self.stable_data)
        
        # Expected slope is approximately 0
        self.assertAlmostEqual(slope, 0.0, places=1)
    
    def test_calculate_linear_slope_empty_data(self):
        """Test linear slope calculation with empty data"""
        slope = self.analytics_service._calculate_linear_slope([])
        self.assertEqual(slope, 0.0)
    
    def test_calculate_linear_slope_single_point(self):
        """Test linear slope calculation with single data point"""
        single_point = [DataPoint("2024-01-01", 70.0)]
        slope = self.analytics_service._calculate_linear_slope(single_point)
        self.assertEqual(slope, 0.0)
    
    def test_determine_trend_direction(self):
        """Test trend direction determination"""
        # Test increasing trend
        self.assertEqual(
            self.analytics_service._determine_trend_direction(0.5), 
            "increasing"
        )
        
        # Test decreasing trend
        self.assertEqual(
            self.analytics_service._determine_trend_direction(-0.5), 
            "decreasing"
        )
        
        # Test stable trend
        self.assertEqual(
            self.analytics_service._determine_trend_direction(0.005), 
            "stable"
        )
        
        # Test threshold boundary
        self.assertEqual(
            self.analytics_service._determine_trend_direction(0.01), 
            "stable"
        )
    
    def test_calculate_trend_confidence_perfect_linear(self):
        """Test confidence calculation with perfect linear data"""
        slope = self.analytics_service._calculate_linear_slope(self.linear_increasing_data)
        confidence = self.analytics_service._calculate_trend_confidence(
            self.linear_increasing_data, slope
        )
        
        # Perfect linear data should have reasonable confidence (adjusted for 7 data points)
        self.assertGreater(confidence, 0.4)  # 7/14 * 1.0 = 0.5 expected
    
    def test_calculate_trend_confidence_noisy_data(self):
        """Test confidence calculation with noisy data"""
        slope = self.analytics_service._calculate_linear_slope(self.noisy_data)
        confidence = self.analytics_service._calculate_trend_confidence(
            self.noisy_data, slope
        )
        
        # Noisy data should have lower confidence
        self.assertLess(confidence, 0.5)
    
    def test_calculate_trend_confidence_insufficient_data(self):
        """Test confidence calculation with insufficient data"""
        insufficient_data = [DataPoint("2024-01-01", 70.0), DataPoint("2024-01-02", 70.5)]
        confidence = self.analytics_service._calculate_trend_confidence(
            insufficient_data, 0.5
        )
        
        # Should return low confidence for insufficient data
        self.assertLessEqual(confidence, 0.1)
    
    def test_calculate_trend_statistics(self):
        """Test comprehensive trend statistics calculation"""
        stats = self.analytics_service.calculate_trend_statistics(self.linear_increasing_data)
        
        # Verify expected statistical measures
        self.assertIn("mean", stats)
        self.assertIn("median", stats)
        self.assertIn("std_dev", stats)
        self.assertIn("min", stats)
        self.assertIn("max", stats)
        self.assertIn("range", stats)
        self.assertIn("slope", stats)
        self.assertIn("trend_strength", stats)
        
        # Verify calculated values
        values = [point.value for point in self.linear_increasing_data]
        self.assertAlmostEqual(stats["mean"], sum(values) / len(values), places=2)
        self.assertAlmostEqual(stats["min"], min(values), places=2)
        self.assertAlmostEqual(stats["max"], max(values), places=2)
        self.assertAlmostEqual(stats["range"], max(values) - min(values), places=2)
        self.assertAlmostEqual(stats["slope"], 0.5, places=2)
    
    def test_calculate_trend_statistics_empty_data(self):
        """Test trend statistics with empty data"""
        stats = self.analytics_service.calculate_trend_statistics([])
        self.assertEqual(stats, {})
    
    def test_calculate_correlation_perfect_positive(self):
        """Test correlation calculation with perfect positive correlation"""
        x_values = [1, 2, 3, 4, 5]
        y_values = [2, 4, 6, 8, 10]  # y = 2x
        
        correlation = self.analytics_service._calculate_correlation(x_values, y_values)
        self.assertAlmostEqual(correlation, 1.0, places=2)
    
    def test_calculate_correlation_perfect_negative(self):
        """Test correlation calculation with perfect negative correlation"""
        x_values = [1, 2, 3, 4, 5]
        y_values = [10, 8, 6, 4, 2]  # y = -2x + 12
        
        correlation = self.analytics_service._calculate_correlation(x_values, y_values)
        self.assertAlmostEqual(correlation, -1.0, places=2)
    
    def test_calculate_correlation_no_correlation(self):
        """Test correlation calculation with no correlation"""
        x_values = [1, 2, 3, 4, 5]
        y_values = [3, 1, 4, 1, 5]  # Random values
        
        correlation = self.analytics_service._calculate_correlation(x_values, y_values)
        # Should be close to 0 for random data
        self.assertLess(abs(correlation), 0.5)
    
    def test_calculate_correlation_insufficient_data(self):
        """Test correlation calculation with insufficient data"""
        x_values = [1]
        y_values = [2]
        
        correlation = self.analytics_service._calculate_correlation(x_values, y_values)
        self.assertEqual(correlation, 0.0)
    
    def test_calculate_correlation_mismatched_lengths(self):
        """Test correlation calculation with mismatched array lengths"""
        x_values = [1, 2, 3]
        y_values = [2, 4]
        
        correlation = self.analytics_service._calculate_correlation(x_values, y_values)
        self.assertEqual(correlation, 0.0)
    
    def test_calculate_correlation_with_zeros(self):
        """Test correlation calculation handling zero values"""
        x_values = [1, 2, 3, 4, 5]
        y_values = [0, 0, 0, 0, 0]  # All zeros
        
        correlation = self.analytics_service._calculate_correlation(x_values, y_values)
        self.assertEqual(correlation, 0.0)
    
    def test_align_nutrition_performance_data(self):
        """Test alignment of nutrition and performance data by date"""
        macro_data = [
            MacroData("2024-01-01", 2000, 150, 200, 80),
            MacroData("2024-01-02", 2100, 160, 210, 85),
            MacroData("2024-01-04", 1900, 140, 190, 75)  # Missing 2024-01-03
        ]
        
        performance_data = [
            {"date": "2024-01-01", "estimated_1rm": 100, "total_volume": 5000},
            {"date": "2024-01-03", "estimated_1rm": 105, "total_volume": 5200},  # Missing macro data
            {"date": "2024-01-04", "estimated_1rm": 102, "total_volume": 4800}
        ]
        
        aligned_data = self.analytics_service._align_nutrition_performance_data(
            macro_data, performance_data
        )
        
        # Should only have data for dates present in both datasets
        self.assertEqual(len(aligned_data), 2)  # 2024-01-01 and 2024-01-04
        
        # Verify data alignment
        self.assertEqual(aligned_data[0]["date"], "2024-01-01")
        self.assertEqual(aligned_data[0]["calories"], 2000)
        self.assertEqual(aligned_data[0]["estimated_1rm"], 100)
        
        self.assertEqual(aligned_data[1]["date"], "2024-01-04")
        self.assertEqual(aligned_data[1]["calories"], 1900)
        self.assertEqual(aligned_data[1]["estimated_1rm"], 102)
    
    def test_validate_correlation_data_requirements_sufficient_data(self):
        """Test data validation with sufficient data"""
        # Mock the data retrieval methods to return sufficient data
        with patch.object(self.analytics_service, '_get_macro_data') as mock_macro, \
             patch.object(self.analytics_service, '_get_performance_data') as mock_perf, \
             patch.object(self.analytics_service, '_align_nutrition_performance_data') as mock_align:
            
            # Mock sufficient data
            mock_macro.return_value = [MacroData(f"2024-01-{i:02d}", 2000, 150, 200, 80) for i in range(1, 16)]  # 15 days
            mock_perf.return_value = [{"date": f"2024-01-{i:02d}", "estimated_1rm": 100, "total_volume": 5000} for i in range(1, 16)]  # 15 days
            mock_align.return_value = [{"date": f"2024-01-{i:02d}", "calories": 2000} for i in range(1, 12)]  # 11 aligned points
            
            result = self.analytics_service._validate_correlation_data_requirements("test@example.com", 30)
            
            self.assertTrue(result["valid"])
            self.assertEqual(result["message"], "Sufficient data for correlation analysis")
            self.assertEqual(result["requirements"]["current_macro_days"], 15)
            self.assertEqual(result["requirements"]["current_performance_days"], 15)
            self.assertEqual(result["requirements"]["current_aligned_points"], 11)
    
    def test_validate_correlation_data_requirements_insufficient_macro_data(self):
        """Test data validation with insufficient macro data"""
        with patch.object(self.analytics_service, '_get_macro_data') as mock_macro, \
             patch.object(self.analytics_service, '_get_performance_data') as mock_perf, \
             patch.object(self.analytics_service, '_align_nutrition_performance_data') as mock_align:
            
            # Mock insufficient macro data
            mock_macro.return_value = [MacroData(f"2024-01-{i:02d}", 2000, 150, 200, 80) for i in range(1, 8)]  # Only 7 days
            mock_perf.return_value = [{"date": f"2024-01-{i:02d}", "estimated_1rm": 100, "total_volume": 5000} for i in range(1, 16)]  # 15 days
            mock_align.return_value = [{"date": f"2024-01-{i:02d}", "calories": 2000} for i in range(1, 8)]  # 7 aligned points
            
            result = self.analytics_service._validate_correlation_data_requirements("test@example.com", 30)
            
            self.assertFalse(result["valid"])
            self.assertIn("Need at least 14 days of nutrition data", result["message"])
            self.assertEqual(result["requirements"]["current_macro_days"], 7)
    
    def test_validate_correlation_data_requirements_insufficient_aligned_data(self):
        """Test data validation with insufficient aligned data"""
        with patch.object(self.analytics_service, '_get_macro_data') as mock_macro, \
             patch.object(self.analytics_service, '_get_performance_data') as mock_perf, \
             patch.object(self.analytics_service, '_align_nutrition_performance_data') as mock_align:
            
            # Mock sufficient individual data but insufficient aligned data
            mock_macro.return_value = [MacroData(f"2024-01-{i:02d}", 2000, 150, 200, 80) for i in range(1, 16)]  # 15 days
            mock_perf.return_value = [{"date": f"2024-01-{i:02d}", "estimated_1rm": 100, "total_volume": 5000} for i in range(16, 31)]  # Different 15 days
            mock_align.return_value = []  # No aligned data
            
            result = self.analytics_service._validate_correlation_data_requirements("test@example.com", 30)
            
            self.assertFalse(result["valid"])
            self.assertIn("Need at least 10 days with both nutrition and performance data", result["message"])
            self.assertEqual(result["requirements"]["current_aligned_points"], 0)
    
    def test_calculate_correlation_with_significance_strong_positive(self):
        """Test correlation with significance for strong positive correlation"""
        x_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y_values = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]  # Perfect positive correlation
        
        result = self.analytics_service._calculate_correlation_with_significance(x_values, y_values)
        
        self.assertAlmostEqual(result["correlation"], 1.0, places=3)
        self.assertEqual(result["p_value"], 0.0)  # Perfect correlation has p-value of 0
        self.assertTrue(result["significant"])
        self.assertEqual(result["confidence_level"], "very_high")
        self.assertEqual(result["strength"], "strong")
        self.assertEqual(result["direction"], "positive")
        self.assertEqual(result["interpretation"], "strong_positive")
        self.assertEqual(result["sample_size"], 10)
    
    def test_calculate_correlation_with_significance_moderate_negative(self):
        """Test correlation with significance for moderate negative correlation"""
        x_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y_values = [10, 8, 7, 6, 4, 3, 2, 1, 1, 1]  # Moderate negative correlation with some noise
        
        result = self.analytics_service._calculate_correlation_with_significance(x_values, y_values)
        
        self.assertLess(result["correlation"], -0.3)  # Should be moderately negative
        self.assertGreater(result["correlation"], -1.0)
        self.assertEqual(result["direction"], "negative")
        self.assertIn(result["strength"], ["moderate", "strong"])  # Could be either depending on exact correlation
        self.assertEqual(result["sample_size"], 10)
    
    def test_calculate_correlation_with_significance_no_correlation(self):
        """Test correlation with significance for no correlation"""
        x_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y_values = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]  # Constant values, no correlation
        
        result = self.analytics_service._calculate_correlation_with_significance(x_values, y_values)
        
        self.assertEqual(result["correlation"], 0.0)
        self.assertFalse(result["significant"])
        self.assertEqual(result["strength"], "negligible")
        self.assertEqual(result["direction"], "none")
        self.assertEqual(result["interpretation"], "no_correlation")
    
    def test_calculate_correlation_with_significance_insufficient_data(self):
        """Test correlation with significance for insufficient data"""
        x_values = [1, 2]
        y_values = [2, 4]
        
        result = self.analytics_service._calculate_correlation_with_significance(x_values, y_values)
        
        self.assertEqual(result["correlation"], 0.0)
        self.assertEqual(result["p_value"], 1.0)
        self.assertFalse(result["significant"])
        self.assertEqual(result["confidence_level"], "none")
        self.assertEqual(result["interpretation"], "insufficient_data")
        self.assertEqual(result["sample_size"], 2)
    
    def test_calculate_p_value_from_t_high_significance(self):
        """Test p-value calculation for high t-statistic"""
        # High t-statistic should result in low p-value
        p_value = self.analytics_service._calculate_p_value_from_t(5.0, 20)
        self.assertEqual(p_value, 0.001)
    
    def test_calculate_p_value_from_t_moderate_significance(self):
        """Test p-value calculation for moderate t-statistic"""
        # Moderate t-statistic should result in moderate p-value
        p_value = self.analytics_service._calculate_p_value_from_t(2.5, 20)
        self.assertEqual(p_value, 0.05)  # 2.5 falls in the 0.05 range for our critical values
    
    def test_calculate_p_value_from_t_low_significance(self):
        """Test p-value calculation for low t-statistic"""
        # Low t-statistic should result in high p-value
        p_value = self.analytics_service._calculate_p_value_from_t(1.0, 20)
        self.assertEqual(p_value, 0.20)
    
    def test_calculate_p_value_from_t_insufficient_degrees_freedom(self):
        """Test p-value calculation with insufficient degrees of freedom"""
        p_value = self.analytics_service._calculate_p_value_from_t(5.0, 2)
        self.assertEqual(p_value, 1.0)


class TestAnalyticsServiceIntegration(unittest.TestCase):
    """Integration tests for AnalyticsService with database operations"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        
        # Create test database schema
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        
        # Create minimal schema for testing
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE bodyweight_log (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                date TEXT,
                weight REAL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE meals (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE meal_items (
                id INTEGER PRIMARY KEY,
                meal_id INTEGER,
                food_id INTEGER,
                quantity REAL,
                FOREIGN KEY(meal_id) REFERENCES meals(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE foods (
                id INTEGER PRIMARY KEY,
                name TEXT,
                calories REAL,
                protein REAL,
                carbs REAL,
                fat REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE performance_metrics (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                date TEXT,
                estimated_1rm REAL,
                total_volume REAL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO users (id, email) VALUES (1, 'test@example.com')")
        
        # Insert weight data with clear trend (using recent dates)
        base_date = datetime.now() - timedelta(days=20)  # Start 20 days ago
        for i in range(14):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            weight = 70.0 + i * 0.2  # Increasing trend
            cursor.execute(
                "INSERT INTO bodyweight_log (user_id, date, weight) VALUES (1, ?, ?)",
                (date_str, weight)
            )
        
        conn.commit()
        conn.close()
        
        self.analytics_service = AnalyticsService()
    
    def tearDown(self):
        """Clean up test database"""
        try:
            os.unlink(self.test_db.name)
        except PermissionError:
            # On Windows, file might still be in use
            pass
    
    @patch('app.analytics.get_db_connection')
    def test_get_weight_data_integration(self, mock_get_db):
        """Test weight data retrieval integration"""
        # Create a context manager mock
        mock_context = MagicMock()
        mock_conn = sqlite3.connect(self.test_db.name)
        mock_conn.row_factory = sqlite3.Row
        mock_context.__enter__ = MagicMock(return_value=mock_conn)
        mock_context.__exit__ = MagicMock(return_value=None)
        mock_get_db.return_value = mock_context
        
        weight_data = self.analytics_service._get_weight_data('test@example.com', 30)
        
        # Should retrieve all 14 data points
        self.assertEqual(len(weight_data), 14)
        
        # Verify data structure
        self.assertIsInstance(weight_data[0], DataPoint)
        # Date should be recent (within last 30 days)
        first_date = datetime.fromisoformat(weight_data[0].date)
        self.assertLess((datetime.now() - first_date).days, 30)
        self.assertEqual(weight_data[0].value, 70.0)
        
        # Verify increasing trend in data
        self.assertLess(weight_data[0].value, weight_data[-1].value)
        
        mock_conn.close()
    
    @patch('app.analytics.get_db_connection')
    def test_correlate_nutrition_performance_integration(self, mock_get_db):
        """Test full correlation analysis integration"""
        # Create a context manager mock
        mock_context = MagicMock()
        mock_conn = sqlite3.connect(self.test_db.name)
        mock_conn.row_factory = sqlite3.Row
        mock_context.__enter__ = MagicMock(return_value=mock_conn)
        mock_context.__exit__ = MagicMock(return_value=None)
        mock_get_db.return_value = mock_context
        
        # Add test data for correlation analysis
        cursor = mock_conn.cursor()
        
        # Add more comprehensive test data
        base_date = datetime.now() - timedelta(days=30)
        
        # Add nutrition data (meals and foods)
        cursor.execute("INSERT INTO foods (id, name, calories, protein, carbs, fat) VALUES (1, 'Test Food', 100, 10, 15, 5)")
        
        for i in range(20):  # 20 days of data
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Add meal
            cursor.execute("INSERT INTO meals (id, user_id, timestamp) VALUES (?, 1, ?)", (i+1, date_str))
            
            # Add meal items with varying quantities to create correlation patterns
            quantity = 2.0 + (i * 0.1)  # Increasing nutrition over time
            cursor.execute("INSERT INTO meal_items (meal_id, food_id, quantity) VALUES (?, 1, ?)", (i+1, quantity))
            
            # Add performance data that correlates with nutrition
            performance_value = 1000 + (i * 50)  # Increasing performance over time
            estimated_1rm = 100 + (i * 2)
            cursor.execute(
                "INSERT INTO performance_metrics (user_id, date, total_volume, estimated_1rm) VALUES (1, ?, ?, ?)",
                ((base_date + timedelta(days=i)).strftime('%Y-%m-%d'), performance_value, estimated_1rm)
            )
        
        mock_conn.commit()
        
        # Test correlation analysis
        result = self.analytics_service.correlate_nutrition_performance('test@example.com', 60)
        
        # Should not have error since we have sufficient data
        self.assertNotIn("error", result)
        
        # Should have metadata
        self.assertIn("metadata", result)
        self.assertGreater(result["metadata"]["data_points"], 10)
        
        # Should have correlation results for each macro
        expected_correlations = [
            "calories_vs_volume", "protein_vs_volume", "carbs_vs_volume", "fat_vs_volume",
            "calories_vs_1rm", "protein_vs_1rm", "carbs_vs_1rm", "fat_vs_1rm"
        ]
        
        for correlation_key in expected_correlations:
            self.assertIn(correlation_key, result)
            correlation_result = result[correlation_key]
            
            # Should have all required fields
            self.assertIn("correlation", correlation_result)
            self.assertIn("p_value", correlation_result)
            self.assertIn("significant", correlation_result)
            self.assertIn("confidence_level", correlation_result)
            self.assertIn("strength", correlation_result)
            self.assertIn("direction", correlation_result)
            self.assertIn("interpretation", correlation_result)
            self.assertIn("sample_size", correlation_result)
            
            # Given our test data setup, correlations should be positive and strong
            self.assertGreater(correlation_result["correlation"], 0.7)
            self.assertEqual(correlation_result["direction"], "positive")
            self.assertEqual(correlation_result["strength"], "strong")
            self.assertTrue(correlation_result["significant"])
        
        mock_conn.close()
    
    @patch('app.analytics.get_db_connection')
    def test_correlate_nutrition_performance_insufficient_data(self, mock_get_db):
        """Test correlation analysis with insufficient data"""
        # Create a context manager mock with minimal data
        mock_context = MagicMock()
        mock_conn = sqlite3.connect(self.test_db.name)
        mock_conn.row_factory = sqlite3.Row
        mock_context.__enter__ = MagicMock(return_value=mock_conn)
        mock_context.__exit__ = MagicMock(return_value=None)
        mock_get_db.return_value = mock_context
        
        # Only add minimal data (insufficient for correlation)
        cursor = mock_conn.cursor()
        cursor.execute("INSERT INTO foods (id, name, calories, protein, carbs, fat) VALUES (1, 'Test Food', 100, 10, 15, 5)")
        
        # Add only 5 days of data (insufficient)
        base_date = datetime.now() - timedelta(days=10)
        for i in range(5):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO meals (id, user_id, timestamp) VALUES (?, 1, ?)", (i+1, date_str))
            cursor.execute("INSERT INTO meal_items (meal_id, food_id, quantity) VALUES (?, 1, 2.0)", (i+1,))
        
        mock_conn.commit()
        
        # Test correlation analysis
        result = self.analytics_service.correlate_nutrition_performance('test@example.com', 60)
        
        # Should have error due to insufficient data
        self.assertIn("error", result)
        self.assertEqual(result["error"], "insufficient_data")
        self.assertIn("message", result)
        self.assertIn("requirements", result)
        
        mock_conn.close()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)