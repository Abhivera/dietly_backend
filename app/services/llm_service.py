import base64
import json
import logging
from typing import List, Dict, Optional
import requests
import asyncio
from pathlib import Path
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
    
    def _get_mime_type(self, image_path: str) -> str:
        """Determine MIME type based on file extension"""
        extension = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_types.get(extension, 'image/jpeg')
    
    def _encode_image(self, image_path: str) -> tuple[str, str]:
        """Encode image to base64 and return with MIME type"""
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            mime_type = self._get_mime_type(image_path)
            return base64_image, mime_type
            
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {str(e)}")
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

    async def analyze_image(self, image_path: str) -> Dict[str, any]:
        """
        Analyze a food image and return nutritional information.
        """
        logger.info(f"Starting image analysis for: {image_path}")
        
        try:
            # Encode image
            base64_image, mime_type = self._encode_image(image_path)
            logger.info(f"Image encoded successfully. MIME type: {mime_type}")
            
            # Prepare payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    "Analyze this image carefully and determine if it contains food items. "
                                    "Return ONLY a valid JSON object (no markdown formatting) with these exact keys:\n"
                                    "- 'is_food': boolean (true if image contains any food items, false if not)\n"
                                    "- 'food_items': array of detected food item names as strings (empty array if no food)\n"
                                    "- 'description': single sentence describing what's in the image\n"
                                    "- 'calories': estimated total calories as a number (0 if no food)\n"
                                    "- 'nutrients': object with keys 'protein', 'carbs', 'fat', 'sugar' (all numbers in grams, all 0 if no food)\n"
                                    "- 'confidence': confidence score between 0 and 1\n\n"
                                    "Example for food image:\n"
                                    '{"is_food":true,"food_items":["apple","banana"],"description":"Fresh fruits on a plate","calories":120,"nutrients":{"protein":1,"carbs":30,"fat":0,"sugar":25},"confidence":0.85}\n\n'
                                    "Example for non-food image:\n"
                                    '{"is_food":false,"food_items":[],"description":"A person sitting in a chair","calories":0,"nutrients":{"protein":0,"carbs":0,"fat":0,"sugar":0},"confidence":0.90}'
                                )
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
            
            # Validate result structure
            required_keys = ['is_food', 'food_items', 'description', 'calories', 'nutrients', 'confidence']
            for key in required_keys:
                if key not in result:
                    logger.warning(f"Missing key '{key}' in result, adding default")
                    if key == 'is_food':
                        result[key] = False
                    elif key == 'food_items':
                        result[key] = []
                    elif key == 'description':
                        result[key] = "Image analyzed"
                    elif key == 'calories':
                        result[key] = 0
                    elif key == 'nutrients':
                        result[key] = {"protein": 0, "carbs": 0, "fat": 0, "sugar": 0}
                    elif key == 'confidence':
                        result[key] = 0.5
            
            logger.info("Image analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in analyze_image: {str(e)}", exc_info=True)
            return {
                "description": f"Error analyzing image: {str(e)}",
                "is_food": False,
                "food_items": [],
                "calories": 0,
                "nutrients": {"protein": 0, "carbs": 0, "fat": 0, "sugar": 0},
                "confidence": 0.0
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