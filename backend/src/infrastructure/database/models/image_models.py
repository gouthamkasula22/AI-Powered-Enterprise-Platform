"""
Image generation models for storing generated images and task tracking.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..config import Base

# Association table for image collections
image_collection_items = Table(
    'image_collection_items',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('collection_id', Integer, ForeignKey('image_gallery_collections.id'), nullable=False),
    Column('image_id', Integer, ForeignKey('generated_images.id'), nullable=False),
    Column('added_at', DateTime, default=func.now(), nullable=False),
    UniqueConstraint('collection_id', 'image_id', name='uq_collection_image')
)

class GeneratedImage(Base):
    """Model for storing generated images with metadata"""
    __tablename__ = "generated_images"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    thread_id = Column(Integer, ForeignKey("chat_threads.id", ondelete="SET NULL"), nullable=True, index=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Image generation data
    prompt = Column(Text, nullable=False)
    revised_prompt = Column(Text, nullable=True)  # DALL-E revised prompt
    image_base64 = Column(Text, nullable=True)  # Base64 encoded image
    image_url = Column(String(500), nullable=True)  # Original DALL-E URL
    
    # Generation parameters
    model_used = Column(String(50), default="dall-e-3")
    size = Column(String(20), default="1024x1024")  # 1024x1024, 1792x1024, 1024x1792
    quality = Column(String(20), default="standard")  # standard, hd
    style = Column(String(20), default="vivid")  # vivid, natural
    
    # Processing metadata
    generation_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    cost_credits = Column(Float, nullable=True)  # Cost tracking
    
    # Organization and metadata
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags for searching
    is_favorite = Column(Boolean, default=False, index=True)
    is_public = Column(Boolean, default=False, index=True)
    download_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("UserModel", back_populates="generated_images")
    thread = relationship("ChatThread", back_populates="generated_images")
    message = relationship("ChatMessage", back_populates="generated_image")
    generation_task = relationship("ImageGenerationTask", back_populates="generated_image", uselist=False)
    collections = relationship("ImageGalleryCollection", secondary="image_collection_items", back_populates="images")

class ImageGenerationTask(Base):
    """Model for tracking async image generation tasks"""
    __tablename__ = "image_generation_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)  # Celery task ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    generated_image_id = Column(Integer, ForeignKey("generated_images.id"), nullable=True, index=True)
    
    # Task status tracking
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)  # 0.0 to 100.0
    current_step = Column(String(100), nullable=True)  # Current processing step
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("UserModel")
    generated_image = relationship("GeneratedImage", back_populates="generation_task")

class ImageGalleryCollection(Base):
    """Model for organizing images into collections/albums"""
    __tablename__ = "image_gallery_collections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("UserModel")
    images = relationship("GeneratedImage", secondary="image_collection_items", back_populates="collections")

