"""
Utilities for handling environment variables.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_env_value(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable.
    
    Args:
        name: The name of the environment variable
        default: The default value to return if the variable is not set
        
    Returns:
        Optional[str]: The value of the environment variable, or the default value
    """
    return os.environ.get(name, default) 