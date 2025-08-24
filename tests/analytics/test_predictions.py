"""
Unit tests for prediction service recommendation generation
Tests macro target recommendations, intervention suggestions, and confidence scoring
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.predictions import PredictionService, HistoricalPattern
from app.models import NutritionRecommendation, PerformancePrediction
from app.analytics import DataPoint, MacroData


class TestRecommendationEngine(unittest.TestCase):
    """Test cases for recommendation engine functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.prediction_service = PredictionService()
        
        # Create test historical patterns
        self.weight_pattern = HistoricalPattern(
            metric_name="weight",
            values=[70.0, 70.2, 70.4, 70.6, 70.8, 71.0, 71.2],
            dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06", "2024-01-07"],
            trend_slope=0.2,  # Increasing weight
            confidence=0.85
        )
        
        self.macro_patterns = {
            "calories": HistoricalPattern(
                metric_name="calories",
                values=[2000, 2100, 2050, 2150, 2200, 2100, 2250],
                dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06", "2024-01-07"],
                trend_slope=25.0,  # Increasing calories
                confidence=0.75
            ),
            "protein": HistoricalPattern(
                metric_name="protein",
                values=[150, 160, 155, 165, 170, 160, 175],
                dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06", "2024-01-07"],
                trend_slope=3.5,  # Increasing protein
                confidence=0.80
            ),
            "carbs": HistoricalPattern(
                metric_name="carbs",
                values=[200, 210, 205, 215, 220, 210, 225],
                dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06", "2024-01-07"],
                trend_slope=3.0,  # Increasing carbs
                confidence=0.70
            ),
            "fat": HistoricalPattern(
                metric_name="fat",
                values=[80, 85, 82, 88, 90, 85, 92],
                dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06", "2024-01-07"],
                trend_slope=1.5,  # Increasing fat
                confidence=0.65
            )
        }
        
        self.performance_pattern = HistoricalPattern(
            metric_name="total_volume",
            values=[5000, 5100, 5050, 5200, 5300, 5250, 5400],
            dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06", "2024-01-07"],
            trend_slope=50.0,  # Increasing performance
            confidence=0.90
        )
    
    def test_recommend_macro_targets_maintenance_goal(self):
        """Test macro recommendations for maintenance goal"""
        # Mock the analytics service methods
        with patch.object(self.prediction_service.analytics_service, 'correlate_nutrition_performance') as mock_correlate, \
             patch.object(self.prediction_service.analytics_service, 'analyze_macro_patterns') as mock_macro_patterns, \
             patch.object(self.prediction_service, '_get_performance_pattern') as mock_perf_pattern:
            
            # Mock correlation data showing positive correlation between protein and performance
            mock_correlate.return_value = {
                "protein_vs_volume": {
                    "correlation": 0.65,
                    "significant": True,
                    "p_value": 0.02
                },
                "calories_vs_volume": {
                    "correlation": 0.45,
                    "significant": True,
                    "p_value": 0.04
                },
                "carbs_vs_volume": {
                    "correlation": 0.35,
                    "significant": False,
                    "p_value": 0.08
                },
                "fat_vs_volume": {
                    "correlation": 0.15,
                    "significant": False,
                    "p_value": 0.15
                }
            }
            
            # Mock current macro patterns
            mock_macro_patterns.return_value = {
                "calories": MagicMock(values=[2100]),
                "protein": MagicMock(values=[160]),
                "carbs": MagicMock(values=[210]),
                "fat": MagicMock(values=[85])
            }
            
            # Mock performance pattern
            mock_perf_pattern.return_value = self.performance_pattern
            
            # Test maintenance goal
            recommendation = self.prediction_service.recommend_macro_targets("test@example.com", "maintenance")
            
            self.assertIsInstance(recommendation, NutritionRecommendation)
            self.assertEqual(recommendation.recommendation_type, "maintenance")
            self.assertGreater(recommendation.confidence_score, 0.0)
            self.assertIn("maintenance", recommendation.rationale)
            
            # Maintenance should keep macros relatively stable
            self.assertAlmostEqual(recommendation.target_calories, 2100, delta=200)
            self.assertAlmostEqual(recommendation.target_protein, 160, delta=20)
    
    def test_recommend_macro_targets_cutting_goal(self):
        """Test macro recommendations for cutting goal"""
        with patch.object(self.prediction_service.analytics_service, 'correlate_nutrition_performance') as mock_correlate, \
             patch.object(self.prediction_service.analytics_service, 'analyze_macro_patterns') as mock_macro_patterns, \
             patch.object(self.prediction_service, '_get_performance_pattern') as mock_perf_pattern:
            
            mock_correlate.return_value = {
                "protein_vs_volume": {"correlation": 0.65, "significant": True, "p_value": 0.02},
                "calories_vs_volume": {"correlation": 0.45, "significant": True, "p_value": 0.04},
                "carbs_vs_volume": {"correlation": 0.35, "significant": False, "p_value": 0.08},
                "fat_vs_volume": {"correlation": 0.15, "significant": False, "p_value": 0.15}
            }
            
            mock_macro_patterns.return_value = {
                "calories": MagicMock(values=[2100]),
                "protein": MagicMock(values=[160]),
                "carbs": MagicMock(values=[210]),
                "fat": MagicMock(values=[85])
            }
            
            mock_perf_pattern.return_value = self.performance_pattern
            
            # Test cutting goal
            recommendation = self.prediction_service.recommend_macro_targets("test@example.com", "cutting")
            
            self.assertIsInstance(recommendation, NutritionRecommendation)
            self.assertEqual(recommendation.recommendation_type, "cutting")
            
            # Cutting should reduce calories and carbs, maintain/increase protein
            self.assertLess(recommendation.target_calories, 2100)  # Should be reduced
            self.assertGreaterEqual(recommendation.target_protein, 160)  # Should maintain or increase
            self.assertLess(recommendation.target_carbs, 210)  # Should be reduced
    
    def test_recommend_macro_targets_bulking_goal(self):
        """Test macro recommendations for bulking goal"""
        with patch.object(self.prediction_service.analytics_service, 'correlate_nutrition_performance') as mock_correlate, \
             patch.object(self.prediction_service.analytics_service, 'analyze_macro_patterns') as mock_macro_patterns, \
             patch.object(self.prediction_service, '_get_performance_pattern') as mock_perf_pattern:
            
            mock_correlate.return_value = {
                "protein_vs_volume": {"correlation": 0.65, "significant": True, "p_value": 0.02},
                "calories_vs_volume": {"correlation": 0.45, "significant": True, "p_value": 0.04},
                "carbs_vs_volume": {"correlation": 0.35, "significant": False, "p_value": 0.08},
                "fat_vs_volume": {"correlation": 0.15, "significant": False, "p_value": 0.15}
            }
            
            mock_macro_patterns.return_value = {
                "calories": MagicMock(values=[2100]),
                "protein": MagicMock(values=[160]),
                "carbs": MagicMock(values=[210]),
                "fat": MagicMock(values=[85])
            }
            
            mock_perf_pattern.return_value = self.performance_pattern
            
            # Test bulking goal
            recommendation = self.prediction_service.recommend_macro_targets("test@example.com", "bulking")
            
            self.assertIsInstance(recommendation, NutritionRecommendation)
            self.assertEqual(recommendation.recommendation_type, "bulking")
            
            # Bulking should increase all macros
            self.assertGreater(recommendation.target_calories, 2100)  # Should be increased
            self.assertGreater(recommendation.target_protein, 160)   # Should be increased
            self.assertGreater(recommendation.target_carbs, 210)     # Should be increased
    
    def test_recommend_macro_targets_insufficient_data(self):
        """Test macro recommendations with insufficient data"""
        with patch.object(self.prediction_service.analytics_service, 'correlate_nutrition_performance') as mock_correlate:
            
            # Mock insufficient data error
            mock_correlate.return_value = {
                "error": "insufficient_data",
                "message": "Need more data for analysis"
            }
            
            recommendation = self.prediction_service.recommend_macro_targets("test@example.com", "maintenance")
            
            self.assertIsNone(recommendation)
    
    def test_generate_intervention_suggestions_declining_performance(self):
        """Test intervention suggestions for declining performance"""
        trend_data = {
            "performance_trend": {
                "trend_direction": "decreasing",
                "rate_of_change": -50.0
            },
            "weight_trend": {
                "trend_direction": "decreasing",
                "rate_of_change": -0.8  # Rapid weight loss
            },
            "macro_patterns": {
                "protein": {
                    "trend_direction": "decreasing",
                    "rate_of_change": -8.0
                },
                "carbs": {
                    "trend_direction": "decreasing",
                    "rate_of_change": -15.0
                }
            }
        }
        
        suggestions = self.prediction_service.generate_intervention_suggestions(trend_data)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Should suggest addressing rapid weight loss
        weight_suggestions = [s for s in suggestions if "weight loss" in s.lower()]
        self.assertGreater(len(weight_suggestions), 0)
        
        # Should suggest addressing declining performance
        performance_suggestions = [s for s in suggestions if "performance" in s.lower()]
        self.assertGreater(len(performance_suggestions), 0)
        
        # Should suggest addressing protein decline
        protein_suggestions = [s for s in suggestions if "protein" in s.lower()]
        self.assertGreater(len(protein_suggestions), 0)
    
    def test_generate_intervention_suggestions_stable_trends(self):
        """Test intervention suggestions for stable trends"""
        trend_data = {
            "performance_trend": {
                "trend_direction": "stable",
                "rate_of_change": 5.0
            },
            "weight_trend": {
                "trend_direction": "stable",
                "rate_of_change": 0.1
            },
            "macro_patterns": {
                "protein": {
                    "trend_direction": "stable",
                    "rate_of_change": 2.0
                },
                "carbs": {
                    "trend_direction": "stable",
                    "rate_of_change": 3.0
                }
            }
        }
        
        suggestions = self.prediction_service.generate_intervention_suggestions(trend_data)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Should suggest maintaining current patterns
        maintenance_suggestions = [s for s in suggestions if "maintain" in s.lower() or "stable" in s.lower()]
        self.assertGreater(len(maintenance_suggestions), 0)
    
    def test_generate_intervention_suggestions_rapid_weight_gain(self):
        """Test intervention suggestions for rapid weight gain"""
        trend_data = {
            "weight_trend": {
                "trend_direction": "increasing",
                "rate_of_change": 0.8  # Rapid weight gain
            }
        }
        
        suggestions = self.prediction_service.generate_intervention_suggestions(trend_data)
        
        self.assertIsInstance(suggestions, list)
        
        # Should suggest monitoring caloric intake
        calorie_suggestions = [s for s in suggestions if "caloric" in s.lower() or "intake" in s.lower()]
        self.assertGreater(len(calorie_suggestions), 0)
    
    def test_calculate_prediction_confidence_with_history(self):
        """Test prediction confidence calculation with historical accuracy"""
        historical_accuracy = {
            "average_accuracy": 0.85,
            "total_predictions": 15,
            "min_accuracy": 0.70,
            "max_accuracy": 0.95
        }
        
        confidence = self.prediction_service.calculate_prediction_confidence(historical_accuracy)
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        
        # With good historical accuracy and sufficient predictions, confidence should be high
        self.assertGreater(confidence, 0.7)
    
    def test_calculate_prediction_confidence_no_history(self):
        """Test prediction confidence calculation with no historical data"""
        historical_accuracy = {
            "average_accuracy": 0,
            "total_predictions": 0,
            "min_accuracy": 0,
            "max_accuracy": 0
        }
        
        confidence = self.prediction_service.calculate_prediction_confidence(historical_accuracy)
        
        # Should return default moderate confidence
        self.assertEqual(confidence, 0.5)
    
    def test_calculate_prediction_confidence_limited_history(self):
        """Test prediction confidence calculation with limited historical data"""
        historical_accuracy = {
            "average_accuracy": 0.90,
            "total_predictions": 3,  # Limited sample size
            "min_accuracy": 0.85,
            "max_accuracy": 0.95
        }
        
        confidence = self.prediction_service.calculate_prediction_confidence(historical_accuracy)
        
        # Should be reduced due to limited sample size
        self.assertLess(confidence, 0.90)  # Less than raw accuracy due to sample size adjustment
        self.assertGreater(confidence, 0.0)
    
    def test_calculate_optimal_macro_targets_with_correlations(self):
        """Test optimal macro target calculation with strong correlations"""
        correlations = {
            "protein_vs_volume": {
                "correlation": 0.75,
                "significant": True
            },
            "calories_vs_volume": {
                "correlation": 0.55,
                "significant": True
            },
            "carbs_vs_volume": {
                "correlation": 0.25,
                "significant": False
            },
            "fat_vs_volume": {
                "correlation": -0.15,
                "significant": False
            }
        }
        
        current_macros = {
            "calories": MagicMock(values=[2000]),
            "protein": MagicMock(values=[150]),
            "carbs": MagicMock(values=[200]),
            "fat": MagicMock(values=[80])
        }
        
        # Mock declining performance to trigger correlation-based adjustments
        performance_pattern = HistoricalPattern(
            metric_name="total_volume",
            values=[5000, 4950, 4900, 4850, 4800],
            dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            trend_slope=-50.0,  # Declining performance
            confidence=0.85
        )
        
        optimal_macros = self.prediction_service._calculate_optimal_macro_targets(
            correlations, current_macros, "maintenance", performance_pattern
        )
        
        self.assertIn("calories", optimal_macros)
        self.assertIn("protein", optimal_macros)
        self.assertIn("carbs", optimal_macros)
        self.assertIn("fat", optimal_macros)
        
        # With declining performance and positive protein correlation, protein should increase
        self.assertGreater(optimal_macros["protein"], 150)
        
        # With positive calorie correlation, calories should increase
        self.assertGreater(optimal_macros["calories"], 2000)
    
    def test_generate_macro_recommendation_rationale(self):
        """Test macro recommendation rationale generation"""
        correlations = {
            "protein_vs_volume": {
                "correlation": 0.65,
                "significant": True
            },
            "calories_vs_volume": {
                "correlation": -0.45,
                "significant": True
            }
        }
        
        current_macros = {
            "calories": MagicMock(values=[2000]),
            "protein": MagicMock(values=[150])
        }
        
        optimal_macros = {
            "calories": 1800,  # 10% decrease
            "protein": 165,    # 10% increase
            "carbs": 200,
            "fat": 80
        }
        
        rationale = self.prediction_service._generate_macro_recommendation_rationale(
            correlations, current_macros, optimal_macros, "cutting"
        )
        
        self.assertIsInstance(rationale, str)
        self.assertIn("cutting", rationale.lower())
        self.assertIn("protein correlates positively", rationale.lower())
        self.assertIn("calories correlates negatively", rationale.lower())
        self.assertIn("increase", rationale.lower())  # Should mention protein increase
        self.assertIn("decrease", rationale.lower())  # Should mention calorie decrease
    
    def test_calculate_macro_recommendation_confidence(self):
        """Test macro recommendation confidence calculation"""
        # High confidence scenario: many significant correlations, good data
        correlations = {
            "protein_vs_volume": {"correlation": 0.75, "significant": True},
            "calories_vs_volume": {"correlation": 0.65, "significant": True},
            "carbs_vs_volume": {"correlation": 0.45, "significant": True},
            "fat_vs_volume": {"correlation": 0.35, "significant": False}
        }
        
        current_macros = {
            "calories": MagicMock(data_points=20),
            "protein": MagicMock(data_points=20),
            "carbs": MagicMock(data_points=20),
            "fat": MagicMock(data_points=20)
        }
        
        confidence = self.prediction_service._calculate_macro_recommendation_confidence(
            correlations, current_macros
        )
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.3)  # Minimum confidence
        self.assertLessEqual(confidence, 1.0)
        
        # With many significant correlations and good data, confidence should be high
        self.assertGreater(confidence, 0.7)
    
    def test_calculate_macro_recommendation_confidence_low_data(self):
        """Test macro recommendation confidence with limited data"""
        correlations = {
            "protein_vs_volume": {"correlation": 0.25, "significant": False},
            "calories_vs_volume": {"correlation": 0.15, "significant": False}
        }
        
        current_macros = {
            "calories": MagicMock(data_points=5),  # Limited data
            "protein": MagicMock(data_points=5)
        }
        
        confidence = self.prediction_service._calculate_macro_recommendation_confidence(
            correlations, current_macros
        )
        
        # Should have lower confidence due to limited data and weak correlations
        self.assertLessEqual(confidence, 0.5)
        self.assertGreaterEqual(confidence, 0.3)  # But not below minimum


class TestPredictionServiceIntegration(unittest.TestCase):
    """Integration tests for prediction service with full workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.prediction_service = PredictionService()
    
    @patch('app.predictions.get_db_connection')
    def test_predict_workout_performance_full_workflow(self, mock_get_db):
        """Test complete workout performance prediction workflow"""
        # Mock database connection
        mock_context = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_context.__enter__ = MagicMock(return_value=mock_conn)
        mock_context.__exit__ = MagicMock(return_value=None)
        mock_get_db.return_value = mock_context
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock sufficient data validation
        mock_cursor.fetchone.side_effect = [
            {"weight_days": 25},      # Weight data
            {"nutrition_days": 25},   # Nutrition data  
            {"workout_days": 25}      # Workout data
        ]
        
        # Mock the analytics service methods
        with patch.object(self.prediction_service.analytics_service, '_get_weight_data') as mock_weight, \
             patch.object(self.prediction_service.analytics_service, '_get_macro_data') as mock_macro, \
             patch.object(self.prediction_service.analytics_service, '_get_performance_data') as mock_perf:
            
            # Mock weight data
            mock_weight.return_value = [
                DataPoint("2024-01-01", 70.0),
                DataPoint("2024-01-07", 70.5),
                DataPoint("2024-01-14", 71.0)
            ]
            
            # Mock macro data
            mock_macro.return_value = [
                MacroData("2024-01-01", 2000, 150, 200, 80),
                MacroData("2024-01-07", 2100, 160, 210, 85),
                MacroData("2024-01-14", 2200, 170, 220, 90)
            ]
            
            # Mock performance data
            mock_perf.return_value = [
                {"date": "2024-01-01", "total_volume": 5000, "estimated_1rm": 100},
                {"date": "2024-01-07", "total_volume": 5200, "estimated_1rm": 105},
                {"date": "2024-01-14", "total_volume": 5400, "estimated_1rm": 110}
            ]
            
            # Test prediction
            prediction = self.prediction_service.predict_workout_performance("test@example.com", "bench_press", 7)
            
            self.assertIsInstance(prediction, PerformancePrediction)
            self.assertEqual(prediction.workout_type, "bench_press")
            self.assertIn("total_volume", prediction.predicted_performance)
            self.assertIn("estimated_1rm", prediction.predicted_performance)
            self.assertIn("lower", prediction.confidence_interval)
            self.assertIn("upper", prediction.confidence_interval)
            self.assertGreater(len(prediction.factors_considered), 0)
            self.assertGreater(prediction.confidence_score, 0.0)
            self.assertLessEqual(prediction.confidence_score, 1.0)
    
    @patch('app.predictions.get_db_connection')
    def test_predict_workout_performance_insufficient_data(self, mock_get_db):
        """Test workout performance prediction with insufficient data"""
        # Mock database connection
        mock_context = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_context.__enter__ = MagicMock(return_value=mock_conn)
        mock_context.__exit__ = MagicMock(return_value=None)
        mock_get_db.return_value = mock_context
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock insufficient data
        mock_cursor.fetchone.side_effect = [
            {"weight_days": 10},      # Insufficient weight data
            {"nutrition_days": 15},   # Sufficient nutrition data  
            {"workout_days": 12}      # Insufficient workout data
        ]
        
        prediction = self.prediction_service.predict_workout_performance("test@example.com", "bench_press", 7)
        
        # Should return None due to insufficient data
        self.assertIsNone(prediction)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)