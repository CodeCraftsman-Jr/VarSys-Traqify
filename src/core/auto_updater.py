#!/usr/bin/env python3
"""
Auto-updater for the Personal Finance Dashboard
Checks for updates and downloads/installs them automatically
"""

import os
import sys
import json
import logging
import requests
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication

from .secure_config import get_secure_config

class UpdateInfo:
    """Information about an available update"""
    def __init__(self, data: Dict[str, Any]):
        self.latest_version = data.get('latest_version', '1.0.0')
        self.download_url = data.get('download_url', '')
        self.release_notes = data.get('release_notes', '')
        self.force_update = data.get('force_update', False)
        self.min_supported_version = data.get('min_supported_version', '1.0.0')

class UpdateDownloader(QThread):
    """Downloads update in background"""
    progress = Signal(int)  # Progress percentage
    finished = Signal(str)  # Downloaded file path
    error = Signal(str)     # Error message

    def __init__(self, download_url: str, file_path: str):
        super().__init__()
        self.download_url = download_url
        self.file_path = file_path
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._should_stop = False

    def stop(self):
        """Request the thread to stop"""
        self._should_stop = True
        self.logger.info("Download stop requested")

    def run(self):
        """Download the update file"""
        try:
            self.logger.info(f"Downloading update from: {self.download_url}")

            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(self.file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    # Check if we should stop
                    if self._should_stop:
                        self.logger.info("Download cancelled by user")
                        return

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress.emit(progress)

            # Check if we were stopped before completion
            if self._should_stop:
                self.logger.info("Download cancelled before completion")
                return

            self.logger.info(f"Update downloaded successfully: {self.file_path}")
            self.finished.emit(self.file_path)

        except Exception as e:
            if not self._should_stop:  # Only log error if not intentionally stopped
                self.logger.error(f"Download failed: {e}")
                self.error.emit(str(e))

class AutoUpdater(QObject):
    """Handles automatic updates for the application"""

    update_available = Signal(UpdateInfo)
    update_downloaded = Signal(str)  # File path
    update_failed = Signal(str)      # Error message

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = get_secure_config()
        self.current_version = "1.0.0"  # This should be read from app config
        self.downloader = None
        self._cleanup_timer = QTimer()
        self._cleanup_timer.setSingleShot(True)
        self._cleanup_timer.timeout.connect(self._force_cleanup)

    def __del__(self):
        """Destructor - ensure proper cleanup"""
        self.cleanup()

    def cleanup(self):
        """Clean up any running threads"""
        if self.downloader and self.downloader.isRunning():
            self.logger.info("Cleaning up download thread...")
            self.downloader.stop()

            # Wait for thread to finish, but not indefinitely
            if not self.downloader.wait(3000):  # Wait up to 3 seconds
                self.logger.warning("Download thread did not stop gracefully, terminating...")
                self.downloader.terminate()
                self.downloader.wait(1000)  # Wait up to 1 second for termination

            self.downloader = None
            self.logger.info("Download thread cleanup completed")
        
    def check_for_updates(self, silent: bool = True) -> Optional[UpdateInfo]:
        """Check if updates are available"""
        try:
            version_url = f"{self.config.functions_base_url}/app/version"
            self.logger.info(f"Checking for updates: {version_url}")
            
            response = requests.get(version_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            update_info = UpdateInfo(data)
            
            if self._is_newer_version(update_info.latest_version, self.current_version):
                self.logger.info(f"Update available: {update_info.latest_version}")
                if not silent:
                    self.update_available.emit(update_info)
                return update_info
            else:
                self.logger.info("Application is up to date")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to check for updates: {e}")
            if not silent:
                self.update_failed.emit(str(e))
            return None
    
    def download_update(self, update_info: UpdateInfo):
        """Download the update"""
        try:
            # Clean up any existing downloader
            self.cleanup()

            # Create temporary file for download
            temp_dir = tempfile.gettempdir()
            filename = f"Traqify_v{update_info.latest_version}.exe"
            temp_path = os.path.join(temp_dir, filename)

            # Start download in background
            self.downloader = UpdateDownloader(update_info.download_url, temp_path)

            # Connect signals
            self.downloader.finished.connect(self._on_download_finished)
            self.downloader.error.connect(self._on_download_error)

            # Set up cleanup timer as a safety net
            self._cleanup_timer.start(300000)  # 5 minutes timeout

            self.downloader.start()
            self.logger.info("Download started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start download: {e}")
            self.update_failed.emit(str(e))
    
    def install_update(self, update_file_path: str):
        """Install the downloaded update (handles both EXE and ZIP)"""
        try:
            if update_file_path.lower().endswith('.zip'):
                self.install_zip_update(update_file_path)
            else:
                self.install_exe_update(update_file_path)

        except Exception as e:
            self.logger.error(f"Failed to install update: {e}")
            self.update_failed.emit(str(e))

    def install_zip_update(self, zip_file_path: str):
        """Install update from ZIP file"""
        try:
            import zipfile
            import shutil

            # Get current application directory
            if getattr(sys, 'frozen', False):
                app_dir = Path(sys.executable).parent
            else:
                app_dir = Path(__file__).parent.parent.parent

            # Extract ZIP to temporary directory
            temp_dir = Path(tempfile.gettempdir()) / "traqify_update"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir()

            with zipfile.ZipFile(zip_file_path, 'r') as zipf:
                zipf.extractall(temp_dir)

            # Find the setup file in extracted content
            setup_files = list(temp_dir.glob("*.exe"))
            if not setup_files:
                raise Exception("No executable found in update ZIP")

            setup_file = setup_files[0]

            # Create batch script to run the setup and exit current app
            batch_script = f"""
@echo off
echo Installing Traqify update...
timeout /t 2 /nobreak > nul
start "" "{setup_file}" /SILENT /NORESTART
del "%~f0"
"""

            batch_path = temp_dir / "install_update.bat"
            with open(batch_path, 'w') as f:
                f.write(batch_script)

            # Run the batch script and exit
            subprocess.Popen([str(batch_path)], shell=True, cwd=str(temp_dir))
            QApplication.quit()

        except Exception as e:
            self.logger.error(f"Failed to install ZIP update: {e}")
            self.update_failed.emit(str(e))

    def install_exe_update(self, exe_file_path: str):
        """Install update from EXE file (fallback method)"""
        try:
            current_exe = sys.executable
            if getattr(sys, 'frozen', False):
                # Running as executable
                current_exe = sys.argv[0]

            # Create batch script to replace the executable
            batch_script = f"""
@echo off
timeout /t 2 /nobreak > nul
move /y "{exe_file_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""

            batch_path = os.path.join(tempfile.gettempdir(), "update_installer.bat")
            with open(batch_path, 'w') as f:
                f.write(batch_script)

            # Run the batch script and exit
            subprocess.Popen([batch_path], shell=True)
            QApplication.quit()

        except Exception as e:
            self.logger.error(f"Failed to install EXE update: {e}")
            self.update_failed.emit(str(e))
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad with zeros if needed
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return False
    
    def _on_download_finished(self, file_path: str):
        """Handle download completion"""
        self.logger.info(f"Download completed: {file_path}")
        self._cleanup_timer.stop()  # Stop the safety timer
        self.update_downloaded.emit(file_path)
        # Note: Don't cleanup the downloader here as it might still be needed

    def _on_download_error(self, error: str):
        """Handle download error"""
        self.logger.error(f"Download error: {error}")
        self._cleanup_timer.stop()  # Stop the safety timer
        self.update_failed.emit(error)
        # Cleanup the failed downloader
        self.cleanup()

    def _force_cleanup(self):
        """Force cleanup when timeout is reached"""
        self.logger.warning("Download timeout reached, forcing cleanup")
        self.cleanup()

def show_update_dialog(update_info: UpdateInfo) -> bool:
    """Show update dialog to user"""
    msg = QMessageBox()
    msg.setWindowTitle("Update Available")
    msg.setIcon(QMessageBox.Information)
    
    text = f"""
A new version of Traqify is available!

Current Version: 1.0.0
Latest Version: {update_info.latest_version}

Release Notes:
{update_info.release_notes}

Would you like to download and install the update?
"""
    
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.Yes)
    
    if update_info.force_update:
        msg.setText(text + "\n\nThis is a required update.")
        msg.setStandardButtons(QMessageBox.Yes)
    
    return msg.exec() == QMessageBox.Yes

def show_download_progress() -> QProgressDialog:
    """Show download progress dialog"""
    progress = QProgressDialog("Downloading update...", "Cancel", 0, 100)
    progress.setWindowTitle("Updating Traqify")
    progress.setModal(True)
    progress.show()
    return progress
