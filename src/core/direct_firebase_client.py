"""
Direct Firebase Client

This module provides direct Firebase Realtime Database access without backend services.
It supports multiple authentication methods and fallback mechanisms.
"""

import json
import logging
import requests
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Firebase SDK imports with fallback
try:
    import pyrebase
    PYREBASE_AVAILABLE = True
except ImportError:
    PYREBASE_AVAILABLE = False

try:
    import firebase_admin
    from firebase_admin import credentials, db as admin_db
    FIREBASE_ADMIN_AVAILABLE = True
except ImportError:
    FIREBASE_ADMIN_AVAILABLE = False


class DirectFirebaseClient:
    """Direct Firebase client with multiple authentication methods"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Firebase configuration
        self.config = self._load_firebase_config()
        self.database_url = self.config.get('database_url', '')
        self.project_id = self.config.get('project_id', '')
        
        # Authentication state
        self.current_user = None
        self.id_token = None
        self.refresh_token = None
        self.token_issued_at = None

        # Session persistence - use absolute path to ensure correct resolution
        # Handle both packaged and script execution
        if getattr(sys, 'frozen', False):
            # Running as packaged executable
            app_root = Path(sys.executable).parent
        else:
            # Running as script
            app_root = Path(__file__).parent.parent.parent
        self.session_file = app_root / "data" / "config" / "firebase_session.json"
        self.remember_session = True

        # Firebase clients
        self.pyrebase_app = None
        self.admin_app = None
        self.auth_client = None
        self.database_client = None

        # Initialize Firebase clients
        self._initialize_clients()

        # Load saved session if available
        session_loaded = self._load_session()
        if session_loaded:
            user_email = self.current_user.get('email', 'Unknown') if self.current_user else 'Unknown'
            self.logger.info(f"✅ Session restored for user: {user_email}")
        else:
            self.logger.info("No saved session found or session invalid")

        self.logger.info("DirectFirebaseClient initialized")
    
    def _load_firebase_config(self) -> Dict[str, Any]:
        """Load Firebase configuration"""
        try:
            # Try to load from secure config first
            config_path = Path("config/secure_firebase_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Convert to Pyrebase format (camelCase keys)
                    return {
                        'apiKey': config.get('api_key', ''),
                        'authDomain': config.get('auth_domain', ''),
                        'databaseURL': config.get('database_url', ''),
                        'projectId': config.get('project_id', ''),
                        'storageBucket': config.get('storage_bucket', ''),
                        'messagingSenderId': config.get('messaging_sender_id', ''),
                        'appId': config.get('app_id', ''),
                        # Keep snake_case versions for internal use
                        'database_url': config.get('database_url', ''),
                        'project_id': config.get('project_id', ''),
                        'auth_domain': config.get('auth_domain', ''),
                        'api_key': config.get('api_key', ''),
                        'storage_bucket': config.get('storage_bucket', ''),
                        'messaging_sender_id': config.get('messaging_sender_id', ''),
                        'app_id': config.get('app_id', '')
                    }
            
            # Fallback to firebase config
            from .firebase_config import firebase_manager
            if firebase_manager and firebase_manager.config:
                return firebase_manager.config
                
            # Default empty configuration - requires environment variables
            return {
                'apiKey': '',
                'authDomain': '',
                'databaseURL': '',
                'projectId': '',
                'storageBucket': '',
                'messagingSenderId': '',
                'appId': '',
                # Keep snake_case versions for internal use
                'database_url': '',
                'project_id': '',
                'auth_domain': '',
                'api_key': '',
                'storage_bucket': '',
                'messaging_sender_id': '',
                'app_id': ''
            }
            
        except Exception as e:
            self.logger.error(f"Error loading Firebase config: {e}")
            return {}
    
    def _initialize_clients(self):
        """Initialize Firebase clients"""
        try:
            # Initialize Pyrebase for web SDK operations
            if PYREBASE_AVAILABLE and self.config:
                try:
                    self.pyrebase_app = pyrebase.initialize_app(self.config)
                    self.auth_client = self.pyrebase_app.auth()
                    self.database_client = self.pyrebase_app.database()
                    self.logger.info("Pyrebase client initialized successfully")
                except Exception as e:
                    self.logger.warning(f"Pyrebase initialization failed: {e}")
            
            # Initialize Firebase Admin SDK if available
            if FIREBASE_ADMIN_AVAILABLE:
                try:
                    # Check if admin app already exists
                    try:
                        self.admin_app = firebase_admin.get_app()
                        self.logger.info("Using existing Firebase Admin app")
                    except ValueError:
                        # No app exists, try to create one
                        service_account_path = Path("config/firebase_service_account.json")
                        if service_account_path.exists():
                            cred = credentials.Certificate(str(service_account_path))
                            self.admin_app = firebase_admin.initialize_app(cred, {
                                'databaseURL': self.database_url
                            })
                            self.logger.info("Firebase Admin SDK initialized with service account")
                        else:
                            self.logger.info("No service account found, Admin SDK not available")
                except Exception as e:
                    self.logger.warning(f"Firebase Admin SDK initialization failed: {e}")
            
        except Exception as e:
            self.logger.error(f"Error initializing Firebase clients: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.current_user is not None and self.id_token is not None
    
    def sign_in_with_email_password(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign in with email and password"""
        try:
            # Try Pyrebase first
            if self.auth_client:
                try:
                    user = self.auth_client.sign_in_with_email_and_password(email, password)

                    self.current_user = user
                    self.id_token = user.get('idToken')
                    self.refresh_token = user.get('refreshToken')
                    self.token_issued_at = datetime.now()

                    # Save session for persistence
                    self.logger.info(f"🔐 Pyrebase authentication successful, saving session...")
                    if self.remember_session:
                        self._save_session()
                    else:
                        self.logger.warning("⚠️ Remember session is disabled, not saving")

                    self.logger.info(f"✅ Successfully signed in user via Pyrebase: {email}")
                    return True, "Sign in successful via Pyrebase"
                except Exception as e:
                    self.logger.warning(f"Pyrebase sign in failed: {e}")

            # Fallback to REST API authentication
            return self._sign_in_with_rest_api(email, password)

        except Exception as e:
            error_msg = f"Sign in failed: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _sign_in_with_rest_api(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign in using Firebase REST API"""
        try:
            # Firebase Auth REST API endpoint
            api_key = self.config.get('api_key', '')
            if not api_key or api_key.startswith('AIzaSyDXXXXXX'):
                return False, "Valid Firebase API key required for authentication"

            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }

            response = requests.post(url, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()

                self.current_user = {
                    'localId': data.get('localId'),
                    'email': data.get('email'),
                    'displayName': data.get('displayName', ''),
                    'idToken': data.get('idToken'),
                    'refreshToken': data.get('refreshToken')
                }
                self.id_token = data.get('idToken')
                self.refresh_token = data.get('refreshToken')
                self.token_issued_at = datetime.now()

                # Save session for persistence
                self.logger.info(f"🔐 REST API authentication successful, saving session...")
                if self.remember_session:
                    self._save_session()
                else:
                    self.logger.warning("⚠️ Remember session is disabled, not saving")

                self.logger.info(f"✅ Successfully signed in user via REST API: {email}")
                return True, "Sign in successful via REST API"
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                return False, f"Authentication failed: {error_message}"

        except Exception as e:
            self.logger.error(f"REST API sign in failed: {e}")
            return False, str(e)
    
    def upload_data(self, module: str, filename: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Upload data directly to Firebase Realtime Database"""
        try:
            if not self.is_authenticated():
                return False, "User not authenticated"
            
            # Clean filename (remove .csv extension)
            clean_filename = filename.replace('.csv', '')
            
            # Construct path
            user_id = self.current_user.get('localId', 'unknown')
            path = f"users/{user_id}/data/{module}/{clean_filename}"
            
            # Try different upload methods
            success, message = self._upload_with_pyrebase(path, data)
            if success:
                return True, message
            
            success, message = self._upload_with_rest_api(path, data)
            if success:
                return True, message
            
            return False, "All upload methods failed"
            
        except Exception as e:
            error_msg = f"Upload error: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def download_data(self, module: str, filename: str) -> Tuple[bool, Optional[Dict], str]:
        """Download data directly from Firebase Realtime Database"""
        try:
            if not self.is_authenticated():
                return False, None, "User not authenticated"
            
            # Clean filename (remove .csv extension)
            clean_filename = filename.replace('.csv', '')
            
            # Construct path
            user_id = self.current_user.get('localId', 'unknown')
            path = f"users/{user_id}/data/{module}/{clean_filename}"
            
            # Try different download methods
            success, data, message = self._download_with_pyrebase(path)
            if success:
                return True, data, message
            
            success, data, message = self._download_with_rest_api(path)
            if success:
                return True, data, message
            
            return False, None, "All download methods failed"
            
        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg

    def _upload_with_pyrebase(self, path: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Upload data using Pyrebase"""
        try:
            if not self.database_client or not self.id_token:
                return False, "Pyrebase client or token not available"

            # Upload data
            self.database_client.child(path).set(data, self.id_token)
            self.logger.info(f"Successfully uploaded data via Pyrebase to: {path}")
            return True, "Data uploaded successfully via Pyrebase"

        except Exception as e:
            self.logger.warning(f"Pyrebase upload failed: {e}")
            return False, str(e)

    def _upload_with_rest_api(self, path: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Upload data using REST API"""
        try:
            if not self.id_token:
                return False, "Authentication token not available"

            url = f"{self.database_url}/{path}.json"
            headers = {'Authorization': f'Bearer {self.id_token}'}

            response = requests.put(url, json=data, headers=headers, timeout=30)

            if response.status_code == 200:
                self.logger.info(f"Successfully uploaded data via REST API to: {path}")
                return True, "Data uploaded successfully via REST API"
            else:
                error_msg = f"REST API upload failed: {response.status_code} - {response.text}"
                self.logger.warning(error_msg)
                return False, error_msg

        except Exception as e:
            self.logger.warning(f"REST API upload failed: {e}")
            return False, str(e)

    def _download_with_pyrebase(self, path: str) -> Tuple[bool, Optional[Dict], str]:
        """Download data using Pyrebase"""
        try:
            if not self.database_client or not self.id_token:
                return False, None, "Pyrebase client or token not available"

            # Download data
            data = self.database_client.child(path).get(self.id_token).val()

            if data is None:
                return False, None, "No data found"

            self.logger.info(f"Successfully downloaded data via Pyrebase from: {path}")
            return True, data, "Data downloaded successfully via Pyrebase"

        except Exception as e:
            self.logger.warning(f"Pyrebase download failed: {e}")
            return False, None, str(e)

    def _download_with_rest_api(self, path: str) -> Tuple[bool, Optional[Dict], str]:
        """Download data using REST API"""
        try:
            if not self.id_token:
                return False, None, "Authentication token not available"

            url = f"{self.database_url}/{path}.json"
            headers = {'Authorization': f'Bearer {self.id_token}'}

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data is None:
                    return False, None, "No data found"

                self.logger.info(f"Successfully downloaded data via REST API from: {path}")
                return True, data, "Data downloaded successfully via REST API"
            else:
                error_msg = f"REST API download failed: {response.status_code} - {response.text}"
                self.logger.warning(error_msg)
                return False, None, error_msg

        except Exception as e:
            self.logger.warning(f"REST API download failed: {e}")
            return False, None, str(e)

    def refresh_auth_token(self) -> bool:
        """Refresh authentication token with improved error handling"""
        try:
            if not self.refresh_token:
                self.logger.warning("No refresh token available")
                return False

            if not self.auth_client:
                self.logger.warning("No auth client available for token refresh")
                return False

            self.logger.info("Attempting to refresh authentication token...")
            user = self.auth_client.refresh(self.refresh_token)

            if not user or 'idToken' not in user:
                self.logger.error("Invalid response from token refresh")
                return False

            # Update tokens
            old_token = self.id_token
            self.id_token = user.get('idToken')
            self.refresh_token = user.get('refreshToken', self.refresh_token)
            self.token_issued_at = datetime.now()

            # Save updated session
            if self.remember_session:
                self._save_session()

            self.logger.info("✅ Authentication token refreshed successfully")
            return True

        except Exception as e:
            error_str = str(e).upper()

            # Check for specific error types that indicate invalid refresh token
            if any(error_type in error_str for error_type in [
                "INVALID_REFRESH_TOKEN",
                "TOKEN_EXPIRED",
                "REFRESH_TOKEN_EXPIRED",
                "400"
            ]):
                self.logger.warning("Refresh token is invalid or expired, clearing session")
                self._clear_session()
                return False
            else:
                # For network errors or other temporary issues, don't clear session
                self.logger.warning(f"Token refresh failed (temporary): {e}")
                return False

    def _save_session(self):
        """Save current session to file for persistence"""
        try:
            self.logger.info(f"🔄 Session save requested - remember_session: {self.remember_session}")

            if not self.remember_session:
                self.logger.info("Session persistence disabled, not saving session")
                return

            self.logger.info("🔄 Attempting to save session...")

            if not self.current_user or not self.id_token:
                self.logger.warning("❌ Cannot save session: missing user or token data")
                self.logger.warning(f"   Current user: {bool(self.current_user)}")
                self.logger.warning(f"   ID token: {bool(self.id_token)}")
                return

            user_email = self.current_user.get('email', 'Unknown') if self.current_user else 'Unknown'
            self.logger.info(f"💾 Saving session for user: {user_email}")

            session_data = {
                'user': self.current_user,
                'id_token': self.id_token,
                'refresh_token': self.refresh_token,
                'token_issued_at': self.token_issued_at.isoformat() if self.token_issued_at else None,
                'saved_at': datetime.now().isoformat(),
                'session_version': '2.0',  # Updated version
                'user_email': user_email,
                'expires_in_days': 30,  # Document the expiration policy
                'remember_session': self.remember_session  # Store the preference
            }

            # Ensure directory exists
            self.logger.info(f"📁 Ensuring directory exists: {self.session_file.parent}")
            self.session_file.parent.mkdir(parents=True, exist_ok=True)

            # Create backup of existing session
            if self.session_file.exists():
                backup_file = self.session_file.with_suffix('.json.backup')
                try:
                    import shutil
                    shutil.copy2(self.session_file, backup_file)
                    self.logger.info(f"💾 Created session backup: {backup_file}")
                except Exception as backup_error:
                    self.logger.warning(f"Could not create session backup: {backup_error}")

            self.logger.info(f"📝 Writing session file: {self.session_file}")
            self.logger.info(f"📝 Absolute path: {self.session_file.absolute()}")
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)

            # Verify the file was created and is valid
            self.logger.info(f"🔍 Checking if session file was created...")
            if self.session_file.exists():
                file_size = self.session_file.stat().st_size
                self.logger.info(f"✅ Session file exists with size: {file_size} bytes")
                if file_size > 0:
                    # Verify the file can be read back
                    try:
                        with open(self.session_file, 'r', encoding='utf-8') as f:
                            test_data = json.load(f)
                        if 'user' in test_data and 'id_token' in test_data:
                            self.logger.info(f"✅ Session saved and verified for user: {user_email} (file size: {file_size} bytes)")
                            self.logger.info(f"✅ Session file location: {self.session_file.absolute()}")
                        else:
                            self.logger.error(f"❌ Session file is missing required fields")
                    except Exception as verify_error:
                        self.logger.error(f"❌ Session file verification failed: {verify_error}")
                        # Remove corrupted file
                        try:
                            self.session_file.unlink()
                        except:
                            pass
                else:
                    self.logger.error(f"❌ Session file is empty: {self.session_file}")
            else:
                self.logger.error(f"❌ Session file was not created: {self.session_file}")
                self.logger.error(f"❌ Expected location: {self.session_file.absolute()}")
                # Check if directory exists
                if self.session_file.parent.exists():
                    self.logger.error(f"❌ Directory exists but file was not created")
                    # List files in directory
                    try:
                        files = list(self.session_file.parent.iterdir())
                        self.logger.error(f"❌ Files in directory: {[f.name for f in files]}")
                    except Exception as e:
                        self.logger.error(f"❌ Could not list directory contents: {e}")
                else:
                    self.logger.error(f"❌ Directory does not exist: {self.session_file.parent}")

        except Exception as e:
            self.logger.error(f"❌ Error saving session: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def _load_session(self) -> bool:
        """Load saved session from file with robust validation"""
        try:
            self.logger.info(f"🔍 Looking for session file at: {self.session_file.absolute()}")
            if not self.session_file.exists():
                self.logger.debug(f"No session file found at: {self.session_file.absolute()}")
                # Check if file exists in other common locations
                alt_paths = [
                    Path("data/config/firebase_session.json"),
                    Path("./data/config/firebase_session.json"),
                    Path.cwd() / "data" / "config" / "firebase_session.json"
                ]
                for alt_path in alt_paths:
                    if alt_path.exists():
                        self.logger.warning(f"⚠️ Found session file at alternative location: {alt_path.absolute()}")
                        break
                return False

            self.logger.info("Loading saved session...")

            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Validate session data structure
            required_fields = ['user', 'id_token', 'refresh_token', 'saved_at']
            for field in required_fields:
                if field not in session_data:
                    self.logger.warning(f"Session file missing required field: {field}")
                    self._clear_session()
                    return False

            # Validate user data
            if not session_data['user'] or not isinstance(session_data['user'], dict):
                self.logger.warning("Invalid user data in session")
                self._clear_session()
                return False

            # Validate essential user fields
            user_data = session_data['user']
            if not user_data.get('email') and not user_data.get('localId'):
                self.logger.warning("Session user data missing essential identifiers (email or localId)")
                self._clear_session()
                return False

            # Validate tokens
            if not session_data['id_token'] or not isinstance(session_data['id_token'], str):
                self.logger.warning("Invalid or missing ID token in session")
                self._clear_session()
                return False

            # Check if session is not too old (30 days)
            saved_at = datetime.fromisoformat(session_data['saved_at'])
            session_age = datetime.now() - saved_at
            if session_age > timedelta(days=30):
                self.logger.info(f"Session expired (older than 30 days), clearing. Age: {session_age.days} days")
                self._clear_session()
                return False

            self.logger.info(f"Loading session saved {session_age.days} days ago")

            # Restore session data
            self.current_user = session_data['user']
            self.id_token = session_data['id_token']
            self.refresh_token = session_data['refresh_token']

            if session_data.get('token_issued_at'):
                self.token_issued_at = datetime.fromisoformat(session_data['token_issued_at'])
            else:
                self.token_issued_at = saved_at

            # Check if token needs refresh (older than 50 minutes)
            if self.token_issued_at:
                token_age = datetime.now() - self.token_issued_at
                token_age_minutes = token_age.total_seconds() / 60

                self.logger.info(f"Token age: {token_age_minutes:.1f} minutes")

                if token_age_minutes > 50:  # 50 minutes
                    self.logger.info("Token is approaching expiry, attempting refresh...")
                    if self.refresh_auth_token():
                        self.logger.info("Session loaded and token refreshed successfully")
                        return True
                    else:
                        self.logger.warning("Token refresh failed, but keeping session for retry later")
                        # Don't clear session immediately - network issues might be temporary
                        # Only clear if refresh token is actually invalid
                        return True  # Still return True to avoid re-login
                else:
                    self.logger.info(f"Token is still valid (age: {token_age_minutes:.1f} minutes)")

            self.logger.info("Session loaded successfully")
            return True

        except Exception as e:
            self.logger.warning(f"Error loading session: {e}")
            self._clear_session()
            return False

    def _clear_session(self):
        """Clear saved session file"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            self.logger.debug("Session file cleared")
        except Exception as e:
            self.logger.error(f"Error clearing session: {e}")

    def has_valid_session(self) -> bool:
        """Check if there's a valid session without loading it"""
        try:
            if not self.session_file.exists():
                return False

            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Check basic structure
            if not all(key in session_data for key in ['saved_at', 'user', 'id_token', 'refresh_token']):
                return False

            # Check age
            saved_at = datetime.fromisoformat(session_data['saved_at'])
            if datetime.now() - saved_at > timedelta(days=30):
                return False

            return True

        except Exception:
            return False

    def sign_out(self):
        """Sign out user and clear session"""
        try:
            user_email = self.current_user.get('email', 'Unknown') if self.current_user else 'Unknown'

            # Clear in-memory state
            self.current_user = None
            self.id_token = None
            self.refresh_token = None
            self.token_issued_at = None

            # Clear saved session
            self._clear_session()

            self.logger.info(f"✅ User signed out successfully: {user_email}")

        except Exception as e:
            self.logger.error(f"Error during sign out: {e}")


# Global instance
_direct_firebase_client = None

def get_direct_firebase_client() -> DirectFirebaseClient:
    """Get global DirectFirebaseClient instance"""
    global _direct_firebase_client
    if _direct_firebase_client is None:
        _direct_firebase_client = DirectFirebaseClient()
    return _direct_firebase_client
