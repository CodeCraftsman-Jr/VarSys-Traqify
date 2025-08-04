"""
Asynchronous sync worker for Google Tasks and Calendar integration.
Provides background processing to prevent UI freezing during comprehensive sync operations.
"""

import time
from datetime import datetime
from typing import Dict, Any, List
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit
from PySide6.QtCore import Qt, QTimer

from .models import TodoDataModel


class SyncProgressDialog(QDialog):
    """Modal progress dialog for comprehensive sync operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Comprehensive Historical Sync")
        self.setModal(True)
        self.setFixedSize(600, 400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
        # Track timing
        self.start_time = None
        self.cancelled = False
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """Setup the progress dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Comprehensive Historical Sync")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("Initializing sync...")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Progress details
        self.progress_details = QLabel("Preparing to sync...")
        self.progress_details.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self.progress_details)
        
        # Elapsed time
        self.time_label = QLabel("Elapsed: 00:00")
        self.time_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self.time_label)
        
        # Log area
        log_label = QLabel("Sync Log:")
        log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(self.log_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_sync)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
    
    def setup_timer(self):
        """Setup timer for elapsed time updates"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_elapsed_time)
        self.timer.start(1000)  # Update every second
    
    def start_sync(self):
        """Start the sync process"""
        self.start_time = time.time()
        self.cancelled = False
        self.cancel_button.setEnabled(True)
        self.close_button.setEnabled(False)
    
    def cancel_sync(self):
        """Cancel the sync operation"""
        self.cancelled = True
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Cancelling sync...")
        self.progress_details.setText("Please wait while the sync operation is cancelled...")
        self.add_log("🛑 Sync cancellation requested by user")
    
    def sync_completed(self, success: bool, message: str = ""):
        """Mark sync as completed"""
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        
        if success:
            self.status_label.setText("✅ Sync completed successfully!")
            self.progress_bar.setValue(100)
            self.add_log(f"✅ Sync completed: {message}")
        else:
            self.status_label.setText("❌ Sync failed")
            self.add_log(f"❌ Sync failed: {message}")
    
    def update_status(self, status: str):
        """Update the status label"""
        self.status_label.setText(status)
    
    def update_progress(self, value: int, details: str = ""):
        """Update progress bar and details"""
        self.progress_bar.setValue(value)
        if details:
            self.progress_details.setText(details)
    
    def add_log(self, message: str):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_elapsed_time(self):
        """Update the elapsed time display"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.time_label.setText(f"Elapsed: {minutes:02d}:{seconds:02d}")
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.cancel_button.isEnabled():
            # Sync is still running, cancel it
            self.cancel_sync()
        event.accept()



