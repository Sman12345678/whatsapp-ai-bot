import json
import logging
import os
import time
from google import genai
from google.genai import types
from pydantic import BaseModel
from config import Config

logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=Config.GEMINI_API_KEY)

class AIService:
    """AI service for handling Gemini interactions"""
    
    @staticmethod
    def get_chat_system_instruction():
        """System instruction for chat interactions"""
        return (
            f"You are {Config.BOT_NAME}, a helpful, fun, and engaging WhatsApp AI assistant. "
            "Your personality traits:\n"
            "- Friendly and approachable with appropriate emojis 😊\n"
            "- Professional yet conversational\n"
            "- Knowledgeable across various topics\n"
            "- Helpful in solving problems and answering questions\n"
            "- Engaging and interactive\n"
            "- Concise but informative responses\n"
            "- Always maintain a positive and supportive tone\n\n"
            "Guidelines:\n"
            "- Keep responses under 300 words for WhatsApp\n"
            "- Use emojis appropriately to enhance communication\n"
            "- Offer follow-up questions when helpful\n"
            "- If you can't help with something, explain why and suggest alternatives\n"
            "- Remember this is a WhatsApp conversation, so be conversational"
        )
    
    @staticmethod
    def get_file_analysis_instruction():
        """System instruction for file analysis"""
        return (
            "You are an expert file content analyzer. Analyze the provided file content and:\n"
            "1. Summarize the main content and purpose\n"
            "2. Identify key information, patterns, or insights\n"
            "3. Highlight important sections or data\n"
            "4. Suggest potential uses or next steps\n"
            "5. Point out any issues, errors, or improvements\n\n"
            "Keep your analysis clear, structured, and actionable. "
            "Use bullet points and emojis for better readability in WhatsApp."
        )
    
    @staticmethod
    def get_image_analysis_instruction():
        """System instruction for image analysis"""
        return (
            "You are an expert image analyzer. Analyze the provided image and:\n"
            "1. Describe what you see in detail\n"
            "2. Identify objects, people, text, or scenes\n"
            "3. Explain the context or setting\n"
            "4. Note colors, composition, and visual elements\n"
            "5. Extract any text present in the image\n"
            "6. Suggest what the image might be used for\n\n"
            "Provide a comprehensive yet concise analysis suitable for WhatsApp. "
            "Use emojis and bullet points for better formatting."
        )
    
    @staticmethod
    def chat_response(message: str, user_context: dict = None) -> str:
        """Generate chat response using Gemini"""
        try:
            start_time = time.time()
            
            prompt = f"User message: {message}"
            if user_context:
                prompt = f"User context: {user_context}\n\n{prompt}"
            
            response = client.models.generate_content(
                model=Config.AI_CHAT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=AIService.get_chat_system_instruction(),
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Chat response generated in {processing_time:.2f}s")
            
            return response.text or "🤔 I'm having trouble generating a response right now. Please try again!"
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return "❌ Sorry, I'm experiencing technical difficulties. Please try again later!"
    
    @staticmethod
    def analyze_file_content(content: str, filename: str, file_type: str) -> str:
        """Analyze file content using Gemini"""
        try:
            start_time = time.time()
            
            prompt = (
                f"File: {filename}\n"
                f"Type: {file_type}\n"
                f"Content:\n{content}"
            )
            
            response = client.models.generate_content(
                model=Config.AI_ANALYSIS_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=AIService.get_file_analysis_instruction(),
                    temperature=0.3,
                    max_output_tokens=1500
                )
            )
            
            processing_time = time.time() - start_time
            logger.info(f"File analysis completed in {processing_time:.2f}s")
            
            return response.text or "📄 I couldn't analyze this file. The content might be too complex or corrupted."
            
        except Exception as e:
            logger.error(f"Error analyzing file content: {e}")
            return "❌ Error analyzing file. Please try again or check if the file format is supported."
    
    @staticmethod
    def analyze_image(image_bytes: bytes, filename: str = "image") -> str:
        """Analyze image using Gemini Vision"""
        try:
            start_time = time.time()
            
            response = client.models.generate_content(
                model=Config.AI_ANALYSIS_MODEL,
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg"
                    ),
                    "Analyze this image in detail."
                ],
                config=types.GenerateContentConfig(
                    system_instruction=AIService.get_image_analysis_instruction(),
                    temperature=0.3,
                    max_output_tokens=1500
                )
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Image analysis completed in {processing_time:.2f}s")
            
            return response.text or "🖼️ I couldn't analyze this image. Please try with a different image."
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return "❌ Error analyzing image. Please ensure the image is clear and try again."
    
    @staticmethod
    def generate_image(prompt: str) -> bytes:
        """Generate image using Gemini"""
        try:
            start_time = time.time()
            
            response = client.models.generate_content(
                model=Config.AI_IMAGE_GENERATION_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                    temperature=0.7
                )
            )
            
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        processing_time = time.time() - start_time
                        logger.info(f"Image generated in {processing_time:.2f}s")
                        return part.inline_data.data
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None

class AnalysisResult(BaseModel):
    """Structured analysis result"""
    summary: str
    key_points: list
    recommendations: list
    confidence: float

def analyze_content_structured(content: str, content_type: str) -> AnalysisResult:
    """Analyze content with structured output"""
    try:
        system_prompt = (
            "Analyze the provided content and return a structured analysis. "
            "Focus on key insights, main points, and actionable recommendations."
        )
        
        prompt = f"Content Type: {content_type}\n\nContent:\n{content}"
        
        response = client.models.generate_content(
            model=Config.AI_ANALYSIS_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=AnalysisResult,
                temperature=0.3
            )
        )
        
        if response.text:
            data = json.loads(response.text)
            return AnalysisResult(**data)
        else:
            raise ValueError("Empty response from model")
            
    except Exception as e:
        logger.error(f"Error in structured analysis: {e}")
        return AnalysisResult(
            summary="Analysis failed",
            key_points=["Error occurred during analysis"],
            recommendations=["Please try again with different content"],
            confidence=0.0
        )
