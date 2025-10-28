"""
Script to create an admin user for the Dermatology application
"""
import sys
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.database import User, UserRole
from app.core.security import get_password_hash


def create_admin_user(
    username: str,
    email: str,
    password: str,
    fullname: str = "Administrator"
):
    """
    Create an admin user in the database
    
    Args:
        username: Admin username
        email: Admin email
        password: Admin password (will be hashed)
        fullname: Admin full name (optional)
    """
    db: Session = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"❌ Error: User with username '{username}' or email '{email}' already exists!")
            return False
        
        # Create new admin user
        hashed_password = get_password_hash(password)
        
        admin_user = User(
            username=username,
            email=email,
            password=hashed_password,
            fullname=fullname,
            role=UserRole.ADMIN,  # Set role to ADMIN
            gender=None,
            avatar_url=None,
            date_of_birth=None
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   User ID: {admin_user.id}")
        print(f"   Username: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Full Name: {admin_user.fullname}")
        print(f"   Role: {admin_user.role.value}")
        print("\n🔑 You can now login with these credentials")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {str(e)}")
        return False
        
    finally:
        db.close()


def update_existing_user_to_admin(username: str):
    """
    Update an existing user's role to ADMIN
    
    Args:
        username: Username of the user to promote to admin
    """
    db: Session = SessionLocal()
    
    try:
        # Find user
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            print(f"❌ Error: User '{username}' not found!")
            return False
        
        # Update role to ADMIN
        user.role = UserRole.ADMIN
        db.commit()
        db.refresh(user)
        
        print("✅ User promoted to admin successfully!")
        print(f"   User ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role.value}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating user: {str(e)}")
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🔐 Admin User Management")
    print("=" * 60)
    print()
    print("Choose an option:")
    print("1. Create new admin user")
    print("2. Promote existing user to admin")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n📝 Enter new admin user details:")
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        fullname = input("Full Name (press Enter for 'Administrator'): ").strip()
        
        if not fullname:
            fullname = "Administrator"
        
        if not username or not email or not password:
            print("❌ Error: Username, email, and password are required!")
            sys.exit(1)
        
        create_admin_user(username, email, password, fullname)
        
    elif choice == "2":
        print("\n📝 Enter username to promote:")
        username = input("Username: ").strip()
        
        if not username:
            print("❌ Error: Username is required!")
            sys.exit(1)
        
        update_existing_user_to_admin(username)
        
    else:
        print("❌ Invalid choice!")
        sys.exit(1)
