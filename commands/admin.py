import logging
from pywa import WhatsApp, types
from models import User, Message, AIRequest, FileProcessing
from config import Config
from app import db
from analytics import Analytics
from datetime import datetime

logger = logging.getLogger(__name__)

def handle_admin_commands(client: WhatsApp, message, user: User, command: str):
    """Handle admin commands"""
    try:
        if not user.is_admin:
            if hasattr(message, 'reply_text'):
                message.reply_text("❌ Access denied. Admin privileges required.")
            else:
                message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        if command == "admin":
            show_admin_panel(client, message, user)
        elif command == "broadcast":
            handle_broadcast(client, message, user)
        elif command == "ban":
            handle_ban_user(client, message, user)
        elif command == "unban":
            handle_unban_user(client, message, user)
        elif command == "stats":
            show_bot_stats(client, message, user)
        else:
            if hasattr(message, 'reply_text'):
                message.reply_text(f"❓ Unknown admin command: {command}")
            else:
                message.reply_text(f"❓ Unknown admin command: {command}")
                
    except Exception as e:
        logger.error(f"Error in admin command {command}: {e}")
        if hasattr(message, 'reply_text'):
            message.reply_text("❌ Error executing admin command.")
        else:
            message.reply_text("❌ Error executing admin command.")

def show_admin_panel(client: WhatsApp, message, user: User):
    """Show admin control panel"""
    try:
        panel_text = f"👑 *{Config.BOT_NAME} - Admin Panel*\n\n"
        
        # Quick stats
        total_users = Analytics.get_total_users()
        total_messages = Analytics.get_total_messages()
        active_users = Analytics.get_active_users(24)  # Last 24 hours
        ai_requests = Analytics.get_ai_requests()
        
        panel_text += "📊 *Quick Stats:*\n"
        panel_text += f"• Total Users: {total_users}\n"
        panel_text += f"• Total Messages: {total_messages}\n"
        panel_text += f"• Active Users (24h): {active_users}\n"
        panel_text += f"• AI Requests: {ai_requests}\n"
        panel_text += f"• Bot Uptime: {Analytics.get_bot_uptime()}\n\n"
        
        panel_text += "🛠️ *Available Actions:*\n"
        panel_text += f"`{Config.BOT_PREFIX}stats` - Detailed statistics\n"
        panel_text += f"`{Config.BOT_PREFIX}broadcast <msg>` - Send to all users\n"
        panel_text += f"`{Config.BOT_PREFIX}ban <phone>` - Ban user\n"
        panel_text += f"`{Config.BOT_PREFIX}unban <phone>` - Unban user\n\n"
        
        panel_text += "🔗 *Quick Links:*\n"
        panel_text += "• Visit dashboard for detailed analytics\n"
        panel_text += f"• Webhook URL: {Config.WEBHOOK_URL}/webhook\n"
        
        buttons = [
            types.Button(title="📊 Full Stats", callback_data="admin_stats"),
            types.Button(title="👥 Users", callback_data="admin_users"),
            types.Button(title="🔧 Settings", callback_data="admin_settings")
        ]
        
        if hasattr(message, 'reply_text'):
            message.reply_text(text=panel_text, buttons=buttons)
        else:
            message.reply_text(text=panel_text, buttons=buttons)
            
        logger.info(f"Admin panel shown to user {user.phone_number}")
        
    except Exception as e:
        logger.error(f"Error showing admin panel: {e}")
        if hasattr(message, 'reply_text'):
            message.reply_text("❌ Error loading admin panel.")
        else:
            message.reply_text("❌ Error loading admin panel.")

def handle_broadcast(client: WhatsApp, message, user: User):
    """Handle broadcast message to all users"""
    try:
        # Extract message text
        if hasattr(message, 'text'):
            text_parts = message.text.split(' ', 1)
            if len(text_parts) < 2:
                message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}broadcast <message>`")
                return
            
            broadcast_message = text_parts[1]
        else:
            message.reply_text("❌ No message content provided for broadcast.")
            return
        
        # Get all active users
        users = User.query.filter(User.is_banned == False).all()
        
        if not users:
            message.reply_text("❌ No active users found.")
            return
        
        # Send broadcast
        sent_count = 0
        failed_count = 0
        
        broadcast_text = f"📢 *Broadcast Message*\n\n{broadcast_message}\n\n"
        broadcast_text += f"_Sent by admin at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        for target_user in users:
            if target_user.phone_number == user.phone_number:
                continue  # Skip sender
                
            try:
                client.send_message(
                    to=target_user.phone_number,
                    text=broadcast_text
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to {target_user.phone_number}: {e}")
                failed_count += 1
        
        result_text = f"📢 *Broadcast Complete*\n\n"
        result_text += f"✅ Sent to: {sent_count} users\n"
        if failed_count > 0:
            result_text += f"❌ Failed: {failed_count} users\n"
        result_text += f"\nMessage: _{broadcast_message}_"
        
        message.reply_text(result_text)
        logger.info(f"Broadcast sent by {user.phone_number}: {sent_count} sent, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Error in broadcast: {e}")
        message.reply_text("❌ Error sending broadcast message.")

def handle_ban_user(client: WhatsApp, message, user: User):
    """Handle banning a user"""
    try:
        if hasattr(message, 'text'):
            text_parts = message.text.split(' ', 1)
            if len(text_parts) < 2:
                message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}ban <phone_number>`")
                return
            
            target_phone = text_parts[1].strip()
        else:
            message.reply_text("❌ No phone number provided.")
            return
        
        # Find target user
        target_user = User.query.filter_by(phone_number=target_phone).first()
        if not target_user:
            message.reply_text(f"❌ User {target_phone} not found.")
            return
        
        if target_user.is_admin:
            message.reply_text("❌ Cannot ban an admin user.")
            return
        
        if target_user.is_banned:
            message.reply_text(f"⚠️ User {target_phone} is already banned.")
            return
        
        # Ban the user
        target_user.is_banned = True
        db.session.commit()
        
        # Notify the banned user
        try:
            client.send_message(
                to=target_phone,
                text="🚫 You have been banned from using this bot. If you believe this is a mistake, please contact support."
            )
        except Exception as e:
            logger.warning(f"Could not notify banned user {target_phone}: {e}")
        
        message.reply_text(f"✅ User {target_phone} has been banned.")
        logger.info(f"User {target_phone} banned by admin {user.phone_number}")
        
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        message.reply_text("❌ Error banning user.")

def handle_unban_user(client: WhatsApp, message, user: User):
    """Handle unbanning a user"""
    try:
        if hasattr(message, 'text'):
            text_parts = message.text.split(' ', 1)
            if len(text_parts) < 2:
                message.reply_text(f"❌ Usage: `{Config.BOT_PREFIX}unban <phone_number>`")
                return
            
            target_phone = text_parts[1].strip()
        else:
            message.reply_text("❌ No phone number provided.")
            return
        
        # Find target user
        target_user = User.query.filter_by(phone_number=target_phone).first()
        if not target_user:
            message.reply_text(f"❌ User {target_phone} not found.")
            return
        
        if not target_user.is_banned:
            message.reply_text(f"⚠️ User {target_phone} is not banned.")
            return
        
        # Unban the user
        target_user.is_banned = False
        db.session.commit()
        
        # Notify the unbanned user
        try:
            client.send_message(
                to=target_phone,
                text="🎉 You have been unbanned! Welcome back to the bot."
            )
        except Exception as e:
            logger.warning(f"Could not notify unbanned user {target_phone}: {e}")
        
        message.reply_text(f"✅ User {target_phone} has been unbanned.")
        logger.info(f"User {target_phone} unbanned by admin {user.phone_number}")
        
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        message.reply_text("❌ Error unbanning user.")

def show_bot_stats(client: WhatsApp, message, user: User):
    """Show detailed bot statistics"""
    try:
        stats_text = f"📊 *{Config.BOT_NAME} - Statistics*\n\n"
        
        # User statistics
        user_stats = Analytics.get_user_stats()
        stats_text += "👥 *User Statistics:*\n"
        stats_text += f"• Total Users: {user_stats['total']}\n"
        stats_text += f"• Active (7 days): {user_stats['active_7d']}\n"
        stats_text += f"• Admins: {user_stats['admins']}\n"
        stats_text += f"• Banned: {user_stats['banned']}\n\n"
        
        # Message statistics
        total_messages = Analytics.get_total_messages()
        commands_used = Analytics.get_commands_used()
        ai_requests = Analytics.get_ai_requests()
        files_processed = Analytics.get_files_processed()
        
        stats_text += "💬 *Message Statistics:*\n"
        stats_text += f"• Total Messages: {total_messages}\n"
        stats_text += f"• Commands Used: {commands_used}\n"
        stats_text += f"• AI Requests: {ai_requests}\n"
        stats_text += f"• Files Processed: {files_processed}\n\n"
        
        # Popular commands
        popular_commands = Analytics.get_popular_commands(5)
        if popular_commands:
            stats_text += "🔥 *Popular Commands:*\n"
            for cmd in popular_commands:
                stats_text += f"• /{cmd['command']}: {cmd['count']} uses\n"
            stats_text += "\n"
        
        # System info
        stats_text += "⚙️ *System Information:*\n"
        stats_text += f"• Bot Uptime: {Analytics.get_bot_uptime()}\n"
        stats_text += f"• Active Groups: {Analytics.get_active_groups()}\n"
        stats_text += f"• Bot Prefix: {Config.BOT_PREFIX}\n"
        stats_text += f"• Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        buttons = [
            types.Button(title="🔄 Refresh", callback_data="admin_stats"),
            types.Button(title="📈 Dashboard", callback_data="admin_dashboard")
        ]
        
        if hasattr(message, 'reply_text'):
            message.reply_text(text=stats_text, buttons=buttons)
        else:
            message.reply_text(text=stats_text, buttons=buttons)
            
        logger.info(f"Bot stats shown to admin {user.phone_number}")
        
    except Exception as e:
        logger.error(f"Error showing bot stats: {e}")
        if hasattr(message, 'reply_text'):
            message.reply_text("❌ Error loading statistics.")
        else:
            message.reply_text("❌ Error loading statistics.")
