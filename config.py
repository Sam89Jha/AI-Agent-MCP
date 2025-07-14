"""
Configuration system for NavieTakieSimulation project.
Supports local, staging, and production environments.
"""

import os
from typing import Dict, Any, Optional
from enum import Enum

class Environment(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"

class Config:
    """Configuration class with environment-specific settings."""
    
    def __init__(self, environment: Optional[str] = None):
        env = environment or os.getenv('ENVIRONMENT')
        self.environment = env if env else 'local'
        
        # Environment-specific configurations
        self.configs = {
            Environment.LOCAL.value: {
                'mcp_server_url': 'http://localhost:8000',
                'dax_app_url': 'http://localhost:3001',
                'pax_app_url': 'http://localhost:3002',
                'api_base_url': 'http://localhost:8000',
                'websocket_url': 'ws://localhost:8000/ws',
                'aws_region': 'us-east-1',
                'use_in_memory_cache': True,
                'debug': True,
                'cors_origins': [
                    'http://localhost:3000',
                    'http://localhost:3001',
                    'http://localhost:3002',
                    'http://127.0.0.1:3000',
                    'http://127.0.0.1:3001',
                    'http://127.0.0.1:3002'
                ],
                'lambda_functions': {
                    'send_message': 'send-message-local',
                    'make_call': 'make-call-local',
                    'get_message': 'get-message-local'
                },
                'database': {
                    'type': 'in_memory',
                    'table_name': 'chat-messages-local'
                }
            },
            
            Environment.STAGING.value: {
                'mcp_server_url': 'https://mcp-staging.sameer-jha.com',
                'dax_app_url': 'https://dax-staging.sameer-jha.com',
                'pax_app_url': 'https://pax-staging.sameer-jha.com',
                'api_base_url': 'https://mcp-staging.sameer-jha.com',
                'websocket_url': 'wss://mcp-staging.sameer-jha.com/ws',
                'aws_region': 'us-east-1',
                'use_in_memory_cache': False,
                'debug': True,
                'cors_origins': [
                    'https://dax-staging.sameer-jha.com',
                    'https://pax-staging.sameer-jha.com'
                ],
                'lambda_functions': {
                    'send_message': 'send-message-staging',
                    'make_call': 'make-call-staging',
                    'get_message': 'get-message-staging'
                },
                'database': {
                    'type': 'dynamodb',
                    'table_name': 'chat-messages-staging'
                }
            },
            
            Environment.PRODUCTION.value: {
                'mcp_server_url': 'https://mcp.sameer-jha.com',
                'dax_app_url': 'https://dax.sameer-jha.com',
                'pax_app_url': 'https://pax.sameer-jha.com',
                'api_base_url': 'https://mcp.sameer-jha.com',
                'websocket_url': 'wss://mcp.sameer-jha.com/ws',
                'aws_region': 'us-east-1',
                'use_in_memory_cache': False,
                'debug': False,
                'cors_origins': [
                    'https://dax.sameer-jha.com',
                    'https://pax.sameer-jha.com'
                ],
                'lambda_functions': {
                    'send_message': 'send-message-prod',
                    'make_call': 'make-call-prod',
                    'get_message': 'get-message-prod'
                },
                'database': {
                    'type': 'dynamodb',
                    'table_name': 'chat-messages-prod'
                }
            }
        }
        
        # Get current environment config
        self.current_config = self.configs.get(self.environment, self.configs[Environment.LOCAL.value])
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.current_config.get(key, default)
    
    def get_api_url(self, endpoint: str = '') -> str:
        """Get full API URL for an endpoint."""
        base_url = self.get('api_base_url')
        return f"{base_url}{endpoint}"
    
    def get_websocket_url(self) -> str:
        """Get WebSocket URL."""
        return self.get('websocket_url')
    
    def get_cors_origins(self) -> list:
        """Get CORS origins for current environment."""
        return self.get('cors_origins', [])
    
    def get_lambda_function_name(self, function_type: str) -> str:
        """Get Lambda function name for current environment."""
        lambda_functions = self.get('lambda_functions', {})
        return lambda_functions.get(function_type, f"{function_type}-{self.environment}")
    
    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.environment == Environment.LOCAL.value
    
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == Environment.STAGING.value
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION.value
    
    def use_in_memory_cache(self) -> bool:
        """Check if should use in-memory cache."""
        return self.get('use_in_memory_cache', False)
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get('debug', False)
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.get('database', {})
    
    def print_config(self):
        """Print current configuration."""
        print(f"🔧 Configuration for environment: {self.environment}")
        print("=" * 50)
        for key, value in self.current_config.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")

# Global config instance
config = Config()

# Convenience functions
def get_config() -> Config:
    """Get global config instance."""
    return config

def get_api_url(endpoint: str = '') -> str:
    """Get API URL for endpoint."""
    return config.get_api_url(endpoint)

def get_websocket_url() -> str:
    """Get WebSocket URL."""
    return config.get_websocket_url()

def get_cors_origins() -> list:
    """Get CORS origins."""
    return config.get_cors_origins()

def is_local() -> bool:
    """Check if local environment."""
    return config.is_local()

def is_staging() -> bool:
    """Check if staging environment."""
    return config.is_staging()

def is_production() -> bool:
    """Check if production environment."""
    return config.is_production()

def use_in_memory_cache() -> bool:
    """Check if should use in-memory cache."""
    return config.use_in_memory_cache()

if __name__ == "__main__":
    # Test configuration
    config.print_config() 