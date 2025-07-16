#!/usr/bin/env python3
"""
Create analytics tables for predictive training performance feature
"""

import sqlite3
from datetime import datetime

DATABASE_PATH = "data/ascend.db"

def create_analytics_tables():
    """Create the analytics_cache and prediction_accuracy tables"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Create analytics_cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                time_period INTEGER NOT NULL,
                result_data TEXT NOT NULL,  -- JSON blob
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                confidence_level REAL DEFAULT 0.0,
                UNIQUE(user_email, analysis_type, time_period)
            )
        """)
        
        # Create prediction_accuracy table
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
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_cache_user_type 
            ON analytics_cache(user_email, analysis_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires 
            ON analytics_cache(expires_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prediction_accuracy_user_type 
            ON prediction_accuracy(user_email, prediction_type)
        """)
        
        conn.commit()
        print("Analytics tables created successfully!")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%analytics%' OR name LIKE '%prediction%'")
        tables = cursor.fetchall()
        print(f"Created tables: {[table[0] for table in tables]}")
        
    except Exception as e:
        print(f"Error creating analytics tables: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_analytics_tables()