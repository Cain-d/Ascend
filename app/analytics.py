"""
Analytics service for predictive training performance analysis
Provides statistical calculations for weight trends, nutrition patterns, and performance correlations
"""

import sqlite3
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import math

from .db import get_db_connection, AnalyticsDB
from .models import TrendAnalysis, TrendInsight


@dataclass
class DataPoint:
    """Represents a single data point with date and value"""
    date: str
    value: float


@dataclass
class MacroData:
    """Represents macro nutrition data for a specific date"""
    date: str
    calories: float
    protein: float
    carbs: float
    fat: float


class AnalyticsService:
    """Core analytics service for trend analysis and statistical calculations"""
    
    def __init__(self):
        self.analytics_db = AnalyticsDB()
    
    def calculate_weight_trends(self, user_email: str, days: int = 30) -> Optional[TrendAnalysis]:
        """
        Analyze weight change patterns over specified time period
        
        Args:
            user_email: User identifier
            days: Number of days to analyze (default 30)
            
        Returns:
            TrendAnalysis object with trend statistics or None if insufficient data
        """
        # Check cache first
        cached_result = self.analytics_db.get_cached_analysis(user_email, "weight_trends", days)
        if cached_result:
            return TrendAnalysis(**cached_result["result_data"])
        
        # Get weight data from database
        weight_data = self._get_weight_data(user_email, days)
        
        if len(weight_data) < 7:  # Minimum 7 data points for meaningful analysis
            return None
        
        # Calculate trend statistics
        values = [point.value for point in weight_data]
        dates = [point.date for point in weight_data]
        
        # Calculate rate of change (slope of linear regression)
        rate_of_change = self._calculate_linear_slope(weight_data)
        
        # Determine trend direction
        trend_direction = self._determine_trend_direction(rate_of_change)
        
        # Calculate confidence level based on data consistency
        confidence_level = self._calculate_trend_confidence(weight_data, rate_of_change)
        
        result = TrendAnalysis(
            metric_name="body_weight",
            time_period=days,
            trend_direction=trend_direction,
            rate_of_change=rate_of_change,
            confidence_level=confidence_level,
            data_points=len(weight_data),
            start_date=dates[0] if dates else "",
            end_date=dates[-1] if dates else ""
        )
        
        # Cache the result
        self.analytics_db.cache_analysis_result(
            user_email, "weight_trends", days, result.dict(), confidence_level
        )
        
        return result
    
    def analyze_macro_patterns(self, user_email: str, days: int = 30) -> Dict[str, TrendAnalysis]:
        """
        Analyze macro nutrition intake patterns over specified time period
        
        Args:
            user_email: User identifier
            days: Number of days to analyze (default 30)
            
        Returns:
            Dictionary with trend analysis for each macro (calories, protein, carbs, fat)
        """
        # Check cache first
        cached_result = self.analytics_db.get_cached_analysis(user_email, "macro_patterns", days)
        if cached_result:
            return {k: TrendAnalysis(**v) for k, v in cached_result["result_data"].items()}
        
        # Get macro data from database
        macro_data = self._get_macro_data(user_email, days)
        
        if len(macro_data) < 7:  # Minimum 7 days for meaningful analysis
            return {}
        
        results = {}
        
        # Analyze each macro nutrient
        for macro_name in ["calories", "protein", "carbs", "fat"]:
            macro_values = [getattr(data, macro_name) for data in macro_data]
            dates = [data.date for data in macro_data]
            
            # Create data points for trend calculation
            data_points = [DataPoint(date, value) for date, value in zip(dates, macro_values)]
            
            # Calculate trend statistics
            rate_of_change = self._calculate_linear_slope(data_points)
            trend_direction = self._determine_trend_direction(rate_of_change)
            confidence_level = self._calculate_trend_confidence(data_points, rate_of_change)
            
            results[macro_name] = TrendAnalysis(
                metric_name=macro_name,
                time_period=days,
                trend_direction=trend_direction,
                rate_of_change=rate_of_change,
                confidence_level=confidence_level,
                data_points=len(data_points),
                start_date=dates[0] if dates else "",
                end_date=dates[-1] if dates else ""
            )
        
        # Cache the results
        cache_data = {k: v.dict() for k, v in results.items()}
        avg_confidence = sum(r.confidence_level for r in results.values()) / len(results) if results else 0
        self.analytics_db.cache_analysis_result(
            user_email, "macro_patterns", days, cache_data, avg_confidence
        )
        
        return results
    
    def correlate_nutrition_performance(self, user_email: str, days: int = 60) -> Dict[str, Any]:
        """
        Calculate correlations between nutrition intake and workout performance with statistical significance
        
        Args:
            user_email: User identifier
            days: Number of days to analyze (default 60)
            
        Returns:
            Dictionary with correlation results including coefficients, p-values, and significance
        """
        # Validate minimum data requirements
        validation_result = self._validate_correlation_data_requirements(user_email, days)
        if not validation_result["valid"]:
            return {
                "error": "insufficient_data",
                "message": validation_result["message"],
                "requirements": validation_result["requirements"]
            }
        
        # Get nutrition and performance data
        macro_data = self._get_macro_data(user_email, days)
        performance_data = self._get_performance_data(user_email, days)
        
        # Align data by date
        aligned_data = self._align_nutrition_performance_data(macro_data, performance_data)
        
        correlations = {}
        
        # Calculate correlations for each macro vs performance metrics
        for macro in ["calories", "protein", "carbs", "fat"]:
            macro_values = [data[macro] for data in aligned_data]
            
            # Correlate with total volume
            volume_values = [data["total_volume"] for data in aligned_data]
            volume_correlation = self._calculate_correlation_with_significance(macro_values, volume_values)
            correlations[f"{macro}_vs_volume"] = volume_correlation
            
            # Correlate with estimated 1RM
            if any(data["estimated_1rm"] for data in aligned_data):
                rm_values = [data["estimated_1rm"] or 0 for data in aligned_data]
                rm_correlation = self._calculate_correlation_with_significance(macro_values, rm_values)
                correlations[f"{macro}_vs_1rm"] = rm_correlation
        
        # Add metadata about the analysis
        correlations["metadata"] = {
            "data_points": len(aligned_data),
            "analysis_period_days": days,
            "macro_data_points": len(macro_data),
            "performance_data_points": len(performance_data),
            "analysis_date": datetime.now().isoformat()
        }
        
        return correlations
    
    def calculate_trend_statistics(self, data_points: List[DataPoint]) -> Dict[str, float]:
        """
        Generate comprehensive statistical summary for a dataset
        
        Args:
            data_points: List of DataPoint objects
            
        Returns:
            Dictionary with statistical measures
        """
        if not data_points:
            return {}
        
        values = [point.value for point in data_points]
        
        stats = {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "coefficient_of_variation": 0
        }
        
        # Calculate coefficient of variation (std_dev / mean)
        if stats["mean"] != 0:
            stats["coefficient_of_variation"] = stats["std_dev"] / abs(stats["mean"])
        
        # Add trend-specific statistics
        stats["slope"] = self._calculate_linear_slope(data_points)
        stats["trend_strength"] = abs(stats["slope"]) / (stats["std_dev"] + 0.001)  # Avoid division by zero
        
        return stats
    
    # Private helper methods
    
    def _get_weight_data(self, user_email: str, days: int) -> List[DataPoint]:
        """Retrieve weight data from database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT bw.date, bw.weight
                    FROM bodyweight_log bw
                    JOIN users u ON bw.user_id = u.id
                    WHERE u.email = ? AND bw.date >= date('now', '-{} days')
                    ORDER BY bw.date
                """.format(days), (user_email,))
                
                rows = cursor.fetchall()
                return [DataPoint(row["date"], row["weight"]) for row in rows]
        except Exception as e:
            print(f"Error retrieving weight data: {e}")
            return []
    
    def _get_macro_data(self, user_email: str, days: int) -> List[MacroData]:
        """Retrieve macro nutrition data from database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        DATE(m.timestamp) as date,
                        SUM(f.calories * mi.quantity) as calories,
                        SUM(f.protein * mi.quantity) as protein,
                        SUM(f.carbs * mi.quantity) as carbs,
                        SUM(f.fat * mi.quantity) as fat
                    FROM meals m
                    JOIN users u ON m.user_id = u.id
                    JOIN meal_items mi ON m.id = mi.meal_id
                    JOIN foods f ON mi.food_id = f.id
                    WHERE u.email = ? AND DATE(m.timestamp) >= date('now', '-{} days')
                    GROUP BY DATE(m.timestamp)
                    ORDER BY DATE(m.timestamp)
                """.format(days), (user_email,))
                
                rows = cursor.fetchall()
                return [MacroData(
                    date=row["date"],
                    calories=row["calories"] or 0,
                    protein=row["protein"] or 0,
                    carbs=row["carbs"] or 0,
                    fat=row["fat"] or 0
                ) for row in rows]
        except Exception as e:
            print(f"Error retrieving macro data: {e}")
            return []
    
    def _get_performance_data(self, user_email: str, days: int) -> List[Dict[str, Any]]:
        """Retrieve workout performance data from database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        pm.date,
                        pm.estimated_1rm,
                        pm.total_volume
                    FROM performance_metrics pm
                    JOIN users u ON pm.user_id = u.id
                    WHERE u.email = ? AND pm.date >= date('now', '-{} days')
                    ORDER BY pm.date
                """.format(days), (user_email,))
                
                rows = cursor.fetchall()
                return [{
                    "date": row["date"],
                    "estimated_1rm": row["estimated_1rm"],
                    "total_volume": row["total_volume"] or 0
                } for row in rows]
        except Exception as e:
            print(f"Error retrieving performance data: {e}")
            return []
    
    def _calculate_linear_slope(self, data_points: List[DataPoint]) -> float:
        """Calculate the slope of linear regression line"""
        if len(data_points) < 2:
            return 0.0
        
        # Convert dates to numeric values (days from first date)
        first_date = datetime.fromisoformat(data_points[0].date)
        x_values = []
        y_values = []
        
        for point in data_points:
            date_obj = datetime.fromisoformat(point.date)
            days_diff = (date_obj - first_date).days
            x_values.append(days_diff)
            y_values.append(point.value)
        
        # Calculate slope using least squares method
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x_squared = sum(x * x for x in x_values)
        
        denominator = n * sum_x_squared - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    def _determine_trend_direction(self, rate_of_change: float, threshold: float = 0.01) -> str:
        """Determine trend direction based on rate of change"""
        if abs(rate_of_change) <= threshold:
            return "stable"
        elif rate_of_change > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _calculate_trend_confidence(self, data_points: List[DataPoint], rate_of_change: float) -> float:
        """Calculate confidence level for trend analysis based on data consistency"""
        if len(data_points) < 3:
            return 0.0
        
        values = [point.value for point in data_points]
        
        # Calculate R-squared for linear fit
        mean_y = statistics.mean(values)
        
        # Predicted values using linear trend
        first_date = datetime.fromisoformat(data_points[0].date)
        predicted_values = []
        
        for point in data_points:
            date_obj = datetime.fromisoformat(point.date)
            days_diff = (date_obj - first_date).days
            predicted_y = values[0] + rate_of_change * days_diff
            predicted_values.append(predicted_y)
        
        # Calculate R-squared
        ss_res = sum((actual - predicted) ** 2 for actual, predicted in zip(values, predicted_values))
        ss_tot = sum((actual - mean_y) ** 2 for actual in values)
        
        if ss_tot == 0:
            # If all values are the same, check if predictions match perfectly
            if ss_res == 0:
                return 1.0  # Perfect fit for constant data
            else:
                return 0.0
        
        r_squared = 1 - (ss_res / ss_tot)
        
        # For perfect linear data, R-squared should be very close to 1
        if r_squared < 0:
            r_squared = 0.0
        
        # Adjust confidence based on number of data points
        data_point_factor = min(1.0, len(data_points) / 14)  # Full confidence at 14+ points
        
        confidence = max(0.0, min(1.0, r_squared * data_point_factor))
        return confidence
    
    def _align_nutrition_performance_data(self, macro_data: List[MacroData], 
                                        performance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Align nutrition and performance data by date"""
        # Create dictionaries for quick lookup
        macro_dict = {data.date: data for data in macro_data}
        perf_dict = {data["date"]: data for data in performance_data}
        
        # Find common dates
        common_dates = set(macro_dict.keys()) & set(perf_dict.keys())
        
        aligned_data = []
        for date in sorted(common_dates):
            macro = macro_dict[date]
            perf = perf_dict[date]
            
            aligned_data.append({
                "date": date,
                "calories": macro.calories,
                "protein": macro.protein,
                "carbs": macro.carbs,
                "fat": macro.fat,
                "estimated_1rm": perf["estimated_1rm"],
                "total_volume": perf["total_volume"]
            })
        
        return aligned_data
    
    def _calculate_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        try:
            # Remove pairs where either value is None or 0 (for meaningful correlation)
            valid_pairs = [(x, y) for x, y in zip(x_values, y_values) if x is not None and y is not None and y != 0]
            
            if len(valid_pairs) < 2:
                return 0.0
            
            x_clean, y_clean = zip(*valid_pairs)
            
            n = len(x_clean)
            sum_x = sum(x_clean)
            sum_y = sum(y_clean)
            sum_xy = sum(x * y for x, y in zip(x_clean, y_clean))
            sum_x_squared = sum(x * x for x in x_clean)
            sum_y_squared = sum(y * y for y in y_clean)
            
            numerator = n * sum_xy - sum_x * sum_y
            denominator = math.sqrt((n * sum_x_squared - sum_x * sum_x) * (n * sum_y_squared - sum_y * sum_y))
            
            if denominator == 0:
                return 0.0
            
            correlation = numerator / denominator
            return max(-1.0, min(1.0, correlation))  # Clamp to [-1, 1]
            
        except Exception as e:
            print(f"Error calculating correlation: {e}")
            return 0.0
    
    def _validate_correlation_data_requirements(self, user_email: str, days: int) -> Dict[str, Any]:
        """
        Validate minimum data requirements for correlation analysis
        
        Args:
            user_email: User identifier
            days: Number of days to analyze
            
        Returns:
            Dictionary with validation result and requirements information
        """
        macro_data = self._get_macro_data(user_email, days)
        performance_data = self._get_performance_data(user_email, days)
        aligned_data = self._align_nutrition_performance_data(macro_data, performance_data)
        
        min_macro_days = 14
        min_performance_days = 14
        min_aligned_points = 10
        
        requirements = {
            "minimum_macro_days": min_macro_days,
            "minimum_performance_days": min_performance_days,
            "minimum_aligned_points": min_aligned_points,
            "current_macro_days": len(macro_data),
            "current_performance_days": len(performance_data),
            "current_aligned_points": len(aligned_data)
        }
        
        # Check each requirement
        if len(macro_data) < min_macro_days:
            return {
                "valid": False,
                "message": f"Need at least {min_macro_days} days of nutrition data for correlation analysis",
                "requirements": requirements
            }
        
        if len(performance_data) < min_performance_days:
            return {
                "valid": False,
                "message": f"Need at least {min_performance_days} days of workout performance data for correlation analysis",
                "requirements": requirements
            }
        
        if len(aligned_data) < min_aligned_points:
            return {
                "valid": False,
                "message": f"Need at least {min_aligned_points} days with both nutrition and performance data for correlation analysis",
                "requirements": requirements
            }
        
        return {
            "valid": True,
            "message": "Sufficient data for correlation analysis",
            "requirements": requirements
        }
    
    def _calculate_correlation_with_significance(self, x_values: List[float], y_values: List[float]) -> Dict[str, Any]:
        """
        Calculate Pearson correlation coefficient with statistical significance testing
        
        Args:
            x_values: First variable values
            y_values: Second variable values
            
        Returns:
            Dictionary with correlation coefficient, p-value, and significance information
        """
        # Calculate basic correlation
        correlation = self._calculate_correlation(x_values, y_values)
        
        # Remove pairs where either value is None or 0 for significance testing
        valid_pairs = [(x, y) for x, y in zip(x_values, y_values) if x is not None and y is not None and y != 0]
        n = len(valid_pairs)
        
        if n < 3:
            return {
                "correlation": 0.0,
                "p_value": 1.0,
                "significant": False,
                "confidence_level": "none",
                "sample_size": n,
                "interpretation": "insufficient_data"
            }
        
        # Calculate t-statistic for significance testing
        if abs(correlation) == 1.0:
            # Perfect correlation
            p_value = 0.0
        else:
            # Calculate t-statistic: t = r * sqrt((n-2)/(1-r^2))
            t_stat = correlation * math.sqrt((n - 2) / (1 - correlation**2)) if correlation**2 != 1 else float('inf')
            
            # Calculate p-value using t-distribution approximation
            # For simplicity, using critical values for common significance levels
            p_value = self._calculate_p_value_from_t(abs(t_stat), n - 2)
        
        # Determine significance levels
        significant_05 = p_value < 0.05
        significant_01 = p_value < 0.01
        significant_001 = p_value < 0.001
        
        if significant_001:
            confidence_level = "very_high"
            significance_symbol = "***"
        elif significant_01:
            confidence_level = "high"
            significance_symbol = "**"
        elif significant_05:
            confidence_level = "moderate"
            significance_symbol = "*"
        else:
            confidence_level = "low"
            significance_symbol = ""
        
        # Interpret correlation strength
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            strength = "strong"
        elif abs_corr >= 0.3:
            strength = "moderate"
        elif abs_corr >= 0.1:
            strength = "weak"
        else:
            strength = "negligible"
        
        direction = "positive" if correlation > 0 else "negative" if correlation < 0 else "none"
        
        interpretation = f"{strength}_{direction}" if correlation != 0 else "no_correlation"
        
        return {
            "correlation": round(correlation, 4),
            "p_value": round(p_value, 4),
            "significant": significant_05,
            "confidence_level": confidence_level,
            "significance_symbol": significance_symbol,
            "sample_size": n,
            "strength": strength,
            "direction": direction,
            "interpretation": interpretation
        }
    
    def _calculate_p_value_from_t(self, t_stat: float, degrees_freedom: int) -> float:
        """
        Calculate approximate p-value from t-statistic using critical values
        
        Args:
            t_stat: Absolute t-statistic value
            degrees_freedom: Degrees of freedom (n-2 for correlation)
            
        Returns:
            Approximate p-value (two-tailed)
        """
        # Critical values for common significance levels (two-tailed)
        # These are approximations for degrees of freedom >= 10
        if degrees_freedom < 3:
            return 1.0
        
        # Use conservative critical values for small samples
        if degrees_freedom <= 10:
            critical_values = {
                0.001: 4.587,  # Very conservative for small samples
                0.01: 3.169,
                0.05: 2.228,
                0.10: 1.812
            }
        else:
            # Standard critical values for larger samples
            critical_values = {
                0.001: 3.291,
                0.01: 2.576,
                0.05: 1.960,
                0.10: 1.645
            }
        
        # Find approximate p-value
        if t_stat >= critical_values[0.001]:
            return 0.001
        elif t_stat >= critical_values[0.01]:
            return 0.01
        elif t_stat >= critical_values[0.05]:
            return 0.05
        elif t_stat >= critical_values[0.10]:
            return 0.10
        else:
            return 0.20  # Not significant at common levels