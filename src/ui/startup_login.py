"""
Startup Login Dialog

This module provides a mandatory login dialog that appears before the application starts.
Users must authenticate with Firebase before accessing the application.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox,
    QProgressBar, QFrame, QApplication, QTabWidget, QWidget,
    QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QKeySequence, QShortcut

from ..core.secure_config import is_firebase_configured
from ..core.direct_firebase_client import get_direct_firebase_client

# Simple user class to replace SecureUser
class SimpleUser:
    def __init__(self, uid, email, display_name=None, email_verified=False):
        self.uid = uid
        self.email = email
        self.display_name = display_name
        self.email_verified = email_verified


class AuthenticationWorker(QObject):
    """Worker thread for Firebase authentication to prevent UI blocking"""

    # Signals
    auth_success = Signal(SimpleUser)
    auth_failed = Signal(str)
    reset_success = Signal()
    reset_failed = Signal(str)
    phone_verification_sent = Signal(str)  # verification_id
    phone_auth_success = Signal(SimpleUser)
    phone_auth_failed = Signal(str)
    finished = Signal()  # Required for QThread cleanup

    def __init__(self, remember_session: bool = True):
        super().__init__()
        self.email = ""
        self.password = ""
        self.phone_number = ""
        self.verification_code = ""
        self.verification_id = ""
        self.operation = ""
        self.remember_session = remember_session
        self.firebase_client = get_direct_firebase_client()
        # Apply the remember_session setting to the Firebase client
        self.firebase_client.remember_session = self.remember_session

    def set_login_data(self, email: str, password: str):
        """Set email login credentials"""
        self.email = email
        self.password = password
        self.operation = "email_login"

    def set_phone_login_data(self, phone_number: str):
        """Set phone login data"""
        self.phone_number = phone_number
        self.operation = "phone_login"

    def set_phone_verification_data(self, verification_id: str, verification_code: str):
        """Set phone verification data"""
        self.verification_id = verification_id
        self.verification_code = verification_code
        self.operation = "phone_verify"

    def set_reset_data(self, email: str):
        """Set reset email"""
        self.email = email
        self.operation = "reset"

    def run(self):
        """Execute the authentication operation"""
        try:
            if self.operation == "email_login":
                from ..core.direct_firebase_client import get_direct_firebase_client
                firebase_client = get_direct_firebase_client()

                # CRITICAL FIX: Apply remember_session setting before authentication
                firebase_client.remember_session = self.remember_session
                self.logger.info(f"Applied remember_session setting: {self.remember_session}")

                success, message = firebase_client.sign_in_with_email_password(self.email, self.password)
                if success:
                    # Create a simple user object for the signal
                    user = SimpleUser(
                        uid=firebase_client.current_user.get('localId', ''),
                        email=self.email,
                        display_name=firebase_client.current_user.get('displayName', ''),
                        email_verified=firebase_client.current_user.get('emailVerified', False)
                    )
                    self.auth_success.emit(user)
                else:
                    self.auth_failed.emit(message)
            elif self.operation == "phone_login":
                # For phone authentication, we'll simulate the process
                # In a real implementation, you'd use Firebase Phone Auth
                verification_id = self._send_phone_verification(self.phone_number)
                if verification_id:
                    self.phone_verification_sent.emit(verification_id)
                else:
                    self.phone_auth_failed.emit("Failed to send verification code")
            elif self.operation == "phone_verify":
                if self._verify_phone_code(self.verification_id, self.verification_code):
                    # Create a dummy user for phone auth (simplified for demo)
                    dummy_user = SimpleUser(uid="phone_user", email=self.phone_number)
                    self.phone_auth_success.emit(dummy_user)
                else:
                    self.phone_auth_failed.emit("Invalid verification code")
            elif self.operation == "reset":
                # Password reset functionality would need to be implemented in direct Firebase client
                self.reset_failed.emit("Password reset not implemented in direct Firebase mode")
        except Exception as e:
            if self.operation in ["email_login", "phone_login", "phone_verify"]:
                self.auth_failed.emit(str(e))
            else:
                self.reset_failed.emit(str(e))
        finally:
            # Ensure the thread can be properly cleaned up
            self.finished.emit()

    def _send_phone_verification(self, phone_number: str) -> str:
        """Send phone verification code (simplified for demo)"""
        try:
            # In production, implement phone auth through Replit backend
            # For now, return a dummy verification ID
            return f"demo_verification_{phone_number}"
        except Exception as e:
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
            self.logger.error(f"Error sending phone verification: {e}")
            return None

    def _verify_phone_code(self, verification_id: str, code: str) -> bool:
        """Verify phone verification code (simplified for demo)"""
        try:
            # In production, implement phone auth verification through Replit backend
            # For demo, accept code "123456"
            return code == "123456"
        except Exception as e:
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
            self.logger.error(f"Error verifying phone code: {e}")
            return False


class StartupLoginDialog(QDialog):
    """Mandatory login dialog for application startup"""
    
    # Signals
    login_successful = Signal(SimpleUser)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.auth_worker = None
        self.auth_thread = None
        self.firebase_client = get_direct_firebase_client()
        self.setup_ui()
        self.setup_connections()
        self.check_firebase_availability()
        
        # Make dialog modal and prevent closing without authentication
        self.setModal(True)
        # Ensure authentication dialog appears on top of loading screen
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
    def setup_ui(self):
        """Setup the login dialog UI"""
        self.setWindowTitle("Firebase Authentication Required")
        self.setMinimumSize(500, 450)
        self.setMaximumSize(500, 450)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header section
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)

        # App title
        title_label = QLabel("Personal Finance Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Choose your sign-in method")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: gray;")
        header_layout.addWidget(subtitle_label)

        layout.addWidget(header_frame)

        # Firebase status
        self.status_frame = QFrame()
        status_layout = QVBoxLayout(self.status_frame)

        self.firebase_status_label = QLabel("Checking Firebase connection...")
        self.firebase_status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.firebase_status_label)

        layout.addWidget(self.status_frame)

        # Tab widget for different authentication methods
        self.auth_tabs = QTabWidget()

        # Email/Password tab
        self.email_tab = self.create_email_tab()
        self.auth_tabs.addTab(self.email_tab, "Email & Password")

        # Phone number tab
        self.phone_tab = self.create_phone_tab()
        self.auth_tabs.addTab(self.phone_tab, "Phone Number")

        layout.addWidget(self.auth_tabs)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Global buttons
        button_layout = QHBoxLayout()

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.on_exit_clicked)
        button_layout.addWidget(self.exit_button)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Status message
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

        # Enable auth tabs by default so users can always see the login interface
        self.auth_tabs.setEnabled(True)

        # Force layout update after UI setup
        QTimer.singleShot(50, self.force_layout_update)

    def create_email_tab(self):
        """Create email/password authentication tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Email form
        form_layout = QFormLayout()

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter your email address")
        self.email_edit.returnPressed.connect(self.on_email_login_clicked)
        form_layout.addRow("Email:", self.email_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.returnPressed.connect(self.on_email_login_clicked)
        form_layout.addRow("Password:", self.password_edit)

        layout.addLayout(form_layout)

        # Remember session
        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setChecked(True)
        layout.addWidget(self.remember_checkbox)

        # Buttons
        button_layout = QHBoxLayout()

        self.reset_button = QPushButton("Reset Password")
        self.reset_button.clicked.connect(self.on_reset_clicked)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()

        self.email_login_button = QPushButton("Sign In with Email")
        self.email_login_button.setDefault(True)
        self.email_login_button.clicked.connect(self.on_email_login_clicked)
        # Make sure the button is visible and enabled
        self.email_login_button.setVisible(True)
        self.email_login_button.setEnabled(True)
        self.email_login_button.setMinimumHeight(35)  # Ensure minimum height
        self.email_login_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        button_layout.addWidget(self.email_login_button)

        layout.addLayout(button_layout)
        layout.addStretch()

        # Ensure the tab and all its widgets are visible
        tab.setVisible(True)
        tab.show()

        # Force layout update
        tab.updateGeometry()
        tab.update()

        return tab

    def create_phone_tab(self):
        """Create phone number authentication tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Phone form
        form_layout = QFormLayout()

        # Country code selection
        phone_layout = QHBoxLayout()

        self.country_combo = QComboBox()
        self.country_combo.addItems([
            "+91 (India)", "+1 (USA/Canada)", "+44 (UK)", "+61 (Australia)",
            "+49 (Germany)", "+33 (France)", "+81 (Japan)", "+86 (China)",
            "+55 (Brazil)", "+7 (Russia)"
        ])
        self.country_combo.setCurrentText("+91 (India)")
        phone_layout.addWidget(self.country_combo)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Enter your phone number")
        self.phone_edit.returnPressed.connect(self.on_phone_login_clicked)
        phone_layout.addWidget(self.phone_edit)

        form_layout.addRow("Phone:", phone_layout)

        # Verification code (initially hidden)
        self.verification_edit = QLineEdit()
        self.verification_edit.setPlaceholderText("Enter 6-digit verification code")
        self.verification_edit.setMaxLength(6)
        self.verification_edit.returnPressed.connect(self.on_verify_phone_clicked)
        self.verification_edit.setVisible(False)

        self.verification_label = QLabel("Verification Code:")
        self.verification_label.setVisible(False)

        form_layout.addRow(self.verification_label, self.verification_edit)

        layout.addLayout(form_layout)

        # Instructions
        self.phone_instructions = QLabel(
            "You will receive a 6-digit verification code via SMS.\n"
            "Standard messaging rates may apply."
        )
        self.phone_instructions.setWordWrap(True)
        self.phone_instructions.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(self.phone_instructions)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.phone_login_button = QPushButton("Send Verification Code")
        self.phone_login_button.clicked.connect(self.on_phone_login_clicked)
        # Make sure the button is visible and styled
        self.phone_login_button.setVisible(True)
        self.phone_login_button.setEnabled(True)
        self.phone_login_button.setMinimumHeight(35)
        self.phone_login_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        button_layout.addWidget(self.phone_login_button)

        self.verify_button = QPushButton("Verify & Sign In")
        self.verify_button.clicked.connect(self.on_verify_phone_clicked)
        self.verify_button.setVisible(False)
        self.verify_button.setMinimumHeight(35)
        self.verify_button.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1E7E34;
            }
        """)
        button_layout.addWidget(self.verify_button)

        layout.addLayout(button_layout)
        layout.addStretch()

        # Ensure the tab and all its widgets are visible
        tab.setVisible(True)
        tab.show()

        # Force layout update
        tab.updateGeometry()
        tab.update()

        return tab

    def setup_connections(self):
        """Setup signal connections"""
        # Firebase client signals would need to be implemented if needed
        # For now, authentication is handled directly in the worker thread

        # Backend selection removed - now using Firebase only

        # Register for service discovery failover notifications
        self.setup_failover_monitoring()

        # Note: Phone auth is simplified for this demo
        # In production, you'd implement proper phone auth through the Replit backend

        # Store verification ID for phone auth
        self.verification_id = None

    def setup_failover_monitoring(self):
        """Setup monitoring for service discovery failover events - DISABLED (Firebase only)"""
        # Service discovery removed - using Firebase direct integration only
        self.logger.info("Failover monitoring disabled - using Firebase direct integration")

    def on_failover_occurred(self, old_endpoint, new_endpoint):
        """Handle automatic failover events from service discovery"""
        try:
            old_name = old_endpoint.name if old_endpoint else "unknown"
            new_name = new_endpoint.name if new_endpoint else "unknown"

            self.logger.info(f"Automatic failover detected: {old_name} -> {new_name}")

            # Refresh status display in the main thread
            QTimer.singleShot(100, self.refresh_backend_status)

        except Exception as e:
            self.logger.error(f"Error handling failover event: {e}")

    def refresh_backend_status(self):
        """Refresh the backend status display"""
        try:
            self.logger.info("Refreshing backend status display")
            # Use the existing check method but with a short delay to ensure service discovery is updated
            QTimer.singleShot(200, self._check_firebase_status)

        except Exception as e:
            self.logger.error(f"Error refreshing backend status: {e}")
        
    def force_layout_update(self):
        """Force layout update to ensure all widgets are visible"""
        try:
            # Force update of all tabs
            for i in range(self.auth_tabs.count()):
                tab = self.auth_tabs.widget(i)
                if tab:
                    tab.updateGeometry()
                    tab.update()

            # Force update of the main dialog
            self.updateGeometry()
            self.update()
            self.repaint()

            # Ensure email login button is visible
            if hasattr(self, 'email_login_button'):
                self.email_login_button.setVisible(True)
                self.email_login_button.show()
                self.email_login_button.raise_()

            # Ensure phone login buttons are visible
            if hasattr(self, 'phone_login_button'):
                self.phone_login_button.setVisible(True)
                self.phone_login_button.show()
                self.phone_login_button.raise_()

            if hasattr(self, 'verify_button'):
                # verify_button should be hidden initially
                self.verify_button.show()  # Make sure it can be shown when needed

        except Exception as e:
            self.logger.error(f"Error in force_layout_update: {e}")

    def check_firebase_availability(self):
        """Check if Firebase is available and configured"""
        QTimer.singleShot(100, self._check_firebase_status)
        
    def _check_firebase_status(self):
        """Internal method to check secure backend status"""
        try:
            if not is_firebase_configured():
                self.firebase_status_label.setText("⚠️ Backend not configured")
                self.firebase_status_label.setStyleSheet("color: orange;")
                # Still enable auth tabs so user can see the interface
                self.auth_tabs.setEnabled(True)
                self.message_label.setText("Backend not configured, but you can see the interface")
                return

            # Firebase direct connection test (service discovery removed)
            try:
                # Simple Firebase connection test - just enable the interface
                self.firebase_status_label.setText("✅ Firebase backend ready")
                self.firebase_status_label.setStyleSheet("color: green;")
                self.auth_tabs.setEnabled(True)
                self.message_label.setText("Please choose your sign-in method")

                # Check for saved session
                self.check_saved_session()
            except Exception as conn_error:
                self.firebase_status_label.setText("❌ Backend connection failed")
                self.firebase_status_label.setStyleSheet("color: red;")
                # Still enable auth tabs so user can try to login
                self.auth_tabs.setEnabled(True)
                self.message_label.setText(f"Backend error: {str(conn_error)}, but you can still try to sign in")

        except Exception as e:
            self.logger.error(f"Error checking backend status: {e}")
            self.firebase_status_label.setText("❌ Backend error")
            self.firebase_status_label.setStyleSheet("color: red;")
            self.show_error(f"Backend error: {str(e)}")
    
    def check_saved_session(self):
        """Check if there's a saved session to restore"""
        self.logger.info("Checking for saved session...")
        try:
            # Check if user is already authenticated with Firebase client
            if self.firebase_client.is_authenticated():
                self.logger.info("Found saved session")
                self.message_label.setText("Restoring previous session...")
                self.message_label.setStyleSheet("color: blue;")

                # Create user object for the session
                user = SimpleUser(
                    uid=self.firebase_client.current_user.get('localId', ''),
                    email=self.firebase_client.current_user.get('email', ''),
                    display_name=self.firebase_client.current_user.get('displayName', ''),
                    email_verified=self.firebase_client.current_user.get('emailVerified', False)
                )

                self.logger.info("Saved session is valid, auto-logging in")
                self.login_successful.emit(user)
                self.accept()
            else:
                self.logger.info("No saved session found or user not authenticated")
                self.message_label.setText("Please sign in to continue")
        except Exception as e:
            self.logger.error(f"Error checking saved session: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.message_label.setText("Please sign in to continue")
    
    def on_email_login_clicked(self):
        """Handle email login button click"""
        email = self.email_edit.text().strip()
        password = self.password_edit.text()

        if not email or not password:
            self.show_message("Please enter both email and password", "orange")
            return

        # Start email authentication in background thread
        # (Remember Me setting is now handled in AuthenticationWorker)
        self.start_email_authentication(email, password)

    def on_phone_login_clicked(self):
        """Handle phone login button click"""
        country_code = self.country_combo.currentText().split()[0]  # Extract +XX
        phone_number = self.phone_edit.text().strip()

        if not phone_number:
            self.show_message("Please enter your phone number", "orange")
            return

        # Format phone number
        full_phone = f"{country_code}{phone_number}"

        # Start phone authentication
        # (Remember Me setting is now handled in AuthenticationWorker)
        self.start_phone_authentication(full_phone)

    def on_verify_phone_clicked(self):
        """Handle phone verification button click"""
        verification_code = self.verification_edit.text().strip()

        if not verification_code or len(verification_code) != 6:
            self.show_message("Please enter the 6-digit verification code", "orange")
            return

        if not self.verification_id:
            self.show_message("No verification ID available. Please request a new code.", "red")
            return

        # Verify phone code
        # (Remember Me setting is now handled in AuthenticationWorker)
        self.verify_phone_code(self.verification_id, verification_code)
    
    def on_reset_clicked(self):
        """Handle reset password button click"""
        email = self.email_edit.text().strip()
        
        if not email:
            self.show_message("Please enter your email address first", "orange")
            self.email_edit.setFocus()
            return
        
        # Confirm reset
        reply = QMessageBox.question(
            self, "Reset Password",
            f"Send password reset email to:\n{email}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.start_password_reset(email)
    
    def on_exit_clicked(self):
        """Handle exit button click"""
        reply = QMessageBox.question(
            self, "Exit Application",
            "Are you sure you want to exit?\nThe application requires Firebase authentication to run.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Reject the dialog to indicate user wants to exit
            self.reject()
            # Force application exit
            QApplication.instance().quit()
            import sys
            sys.exit(0)
    
    def start_email_authentication(self, email: str, password: str):
        """Start email authentication in background thread"""
        self.set_ui_busy(True, "Signing in with email...")

        # Clean up any existing thread
        self.cleanup_auth_thread()

        # Create worker and thread with remember_session setting
        remember_checked = self.remember_checkbox.isChecked()
        self.auth_worker = AuthenticationWorker(remember_session=remember_checked)
        self.auth_thread = QThread()

        # Move worker to thread
        self.auth_worker.moveToThread(self.auth_thread)

        # Connect signals
        self.auth_worker.auth_success.connect(self.on_auth_success)
        self.auth_worker.auth_failed.connect(self.on_auth_failure)
        self.auth_thread.started.connect(self.auth_worker.run)
        self.auth_thread.finished.connect(self.auth_thread.deleteLater)
        self.auth_worker.finished.connect(self.auth_thread.quit)
        self.auth_worker.auth_success.connect(self.cleanup_auth_thread)
        self.auth_worker.auth_failed.connect(self.cleanup_auth_thread)

        # Set login data and start
        self.auth_worker.set_login_data(email, password)
        self.auth_thread.start()

    def _send_phone_verification(self, phone_number: str) -> str:
        """Send phone verification code (simplified for demo)"""
        try:
            # In production, implement phone auth through Replit backend
            # For now, return a dummy verification ID
            return f"demo_verification_{phone_number}"
        except Exception as e:
            self.logger.error(f"Error sending phone verification: {e}")
            return None

    def _verify_phone_code(self, verification_id: str, code: str) -> bool:
        """Verify phone verification code (simplified for demo)"""
        try:
            # In production, implement phone auth verification through Replit backend
            # For demo, accept code "123456"
            return code == "123456"
        except Exception as e:
            self.logger.error(f"Error verifying phone code: {e}")
            return False

    def start_phone_authentication(self, phone_number: str):
        """Start phone authentication (simplified for demo)"""
        self.set_ui_busy(True, "Sending verification code...")

        # Simplified phone auth for demo
        verification_id = self._send_phone_verification(phone_number)

        if verification_id:
            self.verification_id = verification_id
            self.on_phone_verification_sent(verification_id)
        else:
            self.set_ui_busy(False)
            self.show_error("Failed to send verification code")

    def verify_phone_code(self, verification_id: str, code: str):
        """Verify phone verification code (simplified for demo)"""
        self.set_ui_busy(True, "Verifying code...")

        # Simplified phone auth verification
        success = self._verify_phone_code(verification_id, code)

        if success:
            # Create a demo user for phone auth
            demo_user = SimpleUser(uid="phone_user", email=f"phone_{verification_id}@demo.com")
            self.on_phone_auth_success(demo_user)
        else:
            self.set_ui_busy(False)
            self.show_error("Invalid verification code. Try '123456' for demo.")
    
    def start_password_reset(self, email: str):
        """Start password reset in background thread"""
        self.set_ui_busy(True, "Sending reset email...")

        # Clean up any existing thread
        self.cleanup_auth_thread()

        # Create worker and thread with remember_session setting
        remember_checked = self.remember_checkbox.isChecked()
        self.auth_worker = AuthenticationWorker(remember_session=remember_checked)
        self.auth_thread = QThread()

        # Move worker to thread
        self.auth_worker.moveToThread(self.auth_thread)

        # Connect signals
        self.auth_worker.reset_success.connect(self.on_reset_success)
        self.auth_worker.reset_failed.connect(self.on_reset_failure)
        self.auth_thread.started.connect(self.auth_worker.run)
        self.auth_thread.finished.connect(self.auth_thread.deleteLater)
        self.auth_worker.finished.connect(self.auth_thread.quit)
        self.auth_worker.reset_success.connect(self.cleanup_auth_thread)
        self.auth_worker.reset_failed.connect(self.cleanup_auth_thread)
        
        # Set reset data and start
        self.auth_worker.set_reset_data(email)
        self.auth_thread.start()
    
    def set_ui_busy(self, busy: bool, message: str = ""):
        """Set UI to busy state during authentication"""
        # Disable/enable all authentication controls
        self.auth_tabs.setEnabled(not busy)
        self.exit_button.setEnabled(not busy)

        if busy:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.show_message(message, "blue")
        else:
            self.progress_bar.setVisible(False)
    
    def show_message(self, message: str, color: str = "black"):
        """Show a status message"""
        self.message_label.setText(message)
        self.message_label.setStyleSheet(f"color: {color};")
    
    def show_error(self, message: str):
        """Show an error message"""
        self.show_message(message, "red")
        QMessageBox.critical(self, "Authentication Error", message)
    
    def on_auth_success(self, user: SimpleUser):
        """Handle successful authentication"""
        self.set_ui_busy(False)
        self.show_message(f"Welcome, {user.email}!", "green")

        # Verify session was saved if remember_session is enabled
        if self.firebase_client.remember_session:
            if self.firebase_client.session_file.exists():
                self.logger.info("✅ Session file created successfully after authentication")
            else:
                self.logger.warning("⚠️ Session file was not created despite remember_session being enabled")

        # Emit success signal and close dialog
        QTimer.singleShot(1000, lambda: self.login_successful.emit(user))
        QTimer.singleShot(1000, self.accept)
    
    def on_auth_failure(self, error: str):
        """Handle authentication failure"""
        self.set_ui_busy(False)
        self.show_error(f"Sign in failed: {error}")
        if hasattr(self, 'password_edit'):
            self.password_edit.clear()
            self.password_edit.setFocus()

    def on_phone_verification_sent(self, verification_id: str):
        """Handle phone verification code sent"""
        self.set_ui_busy(False)
        self.verification_id = verification_id

        # Show verification code input
        self.verification_label.setVisible(True)
        self.verification_edit.setVisible(True)
        self.verify_button.setVisible(True)
        self.phone_login_button.setText("Resend Code")

        self.show_message(
            f"Verification code sent! Enter the 6-digit code.\n"
            f"For testing, use: 123456",
            "green"
        )
        self.verification_edit.setFocus()

    def on_phone_auth_success(self, user: SimpleUser):
        """Handle successful phone authentication"""
        self.set_ui_busy(False)

        # Note: Session management is handled by the secure client
        self.show_message(f"Welcome, {user.email}!", "green")

        # Emit success signal and close dialog
        QTimer.singleShot(1000, lambda: self.login_successful.emit(user))
        QTimer.singleShot(1000, self.accept)

    def on_phone_auth_failure(self, error: str):
        """Handle phone authentication failure"""
        self.set_ui_busy(False)
        self.show_error(f"Phone authentication failed: {error}")
        if hasattr(self, 'verification_edit'):
            self.verification_edit.clear()
            self.verification_edit.setFocus()
    
    def on_reset_success(self):
        """Handle successful password reset"""
        self.set_ui_busy(False)
        self.show_message("Password reset email sent! Check your inbox.", "green")
        QMessageBox.information(
            self, "Password Reset",
            "Password reset email has been sent to your email address.\n"
            "Please check your inbox and follow the instructions to reset your password."
        )
    
    def on_reset_failure(self, error: str):
        """Handle password reset failure"""
        self.set_ui_busy(False)
        self.show_error(f"Password reset failed: {error}")
    
    def on_user_signed_in(self, user: SimpleUser):
        """Handle user signed in signal from auth manager"""
        self.login_successful.emit(user)
        self.accept()
    
    def on_auth_error(self, error: str):
        """Handle auth error signal from auth manager"""
        self.show_error(error)
    
    def cleanup_auth_thread(self):
        """Clean up authentication thread and worker"""
        try:
            if self.auth_thread and self.auth_thread.isRunning():
                self.logger.debug("Stopping authentication thread...")
                self.auth_thread.quit()
                if not self.auth_thread.wait(5000):  # Wait up to 5 seconds
                    self.logger.warning("Authentication thread did not stop gracefully, terminating...")
                    self.auth_thread.terminate()
                    self.auth_thread.wait(2000)  # Wait for termination

            if self.auth_worker:
                self.logger.debug("Cleaning up authentication worker...")
                self.auth_worker.deleteLater()
                self.auth_worker = None

            if self.auth_thread:
                self.logger.debug("Cleaning up authentication thread...")
                self.auth_thread.deleteLater()
                self.auth_thread = None

            self.logger.debug("Authentication thread cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during auth thread cleanup: {e}")

    def closeEvent(self, event):
        """Handle close event - prevent closing without authentication"""
        # Clean up threads before closing
        self.cleanup_auth_thread()

        if not self.firebase_client.is_authenticated():
            reply = QMessageBox.question(
                self, "Exit Application",
                "Authentication is required to use this application.\n"
                "Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Accept the close event first
                event.accept()
                # Force application exit
                QApplication.instance().quit()
                import sys
                sys.exit(0)
            else:
                event.ignore()
        else:
            event.accept()

    # Backend selection methods removed - now using Firebase only

        # Show a subtle notification
        QMessageBox.information(
            self,
            "Backend Changed",
            f"Authentication backend switched to: {backend_name}\n"
            "New login attempts will use the selected backend."
        )
