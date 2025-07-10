import logging
import os
import tempfile
import time
from pywa import WhatsApp, types
from models import User, AIRequest, FileProcessing
from config import Config
from app import db
from gemini_service import AIService
from file_processor import FileProcessor

logger = logging.getLogger(__name__)

def handle_ai_chat(client: WhatsApp, message: types.Message):
    """Handle AI chat messages"""
    try:
        user = get_user_from_message(message)
        if not user or user.is_banned:
            return
        
        if not message.text:
            message.reply_text("🤖 Send me a text message to start chatting!")
            return
        
        # Show typing indicator
        message.reply_text("🤔 Thinking...")
        
        start_time = time.time()
        
        # Get AI response
        user_context = {
            'name': user.name,
            'phone': user.phone_number,
            'is_admin': user.is_admin
        }
        
        ai_response = AIService.chat_response(message.text, user_context)
        processing_time = time.time() - start_time
        
        # Log AI request
        log_ai_request(user, 'chat', message.text, ai_response, processing_time)
        
        # Send response with reaction
        message.reply_text(ai_response)
        message.react("🤖")
        
        logger.info(f"AI chat processed for {user.phone_number} in {processing_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        message.reply_text("❌ Sorry, I'm having trouble thinking right now. Please try again! 🤖")

def handle_image_message(client: WhatsApp, message: types.Message):
    """Handle image analysis"""
    try:
        user = get_user_from_message(message)
        if not user or user.is_banned:
            return
        
        message.reply_text("📸 Analyzing your image...")
        
        try:
            # Download image
            media_url = client.get_media_url(message.image.id)
            image_bytes = FileProcessor.download_whatsapp_media(media_url, Config.WHATSAPP_ACCESS_TOKEN)
            
            if not image_bytes:
                message.reply_text("❌ Failed to download image. Please try again.")
                return
            
            start_time = time.time()
            
            # Analyze image with AI
            analysis = AIService.analyze_image(image_bytes, message.image.filename or "image")
            processing_time = time.time() - start_time
            
            # Log AI request
            log_ai_request(user, 'image_analysis', f"Image: {message.image.filename}", analysis, processing_time)
            
            # Send analysis
            response_text = f"🖼️ *Image Analysis*\n\n{analysis}"
            message.reply_text(response_text)
            message.react("👁️")
            
            logger.info(f"Image analysis completed for {user.phone_number} in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            message.reply_text("❌ Error analyzing image. Please ensure the image is clear and try again.")
        
    except Exception as e:
        logger.error(f"Error in image handler: {e}")
        message.reply_text("❌ Error processing image.")

def handle_file_message(client: WhatsApp, message: types.Message):
    """Handle file analysis"""
    try:
        user = get_user_from_message(message)
        if not user or user.is_banned:
            return
        
        document = message.document
        filename = document.filename or "unknown_file"
        
        # Check if file type is supported
        if not FileProcessor.is_supported_file(filename):
            message.reply_text(
                f"❌ Unsupported file type. Supported formats:\n"
                f"📄 Documents: {', '.join(Config.SUPPORTED_FILE_TYPES[:10])}\n"
                f"🖼️ Images: {', '.join(Config.SUPPORTED_IMAGE_TYPES)}"
            )
            return
        
        message.reply_text(f"📄 Processing file: `{filename}`...")
        
        try:
            # Download file
            media_url = client.get_media_url(document.id)
            file_bytes = FileProcessor.download_whatsapp_media(media_url, Config.WHATSAPP_ACCESS_TOKEN)
            
            if not file_bytes:
                message.reply_text("❌ Failed to download file. Please try again.")
                return
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_file.write(file_bytes)
                temp_file_path = temp_file.name
            
            try:
                start_time = time.time()
                
                # Process file content
                content, file_info = FileProcessor.process_file(temp_file_path)
                
                if content.startswith("❌"):
                    message.reply_text(content)
                    return
                
                # Analyze with AI
                ai_analysis = AIService.analyze_file_content(content, filename, file_info.get('extension', ''))
                processing_time = time.time() - start_time
                
                # Log processing
                log_file_processing(user, filename, file_info, processing_time, True, True)
                log_ai_request(user, 'file_analysis', f"File: {filename}", ai_analysis, processing_time)
                
                # Send analysis
                response_text = f"📄 *File Analysis: {filename}*\n\n{ai_analysis}"
                
                # Split long messages
                if len(response_text) > 4000:
                    # Send summary first
                    summary_lines = response_text.split('\n')[:15]
                    summary = '\n'.join(summary_lines) + "\n\n📄 *[Content truncated for WhatsApp]*"
                    message.reply_text(summary)
                    
                    # Send full analysis in parts
                    chunks = [response_text[i:i+3500] for i in range(0, len(response_text), 3500)]
                    for i, chunk in enumerate(chunks[:3]):  # Limit to 3 chunks
                        if i == 0:
                            continue  # Skip first chunk as it's already sent as summary
                        message.reply_text(f"📄 *Part {i+1}*\n\n{chunk}")
                else:
                    message.reply_text(response_text)
                
                message.react("📄")
                
                logger.info(f"File analysis completed for {user.phone_number}: {filename} in {processing_time:.2f}s")
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            message.reply_text("❌ Error processing file. Please check the file format and try again.")
        
    except Exception as e:
        logger.error(f"Error in file handler: {e}")
        message.reply_text("❌ Error handling file.")

def get_user_from_message(message: types.Message) -> User:
    """Get user from message"""
    from bot import get_or_create_user
    return get_or_create_user(message.from_user.wa_id, message.from_user.name)

def log_ai_request(user: User, request_type: str, prompt: str, response: str, processing_time: float):
    """Log AI request to database"""
    try:
        ai_request = AIRequest(
            user_id=user.id,
            request_type=request_type,
            prompt=prompt[:1000],  # Truncate long prompts
            response=response[:2000],  # Truncate long responses
            processing_time=processing_time
        )
        db.session.add(ai_request)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error logging AI request: {e}")

def log_file_processing(user: User, filename: str, file_info: dict, processing_time: float, content_extracted: bool, ai_analyzed: bool):
    """Log file processing to database"""
    try:
        file_processing = FileProcessing(
            user_id=user.id,
            filename=filename,
            file_type=file_info.get('extension', 'unknown'),
            file_size=file_info.get('size', 0),
            content_extracted=content_extracted,
            ai_analyzed=ai_analyzed,
            processing_time=processing_time
        )
        db.session.add(file_processing)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error logging file processing: {e}")
