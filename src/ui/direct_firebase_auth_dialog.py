"""
Direct Firebase Authentication Dialog

This dialog provides authentication for direct Firebase access.
"""

import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QPushButton, QLabel, QMessageBox, 
                               QCheckBox, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont


class FirebaseAuthWorker(QThread):
    """Worker thread for Firebase authentication"""
    
    auth_success = Signal(str)  # email
    auth_failed = Signal(str)   # error message
    
    def __init__(self, firebase_client, email, password):
        super().__init__()
        self.firebase_client = firebase_client
        self.email = email
        self.password = password
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def run(self):
        """Perform authentication in background thread"""
        try:
            success, message = self.firebase_client.sign_in_with_email_password(self.email, self.password)
            
            if success:
                self.auth_success.emit(self.email)
            else:
                self.auth_failed.emit(message)
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            self.auth_failed.emit(str(e))


class DirectFirebaseAuthDialog(QDialog):
    """Dialog for direct Firebase authentication"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Get Firebase client
        from ..core.direct_firebase_client import get_direct_firebase_client
        self.firebase_client = get_direct_firebase_client()
        
        self.auth_worker = None
        self.setup_ui()
        self.setup_connections()
        
        # Check if already authenticated
        if self.firebase_client.is_authenticated():
            self.accept()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Firebase Authentication")
        self.setMinimumSize(400, 300)
        self.setModal(True)
        # Ensure authentication dialog appears on top of loading screen
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Sign in to Firebase")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Direct Firebase Realtime Database Access")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: gray; margin-bottom: 20px;")
        layout.addWidget(subtitle_label)
        
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
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: blue; margin: 10px;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.sign_in_button = QPushButton("Sign In")
        self.sign_in_button.setDefault(True)
        button_layout.addWidget(self.sign_in_button)
        
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.sign_in_button.clicked.connect(self.sign_in)
        self.cancel_button.clicked.connect(self.reject)
        self.password_edit.returnPressed.connect(self.sign_in)
    
    def sign_in(self):
        """Perform sign in"""
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both email and password.")
            return
        
        # Apply Remember Me checkbox setting to Firebase client
        remember_checked = self.remember_checkbox.isChecked()
        self.firebase_client.remember_session = remember_checked
        self.logger.info(f"🔧 Applied remember_session setting: {remember_checked}")
        self.logger.info(f"🔧 Firebase client remember_session is now: {self.firebase_client.remember_session}")

        # Disable UI during authentication
        self.sign_in_button.setEnabled(False)
        self.email_edit.setEnabled(False)
        self.password_edit.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Signing in...")

        # Start authentication in background thread
        self.auth_worker = FirebaseAuthWorker(self.firebase_client, email, password)
        self.auth_worker.auth_success.connect(self.on_auth_success)
        self.auth_worker.auth_failed.connect(self.on_auth_failed)
        self.auth_worker.start()
    
    def on_auth_success(self, email):
        """Handle successful authentication"""
        self.logger.info(f"Authentication successful for: {email}")

        # Verify session was saved if remember_session is enabled
        if self.firebase_client.remember_session:
            if self.firebase_client.session_file.exists():
                self.logger.info("✅ Session file created successfully after authentication")
            else:
                self.logger.warning("⚠️ Session file was not created despite remember_session being enabled")

        # Re-enable UI
        self.sign_in_button.setEnabled(True)
        self.email_edit.setEnabled(True)
        self.password_edit.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Authentication successful!")
        self.status_label.setStyleSheet("color: green; margin: 10px;")

        # Close dialog with success
        self.accept()
    
    def on_auth_failed(self, error_message):
        """Handle authentication failure"""
        self.logger.error(f"Authentication failed: {error_message}")
        
        # Re-enable UI
        self.sign_in_button.setEnabled(True)
        self.email_edit.setEnabled(True)
        self.password_edit.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Authentication failed")
        self.status_label.setStyleSheet("color: red; margin: 10px;")
        
        # Show error message
        QMessageBox.critical(self, "Authentication Failed", 
                           f"Failed to sign in:\n\n{error_message}")
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.auth_worker and self.auth_worker.isRunning():
            self.auth_worker.terminate()
            self.auth_worker.wait()
        event.accept()


def show_direct_firebase_auth_dialog(parent=None) -> bool:
    """Show direct Firebase authentication dialog and return success status"""
    dialog = DirectFirebaseAuthDialog(parent)
    result = dialog.exec()
    return result == QDialog.Accepted
