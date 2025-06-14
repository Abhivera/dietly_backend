from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ImageBase(BaseModel):
    original_filename: str

class ImageCreate(ImageBase):
    filename: str
    file_path: str
    file_size: int
    content_type: str

class ImageUpdate(BaseModel):
    description: Optional[str] = None
    tags: Optional[str] = None

class ImageInDB(ImageBase):
    id: int
    filename: str
    file_path: str
    file_size: int
    content_type: str
    description: Optional[str] = None
    tags: Optional[str] = None
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ImageResponse(ImageInDB):
    pass

class ImageAnalysisResponse(BaseModel):
    description: str
    tags: List[str]
    confidence: float