"""
Update Downloader for Auto-Update System

This module handles secure downloading of update files with progress tracking,
integrity verification, and resume capability.
"""

import os
import json
import logging
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, QThread, QTimer


@dataclass
class DownloadProgress:
    """Download progress information"""
    bytes_downloaded: int
    total_bytes: int
    percentage: float
    speed_bps: float
    eta_seconds: float
    status: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'bytes_downloaded': self.bytes_downloaded,
            'total_bytes': self.total_bytes,
            'percentage': self.percentage,
            'speed_bps': self.speed_bps,
            'eta_seconds': self.eta_seconds,
            'status': self.status
        }


class UpdateDownloader(QObject):
    """Handles downloading of update files with progress tracking"""
    
    # Signals
    download_started = Signal(str)  # filename
    download_progress = Signal(DownloadProgress)
    download_completed = Signal(str, str)  # filename, file_path
    download_failed = Signal(str, str)  # filename, error_message
    download_cancelled = Signal(str)  # filename
    checksum_verification_started = Signal(str)  # filename
    checksum_verification_completed = Signal(str, bool)  # filename, success
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Configuration
        self.download_dir = Path("updates/downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Download state
        self.current_download = None
        self.is_downloading = False
        self.should_cancel = False
        
        # Progress tracking
        self.start_time = None
        self.last_progress_time = None
        self.last_bytes_downloaded = 0
        
        self.logger.info("UpdateDownloader initialized")
    
    def download_update(self, download_url: str, filename: str, 
                       expected_checksums: Optional[Dict[str, str]] = None,
                       resume: bool = True) -> bool:
        """Download an update file with progress tracking"""
        if self.is_downloading:
            self.logger.warning("Download already in progress")
            return False
        
        try:
            self.is_downloading = True
            self.should_cancel = False
            self.current_download = filename
            
            file_path = self.download_dir / filename
            temp_path = self.download_dir / f"{filename}.tmp"
            
            self.logger.info(f"Starting download: {filename}")
            self.download_started.emit(filename)
            
            # Check if partial download exists and resume is enabled
            resume_pos = 0
            if resume and temp_path.exists():
                resume_pos = temp_path.stat().st_size
                self.logger.info(f"Resuming download from byte {resume_pos}")
            
            # Prepare headers for resume
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
            
            # Start download
            response = requests.get(download_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get total file size
            if 'content-range' in response.headers:
                # Resuming download
                total_size = int(response.headers['content-range'].split('/')[-1])
            else:
                # New download
                total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                raise Exception("Unable to determine file size")
            
            # Initialize progress tracking
            self.start_time = datetime.now()
            self.last_progress_time = self.start_time
            self.last_bytes_downloaded = resume_pos
            
            # Download file
            mode = 'ab' if resume_pos > 0 else 'wb'
            with open(temp_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.should_cancel:
                        self.logger.info(f"Download cancelled: {filename}")
                        self.download_cancelled.emit(filename)
                        return False
                    
                    if chunk:
                        f.write(chunk)
                        self._update_progress(temp_path.stat().st_size, total_size)
            
            # Verify file size
            final_size = temp_path.stat().st_size
            if final_size != total_size:
                raise Exception(f"File size mismatch: expected {total_size}, got {final_size}")
            
            # Verify checksums if provided
            if expected_checksums:
                self.checksum_verification_started.emit(filename)
                if not self._verify_checksums(temp_path, expected_checksums):
                    raise Exception("Checksum verification failed")
                self.checksum_verification_completed.emit(filename, True)
            
            # Move temp file to final location
            if file_path.exists():
                file_path.unlink()
            temp_path.rename(file_path)
            
            self.logger.info(f"Download completed: {filename}")
            self.download_completed.emit(filename, str(file_path))
            return True
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            self.logger.error(error_msg)
            self.download_failed.emit(filename, error_msg)
            
            # Clean up temp file
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            
            return False
            
        finally:
            self.is_downloading = False
            self.current_download = None
    
    def cancel_download(self):
        """Cancel the current download"""
        if self.is_downloading:
            self.should_cancel = True
            self.logger.info("Download cancellation requested")
    
    def _update_progress(self, bytes_downloaded: int, total_bytes: int):
        """Update download progress"""
        now = datetime.now()
        
        # Calculate progress
        percentage = (bytes_downloaded / total_bytes) * 100 if total_bytes > 0 else 0
        
        # Calculate speed (bytes per second)
        time_diff = (now - self.last_progress_time).total_seconds()
        if time_diff >= 1.0:  # Update every second
            bytes_diff = bytes_downloaded - self.last_bytes_downloaded
            speed_bps = bytes_diff / time_diff if time_diff > 0 else 0
            
            # Calculate ETA
            remaining_bytes = total_bytes - bytes_downloaded
            eta_seconds = remaining_bytes / speed_bps if speed_bps > 0 else 0
            
            # Create progress object
            progress = DownloadProgress(
                bytes_downloaded=bytes_downloaded,
                total_bytes=total_bytes,
                percentage=percentage,
                speed_bps=speed_bps,
                eta_seconds=eta_seconds,
                status="downloading"
            )
            
            self.download_progress.emit(progress)
            
            # Update tracking variables
            self.last_progress_time = now
            self.last_bytes_downloaded = bytes_downloaded
    
    def _verify_checksums(self, file_path: Path, expected_checksums: Dict[str, str]) -> bool:
        """Verify file checksums"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            calculated_checksums = {
                'md5': hashlib.md5(content).hexdigest(),
                'sha256': hashlib.sha256(content).hexdigest()
            }
            
            for algo, expected in expected_checksums.items():
                if expected and calculated_checksums.get(algo) != expected:
                    self.logger.error(f"Checksum mismatch for {algo}: expected {expected}, got {calculated_checksums.get(algo)}")
                    return False
            
            self.logger.info("Checksum verification successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying checksums: {e}")
            return False
    
    def get_download_path(self, filename: str) -> Path:
        """Get the download path for a file"""
        return self.download_dir / filename
    
    def is_file_downloaded(self, filename: str) -> bool:
        """Check if a file has been downloaded"""
        return (self.download_dir / filename).exists()
    
    def get_downloaded_file_size(self, filename: str) -> int:
        """Get the size of a downloaded file"""
        file_path = self.download_dir / filename
        return file_path.stat().st_size if file_path.exists() else 0
    
    def clean_old_downloads(self, keep_latest: int = 3):
        """Clean up old download files, keeping only the latest ones"""
        try:
            files = list(self.download_dir.glob("*.exe"))
            if len(files) <= keep_latest:
                return
            
            # Sort by modification time (newest first)
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Remove old files
            for file_path in files[keep_latest:]:
                try:
                    file_path.unlink()
                    self.logger.info(f"Removed old download: {file_path.name}")
                except Exception as e:
                    self.logger.error(f"Error removing old download {file_path.name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning old downloads: {e}")
    
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
