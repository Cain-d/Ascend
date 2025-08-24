"""
Database utilities for Ascend application
Includes connection management and analytics-specific database operations
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

DATABASE_PATH = "../data/ascend.db"

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()

class AnalyticsDB:
    """Database operations for analytics functionality"""
    
    @staticmethod
    def cache_analysis_result(user_email: str, analysis_type: str, time_period: int, 
                            result_data: Dict[str, Any], confidence_level: float, 
                            cache_hours: int = 24) -> bool:
        """Cache analysis results for performance optimization"""
        try:
            expires_at = datetime.now() + timedelta(hours=cache_hours)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO analytics_cache 
                    (user_email, analysis_type, time_period, result_data, expires_at, confidence_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_email, analysis_type, time_period, json.dumps(result_data), 
                     expires_at.isoformat(), confidence_level))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error caching analysis result: {e}")
            return False
    
    @staticmethod
    def get_cached_analysis(user_email: str, analysis_type: str, time_period: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis results if still valid"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT result_data, confidence_level, created_at 
                    FROM analytics_cache 
                    WHERE user_email = ? AND analysis_type = ? AND time_period = ? 
                    AND expires_at > CURRENT_TIMESTAMP
                """, (user_email, analysis_type, time_period))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "result_data": json.loads(row["result_data"]),
                        "confidence_level": row["confidence_level"],
                        "cached_at": row["created_at"]
                    }
                return None
        except Exception as e:
            print(f"Error retrieving cached analysis: {e}")
            return None
    
    @staticmethod
    def clear_expired_cache() -> int:
        """Remove expired cache entries and return count of removed entries"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM analytics_cache WHERE expires_at <= CURRENT_TIMESTAMP")
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Error clearing expired cache: {e}")
            return 0
    
    @staticmethod
    def log_prediction_accuracy(user_email: str, prediction_type: str, 
                              predicted_value: float, actual_value: float,
                              prediction_date: str, actual_date: str) -> bool:
        """Log prediction accuracy for model improvement"""
        try:
            # Calculate accuracy score (1 - normalized absolute error)
            accuracy_score = max(0, 1 - abs(predicted_value - actual_value) / max(abs(actual_value), 1))
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO prediction_accuracy 
                    (user_email, prediction_type, predicted_value, actual_value, 
                     prediction_date, actual_date, accuracy_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_email, prediction_type, predicted_value, actual_value,
                     prediction_date, actual_date, accuracy_score))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error logging prediction accuracy: {e}")
            return False
    
    @staticmethod
    def get_prediction_accuracy_stats(user_email: str, prediction_type: str = None) -> Dict[str, float]:
        """Get prediction accuracy statistics for a user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        AVG(accuracy_score) as avg_accuracy,
                        MIN(accuracy_score) as min_accuracy,
                        MAX(accuracy_score) as max_accuracy,
                        COUNT(*) as total_predictions
                    FROM prediction_accuracy 
                    WHERE user_email = ?
                """
                params = [user_email]
                
                if prediction_type:
                    query += " AND prediction_type = ?"
                    params.append(prediction_type)
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                if row and row["total_predictions"] > 0:
                    return {
                        "average_accuracy": row["avg_accuracy"],
                        "min_accuracy": row["min_accuracy"],
                        "max_accuracy": row["max_accuracy"],
                        "total_predictions": row["total_predictions"]
                    }
                return {"average_accuracy": 0, "min_accuracy": 0, "max_accuracy": 0, "total_predictions": 0}
        except Exception as e:
            print(f"Error getting prediction accuracy stats: {e}")
            return {"average_accuracy": 0, "min_accuracy": 0, "max_accuracy": 0, "total_predictions": 0}
    
    @staticmethod
    def invalidate_user_cache(user_email: str, analysis_types: List[str] = None) -> int:
        """
        Invalidate cached analysis results for a user when new data is added
        
        Args:
            user_email: User identifier
            analysis_types: Specific analysis types to invalidate (None = all)
            
        Returns:
            Number of cache entries invalidated
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if analysis_types:
                    # Invalidate specific analysis types
                    placeholders = ','.join(['?' for _ in analysis_types])
                    query = f"""
                        DELETE FROM analytics_cache 
                        WHERE user_email = ? AND analysis_type IN ({placeholders})
                    """
                    params = [user_email] + analysis_types
                else:
                    # Invalidate all cache for user
                    query = "DELETE FROM analytics_cache WHERE user_email = ?"
                    params = [user_email]
                
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Error invalidating user cache: {e}")
            return 0
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Get analytics cache statistics for monitoring"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Total cache entries
                cursor.execute("SELECT COUNT(*) as total FROM analytics_cache")
                total = cursor.fetchone()["total"]
                
                # Expired entries
                cursor.execute("SELECT COUNT(*) as expired FROM analytics_cache WHERE expires_at <= CURRENT_TIMESTAMP")
                expired = cursor.fetchone()["expired"]
                
                # Cache by analysis type
                cursor.execute("""
                    SELECT analysis_type, COUNT(*) as count 
                    FROM analytics_cache 
                    WHERE expires_at > CURRENT_TIMESTAMP
                    GROUP BY analysis_type
                """)
                by_type = {row["analysis_type"]: row["count"] for row in cursor.fetchall()}
                
                # Average confidence levels
                cursor.execute("""
                    SELECT analysis_type, AVG(confidence_level) as avg_confidence
                    FROM analytics_cache 
                    WHERE expires_at > CURRENT_TIMESTAMP
                    GROUP BY analysis_type
                """)
                confidence_by_type = {row["analysis_type"]: row["avg_confidence"] for row in cursor.fetchall()}
                
                return {
                    "total_entries": total,
                    "expired_entries": expired,
                    "active_entries": total - expired,
                    "entries_by_type": by_type,
                    "avg_confidence_by_type": confidence_by_type,
                    "cache_hit_potential": round((total - expired) / max(total, 1) * 100, 2)
                }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {"error": str(e)}