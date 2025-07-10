import logging
from pywa import WhatsApp, types
from models import User
from config import Config

logger = logging.getLogger(__name__)

def handle_help_command(client: WhatsApp, message, user: User):
    """Handle help command"""
    try:
        help_text = f"🤖 *{Config.BOT_NAME} - Help*\n\n"
        help_text += "📚 *Available Commands:*\n\n"
        
        # Basic commands
        help_text += f"`{Config.BOT_PREFIX}start` - Start conversation with bot\n"
        help_text += f"`{Config.BOT_PREFIX}help` - Show this help message\n"
        help_text += f"`{Config.BOT_PREFIX}info` - Get bot information\n\n"
        
        # AI features
        help_text += "🧠 *AI Features:*\n"
        help_text += "• Send any text message for AI chat\n"
        help_text += "• Send images for AI analysis\n"
        help_text += "• Send documents for content analysis\n"
        help_text += "• Supported files: PDF, TXT, HTML, JSON, CSV, XML, YAML, code files\n\n"
        
        # Admin commands (only show to admins)
        if user.is_admin:
            help_text += "👑 *Admin Commands:*\n"
            help_text += f"`{Config.BOT_PREFIX}admin` - Show admin panel\n"
            help_text += f"`{Config.BOT_PREFIX}broadcast <message>` - Broadcast to all users\n"
            help_text += f"`{Config.BOT_PREFIX}ban <user>` - Ban a user\n"
            help_text += f"`{Config.BOT_PREFIX}unban <user>` - Unban a user\n"
            help_text += f"`{Config.BOT_PREFIX}stats` - Show bot statistics\n\n"
            
            help_text += "🛡️ *Group Management:*\n"
            help_text += f"`{Config.BOT_PREFIX}kick @user` - Remove user from group\n"
            help_text += f"`{Config.BOT_PREFIX}mute @user` - Mute user in group\n"
            help_text += f"`{Config.BOT_PREFIX}unmute @user` - Unmute user\n"
            help_text += f"`{Config.BOT_PREFIX}promote @user` - Promote to admin\n"
            help_text += f"`{Config.BOT_PREFIX}demote @user` - Remove admin rights\n\n"
        
        help_text += "💡 *Tips:*\n"
        help_text += "• Just send me a message to start chatting!\n"
        help_text += "• I can analyze images and extract text\n"
        help_text += "• Send me documents for detailed analysis\n"
        help_text += "• Use reactions to interact with my messages\n\n"
        
        help_text += "🔗 *Quick Actions:*"
        
        buttons = [
            types.Button(title="🏠 Start", callback_data="start"),
            types.Button(title="📊 Info", callback_data="info")
        ]
        
        if user.is_admin:
            buttons.append(types.Button(title="👑 Admin", callback_data="admin_panel"))
        
        if hasattr(message, 'reply_text'):
            message.reply_text(text=help_text, buttons=buttons)
        else:
            # Handle callback button
            message.reply_text(text=help_text, buttons=buttons)
            
        logger.info(f"Help command executed for user {user.phone_number}")
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        if hasattr(message, 'reply_text'):
            message.reply_text("❌ Error showing help. Please try again.")
        else:
            message.reply_text("❌ Error showing help. Please try again.")
