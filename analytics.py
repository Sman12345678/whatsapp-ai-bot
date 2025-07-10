import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from app import app, db
from models import User, Message, AIRequest, FileProcessing, BotStats, Group

logger = logging.getLogger(__name__)

class Analytics:
    """Analytics service for bot statistics"""
    
    @staticmethod
    def get_total_users() -> int:
        """Get total number of users"""
        try:
            return User.query.count()
        except Exception as e:
            logger.error(f"Error getting total users: {e}")
            return 0
    
    @staticmethod
    def get_total_messages() -> int:
        """Get total number of messages"""
        try:
            return Message.query.count()
        except Exception as e:
            logger.error(f"Error getting total messages: {e}")
            return 0
    
    @staticmethod
    def get_active_users(days: int = 7) -> int:
        """Get number of active users in last N days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return User.query.filter(User.last_seen >= cutoff_date).count()
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return 0
    
    @staticmethod
    def get_commands_used() -> int:
        """Get total number of commands used"""
        try:
            return Message.query.filter(Message.is_command == True).count()
        except Exception as e:
            logger.error(f"Error getting commands used: {e}")
            return 0
    
    @staticmethod
    def get_ai_requests() -> int:
        """Get total number of AI requests"""
        try:
            return AIRequest.query.count()
        except Exception as e:
            logger.error(f"Error getting AI requests: {e}")
            return 0
    
    @staticmethod
    def get_files_processed() -> int:
        """Get total number of files processed"""
        try:
            return FileProcessing.query.count()
        except Exception as e:
            logger.error(f"Error getting files processed: {e}")
            return 0
    
    @staticmethod
    def get_active_groups() -> int:
        """Get number of active groups"""
        try:
            return Group.query.filter(Group.is_active == True).count()
        except Exception as e:
            logger.error(f"Error getting active groups: {e}")
            return 0
    
    @staticmethod
    def get_bot_uptime() -> str:
        """Get bot uptime"""
        try:
            start_time = app.config.get('BOT_START_TIME', datetime.now())
            uptime = datetime.now() - start_time
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            else:
                return f"{minutes}m {seconds}s"
        except Exception as e:
            logger.error(f"Error getting uptime: {e}")
            return "Unknown"
    
    @staticmethod
    def get_popular_commands(limit: int = 10) -> list:
        """Get most popular commands"""
        try:
            result = db.session.query(
                Message.command_name,
                func.count(Message.id).label('count')
            ).filter(
                Message.is_command == True,
                Message.command_name.isnot(None)
            ).group_by(
                Message.command_name
            ).order_by(
                func.count(Message.id).desc()
            ).limit(limit).all()
            
            return [{'command': row.command_name, 'count': row.count} for row in result]
        except Exception as e:
            logger.error(f"Error getting popular commands: {e}")
            return []
    
    @staticmethod
    def get_daily_messages(days: int = 30) -> list:
        """Get daily message counts"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = db.session.query(
                func.date(Message.created_at).label('date'),
                func.count(Message.id).label('count')
            ).filter(
                Message.created_at >= cutoff_date
            ).group_by(
                func.date(Message.created_at)
            ).order_by(
                func.date(Message.created_at)
            ).all()
            
            return [{'date': row.date.isoformat(), 'count': row.count} for row in result]
        except Exception as e:
            logger.error(f"Error getting daily messages: {e}")
            return []
    
    @staticmethod
    def get_user_stats() -> dict:
        """Get user statistics"""
        try:
            total_users = Analytics.get_total_users()
            active_users = Analytics.get_active_users(7)
            admin_users = User.query.filter(User.is_admin == True).count()
            banned_users = User.query.filter(User.is_banned == True).count()
            
            return {
                'total': total_users,
                'active_7d': active_users,
                'admins': admin_users,
                'banned': banned_users
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'total': 0, 'active_7d': 0, 'admins': 0, 'banned': 0}
    
    @staticmethod
    def get_message_type_stats() -> dict:
        """Get message type statistics"""
        try:
            result = db.session.query(
                Message.message_type,
                func.count(Message.id).label('count')
            ).group_by(
                Message.message_type
            ).all()
            
            return {row.message_type: row.count for row in result}
        except Exception as e:
            logger.error(f"Error getting message type stats: {e}")
            return {}
    
    @staticmethod
    def record_daily_stats():
        """Record daily statistics"""
        try:
            today = datetime.utcnow().date()
            
            # Check if stats for today already exist
            existing = BotStats.query.filter_by(date=today).first()
            if existing:
                return
            
            # Record daily stats
            stats = [
                BotStats(metric_name='total_users', metric_value=Analytics.get_total_users(), date=today),
                BotStats(metric_name='total_messages', metric_value=Analytics.get_total_messages(), date=today),
                BotStats(metric_name='ai_requests', metric_value=Analytics.get_ai_requests(), date=today),
                BotStats(metric_name='files_processed', metric_value=Analytics.get_files_processed(), date=today),
                BotStats(metric_name='active_groups', metric_value=Analytics.get_active_groups(), date=today),
            ]
            
            for stat in stats:
                db.session.add(stat)
            
            db.session.commit()
            logger.info(f"Daily stats recorded for {today}")
            
        except Exception as e:
            logger.error(f"Error recording daily stats: {e}")
            db.session.rollback()

def get_dashboard_stats() -> dict:
    """Get comprehensive dashboard statistics"""
    try:
        stats = {
            'total_users': Analytics.get_total_users(),
            'total_messages': Analytics.get_total_messages(),
            'uptime': Analytics.get_bot_uptime(),
            'active_groups': Analytics.get_active_groups(),
            'commands_used': Analytics.get_commands_used(),
            'ai_requests': Analytics.get_ai_requests(),
            'files_processed': Analytics.get_files_processed(),
            'active_users_7d': Analytics.get_active_users(7),
            'popular_commands': Analytics.get_popular_commands(5),
            'daily_messages': Analytics.get_daily_messages(7),
            'user_stats': Analytics.get_user_stats(),
            'message_types': Analytics.get_message_type_stats(),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            'total_users': 0,
            'total_messages': 0,
            'uptime': '0:00:00',
            'active_groups': 0,
            'commands_used': 0,
            'ai_requests': 0,
            'files_processed': 0,
            'active_users_7d': 0,
            'popular_commands': [],
            'daily_messages': [],
            'user_stats': {'total': 0, 'active_7d': 0, 'admins': 0, 'banned': 0},
            'message_types': {},
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
