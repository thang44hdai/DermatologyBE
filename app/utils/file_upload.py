import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config.settings import settings


class FileUploadService:
    """Service for handling file uploads"""
    
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
        Save uploaded image file
        
        Args:
            file: Uploaded file
            upload_dir: Directory to save file
            prefix: Optional prefix for filename
            
        Returns:
            Relative path to saved file
        """
        # Validate file
        FileUploadService.validate_image_file(file)
        
        # Create upload directory if not exists
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{prefix}_{uuid.uuid4().hex}{file_ext}" if prefix else f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        try:
            contents = await file.read()
            
            # Check file size
            if len(contents) > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE / (1024 * 1024)}MB"
                )
            
            with open(file_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
        finally:
            await file.close()
        
        # Return relative path
        return file_path.replace("\\", "/")
    
    @staticmethod
    def delete_image(file_path: Optional[str]) -> bool:
        """
        Delete image file
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted, False if file not found
        """
        if not file_path:
            return False
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        
        return False
    
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
            old_file_path: Path to old file
            upload_dir: Directory to save file
            prefix: Optional prefix for filename
            
        Returns:
            New file path or None if no update
        """
        if not file:
            return None
        
        # Delete old file
        FileUploadService.delete_image(old_file_path)
        
        # Save new file
        return await FileUploadService.save_image(file, upload_dir, prefix)


# Global service instance
file_upload_service = FileUploadService()
