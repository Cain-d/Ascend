"""
Database utilities for Ascend application.
- Connection management (SQLite)
- Analytics-specific database operations (cache & accuracy logs)
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# ---- Configuration -----------------------------------------------------------

# CI-friendly default; override with env var in prod/tests:
#   ENV=ci DATABASE_PATH="data/test.db"
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/ascend.db")

# Ensure parent folder exists (no-op if already present)
_parent = os.path.dirname(DATABASE_PATH) or "."
os.makedirs(_parent, exist_ok=True)


# ---- Connection helpers ------------------------------------------------------

def _connect() -> sqlite3.Connection:
    """
    Create a SQLite connection with sane defaults for web apps and tests.
    """
    conn = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False,  # allow use across FastAPI/TestClient threads
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    conn.row_factory = sqlite3.Row

    # Helpful pragmas: FK enforcement, WAL for fewer write locks, balanced sync.
    # (Safe defaults; adjust if you have different durability needs.)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


@contextmanager
def get_db_connection() -> Any:
    """
    Context-managed DB connection.
    Usage:
        with get_db_connection() as conn:
            conn.execute(...)
            conn.commit()
    """
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


# ---- Utility ----------------------------------------------------------------

def _utc_now_iso() -> str:
    """UTC timestamp in ISO-8601 (no microseconds)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ---- Analytics operations ----------------------------------------------------

class AnalyticsDB:
    """Database operations for analytics functionality."""

    # ---------------- Cache ----------------

    @staticmethod
    def cache_analysis_result(
        user_email: str,
        analysis_type: str,
        time_period: int,
        result_data: Dict[str, Any],
        confidence_level: float,
        cache_hours: int = 24,
    ) -> bool:
        """
        Cache analysis results for performance optimization.
        Returns True on success, False on error.
        """
        try:
            expires_at = (datetime.now(timezone.utc) + timedelta(hours=cache_hours)) \
                .replace(microsecond=0).isoformat()

            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO analytics_cache
                        (user_email, analysis_type, time_period,
                         result_data, expires_at, confidence_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_email,
                        analysis_type,
                        time_period,
                        json.dumps(result_data, separators=(",", ":")),
                        expires_at,
                        confidence_level,
                    ),
                )
                conn.commit()
            return True
        except Exception:
            return False

    @staticmethod
    def get_cached_analysis(
        user_email: str,
        analysis_type: str,
        time_period: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a valid (non-expired) cached result or None.
        """
        try:
            with get_db_connection() as conn:
                cur = conn.execute(
                    """
                    SELECT result_data, confidence_level, created_at
                    FROM analytics_cache
                    WHERE user_email = ?
                      AND analysis_type = ?
                      AND time_period = ?
                      AND expires_at > CURRENT_TIMESTAMP
                    LIMIT 1
                    """,
                    (user_email, analysis_type, time_period),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "result_data": json.loads(row["result_data"]),
                    "confidence_level": row["confidence_level"],
                    "cached_at": row["created_at"],
                }
        except Exception:
            return None

    @staticmethod
    def clear_expired_cache() -> int:
        """
        Remove expired cache entries.
        Returns count of removed rows (0 on error).
        """
        try:
            with get_db_connection() as conn:
                cur = conn.execute(
                    "DELETE FROM analytics_cache WHERE expires_at <= CURRENT_TIMESTAMP"
                )
                conn.commit()
                return cur.rowcount or 0
        except Exception:
            return 0

    # ---------------- Accuracy logging ----------------

    @staticmethod
    def log_prediction_accuracy(
        user_email: str,
        prediction_type: str,
        predicted_value: float,
        actual_value: float,
        prediction_date: str,
        actual_date: str,
    ) -> bool:
        """
        Log prediction accuracy for model improvement.
        Returns True on success.
        """
        try:
            # Avoid division by zero, normalize absolute error
            denom = max(abs(actual_value), 1.0)
            accuracy_score = max(0.0, 1.0 - abs(predicted_value - actual_value) / denom)

            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO prediction_accuracy
                        (user_email, prediction_type, predicted_value, actual_value,
                         prediction_date, actual_date, accuracy_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_email,
                        prediction_type,
                        float(predicted_value),
                        float(actual_value),
                        prediction_date,
                        actual_date,
                        float(accuracy_score),
                        _utc_now_iso(),
                    ),
                )
                conn.commit()
            return True
        except Exception:
            return False

    @staticmethod
    def get_prediction_accuracy_stats(
        user_email: str,
        prediction_type: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Aggregate accuracy metrics for a user (optionally per type).
        Returns zeros on error / no data.
        """
        try:
            base = """
                SELECT
                    AVG(accuracy_score) AS avg_accuracy,
                    MIN(accuracy_score) AS min_accuracy,
                    MAX(accuracy_score) AS max_accuracy,
                    COUNT(*)            AS total_predictions
                FROM prediction_accuracy
                WHERE user_email = ?
            """
            params: List[Any] = [user_email]

            if prediction_type:
                base += " AND prediction_type = ?"
                params.append(prediction_type)

            with get_db_connection() as conn:
                cur = conn.execute(base, params)
                row = cur.fetchone()

            total = int(row["total_predictions"] or 0) if row else 0
            if total <= 0:
                return {
                    "average_accuracy": 0.0,
                    "min_accuracy": 0.0,
                    "max_accuracy": 0.0,
                    "total_predictions": 0.0,
                }

            return {
                "average_accuracy": float(row["avg_accuracy"] or 0),
                "min_accuracy": float(row["min_accuracy"] or 0),
                "max_accuracy": float(row["max_accuracy"] or 0),
                "total_predictions": float(total),
            }
        except Exception:
            return {
                "average_accuracy": 0.0,
                "min_accuracy": 0.0,
                "max_accuracy": 0.0,
                "total_predictions": 0.0,
            }

    # ---------------- Invalidation / stats ----------------

    @staticmethod
    def invalidate_user_cache(
        user_email: str,
        analysis_types: Optional[List[str]] = None,
    ) -> int:
        """
        Invalidate cached analysis results for a user.
        If analysis_types is None, invalidates all cache entries for the user.
        Returns number of deleted rows (0 on error).
        """
        try:
            with get_db_connection() as conn:
                if analysis_types:
                    placeholders = ",".join("?" for _ in analysis_types)
                    query = f"""
                        DELETE FROM analytics_cache
                        WHERE user_email = ? AND analysis_type IN ({placeholders})
                    """
                    params: List[Any] = [user_email, *analysis_types]
                else:
                    query = "DELETE FROM analytics_cache WHERE user_email = ?"
                    params = [user_email]

                cur = conn.execute(query, params)
                conn.commit()
                return cur.rowcount or 0
        except Exception:
            return 0

    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """
        Return cache stats: totals, expired, active, counts by type, avg confidence.
        On error returns {"error": "..."}.
        """
        try:
            with get_db_connection() as conn:
                # Totals
                total = conn.execute(
                    "SELECT COUNT(*) AS c FROM analytics_cache"
                ).fetchone()["c"]

                expired = conn.execute(
                    "SELECT COUNT(*) AS c FROM analytics_cache WHERE expires_at <= CURRENT_TIMESTAMP"
                ).fetchone()["c"]

                # By type (active only)
                by_type_rows = conn.execute(
                    """
                    SELECT analysis_type, COUNT(*) AS c
                    FROM analytics_cache
                    WHERE expires_at > CURRENT_TIMESTAMP
                    GROUP BY analysis_type
                    """
                ).fetchall()
                by_type = {r["analysis_type"]: r["c"] for r in by_type_rows}

                # Confidence (active only)
                conf_rows = conn.execute(
                    """
                    SELECT analysis_type, AVG(confidence_level) AS avg_c
                    FROM analytics_cache
                    WHERE expires_at > CURRENT_TIMESTAMP
                    GROUP BY analysis_type
                    """
                ).fetchall()
                confidence_by_type = {r["analysis_type"]: float(r["avg_c"]) for r in conf_rows}

                active = int(total or 0) - int(expired or 0)
                denom = max(int(total or 0), 1)
                hit_pct = round(active / denom * 100.0, 2)

                return {
                    "total_entries": int(total or 0),
                    "expired_entries": int(expired or 0),
                    "active_entries": active,
                    "entries_by_type": by_type,
                    "avg_confidence_by_type": confidence_by_type,
                    "cache_hit_potential": hit_pct,
                }
        except Exception as e:
            return {"error": str(e)}
