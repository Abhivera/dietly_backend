from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Vlog(Base):
    __tablename__ = "vlogs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="vlogs")

class VlogComment(Base):
    __tablename__ = "vlog_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vlog_id = Column(UUID(as_uuid=True), ForeignKey("vlogs.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment = Column(String, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("vlog_comments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    vlog = relationship("Vlog", backref="comments")
    user = relationship("User", backref="vlog_comments")
    parent = relationship("VlogComment", remote_side=[id], backref="replies")

class VlogLike(Base):
    __tablename__ = "vlog_likes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vlog_id = Column(UUID(as_uuid=True), ForeignKey("vlogs.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    vlog = relationship("Vlog", backref="likes")
    user = relationship("User", backref="vlog_likes")