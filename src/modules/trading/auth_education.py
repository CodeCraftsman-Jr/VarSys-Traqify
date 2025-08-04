"""
Zerodha Authentication Education Components
Provides user education about Zerodha API limitations and authentication requirements
"""

import logging
from datetime import datetime, time, timedelta
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QTextEdit, QGroupBox, QWidget, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon

class ZerodhaEducationDialog(QDialog):
    """Educational dialog explaining Zerodha API limitations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Understanding Zerodha API Authentication")
        self.setModal(True)
        self.setFixedSize(700, 600)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the education dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header_label = QLabel("🎓 Understanding Zerodha API Authentication")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setStyleSheet("color: #2E86AB; margin-bottom: 20px;")
        layout.addWidget(header_label)
        
        # Scrollable content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Why daily authentication section
        self.create_why_section(scroll_layout)
        
        # How it works section
        self.create_how_section(scroll_layout)
        
        # What you can do section
        self.create_what_section(scroll_layout)
        
        # Tips section
        self.create_tips_section(scroll_layout)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Close button
        close_btn = QPushButton("Got it!")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
    def create_why_section(self, layout):
        """Create 'Why Daily Authentication' section"""
        group = QGroupBox("🤔 Why Daily Authentication?")
        group.setStyleSheet(self.get_group_style())
        group_layout = QVBoxLayout(group)
        
        content = QLabel("""
<b>This is a Zerodha API limitation, not an application issue:</b><br><br>

• <b>Security by Design:</b> Zerodha designed their API tokens to expire daily for security reasons<br>
• <b>No Refresh Tokens:</b> Unlike many APIs, Zerodha doesn't provide refresh tokens<br>
• <b>Manual Re-authentication:</b> Every trading day requires fresh authentication<br>
• <b>Industry Standard:</b> Many brokers have similar security measures<br><br>

<b>Token Validity:</b> Approximately 6:00 AM to 6:00 AM next day (Indian time)
        """)
        content.setWordWrap(True)
        content.setStyleSheet("font-size: 11px; padding: 10px;")
        group_layout.addWidget(content)
        
        layout.addWidget(group)
        
    def create_how_section(self, layout):
        """Create 'How It Works' section"""
        group = QGroupBox("⚙️ How Authentication Works")
        group.setStyleSheet(self.get_group_style())
        group_layout = QVBoxLayout(group)
        
        content = QLabel("""
<b>The authentication process involves:</b><br><br>

1. <b>Login URL Generation:</b> App creates a secure login URL<br>
2. <b>Browser Authentication:</b> You log in through Zerodha's secure website<br>
3. <b>Request Token:</b> Zerodha provides a temporary request token<br>
4. <b>Access Token Exchange:</b> App exchanges request token for access token<br>
5. <b>Secure Storage:</b> Access token is stored securely for the session<br><br>

<b>What happens when tokens expire:</b><br>
• App detects expired token automatically<br>
• You're prompted to re-authenticate<br>
• Process takes less than 2 minutes<br>
• All your data and settings are preserved
        """)
        content.setWordWrap(True)
        content.setStyleSheet("font-size: 11px; padding: 10px;")
        group_layout.addWidget(content)
        
        layout.addWidget(group)
        
    def create_what_section(self, layout):
        """Create 'What You Can Do' section"""
        group = QGroupBox("✅ What You Can Do")
        group.setStyleSheet(self.get_group_style())
        group_layout = QVBoxLayout(group)
        
        content = QLabel("""
<b>You have full control over when to authenticate:</b><br><br>

• <b>Skip at Startup:</b> Choose "Connect Later" to use other app features first<br>
• <b>Connect When Ready:</b> Authenticate only when you need trading functionality<br>
• <b>Full App Access:</b> Expense tracking, bank analysis work without trading connection<br>
• <b>Easy Reconnection:</b> Use "Force Reconnect" button when tokens expire<br><br>

<b>Application features that work without trading connection:</b><br>
✓ Expense Tracking and Analysis<br>
✓ Bank Statement Import and Categorization<br>
✓ Financial Reports and Charts<br>
✓ Data Export/Import<br>
✓ Settings and Configuration<br><br>

<b>Features that require trading connection:</b><br>
• Live market data and quotes<br>
• Portfolio and positions<br>
• Order placement and management<br>
• Trading analytics and reports
        """)
        content.setWordWrap(True)
        content.setStyleSheet("font-size: 11px; padding: 10px;")
        group_layout.addWidget(content)
        
        layout.addWidget(group)
        
    def create_tips_section(self, layout):
        """Create 'Tips & Best Practices' section"""
        group = QGroupBox("💡 Tips & Best Practices")
        group.setStyleSheet(self.get_group_style())
        group_layout = QVBoxLayout(group)
        
        content = QLabel("""
<b>To make authentication easier:</b><br><br>

• <b>Morning Routine:</b> Authenticate once when you start trading for the day<br>
• <b>Keep Browser Open:</b> Don't close the browser tab during authentication<br>
• <b>Check Status:</b> Look for connection status indicators in the trading tab<br>
• <b>Plan Ahead:</b> If trading after 6 AM, expect to re-authenticate<br><br>

<b>Troubleshooting:</b><br>
• If authentication fails, try "Force Reconnect"<br>
• Clear browser cache if you encounter login issues<br>
• Ensure your Zerodha account is active and accessible<br>
• Check your internet connection during authentication<br><br>

<b>Remember:</b> This is a one-time setup each trading day, and the app will guide you through it!
        """)
        content.setWordWrap(True)
        content.setStyleSheet("font-size: 11px; padding: 10px;")
        group_layout.addWidget(content)
        
        layout.addWidget(group)
        
    def get_group_style(self):
        """Get consistent group box styling"""
        return """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E8E8E8;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """

class TokenStatusWidget(QWidget):
    """Widget showing current token status and expiry information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(60000)  # Update every minute
        
    def setup_ui(self):
        """Setup the token status widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Status frame
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        
        # Connection status
        self.connection_label = QLabel("🔴 Trading: Not Connected")
        self.connection_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        status_layout.addWidget(self.connection_label)
        
        # Token expiry info
        self.expiry_label = QLabel("Token expires: Not available")
        self.expiry_label.setStyleSheet("font-size: 10px; color: #666;")
        status_layout.addWidget(self.expiry_label)
        
        # Time until expiry
        self.countdown_label = QLabel("")
        self.countdown_label.setStyleSheet("font-size: 10px; color: #888;")
        status_layout.addWidget(self.countdown_label)
        
        layout.addWidget(status_frame)
        
    def update_status(self, connected: bool, token_info: dict = None):
        """Update the token status display"""
        if connected and token_info:
            self.connection_label.setText("🟢 Trading: Connected")
            self.connection_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #28A745;")
            
            # Calculate expiry time (estimate)
            current_time = datetime.now()
            next_expiry = current_time.replace(hour=6, minute=0, second=0, microsecond=0)
            if current_time.hour >= 6:
                next_expiry = next_expiry + timedelta(days=1)
                
            self.expiry_label.setText(f"Token expires: ~{next_expiry.strftime('%Y-%m-%d 06:00')}")
            self.expiry_label.setStyleSheet("font-size: 10px; color: #28A745;")
            
        else:
            self.connection_label.setText("🔴 Trading: Not Connected")
            self.connection_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #DC3545;")
            self.expiry_label.setText("Token expires: Not available")
            self.expiry_label.setStyleSheet("font-size: 10px; color: #666;")
            
        self.update_display()
        
    def update_display(self):
        """Update the countdown display"""
        try:
            current_time = datetime.now()
            next_expiry = current_time.replace(hour=6, minute=0, second=0, microsecond=0)
            if current_time.hour >= 6:
                next_expiry = next_expiry + timedelta(days=1)
                
            time_diff = next_expiry - current_time
            hours = int(time_diff.total_seconds() // 3600)
            minutes = int((time_diff.total_seconds() % 3600) // 60)
            
            if hours > 0:
                self.countdown_label.setText(f"Next expiry in: ~{hours}h {minutes}m")
            else:
                self.countdown_label.setText(f"Next expiry in: ~{minutes}m")
                
        except Exception as e:
            self.logger.error(f"Error updating countdown: {e}")
            self.countdown_label.setText("Next expiry in: Calculating...")
