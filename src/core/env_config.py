"""
Environment-based configuration loader for secure credential management.
This module provides secure loading of configuration from environment variables
and .env files, with fallback to example templates.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class EnvironmentConfig:
    """Environment-based configuration for Firebase and Google services"""
    
    # Firebase Configuration
    firebase_api_key: str = ""
    firebase_project_id: str = ""
    firebase_auth_domain: str = ""
    firebase_database_url: str = ""
    firebase_storage_bucket: str = ""
    firebase_messaging_sender_id: str = ""
    firebase_app_id: str = ""
    firebase_service_account: str = ""
    
    # Google OAuth Configuration
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_project_id: str = ""
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    backend_type: str = "direct_firebase"
    port: int = 5000
    remember_session: bool = True
    session_timeout: int = 3600
    
    def is_firebase_configured(self) -> bool:
        """Check if Firebase is properly configured"""
        return bool(
            self.firebase_api_key and 
            self.firebase_project_id and 
            self.firebase_auth_domain
        )
    
    def is_google_oauth_configured(self) -> bool:
        """Check if Google OAuth is properly configured"""
        return bool(
            self.google_oauth_client_id and 
            self.google_oauth_client_secret
        )
    
    def to_firebase_config(self) -> Dict[str, Any]:
        """Convert to Firebase web config format"""
        return {
            "apiKey": self.firebase_api_key,
            "authDomain": self.firebase_auth_domain,
            "databaseURL": self.firebase_database_url,
            "projectId": self.firebase_project_id,
            "storageBucket": self.firebase_storage_bucket,
            "messagingSenderId": self.firebase_messaging_sender_id,
            "appId": self.firebase_app_id
        }
    
    def to_google_oauth_config(self) -> Dict[str, Any]:
        """Convert to Google OAuth credentials format"""
        return {
            "installed": {
                "client_id": self.google_oauth_client_id,
                "project_id": self.google_oauth_project_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": self.google_oauth_client_secret,
                "redirect_uris": ["http://localhost:8080", "http://localhost"]
            }
        }


class EnvironmentConfigLoader:
    """Secure configuration loader that prioritizes environment variables"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.project_root = project_root or Path.cwd()
        self.config = EnvironmentConfig()
        self._load_dotenv()
        self._load_from_environment()
    
    def _load_dotenv(self):
        """Load environment variables from .env file if it exists"""
        env_file = self.project_root / ".env"
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
                self.logger.info("Loaded environment variables from .env file")
            except Exception as e:
                self.logger.warning(f"Failed to load .env file: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Firebase Configuration
        self.config.firebase_api_key = os.getenv('FIREBASE_API_KEY', '')
        self.config.firebase_project_id = os.getenv('FIREBASE_PROJECT_ID', '')
        self.config.firebase_auth_domain = os.getenv('FIREBASE_AUTH_DOMAIN', '')
        self.config.firebase_database_url = os.getenv('FIREBASE_DATABASE_URL', '')
        self.config.firebase_storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET', '')
        self.config.firebase_messaging_sender_id = os.getenv('FIREBASE_MESSAGING_SENDER_ID', '')
        self.config.firebase_app_id = os.getenv('FIREBASE_APP_ID', '')
        self.config.firebase_service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT', '')
        
        # Google OAuth Configuration
        self.config.google_oauth_client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
        self.config.google_oauth_client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
        self.config.google_oauth_project_id = os.getenv('GOOGLE_OAUTH_PROJECT_ID', '')
        
        # Application Settings
        self.config.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.config.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.config.backend_type = os.getenv('BACKEND_TYPE', 'direct_firebase')
        self.config.port = int(os.getenv('PORT', '5000'))
        self.config.remember_session = os.getenv('REMEMBER_SESSION', 'true').lower() == 'true'
        self.config.session_timeout = int(os.getenv('SESSION_TIMEOUT', '3600'))
        
        # Auto-generate derived values if base values are provided
        if self.config.firebase_project_id and not self.config.firebase_auth_domain:
            self.config.firebase_auth_domain = f"{self.config.firebase_project_id}.firebaseapp.com"
        
        if self.config.firebase_project_id and not self.config.firebase_storage_bucket:
            self.config.firebase_storage_bucket = f"{self.config.firebase_project_id}.firebasestorage.app"
    
    def get_config(self) -> EnvironmentConfig:
        """Get the loaded configuration"""
        return self.config
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate the current configuration and return status"""
        return {
            'firebase_configured': self.config.is_firebase_configured(),
            'google_oauth_configured': self.config.is_google_oauth_configured(),
            'has_firebase_service_account': bool(self.config.firebase_service_account),
            'environment_loaded': True
        }
    
    def get_missing_config_info(self) -> Dict[str, list]:
        """Get information about missing configuration"""
        missing = {
            'firebase': [],
            'google_oauth': []
        }
        
        if not self.config.firebase_api_key:
            missing['firebase'].append('FIREBASE_API_KEY')
        if not self.config.firebase_project_id:
            missing['firebase'].append('FIREBASE_PROJECT_ID')
        if not self.config.firebase_auth_domain:
            missing['firebase'].append('FIREBASE_AUTH_DOMAIN')
        
        if not self.config.google_oauth_client_id:
            missing['google_oauth'].append('GOOGLE_OAUTH_CLIENT_ID')
        if not self.config.google_oauth_client_secret:
            missing['google_oauth'].append('GOOGLE_OAUTH_CLIENT_SECRET')
        
        return missing


# Global instance
_env_config_loader = None

def get_env_config() -> EnvironmentConfig:
    """Get the global environment configuration"""
    global _env_config_loader
    if _env_config_loader is None:
        _env_config_loader = EnvironmentConfigLoader()
    return _env_config_loader.get_config()

def reload_env_config() -> EnvironmentConfig:
    """Reload environment configuration"""
    global _env_config_loader
    _env_config_loader = EnvironmentConfigLoader()
    return _env_config_loader.get_config()

def validate_env_config() -> Dict[str, bool]:
    """Validate environment configuration"""
    global _env_config_loader
    if _env_config_loader is None:
        _env_config_loader = EnvironmentConfigLoader()
    return _env_config_loader.validate_configuration()
