"""
Firebase Sync UI Components

This module provides UI components for displaying sync status,
progress, and manual sync controls.
"""

import json
import logging
import os
import requests
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QPushButton, QProgressBar, QTextEdit, QCheckBox,
    QFrame, QScrollArea, QMessageBox, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QFont, QColor, QPalette

from ..core.firebase_sync import FirebaseSyncEngine, SyncStatus

# Using secure backend system only (Appwrite/Replit/Render)
# No direct Firebase SDK imports needed on client side
firebase_manager = None
firebase_auth = None
FIREBASE_IMPORTS_AVAILABLE = False

# Firebase Configuration (Backend selection removed)
FIREBASE_CONFIG = {
    "firebase": {
        "name": "Firebase Direct Integration",
        "url": "",  # Will be loaded from environment configuration
        "description": "Direct Firebase integration for authentication and data sync",
        "status": "⚠️ Requires Configuration",
        "priority": 1,
        "color": "#FF9800"  # Orange - indicates configuration needed
    }
}

# Import direct Firebase authentication system
try:
    from ..core.direct_firebase_client import get_direct_firebase_client
    FIREBASE_AUTH_AVAILABLE = True
except ImportError:
    get_direct_firebase_client = None
    FIREBASE_AUTH_AVAILABLE = False


class BackendHealthChecker(QObject):
    """Worker thread for checking backend health"""

    health_updated = Signal(str, bool, float, str)  # backend_id, is_healthy, response_time, status_message

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def check_backend_health(self, backend_id: str, config: Dict):
        """Check health of a specific backend"""
        try:
            import time
            start_time = time.time()

            # Test basic connectivity
            response = requests.get(config["url"], timeout=10)
            response_time = time.time() - start_time

            if response.status_code == 200:
                self.health_updated.emit(backend_id, True, response_time, "✅ Healthy")
            else:
                self.health_updated.emit(backend_id, False, response_time, f"⚠️ HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            self.health_updated.emit(backend_id, False, 10.0, "⏰ Timeout")
        except requests.exceptions.ConnectionError:
            self.health_updated.emit(backend_id, False, 0.0, "❌ Connection Failed")
        except Exception as e:
            self.health_updated.emit(backend_id, False, 0.0, f"❌ Error: {str(e)[:30]}")


class BackendSelectionWidget(QWidget):
    """Widget for selecting and managing backend servers"""

    backend_changed = Signal(str)  # backend_id
    test_requested = Signal(str)   # backend_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.health_checker = BackendHealthChecker()
        self.health_status = {}
        self.current_backend = "render"  # Default to Render
        self.setup_ui()
        self.setup_connections()
        self.load_saved_selection()
        self.start_health_monitoring()

    def setup_ui(self):
        """Setup the backend selection UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Firebase status group
        backend_group = QGroupBox("🔥 Firebase Integration Status")
        backend_layout = QVBoxLayout(backend_group)

        # Description
        desc_label = QLabel("Using direct Firebase integration for authentication and data synchronization:")
        desc_label.setWordWrap(True)
        backend_layout.addWidget(desc_label)

        # Firebase status display
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Backend:"))

        firebase_label = QLabel("Firebase Direct Integration - Active")
        firebase_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(firebase_label)
        status_layout.addStretch()

        backend_layout.addLayout(status_layout)

        # Firebase status indicator
        firebase_status_widget = self.create_firebase_status_widget()
        backend_layout.addWidget(firebase_status_widget)

        layout.addWidget(backend_group)

    def create_firebase_status_widget(self) -> QWidget:
        """Create Firebase status widget"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setLineWidth(1)
        widget.setStyleSheet("QFrame { background-color: #f0f8ff; border: 1px solid #4CAF50; border-radius: 4px; }")

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)

        # Firebase icon and name
        name_label = QLabel("🔥 Firebase Direct Integration")
        name_label.setFont(QFont("", 9, QFont.Bold))
        layout.addWidget(name_label)

        # Status indicator
        status_label = QLabel("✅ Active")
        status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(status_label)

        layout.addStretch()

        return widget

    def create_status_widget(self, backend_id: str, config: Dict) -> QWidget:
        """Create status widget for a backend"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setLineWidth(1)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)

        # Backend name
        name_label = QLabel(config["name"])
        name_label.setFont(QFont("", 9, QFont.Bold))
        layout.addWidget(name_label)

        # Status indicator
        status_label = QLabel(config["status"])
        status_label.setObjectName(f"status_{backend_id}")
        layout.addWidget(status_label)

        # Response time
        time_label = QLabel("Response: --")
        time_label.setObjectName(f"time_{backend_id}")
        layout.addWidget(time_label)

        layout.addStretch()

        # Set initial color
        widget.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {config['color']};
                border-radius: 4px;
                background-color: {config['color']}20;
            }}
        """)

        return widget

    def setup_connections(self):
        """Setup signal connections"""
        # No backend selection needed - using Firebase only
        pass

    def on_backend_changed(self):
        """Handle backend selection change - Firebase only"""
        # No backend selection needed - always Firebase
        pass

    def on_health_updated(self, backend_id: str, is_healthy: bool, response_time: float, status_message: str):
        """Handle health status update"""
        self.health_status[backend_id] = {
            'healthy': is_healthy,
            'response_time': response_time,
            'status': status_message
        }

        # Update status widget
        if backend_id in self.status_widgets:
            widget = self.status_widgets[backend_id]

            # Update status label
            status_label = widget.findChild(QLabel, f"status_{backend_id}")
            if status_label:
                status_label.setText(status_message)

            # Update response time
            time_label = widget.findChild(QLabel, f"time_{backend_id}")
            if time_label:
                if response_time > 0:
                    time_label.setText(f"Response: {response_time:.2f}s")
                else:
                    time_label.setText("Response: --")

            # Update color based on health
            config = BACKEND_CONFIGS[backend_id]
            if is_healthy:
                color = "#4CAF50"  # Green
            else:
                color = "#F44336"  # Red

            widget.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid {color};
                    border-radius: 4px;
                    background-color: {color}20;
                }}
            """)

    def start_health_monitoring(self):
        """Start monitoring backend health"""
        self.refresh_health_status()

        # Set up periodic health checks
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.refresh_health_status)
        self.health_timer.start(60000)  # Check every minute

    def refresh_health_status(self):
        """Refresh health status - Firebase only"""
        # Firebase status is always active
        pass

    def test_selected_backend(self):
        """Test Firebase connection"""
        # Firebase connection testing handled by direct client
        pass

    def get_selected_backend(self) -> str:
        """Get the currently selected backend ID"""
        return "firebase"

    def set_selected_backend(self, backend_id: str):
        """Set the selected backend - Firebase only"""
        # Always Firebase, no selection needed
        pass

    def save_selection(self):
        """Save backend selection to file - Firebase only"""
        # Always Firebase, no need to save selection
        pass

    def load_saved_selection(self):
        """Load saved backend selection - Firebase only"""
        # Always Firebase, no need to load selection
        self.current_backend = "firebase"

    def get_backend_config(self, backend_id: str = None) -> Dict:
        """Get configuration for Firebase"""
        return FIREBASE_CONFIG.get("firebase", {})

    def is_backend_healthy(self, backend_id: str = None) -> bool:
        """Check if Firebase is healthy"""
        # Firebase is always considered healthy when configured
        return True


class SyncStatusWidget(QWidget):
    """Widget showing current sync status"""
    
    def __init__(self, sync_engine: FirebaseSyncEngine, parent=None):
        super().__init__(parent)
        self.sync_engine = sync_engine
        self.setup_ui()
        self.setup_connections()
        self.update_status()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def setup_ui(self):
        """Setup the status widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status indicator
        self.status_label = QLabel("Checking sync status...")
        status_font = QFont()
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        layout.addWidget(self.status_label)
        
        # Last sync time
        self.last_sync_label = QLabel("Last sync: Never")
        layout.addWidget(self.last_sync_label)
        
        # Sync count
        self.sync_count_label = QLabel("Synced files: 0")
        layout.addWidget(self.sync_count_label)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.sync_engine.sync_started.connect(self.on_sync_started)
        self.sync_engine.sync_completed.connect(self.on_sync_completed)
        self.sync_engine.sync_error.connect(self.on_sync_error)
    
    def update_status(self):
        """Update status display"""
        status = self.sync_engine.get_sync_status()
        
        # Update status label
        if not status["available"]:
            self.status_label.setText("🔴 Sync Unavailable")
            self.status_label.setStyleSheet("color: red;")
        elif status["status"] == SyncStatus.SYNCING:
            self.status_label.setText("🔄 Syncing...")
            self.status_label.setStyleSheet("color: orange;")
        elif status["status"] == SyncStatus.SUCCESS:
            self.status_label.setText("✅ Sync Complete")
            self.status_label.setStyleSheet("color: green;")
        elif status["status"] == SyncStatus.ERROR:
            self.status_label.setText("❌ Sync Error")
            self.status_label.setStyleSheet("color: red;")
        else:
            self.status_label.setText("⚪ Ready to Sync")
            self.status_label.setStyleSheet("color: gray;")
        
        # Update last sync time
        if status["last_sync"]:
            try:
                last_sync = datetime.fromisoformat(status["last_sync"])
                time_str = last_sync.strftime("%Y-%m-%d %H:%M:%S")
                self.last_sync_label.setText(f"Last sync: {time_str}")
            except:
                self.last_sync_label.setText("Last sync: Unknown")
        else:
            self.last_sync_label.setText("Last sync: Never")
        
        # Update sync count
        self.sync_count_label.setText(f"Synced files: {status['synced_files']}")
    
    def on_sync_started(self):
        """Handle sync started"""
        self.status_label.setText("🔄 Syncing...")
        self.status_label.setStyleSheet("color: orange;")
    
    def on_sync_completed(self, success: bool, message: str):
        """Handle sync completed"""
        if success:
            self.status_label.setText("✅ Sync Complete")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("⚠️ Sync Issues")
            self.status_label.setStyleSheet("color: orange;")
    
    def on_sync_error(self, error: str):
        """Handle sync error"""
        self.status_label.setText("❌ Sync Error")
        self.status_label.setStyleSheet("color: red;")


class SyncProgressWidget(QWidget):
    """Widget showing sync progress"""
    
    def __init__(self, sync_engine: FirebaseSyncEngine, parent=None):
        super().__init__(parent)
        self.sync_engine = sync_engine
        self.setup_ui()
        self.setup_connections()
        self.hide()  # Hidden by default
    
    def setup_ui(self):
        """Setup the progress widget UI"""
        layout = QVBoxLayout(self)
        
        # Progress label
        self.progress_label = QLabel("Preparing sync...")
        layout.addWidget(self.progress_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.sync_engine.sync_started.connect(self.on_sync_started)
        self.sync_engine.sync_progress.connect(self.on_sync_progress)
        self.sync_engine.sync_completed.connect(self.on_sync_completed)
        self.sync_engine.sync_error.connect(self.on_sync_error)
    
    def on_sync_started(self):
        """Handle sync started"""
        self.progress_label.setText("Starting sync...")
        self.progress_bar.setValue(0)
        self.show()
    
    def on_sync_progress(self, operation: str, current: int, total: int):
        """Handle sync progress"""
        self.progress_label.setText(operation)
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
    
    def on_sync_completed(self, success: bool, message: str):
        """Handle sync completed"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("Sync completed")
        QTimer.singleShot(2000, self.hide)
    
    def on_sync_error(self, error: str):
        """Handle sync error"""
        self.progress_label.setText(f"Sync error: {error}")
        QTimer.singleShot(3000, self.hide)


class SyncControlWidget(QWidget):
    """Widget with sync controls and settings"""
    
    # Signals
    settings_changed = Signal()
    
    def __init__(self, sync_engine: FirebaseSyncEngine, parent=None):
        super().__init__(parent)
        self.sync_engine = sync_engine
        self.setup_ui()
        self.setup_connections()
        self.update_ui()
    
    def setup_ui(self):
        """Setup the control widget UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Backend Selection Section
        self.backend_widget = BackendSelectionWidget()
        layout.addWidget(self.backend_widget)

        # Sync Controls Section
        controls_group = QGroupBox("Sync Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Manual sync buttons
        button_layout = QHBoxLayout()

        self.sync_button = QPushButton("Sync Now")
        self.sync_button.clicked.connect(self.manual_sync)
        button_layout.addWidget(self.sync_button)

        self.force_sync_button = QPushButton("Force Full Sync")
        self.force_sync_button.clicked.connect(self.force_sync)
        button_layout.addWidget(self.force_sync_button)

        # Add Test Sync button
        self.test_sync_button = QPushButton("Test Sync")
        self.test_sync_button.clicked.connect(self.test_sync)
        self.test_sync_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.test_sync_button)

        controls_layout.addLayout(button_layout)

        # Directional sync buttons
        directional_layout = QHBoxLayout()

        self.sync_to_button = QPushButton("📤 Sync To Firebase")
        self.sync_to_button.clicked.connect(self.sync_to_firebase)
        self.sync_to_button.setToolTip("Upload local data to Firebase (overwrite remote)")
        self.sync_to_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        directional_layout.addWidget(self.sync_to_button)

        self.sync_from_button = QPushButton("📥 Sync From Firebase")
        self.sync_from_button.clicked.connect(self.sync_from_firebase)
        self.sync_from_button.setToolTip("Download data from Firebase (overwrite local)")
        self.sync_from_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        directional_layout.addWidget(self.sync_from_button)

        controls_layout.addLayout(directional_layout)

        # Status widget
        self.status_widget = SyncStatusWidget(self.sync_engine)
        controls_layout.addWidget(self.status_widget)
        
        # Progress widget
        self.progress_widget = SyncProgressWidget(self.sync_engine)
        controls_layout.addWidget(self.progress_widget)
        
        layout.addWidget(controls_group)
        
        # Sync Settings Section
        settings_group = QGroupBox("Sync Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.auto_sync_checkbox = QCheckBox("Enable automatic sync")
        self.auto_sync_checkbox.setChecked(firebase_manager.config.auto_sync if firebase_manager else False)
        self.auto_sync_checkbox.toggled.connect(self.on_auto_sync_changed)
        settings_layout.addRow(self.auto_sync_checkbox)
        
        layout.addWidget(settings_group)
        
        # Sync Log Section
        log_group = QGroupBox("Sync Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # Clear log button
        clear_log_button = QPushButton("Clear Log")
        clear_log_button.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_button)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
    
    def setup_connections(self):
        """Setup signal connections"""
        self.sync_engine.sync_started.connect(self.on_sync_started)
        self.sync_engine.sync_progress.connect(self.on_sync_progress)
        self.sync_engine.sync_completed.connect(self.on_sync_completed)
        self.sync_engine.sync_error.connect(self.on_sync_error)
        self.sync_engine.conflict_detected.connect(self.on_conflict_detected)

        # Backend selection connections
        self.backend_widget.backend_changed.connect(self.on_backend_changed)
        self.backend_widget.test_requested.connect(self.test_backend_connection)
    
    def update_ui(self):
        """Update UI based on current state"""
        available = self.sync_engine.is_available()
        syncing = self.sync_engine.status == SyncStatus.SYNCING

        self.sync_button.setEnabled(available and not syncing)
        self.force_sync_button.setEnabled(available and not syncing)
        self.test_sync_button.setEnabled(not syncing)  # Test sync can run even if not fully available
        self.sync_to_button.setEnabled(available and not syncing)
        self.sync_from_button.setEnabled(available and not syncing)
        self.auto_sync_checkbox.setEnabled(available)
        
        if not available:
            if not SECURE_AUTH_AVAILABLE:
                self.add_log("Secure backend system not available")
            elif not self._is_user_authenticated():
                self.add_log("Please sign in to enable sync")
            else:
                self.add_log("Firebase sync not available - check backend connection")
    
    def manual_sync(self):
        """Trigger manual sync"""
        if self.sync_engine.is_available():
            self.add_log("Starting manual sync...")
            self.sync_engine.sync_all_data()
        else:
            QMessageBox.warning(self, "Sync Unavailable", 
                              "Firebase sync is not available. Please check your configuration and sign in.")
    
    def force_sync(self):
        """Trigger force sync"""
        reply = QMessageBox.question(
            self, "Force Sync",
            "Force sync will upload all local data to Firebase, potentially overwriting remote changes. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.sync_engine.is_available():
                self.add_log("Starting force sync...")
                self.sync_engine.sync_all_data(force=True)
            else:
                QMessageBox.warning(self, "Sync Unavailable",
                                  "Firebase sync is not available. Please check your configuration and sign in.")

    def test_sync(self):
        """Test sync functionality with detailed feedback"""
        self.add_log("🧪 Starting sync test...")

        try:
            # Test 1: Check secure authentication
            self.add_log("📋 Test 1: Checking authentication...")
            auth_available = False
            auth_details = []

            if SECURE_AUTH_AVAILABLE and get_secure_client:
                secure_client = get_secure_client()
                if secure_client and secure_client.is_authenticated():
                    auth_available = True
                    user = secure_client.current_user
                    auth_details.append(f"✅ Secure client authenticated as: {user.email if user else 'Unknown'}")
                else:
                    auth_details.append("❌ Secure client not authenticated")
            else:
                auth_details.append("❌ Secure authentication not available")

            # Test 2: Check sync engine availability
            self.add_log("📋 Test 2: Checking sync engine...")
            sync_available = self.sync_engine.is_available()
            if sync_available:
                self.add_log("✅ Sync engine is available")
            else:
                self.add_log("❌ Sync engine is not available")

            # Test 3: Check backend connectivity
            self.add_log("📋 Test 3: Testing backend connectivity...")
            backend_status = self._test_backend_connectivity()

            # Test 4: Test data access
            self.add_log("📋 Test 4: Testing data access...")
            data_status = self._test_data_access()

            # Summary
            self.add_log("📊 Test Summary:")
            for detail in auth_details:
                self.add_log(f"   {detail}")

            self.add_log(f"   Sync Engine: {'✅ Available' if sync_available else '❌ Not Available'}")
            self.add_log(f"   Backend: {backend_status}")
            self.add_log(f"   Data Access: {data_status}")

            if auth_available and sync_available:
                self.add_log("🎉 All tests passed! Sync should work properly.")

                # Offer to run a small test sync
                reply = QMessageBox.question(
                    self, "Test Sync Complete",
                    "All connectivity tests passed!\n\n"
                    "Would you like to perform a small test synchronization?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    self.add_log("🔄 Performing test synchronization...")
                    self.sync_engine.sync_all_data()
            else:
                self.add_log("⚠️ Some tests failed. Please check the issues above.")

        except Exception as e:
            self.add_log(f"❌ Test sync failed with error: {str(e)}")
            import traceback
            self.add_log(f"   Traceback: {traceback.format_exc()}")

    def _test_backend_connectivity(self) -> str:
        """Test connectivity to the backend services"""
        try:
            if SECURE_AUTH_AVAILABLE and get_secure_client:
                secure_client = get_secure_client()
                if secure_client:
                    # Check if client is authenticated without triggering verification
                    if secure_client.current_user and secure_client.id_token:
                        return "✅ Connected (authenticated)"
                    else:
                        return "❌ Not authenticated"
                else:
                    return "❌ Client not available"
            else:
                return "❌ Secure client not available"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _test_data_access(self) -> str:
        """Test access to local data"""
        try:
            # Test if we can access the data manager
            if hasattr(self.sync_engine, 'data_manager') and self.sync_engine.data_manager:
                return "✅ Data manager accessible"
            else:
                return "❌ Data manager not accessible"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def sync_to_firebase(self):
        """Upload local data to Firebase (overwrite remote data)"""
        reply = QMessageBox.question(
            self, "Sync To Firebase",
            "This will upload all local data to Firebase and overwrite any remote changes.\n\n"
            "⚠️ Warning: This may overwrite data that was changed on other devices.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.sync_engine.is_available():
                self.add_log("📤 Starting upload to Firebase...")
                try:
                    # Use the sync engine's upload functionality
                    # This will upload all local data modules to Firebase
                    self._perform_directional_sync("upload")
                except Exception as e:
                    self.add_log(f"❌ Upload failed: {str(e)}")
                    QMessageBox.warning(self, "Upload Failed", f"Failed to upload data to Firebase:\n{str(e)}")
            else:
                QMessageBox.warning(self, "Sync Unavailable",
                                  "Firebase sync is not available. Please check your configuration and sign in.")

    def sync_from_firebase(self):
        """Download data from Firebase (overwrite local data)"""
        reply = QMessageBox.question(
            self, "Sync From Firebase",
            "This will download all data from Firebase and overwrite your local changes.\n\n"
            "⚠️ Warning: This may overwrite local data that hasn't been synced yet.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.sync_engine.is_available():
                self.add_log("📥 Starting download from Firebase...")
                try:
                    # Use the sync engine's download functionality
                    # This will download all data modules from Firebase
                    self._perform_directional_sync("download")
                except Exception as e:
                    self.add_log(f"❌ Download failed: {str(e)}")
                    QMessageBox.warning(self, "Download Failed", f"Failed to download data from Firebase:\n{str(e)}")
            else:
                QMessageBox.warning(self, "Sync Unavailable",
                                  "Firebase sync is not available. Please check your configuration and sign in.")

    def _perform_directional_sync(self, direction: str):
        """Perform directional sync operation"""
        try:
            # Get all data modules that can be synced from the sync engine
            data_modules = getattr(self.sync_engine, 'syncable_modules',
                                 ["expenses", "income", "habits", "attendance", "todos", "investments", "budget"])

            if direction == "upload":
                self.add_log("📤 Uploading data modules to Firebase...")
                for module in data_modules:
                    try:
                        # Get all CSV files for this module
                        csv_files = self._get_module_csv_files(module)
                        successful_uploads = 0
                        failed_uploads = 0

                        for csv_file in csv_files:
                            self.add_log(f"   📤 Uploading {module}/{csv_file}...")
                            try:
                                self.sync_engine.upload_file(module, csv_file)
                                successful_uploads += 1
                            except Exception as file_error:
                                failed_uploads += 1
                                self.add_log(f"   ❌ Failed to upload {module}/{csv_file}: {str(file_error)}")

                        if csv_files:
                            if failed_uploads == 0:
                                self.add_log(f"   ✅ {module} uploaded successfully ({len(csv_files)} files)")
                            elif successful_uploads > 0:
                                self.add_log(f"   ⚠️ {module} partially uploaded ({successful_uploads}/{len(csv_files)} files)")
                            else:
                                self.add_log(f"   ❌ {module} upload failed (0/{len(csv_files)} files)")
                        else:
                            self.add_log(f"   ℹ️ No data files found for {module}")

                    except Exception as e:
                        self.add_log(f"   ❌ Failed to process {module}: {str(e)}")

                self.add_log("📤 Upload to Firebase completed!")

            elif direction == "download":
                self.add_log("📥 Downloading data modules from Firebase...")
                for module in data_modules:
                    try:
                        # Get all CSV files for this module
                        csv_files = self._get_module_csv_files(module)
                        for csv_file in csv_files:
                            self.add_log(f"   📥 Downloading {module}/{csv_file}...")
                            remote_data = self.sync_engine.download_file(module, csv_file)
                            if remote_data is not None and not remote_data.empty:
                                # Save the downloaded data locally
                                self.sync_engine.data_manager.write_csv(module, csv_file, remote_data)
                                self.add_log(f"      ✅ Downloaded and saved {len(remote_data)} records")
                            elif remote_data is not None and remote_data.empty:
                                self.add_log(f"      ℹ️ Remote file is empty")
                            else:
                                self.add_log(f"      ⚠️ No remote data found")

                        if csv_files:
                            self.add_log(f"   ✅ {module} downloaded successfully ({len(csv_files)} files)")
                        else:
                            self.add_log(f"   ℹ️ No data files found for {module}")

                    except Exception as e:
                        self.add_log(f"   ❌ Failed to download {module}: {str(e)}")

                self.add_log("📥 Download from Firebase completed!")

        except Exception as e:
            self.add_log(f"❌ Directional sync failed: {str(e)}")
            raise

    def _get_module_csv_files(self, module: str) -> list:
        """Get list of CSV files for a data module"""
        try:
            # Use the same approach as the sync engine - scan the module directory
            module_path = self.sync_engine.data_manager.data_dir / module
            if not module_path.exists():
                return []

            # Get all CSV files in the module directory
            csv_files = list(module_path.glob("*.csv"))
            return [csv_file.name for csv_file in csv_files]

        except Exception as e:
            self.add_log(f"Error getting CSV files for {module}: {str(e)}")
            return []

    def on_auto_sync_changed(self, enabled: bool):
        """Handle auto-sync setting change"""
        if firebase_manager is None:
            self.add_log("Firebase not available")
            return

        firebase_manager.config.auto_sync = enabled
        firebase_manager.save_config()

        if enabled:
            self.sync_engine.start_auto_sync(firebase_manager.config.sync_interval)
            self.add_log("Auto-sync enabled")
        else:
            self.sync_engine.stop_auto_sync()
            self.add_log("Auto-sync disabled")
        
        self.settings_changed.emit()

    def _is_user_authenticated(self) -> bool:
        """Check if user is authenticated via any available method"""
        # Check secure authentication first
        if SECURE_AUTH_AVAILABLE and get_secure_client:
            secure_client = get_secure_client()
            if secure_client and secure_client.current_user:
                return True

        # Fallback to firebase_auth
        if firebase_auth and firebase_auth.current_user:
            return True

        return False
    
    def add_log(self, message: str):
        """Add message to sync log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Clear sync log"""
        self.log_text.clear()
    
    def on_sync_started(self):
        """Handle sync started"""
        self.add_log("Sync started")
        self.update_ui()
    
    def on_sync_progress(self, operation: str, current: int, total: int):
        """Handle sync progress"""
        self.add_log(f"{operation} ({current}/{total})")
    
    def on_sync_completed(self, success: bool, message: str):
        """Handle sync completed"""
        if success:
            self.add_log(f"✅ Sync completed: {message}")
        else:
            self.add_log(f"⚠️ Sync completed with issues: {message}")
        self.update_ui()
    
    def on_sync_error(self, error: str):
        """Handle sync error"""
        self.add_log(f"❌ Sync error: {error}")
        self.update_ui()
    
    def on_conflict_detected(self, module: str, filename: str):
        """Handle conflict detection"""
        self.add_log(f"⚠️ Conflict detected in {module}/{filename}")
        QMessageBox.warning(
            self, "Sync Conflict",
            f"A conflict was detected in {module}/{filename}. "
            "The system attempted to merge the data automatically."
        )

    def on_backend_changed(self, backend_id: str):
        """Handle backend selection change"""
        self.add_log(f"🌐 Backend changed to: {BACKEND_CONFIGS[backend_id]['name']}")

        # Update sync engine backend configuration if possible
        try:
            if hasattr(self.sync_engine, 'update_backend_config'):
                config = self.backend_widget.get_backend_config(backend_id)
                self.sync_engine.update_backend_config(config)
                self.add_log(f"✅ Sync engine updated for {config['name']}")
        except Exception as e:
            self.add_log(f"⚠️ Failed to update sync engine: {str(e)}")

        # Update UI state
        self.update_ui()

    def test_backend_connection(self, backend_id: str):
        """Test connection to a specific backend"""
        self.add_log(f"🔍 Testing connection to {BACKEND_CONFIGS[backend_id]['name']}...")

        config = BACKEND_CONFIGS[backend_id]

        try:
            # Test basic connectivity
            import time
            start_time = time.time()
            response = requests.get(config["url"], timeout=15)
            response_time = time.time() - start_time

            if response.status_code == 200:
                self.add_log(f"✅ Connection successful ({response_time:.2f}s)")

                # Try to test authentication if possible
                self.test_backend_authentication(backend_id, config)
            else:
                self.add_log(f"⚠️ Connection failed: HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            self.add_log(f"⏰ Connection timeout (>15s)")
        except requests.exceptions.ConnectionError:
            self.add_log(f"❌ Connection failed: Cannot reach server")
        except Exception as e:
            self.add_log(f"❌ Connection error: {str(e)}")

    def test_backend_authentication(self, backend_id: str, config: Dict):
        """Test authentication with a backend"""
        try:
            # Get test credentials from environment variables
            test_email = os.getenv('TEST_EMAIL', 'test@example.com')
            test_password = os.getenv('TEST_PASSWORD', 'test_password')

            # Skip authentication test if no real credentials provided
            if test_email == 'test@example.com' or test_password == 'test_password':
                self.add_log(f"⚠️ Skipping authentication test - no test credentials configured")
                self.add_log(f"   Set TEST_EMAIL and TEST_PASSWORD environment variables to test authentication")
                return

            auth_data = {
                "email": test_email,
                "password": test_password
            }

            headers = {"Content-Type": "application/json"}

            if backend_id == "appwrite":
                # Appwrite uses different request format
                auth_payload = {
                    "path": config["auth_endpoint"],
                    "method": "POST",
                    "body": json.dumps(auth_data)
                }
                response = requests.post(config["url"], headers={
                    "Content-Type": "application/json",
                    "X-Appwrite-Project": "6874905d00119a86f907"
                }, json=auth_payload, timeout=15)
            else:
                # Render and Replit use direct endpoints
                auth_url = config["url"] + config["auth_endpoint"]
                response = requests.post(auth_url, headers=headers, json=auth_data, timeout=15)

            if response.status_code == 200:
                try:
                    data = response.json()
                    if backend_id == "appwrite":
                        # Parse Appwrite response
                        response_body = json.loads(data.get('responseBody', '{}'))
                        success = response_body.get('success', False)
                    else:
                        # Direct response
                        success = data.get('success', False)

                    if success:
                        self.add_log(f"✅ Authentication test successful")

                        # Test data access
                        self.test_backend_data_access(backend_id, config, data)
                    else:
                        self.add_log(f"⚠️ Authentication failed: Invalid credentials")
                except json.JSONDecodeError:
                    self.add_log(f"⚠️ Authentication response not valid JSON")
            else:
                self.add_log(f"⚠️ Authentication failed: HTTP {response.status_code}")

        except Exception as e:
            self.add_log(f"⚠️ Authentication test error: {str(e)}")

    def test_backend_data_access(self, backend_id: str, config: Dict, auth_response: Dict):
        """Test data access with a backend"""
        try:
            # Extract token from auth response
            if backend_id == "appwrite":
                response_body = json.loads(auth_response.get('responseBody', '{}'))
                id_token = response_body.get('idToken')
            else:
                id_token = auth_response.get('idToken')

            if not id_token:
                self.add_log(f"⚠️ No authentication token received")
                return

            # Test data download
            test_module = "attendance"
            test_file = "attendance_records"

            headers = {"Authorization": f"Bearer {id_token}"}

            if backend_id == "appwrite":
                # Appwrite uses different request format
                data_payload = {
                    "path": f"{config['data_endpoint']}/{test_module}/{test_file}",
                    "method": "GET",
                    "body": json.dumps({"authorization": f"Bearer {id_token}"})
                }
                response = requests.post(config["url"], headers={
                    "Content-Type": "application/json",
                    "X-Appwrite-Project": "6874905d00119a86f907"
                }, json=data_payload, timeout=15)
            else:
                # Render and Replit use direct endpoints
                data_url = f"{config['url']}{config['data_endpoint']}/{test_module}/{test_file}"
                response = requests.get(data_url, headers=headers, timeout=15)

            if response.status_code == 200:
                try:
                    data = response.json()
                    if backend_id == "appwrite":
                        # Parse Appwrite response
                        response_body = json.loads(data.get('responseBody', '{}'))
                        success = response_body.get('success', False)
                        data_content = response_body.get('data')
                    else:
                        # Direct response
                        success = data.get('success', False)
                        data_content = data.get('data')

                    if success and data_content:
                        data_size = len(str(data_content))
                        self.add_log(f"✅ Data access successful ({data_size:,} characters)")
                        self.add_log(f"🎉 Backend {config['name']} is fully functional!")
                    else:
                        self.add_log(f"⚠️ Data access failed: No data returned")
                except json.JSONDecodeError:
                    self.add_log(f"⚠️ Data response not valid JSON")
            else:
                self.add_log(f"⚠️ Data access failed: HTTP {response.status_code}")

        except Exception as e:
            self.add_log(f"⚠️ Data access test error: {str(e)}")

    def get_selected_backend_config(self) -> Dict:
        """Get the configuration for the currently selected backend"""
        return self.backend_widget.get_backend_config()

    def is_selected_backend_healthy(self) -> bool:
        """Check if the selected backend is healthy"""
        return self.backend_widget.is_backend_healthy()
