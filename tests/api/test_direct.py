#!/usr/bin/env python3

print("Testing direct execution of predictions.py content...")

# Copy the content of predictions.py but with absolute imports
from typing import List
from dataclasses import dataclass

print("Basic imports done...")

from app.db import AnalyticsDB

print("DB imports done...")

print("Models imports done...")

from app.analytics import AnalyticsService

print("Analytics imports done...")


@dataclass
class HistoricalPattern:
    """Represents a historical pattern for prediction"""

    metric_name: str
    values: List[float]
    dates: List[str]
    trend_slope: float
    confidence: float


print("HistoricalPattern defined...")


class PredictionService:
    """Service for generating performance predictions and recommendations"""

    def __init__(self):
        self.analytics_service = AnalyticsService()
        self.analytics_db = AnalyticsDB()

    def test_method(self):
        return "PredictionService is working"


print("PredictionService defined...")

# Test the class
service = PredictionService()
print("PredictionService instantiated successfully!")
print(service.test_method())
