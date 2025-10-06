"""
DALL-E 3 Service Integration

Provides image generation capabilities using OpenAI's DALL-E 3 API.
"""
import openai
import asyncio
import base64
import httpx
import time
from typing import Optional, Dict, Any, List
from ...shared.config import get_settings


class DALLEError(Exception):
    """Custom exception for DALL-E related errors"""
    pass


class DALLEService:
    """Service for DALL-E 3 image generation with enhanced error handling and monitoring"""
    
    def __init__(self):
        self.settings = get_settings()
        if not self.settings.openai_api_key:
            raise DALLEError("OpenAI API key not configured")
            
        self.client = openai.AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            timeout=60.0  # 60 second timeout for image generation
        )
        
        # Cost tracking (credits per request)
        self.cost_map = {
            ("dall-e-3", "1024x1024", "standard"): 0.040,
            ("dall-e-3", "1024x1024", "hd"): 0.080,
            ("dall-e-3", "1792x1024", "standard"): 0.080,
            ("dall-e-3", "1792x1024", "hd"): 0.120,
            ("dall-e-3", "1024x1792", "standard"): 0.080,
            ("dall-e-3", "1024x1792", "hd"): 0.120,
        }
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate image using DALL-E 3
        
        Args:
            prompt: Text description of the image to generate
            size: Image size (1024x1024, 1792x1024, 1024x1792)
            quality: Image quality (standard, hd)
            style: Image style (vivid, natural)
            user_id: User ID for tracking/logging
            
        Returns:
            Dictionary containing image data and metadata
            
        Raises:
            DALLEError: If image generation fails
        """
        start_time = time.time()
        
        try:
            # Validate parameters
            self._validate_parameters(prompt, size, quality, style)
            
            # Generate image through OpenAI API
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,  # type: ignore
                quality=quality,  # type: ignore
                style=style,  # type: ignore
                n=1,  # DALL-E 3 only supports n=1
                response_format="url"
            )
            
            if not response.data:
                raise DALLEError("No image data received from DALL-E API")
            
            image_data = response.data[0]
            image_url = image_data.url
            revised_prompt = image_data.revised_prompt
            
            if not image_url:
                raise DALLEError("No image URL received from DALL-E API")
            
            # Download image and convert to base64
            image_base64 = await self._download_and_encode_image(image_url)
            
            processing_time = int((time.time() - start_time) * 1000)  # milliseconds
            cost = self._calculate_cost("dall-e-3", size, quality)
            
            return {
                "image_base64": image_base64,
                "image_url": image_url,
                "revised_prompt": revised_prompt,
                "original_prompt": prompt,
                "model_used": "dall-e-3",
                "size": size,
                "quality": quality,
                "style": style,
                "processing_time_ms": processing_time,
                "cost_credits": cost,
                "success": True
            }
            
        except openai.APIError as e:
            # Handle OpenAI API specific errors
            error_msg = f"OpenAI API error: {e.message}"
            if e.code:
                error_msg += f" (Code: {e.code})"
            raise DALLEError(error_msg) from e
            
        except httpx.RequestError as e:
            # Handle network errors during image download
            raise DALLEError(f"Network error downloading image: {str(e)}") from e
            
        except Exception as e:
            # Handle any other unexpected errors
            raise DALLEError(f"Unexpected error during image generation: {str(e)}") from e
    
    async def _download_and_encode_image(self, image_url: str) -> str:
        """Download image from URL and encode as base64"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            
            if len(response.content) == 0:
                raise DALLEError("Downloaded image is empty")
                
            # Encode as base64
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            return image_base64
    
    def _validate_parameters(self, prompt: str, size: str, quality: str, style: str):
        """Validate input parameters"""
        if not prompt or len(prompt.strip()) == 0:
            raise DALLEError("Prompt cannot be empty")
            
        if len(prompt) > 1000:
            raise DALLEError("Prompt must be 1000 characters or less")
            
        valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
        if size not in valid_sizes:
            raise DALLEError(f"Invalid size. Must be one of: {', '.join(valid_sizes)}")
            
        valid_qualities = ["standard", "hd"]
        if quality not in valid_qualities:
            raise DALLEError(f"Invalid quality. Must be one of: {', '.join(valid_qualities)}")
            
        valid_styles = ["vivid", "natural"]
        if style not in valid_styles:
            raise DALLEError(f"Invalid style. Must be one of: {', '.join(valid_styles)}")
    
    def _calculate_cost(self, model: str, size: str, quality: str) -> float:
        """Calculate the cost in credits for the generation request"""
        key = (model, size, quality)
        return self.cost_map.get(key, 0.040)  # Default to standard 1024x1024 cost
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the DALL-E model capabilities"""
        return {
            "model": "dall-e-3",
            "supported_sizes": ["1024x1024", "1792x1024", "1024x1792"],
            "supported_qualities": ["standard", "hd"],
            "supported_styles": ["vivid", "natural"],
            "max_prompt_length": 1000,
            "typical_generation_time": "10-30 seconds",
            "cost_per_image": self.cost_map
        }
    
    async def validate_api_key(self) -> bool:
        """Validate that the OpenAI API key is working"""
        try:
            # Make a simple API call to test the key
            models = await self.client.models.list()
            return True
        except Exception:
            return False