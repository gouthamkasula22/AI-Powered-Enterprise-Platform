"""
Image Generation Service - FastAPI BackgroundTasks Implementation

Application service for coordinating image generation workflows.
"""
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from ...infrastructure.database.models.image_models import GeneratedImage
from ...infrastructure.database.models.chat_models import ChatThread, ChatMessage
from ...infrastructure.ai.dalle_service import DALLEService, DALLEError


class ImageGenerationError(Exception):
    """Custom exception for image generation service errors"""
    pass


# In-memory task results storage
# For production, consider using Redis for persistence across restarts
task_results: Dict[str, Dict[str, Any]] = {}


class ImageService:
    """Service for managing image generation operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.dalle_service = DALLEService()
    
    async def create_image_record(
        self,
        user_id: int,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        thread_id: Optional[int] = None,
        message_id: Optional[int] = None
    ) -> GeneratedImage:
        """
        Create initial image record in database
        
        Args:
            user_id: ID of the user requesting the image
            prompt: Text description for the image
            size: Image size (1024x1024, 1792x1024, 1024x1792)
            quality: Image quality (standard, hd)
            style: Image style (vivid, natural)
            thread_id: Optional chat thread ID
            message_id: Optional chat message ID
            
        Returns:
            Created GeneratedImage record
        """
        try:
            # Validate thread ownership if provided
            if thread_id:
                thread_query = select(ChatThread).where(
                    and_(
                        ChatThread.id == thread_id,
                        ChatThread.user_id == user_id
                    )
                )
                result = await self.db_session.execute(thread_query)
                thread = result.scalar_one_or_none()
                if not thread:
                    raise ImageGenerationError("Thread not found or access denied")
            
            # Create image record
            generated_image = GeneratedImage(
                user_id=user_id,
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                thread_id=thread_id,
                message_id=message_id,
                generation_status="pending"
            )
            
            self.db_session.add(generated_image)
            await self.db_session.commit()
            await self.db_session.refresh(generated_image)
            
            return generated_image
            
        except Exception as e:
            await self.db_session.rollback()
            raise ImageGenerationError(f"Failed to create image record: {str(e)}") from e
    
    async def update_image_result(
        self,
        image_id: int,
        result: Dict[str, Any],
        status: str = "completed"
    ) -> GeneratedImage:
        """
        Update image record with generation results
        
        Args:
            image_id: ID of the image record
            result: Generation result from DALL-E
            status: Status to set (completed, failed)
            
        Returns:
            Updated GeneratedImage record
        """
        try:
            # Get image record
            query = select(GeneratedImage).where(GeneratedImage.id == image_id)
            db_result = await self.db_session.execute(query)
            image = db_result.scalar_one_or_none()
            
            if not image:
                raise ImageGenerationError(f"Image record not found: {image_id}")
            
            # Update with results
            image.generation_status = status  # type: ignore[assignment]
            image.image_base64 = result.get("image_base64")  # type: ignore[assignment]
            image.image_url = result.get("image_url")  # type: ignore[assignment]
            image.revised_prompt = result.get("revised_prompt")  # type: ignore[assignment]
            image.processing_time_ms = result.get("processing_time_ms")  # type: ignore[assignment]
            image.cost_credits = result.get("cost_credits")  # type: ignore[assignment]
            
            if status == "failed":
                image.error_message = result.get("error", "Unknown error")
            
            await self.db_session.commit()
            await self.db_session.refresh(image)
            
            return image
            
        except Exception as e:
            await self.db_session.rollback()
            raise ImageGenerationError(f"Failed to update image result: {str(e)}") from e
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status from in-memory storage
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Task status information
        """
        if task_id not in task_results:
            return {"error": "Task not found"}
        
        return task_results[task_id]
    
    async def get_user_gallery(
        self,
        user_id: int,
        page: int = 1,
        limit: int = 20,
        thread_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get user's image gallery with pagination
        
        Args:
            user_id: User ID
            page: Page number (1-indexed)
            limit: Items per page
            thread_id: Optional thread filter
            
        Returns:
            Dictionary with images and pagination info
        """
        try:
            offset = (page - 1) * limit
            
            # Build query
            query = select(GeneratedImage).where(
                and_(
                    GeneratedImage.user_id == user_id,
                    GeneratedImage.generation_status == "completed"
                )
            )
            
            if thread_id:
                query = query.where(GeneratedImage.thread_id == thread_id)
            
            # Get total count
            count_query = select(GeneratedImage).where(
                and_(
                    GeneratedImage.user_id == user_id,
                    GeneratedImage.generation_status == "completed"
                )
            )
            if thread_id:
                count_query = count_query.where(GeneratedImage.thread_id == thread_id)
            
            count_result = await self.db_session.execute(count_query)
            total = len(count_result.scalars().all())
            
            # Get paginated results
            query = query.order_by(desc(GeneratedImage.created_at)).offset(offset).limit(limit)
            result = await self.db_session.execute(query)
            images = result.scalars().all()
            
            return {
                "images": [
                    {
                        "id": img.id,
                        "prompt": img.prompt,
                        "revised_prompt": img.revised_prompt,
                        "image_url": img.image_url,
                        "image_base64": img.image_base64,
                        "size": img.size,
                        "quality": img.quality,
                        "style": img.style,
                        "cost_credits": img.cost_credits,
                        "processing_time_ms": img.processing_time_ms,
                        "created_at": img.created_at.isoformat(),
                        "thread_id": img.thread_id
                    }
                    for img in images
                ],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
            
        except Exception as e:
            raise ImageGenerationError(f"Failed to get gallery: {str(e)}") from e
    
    async def get_image_by_id(self, image_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get specific image by ID
        
        Args:
            image_id: Image ID
            user_id: User ID for authorization
            
        Returns:
            Image data or None
        """
        try:
            query = select(GeneratedImage).where(
                and_(
                    GeneratedImage.id == image_id,
                    GeneratedImage.user_id == user_id
                )
            )
            
            result = await self.db_session.execute(query)
            image = result.scalar_one_or_none()
            
            if not image:
                return None
            
            return {
                "id": image.id,
                "prompt": image.prompt,
                "revised_prompt": image.revised_prompt,
                "image_url": image.image_url,
                "image_base64": image.image_base64,
                "size": image.size,
                "quality": image.quality,
                "style": image.style,
                "cost_credits": image.cost_credits,
                "processing_time_ms": image.processing_time_ms,
                "generation_status": image.generation_status,
                "error_message": image.error_message,
                "created_at": image.created_at.isoformat(),
                "thread_id": image.thread_id,
                "message_id": image.message_id
            }
            
        except Exception as e:
            raise ImageGenerationError(f"Failed to get image: {str(e)}") from e
    
    async def delete_image(self, image_id: int, user_id: int) -> bool:
        """
        Delete an image
        
        Args:
            image_id: Image ID
            user_id: User ID for authorization
            
        Returns:
            True if deleted, False if not found
        """
        try:
            query = select(GeneratedImage).where(
                and_(
                    GeneratedImage.id == image_id,
                    GeneratedImage.user_id == user_id
                )
            )
            
            result = await self.db_session.execute(query)
            image = result.scalar_one_or_none()
            
            if not image:
                return False
            
            await self.db_session.delete(image)
            await self.db_session.commit()
            
            return True
            
        except Exception as e:
            await self.db_session.rollback()
            raise ImageGenerationError(f"Failed to delete image: {str(e)}") from e
    
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
            image_id: Image ID
            user_id: User ID for authorization
            title: Optional new title
            description: Optional new description
            tags: Optional new tags
            is_favorite: Optional favorite status
            
        Returns:
            True if updated, False if not found
        """
        try:
            query = select(GeneratedImage).where(
                and_(
                    GeneratedImage.id == image_id,
                    GeneratedImage.user_id == user_id
                )
            )
            
            result = await self.db_session.execute(query)
            image = result.scalar_one_or_none()
            
            if not image:
                return False
            
            # Update fields if provided
            if title is not None:
                image.title = title  # type: ignore[assignment]
            if description is not None:
                image.description = description  # type: ignore[assignment]
            if tags is not None:
                image.tags = tags  # type: ignore[assignment]
            if is_favorite is not None:
                image.is_favorite = is_favorite  # type: ignore[assignment]
            
            await self.db_session.commit()
            
            return True
            
        except Exception as e:
            await self.db_session.rollback()
            raise ImageGenerationError(f"Failed to update image metadata: {str(e)}") from e
    
    async def get_generation_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's image generation statistics
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Count by status
            count_query = select(GeneratedImage).where(GeneratedImage.user_id == user_id)
            result = await self.db_session.execute(count_query)
            all_images = result.scalars().all()
            
            total_count = len(all_images)
            completed_count = len([img for img in all_images if img.generation_status == "completed"])  # type: ignore[comparison-overlap]
            failed_count = len([img for img in all_images if img.generation_status == "failed"])  # type: ignore[comparison-overlap]
            
            # Calculate total cost
            total_cost = sum(img.cost_credits if img.cost_credits is not None else 0 for img in all_images)
            
            return {
                "total_images": total_count,
                "completed_images": completed_count,
                "failed_images": failed_count,
                "total_cost_credits": total_cost
            }
            
        except Exception as e:
            raise ImageGenerationError(f"Failed to get statistics: {str(e)}") from e


async def generate_image_background(
    task_id: str,
    image_id: int,
    prompt: str,
    size: str,
    quality: str,
    style: str,
    user_id: int,
    db_session: AsyncSession
):
    """
    Background task to generate image using DALL-E
    
    Args:
        task_id: Unique task ID
        image_id: Database image record ID
        prompt: Image generation prompt
        size: Image size
        quality: Image quality
        style: Image style
        user_id: User ID
        db_session: Database session
    """
    try:
        # Update task status
        task_results[task_id] = {
            "task_id": task_id,
            "status": "processing",
            "progress": 50,
            "current_step": "Generating with DALL-E...",
            "image_id": image_id
        }
        
        # Generate image using DALL-E
        dalle_service = DALLEService()
        result = await dalle_service.generate_image(
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            user_id=user_id
        )
        
        # Update database with result
        image_service = ImageService(db_session)
        await image_service.update_image_result(image_id, result, status="completed")
        
        # Store successful result
        task_results[task_id] = {
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "current_step": "Completed!",
            "image_id": image_id,
            "result": result,
            "image_data": result  # For frontend compatibility
        }
        
    except DALLEError as e:
        error_msg = f"DALL-E API error: {str(e)}"
        
        # Update database with error
        try:
            image_service = ImageService(db_session)
            await image_service.update_image_result(
                image_id,
                {"error": error_msg},
                status="failed"
            )
        except:
            pass
        
        # Store failed result
        task_results[task_id] = {
            "task_id": task_id,
            "status": "failed",
            "progress": 100,
            "current_step": "Failed",
            "image_id": image_id,
            "error": error_msg
        }
        
    except Exception as e:
        error_msg = f"Task execution error: {str(e)}"
        
        # Update database with error
        try:
            image_service = ImageService(db_session)
            await image_service.update_image_result(
                image_id,
                {"error": error_msg},
                status="failed"
            )
        except:
            pass
        
        # Store failed result
        task_results[task_id] = {
            "task_id": task_id,
            "status": "failed",
            "progress": 100,
            "current_step": "Failed",
            "image_id": image_id,
            "error": error_msg
        }
