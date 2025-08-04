"""
Update Installer for Auto-Update System

This module handles the installation of updates with backup, file replacement,
and rollback capabilities.
"""

import os
import sys
import json
import shutil
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from PySide6.QtCore import QObject, Signal, QProcess
from PySide6.QtWidgets import QApplication


@dataclass
class BackupInfo:
    """Backup information structure"""
    backup_id: str
    version: str
    backup_path: str
    created_at: str
    files_backed_up: List[str]
    backup_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupInfo':
        return cls(**data)


@dataclass
class InstallationProgress:
    """Installation progress information"""
    stage: str
    progress: float
    message: str
    details: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UpdateInstaller(QObject):
    """Handles installation of updates with backup and rollback capabilities"""
    
    # Signals
    installation_started = Signal(str)  # version
    installation_progress = Signal(InstallationProgress)
    backup_started = Signal(str)  # backup_id
    backup_completed = Signal(str, str)  # backup_id, backup_path
    backup_failed = Signal(str, str)  # backup_id, error_message
    installation_completed = Signal(str, str)  # version, install_path
    installation_failed = Signal(str, str)  # version, error_message
    rollback_started = Signal(str)  # backup_id
    rollback_completed = Signal(str)  # backup_id
    rollback_failed = Signal(str, str)  # backup_id, error_message
    restart_required = Signal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Configuration
        self.backup_dir = Path("updates/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_metadata_file = self.backup_dir / "backup_metadata.json"
        
        # Installation state
        self.current_installation = None
        self.is_installing = False
        
        # Backup management
        self.backup_metadata: Dict[str, BackupInfo] = {}
        self.load_backup_metadata()
        
        self.logger.info("UpdateInstaller initialized")
    
    def load_backup_metadata(self):
        """Load backup metadata from file"""
        try:
            if self.backup_metadata_file.exists():
                with open(self.backup_metadata_file, 'r') as f:
                    data = json.load(f)
                    for backup_id, backup_data in data.items():
                        self.backup_metadata[backup_id] = BackupInfo.from_dict(backup_data)
                self.logger.debug(f"Loaded metadata for {len(self.backup_metadata)} backups")
        except Exception as e:
            self.logger.error(f"Error loading backup metadata: {e}")
    
    def save_backup_metadata(self):
        """Save backup metadata to file"""
        try:
            metadata_dict = {
                backup_id: backup_info.to_dict()
                for backup_id, backup_info in self.backup_metadata.items()
            }
            with open(self.backup_metadata_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
            self.logger.debug("Backup metadata saved")
        except Exception as e:
            self.logger.error(f"Error saving backup metadata: {e}")
    
    def install_update(self, update_file_path: Path, version: str, 
                      create_backup: bool = True) -> bool:
        """Install an update with optional backup"""
        if self.is_installing:
            self.logger.warning("Installation already in progress")
            return False
        
        try:
            self.is_installing = True
            self.current_installation = version
            
            self.logger.info(f"Starting installation of version {version}")
            self.installation_started.emit(version)
            
            # Stage 1: Create backup if requested
            backup_id = None
            if create_backup:
                self._emit_progress("backup", 10, "Creating backup...", "Backing up current installation")
                backup_id = self.create_backup()
                if backup_id is None:
                    raise Exception("Failed to create backup")
            
            # Stage 2: Prepare for installation
            self._emit_progress("prepare", 30, "Preparing installation...", "Validating update file")
            if not self._validate_update_file(update_file_path):
                raise Exception("Update file validation failed")
            
            # Stage 3: Stop application processes (if any)
            self._emit_progress("stop", 40, "Stopping application...", "Preparing for file replacement")
            # Note: In a real scenario, you might need to stop other instances
            
            # Stage 4: Install update
            self._emit_progress("install", 50, "Installing update...", "Replacing application files")
            install_path = self._perform_installation(update_file_path)
            if install_path is None:
                raise Exception("Installation failed")
            
            # Stage 5: Verify installation
            self._emit_progress("verify", 80, "Verifying installation...", "Checking installed files")
            if not self._verify_installation(install_path):
                raise Exception("Installation verification failed")
            
            # Stage 6: Complete installation
            self._emit_progress("complete", 100, "Installation complete", "Update installed successfully")
            
            self.logger.info(f"Installation completed successfully: {version}")
            self.installation_completed.emit(version, str(install_path))
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            error_msg = f"Installation failed: {str(e)}"
            self.logger.error(error_msg)
            self.installation_failed.emit(version, error_msg)
            
            # Attempt rollback if backup was created
            if backup_id and create_backup:
                self.logger.info("Attempting rollback due to installation failure")
                self.rollback_to_backup(backup_id)
            
            return False
            
        finally:
            self.is_installing = False
            self.current_installation = None
    
    def create_backup(self) -> Optional[str]:
        """Create a backup of the current installation"""
        try:
            backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(exist_ok=True)
            
            self.logger.info(f"Creating backup: {backup_id}")
            self.backup_started.emit(backup_id)
            
            # Get current executable path
            current_exe = Path(sys.executable)
            if not current_exe.exists():
                raise Exception("Current executable not found")
            
            # Files to backup
            files_to_backup = [current_exe]
            
            # Add additional files if they exist (config, data, etc.)
            additional_files = [
                Path("config.json"),
                Path("data/config"),
                # Add other important files here
            ]
            
            for file_path in additional_files:
                if file_path.exists():
                    files_to_backup.append(file_path)
            
            # Perform backup
            backed_up_files = []
            total_size = 0
            
            for file_path in files_to_backup:
                if file_path.is_file():
                    dest_path = backup_path / file_path.name
                    shutil.copy2(file_path, dest_path)
                    backed_up_files.append(str(file_path))
                    total_size += file_path.stat().st_size
                elif file_path.is_dir():
                    dest_path = backup_path / file_path.name
                    shutil.copytree(file_path, dest_path, dirs_exist_ok=True)
                    backed_up_files.append(str(file_path))
                    total_size += sum(f.stat().st_size for f in file_path.rglob('*') if f.is_file())
            
            # Create backup info
            backup_info = BackupInfo(
                backup_id=backup_id,
                version=self._get_current_version(),
                backup_path=str(backup_path),
                created_at=datetime.now().isoformat(),
                files_backed_up=backed_up_files,
                backup_size=total_size
            )
            
            # Save backup metadata
            self.backup_metadata[backup_id] = backup_info
            self.save_backup_metadata()
            
            self.logger.info(f"Backup created successfully: {backup_id}")
            self.backup_completed.emit(backup_id, str(backup_path))
            
            return backup_id
            
        except Exception as e:
            error_msg = f"Backup creation failed: {str(e)}"
            self.logger.error(error_msg)
            self.backup_failed.emit(backup_id, error_msg)
            return None
    
    def rollback_to_backup(self, backup_id: str) -> bool:
        """Rollback to a specific backup"""
        try:
            if backup_id not in self.backup_metadata:
                raise Exception(f"Backup {backup_id} not found")
            
            backup_info = self.backup_metadata[backup_id]
            backup_path = Path(backup_info.backup_path)
            
            if not backup_path.exists():
                raise Exception(f"Backup directory not found: {backup_path}")
            
            self.logger.info(f"Starting rollback to backup: {backup_id}")
            self.rollback_started.emit(backup_id)
            
            # Restore files from backup
            for backed_up_file in backup_info.files_backed_up:
                source_path = backup_path / Path(backed_up_file).name
                dest_path = Path(backed_up_file)
                
                if source_path.exists():
                    if source_path.is_file():
                        shutil.copy2(source_path, dest_path)
                    elif source_path.is_dir():
                        if dest_path.exists():
                            shutil.rmtree(dest_path)
                        shutil.copytree(source_path, dest_path)
            
            self.logger.info(f"Rollback completed successfully: {backup_id}")
            self.rollback_completed.emit(backup_id)
            
            return True
            
        except Exception as e:
            error_msg = f"Rollback failed: {str(e)}"
            self.logger.error(error_msg)
            self.rollback_failed.emit(backup_id, error_msg)
            return False

    def _emit_progress(self, stage: str, progress: float, message: str, details: str = ""):
        """Emit installation progress"""
        progress_info = InstallationProgress(
            stage=stage,
            progress=progress,
            message=message,
            details=details
        )
        self.installation_progress.emit(progress_info)

    def _validate_update_file(self, update_file_path: Path) -> bool:
        """Validate the update file"""
        try:
            if not update_file_path.exists():
                self.logger.error(f"Update file not found: {update_file_path}")
                return False

            if update_file_path.suffix.lower() != '.exe':
                self.logger.error(f"Invalid update file type: {update_file_path.suffix}")
                return False

            # Check file size (should be reasonable for an executable)
            file_size = update_file_path.stat().st_size
            if file_size < 1024 * 1024:  # Less than 1MB
                self.logger.error(f"Update file too small: {file_size} bytes")
                return False

            if file_size > 500 * 1024 * 1024:  # More than 500MB
                self.logger.error(f"Update file too large: {file_size} bytes")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating update file: {e}")
            return False

    def _perform_installation(self, update_file_path: Path) -> Optional[Path]:
        """Perform the actual installation"""
        try:
            # Get current executable path
            current_exe = Path(sys.executable)
            install_path = current_exe.parent / f"{current_exe.stem}_new{current_exe.suffix}"

            # Copy new executable
            shutil.copy2(update_file_path, install_path)

            # Verify the copied file
            if not install_path.exists():
                raise Exception("Failed to copy update file")

            if install_path.stat().st_size != update_file_path.stat().st_size:
                raise Exception("File size mismatch after copy")

            return install_path

        except Exception as e:
            self.logger.error(f"Error performing installation: {e}")
            return None

    def _verify_installation(self, install_path: Path) -> bool:
        """Verify the installation"""
        try:
            if not install_path.exists():
                return False

            # Try to run the new executable with a version check
            # This is a basic verification - you might want to add more checks
            result = subprocess.run(
                [str(install_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # If the process runs without error, consider it valid
            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"Error verifying installation: {e}")
            return False

    def _get_current_version(self) -> str:
        """Get the current application version"""
        # This should be implemented to return the actual current version
        # For now, return a placeholder
        return "1.0.0"

    def _cleanup_old_backups(self, keep_count: int = 5):
        """Clean up old backups, keeping only the most recent ones"""
        try:
            if len(self.backup_metadata) <= keep_count:
                return

            # Sort backups by creation date (newest first)
            sorted_backups = sorted(
                self.backup_metadata.items(),
                key=lambda x: x[1].created_at,
                reverse=True
            )

            # Remove old backups
            for backup_id, backup_info in sorted_backups[keep_count:]:
                backup_path = Path(backup_info.backup_path)
                if backup_path.exists():
                    try:
                        shutil.rmtree(backup_path)
                        self.logger.info(f"Removed old backup: {backup_id}")
                    except Exception as e:
                        self.logger.error(f"Error removing backup {backup_id}: {e}")

                # Remove from metadata
                del self.backup_metadata[backup_id]

            # Save updated metadata
            self.save_backup_metadata()

        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")

    def get_available_backups(self) -> List[BackupInfo]:
        """Get list of available backups"""
        return list(self.backup_metadata.values())

    def delete_backup(self, backup_id: str) -> bool:
        """Delete a specific backup"""
        try:
            if backup_id not in self.backup_metadata:
                return False

            backup_info = self.backup_metadata[backup_id]
            backup_path = Path(backup_info.backup_path)

            if backup_path.exists():
                shutil.rmtree(backup_path)

            del self.backup_metadata[backup_id]
            self.save_backup_metadata()

            self.logger.info(f"Backup deleted: {backup_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting backup {backup_id}: {e}")
            return False

    def restart_application(self, new_executable_path: Optional[Path] = None):
        """Restart the application with the new executable"""
        try:
            if new_executable_path is None:
                # Use current executable
                executable_path = sys.executable
            else:
                executable_path = str(new_executable_path)

            self.logger.info(f"Restarting application: {executable_path}")
            self.restart_required.emit()

            # Start new process
            subprocess.Popen([executable_path])

            # Exit current application
            QApplication.instance().quit()

        except Exception as e:
            self.logger.error(f"Error restarting application: {e}")

    def schedule_file_replacement(self, old_file: Path, new_file: Path) -> bool:
        """Schedule file replacement on next restart (Windows-specific)"""
        try:
            if os.name != 'nt':
                return False

            # Use Windows MoveFileEx to schedule replacement on reboot
            import ctypes
            from ctypes import wintypes

            MOVEFILE_DELAY_UNTIL_REBOOT = 0x4

            result = ctypes.windll.kernel32.MoveFileExW(
                wintypes.LPCWSTR(str(new_file)),
                wintypes.LPCWSTR(str(old_file)),
                wintypes.DWORD(MOVEFILE_DELAY_UNTIL_REBOOT)
            )

            if result:
                self.logger.info(f"Scheduled file replacement: {old_file}")
                return True
            else:
                self.logger.error("Failed to schedule file replacement")
                return False

        except Exception as e:
            self.logger.error(f"Error scheduling file replacement: {e}")
            return False
