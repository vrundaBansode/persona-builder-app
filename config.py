import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class to manage environment variables."""
    
    @staticmethod
    def get_api_key(key_name: str) -> str:
        """
        Get an API key from environment variables.
        
        Args:
            key_name (str): Name of the API key to retrieve
            
        Returns:
            str: The API key value
            
        Raises:
            KeyError: If the API key is not found
        """
        api_key = os.getenv(key_name)
        if api_key is None:
            raise KeyError(f"API key '{key_name}' not found in environment variables")
        return api_key
    
    @staticmethod
    def get_config(key_name: str, default=None):
        """
        Get any configuration value from environment variables.
        
        Args:
            key_name (str): Name of the configuration to retrieve
            default: Default value if configuration is not found
            
        Returns:
            The configuration value or default if not found
        """
        return os.getenv(key_name, default)

# Example usage:
# api_key = Config.get_api_key('API_KEY_1')
# debug_mode = Config.get_config('DEBUG', False) 