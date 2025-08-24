#!/usr/bin/env python3
"""
Performance tests for analytics caching and large dataset handling
Tests the performance optimization features implemented in Task 7
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any
import statistics

from app.analytics import AnalyticsService
from app.db import AnalyticsDB, get_db_connection


class PerformanceTestSuite:
    """Test suite for analytics performance with large datasets"""

    def __init__(self):
        self.analytics_service = AnalyticsService()
        self.analytics_db = AnalyticsDB()
        self.test_user_email = "performance_test@example.com"
        self.test_results = []

    def setup_large_dataset(self, days: int = 365, daily_entries: int = 5):
        """Create a large dataset for performance testing"""
        print(f"Setting up large dataset: {days} days, {daily_entries} entries per day")

        # Clear any existing test data
        self.cleanup_test_data()

        # Create test user
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, email, password) VALUES (?, ?, ?)",
                ("performance_test", self.test_user_email, "test_hash"),
            )
            conn.commit()
            cursor.execute(
                "SELECT id FROM users WHERE email = ?", (self.test_user_email,)
            )
            user_row = cursor.fetchone()
            if not user_row:
                raise Exception(f"Failed to create test user: {self.test_user_email}")
            user_id = user_row["id"]

            # Generate weight data
            base_weight = 180.0
            weight_trend = random.uniform(-0.1, 0.1)  # Daily weight change

            for i in range(days):
                date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
                weight = base_weight + (weight_trend * i) + random.uniform(-2, 2)

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO bodyweight_log (user_id, date, weight) 
                    VALUES (?, ?, ?)
                """,
                    (user_id, date, weight),
                )

            # Generate nutrition data
            for i in range(days):
                date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")

                for meal_num in range(daily_entries):
                    timestamp = f"{date} {8 + meal_num * 3}:00:00"

                    cursor.execute(
                        """
                        INSERT INTO meals (user_id, timestamp) VALUES (?, ?)
                    """,
                        (user_id, timestamp),
                    )
                    meal_id = cursor.lastrowid

                    # Add random food items to meal
                    for _ in range(random.randint(1, 4)):
                        # Create or get food
                        food_name = f"TestFood_{random.randint(1, 100)}"
                        calories = random.uniform(50, 500)
                        protein = random.uniform(5, 30)
                        carbs = random.uniform(10, 60)
                        fat = random.uniform(2, 25)

                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO foods (name, calories, protein, carbs, fat)
                            VALUES (?, ?, ?, ?, ?)
                        """,
                            (food_name, calories, protein, carbs, fat),
                        )

                        cursor.execute(
                            "SELECT id FROM foods WHERE name = ?", (food_name,)
                        )
                        food_row = cursor.fetchone()
                        if food_row:
                            food_id = food_row["id"]
                        else:
                            continue  # Skip if food creation failed

                        quantity = random.uniform(0.5, 2.0)
                        cursor.execute(
                            """
                            INSERT INTO meal_items (meal_id, food_id, quantity)
                            VALUES (?, ?, ?)
                        """,
                            (meal_id, food_id, quantity),
                        )

            # Generate workout/performance data
            for i in range(0, days, 2):  # Every other day
                date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")

                # Create workout
                cursor.execute(
                    """
                    INSERT INTO workouts (user_id, date, note) VALUES (?, ?, ?)
                """,
                    (user_id, date, f"Test Workout {i}"),
                )
                workout_id = cursor.lastrowid

                # Add exercise logs
                for exercise_num in range(random.randint(3, 6)):
                    exercise_name = f"Exercise_{exercise_num + 1}"

                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO exercises (name) VALUES (?)
                    """,
                        (exercise_name,),
                    )

                    cursor.execute(
                        "SELECT id FROM exercises WHERE name = ?", (exercise_name,)
                    )
                    exercise_id = cursor.fetchone()["id"]

                    sets = random.randint(3, 5)
                    base_reps = random.randint(8, 15)
                    base_weight = random.uniform(50, 200)

                    # Create individual set entries
                    for set_num in range(1, sets + 1):
                        reps = base_reps + random.randint(
                            -2, 2
                        )  # Slight variation per set
                        weight = base_weight
                        rir = random.randint(0, 3)  # Reps in reserve

                        cursor.execute(
                            """
                            INSERT INTO exercise_logs (workout_id, exercise_id, set_number, reps, weight, rir)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                            (workout_id, exercise_id, set_num, reps, weight, rir),
                        )

                # Add performance metrics
                total_volume = random.uniform(5000, 15000)
                estimated_1rm = random.uniform(150, 300)

                cursor.execute(
                    """
                    INSERT INTO performance_metrics (user_id, date, total_volume, estimated_1rm)
                    VALUES (?, ?, ?, ?)
                """,
                    (user_id, date, total_volume, estimated_1rm),
                )

            conn.commit()

        print("✅ Large dataset created successfully")

    def test_cache_performance(self) -> Dict[str, Any]:
        """Test caching performance with large datasets"""
        print("\n🧪 Testing cache performance...")

        results = {
            "test_name": "cache_performance",
            "cache_hits": [],
            "cache_misses": [],
            "cache_effectiveness": {},
        }

        # Test 1: First call (cache miss)
        start_time = time.time()
        weight_trends_1 = self.analytics_service.calculate_weight_trends(
            self.test_user_email, 90
        )
        first_call_time = time.time() - start_time
        results["cache_misses"].append(first_call_time)

        # Test 2: Second call (cache hit)
        start_time = time.time()
        weight_trends_2 = self.analytics_service.calculate_weight_trends(
            self.test_user_email, 90
        )
        second_call_time = time.time() - start_time
        results["cache_hits"].append(second_call_time)

        # Test 3: Macro patterns (cache miss)
        start_time = time.time()
        macro_trends_1 = self.analytics_service.analyze_macro_patterns(
            self.test_user_email, 90
        )
        macro_first_time = time.time() - start_time
        results["cache_misses"].append(macro_first_time)

        # Test 4: Macro patterns (cache hit)
        start_time = time.time()
        macro_trends_2 = self.analytics_service.analyze_macro_patterns(
            self.test_user_email, 90
        )
        macro_second_time = time.time() - start_time
        results["cache_hits"].append(macro_second_time)

        # Calculate cache effectiveness
        avg_miss_time = statistics.mean(results["cache_misses"])
        avg_hit_time = statistics.mean(results["cache_hits"])
        speedup_factor = (
            avg_miss_time / avg_hit_time if avg_hit_time > 0 else float("inf")
        )

        results["cache_effectiveness"] = {
            "avg_cache_miss_time": round(avg_miss_time, 4),
            "avg_cache_hit_time": round(avg_hit_time, 4),
            "speedup_factor": round(speedup_factor, 2),
            "cache_efficiency_percent": round(
                (1 - avg_hit_time / avg_miss_time) * 100, 2
            ),
        }

        print(f"   Cache miss avg: {avg_miss_time:.4f}s")
        print(f"   Cache hit avg: {avg_hit_time:.4f}s")
        print(f"   Speedup factor: {speedup_factor:.2f}x")
        print(
            f"   Cache efficiency: {results['cache_effectiveness']['cache_efficiency_percent']:.1f}%"
        )

        return results

    def test_large_dataset_performance(self) -> Dict[str, Any]:
        """Test performance with increasingly large datasets"""
        print("\n🧪 Testing large dataset performance...")

        results = {
            "test_name": "large_dataset_performance",
            "dataset_sizes": [],
            "execution_times": {},
            "memory_usage": {},
            "scalability_metrics": {},
        }

        dataset_sizes = [30, 90, 180, 365]

        for days in dataset_sizes:
            print(f"   Testing {days} days of data...")
            results["dataset_sizes"].append(days)

            # Clear cache to ensure fresh calculations
            self.analytics_db.invalidate_user_cache(self.test_user_email)

            # Test weight trends
            start_time = time.time()
            weight_trends = self.analytics_service.calculate_weight_trends(
                self.test_user_email, days
            )
            weight_time = time.time() - start_time

            # Test macro patterns
            start_time = time.time()
            macro_trends = self.analytics_service.analyze_macro_patterns(
                self.test_user_email, days
            )
            macro_time = time.time() - start_time

            # Test correlations
            start_time = time.time()
            correlations = self.analytics_service.correlate_nutrition_performance(
                self.test_user_email, days
            )
            correlation_time = time.time() - start_time

            results["execution_times"][f"{days}_days"] = {
                "weight_trends": round(weight_time, 4),
                "macro_patterns": round(macro_time, 4),
                "correlations": round(correlation_time, 4),
                "total": round(weight_time + macro_time + correlation_time, 4),
            }

            print(f"     Weight trends: {weight_time:.4f}s")
            print(f"     Macro patterns: {macro_time:.4f}s")
            print(f"     Correlations: {correlation_time:.4f}s")

        # Calculate scalability metrics
        if len(dataset_sizes) >= 2:
            small_total = results["execution_times"][f"{dataset_sizes[0]}_days"][
                "total"
            ]
            large_total = results["execution_times"][f"{dataset_sizes[-1]}_days"][
                "total"
            ]
            data_size_ratio = dataset_sizes[-1] / dataset_sizes[0]
            time_ratio = large_total / small_total if small_total > 0 else float("inf")

            results["scalability_metrics"] = {
                "data_size_increase": f"{data_size_ratio:.1f}x",
                "time_increase": f"{time_ratio:.1f}x",
                "scalability_efficiency": round(data_size_ratio / time_ratio, 2)
                if time_ratio > 0
                else 0,
                "linear_scalability_score": round(
                    min(1.0, data_size_ratio / time_ratio), 2
                )
                if time_ratio > 0
                else 0,
            }

        return results

    def test_background_processing(self) -> Dict[str, Any]:
        """Test background processing functionality"""
        print("\n🧪 Testing background processing...")

        results = {
            "test_name": "background_processing",
            "task_submissions": [],
            "task_completions": [],
            "concurrent_tasks": {},
        }

        # Test 1: Submit comprehensive correlation analysis
        try:
            task_id = self.analytics_service.submit_expensive_analysis(
                self.test_user_email, "comprehensive_correlation", days=180
            )
            results["task_submissions"].append(
                {
                    "task_type": "comprehensive_correlation",
                    "task_id": task_id,
                    "status": "submitted",
                }
            )
            print(f"   ✅ Submitted comprehensive correlation task: {task_id}")

            # Wait and check status
            max_wait = 30  # seconds
            wait_time = 0
            while wait_time < max_wait:
                status = self.analytics_service.get_background_task_status(task_id)
                if status["status"] == "completed":
                    results["task_completions"].append(
                        {
                            "task_id": task_id,
                            "completion_time": wait_time,
                            "status": "completed",
                        }
                    )
                    print(f"   ✅ Task completed in {wait_time}s")
                    break
                elif status["status"] == "error":
                    results["task_completions"].append(
                        {
                            "task_id": task_id,
                            "completion_time": wait_time,
                            "status": "error",
                            "error": status.get("error"),
                        }
                    )
                    print(f"   ❌ Task failed: {status.get('error')}")
                    break

                time.sleep(1)
                wait_time += 1

            if wait_time >= max_wait:
                print(f"   ⏱️ Task still running after {max_wait}s")

        except Exception as e:
            print(f"   ❌ Failed to submit background task: {e}")
            results["task_submissions"].append(
                {
                    "task_type": "comprehensive_correlation",
                    "status": "failed",
                    "error": str(e),
                }
            )

        return results

    def test_cache_invalidation(self) -> Dict[str, Any]:
        """Test cache invalidation functionality"""
        print("\n🧪 Testing cache invalidation...")

        results = {
            "test_name": "cache_invalidation",
            "invalidation_tests": [],
            "cache_stats": {},
        }

        # Get initial cache stats
        initial_stats = self.analytics_db.get_cache_stats()
        results["cache_stats"]["initial"] = initial_stats

        # Create some cached data
        self.analytics_service.calculate_weight_trends(self.test_user_email, 30)
        self.analytics_service.analyze_macro_patterns(self.test_user_email, 30)

        # Check cache after population
        populated_stats = self.analytics_db.get_cache_stats()
        results["cache_stats"]["after_population"] = populated_stats

        # Test selective invalidation
        invalidated_count = self.analytics_db.invalidate_user_cache(
            self.test_user_email, ["weight_trends"]
        )
        results["invalidation_tests"].append(
            {
                "type": "selective",
                "target": ["weight_trends"],
                "invalidated_count": invalidated_count,
            }
        )

        # Test full user cache invalidation
        invalidated_count = self.analytics_db.invalidate_user_cache(
            self.test_user_email
        )
        results["invalidation_tests"].append(
            {
                "type": "full_user",
                "target": "all",
                "invalidated_count": invalidated_count,
            }
        )

        # Check final cache stats
        final_stats = self.analytics_db.get_cache_stats()
        results["cache_stats"]["final"] = final_stats

        print("   ✅ Cache invalidation tests completed")
        print(f"   Initial entries: {initial_stats.get('total_entries', 0)}")
        print(f"   After population: {populated_stats.get('total_entries', 0)}")
        print(f"   Final entries: {final_stats.get('total_entries', 0)}")

        return results

    def run_all_tests(self, dataset_days: int = 365) -> Dict[str, Any]:
        """Run all performance tests"""
        print("🚀 Starting Performance Test Suite")
        print("=" * 60)

        # Setup large dataset
        self.setup_large_dataset(days=dataset_days)

        # Run all tests
        all_results = {
            "test_suite": "analytics_performance",
            "dataset_size": f"{dataset_days} days",
            "test_timestamp": datetime.now().isoformat(),
            "results": {},
        }

        try:
            all_results["results"]["cache_performance"] = self.test_cache_performance()
            all_results["results"]["large_dataset_performance"] = (
                self.test_large_dataset_performance()
            )
            all_results["results"]["background_processing"] = (
                self.test_background_processing()
            )
            all_results["results"]["cache_invalidation"] = (
                self.test_cache_invalidation()
            )

            # Generate summary
            all_results["summary"] = self.generate_test_summary(all_results["results"])

        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            all_results["error"] = str(e)
        finally:
            # Cleanup
            self.cleanup_test_data()

        return all_results

    def generate_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of test results"""
        summary = {
            "total_tests": len(results),
            "passed_tests": 0,
            "failed_tests": 0,
            "performance_metrics": {},
            "recommendations": [],
        }

        for test_name, test_result in results.items():
            if "error" not in test_result:
                summary["passed_tests"] += 1
            else:
                summary["failed_tests"] += 1

        # Extract key performance metrics
        if "cache_performance" in results:
            cache_result = results["cache_performance"]
            if "cache_effectiveness" in cache_result:
                summary["performance_metrics"]["cache_speedup"] = cache_result[
                    "cache_effectiveness"
                ]["speedup_factor"]
                summary["performance_metrics"]["cache_efficiency"] = cache_result[
                    "cache_effectiveness"
                ]["cache_efficiency_percent"]

        if "large_dataset_performance" in results:
            dataset_result = results["large_dataset_performance"]
            if "scalability_metrics" in dataset_result:
                summary["performance_metrics"]["scalability_score"] = dataset_result[
                    "scalability_metrics"
                ]["linear_scalability_score"]

        # Generate recommendations
        if summary["performance_metrics"].get("cache_speedup", 0) < 2:
            summary["recommendations"].append(
                "Consider increasing cache duration for better performance"
            )

        if summary["performance_metrics"].get("scalability_score", 1) < 0.5:
            summary["recommendations"].append(
                "Performance degrades significantly with large datasets - consider optimization"
            )

        if summary["failed_tests"] > 0:
            summary["recommendations"].append(
                "Some tests failed - review error logs and fix issues"
            )

        return summary

    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM users WHERE email = ?", (self.test_user_email,)
                )
                user_row = cursor.fetchone()

                if user_row:
                    user_id = user_row["id"]

                    # Delete in correct order to respect foreign keys
                    cursor.execute(
                        "DELETE FROM meal_items WHERE meal_id IN (SELECT id FROM meals WHERE user_id = ?)",
                        (user_id,),
                    )
                    cursor.execute("DELETE FROM meals WHERE user_id = ?", (user_id,))
                    cursor.execute(
                        "DELETE FROM bodyweight_log WHERE user_id = ?", (user_id,)
                    )
                    cursor.execute(
                        "DELETE FROM exercise_logs WHERE workout_id IN (SELECT id FROM workouts WHERE user_id = ?)",
                        (user_id,),
                    )
                    cursor.execute("DELETE FROM workouts WHERE user_id = ?", (user_id,))
                    cursor.execute(
                        "DELETE FROM performance_metrics WHERE user_id = ?", (user_id,)
                    )
                    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

                    # Clean up test foods (they don't have user_id, so clean by name pattern)
                    cursor.execute("DELETE FROM foods WHERE name LIKE 'TestFood_%'")

                    conn.commit()

                # Clear analytics cache for test user
                cursor.execute(
                    "DELETE FROM analytics_cache WHERE user_email = ?",
                    (self.test_user_email,),
                )
                cursor.execute(
                    "DELETE FROM prediction_accuracy WHERE user_email = ?",
                    (self.test_user_email,),
                )
                conn.commit()

        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")


def main():
    """Run the performance test suite"""
    test_suite = PerformanceTestSuite()

    # Run tests with different dataset sizes
    print("Running performance tests with 180 days of data...")
    results = test_suite.run_all_tests(dataset_days=180)

    # Print summary
    print("\n" + "=" * 60)
    print("PERFORMANCE TEST SUMMARY")
    print("=" * 60)

    if "summary" in results:
        summary = results["summary"]
        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")

        if summary["performance_metrics"]:
            print("\nPerformance Metrics:")
            for metric, value in summary["performance_metrics"].items():
                print(f"  {metric}: {value}")

        if summary["recommendations"]:
            print("\nRecommendations:")
            for rec in summary["recommendations"]:
                print(f"  • {rec}")

    if "error" in results:
        print(f"\n❌ Test suite error: {results['error']}")
    else:
        print("\n✅ Performance test suite completed successfully!")

    return results


if __name__ == "__main__":
    main()
