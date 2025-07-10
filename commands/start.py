import logging
from pywa import WhatsApp, types
from models import User
from config import Config

logger = logging.getLogger(__name__)

def handle_start_command(client: WhatsApp, message, user: User):
    """Handle start command"""
    try:
        welcome_text = f"🎉 *Welcome to {Config.BOT_NAME}!*\n\n"
        
        if user.name:
            welcome_text += f"Hello {user.name}! 👋\n\n"
        else:
            welcome_text += f"Hello there! 👋\n\n"
        
        welcome_text += "🤖 I'm an AI-powered WhatsApp bot with amazing capabilities:\n\n"
        
        welcome_text += "💬 *Chat Features:*\n"
        welcome_text += "• Intelligent conversations with AI\n"
        welcome_text += "• Fun and engaging responses\n"
        welcome_text += "• Contextual understanding\n\n"
        
        welcome_text += "📄 *File Analysis:*\n"
        welcome_text += "• PDF text extraction\n"
        welcome_text += "• Code analysis (Python, JS, etc.)\n"
        welcome_text += "• Document processing\n"
        welcome_text += "• HTML, JSON, CSV parsing\n\n"
        
        welcome_text += "🖼️ *Image Analysis:*\n"
        welcome_text += "• Describe images in detail\n"
        welcome_text += "• Extract text from images\n"
        welcome_text += "• Object and scene recognition\n\n"
        
        if user.is_admin:
            welcome_text += "👑 *Admin Features:*\n"
            welcome_text += "• Group management tools\n"
            welcome_text += "• User moderation\n"
            welcome_text += "• Broadcast messages\n"
            welcome_text += "• Bot analytics dashboard\n\n"
        
        welcome_text += "🚀 *Getting Started:*\n"
        welcome_text += f"• Type `{Config.BOT_PREFIX}help` for all commands\n"
        welcome_text += "• Send me any message to start chatting\n"
        welcome_text += "• Send images or files for analysis\n\n"
        
        welcome_text += "Let's start our conversation! What would you like to do? 😊"
        
        buttons = [
            types.Button(title="💬 Start Chat", callback_data="start_chat"),
            types.Button(title="📚 Help", callback_data="help"),
            types.Button(title="📊 Features", callback_data="info")
        ]
        
        if user.is_admin:
            buttons.append(types.Button(title="👑 Admin Panel", callback_data="admin_panel"))
        
        if hasattr(message, 'reply_text'):
            message.reply_text(text=welcome_text, buttons=buttons)
        else:
            # Handle callback button
            message.reply_text(text=welcome_text, buttons=buttons)
        
        # Add a welcome reaction
        if hasattr(message, 'react'):
            message.react("🎉")
            
        logger.info(f"Start command executed for user {user.phone_number}")
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        if hasattr(message, 'reply_text'):
            message.reply_text("❌ Error showing welcome message. Please try again.")
        else:
            message.reply_text("❌ Error showing welcome message. Please try again.")
