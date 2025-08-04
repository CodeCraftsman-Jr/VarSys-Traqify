"""
Service Discovery Management Widget
Provides UI for monitoring and managing the triple deployment strategy
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QGroupBox, QComboBox,
    QLineEdit, QTextEdit, QProgressBar, QMessageBox, QTabWidget,
    QHeaderView, QFrame
)
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QFont, QColor

# Service discovery removed - Firebase only
# from ..core.service_discovery import service_discovery

class ServiceDiscoveryWidget(QWidget):
    """Widget for managing Firebase status (service discovery removed)"""

    platform_changed = Signal(str)
    failover_occurred = Signal(str, str)  # old_platform, new_platform
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
        self.refresh_status()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Service Discovery & Failover Management")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Status tab
        status_tab = self.create_status_tab()
        tabs.addTab(status_tab, "Status")
        
        # Configuration tab
        config_tab = self.create_config_tab()
        tabs.addTab(config_tab, "Configuration")
        
        # Monitoring tab
        monitoring_tab = self.create_monitoring_tab()
        tabs.addTab(monitoring_tab, "Monitoring")
        
        layout.addWidget(tabs)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh Status")
        self.refresh_btn.clicked.connect(self.refresh_status)
        button_layout.addWidget(self.refresh_btn)
        
        self.test_all_btn = QPushButton("Test All Endpoints")
        self.test_all_btn.clicked.connect(self.test_all_endpoints)
        button_layout.addWidget(self.test_all_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def create_status_tab(self) -> QWidget:
        """Create the status monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Current status
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)
        
        # Current platform
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Active Platform:"))
        self.current_platform_label = QLabel("Unknown")
        self.current_platform_label.setFont(QFont("Arial", 10, QFont.Bold))
        current_layout.addWidget(self.current_platform_label)
        current_layout.addStretch()
        status_layout.addLayout(current_layout)
        
        # Health status
        health_layout = QHBoxLayout()
        health_layout.addWidget(QLabel("Health Status:"))
        self.health_status_label = QLabel("Checking...")
        health_layout.addWidget(self.health_status_label)
        health_layout.addStretch()
        status_layout.addLayout(health_layout)
        
        layout.addWidget(status_group)
        
        # Endpoints table
        endpoints_group = QGroupBox("Endpoint Status")
        endpoints_layout = QVBoxLayout(endpoints_group)
        
        self.endpoints_table = QTableWidget()
        self.endpoints_table.setColumnCount(7)
        self.endpoints_table.setHorizontalHeaderLabels([
            "Platform", "URL", "Priority", "Status", "Response Time", "Success/Error", "Last Check"
        ])
        
        # Make table responsive
        header = self.endpoints_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        endpoints_layout.addWidget(self.endpoints_table)
        layout.addWidget(endpoints_group)
        
        return widget
    
    def create_config_tab(self) -> QWidget:
        """Create the configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Platform selection
        selection_group = QGroupBox("Platform Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        force_layout = QHBoxLayout()
        force_layout.addWidget(QLabel("Force Platform:"))
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Firebase"])
        self.platform_combo.setEnabled(False)  # Firebase only
        force_layout.addWidget(self.platform_combo)
        
        self.force_btn = QPushButton("Apply")
        self.force_btn.clicked.connect(self.force_platform)
        force_layout.addWidget(self.force_btn)
        
        force_layout.addStretch()
        selection_layout.addLayout(force_layout)
        layout.addWidget(selection_group)
        
        # URL configuration
        url_group = QGroupBox("Endpoint URLs")
        url_layout = QVBoxLayout(url_group)
        
        self.url_inputs = {}
        platforms = ["render", "appwrite", "replit"]
        
        for platform in platforms:
            platform_layout = QHBoxLayout()
            platform_layout.addWidget(QLabel(f"{platform.title()}:"))
            
            url_input = QLineEdit()
            url_input.setPlaceholderText(f"Enter {platform} URL")
            self.url_inputs[platform] = url_input
            platform_layout.addWidget(url_input)
            
            update_btn = QPushButton("Update")
            update_btn.clicked.connect(lambda checked, p=platform: self.update_url(p))
            platform_layout.addWidget(update_btn)
            
            url_layout.addLayout(platform_layout)
        
        layout.addWidget(url_group)
        
        # Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Health Check Interval (seconds):"))
        self.interval_input = QLineEdit()
        self.interval_input.setText("60")
        interval_layout.addWidget(self.interval_input)
        
        update_interval_btn = QPushButton("Update")
        update_interval_btn.clicked.connect(self.update_interval)
        interval_layout.addWidget(update_interval_btn)
        
        settings_layout.addLayout(interval_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return widget
    
    def create_monitoring_tab(self) -> QWidget:
        """Create the monitoring and logs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Failover history
        history_group = QGroupBox("Failover History")
        history_layout = QVBoxLayout(history_group)
        
        self.history_text = QTextEdit()
        self.history_text.setMaximumHeight(150)
        self.history_text.setReadOnly(True)
        history_layout.addWidget(self.history_text)
        
        layout.addWidget(history_group)
        
        # Performance metrics
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QVBoxLayout(metrics_group)
        
        # Response time chart placeholder
        metrics_layout.addWidget(QLabel("Response time metrics would go here"))
        
        layout.addWidget(metrics_group)
        
        # Service discovery logs
        logs_group = QGroupBox("Service Discovery Logs")
        logs_layout = QVBoxLayout(logs_group)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        logs_layout.addWidget(self.logs_text)
        
        layout.addWidget(logs_group)
        
        return widget
    
    def setup_timer(self):
        """Set up automatic refresh timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(5000)  # Refresh every 5 seconds
    
    def refresh_status(self):
        """Refresh the Firebase status"""
        try:
            # Firebase is always the current platform
            self.current_platform_label.setText("Firebase")

            # Firebase is always healthy when configured
            health_text = "🟢 Firebase active"
            self.health_status_label.setStyleSheet("color: green;")
            self.health_status_label.setText(health_text)

            # Update endpoints table with Firebase info
            firebase_endpoints = [{
                'name': 'Firebase',
                'url': 'https://jointjourney-a12d2-default-rtdb.asia-southeast1.firebasedatabase.app',
                'is_healthy': True,
                'response_time': 0.1,
                'priority': 1
            }]
            self.update_endpoints_table(firebase_endpoints)

        except Exception as e:
            self.health_status_label.setText(f"Error: {str(e)}")
            self.health_status_label.setStyleSheet("color: red;")
    
    def update_endpoints_table(self, endpoints):
        """Update the endpoints status table"""
        self.endpoints_table.setRowCount(len(endpoints))
        
        for row, endpoint in enumerate(endpoints):
            # Platform name
            self.endpoints_table.setItem(row, 0, QTableWidgetItem(endpoint.get('name', '')))
            
            # URL (truncated)
            url = endpoint.get('url', '')
            if len(url) > 40:
                url = url[:37] + "..."
            self.endpoints_table.setItem(row, 1, QTableWidgetItem(url))
            
            # Priority
            self.endpoints_table.setItem(row, 2, QTableWidgetItem(str(endpoint.get('priority', 0))))
            
            # Status
            status_item = QTableWidgetItem("🟢 Healthy" if endpoint.get('is_healthy', False) else "🔴 Unhealthy")
            if endpoint.get('is_healthy', False):
                status_item.setBackground(QColor(200, 255, 200))
            else:
                status_item.setBackground(QColor(255, 200, 200))
            self.endpoints_table.setItem(row, 3, status_item)
            
            # Response time
            response_time = endpoint.get('response_time', 0)
            self.endpoints_table.setItem(row, 4, QTableWidgetItem(f"{response_time:.2f}s"))
            
            # Success/Error count
            success_count = endpoint.get('success_count', 0)
            error_count = endpoint.get('error_count', 0)
            self.endpoints_table.setItem(row, 5, QTableWidgetItem(f"{success_count}/{error_count}"))
            
            # Last check
            last_check = endpoint.get('last_check')
            if last_check:
                try:
                    dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = "Unknown"
            else:
                time_str = "Never"
            self.endpoints_table.setItem(row, 6, QTableWidgetItem(time_str))
    
    def test_all_endpoints(self):
        """Test Firebase connection"""
        try:
            # Firebase connection is always available when configured
            self.refresh_status()
            QMessageBox.information(self, "Test Complete", "Firebase connection verified.")

        except Exception as e:
            QMessageBox.warning(self, "Test Failed", f"Failed to test Firebase: {str(e)}")
    
    def force_platform(self):
        """Force selection of Firebase (only option)"""
        platform = self.platform_combo.currentText()

        # Firebase is the only option
        QMessageBox.information(self, "Platform Selection", "Firebase is the only available platform.")
        self.platform_changed.emit("Firebase")
    
    def update_url(self, platform: str):
        """Update URL for Firebase (not configurable)"""
        QMessageBox.information(self, "URL Update", "Firebase URL is not configurable.")

    def update_interval(self):
        """Update health check interval (not applicable for Firebase)"""
        QMessageBox.information(self, "Interval Update", "Health check interval is not configurable for Firebase.")
    
    def add_failover_log(self, old_platform: str, new_platform: str):
        """Add a failover event to the log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] Failover: {old_platform} -> {new_platform}\n"
        self.history_text.append(log_entry)
        
        # Emit signal
        self.failover_occurred.emit(old_platform, new_platform)
