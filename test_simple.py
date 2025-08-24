#!/usr/bin/env python3

print("Starting import test...")

try:
    print("Importing dataclass...")
    from dataclasses import dataclass
    print("✓ dataclass imported")
    
    print("Importing typing...")
    from typing import Dict, List, Optional, Any
    print("✓ typing imported")
    
    print("Importing datetime...")
    from datetime import datetime, timedelta
    print("✓ datetime imported")
    
    print("Importing statistics...")
    import statistics
    print("✓ statistics imported")
    
    print("Importing math...")
    import math
    print("✓ math imported")
    
    print("Importing app.db...")
    from app.db import get_db_connection, AnalyticsDB
    print("✓ app.db imported")
    
    print("Importing app.models...")
    from app.models import PerformancePrediction, NutritionRecommendation
    print("✓ app.models imported")
    
    print("Importing app.analytics...")
    from app.analytics import AnalyticsService, DataPoint, MacroData
    print("✓ app.analytics imported")
    
    print("Now importing app.predictions...")
    import app.predictions
    print("✓ app.predictions module imported")
    
    print("Module contents:", dir(app.predictions))
    
    print("Trying to import PredictionService...")
    from app.predictions import PredictionService
    print("✓ PredictionService imported successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()