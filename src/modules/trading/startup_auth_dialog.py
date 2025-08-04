"""
Zerodha Startup Authentication Dialog
Provides user education and optional authentication during application startup
"""

import logging
from datetime import datetime, time
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QTextEdit, QCheckBox, QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon

class ZerodhaStartupDialog(QDialog):
    """Startup dialog for Zerodha authentication with user education"""
    
    # Signals
    connect_now_requested = Signal()
    connect_later_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.user_choice = None
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Zerodha Trading Connection")
        self.setModal(True)
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header section
        self.create_header(layout)
        
        # Information section
        self.create_info_section(layout)
        
        # Token status section
        self.create_token_status_section(layout)
        
        # Options section
        self.create_options_section(layout)
        
        # Buttons section
        self.create_buttons_section(layout)
        
    def create_header(self, layout):
        """Create header with title and icon"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("Zerodha Trading Connection")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2E86AB; margin-bottom: 10px;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("⚠️ Not Connected")
        self.status_label.setStyleSheet("color: #F24236; font-weight: bold;")
        header_layout.addWidget(self.status_label)
        
        layout.addWidget(header_frame)
        
    def create_info_section(self, layout):
        """Create information section explaining Zerodha limitations"""
        info_group = QGroupBox("📚 Important Information")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3e3e42;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #252526;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
        """)
        
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setStyleSheet("""
            QTextEdit {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 10px;
                font-size: 11px;
            }
        """)
        
        info_content = """
<b>🔐 Zerodha API Token Limitations:</b><br>
• Access tokens are valid for <b>one trading day only</b> (expire around 6:00 AM next day)<br>
• Tokens <b>cannot be automatically refreshed</b> - this is a Zerodha API limitation<br>
• <b>Daily re-authentication is required</b> for trading functionality<br>
• Other app features (expenses, bank analysis) work independently of trading connection<br><br>

<b>💡 What this means:</b><br>
• You can skip authentication now and connect later when ready to trade<br>
• The application will work normally for all non-trading features<br>
• When you're ready to trade, simply go to the Trading tab and connect
        """
        
        info_text.setHtml(info_content)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
    def create_token_status_section(self, layout):
        """Create token status section"""
        status_group = QGroupBox("🕐 Token Status")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E8E8E8;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        status_layout = QVBoxLayout(status_group)
        
        # Current time
        current_time = datetime.now()
        time_label = QLabel(f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        time_label.setStyleSheet("font-size: 11px; color: #666;")
        status_layout.addWidget(time_label)
        
        # Token expiry info
        self.token_status_label = QLabel("No active token found")
        self.token_status_label.setStyleSheet("font-size: 11px; color: #F24236; font-weight: bold;")
        status_layout.addWidget(self.token_status_label)
        
        # Next expiry estimate
        next_expiry = current_time.replace(hour=6, minute=0, second=0, microsecond=0)
        if current_time.hour >= 6:
            next_expiry = next_expiry.replace(day=next_expiry.day + 1)
            
        expiry_label = QLabel(f"Next token expiry (estimated): {next_expiry.strftime('%Y-%m-%d 06:00:00')}")
        expiry_label.setStyleSheet("font-size: 10px; color: #888;")
        status_layout.addWidget(expiry_label)
        
        layout.addWidget(status_group)
        
    def create_options_section(self, layout):
        """Create options section"""
        options_frame = QFrame()
        options_layout = QVBoxLayout(options_frame)
        
        # Remember choice checkbox
        self.remember_choice_cb = QCheckBox("Remember my choice for today")
        self.remember_choice_cb.setToolTip("Skip this dialog for the rest of today's session")
        options_layout.addWidget(self.remember_choice_cb)
        
        layout.addWidget(options_frame)
        
    def create_buttons_section(self, layout):
        """Create buttons section"""
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        
        # Connect Now button
        self.connect_now_btn = QPushButton("🔗 Connect Now")
        self.connect_now_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1E7E34;
            }
        """)
        self.connect_now_btn.setToolTip("Start Zerodha authentication process now")
        
        # Connect Later button
        self.connect_later_btn = QPushButton("⏰ Connect Later")
        self.connect_later_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
            QPushButton:pressed {
                background-color: #545B62;
            }
        """)
        self.connect_later_btn.setToolTip("Skip authentication and connect later from Trading tab")
        
        buttons_layout.addWidget(self.connect_now_btn)
        buttons_layout.addWidget(self.connect_later_btn)
        
        layout.addWidget(buttons_frame)
        
    def setup_connections(self):
        """Setup signal connections"""
        self.connect_now_btn.clicked.connect(self.on_connect_now)
        self.connect_later_btn.clicked.connect(self.on_connect_later)
        
    def on_connect_now(self):
        """Handle Connect Now button click"""
        self.user_choice = "connect_now"
        self.connect_now_requested.emit()
        self.accept()
        
    def on_connect_later(self):
        """Handle Connect Later button click"""
        self.user_choice = "connect_later"
        self.connect_later_requested.emit()
        self.accept()
        
    def update_token_status(self, has_token: bool, token_info: dict = None):
        """Update token status display"""
        if has_token and token_info:
            self.token_status_label.setText("✅ Valid token found")
            self.token_status_label.setStyleSheet("font-size: 11px; color: #28A745; font-weight: bold;")
            self.status_label.setText("✅ Connected")
            self.status_label.setStyleSheet("color: #28A745; font-weight: bold;")
        else:
            self.token_status_label.setText("❌ No valid token found")
            self.token_status_label.setStyleSheet("font-size: 11px; color: #F24236; font-weight: bold;")
            self.status_label.setText("⚠️ Not Connected")
            self.status_label.setStyleSheet("color: #F24236; font-weight: bold;")
            
    def should_remember_choice(self) -> bool:
        """Check if user wants to remember their choice"""
        return self.remember_choice_cb.isChecked()
        
    def get_user_choice(self) -> str:
        """Get the user's choice"""
        return self.user_choice
