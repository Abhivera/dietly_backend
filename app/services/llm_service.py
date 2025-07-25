import base64
import json
import logging
from typing import List, Dict, Optional
import requests
import asyncio
from pathlib import Path
from io import BytesIO
from PIL import Image
from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        
        # Validate API key
        if not self.api_key:
            raise ValueError("Gemini API key is not configured")
    
    def _get_mime_type(self, image_path: str = None, content_type: str = None, image_content: bytes = None) -> str:
        """Determine MIME type based on file extension, content type, or image content"""
        
        # If content_type is provided (from upload), use it
        if content_type:
            if 'jpeg' in content_type or 'jpg' in content_type:
                return 'image/jpeg'
            elif 'png' in content_type:
                return 'image/png'
            elif 'gif' in content_type:
                return 'image/gif'
            elif 'webp' in content_type:
                return 'image/webp'
        
        # If image_path is provided, use file extension
        if image_path:
            extension = Path(image_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            return mime_types.get(extension, 'image/jpeg')
        
        # Try to detect from image content using PIL
        if image_content:
            try:
                image = Image.open(BytesIO(image_content))
                format_lower = image.format.lower()
                if format_lower == 'jpeg':
                    return 'image/jpeg'
                elif format_lower == 'png':
                    return 'image/png'
                elif format_lower == 'gif':
                    return 'image/gif'
                elif format_lower == 'webp':
                    return 'image/webp'
            except Exception as e:
                logger.warning(f"Could not detect image format from content: {str(e)}")
        
        # Default fallback
        return 'image/jpeg'
    
    def _encode_image_from_path(self, image_path: str) -> tuple[str, str]:
        """Encode image from file path to base64 and return with MIME type"""
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            with open(image_path, "rb") as image_file:
                image_content = image_file.read()
                base64_image = base64.b64encode(image_content).decode('utf-8')
            
            mime_type = self._get_mime_type(image_path=image_path)
            return base64_image, mime_type
            
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {str(e)}")
            raise

    def _encode_image_from_bytes(self, image_content: bytes, content_type: str = None) -> tuple[str, str]:
        """Encode image from bytes to base64 and return with MIME type"""
        try:
            base64_image = base64.b64encode(image_content).decode('utf-8')
            mime_type = self._get_mime_type(content_type=content_type, image_content=image_content)
            return base64_image, mime_type
            
        except Exception as e:
            logger.error(f"Error encoding image from bytes: {str(e)}")
            raise

    def _make_api_request(self, payload: Dict) -> requests.Response:
        """Make API request with proper error handling"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FoodAnalyzer/1.0"
        }
        
        url = f"{self.base_url}?key={self.api_key}"
        
        logger.info(f"Making request to: {url}")
        logger.debug(f"Payload size: {len(json.dumps(payload))} bytes")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30  # Add timeout
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def _parse_response(self, response: requests.Response) -> Dict:
        """Parse and validate API response"""
        try:
            response.raise_for_status()
            content = response.json()
            
            logger.debug(f"Full response: {json.dumps(content, indent=2)}")
            
            # Check for API errors
            if "error" in content:
                error_msg = content["error"].get("message", "Unknown API error")
                logger.error(f"API Error: {error_msg}")
                raise Exception(f"Gemini API Error: {error_msg}")
            
            # Extract text response
            if not content.get("candidates"):
                raise Exception("No candidates in response")
            
            candidate = content["candidates"][0]
            
            # Check for safety filters
            if candidate.get("finishReason") == "SAFETY":
                raise Exception("Content was blocked by safety filters")
            
            if not candidate.get("content", {}).get("parts"):
                raise Exception("No content parts in response")
            
            text_response = candidate["content"]["parts"][0]["text"]
            logger.info(f"Raw text response: {text_response}")
            
            # Clean and parse JSON
            text_response = text_response.strip()
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
            text_response = text_response.strip()
            
            try:
                result = json.loads(text_response)
                logger.info(f"Parsed result: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {str(e)}")
                logger.error(f"Raw text that failed to parse: {text_response}")
                raise Exception(f"Failed to parse JSON response: {str(e)}")
                
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                error_detail = response.json().get("error", {}).get("message", "Bad request")
                logger.error(f"HTTP 400 Error: {error_detail}")
                raise Exception(f"Bad request to Gemini API: {error_detail}")
            elif response.status_code == 401:
                logger.error("HTTP 401: Invalid API key")
                raise Exception("Invalid Gemini API key")
            elif response.status_code == 403:
                logger.error("HTTP 403: API access forbidden")
                raise Exception("Gemini API access forbidden - check billing/quotas")
            elif response.status_code == 429:
                logger.error("HTTP 429: Rate limit exceeded")
                raise Exception("Gemini API rate limit exceeded")
            else:
                logger.error(f"HTTP {response.status_code}: {str(e)}")
                raise Exception(f"Gemini API HTTP error: {response.status_code}")

    async def analyze_image(self, image_path: str, description: str = None) -> Dict[str, any]:
        """
        Analyze a food image from file path and return nutritional information.
        Optionally use a user-provided description for more context.
        """
        logger.info(f"Starting image analysis for: {image_path}")
        
        try:
            # Encode image from file path
            base64_image, mime_type = self._encode_image_from_path(image_path)
            logger.info(f"Image encoded successfully. MIME type: {mime_type}")
            
            return await self._analyze_image_with_data(base64_image, mime_type, description=description)
            
        except Exception as e:
            logger.error(f"Error in analyze_image: {str(e)}", exc_info=True)
            return self._get_error_response(str(e))

    async def analyze_image_content(self, image_content: bytes, content_type: str = None) -> Dict[str, any]:
        """
        Analyze a food image from raw bytes content.
        """
        logger.info(f"Starting image analysis from bytes content. Content type: {content_type}")
        
        try:
            # Encode image from bytes
            base64_image, mime_type = self._encode_image_from_bytes(image_content, content_type)
            logger.info(f"Image encoded successfully. MIME type: {mime_type}")
            
            return await self._analyze_image_with_data(base64_image, mime_type)
            
        except Exception as e:
            logger.error(f"Error in analyze_image_content: {str(e)}", exc_info=True)
            return self._get_error_response(str(e))

    async def _analyze_image_with_data(self, base64_image: str, mime_type: str, description: str = None) -> Dict[str, any]:
        """
        Core method to analyze image with base64 data and MIME type.
        Optionally use a user-provided description for more context.
        Now requests and expects a 'food_items_details' field: array of objects with 'name', 'count', and 'per_item_calories'.
        """
        try:
            # Prepare prompt text
            prompt_text = (
                "Analyze this image carefully and determine if it contains food items. "
                "Return ONLY a valid JSON object (no markdown formatting) with these exact keys:\n"
                "- 'is_food': boolean (true if image contains any food items, false if not)\n"
                "- 'food_items': array of detected food item names as strings (empty array if no food)\n"
                "- 'food_items_details': array of objects, each with 'name' (string), 'count' (int), and 'per_item_calories' (int, estimated calories per item; 0 if not food or unknown)\n"
                "- 'description': single sentence describing what's in the image, including the number of each food item if possible\n"
                "- 'calories': estimated total calories as a number (0 if no food)\n"
                "- 'nutrients': object with keys 'protein', 'carbs', 'fat', 'sugar' (all numbers in grams, all 0 if no food)\n"
                "- 'confidence': confidence score between 0 and 1\n"
                "- 'exercise_recommendations': object with keys 'steps' (int, number of steps to burn calories) and 'walking_km' (float, km to walk to burn calories)\n\n"
                "Example for food image:\n"
                '{"is_food":true,"food_items":["samosa","chutney"],"food_items_details":[{"name":"samosa","count":5,"per_item_calories":300},{"name":"chutney","count":1,"per_item_calories":0}],"description":"The image shows 5 samosas and 1 chutney on a plate.","calories":1500,"nutrients":{"protein":30,"carbs":150,"fat":90,"sugar":15},"confidence":0.95,"exercise_recommendations":{"steps":30000,"walking_km":30.0}}\n\n'
                "Example for non-food image:\n"
                '{"is_food":false,"food_items":[],"food_items_details":[],"description":"A person sitting in a chair","calories":0,"nutrients":{"protein":0,"carbs":0,"fat":0,"sugar":0},"confidence":0.90,"exercise_recommendations":{"steps":0,"walking_km":0.0}}'
            )
            if description:
                prompt_text = (
                    f"The user provided this description for context: '{description}'. "
                    f"Use this information to help with the analysis if relevant. "
                    + prompt_text
                )
            # Prepare payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt_text
                            },
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_image
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 32,
                    "topP": 1,
                    "maxOutputTokens": 1024,
                }
            }
            
            # Make request (run in thread pool for async)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self._make_api_request, 
                payload
            )
            
            # Parse response
            result = self._parse_response(response)
            
            # Validate and fix result structure
            result = self._validate_and_fix_result(result)
            
            logger.info("Image analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in _analyze_image_with_data: {str(e)}", exc_info=True)
            return self._get_error_response(str(e))

    def _validate_and_fix_result(self, result: Dict) -> Dict:
        """Validate result structure and add missing keys with defaults, including food_items_details"""
        required_keys = ['is_food', 'food_items', 'food_items_details', 'description', 'calories', 'nutrients', 'confidence', 'exercise_recommendations']
        
        for key in required_keys:
            if key not in result:
                logger.warning(f"Missing key '{key}' in result, adding default")
                if key == 'is_food':
                    result[key] = False
                elif key == 'food_items':
                    result[key] = []
                elif key == 'food_items_details':
                    result[key] = []
                elif key == 'description':
                    result[key] = "Image analyzed"
                elif key == 'calories':
                    result[key] = 0
                elif key == 'nutrients':
                    result[key] = {"protein": 0, "carbs": 0, "fat": 0, "sugar": 0}
                elif key == 'confidence':
                    result[key] = 0.5
                elif key == 'exercise_recommendations':
                    cals = result.get('calories', 0)
                    result[key] = {"steps": int(cals*20), "walking_km": round(cals/50, 2)}
        
        # Ensure nutrients has all required keys
        if 'nutrients' in result and isinstance(result['nutrients'], dict):
            nutrient_keys = ['protein', 'carbs', 'fat', 'sugar']
            for nutrient in nutrient_keys:
                if nutrient not in result['nutrients']:
                    result['nutrients'][nutrient] = 0
        
        # Ensure exercise_recommendations has both keys
        if 'exercise_recommendations' in result:
            rec = result['exercise_recommendations']
            cals = result.get('calories', 0)
            if not isinstance(rec, dict):
                rec = {"steps": int(cals*20), "walking_km": round(cals/50, 2)}
            if 'steps' not in rec:
                rec['steps'] = int(cals*20)
            if 'walking_km' not in rec:
                rec['walking_km'] = round(cals/50, 2)
            result['exercise_recommendations'] = rec
        
        return result

    def _get_error_response(self, error_message: str) -> Dict:
        """Generate standard error response"""
        return {
            "description": f"Error analyzing image: {error_message}",
            "is_food": False,
            "food_items": [],
            "calories": 0,
            "nutrients": {"protein": 0, "carbs": 0, "fat": 0, "sugar": 0},
            "confidence": 0.0,
            "exercise_recommendations": {"steps": 0, "walking_km": 0.0}
        }

    # Test method for debugging
    async def test_api_connection(self) -> bool:
        """Test if API connection works with a simple text request"""
        try:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": "Say 'Hello, API is working!' in JSON format: {\"message\": \"Hello, API is working!\"}"
                            }
                        ]
                    }
                ]
            }
            
            response = self._make_api_request(payload)
            result = self._parse_response(response)
            logger.info(f"API test successful: {result}")
            return True
            
        except Exception as e:
            logger.error(f"API test failed: {str(e)}")
            return False