import firebase_admin
from firebase_admin import credentials, storage
from fastapi import UploadFile, HTTPException, status
import uuid
from ..config import settings

class FirebaseService:
    def __init__(self):
        # Initialize Firebase with your service account
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'storageBucket': settings.FIREBASE_STORAGE_BUCKET
            })
        self.bucket = storage.bucket()

    async def upload_file(self, file: UploadFile, user_id: int = None) -> str:
        try:
            # Create a unique filename
            extension = file.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{extension}"
            
            # Add user_id to path if provided
            path = f"documents/{filename}"
            if user_id:
                path = f"users/{user_id}/documents/{filename}"
            
            # Create a new blob and upload the file's contents
            blob = self.bucket.blob(path)
            
            # Read the file content
            content = await file.read()
            
            # Upload to Firebase
            blob.upload_from_string(
                content,
                content_type=file.content_type
            )
            
            # Make the blob publicly accessible
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading to Firebase: {str(e)}"
            ) 