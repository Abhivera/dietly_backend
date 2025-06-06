import os
from uuid import uuid4
from fastapi import UploadFile
from PIL import Image

class FileUploadHelper:
    @staticmethod
    def save_image(file: UploadFile, upload_dir: str) -> str:
        # Ensure directory exists
        os.makedirs(upload_dir, exist_ok=True)

        # Create a unique filename
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid4().hex}{ext}"
        file_path = os.path.join(upload_dir, unique_filename)

        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        return file_path

    @staticmethod
    def resize_image(file_path: str, max_width: int, max_height: int):
        try:
            with Image.open(file_path) as img:
                img.thumbnail((max_width, max_height))
                img.save(file_path)
        except Exception as e:
            raise RuntimeError(f"Image resizing failed: {str(e)}")
