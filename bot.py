import os
import logging
from pywa import WhatsApp, types, filters
from pywa.errors import WhatsAppError
from app import app, db
from config import Config
from models import User, Group, Message
from datetime import datetime

# Import command handlers
from commands.help import handle_help_command
from commands.start import handle_start_command
from commands.admin import handle_admin_commands
from commands.group import handle_group_commands
from commands.ai import handle_ai_chat, handle_file_message, handle_image_message

logger = logging.getLogger(__name__)

# Initialize WhatsApp bot (only if credentials are available)
wa = None
if Config.WHATSAPP_PHONE_ID and Config.WHATSAPP_ACCESS_TOKEN:
    try:
        wa = WhatsApp(
            phone_id=Config.WHATSAPP_PHONE_ID,
            token=Config.WHATSAPP_ACCESS_TOKEN,
            server=app,
            callback_url=f"{Config.WEBHOOK_URL}/webhook",
            verify_token=Config.WHATSAPP_VERIFY_TOKEN,
            app_id=Config.WHATSAPP_APP_ID,
            app_secret=Config.WHATSAPP_APP_SECRET
        )
        logger.info("WhatsApp bot initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize WhatsApp bot: {e}")
        wa = None
else:
    logger.warning("WhatsApp bot running in demo mode - no API credentials provided")

def get_or_create_user(phone_number: str, name: str = None) -> User:
    """Get or create user in database"""
    with app.app_context():
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            user = User(
                phone_number=phone_number,
                name=name,
                is_admin=(phone_number == Config.BOT_ADMIN_PHONE)
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user: {phone_number}")
        else:
            user.last_seen = datetime.utcnow()
            if name and not user.name:
                user.name = name
            db.session.commit()
        return user

def log_message(message: types.Message) -> None:
    """Log message to database"""
    with app.app_context():
        try:
            user = get_or_create_user(message.from_user.wa_id, message.from_user.name)
            
            # Check if user is banned
            if user.is_banned:
                message.reply_text("❌ You are banned from using this bot.")
                return
            
            msg = Message(
                message_id=message.id,
                user_id=user.id,
                content=getattr(message, 'text', ''),
                message_type=message.type.value,
                is_command=message.text and message.text.startswith(Config.BOT_PREFIX) if hasattr(message, 'text') else False,
                command_name=message.text.split()[0][1:] if message.text and message.text.startswith(Config.BOT_PREFIX) else None
            )
            
            # Handle group messages
            if hasattr(message, 'from_') and hasattr(message.from_, 'group_id'):
                group = Group.query.filter_by(group_id=message.from_.group_id).first()
                if not group:
                    group = Group(group_id=message.from_.group_id)
                    db.session.add(group)
                    db.session.commit()
                msg.group_id = group.id
            
            db.session.add(msg)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging message: {e}")

def handle_message(client: WhatsApp, msg: types.Message):
    """Main message handler"""
    try:
        user = get_or_create_user(msg.from_user.wa_id, msg.from_user.name)
        
        # Check if user is banned
        if user.is_banned:
            admin_contact = getattr(Config, "BOT_ADMIN_PHONE", None)
            admin_msg = f"❌ You are banned from using this bot."
            if admin_contact:
                admin_msg += f" Please contact the admin at {admin_contact} for more information."
            msg.reply_text(admin_msg)
            return

        log_message(msg)
        
        # Check if it's a command
        if msg.text and msg.text.startswith(Config.BOT_PREFIX):
            handle_command(client, msg)
        else:
            # Handle different message types
            if msg.type == types.MessageType.TEXT:
                handle_ai_chat(client, msg)
            elif msg.type == types.MessageType.IMAGE:
                handle_image_message(client, msg)
            elif msg.type == types.MessageType.DOCUMENT:
                handle_file_message(client, msg)
            else:
                msg.reply_text(
                    f"🤖 I received your message! Send me text to chat or use {Config.BOT_PREFIX}help for commands."
                )
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        msg.reply_text("❌ Sorry, something went wrong. Please try again later.")

# Only register handlers if WhatsApp bot is initialized
if wa:
    wa.on_message()(handle_message)

def handle_command(client: WhatsApp, msg: types.Message):
    """Handle bot commands"""
    command_text = msg.text.lower()
    command = command_text.split()[0][1:]  # Remove prefix
    
    user = get_or_create_user(msg.from_user.wa_id, msg.from_user.name)
    
    try:
        if command == "help":
            handle_help_command(client, msg, user)
        elif command == "start":
            handle_start_command(client, msg, user)
        elif command in ["admin", "broadcast", "ban", "unban", "stats"]:
            handle_admin_commands(client, msg, user, command)
        elif command in ["kick", "ban", "mute", "unmute", "promote", "demote"]:
            handle_group_commands(client, msg, user, command)
        else:
            msg.reply_text(
                f"❓ Unknown command: `{command}`\n\n"
                f"Type `{Config.BOT_PREFIX}help` to see available commands.",
                buttons=[
                    types.Button(title="📚 Help", callback_data="help"),
                    types.Button(title="🏠 Start", callback_data="start")
                ]
            )
    except Exception as e:
        logger.error(f"Error handling command {command}: {e}")
        msg.reply_text("❌ Error executing command. Please try again.")

def handle_button_callback(client: WhatsApp, clb: types.CallbackButton):
    """Handle button callbacks"""
    try:
        user = get_or_create_user(clb.from_user.wa_id, clb.from_user.name)
        
        if clb.data == "help":
            handle_help_command(client, clb, user)
        elif clb.data == "start":
            handle_start_command(client, clb, user)
        elif clb.data.startswith("admin_"):
            if user.is_admin:
                handle_admin_commands(client, clb, user, clb.data.replace("admin_", ""))
            else:
                clb.reply_text("❌ Admin access required.")
        else:
            clb.reply_text("🤖 Button processed!")
            
    except Exception as e:
        logger.error(f"Error handling button callback: {e}")
        clb.reply_text("❌ Error processing button. Please try again.")

def handle_message_status(client: WhatsApp, status: types.MessageStatus):
    """Handle message status updates"""
    logger.debug(f"Message {status.id} status: {status.status}")

# Register all handlers if WhatsApp bot is initialized
if wa:
    wa.on_callback_button()(handle_button_callback)
    wa.on_message_status()(handle_message_status)
    logger.info("WhatsApp bot handlers registered successfully")
else:
    logger.info("WhatsApp bot running in demo mode")
