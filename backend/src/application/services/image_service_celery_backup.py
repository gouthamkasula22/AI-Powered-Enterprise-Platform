"""
Image Generation Service

Application service for coordinating image generation workflows.
"""
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from ...infrastructure.database.models.image_models import GeneratedImage, ImageGenerationTask
from ...infrastructure.database.models.chat_models import ChatThread, ChatMessage
from ...infrastructure.ai.dalle_service import DALLEService, DALLEError


class ImageGenerationError(Exception):
    """Custom exception for image generation service errors"""
    pass


class ImageService:
    """Service for managing image generation operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.dalle_service = DALLEService()
    
    async def start_generation(
        self,
        user_id: int,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        thread_id: Optional[int] = None,
        message_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Start an async image generation task
        
        Args:
            user_id: ID of the user requesting the image
            prompt: Text description for the image
            size: Image size (1024x1024, 1792x1024, 1024x1792)
            quality: Image quality (standard, hd)
            style: Image style (vivid, natural)
            thread_id: Optional chat thread ID
            message_id: Optional chat message ID
            
        Returns:
            Dictionary with task information
        """
        try:
            # Validate parameters
            await self._validate_generation_request(user_id, prompt, size, quality, style, thread_id)
            
            # Create GeneratedImage record
            generated_image = GeneratedImage(
                user_id=user_id,
                thread_id=thread_id,
                message_id=message_id,
                prompt=prompt,
                model_used="dall-e-3",
                size=size,
                quality=quality,
                style=style,
                generation_status="pending"
            )
            
            self.db_session.add(generated_image)
            await self.db_session.commit()
            await self.db_session.refresh(generated_image)
            
            # Create task ID
            task_id = str(uuid.uuid4())
            
            # Create task tracking record
            task_record = ImageGenerationTask(
                task_id=task_id,
                user_id=user_id,
                generated_image_id=generated_image.id,
                status="pending"
            )
            
            self.db_session.add(task_record)
            await self.db_session.commit()
            
            # Import and start Celery task
            from ...infrastructure.tasks.image_tasks import generate_image_task
            # The task is properly decorated with @celery_app.task, so .delay() should work
            celery_task = generate_image_task.delay(  # type: ignore
                generated_image.id,
                prompt,
                size=size,
                quality=quality,
                style=style
            )
            
            # Update task record with Celery task ID
            task_record.task_id = celery_task.id
            await self.db_session.commit()
            
            return {
                "task_id": celery_task.id,
                "image_id": generated_image.id,
                "status": "pending",
                "estimated_time": "10-30 seconds",
                "progress": 0
            }
            
        except DALLEError as e:
            raise ImageGenerationError(f"AI service error: {str(e)}") from e
        except Exception as e:
            await self.db_session.rollback()
            raise ImageGenerationError(f"Failed to start image generation: {str(e)}") from e
    
    async def get_task_status(self, task_id: str, user_id: int) -> Dict[str, Any]:
        """
        Get the status of an image generation task
        
        Args:
            task_id: Celery task ID
            user_id: User ID for security check
            
        Returns:
            Dictionary with task status and progress
        """
        try:
            # Get task record from database
            query = select(ImageGenerationTask).where(
                and_(
                    ImageGenerationTask.task_id == task_id,
                    ImageGenerationTask.user_id == user_id
                )
            ).options(selectinload(ImageGenerationTask.generated_image))
            
            result = await self.db_session.execute(query)
            task_record = result.scalar_one_or_none()
            
            if not task_record:
                return {"error": "Task not found or access denied"}
            
            # Get Celery task status
            from ...infrastructure.tasks.celery_app import celery_app
            celery_task = celery_app.AsyncResult(task_id)
            
            task_info = {
                "task_id": task_id,
                "status": task_record.status,
                "progress": task_record.progress,
                "created_at": task_record.created_at.isoformat(),
                "image_id": task_record.generated_image_id
            }
            
            # Add Celery-specific information
            if celery_task.state == 'PENDING':
                task_info.update({
                    "current_step": "Task queued...",
                    "progress": 0
                })
            elif celery_task.state == 'PROGRESS':
                meta = celery_task.info
                task_info.update({
                    "current_step": meta.get('current_step', 'Processing...'),
                    "progress": meta.get('progress', task_record.progress)
                })
            elif celery_task.state == 'SUCCESS':
                task_info.update({
                    "status": "completed",
                    "progress": 100,
                    "current_step": "Completed!",
                    "completed_at": task_record.completed_at.isoformat() if task_record.completed_at is not None else None,
                    "result": celery_task.info
                })
            elif celery_task.state == 'FAILURE':
                task_info.update({
                    "status": "failed",
                    "progress": 100,
                    "error": str(celery_task.info),
                    "completed_at": task_record.completed_at.isoformat() if task_record.completed_at is not None else None
                })
            
            # If task is completed, include image data
            if str(task_record.status) == "completed" and task_record.generated_image is not None:
                image = task_record.generated_image
                task_info["image_data"] = {
                    "id": image.id,
                    "prompt": image.prompt,
                    "revised_prompt": image.revised_prompt,
                    "image_base64": image.image_base64,  # Include full base64 data for frontend display
                    "size": image.size,
                    "quality": image.quality,
                    "style": image.style,
                    "processing_time_ms": image.processing_time_ms,
                    "cost_credits": image.cost_credits
                }
            
            return task_info
            
        except Exception as e:
            return {"error": f"Failed to get task status: {str(e)}"}
    
    async def get_image_by_id(self, image_id: int, user_id: int) -> Optional[GeneratedImage]:
        """
        Get a generated image by ID
        
        Args:
            image_id: ID of the generated image
            user_id: User ID for security check
            
        Returns:
            GeneratedImage object or None if not found
        """
        query = select(GeneratedImage).where(
            and_(
                GeneratedImage.id == image_id,
                GeneratedImage.user_id == user_id
            )
        )
        
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_gallery(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's image gallery with pagination and filtering
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status_filter: Filter by generation status
            search_query: Search in prompts and titles
            
        Returns:
            Dictionary with images and pagination info
        """
        query = select(GeneratedImage).where(
            GeneratedImage.user_id == user_id
        )
        
        # Apply filters
        if status_filter:
            query = query.where(GeneratedImage.generation_status == status_filter)
        
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(
                or_(
                    GeneratedImage.prompt.ilike(search_pattern),
                    GeneratedImage.title.ilike(search_pattern),
                    GeneratedImage.revised_prompt.ilike(search_pattern)
                )
            )
        
        # Order by creation date (newest first)
        query = query.order_by(desc(GeneratedImage.created_at))
        
        # Count total records
        count_query = select(GeneratedImage.id).where(GeneratedImage.user_id == user_id)
        if status_filter:
            count_query = count_query.where(GeneratedImage.generation_status == status_filter)
        if search_query:
            search_pattern = f"%{search_query}%"
            count_query = count_query.where(
                or_(
                    GeneratedImage.prompt.ilike(search_pattern),
                    GeneratedImage.title.ilike(search_pattern),
                    GeneratedImage.revised_prompt.ilike(search_pattern)
                )
            )
        
        total_count = len((await self.db_session.execute(count_query)).all())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db_session.execute(query)
        images = result.scalars().all()
        
        # Convert to serializable format
        images_data = [
            {
                "id": img.id,
                "prompt": img.prompt,
                "revised_prompt": img.revised_prompt,
                "title": img.title,
                "description": img.description,
                "size": img.size,
                "quality": img.quality,
                "style": img.style,
                "generation_status": img.generation_status,
                "processing_time_ms": img.processing_time_ms,
                "cost_credits": img.cost_credits,
                "is_favorite": img.is_favorite,
                "created_at": img.created_at.isoformat(),
                "thread_id": img.thread_id,
                # Note: image_base64 not included here for performance
                # Use separate endpoint to get full image data
            }
            for img in images
        ]
        
        return {
            "images": images_data,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_more": skip + len(images) < total_count
        }
    
    async def update_image_metadata(
        self,
        image_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_favorite: Optional[bool] = None
    ) -> bool:
        """
        Update image metadata
        
        Args:
            image_id: ID of the image to update
            user_id: User ID for security check
            title: New title for the image
            description: New description for the image
            tags: New tags for the image
            is_favorite: Whether to mark as favorite
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            image = await self.get_image_by_id(image_id, user_id)
            if not image:
                return False
            
            # Update provided fields
            if title is not None:
                image.title = title  # type: ignore
            if description is not None:
                image.description = description  # type: ignore
            if tags is not None:
                image.tags = tags  # type: ignore
            if is_favorite is not None:
                image.is_favorite = is_favorite  # type: ignore
            
            await self.db_session.commit()
            return True
            
        except Exception:
            await self.db_session.rollback()
            return False
    
    async def delete_image(self, image_id: int, user_id: int) -> bool:
        """
        Delete a generated image
        
        Args:
            image_id: ID of the image to delete
            user_id: User ID for security check
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            image = await self.get_image_by_id(image_id, user_id)
            if not image:
                return False
            
            await self.db_session.delete(image)
            await self.db_session.commit()
            return True
            
        except Exception:
            await self.db_session.rollback()
            return False
    
    async def _validate_generation_request(
        self,
        user_id: int,
        prompt: str,
        size: str,
        quality: str,
        style: str,
        thread_id: Optional[int]
    ):
        """Validate image generation request parameters"""
        
        # Validate prompt
        if not prompt or len(prompt.strip()) == 0:
            raise ImageGenerationError("Prompt cannot be empty")
        
        if len(prompt) > 1000:
            raise ImageGenerationError("Prompt must be 1000 characters or less")
        
        # Validate parameters
        valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
        if size not in valid_sizes:
            raise ImageGenerationError(f"Invalid size. Must be one of: {', '.join(valid_sizes)}")
        
        valid_qualities = ["standard", "hd"]
        if quality not in valid_qualities:
            raise ImageGenerationError(f"Invalid quality. Must be one of: {', '.join(valid_qualities)}")
        
        valid_styles = ["vivid", "natural"]
        if style not in valid_styles:
            raise ImageGenerationError(f"Invalid style. Must be one of: {', '.join(valid_styles)}")
        
        # Validate thread exists if provided
        if thread_id:
            query = select(ChatThread).where(
                and_(
                    ChatThread.id == thread_id,
                    ChatThread.user_id == user_id
                )
            )
            result = await self.db_session.execute(query)
            thread = result.scalar_one_or_none()
            
            if not thread:
                raise ImageGenerationError("Invalid thread ID or access denied")
    
    async def get_generation_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's image generation statistics
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Query for statistics
            query = select(GeneratedImage).where(GeneratedImage.user_id == user_id)
            result = await self.db_session.execute(query)
            images = result.scalars().all()
            
            total_images = len(images)
            completed_images = len([img for img in images if str(img.generation_status) == "completed"])
            failed_images = len([img for img in images if str(img.generation_status) == "failed"])
            pending_images = len([img for img in images if str(img.generation_status) == "pending"])
            
            total_cost = sum(float(img.cost_credits) if img.cost_credits is not None else 0 for img in images)  # type: ignore
            avg_processing_time = sum(int(img.processing_time_ms) if img.processing_time_ms is not None else 0 for img in images) / max(completed_images, 1)  # type: ignore
            
            return {
                "total_images": total_images,
                "completed_images": completed_images,
                "failed_images": failed_images,
                "pending_images": pending_images,
                "success_rate": (completed_images / max(total_images, 1)) * 100,
                "total_cost_credits": total_cost,
                "average_processing_time_ms": int(avg_processing_time)
            }
            
        except Exception as e:
            return {"error": f"Failed to get statistics: {str(e)}"}