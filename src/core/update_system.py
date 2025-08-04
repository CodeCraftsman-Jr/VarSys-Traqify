#!/usr/bin/env python3
"""
Update System Module
Handles application updates, version checking, and installation
"""

import os
import sys
import json
import logging
import hashlib
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from urllib.parse import urlparse
import requests
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QApplication


@dataclass
class VersionInfo:
    """Version information structure"""
    version: str
    build_number: int
    release_date: str
    download_url: str
    changelog: List[str]
    file_size: int
    checksum: str
    is_critical: bool = False
    min_version_required: str = "1.0.0"
    
    def __post_init__(self):
        if isinstance(self.changelog, str):
            self.changelog = [self.changelog]


@dataclass
class UpdateSettings:
    """Update system settings"""
    auto_check: bool = True
    check_interval_hours: int = 24
    download_updates_automatically: bool = False
    install_updates_automatically: bool = False
    backup_before_update: bool = True
    update_channel: str = "stable"  # stable, beta, alpha
    last_check: Optional[str] = None
    skip_version: Optional[str] = None


class UpdateChecker(QThread):
    """Thread for checking updates"""
    
    # Signals
    update_available = Signal(dict)  # version_info
    no_update_available = Signal()
    check_failed = Signal(str)  # error message
    progress_updated = Signal(int, str)  # progress, message
    
    def __init__(self, current_version: str, update_url: str, settings: UpdateSettings):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.current_version = current_version
        self.update_url = update_url
        self.settings = settings
        self._should_stop = False
        
    def run(self):
        """Check for updates"""
        try:
            self.progress_updated.emit(10, "Connecting to update server...")
            
            # Make request to update server
            headers = {
                'User-Agent': f'PersonalFinanceDashboard/{self.current_version}',
                'X-Current-Version': self.current_version,
                'X-Update-Channel': self.settings.update_channel
            }
            
            response = requests.get(self.update_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            self.progress_updated.emit(50, "Processing update information...")
            
            update_data = response.json()
            
            # Parse version info
            latest_version = update_data.get('latest_version')
            if not latest_version:
                self.check_failed.emit("Invalid update response: missing version info")
                return
                
            version_info = VersionInfo(**latest_version)
            
            self.progress_updated.emit(80, "Comparing versions...")
            
            # Compare versions
            if self._is_newer_version(version_info.version, self.current_version):
                # Check if this version should be skipped
                if self.settings.skip_version == version_info.version:
                    self.logger.info(f"Skipping version {version_info.version} as requested")
                    self.no_update_available.emit()
                else:
                    self.logger.info(f"Update available: {version_info.version}")
                    self.update_available.emit(asdict(version_info))
            else:
                self.logger.info("No updates available")
                self.no_update_available.emit()
                
            self.progress_updated.emit(100, "Update check complete")
            
        except requests.RequestException as e:
            error_msg = f"Network error during update check: {e}"
            self.logger.error(error_msg)
            self.check_failed.emit(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid update response format: {e}"
            self.logger.error(error_msg)
            self.check_failed.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during update check: {e}"
            self.logger.error(error_msg)
            self.check_failed.emit(error_msg)
            
    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """Compare version strings"""
        try:
            # Simple version comparison (assumes semantic versioning)
            new_parts = [int(x) for x in new_version.split('.')]
            current_parts = [int(x) for x in current_version.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(new_parts), len(current_parts))
            new_parts.extend([0] * (max_len - len(new_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return new_parts > current_parts
        except (ValueError, AttributeError):
            self.logger.warning(f"Could not compare versions: {new_version} vs {current_version}")
            return False
            
    def stop(self):
        """Stop the update check"""
        self._should_stop = True


class UpdateDownloader(QThread):
    """Thread for downloading updates"""
    
    # Signals
    download_progress = Signal(int, int, int)  # bytes_downloaded, total_bytes, percentage
    download_completed = Signal(str)  # file_path
    download_failed = Signal(str)  # error message
    checksum_verified = Signal(bool)  # verification result
    
    def __init__(self, version_info: VersionInfo, download_dir: Path):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.version_info = version_info
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._should_stop = False
        
    def run(self):
        """Download the update"""
        try:
            url = self.version_info.download_url
            filename = Path(urlparse(url).path).name
            if not filename:
                filename = f"update_{self.version_info.version}.exe"
                
            file_path = self.download_dir / filename
            
            self.logger.info(f"Downloading update from {url} to {file_path}")
            
            # Download with progress tracking
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._should_stop:
                        f.close()
                        file_path.unlink(missing_ok=True)
                        return
                        
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            percentage = int((downloaded_size / total_size) * 100)
                            self.download_progress.emit(downloaded_size, total_size, percentage)
                            
            self.logger.info(f"Download completed: {file_path}")
            
            # Verify checksum if provided
            if self.version_info.checksum:
                self.logger.info("Verifying download integrity...")
                if self._verify_checksum(file_path, self.version_info.checksum):
                    self.checksum_verified.emit(True)
                    self.download_completed.emit(str(file_path))
                else:
                    self.checksum_verified.emit(False)
                    self.download_failed.emit("Download verification failed: checksum mismatch")
                    file_path.unlink(missing_ok=True)
            else:
                self.download_completed.emit(str(file_path))
                
        except requests.RequestException as e:
            error_msg = f"Download failed: {e}"
            self.logger.error(error_msg)
            self.download_failed.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during download: {e}"
            self.logger.error(error_msg)
            self.download_failed.emit(error_msg)
            
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_checksum = sha256_hash.hexdigest()
            return actual_checksum.lower() == expected_checksum.lower()
        except Exception as e:
            self.logger.error(f"Checksum verification failed: {e}")
            return False
            
    def stop(self):
        """Stop the download"""
        self._should_stop = True


class UpdateInstaller:
    """Handles update installation"""
    
    def __init__(self, app_dir: Path, backup_dir: Path):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.app_dir = Path(app_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self) -> bool:
        """Create backup of current application"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            
            self.logger.info(f"Creating backup at {backup_path}")
            
            # Copy current application files
            if self.app_dir.exists():
                shutil.copytree(self.app_dir, backup_path, ignore=shutil.ignore_patterns('*.log', '__pycache__'))
                
            self.logger.info("Backup created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            return False
            
    def install_update(self, installer_path: Path, silent: bool = True) -> bool:
        """Install the update"""
        try:
            if not installer_path.exists():
                self.logger.error(f"Installer not found: {installer_path}")
                return False
                
            self.logger.info(f"Installing update from {installer_path}")
            
            # Prepare installation command
            cmd = [str(installer_path)]
            if silent:
                cmd.extend(['/SILENT', '/NORESTART'])
                
            # Run installer
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("Update installed successfully")
                return True
            else:
                self.logger.error(f"Installation failed with code {result.returncode}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            return False
            
    def rollback_update(self, backup_path: Path) -> bool:
        """Rollback to previous version"""
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup not found: {backup_path}")
                return False
                
            self.logger.info(f"Rolling back from backup: {backup_path}")
            
            # Remove current installation
            if self.app_dir.exists():
                shutil.rmtree(self.app_dir)
                
            # Restore from backup
            shutil.copytree(backup_path, self.app_dir)
            
            self.logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False


class UpdateManager(QObject):
    """Main update manager that coordinates all update operations"""

    # Signals
    update_check_started = Signal()
    update_available = Signal(dict)  # version_info
    no_update_available = Signal()
    update_check_failed = Signal(str)

    download_started = Signal()
    download_progress = Signal(int, int, int)  # bytes_downloaded, total_bytes, percentage
    download_completed = Signal(str)  # file_path
    download_failed = Signal(str)

    installation_started = Signal()
    installation_completed = Signal()
    installation_failed = Signal(str)

    backup_created = Signal(str)  # backup_path
    backup_failed = Signal(str)

    def __init__(self, current_version: str, app_dir: Path, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.current_version = current_version
        self.app_dir = Path(app_dir)

        # Directories
        self.update_dir = self.app_dir / "updates"
        self.backup_dir = self.app_dir / "backups"
        self.download_dir = self.update_dir / "downloads"

        # Ensure directories exist
        self.update_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Settings
        self.settings = self.load_settings()

        # Components
        self.update_checker = None
        self.downloader = None
        self.installer = UpdateInstaller(self.app_dir, self.backup_dir)

        # Auto-check timer
        self.auto_check_timer = QTimer()
        self.auto_check_timer.timeout.connect(self.check_for_updates)

        # Start auto-check if enabled
        if self.settings.auto_check:
            self.start_auto_check()

    def load_settings(self) -> UpdateSettings:
        """Load update settings"""
        settings_file = self.update_dir / "update_settings.json"

        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                return UpdateSettings(**data)
            except Exception as e:
                self.logger.warning(f"Failed to load update settings: {e}")

        return UpdateSettings()

    def save_settings(self):
        """Save update settings"""
        settings_file = self.update_dir / "update_settings.json"

        try:
            with open(settings_file, 'w') as f:
                json.dump(asdict(self.settings), f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save update settings: {e}")

    def start_auto_check(self):
        """Start automatic update checking"""
        if self.settings.auto_check and self.settings.check_interval_hours > 0:
            interval_ms = self.settings.check_interval_hours * 60 * 60 * 1000
            self.auto_check_timer.start(interval_ms)
            self.logger.info(f"Auto-check enabled: every {self.settings.check_interval_hours} hours")

            # Check if we should check now
            if self.should_check_now():
                QTimer.singleShot(5000, self.check_for_updates)  # Check after 5 seconds

    def stop_auto_check(self):
        """Stop automatic update checking"""
        self.auto_check_timer.stop()
        self.logger.info("Auto-check disabled")

    def should_check_now(self) -> bool:
        """Check if we should check for updates now"""
        if not self.settings.last_check:
            return True

        try:
            last_check = datetime.fromisoformat(self.settings.last_check)
            now = datetime.now()
            hours_since_check = (now - last_check).total_seconds() / 3600

            return hours_since_check >= self.settings.check_interval_hours
        except Exception:
            return True

    def check_for_updates(self, update_url: str = None):
        """Check for updates"""
        if self.update_checker and self.update_checker.isRunning():
            self.logger.info("Update check already in progress")
            return

        # Default update URL (you would replace this with your actual update server)
        if not update_url:
            update_url = "https://api.example.com/updates/check"

        self.logger.info("Starting update check...")
        self.update_check_started.emit()

        # Create and start update checker
        self.update_checker = UpdateChecker(self.current_version, update_url, self.settings)

        # Connect signals
        self.update_checker.update_available.connect(self._on_update_available)
        self.update_checker.no_update_available.connect(self._on_no_update_available)
        self.update_checker.check_failed.connect(self._on_update_check_failed)
        self.update_checker.finished.connect(self._on_update_check_finished)

        self.update_checker.start()

    def download_update(self, version_info: dict):
        """Download an update"""
        if self.downloader and self.downloader.isRunning():
            self.logger.info("Download already in progress")
            return

        self.logger.info(f"Starting download for version {version_info['version']}")
        self.download_started.emit()

        # Create version info object
        version_obj = VersionInfo(**version_info)

        # Create and start downloader
        self.downloader = UpdateDownloader(version_obj, self.download_dir)

        # Connect signals
        self.downloader.download_progress.connect(self.download_progress.emit)
        self.downloader.download_completed.connect(self._on_download_completed)
        self.downloader.download_failed.connect(self._on_download_failed)
        self.downloader.checksum_verified.connect(self._on_checksum_verified)

        self.downloader.start()

    def install_update(self, installer_path: str, create_backup: bool = True):
        """Install an update"""
        installer_file = Path(installer_path)

        if not installer_file.exists():
            error_msg = f"Installer file not found: {installer_path}"
            self.logger.error(error_msg)
            self.installation_failed.emit(error_msg)
            return

        self.logger.info(f"Starting installation from {installer_path}")
        self.installation_started.emit()

        try:
            # Create backup if requested
            if create_backup and self.settings.backup_before_update:
                self.logger.info("Creating backup before installation...")
                if self.installer.create_backup():
                    backup_path = self.backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    self.backup_created.emit(str(backup_path))
                else:
                    error_msg = "Failed to create backup"
                    self.logger.error(error_msg)
                    self.backup_failed.emit(error_msg)
                    if self.settings.backup_before_update:  # Don't proceed if backup was required
                        self.installation_failed.emit("Installation cancelled: backup failed")
                        return

            # Install update
            if self.installer.install_update(installer_file):
                self.logger.info("Installation completed successfully")
                self.installation_completed.emit()

                # Clean up downloaded file
                try:
                    installer_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Failed to clean up installer: {e}")

            else:
                error_msg = "Installation failed"
                self.logger.error(error_msg)
                self.installation_failed.emit(error_msg)

        except Exception as e:
            error_msg = f"Installation error: {e}"
            self.logger.error(error_msg)
            self.installation_failed.emit(error_msg)

    def _on_update_available(self, version_info: dict):
        """Handle update available"""
        self.logger.info(f"Update available: {version_info['version']}")
        self.update_available.emit(version_info)

        # Auto-download if enabled
        if self.settings.download_updates_automatically:
            self.download_update(version_info)

    def _on_no_update_available(self):
        """Handle no update available"""
        self.logger.info("No updates available")
        self.no_update_available.emit()

    def _on_update_check_failed(self, error_msg: str):
        """Handle update check failure"""
        self.logger.error(f"Update check failed: {error_msg}")
        self.update_check_failed.emit(error_msg)

    def _on_update_check_finished(self):
        """Handle update check completion"""
        # Update last check time
        self.settings.last_check = datetime.now().isoformat()
        self.save_settings()

    def _on_download_completed(self, file_path: str):
        """Handle download completion"""
        self.logger.info(f"Download completed: {file_path}")
        self.download_completed.emit(file_path)

        # Auto-install if enabled
        if self.settings.install_updates_automatically:
            self.install_update(file_path)

    def _on_download_failed(self, error_msg: str):
        """Handle download failure"""
        self.logger.error(f"Download failed: {error_msg}")
        self.download_failed.emit(error_msg)

    def _on_checksum_verified(self, verified: bool):
        """Handle checksum verification result"""
        if verified:
            self.logger.info("Download integrity verified")
        else:
            self.logger.error("Download integrity verification failed")

    def set_update_settings(self, **kwargs):
        """Update settings"""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)

        self.save_settings()

        # Restart auto-check if settings changed
        if 'auto_check' in kwargs or 'check_interval_hours' in kwargs:
            self.stop_auto_check()
            if self.settings.auto_check:
                self.start_auto_check()

    def get_update_settings(self) -> dict:
        """Get current update settings"""
        return asdict(self.settings)

    def skip_version(self, version: str):
        """Skip a specific version"""
        self.settings.skip_version = version
        self.save_settings()
        self.logger.info(f"Version {version} will be skipped")

    def cleanup_old_downloads(self, keep_days: int = 7):
        """Clean up old download files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)

            for file_path in self.download_dir.iterdir():
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        self.logger.info(f"Cleaned up old download: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old downloads: {e}")

    def cleanup_old_backups(self, keep_count: int = 5):
        """Clean up old backup directories"""
        try:
            backup_dirs = [d for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith('backup_')]
            backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Keep only the most recent backups
            for backup_dir in backup_dirs[keep_count:]:
                shutil.rmtree(backup_dir)
                self.logger.info(f"Cleaned up old backup: {backup_dir}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")

    def get_available_backups(self) -> List[Dict[str, Any]]:
        """Get list of available backups"""
        backups = []

        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith('backup_'):
                    stat = backup_dir.stat()
                    backups.append({
                        'path': str(backup_dir),
                        'name': backup_dir.name,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'size': sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
                    })

            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)

        except Exception as e:
            self.logger.error(f"Failed to get backup list: {e}")

        return backups

    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore from a backup"""
        try:
            return self.installer.rollback_update(Path(backup_path))
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            return False
