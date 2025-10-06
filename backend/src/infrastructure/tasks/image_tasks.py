"""
Image Generation Tasks

Celery tasks for async image generation processing.
"""
import asyncio
import traceback
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from .celery_app import celery_app
from ..ai.dalle_service import DALLEService, DALLEError
from ..database.models.image_models import GeneratedImage, ImageGenerationTask
from ...shared.config import get_settings

# Create async session for database operations
settings = get_settings()
async_engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)


@celery_app.task(bind=True, name='image_generation.generate_image')
def generate_image_task(self, image_id: int, prompt: str, **kwargs):
    """
    Celery task for DALL-E image generation using async processing
    
    Args:
        image_id: Generated image record ID
        prompt: Text prompt for image generation
        **kwargs: Additional generation parameters (size, quality, style)
    """
    task_id = self.request.id
    
    # Use hybrid approach: simple generation + database update
    return asyncio.run(_async_generate_image_hybrid(self, task_id, image_id, prompt, **kwargs))


async def _async_generate_image_simple(task_id: str, image_id: int, prompt: str, **kwargs):
    """Simplified async function for image generation - no database operations"""
    try:
        # Initialize DALL-E service
        dalle_service = DALLEService()
        
        # Extract generation parameters
        size = kwargs.get('size', '1024x1024')
        quality = kwargs.get('quality', 'standard')
        style = kwargs.get('style', 'vivid')
        
        # Generate image (async call) - use a default user_id since we don't have session access
        generation_result = await dalle_service.generate_image(
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            user_id=1  # Use default user_id to avoid session issues
        )
        
        # Return successful result
        return {
            'task_id': task_id,
            'status': 'completed',
            'image_id': image_id,
            'image_base64': generation_result.get("image_base64"),
            'revised_prompt': generation_result.get("revised_prompt"),
            'cost_credits': generation_result.get("cost_credits"),
            'processing_time_ms': generation_result.get("processing_time_ms")
        }
        
    except Exception as e:
        # Return error result
        return {
            'task_id': task_id,
            'status': 'failed',
            'image_id': image_id,
            'error': f"DALL-E generation failed: {str(e)}"
        }


async def _async_generate_image_hybrid(task_instance, task_id: str, image_id: int, prompt: str, **kwargs):
    """Hybrid approach: generate image and return result, but also update database"""
    try:
        # First, generate the image (simple approach)
        dalle_service = DALLEService()
        
        # Extract generation parameters
        size = kwargs.get('size', '1024x1024')
        quality = kwargs.get('quality', 'standard')
        style = kwargs.get('style', 'vivid')
        
        # Generate image (async call)
        generation_result = await dalle_service.generate_image(
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            user_id=1  # Use default user_id to avoid session issues
        )
        
        # Try to update database asynchronously (best effort)
        try:
            db_session = AsyncSessionLocal()
            
            # Update image record with results
            result = await db_session.execute(select(GeneratedImage).where(GeneratedImage.id == image_id))
            image = result.scalar_one_or_none()
            if image:
                image.image_base64 = generation_result.get("image_base64")  # type: ignore
                image.image_url = generation_result.get("image_url")  # type: ignore
                image.revised_prompt = generation_result.get("revised_prompt")  # type: ignore
                image.processing_time_ms = generation_result.get("processing_time_ms")  # type: ignore
                image.cost_credits = generation_result.get("cost_credits")  # type: ignore
                image.generation_status = "completed"  # type: ignore
                await db_session.commit()
            await db_session.close()
        except Exception as db_error:
            print(f"Database update failed (non-critical): {db_error}")
        
        # Return successful result with full image data
        return {
            'task_id': task_id,
            'status': 'completed',
            'image_id': image_id,
            'image_base64': generation_result.get("image_base64"),
            'revised_prompt': generation_result.get("revised_prompt"),
            'cost_credits': generation_result.get("cost_credits"),
            'processing_time_ms': generation_result.get("processing_time_ms"),
            'size': size,
            'quality': quality,
            'style': style
        }
        
    except Exception as e:
        # Return error result
        return {
            'task_id': task_id,
            'status': 'failed',
            'image_id': image_id,
            'error': f"DALL-E generation failed: {str(e)}"
        }


async def _async_generate_image(task_instance, task_id: str, image_id: int, prompt: str, **kwargs):
    """Async function to handle image generation with proper database operations"""
    db_session = None
    try:
        # Create a fresh session for this task
        db_session = AsyncSessionLocal()
        
        # Get image record using async query
        result = await db_session.execute(select(GeneratedImage).where(GeneratedImage.id == image_id))
        image = result.scalar_one_or_none()
        if not image:
            raise Exception(f"Image record not found: {image_id}")
        
        # Update task record
        task_result = await db_session.execute(
            select(ImageGenerationTask).where(ImageGenerationTask.task_id == task_id)
        )
        task_record = task_result.scalar_one_or_none()
        
        if task_record:
            task_record.status = "processing"  # type: ignore
            task_record.started_at = datetime.utcnow()  # type: ignore  
            task_record.progress = 10.0  # type: ignore
            await db_session.commit()
        
        # Progress: Connecting to DALL-E API (removed update_state for now)
        
        # Initialize DALL-E service
        dalle_service = DALLEService()
        
        # Extract generation parameters
        size = kwargs.get('size', '1024x1024')
        quality = kwargs.get('quality', 'standard')
        style = kwargs.get('style', 'vivid')
        
        # Progress: Generating image (removed update_state for now)
        
        # Generate image (async call)
        generation_result = await dalle_service.generate_image(
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            user_id=int(image.user_id)  # type: ignore
        )
        
        # Progress: Saving image to database (removed update_state for now)
        
        # Update image record with results
        image.image_base64 = generation_result.get("image_base64")  # type: ignore
        image.image_url = generation_result.get("image_url")  # type: ignore
        image.revised_prompt = generation_result.get("revised_prompt")  # type: ignore
        image.processing_time_ms = generation_result.get("processing_time_ms")  # type: ignore
        image.cost_credits = generation_result.get("cost_credits")  # type: ignore
        image.generation_status = "completed"  # type: ignore
        
        # Update task record
        if task_record:
            task_record.status = "completed"  # type: ignore
            task_record.progress = 100.0  # type: ignore
            task_record.completed_at = datetime.utcnow()  # type: ignore
            if hasattr(task_record, 'result_data'):
                task_record.result_data = {  # type: ignore
                    "image_id": image_id,
                    "revised_prompt": generation_result.get("revised_prompt"),
                    "cost_credits": generation_result.get("cost_credits")
                }
        
        await db_session.commit()
        
        # Progress: Image generation completed (removed update_state for now)
        
        return {
            'task_id': task_id,
            'status': 'completed',
            'image_id': image_id,
            'image_base64': generation_result.get("image_base64"),
            'revised_prompt': generation_result.get("revised_prompt"),
            'cost_credits': generation_result.get("cost_credits"),
            'processing_time_ms': generation_result.get("processing_time_ms")
        }
        
    except DALLEError as e:
        error_message = f"DALL-E API error: {str(e)}"
        return await _handle_async_task_failure(task_instance, db_session, image_id, task_id, error_message)
    except Exception as e:
        error_message = f"Task execution error: {str(e)}"
        return await _handle_async_task_failure(task_instance, db_session, image_id, task_id, error_message)
    finally:
        if db_session:
            await db_session.close()


async def _handle_async_task_failure(task_instance, db_session, image_id, task_id, error_message):
    """Handle task failure and update database records asynchronously"""
    try:
        # Update image record
        result = await db_session.execute(select(GeneratedImage).where(GeneratedImage.id == image_id))
        image = result.scalar_one_or_none()
        if image:
            image.generation_status = "failed"  # type: ignore
            image.error_message = error_message  # type: ignore
        
        # Update task record
        task_result = await db_session.execute(
            select(ImageGenerationTask).where(ImageGenerationTask.task_id == task_id)
        )
        task_record = task_result.scalar_one_or_none()
        if task_record:
            task_record.status = "failed"  # type: ignore
            task_record.progress = 100.0  # type: ignore
            task_record.completed_at = datetime.utcnow()  # type: ignore
            task_record.error_message = error_message  # type: ignore
        
        await db_session.commit()
        
        # Task failed (removed update_state for now)
        
        return {
            'task_id': task_id,
            'status': 'failed',
            'error': error_message
        }
        
    except Exception as cleanup_error:
        print(f"Error during cleanup: {cleanup_error}")
        return {
            'task_id': task_id,
            'status': 'failed', 
            'error': f"{error_message} (cleanup failed: {cleanup_error})"
        }


@celery_app.task(name='image_generation.cleanup_old_tasks')
def cleanup_old_tasks():
    """Clean up old completed/failed image generation tasks"""
    return asyncio.run(_async_cleanup_old_tasks())


async def _async_cleanup_old_tasks():
    """Async function to clean up old tasks"""
    try:
        # Create a new session for cleanup
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        settings = get_settings()
        engine = create_async_engine(settings.database_url)
        AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
        
        async with AsyncSessionLocal() as db_session:
            try:
                # Delete tasks older than 7 days
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                
                result = await db_session.execute(
                    select(ImageGenerationTask).where(
                        ImageGenerationTask.created_at < cutoff_date,
                        ImageGenerationTask.status.in_(['completed', 'failed'])
                    )
                )
                old_tasks = result.scalars().all()
                
                count = len(old_tasks)
                for task in old_tasks:
                    await db_session.delete(task)
                
                await db_session.commit()
                return f"Cleaned up {count} old tasks"
                
            except Exception as cleanup_error:
                await db_session.rollback()
                return f"Cleanup failed: {str(cleanup_error)}"
                
    except Exception as e:
        return f"Cleanup initialization failed: {str(e)}"