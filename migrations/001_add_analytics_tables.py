"""
Migration: Add analytics cache and prediction accuracy tables
Date: 2025-07-16
Description: Adds tables for caching analytics results and tracking prediction accuracy
"""

import sqlite3
import os
from datetime import datetime


def run_migration(db_path="data/ascend.db"):
    """Run the analytics tables migration"""

    # Ensure the data folder exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Analytics cache table for performance optimization
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            analysis_type TEXT NOT NULL,
            time_period INTEGER NOT NULL,
            result_data TEXT NOT NULL,  -- JSON blob
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            confidence_level REAL,
            UNIQUE(user_email, analysis_type, time_period)
        )
        """)

        # Prediction accuracy tracking table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_accuracy (
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

        # Create indexes for better query performance
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_analytics_cache_user_type 
        ON analytics_cache(user_email, analysis_type)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires 
        ON analytics_cache(expires_at)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_prediction_accuracy_user 
        ON prediction_accuracy(user_email, prediction_type)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_prediction_accuracy_dates 
        ON prediction_accuracy(prediction_date, actual_date)
        """)

        conn.commit()
        print(
            f"✅ Analytics tables migration completed successfully at {datetime.now()}"
        )

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
