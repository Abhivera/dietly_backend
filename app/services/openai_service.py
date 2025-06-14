import openai
from typing import List, Dict
import base64
import json
from app.core.config import settings

class OpenAIService:
    def __init__(self):
        openai.api_key = settings.openai_api_key
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def analyze_image(self, image_path: str) -> Dict[str, any]:
        """
        Analyze image using OpenAI Vision API
        """
        try:
            # Read and encode image
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and provide: 1) A detailed description, 2) A list of relevant tags/keywords, 3) Your confidence level (0-1). Format as JSON with keys: description, tags, confidence"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to manual parsing if needed
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Fallback parsing
                result = {
                    "description": content,
                    "tags": [],
                    "confidence": 0.8
                }
            
            return result
            
        except Exception as e:
            return {
                "description": f"Error analyzing image: {str(e)}",
                "tags": [],
                "confidence": 0.0
            }
    
    async def generate_image_tags(self, description: str) -> List[str]:
        """
        Generate tags based on image description
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": f"Generate 5-10 relevant tags for an image with this description: {description}. Return only the tags separated by commas."
                    }
                ],
                max_tokens=100
            )
            
            tags_text = response.choices[0].message.content.strip()
            tags = [tag.strip() for tag in tags_text.split(',')]
            return tags
            
        except Exception as e:
            return ["error", "analysis_failed"]