"""
Main Update Manager

This module coordinates all update-related functionality including version checking,
downloading, installation, and user interface integration.
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from .version_manager import VersionManager, VersionInfo
from .update_downloader import UpdateDownloader, DownloadProgress
from .update_installer import UpdateInstaller, InstallationProgress
from ..ui.update_dialogs import UpdateNotificationDialog, UpdateProgressDialog


class UpdateManager(QObject):
    """Main update manager that coordinates all update functionality"""
    
    # Signals
    update_check_started = Signal()
    update_check_completed = Signal(bool, str)  # success, message
    update_available = Signal(VersionInfo)
    update_download_started = Signal(str)  # version
    update_download_completed = Signal(str)  # version
    update_installation_started = Signal(str)  # version
    update_installation_completed = Signal(str)  # version
    update_failed = Signal(str, str)  # stage, error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Core components
        self.version_manager = VersionManager()
        self.downloader = UpdateDownloader()
        self.installer = UpdateInstaller()
        
        # UI components
        self.notification_dialog: Optional[UpdateNotificationDialog] = None
        self.progress_dialog: Optional[UpdateProgressDialog] = None
        
        # State
        self.current_update_info: Optional[VersionInfo] = None
        self.auto_install_after_download = False
        self.create_backup_before_install = True
        
        # Auto-check timer
        self.auto_check_timer = QTimer()
        self.auto_check_timer.timeout.connect(self.check_for_updates)
        
        self.setup_connections()
        self.setup_auto_check()
        
        self.logger.info("UpdateManager initialized")
    
    def setup_connections(self):
        """Setup signal connections between components"""
        # Version manager connections
        self.version_manager.version_check_started.connect(self.update_check_started.emit)
        self.version_manager.version_check_completed.connect(self.update_check_completed.emit)
        self.version_manager.new_version_available.connect(self.on_new_version_available)
        self.version_manager.no_updates_available.connect(self.on_no_updates_available)
        self.version_manager.version_check_error.connect(self.on_version_check_error)
        
        # Downloader connections
        self.downloader.download_started.connect(self.on_download_started)
        self.downloader.download_progress.connect(self.on_download_progress)
        self.downloader.download_completed.connect(self.on_download_completed)
        self.downloader.download_failed.connect(self.on_download_failed)
        self.downloader.download_cancelled.connect(self.on_download_cancelled)
        
        # Installer connections
        self.installer.installation_started.connect(self.on_installation_started)
        self.installer.installation_progress.connect(self.on_installation_progress)
        self.installer.installation_completed.connect(self.on_installation_completed)
        self.installer.installation_failed.connect(self.on_installation_failed)
        self.installer.restart_required.connect(self.on_restart_required)
    
    def setup_auto_check(self):
        """Setup automatic update checking"""
        if self.version_manager.settings.auto_check:
            # Check immediately if it's time
            if self.version_manager.should_check_for_updates():
                QTimer.singleShot(5000, self.check_for_updates)  # Check after 5 seconds
            
            # Setup periodic checking
            interval_ms = self.version_manager.settings.check_interval_hours * 60 * 60 * 1000
            self.auto_check_timer.start(interval_ms)
            self.logger.info(f"Auto-check enabled with {self.version_manager.settings.check_interval_hours}h interval")
    
    def set_current_version(self, version: str):
        """Set the current application version"""
        self.version_manager.set_current_version(version)
    
    def check_for_updates(self, show_no_updates: bool = False) -> bool:
        """Check for updates"""
        try:
            self.logger.info("Checking for updates...")
            version_info = self.version_manager.check_for_updates()
            
            if version_info is None and show_no_updates:
                QMessageBox.information(
                    QApplication.activeWindow(),
                    "No Updates",
                    "You are running the latest version of Personal Finance Dashboard."
                )
            
            return version_info is not None
            
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            if show_no_updates:
                QMessageBox.warning(
                    QApplication.activeWindow(),
                    "Update Check Failed",
                    f"Failed to check for updates:\n{str(e)}"
                )
            return False
    
    def on_new_version_available(self, version_info: VersionInfo):
        """Handle new version available"""
        self.current_update_info = version_info
        self.update_available.emit(version_info)
        
        # Show notification dialog
        self.show_update_notification(version_info)
    
    def on_no_updates_available(self):
        """Handle no updates available"""
        self.logger.info("No updates available")
    
    def on_version_check_error(self, error_message: str):
        """Handle version check error"""
        self.logger.error(f"Version check error: {error_message}")
    
    def show_update_notification(self, version_info: VersionInfo):
        """Show update notification dialog"""
        if self.notification_dialog is not None:
            return  # Dialog already shown
        
        self.notification_dialog = UpdateNotificationDialog(version_info)
        self.notification_dialog.update_accepted.connect(self.on_update_accepted)
        self.notification_dialog.update_declined.connect(self.on_update_declined)
        self.notification_dialog.update_skipped.connect(self.on_update_skipped)
        self.notification_dialog.finished.connect(self.on_notification_dialog_closed)
        
        self.notification_dialog.show()
    
    def on_update_accepted(self, version_info: VersionInfo):
        """Handle update acceptance"""
        if self.notification_dialog:
            options = self.notification_dialog.get_install_options()
            self.auto_install_after_download = options['auto_install']
            self.create_backup_before_install = options['create_backup']
        
        self.start_update_download(version_info)
    
    def on_update_declined(self, version_info: VersionInfo):
        """Handle update decline"""
        self.logger.info(f"User declined update to version {version_info.version}")
    
    def on_update_skipped(self, version_info: VersionInfo):
        """Handle update skip"""
        self.version_manager.skip_version(version_info.version)
        self.logger.info(f"User skipped version {version_info.version}")
    
    def on_notification_dialog_closed(self):
        """Handle notification dialog closed"""
        self.notification_dialog = None
    
    def start_update_download(self, version_info: VersionInfo):
        """Start downloading an update"""
        if not version_info.download_url:
            QMessageBox.warning(
                QApplication.activeWindow(),
                "Download Error",
                "No download URL available for this update."
            )
            return
        
        # Show progress dialog
        self.progress_dialog = UpdateProgressDialog()
        self.progress_dialog.cancel_requested.connect(self.cancel_update)
        self.progress_dialog.show()
        
        # Start download
        filename = f"PersonalFinanceDashboard-{version_info.version}.exe"
        self.downloader.download_update(
            version_info.download_url,
            filename,
            version_info.checksum
        )
    
    def cancel_update(self):
        """Cancel current update process"""
        self.downloader.cancel_download()
        if self.progress_dialog:
            self.progress_dialog.accept()
    
    def on_download_started(self, filename: str):
        """Handle download started"""
        self.logger.info(f"Download started: {filename}")
        self.update_download_started.emit(self.current_update_info.version)
    
    def on_download_progress(self, progress: DownloadProgress):
        """Handle download progress"""
        if self.progress_dialog:
            self.progress_dialog.update_download_progress(progress)
    
    def on_download_completed(self, filename: str, file_path: str):
        """Handle download completed"""
        self.logger.info(f"Download completed: {filename}")
        self.update_download_completed.emit(self.current_update_info.version)
        
        if self.auto_install_after_download:
            self.start_update_installation(Path(file_path))
        else:
            if self.progress_dialog:
                self.progress_dialog.set_completed(True, "Download completed")
                # Ask user if they want to install now
                QTimer.singleShot(2000, lambda: self.ask_install_now(Path(file_path)))
    
    def on_download_failed(self, filename: str, error_message: str):
        """Handle download failed"""
        self.logger.error(f"Download failed: {filename} - {error_message}")
        self.update_failed.emit("download", error_message)
        
        if self.progress_dialog:
            self.progress_dialog.set_completed(False, f"Download failed: {error_message}")
    
    def on_download_cancelled(self, filename: str):
        """Handle download cancelled"""
        self.logger.info(f"Download cancelled: {filename}")
        if self.progress_dialog:
            self.progress_dialog.accept()
    
    def ask_install_now(self, update_file_path: Path):
        """Ask user if they want to install now"""
        if self.progress_dialog:
            self.progress_dialog.accept()
        
        reply = QMessageBox.question(
            QApplication.activeWindow(),
            "Install Update",
            "Update downloaded successfully.\nWould you like to install it now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.start_update_installation(update_file_path)
    
    def start_update_installation(self, update_file_path: Path):
        """Start installing an update"""
        if not self.progress_dialog:
            self.progress_dialog = UpdateProgressDialog()
            self.progress_dialog.show()
        
        # Start installation
        self.installer.install_update(
            update_file_path,
            self.current_update_info.version,
            self.create_backup_before_install
        )

    def on_installation_started(self, version: str):
        """Handle installation started"""
        self.logger.info(f"Installation started: {version}")
        self.update_installation_started.emit(version)

    def on_installation_progress(self, progress: InstallationProgress):
        """Handle installation progress"""
        if self.progress_dialog:
            self.progress_dialog.update_installation_progress(progress)

    def on_installation_completed(self, version: str, install_path: str):
        """Handle installation completed"""
        self.logger.info(f"Installation completed: {version}")
        self.update_installation_completed.emit(version)

        if self.progress_dialog:
            self.progress_dialog.set_completed(True, "Installation completed")

        # Ask user about restart
        QTimer.singleShot(2000, self.ask_restart_application)

    def on_installation_failed(self, version: str, error_message: str):
        """Handle installation failed"""
        self.logger.error(f"Installation failed: {version} - {error_message}")
        self.update_failed.emit("installation", error_message)

        if self.progress_dialog:
            self.progress_dialog.set_completed(False, f"Installation failed: {error_message}")

    def on_restart_required(self):
        """Handle restart required"""
        self.ask_restart_application()

    def ask_restart_application(self):
        """Ask user to restart the application"""
        if self.progress_dialog:
            self.progress_dialog.accept()

        reply = QMessageBox.question(
            QApplication.activeWindow(),
            "Restart Required",
            "The update has been installed successfully.\n"
            "The application needs to be restarted to complete the update.\n\n"
            "Would you like to restart now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.restart_application()

    def restart_application(self):
        """Restart the application"""
        try:
            self.installer.restart_application()
        except Exception as e:
            self.logger.error(f"Error restarting application: {e}")
            QMessageBox.warning(
                QApplication.activeWindow(),
                "Restart Failed",
                f"Failed to restart automatically: {str(e)}\n\n"
                "Please restart the application manually to complete the update."
            )

    def get_update_settings_widget(self):
        """Get the update settings widget for the settings dialog"""
        from ..ui.update_dialogs import UpdateSettingsWidget
        widget = UpdateSettingsWidget()
        widget.check_for_updates_requested.connect(lambda: self.check_for_updates(show_no_updates=True))
        return widget

    def cleanup(self):
        """Cleanup resources"""
        if self.auto_check_timer.isActive():
            self.auto_check_timer.stop()

        if self.notification_dialog:
            self.notification_dialog.close()

        if self.progress_dialog:
            self.progress_dialog.close()

        # Clean up old downloads
        self.downloader.clean_old_downloads()


# Global update manager instance
update_manager = UpdateManager()
