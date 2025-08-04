#!/usr/bin/env python3
"""
Update Dialog Module
Provides user interface for application updates
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QTabWidget, QWidget, QGroupBox,
    QCheckBox, QSpinBox, QComboBox, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QPixmap, QIcon


class UpdateNotificationDialog(QDialog):
    """Dialog for notifying users about available updates"""
    
    # Signals
    download_requested = Signal(dict)  # version_info
    skip_version_requested = Signal(str)  # version
    remind_later_requested = Signal()
    
    def __init__(self, version_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.version_info = version_info
        
        self.setup_ui()
        self.populate_data()
        
    def setup_ui(self):
        """Setup the notification dialog UI"""
        self.setWindowTitle("Update Available")
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.setFixedSize(550, 450)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section
        self.setup_header(layout)
        
        # Content section
        self.setup_content(layout)
        
        # Buttons section
        self.setup_buttons(layout)
        
    def setup_header(self, layout):
        """Setup the header section with proper text visibility"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setSpacing(15)

        # Update icon
        icon_label = QLabel()
        icon_label.setText("🔄")
        icon_label.setFont(QFont("Arial", 28))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(60, 60)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border-radius: 30px;
                color: #1976d2;
            }
        """)
        header_layout.addWidget(icon_label)

        # Title and version info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        self.title_label = QLabel("Update Available!")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #28a745;
                padding: 2px 0;
                border: none;
            }
        """)
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label)

        self.version_label = QLabel()
        self.version_label.setFont(QFont("Segoe UI", 12))
        self.version_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                padding: 2px 0;
                border: none;
            }
        """)
        self.version_label.setWordWrap(True)
        info_layout.addWidget(self.version_label)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        layout.addWidget(header_frame)
        
    def setup_content(self, layout):
        """Setup the content section with proper text visibility"""
        # Version details
        details_group = QGroupBox("Update Details")
        details_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        details_layout = QVBoxLayout(details_group)

        self.release_date_label = QLabel()
        self.release_date_label.setStyleSheet("color: #2c3e50; font-size: 11px; padding: 2px;")

        self.file_size_label = QLabel()
        self.file_size_label.setStyleSheet("color: #2c3e50; font-size: 11px; padding: 2px;")

        self.critical_label = QLabel()
        self.critical_label.setStyleSheet("color: #2c3e50; font-size: 11px; padding: 2px; font-weight: bold;")

        details_layout.addWidget(self.release_date_label)
        details_layout.addWidget(self.file_size_label)
        details_layout.addWidget(self.critical_label)

        layout.addWidget(details_group)

        # Changelog
        changelog_group = QGroupBox("What's New")
        changelog_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        changelog_layout = QVBoxLayout(changelog_group)

        self.changelog_text = QTextEdit()
        self.changelog_text.setReadOnly(True)
        self.changelog_text.setMaximumHeight(120)
        self.changelog_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                color: #2c3e50;
                font-size: 11px;
            }
        """)

        changelog_layout.addWidget(self.changelog_text)
        layout.addWidget(changelog_group)
        
    def setup_buttons(self, layout):
        """Setup the buttons section"""
        button_layout = QHBoxLayout()
        
        # Skip this version button
        self.skip_button = QPushButton("Skip This Version")
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.skip_button.clicked.connect(self.skip_version)
        button_layout.addWidget(self.skip_button)
        
        button_layout.addStretch()
        
        # Remind later button
        self.remind_button = QPushButton("Remind Me Later")
        self.remind_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.remind_button.clicked.connect(self.remind_later)
        button_layout.addWidget(self.remind_button)
        
        # Download button
        self.download_button = QPushButton("Download Update")
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.download_button.clicked.connect(self.download_update)
        button_layout.addWidget(self.download_button)
        
        layout.addLayout(button_layout)
        
    def populate_data(self):
        """Populate the dialog with version information"""
        version = self.version_info.get('version', 'Unknown')
        self.version_label.setText(f"Version {version} is now available")
        
        # Release date
        release_date = self.version_info.get('release_date', '')
        if release_date:
            try:
                date_obj = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%B %d, %Y')
                self.release_date_label.setText(f"📅 Released: {formatted_date}")
            except:
                self.release_date_label.setText(f"📅 Released: {release_date}")
        else:
            self.release_date_label.setText("📅 Release date: Not specified")
            
        # File size
        file_size = self.version_info.get('file_size', 0)
        if file_size > 0:
            size_mb = file_size / (1024 * 1024)
            self.file_size_label.setText(f"💾 Download size: {size_mb:.1f} MB")
        else:
            self.file_size_label.setText("💾 Download size: Not specified")
            
        # Critical update indicator
        is_critical = self.version_info.get('is_critical', False)
        if is_critical:
            self.critical_label.setText("⚠️ This is a critical security update")
            self.critical_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        else:
            self.critical_label.setText("ℹ️ Regular update")
            self.critical_label.setStyleSheet("color: #17a2b8;")
            
        # Changelog
        changelog = self.version_info.get('changelog', [])
        if changelog:
            if isinstance(changelog, list):
                changelog_text = '\n'.join(f"• {item}" for item in changelog)
            else:
                changelog_text = str(changelog)
            self.changelog_text.setPlainText(changelog_text)
        else:
            self.changelog_text.setPlainText("No changelog information available.")
            
    def download_update(self):
        """Handle download button click"""
        self.download_requested.emit(self.version_info)
        self.accept()
        
    def skip_version(self):
        """Handle skip version button click"""
        version = self.version_info.get('version', '')
        if version:
            reply = QMessageBox.question(
                self, "Skip Version",
                f"Are you sure you want to skip version {version}?\n\n"
                "You won't be notified about this version again.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.skip_version_requested.emit(version)
                self.reject()
        
    def remind_later(self):
        """Handle remind later button click"""
        self.remind_later_requested.emit()
        self.reject()


class UpdateProgressDialog(QDialog):
    """Dialog for showing update progress"""
    
    # Signals
    cancel_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.current_operation = ""
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the progress dialog UI"""
        self.setWindowTitle("Updating Application")
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.setFixedSize(450, 200)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Status label
        self.status_label = QLabel("Preparing update...")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ced4da;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Detail label
        self.detail_label = QLabel("")
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setStyleSheet("color: #6c757d;")
        layout.addWidget(self.detail_label)
        
        layout.addStretch()
        
        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.cancel_button.clicked.connect(self.cancel_update)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def update_progress(self, progress: int, status: str = "", detail: str = ""):
        """Update the progress display"""
        self.progress_bar.setValue(progress)
        
        if status:
            self.status_label.setText(status)
            
        if detail:
            self.detail_label.setText(detail)
            
        # Disable cancel button during installation
        if "installing" in status.lower():
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Installing...")
        else:
            self.cancel_button.setEnabled(True)
            self.cancel_button.setText("Cancel")
            
    def cancel_update(self):
        """Handle cancel button click"""
        if self.cancel_button.isEnabled():
            reply = QMessageBox.question(
                self, "Cancel Update",
                "Are you sure you want to cancel the update?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.cancel_requested.emit()
                self.reject()


class UpdateSettingsDialog(QDialog):
    """Dialog for configuring update settings"""

    # Signals
    settings_changed = Signal(dict)  # new_settings

    def __init__(self, current_settings: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.current_settings = current_settings.copy()

        self.setup_ui()
        self.populate_settings()

    def setup_ui(self):
        """Setup the settings dialog UI with proper text visibility"""
        self.setWindowTitle("Update Settings")
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.setFixedSize(550, 500)  # Increased height from 450 to 500

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(12)  # Reduced from 15 to 12
        layout.setContentsMargins(20, 15, 20, 15)  # Reduced top/bottom margins

        # Auto-check settings
        auto_check_group = QGroupBox("Automatic Update Checking")
        auto_check_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        auto_check_layout = QVBoxLayout(auto_check_group)
        auto_check_layout.setSpacing(6)  # Reduced from 8 to 6
        auto_check_layout.setContentsMargins(10, 12, 10, 8)  # Adjusted margins

        self.auto_check_checkbox = QCheckBox("Check for updates automatically")
        self.auto_check_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #2c3e50;
                spacing: 5px;
                padding: 3px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        auto_check_layout.addWidget(self.auto_check_checkbox)

        # Check interval
        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(8)  # Reduced from 10 to 8
        interval_layout.setContentsMargins(5, 2, 5, 2)  # Reduced vertical margins

        interval_label = QLabel("Check every:")

        interval_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                font-weight: normal;
                padding: 5px;
                background: transparent;
                border: none;
            }
        """)
        interval_label.setMinimumHeight(25)
        interval_layout.addWidget(interval_label)

        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 168)  # 1 hour to 1 week
        self.interval_spinbox.setSuffix(" hours")
        self.interval_spinbox.setStyleSheet("""
            QSpinBox {
                color: #2c3e50;
                font-size: 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px 8px;
                background-color: white;
                min-width: 130px;
                min-height: 25px;
                max-height: 30px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px;
                background-color: #f8f9fa;
                border: 1px solid #bdc3c7;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e9ecef;
            }
        """)
        interval_layout.addWidget(self.interval_spinbox)

        interval_layout.addStretch()
        auto_check_layout.addLayout(interval_layout)

        layout.addWidget(auto_check_group)

        # Download settings
        download_group = QGroupBox("Download Settings")
        download_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        download_layout = QVBoxLayout(download_group)
        download_layout.setSpacing(6)  # Reduced from 8 to 6
        download_layout.setContentsMargins(10, 12, 10, 8)  # Adjusted margins

        self.auto_download_checkbox = QCheckBox("Download updates automatically")
        self.auto_download_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #2c3e50;
                spacing: 5px;
                padding: 3px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        download_layout.addWidget(self.auto_download_checkbox)

        layout.addWidget(download_group)

        # Installation settings
        install_group = QGroupBox("Installation Settings")
        install_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        install_layout = QVBoxLayout(install_group)
        install_layout.setSpacing(6)  # Reduced from 8 to 6
        install_layout.setContentsMargins(10, 12, 10, 8)  # Adjusted margins

        self.auto_install_checkbox = QCheckBox("Install updates automatically")
        self.auto_install_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #2c3e50;
                spacing: 5px;
                padding: 3px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        install_layout.addWidget(self.auto_install_checkbox)

        self.backup_checkbox = QCheckBox("Create backup before updating")
        self.backup_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #2c3e50;
                spacing: 5px;
                padding: 3px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        install_layout.addWidget(self.backup_checkbox)

        layout.addWidget(install_group)

        # Update channel
        channel_group = QGroupBox("Update Channel")
        channel_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        channel_layout = QVBoxLayout(channel_group)
        channel_layout.setSpacing(6)  # Reduced from 8 to 6
        channel_layout.setContentsMargins(10, 12, 10, 8)  # Adjusted margins

        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["stable", "beta", "alpha"])
        self.channel_combo.setStyleSheet("""
            QComboBox {
                color: #2c3e50;
                font-size: 11px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 5px;
                background-color: white;
                min-height: 16px;
            }
            QComboBox::drop-down {
                border: none;
                width: 16px;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
            }
        """)
        channel_layout.addWidget(self.channel_combo)

        channel_help = QLabel("• Stable: Recommended for most users\n• Beta: Early access to new features\n• Alpha: Latest development builds")
        channel_help.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 10px;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
                border: 1px solid #e9ecef;
            }
        """)
        channel_layout.addWidget(channel_help)

        layout.addWidget(channel_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        # Connect signals for enabling/disabling dependent controls
        self.auto_check_checkbox.toggled.connect(self.on_auto_check_toggled)
        self.auto_download_checkbox.toggled.connect(self.on_auto_download_toggled)

    def populate_settings(self):
        """Populate the dialog with current settings"""
        self.auto_check_checkbox.setChecked(self.current_settings.get('auto_check', True))
        self.interval_spinbox.setValue(self.current_settings.get('check_interval_hours', 24))
        self.auto_download_checkbox.setChecked(self.current_settings.get('download_updates_automatically', False))
        self.auto_install_checkbox.setChecked(self.current_settings.get('install_updates_automatically', False))
        self.backup_checkbox.setChecked(self.current_settings.get('backup_before_update', True))

        channel = self.current_settings.get('update_channel', 'stable')
        index = self.channel_combo.findText(channel)
        if index >= 0:
            self.channel_combo.setCurrentIndex(index)

        # Update dependent controls
        self.on_auto_check_toggled(self.auto_check_checkbox.isChecked())
        self.on_auto_download_toggled(self.auto_download_checkbox.isChecked())

    def on_auto_check_toggled(self, checked: bool):
        """Handle auto-check checkbox toggle"""
        self.interval_spinbox.setEnabled(checked)
        self.auto_download_checkbox.setEnabled(checked)

        if not checked:
            self.auto_download_checkbox.setChecked(False)
            self.auto_install_checkbox.setChecked(False)

    def on_auto_download_toggled(self, checked: bool):
        """Handle auto-download checkbox toggle"""
        self.auto_install_checkbox.setEnabled(checked)

        if not checked:
            self.auto_install_checkbox.setChecked(False)

    def save_settings(self):
        """Save the settings and emit signal"""
        new_settings = {
            'auto_check': self.auto_check_checkbox.isChecked(),
            'check_interval_hours': self.interval_spinbox.value(),
            'download_updates_automatically': self.auto_download_checkbox.isChecked(),
            'install_updates_automatically': self.auto_install_checkbox.isChecked(),
            'backup_before_update': self.backup_checkbox.isChecked(),
            'update_channel': self.channel_combo.currentText()
        }

        self.settings_changed.emit(new_settings)
        self.accept()


class UpdateHistoryDialog(QDialog):
    """Dialog for showing update history and managing backups"""

    def __init__(self, backups: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.backups = backups

        self.setup_ui()
        self.populate_backups()

    def setup_ui(self):
        """Setup the history dialog UI"""
        self.setWindowTitle("Update History & Backups")
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.resize(500, 400)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_label = QLabel("Available Backups")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(header_label)

        # Backup list
        self.backup_list = QListWidget()
        self.backup_list.setAlternatingRowColors(True)
        layout.addWidget(self.backup_list)

        # Buttons
        button_layout = QHBoxLayout()

        self.restore_button = QPushButton("Restore Selected")
        self.restore_button.setEnabled(False)
        self.restore_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        button_layout.addWidget(self.restore_button)

        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        # Connect signals
        self.backup_list.itemSelectionChanged.connect(self.on_selection_changed)

    def populate_backups(self):
        """Populate the backup list"""
        for backup in self.backups:
            item = QListWidgetItem()

            name = backup['name']
            created = backup['created']
            size_mb = backup['size'] / (1024 * 1024)

            try:
                created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                created_str = created_dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                created_str = created

            item.setText(f"{name}\nCreated: {created_str}\nSize: {size_mb:.1f} MB")
            item.setData(Qt.UserRole, backup['path'])

            self.backup_list.addItem(item)

        if not self.backups:
            item = QListWidgetItem("No backups available")
            item.setFlags(Qt.NoItemFlags)
            self.backup_list.addItem(item)

    def on_selection_changed(self):
        """Handle backup selection change"""
        has_selection = bool(self.backup_list.selectedItems())
        self.restore_button.setEnabled(has_selection)

    def get_selected_backup_path(self) -> Optional[str]:
        """Get the path of the selected backup"""
        selected_items = self.backup_list.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.UserRole)
        return None

