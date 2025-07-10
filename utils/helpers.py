import re
import os
import uuid
import mimetypes
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

def format_phone_number(phone: str) -> str:
    """
    Format phone number to WhatsApp standard format
    
    Args:
        phone: Raw phone number string
        
    Returns:
        Formatted phone number
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits_only = re.sub(r'[^\d]', '', phone)
    
    # Add country code if missing (assuming +1 for US/Canada)
    if len(digits_only) == 10:
        digits_only = "1" + digits_only
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        pass  # Already has country code
    
    return digits_only

def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'[^\d]', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(digits_only) <= 15

def clean_filename(filename: str) -> str:
    """
    Clean filename to remove potentially dangerous characters
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    if not filename:
        return "unknown_file"
    
    # Remove or replace dangerous characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    cleaned = cleaned.strip('. ')
    
    # Ensure filename is not empty
    if not cleaned:
        cleaned = "cleaned_file"
    
    # Limit length
    if len(cleaned) > 255:
        name, ext = os.path.splitext(cleaned)
        max_name_length = 255 - len(ext)
        cleaned = name[:max_name_length] + ext
    
    return cleaned

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: File name
        
    Returns:
        File extension (lowercase, without dot)
    """
    if not filename:
        return ""
    
    _, ext = os.path.splitext(filename)
    return ext.lower().lstrip('.')

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input text
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove or escape HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text

def generate_unique_id() -> str:
    """
    Generate a unique identifier
    
    Returns:
        Unique ID string
    """
    return str(uuid.uuid4())

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def get_mime_type(filename: str) -> str:
    """
    Get MIME type for a file
    
    Args:
        filename: File name
        
    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"

def is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime timestamp
    
    Args:
        timestamp: Datetime object
        format_str: Format string
        
    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return ""
    
    return timestamp.strftime(format_str)

def calculate_age(created_at: datetime) -> str:
    """
    Calculate age/time difference from creation date
    
    Args:
        created_at: Creation datetime
        
    Returns:
        Human-readable age string
    """
    if not created_at:
        return "Unknown"
    
    now = datetime.utcnow()
    diff = now - created_at
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def extract_mentions(text: str) -> List[str]:
    """
    Extract user mentions from text
    
    Args:
        text: Text containing mentions
        
    Returns:
        List of mentioned usernames/phone numbers
    """
    if not text:
        return []
    
    # Extract @username patterns
    username_mentions = re.findall(r'@(\w+)', text)
    
    # Extract phone number patterns
    phone_mentions = re.findall(r'\+?[\d\s\-\(\)]{10,}', text)
    
    # Clean phone numbers
    cleaned_phones = [format_phone_number(phone) for phone in phone_mentions]
    
    return username_mentions + [phone for phone in cleaned_phones if validate_phone_number(phone)]

def parse_command_args(text: str, prefix: str = "/") -> Dict[str, Any]:
    """
    Parse command arguments from message text
    
    Args:
        text: Message text
        prefix: Command prefix
        
    Returns:
        Dictionary with command and arguments
    """
    if not text or not text.startswith(prefix):
        return {"command": None, "args": [], "raw_args": ""}
    
    # Remove prefix and split
    command_text = text[len(prefix):].strip()
    parts = command_text.split()
    
    if not parts:
        return {"command": None, "args": [], "raw_args": ""}
    
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    raw_args = " ".join(args)
    
    return {
        "command": command,
        "args": args,
        "raw_args": raw_args
    }

def hash_string(text: str) -> str:
    """
    Create SHA-256 hash of a string
    
    Args:
        text: Text to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def chunk_text(text: str, chunk_size: int = 4000) -> List[str]:
    """
    Split text into chunks for WhatsApp message limits
    
    Args:
        text: Text to split
        chunk_size: Maximum chunk size
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by lines first to maintain formatting
    lines = text.split('\n')
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= chunk_size:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If single line is too long, split it
            if len(line) > chunk_size:
                words = line.split(' ')
                current_chunk = ""
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= chunk_size:
                        if current_chunk:
                            current_chunk += ' ' + word
                        else:
                            current_chunk = word
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = word
            else:
                current_chunk = line
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def is_image_file(filename: str) -> bool:
    """
    Check if filename represents an image file
    
    Args:
        filename: File name to check
        
    Returns:
        True if image file, False otherwise
    """
    image_extensions = {
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tga'
    }
    
    extension = get_file_extension(filename)
    return extension in image_extensions

def is_document_file(filename: str) -> bool:
    """
    Check if filename represents a document file
    
    Args:
        filename: File name to check
        
    Returns:
        True if document file, False otherwise
    """
    document_extensions = {
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'odt'
    }
    
    extension = get_file_extension(filename)
    return extension in document_extensions

def is_code_file(filename: str) -> bool:
    """
    Check if filename represents a code file
    
    Args:
        filename: File name to check
        
    Returns:
        True if code file, False otherwise
    """
    code_extensions = {
        'py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'php', 'rb', 'go', 
        'rs', 'swift', 'kt', 'ts', 'jsx', 'tsx', 'vue', 'xml', 'json', 
        'yaml', 'yml', 'sql', 'sh', 'bat', 'ps1'
    }
    
    extension = get_file_extension(filename)
    return extension in code_extensions

def get_file_category(filename: str) -> str:
    """
    Categorize file based on extension
    
    Args:
        filename: File name
        
    Returns:
        File category string
    """
    if is_image_file(filename):
        return "image"
    elif is_document_file(filename):
        return "document"
    elif is_code_file(filename):
        return "code"
    else:
        return "other"

def create_progress_bar(current: int, total: int, width: int = 20) -> str:
    """
    Create a text-based progress bar
    
    Args:
        current: Current progress value
        total: Total value
        width: Width of progress bar in characters
        
    Returns:
        Progress bar string
    """
    if total == 0:
        return "█" * width
    
    progress = current / total
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    percentage = int(progress * 100)
    
    return f"{bar} {percentage}%"

def escape_markdown(text: str) -> str:
    """
    Escape markdown special characters
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    if not text:
        return ""
    
    # Escape common markdown characters
    escape_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def format_whatsapp_message(text: str, bold: bool = False, italic: bool = False, monospace: bool = False) -> str:
    """
    Format text for WhatsApp with styling
    
    Args:
        text: Text to format
        bold: Apply bold formatting
        italic: Apply italic formatting
        monospace: Apply monospace formatting
        
    Returns:
        Formatted text
    """
    if not text:
        return ""
    
    if monospace:
        return f"```{text}```"
    
    if bold:
        text = f"*{text}*"
    
    if italic:
        text = f"_{text}_"
    
    return text
