"""
Firebase Storage utility for uploading files
"""
import os
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile
from app.config.firebase_config import get_storage_bucket, initialize_firebase


class FirebaseStorage:
    """Firebase Storage manager for file uploads"""
    
    def __init__(self):
        """Initialize Firebase Storage"""
        self.enabled = initialize_firebase()
        self.bucket = get_storage_bucket() if self.enabled else None
        
        if not self.bucket:
            print("⚠️  Firebase Storage not available. Uploads will use local storage.")
            self.enabled = False
    
    def upload_file(
        self, 
        file: UploadFile, 
        folder: str = "uploads",
        filename: Optional[str] = None
    ) -> str:
        """
        Upload a file to Firebase Storage
        
        Args:
            file: UploadFile object from FastAPI
            folder: Folder path in storage (e.g., 'diseases', 'medicines', 'scans')
            filename: Optional custom filename. If None, generates unique name
            
        Returns:
            Public URL of uploaded file
        """
        if not self.enabled or not self.bucket:
            raise Exception("Firebase Storage is not available. Please check your configuration.")
        
        try:
            # Generate filename if not provided
            if filename is None:
                file_extension = Path(file.filename).suffix
                filename = f"{uuid.uuid4()}{file_extension}"
            
            # Create blob path
            blob_path = f"{folder}/{filename}"
            blob = self.bucket.blob(blob_path)
            
            # Reset file pointer to beginning
            file.file.seek(0)
            
            # Upload file
            blob.upload_from_file(
                file.file, 
                content_type=file.content_type
            )
            
            # Make the blob publicly accessible
            blob.make_public()
            
            # Return public URL
            return blob.public_url
            
        except Exception as e:
            raise Exception(f"Failed to upload file to Firebase: {e}")
    
    def upload_multiple_files(
        self,
        files: List[UploadFile],
        folder: str = "uploads"
    ) -> List[str]:
        """
        Upload multiple files to Firebase Storage
        
        Args:
            files: List of UploadFile objects
            folder: Folder path in storage
            
        Returns:
            List of public URLs
        """
        urls = []
        for file in files:
            url = self.upload_file(file, folder)
            urls.append(url)
        return urls
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete a file from Firebase Storage
        
        Args:
            file_url: Public URL or path of the file
            
        Returns:
            True if deleted successfully
        """
        try:
            # Extract blob path from URL
            # Format: https://storage.googleapis.com/bucket-name/path/to/file.jpg
            if "storage.googleapis.com" in file_url:
                parts = file_url.split(self.bucket.name + "/")
                if len(parts) > 1:
                    blob_path = parts[1]
                else:
                    blob_path = file_url
            else:
                blob_path = file_url
            
            # Delete blob
            blob = self.bucket.blob(blob_path)
            blob.delete()
            
            return True
            
        except Exception as e:
            print(f"Failed to delete file: {e}")
            return False
    
    def delete_multiple_files(self, file_urls: List[str]) -> int:
        """
        Delete multiple files from Firebase Storage
        
        Args:
            file_urls: List of file URLs
            
        Returns:
            Number of files deleted successfully
        """
        deleted_count = 0
        for url in file_urls:
            if self.delete_file(url):
                deleted_count += 1
        return deleted_count
    
    def get_signed_url(self, blob_path: str, expiration_hours: int = 1) -> str:
        """
        Generate a signed URL for private file access
        
        Args:
            blob_path: Path to the blob in storage
            expiration_hours: URL expiration time in hours
            
        Returns:
            Signed URL
        """
        try:
            blob = self.bucket.blob(blob_path)
            url = blob.generate_signed_url(
                expiration=timedelta(hours=expiration_hours),
                method='GET'
            )
            return url
        except Exception as e:
            raise Exception(f"Failed to generate signed URL: {e}")


# Global instance
firebase_storage = FirebaseStorage()
