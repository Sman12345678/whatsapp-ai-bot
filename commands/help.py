import logging
import os
import importlib
from pywa import WhatsApp, types
from models import User
from config import Config

logger = logging.getLogger(__name__)

def get_command_list():
    # Scan the commands directory for files that start with handle_ and end with _command.py
    commands_dir = os.path.dirname(__file__)
    commands = []
    for fname in os.listdir(commands_dir):
        if fname.startswith("handle_") and fname.endswith("_command.py"):
            command_name = fname[len("handle_"):-len("_command.py")]
            commands.append(command_name)
        elif fname.endswith(".py") and fname not in ("__init__.py", "base.py", "help.py"):
            command_name = fname[:-3]
            commands.append(command_name)
    # Remove duplicates and sort
    commands = sorted(set(commands))
    return commands

def handle_help_command(client: WhatsApp, message, user: User):
    """Handle help command with dynamic command listing and better visuals"""
    try:
        help_text = f"🤖 *{Config.BOT_NAME} - Help*\n\n"
        help_text += "📚 *Available Commands:*\n\n"

        commands = get_command_list()
        for cmd in commands:
            emoji = "🄾"
            help_text += f"{emoji} *{Config.BOT_PREFIX}{cmd}* – Useful command\n"

        # Add extra instructions or tips
        help_text += "\n💡 *Tips:*\n"
        help_text += "🟢 *Just send me a message to start chatting!*\n"
        help_text += "🟣 *I can analyze images and extract text.*\n"
        help_text += "🟠 *Send me documents for detailed analysis.*\n"
        help_text += "🟤 *Use reactions to interact with my messages.*\n"

        # Buttons for quick actions
        buttons = [
            types.Button(title="🏠 Start", callback_data="start"),
            types.Button(title="🄾 Info", callback_data="info")
        ]
        if user.is_admin:
            buttons.append(types.Button(title="👑 Admin", callback_data="admin_panel"))

        if hasattr(message, 'reply_text'):
            message.reply_text(text=help_text, buttons=buttons)
        else:
            message.reply_text(text=help_text, buttons=buttons)

        logger.info(f"Help command executed for user {user.phone_number}")

    except Exception as e:
        logger.error(f"Error in help command: {e}")
        if hasattr(message, 'reply_text'):
            message.reply_text("❌ Error showing help. Please try again.")
        else:
            message.reply_text("❌ Error showing help. Please try again.")
