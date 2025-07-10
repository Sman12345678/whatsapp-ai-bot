import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the WhatsApp bot"""
    
    # WhatsApp API Configuration
    WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_APP_ID = os.getenv("WHATSAPP_APP_ID")
    WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")
    WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "your_verify_token")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://yourdomain.com")
    
    # Google Gemini AI Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Bot Configuration
    BOT_PREFIX = os.getenv("BOT_PREFIX", "/")
    BOT_NAME = os.getenv("BOT_NAME", "WhatsApp AI Bot")
    BOT_ADMIN_PHONE = os.getenv("BOT_ADMIN_PHONE")
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///whatsapp_bot.db")
    
    # Security
    SESSION_SECRET = os.getenv("SESSION_SECRET", "your-secret-key-here")
    
    # Bot Settings
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "16777216"))  # 16MB default
    SUPPORTED_FILE_TYPES = [
        'pdf', 'txt', 'html', 'js', 'py', 'json', 'csv', 
        'md', 'xml', 'yaml', 'yml', 'log', 'css', 'java',
        'cpp', 'c', 'php', 'rb', 'go', 'rs', 'swift'
    ]
    SUPPORTED_IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    
    # AI Configuration
    AI_CHAT_MODEL = "gemini-2.5-flash"
    AI_ANALYSIS_MODEL = "gemini-2.5-pro"
    AI_IMAGE_GENERATION_MODEL = "gemini-2.0-flash-preview-image-generation"
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "30"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        # Only require GEMINI_API_KEY for basic functionality
        # WhatsApp credentials are optional for demo/development
        required_vars = [
            'GEMINI_API_KEY'
        ]
        
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Warn about missing WhatsApp credentials but don't fail
        whatsapp_vars = ['WHATSAPP_PHONE_ID', 'WHATSAPP_ACCESS_TOKEN']
        missing_whatsapp = [var for var in whatsapp_vars if not getattr(cls, var)]
        if missing_whatsapp:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"WhatsApp API credentials missing: {', '.join(missing_whatsapp)}. Bot will run in demo mode.")
        
        return True

# Validate configuration on import
Config.validate()
