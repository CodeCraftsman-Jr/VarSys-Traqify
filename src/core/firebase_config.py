"""
Firebase Configuration Manager

This module provides Firebase configuration and initialization for the Personal Finance Dashboard.
It handles both direct Firebase SDK usage and secure backend communication.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Try to import Firebase SDK components
try:
    import pyrebase
    import firebase_admin
    from firebase_admin import credentials, db, auth
    FIREBASE_SDK_AVAILABLE = True
except ImportError:
    FIREBASE_SDK_AVAILABLE = False
    pyrebase = None
    firebase_admin = None


class FirebaseManager:
    """Manages Firebase configuration and connections"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Firebase instances
        self.pyrebase_app = None
        self.admin_app = None
        self.auth_client = None
        self.database_client = None
        
        # Configuration
        self.config = self._load_config()
        self.is_initialized = False
        
        # Initialize if SDK is available
        if FIREBASE_SDK_AVAILABLE:
            self._initialize_firebase()
        else:
            self.logger.warning("Firebase SDK not available - using secure backend only")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load Firebase configuration from environment variables with secure fallbacks"""
        try:
            # Import environment config loader
            from .env_config import get_env_config
            env_config = get_env_config()

            # Try to load from environment variables first (most secure)
            if env_config.is_firebase_configured():
                self.logger.info("Loading Firebase configuration from environment variables")
                return env_config.to_firebase_config()

            # Try legacy environment variable format
            web_config_json = os.getenv('FIREBASE_WEB_CONFIG')
            if web_config_json:
                self.logger.info("Loading Firebase configuration from FIREBASE_WEB_CONFIG")
                return json.loads(web_config_json)

            # Fallback to config file (ONLY for development - should not contain real credentials in production)
            config_paths = [
                "config/secure_firebase_config.json",
                "secure_firebase_config.json",
                "firebase_config.json"
            ]

            for config_path in config_paths:
                if Path(config_path).exists():
                    self.logger.warning(f"Loading Firebase configuration from file: {config_path}")
                    self.logger.warning("WARNING: Using file-based configuration is not recommended for production!")
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                        # Convert to Firebase web config format
                        return {
                            "apiKey": config_data.get("api_key", ""),
                            "authDomain": config_data.get("auth_domain", ""),
                            "databaseURL": config_data.get("database_url", ""),
                            "projectId": config_data.get("project_id", ""),
                            "storageBucket": config_data.get("storage_bucket", ""),
                            "messagingSenderId": config_data.get("messaging_sender_id", ""),
                            "appId": config_data.get("app_id", "")
                        }

            # No configuration found - return empty config
            self.logger.warning("No Firebase configuration found. Please set environment variables or create config file.")
            self.logger.info("See .env.example for required environment variables")
            return {
                "apiKey": "",
                "authDomain": "",
                "databaseURL": "",
                "projectId": "",
                "storageBucket": "",
                "messagingSenderId": "",
                "appId": ""
            }

        except Exception as e:
            self.logger.error(f"Error loading Firebase config: {e}")
            return {}
    
    def _initialize_firebase(self):
        """Initialize Firebase SDK if available"""
        try:
            if not FIREBASE_SDK_AVAILABLE:
                self.logger.warning("Firebase SDK not available")
                return False
            
            # Initialize Pyrebase for client operations
            if self.config and not self.pyrebase_app:
                try:
                    self.pyrebase_app = pyrebase.initialize_app(self.config)
                    self.auth_client = self.pyrebase_app.auth()
                    self.database_client = self.pyrebase_app.database()
                    self.logger.info("Pyrebase initialized successfully")
                except Exception as e:
                    self.logger.warning(f"Pyrebase initialization failed: {e}")
            
            # Initialize Firebase Admin SDK if service account is available
            service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
            if service_account_json and not self.admin_app:
                try:
                    service_account = json.loads(service_account_json)
                    cred = credentials.Certificate(service_account)
                    self.admin_app = firebase_admin.initialize_app(cred, {
                        'databaseURL': self.config.get('databaseURL')
                    })
                    self.logger.info("Firebase Admin SDK initialized successfully")
                except Exception as e:
                    self.logger.warning(f"Firebase Admin SDK initialization failed: {e}")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"Firebase initialization failed: {e}")
            return False
    
    def get_auth(self):
        """Get Firebase auth client"""
        if self.auth_client:
            return self.auth_client
        return None
    
    def get_database(self):
        """Get Firebase database client"""
        if self.database_client:
            return self.database_client
        return None
    
    def get_admin_database(self):
        """Get Firebase admin database client"""
        if self.admin_app:
            return db
        return None
    
    def is_available(self) -> bool:
        """Check if Firebase is available"""
        return FIREBASE_SDK_AVAILABLE and self.is_initialized
    
    def get_config(self) -> Dict[str, Any]:
        """Get Firebase configuration"""
        return self.config


# Global Firebase manager instance
firebase_manager = FirebaseManager()
