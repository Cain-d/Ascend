#!/usr/bin/env python3
"""
Database initialization script for Ascend
Creates the database and runs all migrations
"""

import sys
from pathlib import Path


def ensure_data_directory():
    """Ensure the data directory exists"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir


def main():
    """Initialize the database"""
    print("🚀 Initializing Ascend database...")

    # Ensure data directory exists
    data_dir = ensure_data_directory()
    print(f"✅ Data directory: {data_dir.absolute()}")

    # Set database path
    db_path = data_dir / "ascend.db"

    # Run migrations
    print("📄 Running database migrations...")

    try:
        from run_migrations import run_all_migrations

        success = run_all_migrations(str(db_path))

        if success:
            print("✅ Database initialized successfully!")
            print(f"📍 Database location: {db_path.absolute()}")
            print("\n🎯 Next steps:")
            print("1. Copy .env.example to .env and configure your settings")
            print("2. Start the API server: uvicorn app.main:app --reload")
            print("3. Visit http://127.0.0.1:8000/docs for API documentation")
        else:
            print("❌ Database initialization failed!")
            sys.exit(1)

    except ImportError as e:
        print(f"❌ Error importing migration runner: {e}")
        print(
            "Make sure you're in the correct directory and dependencies are installed"
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
