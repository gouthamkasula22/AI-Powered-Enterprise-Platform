"""
Image Generation API Routes - FastAPI BackgroundTasks

FastAPI router for image generation endpoints using BackgroundTasks.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Annotated
import base64
import uuid

from ...application.services.image_service import (
    ImageService, 
    ImageGenerationError, 
    generate_image_background,
    task_results
)
from ...infrastructure.database.database import get_db_session
from .dependencies.auth import get_current_active_user
from ...application.dto import UserDTO
from ...infrastructure.database.models.image_models import GeneratedImage
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/api/images", tags=["Image Generation"])


# Pydantic models for request/response
class ImageGenerationRequest(BaseModel):
    """Request model for image generation"""
    prompt: str = Field(..., min_length=1, max_length=1000, description="Text description for the image")
    size: str = Field("1024x1024", description="Image size")
    quality: str = Field("standard", description="Image quality")
    style: str = Field("vivid", description="Image style")
    thread_id: Optional[int] = Field(None, description="Chat thread ID (optional)")
    message_id: Optional[int] = Field(None, description="Chat message ID (optional)")
    
    @validator('size')
    def validate_size(cls, v):
        if v not in ["1024x1024", "1792x1024", "1024x1792"]:
            raise ValueError('Invalid size. Must be one of: 1024x1024, 1792x1024, 1024x1792')
        return v
    
    @validator('quality')
    def validate_quality(cls, v):
        if v not in ["standard", "hd"]:
            raise ValueError('Invalid quality. Must be one of: standard, hd')
        return v
    
    @validator('style')
    def validate_style(cls, v):
        if v not in ["vivid", "natural"]:
            raise ValueError('Invalid style. Must be one of: vivid, natural')
        return v


class ImageGenerationResponse(BaseModel):
    """Response model for image generation start"""
    task_id: str
    image_id: int
    status: str
    estimated_time: str
    progress: int


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    task_id: str
    status: str
    progress: float
    current_step: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    image_id: Optional[int] = None
    image_data: Optional[dict] = None


class ImageMetadataUpdate(BaseModel):
    """Request model for updating image metadata"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, description="Image tags")
    is_favorite: Optional[bool] = None


class GalleryResponse(BaseModel):
    """Response model for image gallery"""
    images: List[dict]
    total: int
    skip: int
    limit: int
    has_more: bool


# Dependencies
async def get_image_service(db_session: AsyncSession = Depends(get_db_session)) -> ImageService:
    """Get image service instance"""
    return ImageService(db_session)

async def get_current_user_id(current_user: UserDTO = Depends(get_current_active_user)) -> int:
    """Extract user ID from current user"""
    return current_user.id


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    image_service: ImageService = Depends(get_image_service),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Start image generation task using FastAPI BackgroundTasks
    
    Generate an image using DALL-E 3 based on the provided text prompt.
    The generation runs asynchronously - use the returned task_id to check progress.
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create initial image record in database
        image_record = await image_service.create_image_record(
            user_id=user_id,
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            style=request.style,
            thread_id=request.thread_id,
            message_id=request.message_id
        )
        
        # Initialize task status in memory
        task_results[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "current_step": "Task queued...",
            "image_id": image_record.id,
            "created_at": image_record.created_at.isoformat()
        }
        
        # Add background task for image generation
        background_tasks.add_task(
            generate_image_background,
            task_id=task_id,
            image_id=int(image_record.id),  # type: ignore[arg-type]
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            style=request.style,
            user_id=user_id,
            db_session=db_session
        )
        
        return ImageGenerationResponse(
            task_id=task_id,
            image_id=int(image_record.id),  # type: ignore[arg-type]
            status="pending",
            estimated_time="10-30 seconds",
            progress=0
        )
        
    except ImageGenerationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/tasks/{task_id}/status")
async def get_generation_status(
    task_id: str,
    user_id: int = Depends(get_current_user_id),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Get image generation task status and progress using in-memory storage
    
    Check the status of an ongoing or completed image generation task.
    Returns progress updates and final results when completed.
    """
    try:
        # Get status from in-memory storage
        status_info = image_service.get_task_status(task_id)
        
        if "error" in status_info and status_info["error"] == "Task not found":
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/gallery")
async def get_user_gallery(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    thread_id: Optional[int] = Query(None, description="Filter by thread ID"),
    user_id: int = Depends(get_current_user_id),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Get user's image gallery with pagination
    
    Retrieve a paginated list of the user's completed generated images.
    """
    try:
        gallery_data = await image_service.get_user_gallery(
            user_id=user_id,
            page=page,
            limit=limit,
            thread_id=thread_id
        )
        
        return gallery_data
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gallery: {str(e)}"
        )


@router.get("/{image_id}")
async def get_image_data(
    image_id: int,
    include_base64: bool = Query(False, description="Include base64 image data in response"),
    user_id: int = Depends(get_current_user_id),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Get detailed information about a specific generated image
    
    Retrieve full details about a generated image, optionally including
    the base64-encoded image data.
    """
    try:
        image_data = await image_service.get_image_by_id(image_id, user_id)
        
        if not image_data:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Image not found or access denied"
            )
        
        # Remove base64 if not requested
        if not include_base64 and "image_base64" in image_data:
            del image_data["image_base64"]
        
        return image_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get image data: {str(e)}"
        )


@router.get("/{image_id}/download")
async def download_image(
    image_id: int,
    user_id: int = Depends(get_current_user_id),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Download image as binary file
    
    Download the generated image as a PNG file. Increments the download counter.
    """
    try:
        image_data = await image_service.get_image_by_id(image_id, user_id)
        
        if not image_data:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Image not found or access denied"
            )
        
        if not image_data.get("image_base64"):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Image data not available"
            )
        
        # Decode base64 to binary
        try:
            image_binary = base64.b64decode(image_data["image_base64"])
        except Exception:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid image data"
            )
        
        # Generate filename
        title_str = str(image_data.get("title", ""))
        prompt_str = str(image_data.get("prompt", ""))
        text_for_filename = title_str or prompt_str
        safe_prompt = "".join(c for c in text_for_filename[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"generated_image_{image_data['id']}_{safe_prompt}.png"
        
        return Response(
            content=image_binary,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\""
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download image: {str(e)}"
        )


@router.patch("/{image_id}")
async def update_image_metadata(
    image_id: int,
    update_data: ImageMetadataUpdate,
    user_id: int = Depends(get_current_user_id),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Update image metadata
    
    Update the title, description, tags, or favorite status of a generated image.
    """
    try:
        success = await image_service.update_image_metadata(
            image_id=image_id,
            user_id=user_id,
            title=update_data.title,
            description=update_data.description,
            tags=update_data.tags,
            is_favorite=update_data.is_favorite
        )
        
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Image not found or access denied"
            )
        
        return {"message": "Image metadata updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update image metadata: {str(e)}"
        )


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    user_id: int = Depends(get_current_user_id),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Delete a generated image
    
    Permanently delete a generated image and all its associated data.
    """
    try:
        success = await image_service.delete_image(image_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Image not found or access denied"
            )
        
        return {"message": "Image deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image: {str(e)}"
        )


@router.get("/statistics/user")
async def get_user_statistics(
    user_id: int = Depends(get_current_user_id),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Get user's image generation statistics
    
    Retrieve statistics about the user's image generation activity,
    including total images, success rate, and cost information.
    """
    try:
        stats = await image_service.get_generation_statistics(user_id)
        
        if "error" in stats:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=stats["error"]
            )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/model/info")
async def get_model_info():
    """
    Get information about the DALL-E model capabilities
    
    Retrieve technical details about the image generation model,
    including supported parameters and cost information.
    """
    try:
        from ...infrastructure.ai.dalle_service import DALLEService
        dalle_service = DALLEService()
        model_info = await dalle_service.get_model_info()
        
        return model_info
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )
