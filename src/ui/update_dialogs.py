"""
Update UI Components

This module provides user interface components for the auto-update system,
including update notifications, progress dialogs, and changelog display.
"""

import logging
from typing import Optional, List
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QCheckBox, QGroupBox, QScrollArea,
    QFrame, QSizePolicy, QSpacerItem, QMessageBox
)
from PySide6.QtGui import QFont, QPixmap, QIcon

from ..core.version_manager import VersionInfo
from ..core.update_downloader import DownloadProgress
from ..core.update_installer import InstallationProgress


class UpdateNotificationDialog(QDialog):
    """Dialog to notify users about available updates"""
    
    # Signals
    update_accepted = Signal(VersionInfo)
    update_declined = Signal(VersionInfo)
    update_skipped = Signal(VersionInfo)
    
    def __init__(self, version_info: VersionInfo, parent=None):
        super().__init__(parent)
        self.version_info = version_info
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.setup_ui()
        self.setup_connections()
        self.populate_data()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Update Available")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Icon (you can add an update icon here)
        icon_label = QLabel("🔄")
        icon_label.setFont(QFont("Arial", 24))
        header_layout.addWidget(icon_label)
        
        # Title and version
        title_layout = QVBoxLayout()
        title_label = QLabel("Update Available")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_layout.addWidget(title_label)
        
        version_label = QLabel(f"Version {self.version_info.version}")
        version_label.setFont(QFont("Arial", 12))
        version_label.setStyleSheet("color: #666;")
        title_layout.addWidget(version_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Update info
        info_group = QGroupBox("Update Information")
        info_layout = QVBoxLayout(info_group)
        
        # Release date
        date_label = QLabel(f"Release Date: {self.version_info.release_date}")
        info_layout.addWidget(date_label)
        
        # Channel
        channel_label = QLabel(f"Channel: {self.version_info.channel.title()}")
        info_layout.addWidget(channel_label)
        
        # Size
        size_mb = self.version_info.download_size / (1024 * 1024) if self.version_info.download_size > 0 else 0
        size_label = QLabel(f"Download Size: {size_mb:.1f} MB")
        info_layout.addWidget(size_label)
        
        # Update notes
        if self.version_info.update_notes:
            notes_label = QLabel("Update Notes:")
            notes_label.setFont(QFont("Arial", 10, QFont.Bold))
            info_layout.addWidget(notes_label)
            
            notes_text = QLabel(self.version_info.update_notes)
            notes_text.setWordWrap(True)
            notes_text.setStyleSheet("padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
            info_layout.addWidget(notes_text)
        
        layout.addWidget(info_group)
        
        # Changelog
        changelog_group = QGroupBox("What's New")
        changelog_layout = QVBoxLayout(changelog_group)
        
        self.changelog_text = QTextEdit()
        self.changelog_text.setMaximumHeight(150)
        self.changelog_text.setReadOnly(True)
        changelog_layout.addWidget(self.changelog_text)
        
        layout.addWidget(changelog_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.auto_install_checkbox = QCheckBox("Install automatically after download")
        self.auto_install_checkbox.setChecked(False)
        options_layout.addWidget(self.auto_install_checkbox)
        
        self.backup_checkbox = QCheckBox("Create backup before installing")
        self.backup_checkbox.setChecked(True)
        options_layout.addWidget(self.backup_checkbox)
        
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.skip_button = QPushButton("Skip This Version")
        self.skip_button.setStyleSheet("color: #666;")
        button_layout.addWidget(self.skip_button)
        
        button_layout.addStretch()
        
        self.later_button = QPushButton("Remind Me Later")
        button_layout.addWidget(self.later_button)
        
        self.download_button = QPushButton("Download Update")
        self.download_button.setDefault(True)
        self.download_button.setStyleSheet("""
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
        """)
        button_layout.addWidget(self.download_button)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.download_button.clicked.connect(self.accept_update)
        self.later_button.clicked.connect(self.decline_update)
        self.skip_button.clicked.connect(self.skip_update)
    
    def populate_data(self):
        """Populate the dialog with version data"""
        # Format changelog
        changelog_html = "<html><body>"
        
        if 'changes' in self.version_info.changelog:
            for change in self.version_info.changelog['changes']:
                change_type = change.get('type', 'change')
                description = change.get('description', '')
                
                # Color code by change type
                color = {
                    'feature': '#4CAF50',
                    'improvement': '#2196F3', 
                    'bugfix': '#FF9800',
                    'security': '#F44336',
                    'experimental': '#9C27B0'
                }.get(change_type, '#666')
                
                changelog_html += f"""
                <p style="margin: 5px 0;">
                    <span style="color: {color}; font-weight: bold;">
                        {change_type.title()}:
                    </span>
                    {description}
                </p>
                """
        
        changelog_html += "</body></html>"
        self.changelog_text.setHtml(changelog_html)
    
    def accept_update(self):
        """Handle update acceptance"""
        self.update_accepted.emit(self.version_info)
        self.accept()
    
    def decline_update(self):
        """Handle update decline"""
        self.update_declined.emit(self.version_info)
        self.reject()
    
    def skip_update(self):
        """Handle update skip"""
        self.update_skipped.emit(self.version_info)
        self.reject()
    
    def get_install_options(self) -> dict:
        """Get user-selected install options"""
        return {
            'auto_install': self.auto_install_checkbox.isChecked(),
            'create_backup': self.backup_checkbox.isChecked()
        }


class UpdateProgressDialog(QDialog):
    """Dialog to show update download and installation progress"""

    # Signals
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.current_stage = "idle"
        self.can_cancel = True

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Updating Application")
        self.setFixedSize(500, 300)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Header
        header_label = QLabel("Updating Personal Finance Dashboard")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        # Status
        self.status_label = QLabel("Preparing update...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Details
        self.details_label = QLabel("")
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.details_label)

        # Speed and ETA (for downloads)
        self.speed_eta_label = QLabel("")
        self.speed_eta_label.setAlignment(Qt.AlignCenter)
        self.speed_eta_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.speed_eta_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(True)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def setup_connections(self):
        """Setup signal connections"""
        self.cancel_button.clicked.connect(self.request_cancel)

    def update_download_progress(self, progress: DownloadProgress):
        """Update progress for download stage"""
        self.current_stage = "download"
        self.progress_bar.setValue(int(progress.percentage))
        self.status_label.setText(f"Downloading update... {progress.percentage:.1f}%")

        # Format details
        downloaded = self.format_bytes(progress.bytes_downloaded)
        total = self.format_bytes(progress.total_bytes)
        speed = self.format_speed(progress.speed_bps)
        eta = self.format_time(progress.eta_seconds)

        self.details_label.setText(f"{downloaded} of {total}")
        self.speed_eta_label.setText(f"Speed: {speed} • ETA: {eta}")

    def update_installation_progress(self, progress: InstallationProgress):
        """Update progress for installation stage"""
        self.current_stage = "install"
        self.progress_bar.setValue(int(progress.progress))
        self.status_label.setText(progress.message)
        self.details_label.setText(progress.details)
        self.speed_eta_label.setText("")

        # Disable cancel during critical stages
        if progress.stage in ["install", "verify"]:
            self.can_cancel = False
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Please Wait...")

    def set_completed(self, success: bool, message: str):
        """Set completion state"""
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("✅ " + message)
            self.details_label.setText("Update completed successfully")
            self.cancel_button.setText("Close")
            self.cancel_button.setEnabled(True)
        else:
            self.status_label.setText("❌ " + message)
            self.details_label.setText("Update failed")
            self.cancel_button.setText("Close")
            self.cancel_button.setEnabled(True)

    def request_cancel(self):
        """Handle cancel request"""
        if self.can_cancel and self.current_stage != "completed":
            reply = QMessageBox.question(
                self, "Cancel Update",
                "Are you sure you want to cancel the update?\n"
                "This may leave the application in an inconsistent state.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.cancel_requested.emit()
        else:
            self.accept()

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"

    def format_speed(self, bps: float) -> str:
        """Format speed into human readable format"""
        return f"{self.format_bytes(int(bps))}/s"

    def format_time(self, seconds: float) -> str:
        """Format time into human readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


class UpdateSettingsWidget(QFrame):
    """Widget for update settings in the main settings dialog"""

    # Signals
    settings_changed = Signal()
    check_for_updates_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.setup_ui()
        self.setup_connections()
        self.load_settings()

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Auto-check settings
        auto_check_group = QGroupBox("Automatic Update Checking")
        auto_check_layout = QVBoxLayout(auto_check_group)

        self.auto_check_checkbox = QCheckBox("Check for updates automatically")
        auto_check_layout.addWidget(self.auto_check_checkbox)

        # Check interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Check every:"))

        from PySide6.QtWidgets import QSpinBox
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 168)  # 1 hour to 1 week
        self.interval_spinbox.setValue(24)
        self.interval_spinbox.setSuffix(" hours")
        interval_layout.addWidget(self.interval_spinbox)

        interval_layout.addStretch()
        auto_check_layout.addLayout(interval_layout)

        layout.addWidget(auto_check_group)

        # Update channel
        channel_group = QGroupBox("Update Channel")
        channel_layout = QVBoxLayout(channel_group)

        from PySide6.QtWidgets import QRadioButton, QButtonGroup
        self.channel_group = QButtonGroup()

        self.stable_radio = QRadioButton("Stable (Recommended)")
        self.stable_radio.setToolTip("Stable, tested releases")
        self.channel_group.addButton(self.stable_radio, 0)
        channel_layout.addWidget(self.stable_radio)

        self.beta_radio = QRadioButton("Beta")
        self.beta_radio.setToolTip("Pre-release versions with new features")
        self.channel_group.addButton(self.beta_radio, 1)
        channel_layout.addWidget(self.beta_radio)

        self.dev_radio = QRadioButton("Development")
        self.dev_radio.setToolTip("Latest development builds (may be unstable)")
        self.channel_group.addButton(self.dev_radio, 2)
        channel_layout.addWidget(self.dev_radio)

        layout.addWidget(channel_group)

        # Auto-install settings
        install_group = QGroupBox("Installation Options")
        install_layout = QVBoxLayout(install_group)

        self.auto_download_checkbox = QCheckBox("Download updates automatically")
        install_layout.addWidget(self.auto_download_checkbox)

        self.auto_install_checkbox = QCheckBox("Install updates automatically")
        install_layout.addWidget(self.auto_install_checkbox)

        self.backup_checkbox = QCheckBox("Create backup before installing updates")
        self.backup_checkbox.setChecked(True)
        install_layout.addWidget(self.backup_checkbox)

        layout.addWidget(install_group)

        # Manual check
        manual_group = QGroupBox("Manual Check")
        manual_layout = QVBoxLayout(manual_group)

        manual_button_layout = QHBoxLayout()
        self.check_now_button = QPushButton("Check for Updates Now")
        manual_button_layout.addWidget(self.check_now_button)
        manual_button_layout.addStretch()

        manual_layout.addLayout(manual_button_layout)

        self.last_check_label = QLabel("Last checked: Never")
        self.last_check_label.setStyleSheet("color: #666; font-size: 11px;")
        manual_layout.addWidget(self.last_check_label)

        layout.addWidget(manual_group)

        layout.addStretch()

    def setup_connections(self):
        """Setup signal connections"""
        self.auto_check_checkbox.toggled.connect(self.on_settings_changed)
        self.interval_spinbox.valueChanged.connect(self.on_settings_changed)
        self.channel_group.buttonToggled.connect(self.on_settings_changed)
        self.auto_download_checkbox.toggled.connect(self.on_settings_changed)
        self.auto_install_checkbox.toggled.connect(self.on_settings_changed)
        self.backup_checkbox.toggled.connect(self.on_settings_changed)
        self.check_now_button.clicked.connect(self.check_for_updates_requested.emit)

        # Enable/disable interval when auto-check is toggled
        self.auto_check_checkbox.toggled.connect(self.interval_spinbox.setEnabled)

    def load_settings(self):
        """Load current update settings"""
        try:
            from ..core.version_manager import VersionManager
            version_manager = VersionManager()
            settings = version_manager.settings

            self.auto_check_checkbox.setChecked(settings.auto_check)
            self.interval_spinbox.setValue(settings.check_interval_hours)
            self.interval_spinbox.setEnabled(settings.auto_check)

            # Set channel
            channel_map = {"stable": 0, "beta": 1, "dev": 2}
            channel_id = channel_map.get(settings.update_channel, 0)
            self.channel_group.button(channel_id).setChecked(True)

            self.auto_download_checkbox.setChecked(settings.download_updates_automatically)
            self.auto_install_checkbox.setChecked(settings.install_updates_automatically)
            self.backup_checkbox.setChecked(settings.backup_before_update)

            # Update last check time
            if settings.last_check:
                try:
                    last_check = datetime.fromisoformat(settings.last_check.replace('Z', '+00:00'))
                    self.last_check_label.setText(f"Last checked: {last_check.strftime('%Y-%m-%d %H:%M')}")
                except Exception:
                    self.last_check_label.setText("Last checked: Unknown")

        except Exception as e:
            self.logger.error(f"Error loading update settings: {e}")

    def save_settings(self):
        """Save current update settings"""
        try:
            from ..core.version_manager import VersionManager
            version_manager = VersionManager()

            version_manager.settings.auto_check = self.auto_check_checkbox.isChecked()
            version_manager.settings.check_interval_hours = self.interval_spinbox.value()

            # Get selected channel
            channel_map = {0: "stable", 1: "beta", 2: "dev"}
            channel_id = self.channel_group.checkedId()
            version_manager.settings.update_channel = channel_map.get(channel_id, "stable")

            version_manager.settings.download_updates_automatically = self.auto_download_checkbox.isChecked()
            version_manager.settings.install_updates_automatically = self.auto_install_checkbox.isChecked()
            version_manager.settings.backup_before_update = self.backup_checkbox.isChecked()

            version_manager.save_settings()

        except Exception as e:
            self.logger.error(f"Error saving update settings: {e}")

    def on_settings_changed(self):
        """Handle settings change"""
        self.save_settings()
        self.settings_changed.emit()
