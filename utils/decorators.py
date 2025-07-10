import time
import logging
from functools import wraps
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Callable, Dict, Any
from pywa import types
from models import User
from config import Config

logger = logging.getLogger(__name__)

# Rate limiting storage (in-memory for MVP)
rate_limit_storage: Dict[str, deque] = defaultdict(deque)

def rate_limit(max_requests: int = None, window_seconds: int = 60):
    """
    Rate limiting decorator for WhatsApp bot functions
    
    Args:
        max_requests: Maximum requests allowed in the time window
        window_seconds: Time window in seconds
    """
    if max_requests is None:
        max_requests = Config.MAX_REQUESTS_PER_MINUTE
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user identifier from message
            user_id = None
            for arg in args:
                if isinstance(arg, types.Message):
                    user_id = arg.from_user.wa_id
                    break
                elif isinstance(arg, types.CallbackButton):
                    user_id = arg.from_user.wa_id
                    break
            
            if not user_id:
                # If we can't identify the user, allow the request
                return func(*args, **kwargs)
            
            # Check rate limit
            now = datetime.now()
            cutoff_time = now - timedelta(seconds=window_seconds)
            
            # Clean old requests
            user_requests = rate_limit_storage[user_id]
            while user_requests and user_requests[0] < cutoff_time:
                user_requests.popleft()
            
            # Check if limit exceeded
            if len(user_requests) >= max_requests:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                
                # Send rate limit message
                for arg in args:
                    if hasattr(arg, 'reply_text'):
                        arg.reply_text(
                            f"⏰ Rate limit exceeded! Please wait {window_seconds} seconds before trying again."
                        )
                        break
                return None
            
            # Record this request
            user_requests.append(now)
            
            # Execute the function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def admin_required(func: Callable) -> Callable:
    """
    Decorator to ensure only admin users can execute the function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract user from arguments
        user = None
        message = None
        
        for arg in args:
            if isinstance(arg, User):
                user = arg
            elif isinstance(arg, (types.Message, types.CallbackButton)):
                message = arg
                # Get user from database
                from bot import get_or_create_user
                user = get_or_create_user(
                    arg.from_user.wa_id, 
                    arg.from_user.name
                )
            
            if user and message:
                break
        
        if not user:
            logger.error("Could not determine user for admin check")
            return None
        
        if not user.is_admin:
            logger.warning(f"Non-admin user {user.phone_number} attempted admin action")
            
            if message and hasattr(message, 'reply_text'):
                message.reply_text(
                    "❌ Access denied. Admin privileges required.\n\n"
                    "Contact the bot administrator if you believe this is an error."
                )
            return None
        
        return func(*args, **kwargs)
    
    return wrapper

def log_performance(include_args: bool = False):
    """
    Decorator to log function performance metrics
    
    Args:
        include_args: Whether to include function arguments in logs
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = func.__name__
            
            try:
                # Log function start
                if include_args:
                    logger.debug(f"Starting {function_name} with args: {args[:2]}...")  # Limit args logging
                else:
                    logger.debug(f"Starting {function_name}")
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Log successful completion
                execution_time = time.time() - start_time
                logger.info(f"Completed {function_name} in {execution_time:.3f}s")
                
                return result
                
            except Exception as e:
                # Log error with execution time
                execution_time = time.time() - start_time
                logger.error(f"Error in {function_name} after {execution_time:.3f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator

def retry(max_attempts: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator to retry function execution on failure
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each failed attempt
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    logger.warning(f"Attempt {attempt + 1} of {func.__name__} failed: {str(e)}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator

def validate_input(validation_rules: Dict[str, Any]):
    """
    Decorator to validate function input parameters
    
    Args:
        validation_rules: Dictionary of parameter validation rules
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function parameter names
            import inspect
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            
            # Combine args and kwargs into a single dict
            all_params = {}
            for i, arg in enumerate(args):
                if i < len(param_names):
                    all_params[param_names[i]] = arg
            all_params.update(kwargs)
            
            # Validate each parameter
            for param_name, rules in validation_rules.items():
                if param_name not in all_params:
                    continue
                
                value = all_params[param_name]
                
                # Check required
                if rules.get('required') and value is None:
                    raise ValueError(f"Parameter '{param_name}' is required")
                
                # Check type
                if 'type' in rules and value is not None:
                    expected_type = rules['type']
                    if not isinstance(value, expected_type):
                        raise TypeError(f"Parameter '{param_name}' must be of type {expected_type.__name__}")
                
                # Check min/max length for strings
                if isinstance(value, str) and value:
                    if 'min_length' in rules and len(value) < rules['min_length']:
                        raise ValueError(f"Parameter '{param_name}' must be at least {rules['min_length']} characters")
                    if 'max_length' in rules and len(value) > rules['max_length']:
                        raise ValueError(f"Parameter '{param_name}' must be at most {rules['max_length']} characters")
                
                # Check custom validator
                if 'validator' in rules and value is not None:
                    validator = rules['validator']
                    if not validator(value):
                        error_msg = rules.get('error_message', f"Invalid value for parameter '{param_name}'")
                        raise ValueError(error_msg)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def cache_result(ttl_seconds: int = 300):
    """
    Simple in-memory cache decorator with TTL
    
    Args:
        ttl_seconds: Time to live for cached results in seconds
    """
    cache = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Check if we have a valid cached result
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
                else:
                    # Cache expired, remove it
                    del cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator

def sanitize_output(func: Callable) -> Callable:
    """
    Decorator to sanitize function output for WhatsApp messages
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        if isinstance(result, str):
            # Remove or escape potentially problematic characters
            result = result.replace('\r\n', '\n')  # Normalize line endings
            result = result.replace('\r', '\n')    # Normalize line endings
            
            # Limit message length for WhatsApp
            if len(result) > 4096:
                result = result[:4090] + "..."
                logger.warning(f"Message truncated in {func.__name__} - original length: {len(result)}")
        
        return result
    
    return wrapper

def handle_exceptions(default_response: str = "❌ An error occurred. Please try again."):
    """
    Decorator to handle exceptions gracefully and provide user-friendly error messages
    
    Args:
        default_response: Default error message to send to user
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {str(e)}", exc_info=True)
                
                # Try to send error message to user
                for arg in args:
                    if hasattr(arg, 'reply_text'):
                        try:
                            arg.reply_text(default_response)
                        except Exception as reply_error:
                            logger.error(f"Failed to send error message: {str(reply_error)}")
                        break
                
                # Re-raise exception for logging purposes
                raise
        
        return wrapper
    return decorator
