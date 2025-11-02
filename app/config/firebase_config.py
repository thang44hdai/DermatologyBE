"""
Firebase Storage Configuration
"""
import os
import firebase_admin
from firebase_admin import credentials, storage
from pathlib import Path
from .settings import settings

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        print("✅ Firebase already initialized")
    except ValueError:
        # Check if Firebase is configured
        if not settings.FIREBASE_SERVICE_ACCOUNT_KEY or not settings.FIREBASE_STORAGE_BUCKET:
            print("⚠️  Firebase Storage not configured. Using local storage.")
            print("   Set FIREBASE_SERVICE_ACCOUNT_KEY and FIREBASE_STORAGE_BUCKET in .env")
            return False
        
        # Path to service account key JSON file
        service_account_path = settings.FIREBASE_SERVICE_ACCOUNT_KEY
        
        if not os.path.exists(service_account_path):
            print(f"⚠️  Firebase service account key not found at: {service_account_path}")
            print("   Download it from Firebase Console and place it in the project root.")
            print("   Using local storage instead.")
            return False
        
        try:
            # Initialize Firebase
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': settings.FIREBASE_STORAGE_BUCKET
            })
            
            print("✅ Firebase initialized successfully!")
            print(f"📦 Storage Bucket: {settings.FIREBASE_STORAGE_BUCKET}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Firebase: {e}")
            print("   Using local storage instead.")
            return False


def get_storage_bucket():
    """Get Firebase Storage bucket"""
    try:
        bucket = storage.bucket()
        
        # Test if bucket exists by checking if we can access it
        try:
            # This will fail if bucket doesn't exist or no permission
            bucket.exists()
        except Exception as bucket_error:
            print(f"❌ Firebase Storage bucket error: {bucket_error}")
            print(f"   Bucket: {settings.FIREBASE_STORAGE_BUCKET}")
            print("   Please ensure:")
            print("   1. Storage is enabled in Firebase Console")
            print("   2. Bucket exists and name is correct")
            print("   3. Service account has Storage Admin permissions")
            return None
            
        return bucket
        
    except Exception as e:
        print(f"❌ Failed to get Firebase storage bucket: {e}")
        return None
