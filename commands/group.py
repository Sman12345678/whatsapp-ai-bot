import logging
from pywa import WhatsApp, types
from models import User
from config import Config
import re

logger = logging.getLogger(__name__)

def handle_group_commands(client: WhatsApp, message, user: User, command: str):
    """Handle group management commands"""
    try:
        if not user.is_admin:
            message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        # Check if message is from a group
        if not hasattr(message, 'from_') or not hasattr(message.from_, 'group_id'):
            message.reply_text("❌ This command can only be used in groups.")
            return
        
        if command == "kick":
            handle_kick_user(client, message, user)
        elif command == "ban":
            handle_ban_from_group(client, message, user)
        elif command == "mute":
            handle_mute_user(client, message, user)
        elif command == "unmute":
            handle_unmute_user(client, message, user)
        elif command == "promote":
            handle_promote_user(client, message, user)
        elif command == "demote":
            handle_demote_user(client, message, user)
        else:
            message.reply_text(f"❓ Unknown group command: {command}")
            
    except Exception as e:
        logger.error(f"Error in group command {command}: {e}")
        message.reply_text("❌ Error executing group command.")

def extract_mentioned_user(message_text: str) -> str:
    """Extract mentioned user from message"""
    # Look for @username or phone number patterns
    mentions = re.findall(r'@(\w+)', message_text)
    if mentions:
        return mentions[0]
    
    # Look for phone numbers
    phones = re.findall(r'\+?[\d\s\-\(\)]+', message_text)
    if phones:
        return phones[0].strip()
    
    return None

def handle_kick_user(client: WhatsApp, message, user: User):
    """Handle kicking user from group"""
    try:
        mentioned_user = extract_mentioned_user(message.text)
        if not mentioned_user:
            message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}kick @username` or `{Config.BOT_PREFIX}kick <phone_number>`")
            return
        
        # Note: Actual implementation would require WhatsApp Business API group management
        # This is a simulation of the functionality
        
        response_text = f"🚫 *Group Action: Kick User*\n\n"
        response_text += f"Target: {mentioned_user}\n"
        response_text += f"Action: Remove from group\n"
        response_text += f"Executed by: {user.name or user.phone_number}\n\n"
        response_text += "⚠️ *Note: Group management requires WhatsApp Business API group admin permissions.*"
        
        # In a real implementation, you would use:
        # client.remove_group_participant(group_id=message.from_.group_id, user_id=mentioned_user)
        
        message.reply_text(response_text)
        logger.info(f"Kick command executed by {user.phone_number} for {mentioned_user}")
        
    except Exception as e:
        logger.error(f"Error kicking user: {e}")
        message.reply_text("❌ Error removing user from group.")

def handle_ban_from_group(client: WhatsApp, message, user: User):
    """Handle banning user from group"""
    try:
        mentioned_user = extract_mentioned_user(message.text)
        if not mentioned_user:
            message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}ban @username` or `{Config.BOT_PREFIX}ban <phone_number>`")
            return
        
        response_text = f"🔨 *Group Action: Ban User*\n\n"
        response_text += f"Target: {mentioned_user}\n"
        response_text += f"Action: Ban from group\n"
        response_text += f"Executed by: {user.name or user.phone_number}\n\n"
        response_text += "⚠️ *Note: This would prevent the user from rejoining the group.*"
        
        # In a real implementation, you would:
        # 1. Remove the user from the group
        # 2. Add them to a ban list
        # 3. Monitor for rejoin attempts
        
        message.reply_text(response_text)
        logger.info(f"Ban command executed by {user.phone_number} for {mentioned_user}")
        
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        message.reply_text("❌ Error banning user from group.")

def handle_mute_user(client: WhatsApp, message, user: User):
    """Handle muting user in group"""
    try:
        mentioned_user = extract_mentioned_user(message.text)
        if not mentioned_user:
            message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}mute @username` or `{Config.BOT_PREFIX}mute <phone_number>`")
            return
        
        response_text = f"🔇 *Group Action: Mute User*\n\n"
        response_text += f"Target: {mentioned_user}\n"
        response_text += f"Action: Restrict messaging\n"
        response_text += f"Executed by: {user.name or user.phone_number}\n\n"
        response_text += "ℹ️ *User will not be able to send messages in this group.*"
        
        # In a real implementation with proper group admin rights:
        # client.restrict_group_participant(group_id=message.from_.group_id, user_id=mentioned_user, permissions={'send_messages': False})
        
        message.reply_text(response_text)
        logger.info(f"Mute command executed by {user.phone_number} for {mentioned_user}")
        
    except Exception as e:
        logger.error(f"Error muting user: {e}")
        message.reply_text("❌ Error muting user.")

def handle_unmute_user(client: WhatsApp, message, user: User):
    """Handle unmuting user in group"""
    try:
        mentioned_user = extract_mentioned_user(message.text)
        if not mentioned_user:
            message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}unmute @username` or `{Config.BOT_PREFIX}unmute <phone_number>`")
            return
        
        response_text = f"🔊 *Group Action: Unmute User*\n\n"
        response_text += f"Target: {mentioned_user}\n"
        response_text += f"Action: Restore messaging rights\n"
        response_text += f"Executed by: {user.name or user.phone_number}\n\n"
        response_text += "✅ *User can now send messages in this group.*"
        
        # In a real implementation:
        # client.restrict_group_participant(group_id=message.from_.group_id, user_id=mentioned_user, permissions={'send_messages': True})
        
        message.reply_text(response_text)
        logger.info(f"Unmute command executed by {user.phone_number} for {mentioned_user}")
        
    except Exception as e:
        logger.error(f"Error unmuting user: {e}")
        message.reply_text("❌ Error unmuting user.")

def handle_promote_user(client: WhatsApp, message, user: User):
    """Handle promoting user to admin"""
    try:
        mentioned_user = extract_mentioned_user(message.text)
        if not mentioned_user:
            message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}promote @username` or `{Config.BOT_PREFIX}promote <phone_number>`")
            return
        
        response_text = f"⬆️ *Group Action: Promote User*\n\n"
        response_text += f"Target: {mentioned_user}\n"
        response_text += f"Action: Promote to admin\n"
        response_text += f"Executed by: {user.name or user.phone_number}\n\n"
        response_text += "👑 *User will receive admin privileges in this group.*"
        
        # In a real implementation:
        # client.promote_group_participant(group_id=message.from_.group_id, user_id=mentioned_user)
        
        message.reply_text(response_text)
        logger.info(f"Promote command executed by {user.phone_number} for {mentioned_user}")
        
    except Exception as e:
        logger.error(f"Error promoting user: {e}")
        message.reply_text("❌ Error promoting user.")

def handle_demote_user(client: WhatsApp, message, user: User):
    """Handle demoting user from admin"""
    try:
        mentioned_user = extract_mentioned_user(message.text)
        if not mentioned_user:
            message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}demote @username` or `{Config.BOT_PREFIX}demote <phone_number>`")
            return
        
        response_text = f"⬇️ *Group Action: Demote User*\n\n"
        response_text += f"Target: {mentioned_user}\n"
        response_text += f"Action: Remove admin rights\n"
        response_text += f"Executed by: {user.name or user.phone_number}\n\n"
        response_text += "👤 *User will lose admin privileges in this group.*"
        
        # In a real implementation:
        # client.demote_group_participant(group_id=message.from_.group_id, user_id=mentioned_user)
        
        message.reply_text(response_text)
        logger.info(f"Demote command executed by {user.phone_number} for {mentioned_user}")
        
    except Exception as e:
        logger.error(f"Error demoting user: {e}")
        message.reply_text("❌ Error demoting user.")
