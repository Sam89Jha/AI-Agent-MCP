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
                'dax_app_url': 'http://localhost:3000',  # Fixed port
                'pax_app_url': 'http://localhost:3001',  # Fixed port
                'api_base_url': 'http://localhost:8000',
                'websocket_url': 'ws://localhost:8000/ws',
                'aws_region': 'us-east-1',
                'use_in_memory_cache': True,
                'debug': True,
                'cors_origins': [
                    'http://localhost:3000',
                    'http://localhost:3001',
                    'http://127.0.0.1:3000',
                    'http://127.0.0.1:3001'
                ],
                'api_gateway_url': 'https://fqzkfukm45.execute-api.us-east-1.amazonaws.com/prod',
                'backend_apis': {
                    'send_message': '/api/v1/send_message',
                    'make_call': '/api/v1/make_call',
                    'get_message': '/api/v1/get_message'
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
                'api_gateway_url': 'https://fqzkfukm45.execute-api.us-east-1.amazonaws.com/prod',
                'backend_apis': {
                    'send_message': '/api/v1/send_message',
                    'make_call': '/api/v1/make_call',
                    'get_message': '/api/v1/get_message'
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
                'api_gateway_url': 'https://fqzkfukm45.execute-api.us-east-1.amazonaws.com/prod',
                'backend_apis': {
                    'send_message': '/api/v1/send_message',
                    'make_call': '/api/v1/make_call',
                    'get_message': '/api/v1/get_message'
                },
                'database': {
                    'type': 'dynamodb',
                    'table_name': 'chat-messages-prod'
                }
            }
        }
        
        # Get current environment config
        self.current_config = self.configs.get(self.environment, self.configs[Environment.LOCAL.value])
        # Override with environment variables if present (for Beanstalk)
        self._override_with_env()
    
    def _override_with_env(self):
        # Allow override of key URLs and region from environment variables
        if os.getenv('API_GATEWAY_URL'):
            self.current_config['api_gateway_url'] = os.getenv('API_GATEWAY_URL')
        if os.getenv('WEBSOCKET_URL'):
            self.current_config['websocket_url'] = os.getenv('WEBSOCKET_URL')
        if os.getenv('AWS_REGION'):
            self.current_config['aws_region'] = os.getenv('AWS_REGION')
        # Optionally override backend_apis endpoints
        for api in ['send_message', 'make_call', 'get_message']:
            env_var = os.getenv(f'BACKEND_API_{api.upper()}')
            if env_var:
                self.current_config['backend_apis'][api] = env_var
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.current_config.get(key, default)
    
    def get_api_url(self, endpoint: str = '') -> str:
        """Get full API URL for an endpoint."""
        base_url = self.get('api_base_url')
        return f"{base_url}{endpoint}"
    
    def get_api_gateway_url(self, api_name: str = '') -> str:
        """Get API Gateway URL for backend APIs."""
        base_url = self.get('api_gateway_url')
        backend_apis = self.get('backend_apis', {})
        endpoint = backend_apis.get(api_name, '')
        return f"{base_url}{endpoint}"
    
    def get_websocket_url(self) -> str:
        """Get WebSocket URL."""
        return self.get('websocket_url')
    
    def get_cors_origins(self) -> list:
        """Get CORS origins for current environment."""
        return self.get('cors_origins', [])
    
    def get_backend_api_url(self, api_name: str) -> str:
        """Get backend API URL for a specific API."""
        return self.get_api_gateway_url(api_name)
    
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

def get_api_gateway_url(api_name: str = '') -> str:
    """Get API Gateway URL for backend APIs."""
    return config.get_api_gateway_url(api_name)

def get_backend_api_url(api_name: str) -> str:
    """Get backend API URL for a specific API."""
    return config.get_backend_api_url(api_name)

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