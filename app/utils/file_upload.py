import os
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from app.config.settings import settings

# Try to import Firebase storage, fallback to local storage if not available
try:
    from app.utils.firebase_storage import firebase_storage
    USE_FIREBASE = True
except ImportError:
    USE_FIREBASE = False
    print("⚠️  Firebase not configured. Using local file storage.")


class FileUploadService:
    """Service for handling file uploads (Firebase or Local)"""
    
    @staticmethod
    def validate_image_file(file: UploadFile) -> None:
        """
        Validate uploaded image file
        
        Args:
            file: Uploaded file
            
        Raises:
            HTTPException: If file is invalid
        """
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded"
            )
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
    
    @staticmethod
    async def save_image(
        file: UploadFile,
        upload_dir: str,
        prefix: str = ""
    ) -> str:
        """
        Save uploaded image file to Firebase or local storage
        
        Args:
            file: Uploaded file
            upload_dir: Directory/folder to save file (e.g., 'diseases', 'medicines')
            prefix: Optional prefix for filename
            
        Returns:
            URL or relative path to saved file
        """
        # Validate file
        FileUploadService.validate_image_file(file)
        
        # Check file size before upload
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE / (1024 * 1024)}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        try:
            if USE_FIREBASE:
                # Upload to Firebase Storage
                file_ext = Path(file.filename).suffix.lower()
                filename = f"{prefix}_{uuid.uuid4().hex}{file_ext}" if prefix else f"{uuid.uuid4().hex}{file_ext}"
                
                # Extract folder name from upload_dir (e.g., 'uploads/diseases' -> 'diseases')
                folder = upload_dir.replace('uploads/', '').replace('uploads\\', '')
                
                url = firebase_storage.upload_file(file, folder=folder, filename=filename)
                return url
            else:
                # Fallback to local storage
                Path(upload_dir).mkdir(parents=True, exist_ok=True)
                
                file_ext = Path(file.filename).suffix.lower()
                unique_filename = f"{prefix}_{uuid.uuid4().hex}{file_ext}" if prefix else f"{uuid.uuid4().hex}{file_ext}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                with open(file_path, "wb") as f:
                    f.write(contents)
                
                return file_path.replace("\\", "/")
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
        finally:
            await file.close()
    
    @staticmethod
    async def save_multiple_images(
        files: List[UploadFile],
        upload_dir: str,
        prefix: str = ""
    ) -> List[str]:
        """
        Save multiple uploaded image files
        
        Args:
            files: List of uploaded files
            upload_dir: Directory/folder to save files
            prefix: Optional prefix for filenames
            
        Returns:
            List of URLs or relative paths to saved files
        """
        urls = []
        for file in files:
            url = await FileUploadService.save_image(file, upload_dir, prefix)
            urls.append(url)
        return urls
    
    @staticmethod
    def delete_image(file_path: Optional[str]) -> bool:
        """
        Delete image file from Firebase or local storage
        
        Args:
            file_path: URL or path to file to delete
            
        Returns:
            True if deleted, False if file not found
        """
        if not file_path:
            return False
        
        try:
            if USE_FIREBASE and (file_path.startswith('http://') or file_path.startswith('https://')):
                # Delete from Firebase
                return firebase_storage.delete_file(file_path)
            else:
                # Delete from local storage
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            pass
        
        return False
    
    @staticmethod
    def delete_multiple_images(file_paths: List[str]) -> int:
        """
        Delete multiple image files
        
        Args:
            file_paths: List of URLs or paths to files
            
        Returns:
            Number of files deleted successfully
        """
        deleted_count = 0
        for file_path in file_paths:
            if FileUploadService.delete_image(file_path):
                deleted_count += 1
        return deleted_count
    
    @staticmethod
    async def update_image(
        file: Optional[UploadFile],
        old_file_path: Optional[str],
        upload_dir: str,
        prefix: str = ""
    ) -> Optional[str]:
        """
        Update image - delete old and save new
        
        Args:
            file: New uploaded file (None if no update)
            old_file_path: URL or path to old file
            upload_dir: Directory to save file
            prefix: Optional prefix for filename
            
        Returns:
            New file URL/path or None if no update
        """
        if not file:
            return None
        
        # Delete old file
        FileUploadService.delete_image(old_file_path)
        
        # Save new file
        return await FileUploadService.save_image(file, upload_dir, prefix)


# Global service instance
file_upload_service = FileUploadService()
