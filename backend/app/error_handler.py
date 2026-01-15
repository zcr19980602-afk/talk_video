"""Error handling and retry logic."""

import logging
import asyncio
from typing import TypeVar, Callable, Any, Optional
from functools import wraps
from .models import ErrorType, ErrorMessage
from .config import retry_config

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorHandler:
    """Handles errors and implements retry logic."""
    
    @staticmethod
    def create_error_message(
        error_type: ErrorType,
        error: Exception
    ) -> ErrorMessage:
        """
        Create error message from exception.
        
        Args:
            error_type: Type of error
            error: Exception object
            
        Returns:
            ErrorMessage object
        """
        return ErrorMessage.from_error_type(
            error_type,
            details=str(error)
        )
    
    @staticmethod
    def log_error(
        error_type: ErrorType,
        error: Exception,
        context: Optional[dict] = None
    ) -> None:
        """
        Log error with context.
        
        Args:
            error_type: Type of error
            error: Exception object
            context: Additional context
        """
        context_str = f" | Context: {context}" if context else ""
        logger.error(
            f"Error [{error_type.value}]: {str(error)}{context_str}",
            exc_info=True
        )
    
    @staticmethod
    async def retry_async(
        func: Callable[..., Any],
        *args: Any,
        max_retries: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """
        Retry async function with exponential backoff.
        
        Args:
            func: Async function to retry
            *args: Function arguments
            max_retries: Maximum number of retries
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        max_retries = max_retries or retry_config.max_retries
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = retry_config.get_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {max_retries + 1} attempts failed. Last error: {e}"
                    )
        
        raise last_exception
    
    @staticmethod
    def with_error_handling(error_type: ErrorType):
        """
        Decorator for adding error handling to functions.
        
        Args:
            error_type: Type of error to handle
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    ErrorHandler.log_error(error_type, e)
                    raise
            return wrapper
        return decorator
    
    @staticmethod
    def mask_sensitive_data(data: str, show_chars: int = 8) -> str:
        """
        Mask sensitive data for logging.
        
        Args:
            data: Sensitive string
            show_chars: Number of characters to show at start
            
        Returns:
            Masked string
        """
        if len(data) <= show_chars:
            return "***"
        return f"{data[:show_chars]}...***"


def handle_api_error(error: Exception) -> ErrorType:
    """
    Determine error type from exception.
    
    Args:
        error: Exception object
        
    Returns:
        ErrorType enum value
    """
    error_str = str(error).lower()
    
    if "network" in error_str or "connection" in error_str:
        return ErrorType.NETWORK_ERROR
    elif "401" in error_str or "403" in error_str or "unauthorized" in error_str:
        return ErrorType.PERMISSION_DENIED
    elif "404" in error_str:
        return ErrorType.DEVICE_NOT_FOUND
    elif "timeout" in error_str:
        return ErrorType.NETWORK_ERROR
    else:
        return ErrorType.UNKNOWN_ERROR


async def safe_api_call(
    func: Callable[..., Any],
    error_type: ErrorType,
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Safely call API function with error handling and retry.
    
    Args:
        func: API function to call
        error_type: Type of error for this API
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        Exception with error handling
    """
    try:
        return await ErrorHandler.retry_async(func, *args, **kwargs)
    except Exception as e:
        ErrorHandler.log_error(error_type, e)
        raise
