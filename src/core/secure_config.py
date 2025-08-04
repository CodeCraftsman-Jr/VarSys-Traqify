"""
Secure Configuration Module for Personal Finance Dashboard

This module contains only public, non-sensitive configuration information.
All sensitive credentials are handled securely by Firebase Cloud Functions.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class SecureFirebaseConfig:
    """Secure Firebase configuration with only public information"""
    
    # Public Firebase project information (will be loaded from environment)
    project_id: str = ""
    auth_domain: str = ""
    
    # Backend API endpoints (public URLs) - Replit hosting
    functions_base_url: str = "https://your-replit-app-name.your-username.repl.co"
    
    # Public configuration
    enabled: bool = True
    auto_sync: bool = False
    sync_interval: int = 300  # seconds
    remember_session: bool = True
    
    # Client-side settings
    timeout_seconds: int = 30
    retry_attempts: int = 3

    # Backend configuration
    backend_type: str = "appwrite"  # "appwrite" or "direct_firebase"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecureFirebaseConfig':
        """Create from dictionary with defaults for missing fields"""
        # Create a new instance with defaults
        config = cls()

        # Update only the fields that are present in the data
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config
    
    def get_endpoint_url(self, endpoint: str) -> str:
        """Get full URL for a specific endpoint"""
        return f"{self.functions_base_url}/{endpoint.lstrip('/')}"
    
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return bool(
            self.functions_base_url and
            self.enabled
        )

class SecureConfigManager:
    """Manages secure configuration without exposing sensitive credentials"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Configuration file path
        if config_path:
            self.config_path = config_path
        else:
            # Try multiple config file locations
            possible_paths = [
                "config/secure_firebase_config.json",
                "secure_firebase_config_replit.json",
                "secure_firebase_config.json"
            ]

            self.config_path = None
            for path in possible_paths:
                if Path(path).exists():
                    self.config_path = path
                    break

            # Default to the main config file if none found
            if not self.config_path:
                self.config_path = "config/secure_firebase_config.json"
        
        self.config = SecureFirebaseConfig()
        self.load_config()
    
    def load_config(self) -> bool:
        """Load secure configuration from file"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = SecureFirebaseConfig.from_dict(config_data)
                self.logger.info("Secure Firebase configuration loaded successfully")
                return True
            else:
                self.logger.info("Secure configuration file not found, using defaults")
                self.save_config()  # Create default config file
                return True
        except Exception as e:
            self.logger.error(f"Error loading secure configuration: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save secure configuration to file"""
        try:
            config_file = Path(self.config_path)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            self.logger.info("Secure configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving secure configuration: {e}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """Update configuration with new values"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    self.logger.warning(f"Unknown configuration key: {key}")
            
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    def get_config(self) -> SecureFirebaseConfig:
        """Get current configuration"""
        return self.config
    
    def is_configured(self) -> bool:
        """Check if Firebase is properly configured"""
        return self.config.is_valid()
    
    def get_auth_endpoints(self) -> Dict[str, str]:
        """Get authentication endpoint URLs - Firebase direct integration"""
        # Use configured Firebase functions URL directly (service discovery removed)
        base_url = self.config.functions_base_url
        return {
            'signup': f"{base_url}/auth/signup",
            'signin': f"{base_url}/auth/sign-in",
            'get_user': f"{base_url}/auth/get-user",
            'verify': f"{base_url}/auth/verify",
            'reset_password': f"{base_url}/auth/reset-password",
            'refresh': f"{base_url}/auth/refresh"
        }
    
    def get_data_endpoints(self) -> Dict[str, str]:
        """Get data management endpoint URLs - Firebase direct integration"""
        # Use configured Firebase functions URL directly (service discovery removed)
        base_url = self.config.functions_base_url
        return {
            'get_data': f"{base_url}/data",
            'upload_data': f"{base_url}/data",
            'sync_all': f"{base_url}/data/sync/all",
            'batch_upload': f"{base_url}/data/sync/upload"
        }
    
    def get_user_endpoints(self) -> Dict[str, str]:
        """Get user management endpoint URLs"""
        base_url = self.config.functions_base_url
        return {
            'profile': f"{base_url}/user/profile",
            'settings': f"{base_url}/user/settings",
            'delete_account': f"{base_url}/user/account"
        }

# Global instance
secure_config_manager = SecureConfigManager()

def get_secure_config() -> SecureFirebaseConfig:
    """Get the global secure configuration"""
    return secure_config_manager.get_config()

def is_firebase_configured() -> bool:
    """Check if Firebase is configured securely"""
    return secure_config_manager.is_configured()

def get_auth_endpoints() -> Dict[str, str]:
    """Get authentication endpoints"""
    return secure_config_manager.get_auth_endpoints()

def get_data_endpoints() -> Dict[str, str]:
    """Get data endpoints"""
    return secure_config_manager.get_data_endpoints()

def get_user_endpoints() -> Dict[str, str]:
    """Get user endpoints"""
    return secure_config_manager.get_user_endpoints()
