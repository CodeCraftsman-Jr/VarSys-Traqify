"""
Version Management System for Auto-Updates

This module handles version checking, comparison, and metadata management
for the auto-update system using Firebase Hosting.
"""

import re
import json
import logging
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from packaging import version

from PySide6.QtCore import QObject, Signal


@dataclass
class VersionInfo:
    """Version information structure"""
    version: str
    build_number: int
    release_date: str
    channel: str
    required: bool
    download_url: str
    download_size: int
    checksum: Dict[str, str]
    changelog: Dict[str, Any]
    system_requirements: Dict[str, str]
    update_notes: str
    rollback_supported: bool
    auto_update_eligible: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VersionInfo':
        return cls(**data)
    
    def is_newer_than(self, other_version: str) -> bool:
        """Check if this version is newer than the given version"""
        try:
            return version.parse(self.version) > version.parse(other_version)
        except Exception:
            # Fallback to string comparison if version parsing fails
            return self.version > other_version
    
    def is_compatible_with_current_system(self) -> bool:
        """Check if this version is compatible with the current system"""
        # Add system compatibility checks here
        # For now, assume all versions are compatible
        return True


@dataclass
class UpdateSettings:
    """Update settings configuration"""
    auto_check: bool = True
    check_interval_hours: int = 24
    download_updates_automatically: bool = False
    install_updates_automatically: bool = False
    backup_before_update: bool = True
    update_channel: str = "stable"
    last_check: Optional[str] = None
    skip_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateSettings':
        return cls(**data)


class VersionManager(QObject):
    """Manages version checking and comparison for auto-updates"""
    
    # Signals
    version_check_started = Signal()
    version_check_completed = Signal(bool, str)  # success, message
    new_version_available = Signal(VersionInfo)
    no_updates_available = Signal()
    version_check_error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Configuration
        self.current_version = self._get_current_version()
        self.base_url = "https://jointjourney-a12d2.web.app/updates"
        self.settings_file = Path("updates/update_settings.json")
        self.version_cache_file = Path("updates/version_cache.json")
        
        # Load settings
        self.settings = self.load_settings()
        
        # Version cache
        self.version_cache: Dict[str, VersionInfo] = {}
        self.load_version_cache()
        
        self.logger.info("VersionManager initialized")

    def _get_current_version(self) -> str:
        """Get current version from config.json"""
        try:
            config_file = Path("config.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('app_version', '1.0.0')
        except Exception as e:
            self.logger.error(f"Error reading version from config: {e}")
        return '1.0.0'

    def load_settings(self) -> UpdateSettings:
        """Load update settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                return UpdateSettings.from_dict(data)
        except Exception as e:
            self.logger.error(f"Error loading update settings: {e}")
        
        # Return default settings
        return UpdateSettings()
    
    def save_settings(self):
        """Save update settings to file"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings.to_dict(), f, indent=2)
            self.logger.debug("Update settings saved")
        except Exception as e:
            self.logger.error(f"Error saving update settings: {e}")
    
    def load_version_cache(self):
        """Load cached version information"""
        try:
            if self.version_cache_file.exists():
                with open(self.version_cache_file, 'r') as f:
                    data = json.load(f)
                    for channel, version_data in data.items():
                        self.version_cache[channel] = VersionInfo.from_dict(version_data)
                self.logger.debug(f"Loaded version cache for {len(self.version_cache)} channels")
        except Exception as e:
            self.logger.error(f"Error loading version cache: {e}")
    
    def save_version_cache(self):
        """Save version cache to file"""
        try:
            self.version_cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_data = {
                channel: version_info.to_dict() 
                for channel, version_info in self.version_cache.items()
            }
            with open(self.version_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            self.logger.debug("Version cache saved")
        except Exception as e:
            self.logger.error(f"Error saving version cache: {e}")

    def set_current_version(self, version: str):
        """Set the current application version"""
        self.current_version = version
        self.logger.info(f"Current version set to: {version}")

    def check_for_updates(self, channel: Optional[str] = None) -> Optional[VersionInfo]:
        """Check for updates in the specified channel"""
        if channel is None:
            channel = self.settings.update_channel

        self.version_check_started.emit()

        try:
            # Fetch version information from Firebase Hosting
            version_info = self.fetch_version_info(channel)

            if version_info is None:
                self.version_check_error.emit(f"Failed to fetch version info for channel: {channel}")
                return None

            # Cache the version info
            self.version_cache[channel] = version_info
            self.save_version_cache()

            # Update last check time
            self.settings.last_check = datetime.now(timezone.utc).isoformat()
            self.save_settings()

            # Check if update is available
            if self.is_update_available(version_info):
                self.logger.info(f"New version available: {version_info.version}")
                self.new_version_available.emit(version_info)
                self.version_check_completed.emit(True, f"Update available: {version_info.version}")
                return version_info
            else:
                self.logger.info("No updates available")
                self.no_updates_available.emit()
                self.version_check_completed.emit(True, "No updates available")
                return None

        except Exception as e:
            error_msg = f"Error checking for updates: {str(e)}"
            self.logger.error(error_msg)
            self.version_check_error.emit(error_msg)
            self.version_check_completed.emit(False, error_msg)
            return None

    def fetch_version_info(self, channel: str) -> Optional[VersionInfo]:
        """Fetch version information from Firebase Hosting"""
        try:
            url = f"{self.base_url}/{channel}/version.json"
            self.logger.debug(f"Fetching version info from: {url}")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            version_info = VersionInfo.from_dict(data)

            self.logger.debug(f"Fetched version info: {version_info.version}")
            return version_info

        except requests.RequestException as e:
            self.logger.error(f"Network error fetching version info: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in version info: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing version info: {e}")
            return None

    def is_update_available(self, version_info: VersionInfo) -> bool:
        """Check if an update is available"""
        # Skip if user has chosen to skip this version
        if self.settings.skip_version == version_info.version:
            self.logger.debug(f"Skipping version {version_info.version} as requested by user")
            return False

        # Check if version is newer
        if not version_info.is_newer_than(self.current_version):
            return False

        # Check system compatibility
        if not version_info.is_compatible_with_current_system():
            self.logger.warning(f"Version {version_info.version} is not compatible with current system")
            return False

        return True

    def should_check_for_updates(self) -> bool:
        """Check if it's time to check for updates"""
        if not self.settings.auto_check:
            return False

        if self.settings.last_check is None:
            return True

        try:
            last_check = datetime.fromisoformat(self.settings.last_check.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            hours_since_check = (now - last_check).total_seconds() / 3600

            return hours_since_check >= self.settings.check_interval_hours
        except Exception as e:
            self.logger.error(f"Error checking last update time: {e}")
            return True

    def get_cached_version_info(self, channel: str) -> Optional[VersionInfo]:
        """Get cached version information for a channel"""
        return self.version_cache.get(channel)

    def skip_version(self, version: str):
        """Mark a version to be skipped"""
        self.settings.skip_version = version
        self.save_settings()
        self.logger.info(f"Version {version} marked to be skipped")

    def clear_skip_version(self):
        """Clear the skip version setting"""
        self.settings.skip_version = None
        self.save_settings()
        self.logger.info("Skip version setting cleared")

    def get_available_channels(self) -> List[str]:
        """Get list of available update channels"""
        return ["stable", "beta", "dev"]

    def validate_checksum(self, file_path: Path, expected_checksums: Dict[str, str]) -> bool:
        """Validate file checksum"""
        try:
            if not file_path.exists():
                return False

            # Calculate checksums
            with open(file_path, 'rb') as f:
                content = f.read()

            calculated_checksums = {
                'md5': hashlib.md5(content).hexdigest(),
                'sha256': hashlib.sha256(content).hexdigest()
            }

            # Check against expected checksums
            for algo, expected in expected_checksums.items():
                if expected and calculated_checksums.get(algo) != expected:
                    self.logger.error(f"Checksum mismatch for {algo}: expected {expected}, got {calculated_checksums.get(algo)}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating checksum: {e}")
            return False
