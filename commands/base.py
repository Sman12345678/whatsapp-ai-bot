from abc import ABC, abstractmethod
from pywa import WhatsApp, types
from models import User

class Command(ABC):
    """Base class for bot commands"""
    
    def __init__(self, name: str, description: str, admin_only: bool = False):
        self.name = name
        self.description = description
        self.admin_only = admin_only
    
    @abstractmethod
    def execute(self, client: WhatsApp, message: types.Message, user: User, args: list):
        """Execute the command"""
        pass
    
    def can_execute(self, user: User) -> bool:
        """Check if user can execute this command"""
        if self.admin_only and not user.is_admin:
            return False
        if user.is_banned:
            return False
        return True
    
    def get_usage(self) -> str:
        """Get command usage string"""
        return f"/{self.name}"
    
    def get_help_text(self) -> str:
        """Get help text for the command"""
        admin_text = " (Admin only)" if self.admin_only else ""
        return f"`{self.get_usage()}` - {self.description}{admin_text}"
