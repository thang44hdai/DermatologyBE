"""
Database Initialization Script
Run this script to create all tables in MySQL database
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import engine, Base
from app.models.database import User, PredictionHistory


def init_database():
    """Initialize database by creating all tables"""
    try:
        print("🔄 Creating database tables...")
        print(f"📍 Database URL: {engine.url}")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        print("\n📋 Created tables:")
        print("  - users")
        print("  - prediction_history")
        
        return True
    except Exception as e:
        print(f"❌ Error creating database tables: {str(e)}")
        return False


def drop_all_tables():
    """Drop all tables (use with caution!)"""
    try:
        response = input("⚠️  Are you sure you want to drop all tables? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled.")
            return False
            
        print("🔄 Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped successfully!")
        return True
    except Exception as e:
        print(f"❌ Error dropping tables: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--drop", 
        action="store_true", 
        help="Drop all tables before creating (CAUTION: this will delete all data!)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🗄️  Dermatology Backend - Database Initialization")
    print("=" * 60)
    print()
    
    if args.drop:
        if drop_all_tables():
            print()
            init_database()
    else:
        init_database()
    
    print()
    print("=" * 60)
