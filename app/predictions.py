from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.db import AnalyticsDB


class PredictionService:
    def __init__(self):
        pass

    def predict_workout_performance(self, user_email, workout_type="general"):
        return None

    def recommend_macro_targets(self, user_email, goal_type="maintenance"):
        return None

    def generate_intervention_suggestions(self, user_email):
        return []

    def calculate_prediction_confidence(self, user_email, prediction_type):
        return 0.5

    def log_prediction_accuracy(
        self,
        user_email: str,
        prediction_type: str,
        predicted_value: float,
        actual_value: float,
        prediction_date: str,
        actual_date: Optional[str] = None,
    ) -> bool:
        """
        Log prediction accuracy when actual results become available

        Args:
            user_email: User identifier
            prediction_type: Type of prediction (e.g., 'workout_performance', 'weight_change')
            predicted_value: The predicted value
            actual_value: The actual observed value
            prediction_date: When the prediction was made (ISO format)
            actual_date: When the actual value was observed (defaults to now)

        Returns:
            bool: True if logged successfully, False otherwise
        """
        if actual_date is None:
            actual_date = datetime.now().isoformat()

        return AnalyticsDB.log_prediction_accuracy(
            user_email,
            prediction_type,
            predicted_value,
            actual_value,
            prediction_date,
            actual_date,
        )

    def get_prediction_accuracy_stats(
        self, user_email: str, prediction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get prediction accuracy statistics for a user

        Args:
            user_email: User identifier
            prediction_type: Specific prediction type to analyze (optional)

        Returns:
            Dict containing accuracy statistics
        """
        return AnalyticsDB.get_prediction_accuracy_stats(
            user_email, prediction_type if prediction_type is not None else ""
        )

    def get_recent_prediction_accuracy(
        self, user_email: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get recent prediction accuracy records for analysis

        Args:
            user_email: User identifier
            days: Number of days to look back

        Returns:
            List of recent accuracy records
        """
        try:
            from app.db import get_db_connection

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT prediction_type, predicted_value, actual_value, 
                           accuracy_score, prediction_date, actual_date
                    FROM prediction_accuracy 
                    WHERE user_email = ? AND actual_date >= ?
                    ORDER BY actual_date DESC
                """,
                    (user_email, cutoff_date),
                )

                records = []
                for row in cursor.fetchall():
                    records.append(
                        {
                            "prediction_type": row["prediction_type"],
                            "predicted_value": row["predicted_value"],
                            "actual_value": row["actual_value"],
                            "accuracy_score": row["accuracy_score"],
                            "prediction_date": row["prediction_date"],
                            "actual_date": row["actual_date"],
                            "error_magnitude": abs(
                                row["predicted_value"] - row["actual_value"]
                            ),
                        }
                    )

                return records

        except Exception:
            return []

    def calculate_accuracy_trends(
        self, user_email: str, prediction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate accuracy trends over time to assess model improvement

        Args:
            user_email: User identifier
            prediction_type: Specific prediction type to analyze (optional)

        Returns:
            Dict containing trend analysis
        """
        try:
            from app.db import get_db_connection

            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Get accuracy over time
                query = """
                    SELECT 
                        DATE(actual_date) as date,
                        AVG(accuracy_score) as daily_accuracy,
                        COUNT(*) as predictions_count
                    FROM prediction_accuracy 
                    WHERE user_email = ?
                """
                params = [user_email]

                if prediction_type:
                    query += " AND prediction_type = ?"
                    params.append(prediction_type)

                query += """
                    GROUP BY DATE(actual_date)
                    ORDER BY date DESC
                    LIMIT 30
                """

                cursor.execute(query, params)
                daily_accuracy = cursor.fetchall()

                if not daily_accuracy:
                    return {
                        "trend": "insufficient_data",
                        "message": "Not enough prediction accuracy data for trend analysis",
                    }

                # Calculate trend direction
                recent_accuracy = [row["daily_accuracy"] for row in daily_accuracy[:7]]
                older_accuracy = [row["daily_accuracy"] for row in daily_accuracy[7:14]]

                if len(recent_accuracy) >= 3 and len(older_accuracy) >= 3:
                    recent_avg = sum(recent_accuracy) / len(recent_accuracy)
                    older_avg = sum(older_accuracy) / len(older_accuracy)

                    if recent_avg > older_avg + 0.05:
                        trend = "improving"
                    elif recent_avg < older_avg - 0.05:
                        trend = "declining"
                    else:
                        trend = "stable"
                else:
                    trend = "insufficient_data"

                return {
                    "trend": trend,
                    "recent_average_accuracy": sum(recent_accuracy)
                    / len(recent_accuracy)
                    if recent_accuracy
                    else 0,
                    "older_average_accuracy": sum(older_accuracy) / len(older_accuracy)
                    if older_accuracy
                    else 0,
                    "total_predictions": sum(
                        row["predictions_count"] for row in daily_accuracy
                    ),
                    "analysis_period_days": len(daily_accuracy),
                    "daily_data": [
                        {
                            "date": row["date"],
                            "accuracy": row["daily_accuracy"],
                            "predictions": row["predictions_count"],
                        }
                        for row in daily_accuracy
                    ],
                }

        except Exception:
            return {"trend": "error", "message": f"Error calculating trends: {str(e)}"}

    def get_prediction_type_performance(
        self, user_email: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get accuracy performance broken down by prediction type

        Args:
            user_email: User identifier

        Returns:
            Dict with performance stats for each prediction type
        """
        try:
            from app.db import get_db_connection

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        prediction_type,
                        COUNT(*) as total_predictions,
                        AVG(accuracy_score) as avg_accuracy,
                        MIN(accuracy_score) as min_accuracy,
                        MAX(accuracy_score) as max_accuracy,
                        AVG(ABS(predicted_value - actual_value)) as avg_error
                    FROM prediction_accuracy 
                    WHERE user_email = ?
                    GROUP BY prediction_type
                    ORDER BY total_predictions DESC
                """,
                    (user_email,),
                )

                results = {}
                for row in cursor.fetchall():
                    results[row["prediction_type"]] = {
                        "total_predictions": row["total_predictions"],
                        "average_accuracy": row["avg_accuracy"],
                        "min_accuracy": row["min_accuracy"],
                        "max_accuracy": row["max_accuracy"],
                        "average_error": row["avg_error"],
                        "reliability_score": self._calculate_reliability_score(
                            row["total_predictions"], row["avg_accuracy"]
                        ),
                    }

                return results

        except Exception:
            return {}

    def _calculate_reliability_score(
        self, total_predictions: int, avg_accuracy: float
    ) -> float:
        """
        Calculate a reliability score based on prediction count and accuracy

        Args:
            total_predictions: Number of predictions made
            avg_accuracy: Average accuracy score

        Returns:
            Reliability score from 0 to 1
        """
        # Weight accuracy by number of predictions (more predictions = more reliable)
        prediction_weight = min(
            1.0, total_predictions / 20
        )  # Full weight at 20+ predictions
        return round(avg_accuracy * prediction_weight, 3)
