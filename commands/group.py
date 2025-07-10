import logging
from pywa import WhatsApp, types
from models import User
from config import Config
import re

logger = logging.getLogger(__name__)

def handle_group_commands(client: WhatsApp, message, user: User, command: str):
    """Handle group management commands (ban/unban only)"""
    try:
        if not user.is_admin:
            message.reply_text("❌ Access denied. Admin privileges required.")
            return

        # Check if message is from a group
        if not hasattr(message, "from_") or not hasattr(message.from_, "group_id"):
            message.reply_text("❌ This command can only be used in groups.")
            return

        if command == "ban":
            handle_ban_user(client, message, user)
        elif command == "unban":
            handle_unban_user(client, message, user)
        else:
            message.reply_text(f"❓ Unknown group command: {command}")
    except Exception as e:
        logger.error(f"Error in group command {command}: {e}")
        message.reply_text("❌ Error executing group command.")

def extract_mentioned_user(message_text: str):
    """Extract mentioned user from message"""
    mentions = re.findall(r'@(\w+)', message_text)
    if mentions:
        return mentions[0]
    phones = re.findall(r'\+?[\d\s\-\(\)]+', message_text)
    if phones:
        return phones[0].strip()
    return None

def handle_ban_user(client: WhatsApp, message, user: User):
    """Ban a user from the bot (prevents user from interacting with the bot)"""
    try:
        mentioned = extract_mentioned_user(message.text)
        if not mentioned:
            message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}ban @username` or `{Config.BOT_PREFIX}ban <phone_number>`")
            return

        # Find user in DB by phone number or username
        banned_user = User.query.filter(
            (User.phone_number == mentioned) | (User.name == mentioned)
        ).first()
        if not banned_user:
            message.reply_text(f"❌ User `{mentioned}` not found.")
            return

        if banned_user.is_admin:
            message.reply_text("❌ You can't ban another admin.")
            return

        banned_user.is_banned = True
        banned_user.banned_by = user.id
        banned_user.banned_at = types.now()
        banned_user.ban_reason = f"Banned by {user.name or user.phone_number} in group {getattr(message.from_, 'group_id', '')}"
        from app import db
        db.session.commit()

        response_text = (
            f"🔨 *Ban User*\n\n"
            f"User: {banned_user.name or banned_user.phone_number}\n"
            f"Action: Banned from bot\n"
            f"By: {user.name or user.phone_number}\n"
            f"🄾 User will not be able to interact with the bot."
        )
        message.reply_text(response_text)
        logger.info(f"Ban command executed by {user.phone_number} for {mentioned}")

    except Exception as e:
        logger.error(f"Error banning user: {e}")
        message.reply_text("❌ Error banning user.")

def handle_unban_user(client: WhatsApp, message, user: User):
    """Unban a user from the bot (restores user access)"""
    try:
        mentioned = extract_mentioned_user(message.text)
        if not mentioned:
            message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}unban @username` or `{Config.BOT_PREFIX}unban <phone_number>`")
            return

        unbanned_user = User.query.filter(
            (User.phone_number == mentioned) | (User.name == mentioned)
        ).first()
        if not unbanned_user:
            message.reply_text(f"❌ User `{mentioned}` not found.")
            return

        unbanned_user.is_banned = False
        unbanned_user.banned_by = None
        unbanned_user.banned_at = None
        unbanned_user.ban_reason = None
        from app import db
        db.session.commit()

        response_text = (
            f"✅ *Unban User*\n\n"
            f"User: {unbanned_user.name or unbanned_user.phone_number}\n"
            f"Action: Unbanned\n"
            f"By: {user.name or user.phone_number}\n"
            f"🄾 User can now interact with the bot."
        )
        message.reply_text(response_text)
        logger.info(f"Unban command executed by {user.phone_number} for {mentioned}")

    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        message.reply_text("❌ Error unbanning user.")
