"""
Database Initialization Script
Run this script to create all tables in MySQL database
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import engine, Base, SessionLocal
from app.models.database import User, UserRole
from app.core.security import get_password_hash


def create_admin_user(db):
    """Create default admin user if not exists"""
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            admin_user = User(
                email="admin@dermatology.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),  # Change this!
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=1
            )
            db.add(admin_user)
            db.commit()
            print("✅ Default admin user created!")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠️  IMPORTANT: Change the admin password after first login!")
        else:
            print("ℹ️  Admin user already exists")
            
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        db.rollback()


def init_database():
    """Initialize database by creating all tables"""
    try:
        print("🔄 Creating database tables...")
        print(f"📍 Database URL: {engine.url}")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        print("\n📋 Created tables:")
        print("  - users (with role column)")
        print("  - prediction_history")
        
        # Create default admin user
        print("\n🔄 Creating default admin user...")
        db = SessionLocal()
        try:
            create_admin_user(db)
        finally:
            db.close()
        
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
