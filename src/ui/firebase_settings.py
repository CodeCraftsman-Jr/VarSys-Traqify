"""
Firebase Settings Widget

This module provides UI components for Firebase account management
and configuration within the Settings dialog.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QTextEdit, QMessageBox, QDialog, QDialogButtonBox,
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon

# Legacy Firebase imports removed - using secure backend system only
firebase_manager = None
firebase_auth = None
FirebaseUser = None
FIREBASE_IMPORTS_AVAILABLE = False

# Import direct Firebase authentication system
try:
    from ..core.direct_firebase_client import get_direct_firebase_client
    FIREBASE_AUTH_AVAILABLE = True
except ImportError:
    get_direct_firebase_client = None
    FIREBASE_AUTH_AVAILABLE = False

# Import secure authentication system
try:
    from ..core.direct_firebase_client import get_direct_firebase_client as get_secure_client
    SECURE_AUTH_AVAILABLE = True
except ImportError:
    get_secure_client = None
    SECURE_AUTH_AVAILABLE = False

# Simple user class for compatibility
class SecureUser:
    def __init__(self, uid, email, display_name=None, email_verified=False):
        self.uid = uid
        self.email = email
        self.display_name = display_name
        self.email_verified = email_verified


class FirebaseLoginDialog(QDialog):
    """Dialog for Firebase login/registration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the login dialog UI"""
        self.setWindowTitle("Firebase Account")
        self.setMinimumSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Sign in to Firebase Account")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Form
        form_layout = QFormLayout()
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter your email")
        form_layout.addRow("Email:", self.email_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter your password")
        form_layout.addRow("Password:", self.password_edit)
        
        layout.addLayout(form_layout)
        
        # Remember session
        self.remember_checkbox = QCheckBox("Remember session")
        self.remember_checkbox.setChecked(True)
        layout.addWidget(self.remember_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Sign In")
        self.login_button.clicked.connect(self.sign_in)
        button_layout.addWidget(self.login_button)

        self.reset_button = QPushButton("Reset Password")
        self.reset_button.clicked.connect(self.reset_password)
        button_layout.addWidget(self.reset_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
    def sign_in(self):
        """Handle sign in"""
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        
        if not email or not password:
            self.status_label.setText("Please enter both email and password")
            return
        
        self.status_label.setText("Signing in...")
        self.login_button.setEnabled(False)
        
        # Set remember session preference
        firebase_auth.remember_session = self.remember_checkbox.isChecked()
        
        # Attempt sign in
        if firebase_auth.sign_in(email, password):
            self.accept()
        else:
            self.status_label.setText("Sign in failed. Please check your credentials.")
            self.login_button.setEnabled(True)
    
    def reset_password(self):
        """Handle password reset"""
        email = self.email_edit.text().strip()

        if not email:
            self.status_label.setText("Please enter your email address")
            return

        self.status_label.setText("Sending reset email...")
        self.reset_button.setEnabled(False)

        # Attempt password reset
        if firebase_auth.reset_password(email):
            self.status_label.setText("Password reset email sent! Check your inbox.")
            QMessageBox.information(
                self, "Password Reset",
                "Password reset email has been sent to your email address.\n"
                "Please check your inbox and follow the instructions."
            )
        else:
            self.status_label.setText("Failed to send reset email. Please check your email address.")

        self.reset_button.setEnabled(True)


class ChangePasswordDialog(QDialog):
    """Dialog for changing password"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the change password dialog UI"""
        self.setWindowTitle("Change Password")
        self.setMinimumSize(350, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        self.current_password_edit = QLineEdit()
        self.current_password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Current Password:", self.current_password_edit)
        
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("New Password:", self.new_password_edit)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Confirm Password:", self.confirm_password_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.change_password)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
    def change_password(self):
        """Handle password change"""
        current = self.current_password_edit.text()
        new = self.new_password_edit.text()
        confirm = self.confirm_password_edit.text()
        
        if not all([current, new, confirm]):
            self.status_label.setText("Please fill all fields")
            return
        
        if new != confirm:
            self.status_label.setText("New passwords don't match")
            return
        
        if len(new) < 6:
            self.status_label.setText("Password must be at least 6 characters")
            return
        
        if firebase_auth.change_password(current, new):
            QMessageBox.information(self, "Success", "Password changed successfully!")
            self.accept()
        else:
            self.status_label.setText("Failed to change password. Check current password.")


class FirebaseAccountWidget(QWidget):
    """Widget for Firebase account management"""
    
    # Signals
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.current_user: Optional[FirebaseUser] = None
        self.secure_user: Optional[SecureUser] = None
        self.secure_client = None

        # Initialize secure client if available
        if SECURE_AUTH_AVAILABLE and get_secure_client:
            self.secure_client = get_secure_client()

        # Also try direct Firebase client
        if FIREBASE_AUTH_AVAILABLE and get_direct_firebase_client:
            if not self.secure_client:
                self.secure_client = get_direct_firebase_client()

        self.setup_ui()
        self.setup_connections()
        self.update_ui()
        
    def setup_ui(self):
        """Setup the Firebase account UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Firebase Status Section
        status_group = QGroupBox("Firebase Status")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Checking Firebase status...")
        status_layout.addWidget(self.status_label)

        # Add refresh button with loading state support
        refresh_layout = QHBoxLayout()

        self.refresh_button = QPushButton("🔄 Refresh Account Info")
        self.refresh_button.clicked.connect(self.refresh_account_info)
        self.refresh_button.setToolTip("Manually refresh authentication state and account information")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        refresh_layout.addWidget(self.refresh_button)
        refresh_layout.addStretch()  # Push button to the left

        status_layout.addLayout(refresh_layout)

        layout.addWidget(status_group)
        
        # Account Information Section
        self.account_group = QGroupBox("Account Information")
        account_layout = QFormLayout(self.account_group)
        
        self.uid_label = QLabel("Not signed in")
        account_layout.addRow("User ID:", self.uid_label)
        
        self.email_label = QLabel("Not signed in")
        account_layout.addRow("Email:", self.email_label)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username")
        account_layout.addRow("Username:", self.username_edit)
        
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("Enter display name")
        account_layout.addRow("Display Name:", self.display_name_edit)
        
        layout.addWidget(self.account_group)
        
        # Account Actions Section
        actions_group = QGroupBox("Account Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        # Sign out button
        self.sign_out_button = QPushButton("Sign Out")
        self.sign_out_button.clicked.connect(self.sign_out)
        actions_layout.addWidget(self.sign_out_button)
        
        # Profile update buttons
        profile_layout = QHBoxLayout()
        
        self.update_profile_button = QPushButton("Update Profile")
        self.update_profile_button.clicked.connect(self.update_profile)
        profile_layout.addWidget(self.update_profile_button)
        
        self.change_password_button = QPushButton("Change Password")
        self.change_password_button.clicked.connect(self.show_change_password_dialog)
        profile_layout.addWidget(self.change_password_button)
        
        actions_layout.addLayout(profile_layout)
        
        layout.addWidget(actions_group)
        
        # Session Settings Section
        session_group = QGroupBox("Session Settings")
        session_layout = QFormLayout(session_group)
        
        self.remember_session_checkbox = QCheckBox("Remember session on app restart")
        self.remember_session_checkbox.setChecked(firebase_auth.remember_session if firebase_auth else False)
        session_layout.addRow(self.remember_session_checkbox)
        
        layout.addWidget(session_group)
        
        layout.addStretch()
        
    def setup_connections(self):
        """Setup signal connections"""
        if firebase_auth is not None:
            try:
                firebase_auth.user_signed_in.connect(self.on_user_signed_in)
                firebase_auth.user_signed_out.connect(self.on_user_signed_out)
                firebase_auth.user_updated.connect(self.on_user_updated)
                firebase_auth.auth_error.connect(self.on_auth_error)
            except AttributeError:
                # Firebase auth doesn't have these signals
                pass

        # Connect to secure client signals if available
        if self.secure_client is not None:
            try:
                # Only connect if the signals exist
                if hasattr(self.secure_client, 'user_signed_in'):
                    self.secure_client.user_signed_in.connect(self.on_secure_user_signed_in)
                if hasattr(self.secure_client, 'user_signed_out'):
                    self.secure_client.user_signed_out.connect(self.on_secure_user_signed_out)
                if hasattr(self.secure_client, 'auth_error'):
                    self.secure_client.auth_error.connect(self.on_auth_error)
            except AttributeError:
                # Secure client doesn't have these signals
                pass

        try:
            self.remember_session_checkbox.toggled.connect(self.on_remember_session_changed)
        except AttributeError:
            # Widget might not exist yet
            pass
        
    def update_ui(self):
        """Update UI based on current state"""
        # Check if secure authentication is available
        if not SECURE_AUTH_AVAILABLE or not self.secure_client:
            self.status_label.setText("❌ Secure Firebase authentication not available")
            self.account_group.setEnabled(False)
            return

        # Check if user is authenticated via secure client
        try:
            # Get current user from secure client
            current_user = self.secure_client.current_user if self.secure_client else None

            # Convert to SecureUser format if needed
            if current_user:
                if hasattr(current_user, 'email'):
                    # Direct user object
                    self.secure_user = SecureUser(
                        uid=getattr(current_user, 'uid', getattr(current_user, 'localId', 'unknown')),
                        email=current_user.email,
                        display_name=getattr(current_user, 'display_name', getattr(current_user, 'displayName', None)),
                        email_verified=getattr(current_user, 'email_verified', getattr(current_user, 'emailVerified', False))
                    )
                elif isinstance(current_user, dict):
                    # Dictionary format from Firebase
                    self.secure_user = SecureUser(
                        uid=current_user.get('uid', current_user.get('localId', 'unknown')),
                        email=current_user.get('email', 'unknown'),
                        display_name=current_user.get('display_name', current_user.get('displayName')),
                        email_verified=current_user.get('email_verified', current_user.get('emailVerified', False))
                    )
                else:
                    self.secure_user = current_user
            else:
                self.secure_user = None

            # Check if secure client is authenticated
            is_authenticated = self.secure_client.is_authenticated() if self.secure_client else False

            if is_authenticated and self.secure_user:
                # User is authenticated via secure backend
                self.status_label.setText("✅ Firebase is available and configured (Secure Backend)")
                self.account_group.setEnabled(True)

                # Update user information
                self.uid_label.setText(self.secure_user.uid or "Unknown")
                self.email_label.setText(self.secure_user.email or "Unknown")

                # Secure user doesn't have username field, only display name
                self.username_edit.setText("")
                self.display_name_edit.setText(self.secure_user.display_name or "")

                # Enable account actions
                self.sign_out_button.setEnabled(True)
                self.update_profile_button.setEnabled(True)
                self.change_password_button.setEnabled(True)
                self.username_edit.setEnabled(False)  # Username not supported in secure mode
                self.display_name_edit.setEnabled(True)

                self.logger.info(f"Account tab updated for user: {self.secure_user.email}")

            else:
                # User is not authenticated
                self.status_label.setText("⚠️ Please sign in to view account information")
                self.account_group.setEnabled(True)  # Keep enabled so user can see the sign-in state

                # Clear user information
                self.uid_label.setText("Not signed in")
                self.email_label.setText("Not signed in")
                self.username_edit.setText("")
                self.display_name_edit.setText("")

                # Disable account actions
                self.sign_out_button.setEnabled(False)
                self.update_profile_button.setEnabled(False)
                self.change_password_button.setEnabled(False)
                self.username_edit.setEnabled(False)
                self.display_name_edit.setEnabled(False)

                self.logger.info("Account tab updated - user not signed in")

        except Exception as e:
            self.logger.error(f"Error updating account UI: {e}")
            self.status_label.setText(f"❌ Error checking authentication status: {str(e)}")
            self.account_group.setEnabled(False)
    
    def sign_out(self):
        """Sign out from Firebase and exit application"""
        reply = QMessageBox.question(
            self, "Sign Out",
            "Signing out will close the application since Firebase authentication is required.\n\n"
            "Are you sure you want to sign out?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if self.secure_client:
                    self.secure_client.sign_out()
                    QMessageBox.information(
                        self, "Signed Out",
                        "You have been signed out successfully.\nThe application will now close."
                    )
                    # Exit the application
                    from PySide6.QtWidgets import QApplication
                    QApplication.quit()
                else:
                    QMessageBox.warning(self, "Error", "Unable to sign out - secure client not available")
            except Exception as e:
                self.logger.error(f"Error during sign out: {e}")
                QMessageBox.warning(self, "Error", f"Error during sign out: {str(e)}")

    def update_profile(self):
        """Update user profile"""
        if not self.secure_user:
            QMessageBox.warning(self, "Error", "No user signed in")
            return

        display_name = self.display_name_edit.text().strip()

        try:
            # Note: Profile updates via secure backend would need to be implemented
            # For now, just show a message that this feature is not yet available
            QMessageBox.information(
                self, "Profile Update",
                "Profile updates via secure backend are not yet implemented.\n"
                "This feature will be available in a future update."
            )
            self.settings_changed.emit()
        except Exception as e:
            self.logger.error(f"Error updating profile: {e}")
            QMessageBox.warning(self, "Error", f"Failed to update profile: {str(e)}")
    
    def show_change_password_dialog(self):
        """Show change password dialog"""
        dialog = ChangePasswordDialog(self)
        dialog.exec()

    def refresh_account_info(self):
        """Manually refresh authentication state and account information"""
        try:
            # Show loading state
            original_text = self.refresh_button.text()
            self.refresh_button.setText("🔄 Refreshing...")
            self.refresh_button.setEnabled(False)
            self.status_label.setText("🔄 Refreshing authentication state...")

            # Process events to update UI immediately
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()

            self.logger.info("Manual refresh of account information requested")

            # Add a small delay to show the loading state (optional, for better UX)
            import time
            time.sleep(0.5)

            # Perform the actual refresh by calling update_ui
            self.update_ui()

            # Show success feedback
            if self.secure_client and self.secure_client.is_authenticated():
                self.logger.info("Account information refreshed successfully")
                # Briefly show success message
                self.status_label.setText("✅ Account information refreshed successfully")
                QApplication.processEvents()
                time.sleep(1)
                # Then update to normal status
                self.update_ui()
            else:
                self.logger.info("Account refresh completed - user not authenticated")

        except Exception as e:
            self.logger.error(f"Error refreshing account info: {e}")
            self.status_label.setText(f"❌ Error refreshing account: {str(e)}")

        finally:
            # Restore button state
            self.refresh_button.setText(original_text)
            self.refresh_button.setEnabled(True)

    def on_user_signed_in(self, user: FirebaseUser):
        """Handle user signed in"""
        self.current_user = user
        self.update_ui()
    
    def on_user_signed_out(self):
        """Handle user signed out"""
        self.current_user = None
        self.update_ui()
    
    def on_user_updated(self, user: FirebaseUser):
        """Handle user updated"""
        self.current_user = user
        self.update_ui()
    
    def on_auth_error(self, error: str):
        """Handle authentication error"""
        QMessageBox.warning(self, "Authentication Error", error)
    
    def on_remember_session_changed(self, checked: bool):
        """Handle remember session setting change"""
        if firebase_auth is not None:
            firebase_auth.remember_session = checked
        self.settings_changed.emit()

    def on_secure_user_signed_in(self, user):
        """Handle secure user signed in"""
        # Convert user data to SecureUser if needed
        if hasattr(user, 'email'):
            # Direct user object
            self.secure_user = SecureUser(
                uid=getattr(user, 'uid', getattr(user, 'localId', 'unknown')),
                email=user.email,
                display_name=getattr(user, 'display_name', getattr(user, 'displayName', None)),
                email_verified=getattr(user, 'email_verified', getattr(user, 'emailVerified', False))
            )
        elif isinstance(user, dict):
            # Dictionary format from Firebase
            self.secure_user = SecureUser(
                uid=user.get('uid', user.get('localId', 'unknown')),
                email=user.get('email', 'unknown'),
                display_name=user.get('display_name', user.get('displayName')),
                email_verified=user.get('email_verified', user.get('emailVerified', False))
            )
        else:
            self.secure_user = user

        self.update_ui()
        self.logger.info(f"Secure user signed in: {self.secure_user.email if self.secure_user else 'Unknown'}")

    def on_secure_user_signed_out(self):
        """Handle secure user signed out"""
        self.secure_user = None
        self.update_ui()
        self.logger.info("Secure user signed out")
