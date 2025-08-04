"""
Firebase Authentication Module

This module handles Firebase user authentication, session management,
and user account operations.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, Signal, QTimer


@dataclass
class FirebaseUser:
    """Firebase user information"""
    uid: str
    email: str
    display_name: Optional[str] = None
    username: Optional[str] = None
    email_verified: bool = False
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'uid': self.uid,
            'email': self.email,
            'display_name': self.display_name,
            'username': self.username,
            'email_verified': self.email_verified,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FirebaseUser':
        """Create from dictionary"""
        return cls(**data)


class FirebaseAuthManager(QObject):
    """Manages Firebase authentication operations"""
    
    # Signals
    user_signed_in = Signal(FirebaseUser)
    user_signed_out = Signal()
    auth_error = Signal(str)
    user_updated = Signal(FirebaseUser)
    token_refreshed = Signal()  # Emitted when token is successfully refreshed
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Current user
        self.current_user: Optional[FirebaseUser] = None
        self.id_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
        # Session management - use different file to avoid conflict with DirectFirebaseClient
        self.session_file = Path("data/config/firebase_auth_session.json")
        self.remember_session = True

        # Token refresh management
        self.token_refresh_timer = QTimer()
        self.token_refresh_timer.timeout.connect(self._auto_refresh_token)
        self.token_refresh_interval = 50 * 60 * 1000  # 50 minutes in milliseconds (refresh before 1-hour expiry)
        self.last_token_refresh = None

        # Token validation timer (more frequent checks)
        self.token_validation_timer = QTimer()
        self.token_validation_timer.timeout.connect(self._validate_token_expiry)
        self.token_validation_interval = 5 * 60 * 1000  # 5 minutes in milliseconds
        self.token_issued_at = None

        # Check if DirectFirebaseClient is being used (to avoid conflicts)
        self.use_direct_firebase = self._check_direct_firebase_usage()

        # Load saved session if available and not using DirectFirebaseClient
        if not self.use_direct_firebase:
            self.load_session()
        else:
            self.logger.info("DirectFirebaseClient detected, skipping FirebaseAuthManager session loading")

        # Start token refresh timer if user is authenticated
        if self.is_authenticated():
            self.start_token_refresh_timer()

        self.logger.info("FirebaseAuthManager initialized")

    def _check_direct_firebase_usage(self) -> bool:
        """Check if DirectFirebaseClient is being used to avoid conflicts"""
        try:
            # Check secure config to see if direct_firebase backend is configured
            from .secure_config import get_secure_config
            config = get_secure_config()
            return config.backend_type == "direct_firebase"
        except Exception:
            # If we can't determine, assume DirectFirebaseClient is not being used
            return False

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self.current_user is not None and self.id_token is not None

    def is_available(self) -> bool:
        """Check if Firebase auth is available"""
        try:
            from .firebase_config import firebase_manager
            return firebase_manager.is_available()
        except ImportError:
            # In secure backend mode, Firebase auth is not directly available on client
            # All authentication goes through secure backend (Appwrite/Replit/Render)
            return False
    
    def sign_up(self, email: str, password: str, display_name: Optional[str] = None) -> bool:
        """Create a new user account using direct Firebase Auth"""
        try:
            if not self.is_available():
                self.auth_error.emit("Firebase authentication is not available")
                return False

            try:
                from .firebase_config import firebase_manager
                auth = firebase_manager.get_auth()
                if not auth:
                    self.auth_error.emit("Firebase authentication not initialized")
                    return False
            except ImportError:
                self.auth_error.emit("Firebase configuration not available")
                return False

            # Create user account
            user_data = auth.create_user_with_email_and_password(email, password)

            # Send email verification
            auth.send_email_verification(user_data['idToken'])

            # Update profile if display name provided
            if display_name:
                auth.update_profile(user_data['idToken'], display_name=display_name)

            # Create user object
            firebase_user = FirebaseUser(
                uid=user_data['localId'],
                email=email,
                display_name=display_name,
                email_verified=False,
                created_at=datetime.now().isoformat()
            )

            # Store user data in database
            self._store_user_data(firebase_user)

            # Store session
            self.current_user = firebase_user
            self.id_token = user_data['idToken']
            self.refresh_token = user_data['refreshToken']
            self.token_issued_at = datetime.now()

            if self.remember_session:
                self.save_session()
                self.start_token_refresh_timer()

            self.user_signed_in.emit(firebase_user)
            self.logger.info(f"User account created successfully: {email}")
            return True

        except Exception as e:
            error_msg = f"Error creating user account: {str(e)}"
            self.logger.error(error_msg)
            self.auth_error.emit(error_msg)
            return False
    
    def sign_in(self, email: str, password: str) -> bool:
        """Sign in with email and password"""
        try:
            if not self.is_available():
                self.auth_error.emit("Firebase authentication is not available")
                return False

            try:
                from .firebase_config import firebase_manager
                auth = firebase_manager.get_auth()
                if not auth:
                    self.auth_error.emit("Firebase authentication not initialized")
                    return False
            except ImportError:
                self.auth_error.emit("Firebase configuration not available")
                return False
            
            # Sign in user
            user_data = auth.sign_in_with_email_and_password(email, password)
            
            # Get user info
            user_info = auth.get_account_info(user_data['idToken'])
            user_details = user_info['users'][0]
            
            # Create user object
            firebase_user = FirebaseUser(
                uid=user_details['localId'],
                email=user_details['email'],
                display_name=user_details.get('displayName'),
                email_verified=user_details.get('emailVerified', False),
                last_login=datetime.now().isoformat()
            )
            
            # Load additional user data from database
            self._load_user_data(firebase_user)
            
            # Store session
            self.current_user = firebase_user
            self.id_token = user_data['idToken']
            self.refresh_token = user_data['refreshToken']
            self.token_issued_at = datetime.now()  # Track when token was issued

            if self.remember_session:
                self.save_session()
                # Start automatic token refresh timer
                self.start_token_refresh_timer()

            # Update last login
            self._update_user_data(firebase_user)

            self.user_signed_in.emit(firebase_user)
            self.logger.info(f"User signed in successfully: {email}")
            return True
            
        except Exception as e:
            error_msg = f"Error signing in: {str(e)}"
            self.logger.error(error_msg)
            self.auth_error.emit(error_msg)
            return False
    
    def sign_out(self) -> bool:
        """Sign out current user"""
        try:
            # Stop token refresh timer
            self.stop_token_refresh_timer()

            self.current_user = None
            self.id_token = None
            self.refresh_token = None

            # Clear saved session
            self.clear_session()

            self.user_signed_out.emit()
            self.logger.info("User signed out successfully")
            return True
            
        except Exception as e:
            error_msg = f"Error signing out: {str(e)}"
            self.logger.error(error_msg)
            self.auth_error.emit(error_msg)
            return False
    
    def change_password(self, current_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            if not self.current_user or not self.id_token:
                self.auth_error.emit("No user signed in")
                return False

            try:
                from .firebase_config import firebase_manager
                auth = firebase_manager.get_auth()
                if not auth:
                    self.auth_error.emit("Firebase authentication not initialized")
                    return False
            except ImportError:
                # In secure backend mode, just clear local session
                pass
            
            # Re-authenticate user first
            user_data = auth.sign_in_with_email_and_password(
                self.current_user.email, current_password
            )
            
            # Change password
            auth.update_profile(user_data['idToken'], password=new_password)
            
            self.logger.info("Password changed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Error changing password: {str(e)}"
            self.logger.error(error_msg)
            self.auth_error.emit(error_msg)
            return False
    
    def update_profile(self, display_name: Optional[str] = None, 
                      username: Optional[str] = None) -> bool:
        """Update user profile"""
        try:
            if not self.current_user or not self.id_token:
                self.auth_error.emit("No user signed in")
                return False
            
            try:
                from .firebase_config import firebase_manager
                auth = firebase_manager.get_auth()
                if not auth:
                    self.auth_error.emit("Firebase authentication not initialized")
                    return False
            except ImportError:
                self.auth_error.emit("Firebase configuration not available")
                return False
            
            # Update Firebase profile
            if display_name:
                auth.update_profile(self.id_token, display_name=display_name)
                self.current_user.display_name = display_name
            
            # Update username in our database
            if username:
                self.current_user.username = username
            
            # Update user data in database
            self._update_user_data(self.current_user)
            
            self.user_updated.emit(self.current_user)
            self.logger.info("User profile updated successfully")
            return True
            
        except Exception as e:
            error_msg = f"Error updating profile: {str(e)}"
            self.logger.error(error_msg)
            self.auth_error.emit(error_msg)
            return False
    
    def reset_password(self, email: str) -> bool:
        """Send password reset email"""
        try:
            if not self.is_available():
                self.auth_error.emit("Firebase authentication is not available")
                return False

            try:
                from .firebase_config import firebase_manager
                auth = firebase_manager.get_auth()
                if not auth:
                    self.auth_error.emit("Firebase authentication not initialized")
                    return False
            except ImportError:
                self.auth_error.emit("Firebase configuration not available")
                return False

            auth.send_password_reset_email(email)
            self.logger.info(f"Password reset email sent to: {email}")
            return True

        except Exception as e:
            error_msg = f"Error sending password reset email: {str(e)}"
            self.logger.error(error_msg)
            self.auth_error.emit(error_msg)
            return False

    def send_phone_verification(self, phone_number: str) -> Optional[str]:
        """Send phone verification code (simulated for now)"""
        try:
            if not self.is_available():
                self.auth_error.emit("Firebase authentication is not available")
                return None

            # In a real implementation, you would use Firebase Phone Auth
            # For now, we'll simulate this process
            import hashlib
            import time

            verification_id = hashlib.md5(f"{phone_number}{time.time()}".encode()).hexdigest()[:8]

            self.logger.info(f"Phone verification code sent to {phone_number}")
            self.logger.info(f"Verification ID: {verification_id}")
            self.logger.info("For testing, use verification code: 123456")

            return verification_id

        except Exception as e:
            error_msg = f"Error sending phone verification: {str(e)}"
            self.logger.error(error_msg)
            self.auth_error.emit(error_msg)
            return None

    def verify_phone_code(self, verification_id: str, code: str, phone_number: str) -> bool:
        """Verify phone verification code (simulated for now)"""
        try:
            if not self.is_available():
                self.auth_error.emit("Firebase authentication is not available")
                return False

            # In a real implementation, you would verify with Firebase Phone Auth
            # For simulation, we'll accept "123456" as valid code
            if code == "123456":
                # Create a phone-authenticated user
                phone_user = FirebaseUser(
                    uid=f"phone_{verification_id}",
                    email=f"phone_{verification_id}@phone.auth",
                    display_name=f"Phone User",
                    username=phone_number,
                    email_verified=True,
                    created_at=datetime.now().isoformat(),
                    last_login=datetime.now().isoformat()
                )

                # Set as current user
                self.current_user = phone_user
                self.id_token = f"phone_token_{verification_id}"
                self.refresh_token = f"phone_refresh_{verification_id}"

                # Store user data
                self._store_user_data(phone_user)

                # Save session if remember is enabled
                if self.remember_session:
                    self.save_session()

                self.user_signed_in.emit(phone_user)
                self.logger.info(f"Phone authentication successful for: {phone_number}")
                return True
            else:
                self.auth_error.emit("Invalid verification code")
                return False

        except Exception as e:
            error_msg = f"Error verifying phone code: {str(e)}"
            self.logger.error(error_msg)
            self.auth_error.emit(error_msg)
            return False
    
    def refresh_session(self) -> bool:
        """Refresh authentication session with enhanced error handling"""
        try:
            if not self.refresh_token:
                self.logger.warning("No refresh token available for session refresh")
                return False

            try:
                from .firebase_config import firebase_manager
                auth = firebase_manager.get_auth()
                if not auth:
                    self.logger.warning("Firebase auth not available for session refresh")
                    return False
            except ImportError:
                self.logger.warning("Firebase configuration not available for session refresh")
                return False

            self.logger.debug("Attempting to refresh authentication token...")

            # Refresh token
            user_data = auth.refresh(self.refresh_token)

            # Validate the response
            if not user_data or 'idToken' not in user_data:
                self.logger.error("Invalid response from token refresh")
                return False

            # Update tokens
            old_id_token = self.id_token
            self.id_token = user_data['idToken']
            self.refresh_token = user_data.get('refreshToken', self.refresh_token)

            # Update token issued timestamp
            self.token_issued_at = datetime.now()

            # Save updated session
            if self.remember_session:
                self.save_session()

            self.logger.info("✅ Session refreshed successfully")

            # Emit signal to notify other components of token update
            self.token_refreshed.emit()

            return True

        except Exception as e:
            error_str = str(e).upper()

            # Handle specific error types
            if any(error_type in error_str for error_type in [
                "INVALID_REFRESH_TOKEN",
                "TOKEN_EXPIRED",
                "REFRESH_TOKEN_EXPIRED",
                "400"
            ]):
                self.logger.warning("Refresh token expired or invalid, clearing session")
                self._handle_expired_refresh_token()
                return False

            elif any(error_type in error_str for error_type in [
                "NETWORK",
                "CONNECTION",
                "TIMEOUT",
                "503",
                "502"
            ]):
                self.logger.warning(f"Network error during token refresh: {e}")
                # Don't clear session for network errors, just return False
                return False

            else:
                self.logger.error(f"Unexpected error refreshing session: {e}")
                # For unknown errors, don't clear session immediately
                return False

    def _handle_expired_refresh_token(self):
        """Handle expired refresh token scenario"""
        try:
            # Stop the refresh timer
            self.stop_token_refresh_timer()

            # Clear session data
            self.clear_session()
            self.current_user = None
            self.id_token = None
            self.refresh_token = None

            # Emit sign out signal
            self.user_signed_out.emit()

            self.logger.info("Session cleared due to expired refresh token")

        except Exception as e:
            self.logger.error(f"Error handling expired refresh token: {e}")

    def start_token_refresh_timer(self):
        """Start the automatic token refresh timer"""
        if self.is_authenticated() and self.remember_session:
            self.token_refresh_timer.start(self.token_refresh_interval)
            self.token_validation_timer.start(self.token_validation_interval)
            self.last_token_refresh = datetime.now()
            self.token_issued_at = datetime.now()  # Track when token was issued/refreshed
            self.logger.info(f"Token refresh timer started - will refresh every {self.token_refresh_interval // 60000} minutes")
            self.logger.debug(f"Token validation timer started - will check every {self.token_validation_interval // 60000} minutes")

    def stop_token_refresh_timer(self):
        """Stop the automatic token refresh timer"""
        self.token_refresh_timer.stop()
        self.token_validation_timer.stop()
        self.logger.debug("Token refresh and validation timers stopped")

    def _auto_refresh_token(self):
        """Automatically refresh the authentication token"""
        try:
            self.logger.info("🔄 Performing automatic token refresh...")

            if not self.is_authenticated():
                self.logger.warning("User not authenticated, stopping token refresh timer")
                self.stop_token_refresh_timer()
                return

            # Attempt to refresh the token
            if self.refresh_session():
                self.last_token_refresh = datetime.now()
                self.logger.info("✅ Automatic token refresh successful")
            else:
                self.logger.warning("❌ Automatic token refresh failed")
                # Don't stop the timer immediately, try again next time
                # If it fails multiple times, the refresh_session method will handle cleanup

        except Exception as e:
            self.logger.error(f"Error in automatic token refresh: {e}")

    def _validate_token_expiry(self):
        """Validate if token is approaching expiry and trigger early refresh"""
        try:
            if not self.is_authenticated() or not self.token_issued_at:
                return

            # Calculate token age
            token_age = datetime.now() - self.token_issued_at

            # Firebase ID tokens typically expire after 1 hour
            # Trigger refresh if token is older than 45 minutes
            if token_age.total_seconds() > 45 * 60:  # 45 minutes
                self.logger.info("🔔 Token approaching expiry, triggering early refresh...")
                if self.refresh_session():
                    self.logger.info("✅ Early token refresh successful")
                else:
                    self.logger.warning("❌ Early token refresh failed")

        except Exception as e:
            self.logger.error(f"Error in token expiry validation: {e}")

    def start_token_validation_timer(self):
        """Start the token validation timer"""
        if self.is_authenticated():
            self.token_validation_timer.start(self.token_validation_interval)
            self.logger.debug("Token validation timer started")

    def stop_token_validation_timer(self):
        """Stop the token validation timer"""
        self.token_validation_timer.stop()
        self.logger.debug("Token validation timer stopped")

    def save_session(self):
        """Save current session to file"""
        try:
            if not self.current_user or not self.id_token:
                return
            
            session_data = {
                'user': self.current_user.to_dict(),
                'id_token': self.id_token,
                'refresh_token': self.refresh_token,
                'saved_at': datetime.now().isoformat(),
                'token_issued_at': self.token_issued_at.isoformat() if self.token_issued_at else None,
                'last_token_refresh': self.last_token_refresh.isoformat() if self.last_token_refresh else None,
                'session_version': '2.0'  # Version for future compatibility
            }
            
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            self.logger.debug("Session saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving session: {e}")
    
    def load_session(self) -> bool:
        """Load saved session from file"""
        try:
            if not self.session_file.exists():
                return False

            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Check if session is not too old (7 days)
            saved_at = datetime.fromisoformat(session_data['saved_at'])
            if datetime.now() - saved_at > timedelta(days=7):
                self.logger.info("Session expired (older than 7 days), clearing")
                self.clear_session()
                return False

            # Restore session
            self.current_user = FirebaseUser.from_dict(session_data['user'])
            self.id_token = session_data['id_token']
            self.refresh_token = session_data['refresh_token']

            # Restore token timestamps if available (for session version 2.0+)
            if 'token_issued_at' in session_data and session_data['token_issued_at']:
                self.token_issued_at = datetime.fromisoformat(session_data['token_issued_at'])
            else:
                # For older sessions, assume token was issued when session was saved
                self.token_issued_at = datetime.fromisoformat(session_data['saved_at'])

            if 'last_token_refresh' in session_data and session_data['last_token_refresh']:
                self.last_token_refresh = datetime.fromisoformat(session_data['last_token_refresh'])

            # Check if token needs immediate refresh based on age
            if self.token_issued_at:
                token_age = datetime.now() - self.token_issued_at
                if token_age.total_seconds() > 55 * 60:  # Token older than 55 minutes
                    self.logger.info("Loaded token is approaching expiry, refreshing immediately...")

            # Try to refresh session
            if self.refresh_session():
                self.logger.info("Session loaded and refreshed successfully")
                # Start token refresh timer for restored session
                if self.remember_session:
                    self.start_token_refresh_timer()
                return True
            else:
                # Session refresh failed (token invalid), clear it
                self.logger.info("Session refresh failed, clearing session")
                self.clear_session()
                return False

        except Exception as e:
            self.logger.info(f"Error loading session (clearing): {e}")
            self.clear_session()
            return False
    
    def clear_session(self):
        """Clear saved session"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            self.logger.debug("Session cleared")
        except Exception as e:
            self.logger.error(f"Error clearing session: {e}")
    
    def _store_user_data(self, user: FirebaseUser):
        """Store user data in Firebase database"""
        try:
            try:
                from .firebase_config import firebase_manager
                database = firebase_manager.get_database()
                if database and self.id_token:
                    # Authenticate the database request with the user's ID token
                    database.child("users").child(user.uid).set(user.to_dict(), self.id_token)
            except ImportError:
                # Firebase not available, skip storing user data
                pass
        except Exception as e:
            self.logger.error(f"Error storing user data: {e}")
    
    def _load_user_data(self, user: FirebaseUser):
        """Load additional user data from Firebase database"""
        try:
            try:
                from .firebase_config import firebase_manager
                database = firebase_manager.get_database()
                if database and self.id_token:
                    # Authenticate the database request with the user's ID token
                    user_data = database.child("users").child(user.uid).get(self.id_token).val()
                    if user_data:
                        user.username = user_data.get('username')
                        user.created_at = user_data.get('created_at')
            except ImportError:
                # Firebase not available, skip loading user data
                pass
        except Exception as e:
            self.logger.error(f"Error loading user data: {e}")

    def _update_user_data(self, user: FirebaseUser):
        """Update user data in Firebase database"""
        try:
            try:
                from .firebase_config import firebase_manager
                database = firebase_manager.get_database()
                if database and self.id_token:
                    # Authenticate the database request with the user's ID token
                    database.child("users").child(user.uid).update(user.to_dict(), self.id_token)
            except ImportError:
                # Firebase not available, skip updating user data
                pass
        except Exception as e:
            self.logger.error(f"Error updating user data: {e}")


# Global Firebase auth manager instance
firebase_auth = FirebaseAuthManager()
