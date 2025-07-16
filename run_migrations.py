"""
Migration runner for Ascend database
Runs all pending migrations in order
"""

import os
import sys
import importlib.util
from pathlib import Path

def run_all_migrations(db_path="data/ascend.db"):
    """Run all migration files in the migrations directory"""
    
    migrations_dir = Path("migrations")
    
    if not migrations_dir.exists():
        print("❌ Migrations directory not found")
        return False
    
    # Get all migration files and sort them
    migration_files = sorted([f for f in migrations_dir.glob("*.py") if f.name != "__init__.py"])
    
    if not migration_files:
        print("ℹ️  No migration files found")
        return True
    
    print(f"🔄 Running {len(migration_files)} migration(s)...")
    
    for migration_file in migration_files:
        try:
            print(f"📄 Running migration: {migration_file.name}")
            
            # Import and run the migration
            spec = importlib.util.spec_from_file_location("migration", migration_file)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            
            # Run the migration
            migration_module.run_migration(db_path)
            
        except Exception as e:
            print(f"❌ Failed to run migration {migration_file.name}: {e}")
            return False
    
    print("✅ All migrations completed successfully")
    return True

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/ascend.db"
    success = run_all_migrations(db_path)
    sys.exit(0 if success else 1)