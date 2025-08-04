"""
Firebase Data Synchronization Engine

This module handles intelligent data synchronization between local storage
and Firebase, minimizing read/write operations to stay within free tier limits.
"""

import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone, date
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, asdict
import threading

import pandas as pd
from PySide6.QtCore import QObject, Signal, QThread, QTimer, QMetaObject, Qt


from .secure_config import get_secure_config
from .data_manager import DataManager

# Firebase components - try to import if available
try:
    from .firebase_config import firebase_manager
    from .firebase_auth import firebase_auth_manager as firebase_auth
    FIREBASE_AVAILABLE = firebase_manager.is_available()
except ImportError:
    # Firebase not available - use secure backend only
    firebase_manager = None
    firebase_auth = None
    FIREBASE_AVAILABLE = False


@dataclass
class SyncMetadata:
    """Metadata for tracking sync state"""
    module: str
    filename: str
    last_sync: str
    local_hash: str
    remote_hash: str
    last_modified: str
    sync_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncMetadata':
        return cls(**data)


class SyncStatus:
    """Sync operation status"""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    CONFLICT = "conflict"


class FirebaseSyncEngine(QObject):
    """Manages data synchronization with Firebase"""
    
    # Signals
    sync_started = Signal()
    sync_progress = Signal(str, int, int)  # operation, current, total
    sync_completed = Signal(bool, str)     # success, message
    sync_error = Signal(str)
    conflict_detected = Signal(str, str)   # module, filename
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.data_manager = data_manager
        self.status = SyncStatus.IDLE
        self.last_sync_time: Optional[datetime] = None

        # Initialize Firebase client based on configuration
        from .secure_config import get_secure_config
        self.config = get_secure_config()

        # Always use direct Firebase client
        from .direct_firebase_client import get_direct_firebase_client
        self.firebase_client = get_direct_firebase_client()
        self.secure_client = None
        self.use_direct_firebase = True
        self.logger.info("Using direct Firebase client")
        
        # Sync metadata tracking
        self.metadata_file = Path("data/config/sync_metadata.json")
        self.sync_metadata: Dict[str, SyncMetadata] = {}

        # Sync coordination to prevent concurrent operations
        self._module_locks = set()  # Track modules currently being synced
        self._main_thread = threading.current_thread()  # Track main thread for safe signal emission

        # Modules to sync
        self.syncable_modules = [
            "expenses", "income", "habits", "attendance",
            "todos", "investments", "budget"
        ]
        
        # Load existing metadata
        self.load_metadata()
        
        # Auto-sync timer
        self.auto_sync_timer = QTimer()
        self.auto_sync_timer.timeout.connect(self.auto_sync)
        
        self.logger.info("FirebaseSyncEngine initialized")

    def _emit_signal_safe(self, signal, *args):
        """Emit signal safely from any thread"""
        if threading.current_thread() == self._main_thread:
            # We're in the main thread, emit directly
            try:
                signal.emit(*args)
            except Exception as e:
                self.logger.error(f"Error emitting signal from main thread: {e}")
        else:
            # We're in a background thread, log instead of emitting to prevent crashes
            signal_name = getattr(signal, 'signal', str(signal))
            self.logger.debug(f"Background thread signal emission suppressed: {signal_name} with args: {args}")
            # Note: In a production app, you might want to queue these for later emission
            # For now, we'll just log them to prevent Qt threading crashes

    def is_available(self) -> bool:
        """Check if sync is available"""
        if not self.config.enabled:
            return False

        # Always use direct Firebase authentication
        return self.firebase_client.is_authenticated()
    
    def start_auto_sync(self, interval_seconds: int = None):
        """Start automatic synchronization"""
        if interval_seconds is None:
            interval_seconds = self.config.sync_interval

        if self.is_available() and self.config.auto_sync:
            self.auto_sync_timer.start(interval_seconds * 1000)
            self.logger.info(f"Auto-sync started with {interval_seconds}s interval")
    
    def stop_auto_sync(self):
        """Stop automatic synchronization"""
        self.auto_sync_timer.stop()
        self.logger.info("Auto-sync stopped")
    
    def auto_sync(self):
        """Perform automatic sync if conditions are met"""
        if self.status == SyncStatus.IDLE and self.is_available():
            self.sync_all_data()
    
    def sync_all_data(self, force: bool = False):
        """Sync all data modules"""
        # Check if sync is available with detailed logging
        if not self.is_available():
            error_msg = "Sync unavailable: Please sign in to Firebase to enable data synchronization"
            self.logger.warning("Sync unavailable - Firebase user not authenticated")
            self._emit_signal_safe(self.sync_error, error_msg)
            return

        if self.status != SyncStatus.IDLE:
            self._emit_signal_safe(self.sync_error, "Sync already in progress")
            return

        self.status = SyncStatus.SYNCING
        self._emit_signal_safe(self.sync_started)

        try:
            # Ensure database exists before syncing
            self._emit_signal_safe(self.sync_progress, "Initializing database...", 0, len(self.syncable_modules) + 1)

            # Get detailed authentication status for debugging
            auth_status = self.secure_client.get_session_status()
            self.logger.info(f"Starting sync - Auth status: {auth_status}")

            # Try database initialization with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                if self._ensure_database_exists():
                    break

                if attempt < max_retries - 1:
                    self.logger.warning(f"Database initialization attempt {attempt + 1} failed, retrying...")

                    # Try to refresh authentication if needed
                    try:
                        if hasattr(self.secure_client, 'refresh_token_if_needed'):
                            self.secure_client.refresh_token_if_needed()
                            self.logger.info("Attempted token refresh")
                    except Exception as refresh_error:
                        self.logger.warning(f"Token refresh failed: {refresh_error}")

                    import time
                    time.sleep(1)  # Wait 1 second before retry
                else:
                    # Provide more helpful error message based on auth status
                    if not auth_status.get('has_user'):
                        error_msg = "Database initialization failed: User not signed in"
                    elif not auth_status.get('has_token'):
                        error_msg = "Database initialization failed: Authentication token expired"
                    else:
                        error_msg = f"Database initialization failed after {max_retries} attempts: Connection error"

                    self.logger.error(f"{error_msg}. Auth status: {auth_status}")
                    raise Exception(error_msg)

            total_modules = len(self.syncable_modules)
            synced_count = 0
            errors = []

            for module in self.syncable_modules:
                self._emit_signal_safe(self.sync_progress, f"Syncing {module}...", synced_count, total_modules)

                try:
                    self.sync_module(module, force)
                    synced_count += 1
                except Exception as e:
                    error_msg = f"Error syncing {module}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)

            # Update last sync time
            self.last_sync_time = datetime.now(timezone.utc)

            # Save metadata
            self.save_metadata()

            if errors:
                error_summary = f"Sync completed with {len(errors)} errors:\n" + "\n".join(errors)
                self._emit_signal_safe(self.sync_completed, False, error_summary)
            else:
                self._emit_signal_safe(self.sync_completed, True, f"Successfully synced {synced_count} modules")

        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            self.logger.error(error_msg)
            self._emit_signal_safe(self.sync_error, error_msg)

        finally:
            self.status = SyncStatus.IDLE
    
    def sync_module(self, module: str, force: bool = False):
        """Sync a specific module with comprehensive error handling and concurrency protection"""
        # Check if module is already being synced
        if module in self._module_locks:
            self.logger.debug(f"Module {module} is already being synced, skipping duplicate request")
            return

        try:
            # Acquire lock for this module
            self._module_locks.add(module)
            self.logger.debug(f"Acquired sync lock for module: {module}")

            if not self.is_available():
                self.logger.warning(f"Firebase sync not available for module: {module}")
                return

            # Get all CSV files in the module directory
            module_path = self.data_manager.data_dir / module
            if not module_path.exists():
                self.logger.debug(f"Module directory does not exist: {module_path}")
                return

            try:
                csv_files = list(module_path.glob("*.csv"))
            except Exception as e:
                self.logger.error(f"Error listing CSV files in {module_path}: {e}")
                return

            if not csv_files:
                self.logger.debug(f"No CSV files found in module: {module}")
                return

            self.logger.debug(f"Syncing {len(csv_files)} files for module: {module}")

            for csv_file in csv_files:
                try:
                    filename = csv_file.name
                    self.sync_file(module, filename, force)
                except Exception as file_error:
                    self.logger.error(f"Error syncing file {csv_file.name} in module {module}: {file_error}")
                    # Continue with other files instead of failing completely
                    continue

        except Exception as e:
            self.logger.error(f"Critical error in sync_module for {module}: {e}")
            # Don't re-raise to prevent application crash
            self._emit_signal_safe(self.sync_error, f"Sync failed for module {module}: {str(e)}")
        finally:
            # Always release the lock
            self._module_locks.discard(module)
            self.logger.debug(f"Released sync lock for module: {module}")
    
    def sync_file(self, module: str, filename: str, force: bool = False):
        """Sync a specific file with comprehensive error handling"""
        file_key = f"{module}/{filename}"

        try:
            self.logger.debug(f"Starting sync for file: {module}/{filename}")

            # Get current file state with error handling
            try:
                local_hash = self.get_file_hash(module, filename)
                local_modified = self.get_file_modified_time(module, filename)
            except Exception as hash_error:
                self.logger.error(f"Error getting file state for {module}/{filename}: {hash_error}")
                # Use empty values as fallback
                local_hash = ""
                local_modified = ""

            # Get existing metadata
            metadata = self.sync_metadata.get(file_key)

            # Check if sync is needed
            if not force and metadata:
                try:
                    if (metadata.local_hash == local_hash and
                        metadata.last_modified == local_modified):
                        # No local changes, check remote
                        remote_hash = self.get_remote_hash(module, filename)
                        if remote_hash == metadata.remote_hash:
                            # No changes on either side
                            self.logger.debug(f"No changes detected for {module}/{filename}, skipping sync")
                            return
                except Exception as metadata_error:
                    self.logger.warning(f"Error checking metadata for {module}/{filename}: {metadata_error}")
                    # Continue with sync as fallback

            # Perform sync with error handling
            try:
                if metadata is None or force:
                    # First sync or forced sync - upload everything
                    self.logger.debug(f"Performing initial/forced sync for {module}/{filename}")
                    self.upload_file(module, filename)
                else:
                    # Intelligent sync - check for conflicts
                    self.logger.debug(f"Performing intelligent sync for {module}/{filename}")

                    try:
                        remote_data = self.download_file(module, filename)
                        local_data = self.data_manager.read_csv(module, filename)

                        if remote_data is not None and not local_data.empty:
                            try:
                                if not local_data.equals(remote_data):
                                    # Conflict detected - use timestamp-based resolution
                                    self.logger.info(f"Conflict detected for {module}/{filename}, resolving...")
                                    self.resolve_conflict(module, filename, local_data, remote_data)
                                else:
                                    self.logger.debug(f"Data identical for {module}/{filename}, no sync needed")
                            except Exception as compare_error:
                                self.logger.warning(f"Error comparing data for {module}/{filename}: {compare_error}")
                                # Upload local changes as fallback
                                if not local_data.empty:
                                    self.upload_file(module, filename)
                        elif not local_data.empty:
                            # Upload local changes
                            self.logger.debug(f"Uploading local changes for {module}/{filename}")
                            self.upload_file(module, filename)
                        else:
                            self.logger.debug(f"No local data to sync for {module}/{filename}")

                    except Exception as sync_data_error:
                        self.logger.error(f"Error during data sync for {module}/{filename}: {sync_data_error}")
                        # Try a simple upload as fallback (including empty files)
                        try:
                            local_data = self.data_manager.read_csv(module, filename)
                            if local_data is not None:  # Upload both empty and non-empty files
                                self.upload_file(module, filename)
                        except Exception as fallback_error:
                            self.logger.error(f"Fallback upload also failed for {module}/{filename}: {fallback_error}")
                            raise sync_data_error  # Re-raise original error

            except Exception as upload_error:
                self.logger.error(f"Upload failed for {module}/{filename}: {upload_error}")
                # Don't re-raise to prevent application crash, but log the error
                return

            # Update metadata with error handling
            try:
                self.update_metadata(module, filename, local_hash, local_modified)
                self.logger.debug(f"Successfully synced file: {module}/{filename}")
            except Exception as metadata_update_error:
                self.logger.error(f"Error updating metadata for {module}/{filename}: {metadata_update_error}")
                # Don't fail the sync just because metadata update failed

        except Exception as e:
            self.logger.error(f"Critical error in sync_file for {module}/{filename}: {e}")
            # Don't re-raise to prevent application crash
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return
    
    def upload_file(self, module: str, filename: str):
        """Upload file to Firebase"""
        try:
            # Always use direct Firebase
            return self._upload_via_direct_firebase(module, filename)
        except Exception as e:
            self.logger.error(f"Upload failed for {module}/{filename}: {e}")
            # Emit a user-friendly error message
            error_msg = str(e)
            if "not signed in" in error_msg.lower():
                self._emit_signal_safe(self.sync_error, "Upload failed: Please sign in to enable sync")
            elif "token expired" in error_msg.lower():
                self._emit_signal_safe(self.sync_error, "Upload failed: Session expired, please sign in again")
            elif "connection" in error_msg.lower():
                self._emit_signal_safe(self.sync_error, "Upload failed: Connection error, check your internet")
            else:
                self._emit_signal_safe(self.sync_error, f"Upload failed: {error_msg}")
            raise  # Re-raise so the calling code can handle it properly

    def _upload_via_direct_firebase(self, module: str, filename: str):
        """Upload file using direct Firebase client"""
        try:
            # Get file data
            file_path = self.data_manager.get_file_path(module, filename)
            if not file_path.exists():
                raise Exception(f"File not found: {file_path}")

            # Read data
            data = self.data_manager.read_csv(module, filename)
            if data is None:
                self.logger.warning(f"Could not read data for {module}/{filename}")
                return

            # Handle empty data by uploading empty marker
            if data.empty:
                self.logger.info(f"Data is empty for {module}/{filename}, uploading empty marker")
                upload_data = {
                    'records': [],
                    'columns': [],
                    'metadata': {
                        'row_count': 0,
                        'column_count': 0,
                        'uploaded_at': datetime.now().isoformat(),
                        'empty': True,
                        'backend': 'direct_firebase'
                    }
                }

                # Upload empty marker via direct Firebase client
                success, message = self.firebase_client.upload_data(module, filename, upload_data)

                if success:
                    self.logger.info(f"Successfully uploaded empty data marker for {module}/{filename} via direct Firebase: {message}")
                else:
                    raise Exception(f"Direct Firebase upload of empty data failed: {message}")
                return

            # Prepare data for upload using comprehensive data preparation
            data_copy = data.copy()

            # Use the comprehensive data preparation function that handles NaN, inf, -inf
            data_copy = self._prepare_dataframe_for_upload(data_copy)

            # Create upload data structure with JSON serialization test
            try:
                import json
                records_data = data_copy.to_dict('records')

                # Test JSON serialization to catch any remaining issues
                json.dumps(records_data[:1] if records_data else [])  # Test with first record

                upload_data = {
                    'records': records_data,
                    'columns': data_copy.columns.tolist(),
                    'metadata': {
                        'row_count': len(data_copy),
                        'column_count': len(data_copy.columns),
                        'uploaded_at': datetime.now().isoformat(),
                        'backend': 'direct_firebase'
                    }
                }

                # Final JSON serialization test
                json.dumps(upload_data['metadata'])  # Test metadata serialization

            except Exception as json_error:
                self.logger.error(f"JSON serialization error for {module}/{filename}: {json_error}")
                self.logger.error(f"Data types: {data_copy.dtypes.to_dict()}")
                self.logger.error(f"Sample data: {data_copy.head(1).to_dict()}")

                # Emergency fallback: convert all data to strings
                self.logger.warning("Applying emergency string conversion fallback")
                for col in data_copy.columns:
                    try:
                        data_copy[col] = data_copy[col].astype(str).replace(['nan', 'None', 'NaT', 'inf', '-inf'], '')
                    except:
                        data_copy[col] = ''

                # Retry with string-converted data
                upload_data = {
                    'records': data_copy.to_dict('records'),
                    'columns': data_copy.columns.tolist(),
                    'metadata': {
                        'row_count': len(data_copy),
                        'column_count': len(data_copy.columns),
                        'uploaded_at': datetime.now().isoformat(),
                        'backend': 'direct_firebase'
                    }
                }

            # Upload via direct Firebase client
            success, message = self.firebase_client.upload_data(module, filename, upload_data)

            if success:
                self.logger.info(f"Successfully uploaded {module}/{filename} via direct Firebase: {message}")
            else:
                raise Exception(f"Direct Firebase upload failed: {message}")

        except Exception as e:
            self.logger.error(f"Direct Firebase upload failed for {module}/{filename}: {e}")
            raise

    def _upload_via_secure_client(self, module: str, filename: str):
        """Upload file using secure client"""
        try:
            # Get file data
            file_path = self.data_manager.get_file_path(module, filename)
            if not file_path.exists():
                raise Exception(f"File not found: {file_path}")

            # Read and upload data with comprehensive error handling
            try:
                data = self.data_manager.read_csv(module, filename)
            except Exception as load_error:
                self.logger.error(f"Error loading data for {module}/{filename}: {load_error}")
                raise Exception(f"Failed to load data: {load_error}")

            if data is not None and not data.empty:
                try:
                    # Prepare data for JSON serialization
                    data_copy = data.copy()
                    self.logger.debug(f"Preparing {len(data_copy)} rows for upload from {module}/{filename}")

                    # Prepare data with error handling
                    self._prepare_data_for_upload(data_copy)

                    self.logger.debug(f"Data preparation completed, uploading {len(data_copy)} rows")

                    # Structure data properly for Firebase Realtime Database with error handling
                    try:
                        # Test JSON serialization before creating upload structure
                        import json
                        records_data = data_copy.to_dict('records')

                        # Test if the records can be JSON serialized
                        json.dumps(records_data[:1] if records_data else [])  # Test with first record

                        upload_data = {
                            'records': records_data,
                            'columns': data_copy.columns.tolist(),
                            'metadata': {
                                'row_count': len(data_copy),
                                'column_count': len(data_copy.columns),
                                'uploaded_at': datetime.now().isoformat()
                            }
                        }

                        # Final JSON serialization test
                        json.dumps(upload_data['metadata'])  # Test metadata serialization

                    except Exception as json_error:
                        self.logger.error(f"JSON serialization error for {module}/{filename}: {json_error}")
                        self.logger.error(f"Data types: {data_copy.dtypes.to_dict()}")
                        self.logger.error(f"Sample data: {data_copy.head(1).to_dict()}")

                        # Try emergency data cleaning
                        try:
                            self.logger.info("Attempting emergency data cleaning...")
                            for col in data_copy.columns:
                                data_copy[col] = data_copy[col].astype(str).replace(['nan', 'None', 'NaT'], '')

                            # Retry JSON serialization
                            records_data = data_copy.to_dict('records')
                            json.dumps(records_data[:1] if records_data else [])

                            upload_data = {
                                'records': records_data,
                                'columns': data_copy.columns.tolist(),
                                'metadata': {
                                    'row_count': len(data_copy),
                                    'column_count': len(data_copy.columns),
                                    'uploaded_at': datetime.now().isoformat()
                                }
                            }
                            self.logger.info("Emergency data cleaning successful")

                        except Exception as emergency_error:
                            self.logger.error(f"Emergency data cleaning failed: {emergency_error}")
                            raise Exception(f"Data serialization failed: {json_error}")

                    # Upload the data
                    try:
                        success, message = self.secure_client.upload_data(module, filename, upload_data)
                        if success:
                            self.logger.info(f"Successfully uploaded {module}/{filename} via secure client ({len(data_copy)} rows)")
                            return True
                        else:
                            self.logger.error(f"Secure client upload failed for {module}/{filename}: {message}")
                            raise Exception(f"Backend error: {message}")
                    except Exception as upload_error:
                        self.logger.error(f"Upload request failed for {module}/{filename}: {upload_error}")
                        raise Exception(f"Upload failed: {upload_error}")

                except Exception as data_prep_error:
                    self.logger.error(f"Data preparation failed for {module}/{filename}: {data_prep_error}")
                    raise Exception(f"Data preparation failed: {data_prep_error}")

            elif data is not None and data.empty:
                # Handle empty data case
                self.logger.info(f"Data is empty for {module}/{filename}, uploading empty marker")
                try:
                    upload_data = {
                        'records': [],
                        'columns': [],
                        'metadata': {
                            'row_count': 0,
                            'column_count': 0,
                            'uploaded_at': datetime.now().isoformat(),
                            'empty': True
                        }
                    }
                    success, message = self.secure_client.upload_data(module, filename, upload_data)
                    if success:
                        self.logger.info(f"Successfully uploaded empty data marker for {module}/{filename}")
                        return True
                    else:
                        raise Exception(f"Failed to upload empty data marker: {message}")
                except Exception as empty_upload_error:
                    self.logger.error(f"Failed to upload empty data for {module}/{filename}: {empty_upload_error}")
                    raise Exception(f"Empty data upload failed: {empty_upload_error}")
            else:
                raise Exception("No data to upload - data is None")
        except Exception as e:
            self.logger.error(f"Secure upload failed: {e}")
            raise

    def _prepare_data_for_upload(self, data: pd.DataFrame):
        """Prepare DataFrame for JSON serialization with comprehensive error handling"""
        try:
            self.logger.debug(f"Preparing data for upload: {len(data)} rows, {len(data.columns)} columns")

            if data.empty:
                self.logger.debug("Data is empty, nothing to prepare")
                return

            # Process each column with individual error handling
            for col in data.columns:
                try:
                    col_dtype = str(data[col].dtype)
                    self.logger.debug(f"Processing column '{col}' with dtype: {col_dtype}")

                    if 'datetime64' in col_dtype or pd.api.types.is_datetime64_any_dtype(data[col]):
                        # Handle datetime columns
                        try:
                            data[col] = data[col].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
                            self.logger.debug(f"Converted datetime column '{col}' to string")
                        except Exception as dt_error:
                            self.logger.warning(f"Error converting datetime column '{col}': {dt_error}")
                            data[col] = data[col].astype(str).fillna('')

                    elif col_dtype == 'object':
                        # Handle object columns with safe conversion
                        def safe_convert_timestamps(x):
                            try:
                                if pd.isna(x) or x is None or x == '':
                                    return ''
                                elif isinstance(x, (pd.Timestamp, datetime)):
                                    return x.strftime('%Y-%m-%d %H:%M:%S')
                                elif isinstance(x, date):
                                    return x.strftime('%Y-%m-%d')
                                elif isinstance(x, (int, float)):
                                    if pd.isna(x):
                                        return ''
                                    return str(x)
                                else:
                                    return str(x)
                            except Exception as conv_error:
                                self.logger.debug(f"Error converting value {x}: {conv_error}")
                                return str(x) if x is not None else ''

                        try:
                            data[col] = data[col].apply(safe_convert_timestamps)
                            self.logger.debug(f"Processed object column '{col}'")
                        except Exception as obj_error:
                            self.logger.warning(f"Error processing object column '{col}': {obj_error}")
                            data[col] = data[col].astype(str).fillna('')

                    elif 'float' in col_dtype or 'int' in col_dtype:
                        # Handle numeric columns
                        try:
                            data[col] = data[col].fillna(0 if 'int' in col_dtype else 0.0)
                            self.logger.debug(f"Cleaned numeric column '{col}'")
                        except Exception as num_error:
                            self.logger.warning(f"Error cleaning numeric column '{col}': {num_error}")
                            data[col] = data[col].astype(str).fillna('')

                    else:
                        # Handle other data types
                        try:
                            data[col] = data[col].astype(str).fillna('')
                            self.logger.debug(f"Converted column '{col}' to string")
                        except Exception as str_error:
                            self.logger.warning(f"Error converting column '{col}' to string: {str_error}")
                            data[col] = ''

                except Exception as col_error:
                    self.logger.error(f"Critical error processing column '{col}': {col_error}")
                    try:
                        data[col] = data[col].astype(str).fillna('')
                    except:
                        data[col] = ''

            # Final cleanup
            try:
                data.fillna('', inplace=True)
                self.logger.debug("Final NaN cleanup completed")
            except Exception as fillna_error:
                self.logger.error(f"Error in final NaN cleanup: {fillna_error}")
                for col in data.columns:
                    try:
                        data[col] = data[col].replace([pd.NA, None, float('nan')], '')
                    except:
                        continue

            self.logger.debug(f"Data preparation completed successfully")

        except Exception as e:
            self.logger.error(f"Critical error preparing data for upload: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")

            # Emergency fallback
            try:
                for col in data.columns:
                    try:
                        data[col] = data[col].astype(str).replace(['nan', 'None', 'NaT'], '').fillna('')
                    except:
                        data[col] = ''
                self.logger.info("Emergency data preparation fallback completed")
            except Exception as emergency_error:
                self.logger.error(f"Emergency fallback failed: {emergency_error}")
                raise Exception(f"Data preparation completely failed: {e}")

    def _upload_via_local_firebase(self, module: str, filename: str):
        """Upload file using local Firebase"""
        try:
            database = firebase_manager.get_database()
            if not database:
                raise Exception("Firebase database not available")

            user_id = firebase_auth.current_user.uid

            # Read local data
            df = self.data_manager.read_csv(module, filename)

            if df.empty:
                # Upload empty marker
                data_to_upload = {"_empty": True, "_timestamp": datetime.now().isoformat()}
            else:
                # Convert DataFrame to dict with proper serialization
                df_serializable = self._prepare_dataframe_for_upload(df)

                # Test JSON serialization before uploading
                try:
                    import json
                    records_data = df_serializable.to_dict('records')
                    # Test if the data can be JSON serialized
                    json.dumps(records_data)

                    data_to_upload = {
                        "records": records_data,                      # CSV rows as list of dictionaries
                        "columns": df_serializable.columns.tolist(), # Column names
                        "metadata": {
                            "row_count": len(df_serializable),
                            "column_count": len(df_serializable.columns),
                            "uploaded_at": datetime.now().isoformat(),
                            "backend": "local_firebase"
                        }
                    }
                except (TypeError, ValueError) as json_error:
                    self.logger.error(f"JSON serialization failed for {module}/{filename}: {json_error}")
                    # Log problematic data for debugging
                    self.logger.error(f"Problematic data types: {df_serializable.dtypes.to_dict()}")
                    raise Exception(f"Data contains non-JSON-serializable values: {json_error}")

            # Upload to Firebase
            path = f"users/{user_id}/data/{module}/{filename.replace('.csv', '')}"

            # Get authentication token
            id_token = firebase_auth.id_token
            if not id_token:
                raise Exception("User not authenticated - no ID token available")

            # Try to upload, and if database doesn't exist, create it
            try:
                database.child(path).set(data_to_upload, id_token)
                self.logger.debug(f"Uploaded {module}/{filename} to Firebase")
            except Exception as upload_error:
                if "404" in str(upload_error) or "Not Found" in str(upload_error):
                    # Database doesn't exist, try to create it automatically
                    self.logger.info(f"Database doesn't exist, attempting to create it...")
                    if self._create_database_structure():
                        # Retry upload after creating database
                        try:
                            database.child(path).set(data_to_upload, id_token)
                            self.logger.info(f"Database created and uploaded {module}/{filename} to Firebase")
                        except Exception as retry_error:
                            self.logger.error(f"Upload failed even after database creation: {retry_error}")
                            raise Exception(f"Database creation succeeded but upload failed: {retry_error}")
                    else:
                        # Database creation failed - provide helpful guidance
                        error_msg = (
                            f"Cannot sync {module}/{filename} - Realtime Database doesn't exist.\n"
                            f"Please run: python setup_firebase_database.py\n"
                            f"Or manually create the database in Firebase Console:\n"
                            f"https://console.firebase.google.com/project/jointjourney-a12d2/database"
                        )
                        raise Exception(error_msg)
                elif "Invalid data" in str(upload_error) or "parse JSON" in str(upload_error):
                    # JSON parsing error - log detailed information
                    self.logger.error(f"JSON parsing error for {module}/{filename}")
                    self.logger.error(f"Data shape: {df.shape}")
                    self.logger.error(f"Data types: {df.dtypes.to_dict()}")
                    self.logger.error(f"Sample data: {df.head(2).to_dict()}")
                    raise Exception(f"Firebase rejected data due to JSON parsing error: {upload_error}")
                else:
                    self.logger.error(f"Upload error for {module}/{filename}: {upload_error}")
                    raise upload_error

        except Exception as e:
            self.logger.error(f"Error uploading {module}/{filename}: {e}")
            raise
    
    def download_file(self, module: str, filename: str) -> Optional[pd.DataFrame]:
        """Download file from Firebase with enhanced error handling"""
        try:
            # Always use direct Firebase
            return self._download_via_direct_firebase(module, filename)

        except Exception as e:
            # Handle 404 errors gracefully (database doesn't exist yet)
            if "404" in str(e) or "Not Found" in str(e):
                self.logger.debug(f"No remote data found for {module}/{filename} (database not created yet)")
                return pd.DataFrame()
            else:
                self.logger.error(f"Error downloading {module}/{filename}: {e}")
                return None

    def _download_via_direct_firebase(self, module: str, filename: str) -> Optional[pd.DataFrame]:
        """Download file using direct Firebase client"""
        try:
            # Download via direct Firebase client
            success, data, message = self.firebase_client.download_data(module, filename)

            if not success:
                if "No data found" in message:
                    self.logger.debug(f"No remote data found for {module}/{filename}")
                    return pd.DataFrame()
                else:
                    self.logger.error(f"Direct Firebase download failed for {module}/{filename}: {message}")
                    return None

            if not data:
                return pd.DataFrame()

            # Convert back to DataFrame - handle both old and new data structures
            if "records" in data and "columns" in data:
                # New structure: records + columns + metadata
                df = pd.DataFrame(data["records"], columns=data["columns"])
                self.logger.info(f"Successfully downloaded {len(df)} records for {module}/{filename} via direct Firebase")
                return df
            elif "data" in data and "columns" in data:
                # Old structure: data + columns (for backward compatibility)
                df = pd.DataFrame(data["data"], columns=data["columns"])
                self.logger.info(f"Successfully downloaded {len(df)} records for {module}/{filename} via direct Firebase (legacy format)")
                return df
            else:
                self.logger.warning(f"Unexpected data structure for {module}/{filename}: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Direct Firebase download failed for {module}/{filename}: {e}")
            return None

    def resolve_conflict(self, module: str, filename: str,
                        local_data: pd.DataFrame, remote_data: pd.DataFrame):
        """Resolve sync conflicts using timestamp-based strategy"""
        try:
            # For now, use a simple strategy: merge by ID and use latest timestamp
            if 'id' in local_data.columns and 'id' in remote_data.columns:
                # Merge data by ID, preferring newer entries
                merged_data = self.merge_by_timestamp(local_data, remote_data)
                
                # Save merged data locally
                self.data_manager.write_csv(module, filename, merged_data)
                
                # Upload merged data
                self.upload_file(module, filename)
                
                self.logger.info(f"Resolved conflict for {module}/{filename} by merging")
            else:
                # No ID column - use remote data (server wins)
                self.data_manager.write_csv(module, filename, remote_data)
                self.logger.info(f"Resolved conflict for {module}/{filename} using remote data")
            
        except Exception as e:
            self.logger.error(f"Error resolving conflict for {module}/{filename}: {e}")
            self._emit_signal_safe(self.conflict_detected, module, filename)
    
    def merge_by_timestamp(self, local_data: pd.DataFrame, 
                          remote_data: pd.DataFrame) -> pd.DataFrame:
        """Merge DataFrames by timestamp, preferring newer entries"""
        # Combine both datasets
        combined = pd.concat([local_data, remote_data], ignore_index=True)
        
        # If there's a timestamp column, use it for conflict resolution
        timestamp_cols = ['timestamp', 'created_at', 'updated_at', 'date']
        timestamp_col = None
        
        for col in timestamp_cols:
            if col in combined.columns:
                timestamp_col = col
                break
        
        if timestamp_col:
            # Sort by timestamp and drop duplicates by ID, keeping the latest
            combined = combined.sort_values(timestamp_col)
            combined = combined.drop_duplicates(subset=['id'], keep='last')
        else:
            # No timestamp column - just drop duplicates by ID
            combined = combined.drop_duplicates(subset=['id'], keep='last')
        
        return combined.reset_index(drop=True)
    
    def get_file_hash(self, module: str, filename: str) -> str:
        """Get hash of file contents with comprehensive error handling"""
        try:
            self.logger.debug(f"Getting file hash for {module}/{filename}")

            # Get file path with error handling
            try:
                file_path = self.data_manager.get_file_path(module, filename)
            except Exception as path_error:
                self.logger.error(f"Error getting file path for {module}/{filename}: {path_error}")
                return ""

            # Check if file exists
            try:
                if not file_path.exists():
                    self.logger.debug(f"File does not exist: {file_path}")
                    return ""
            except Exception as exists_error:
                self.logger.error(f"Error checking file existence for {file_path}: {exists_error}")
                return ""

            # Read file content with error handling
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
            except Exception as read_error:
                self.logger.error(f"Error reading file {file_path}: {read_error}")
                return ""

            # Calculate hash with error handling
            try:
                hash_value = hashlib.md5(content).hexdigest()
                self.logger.debug(f"Successfully calculated hash for {module}/{filename}: {hash_value[:8]}...")
                return hash_value
            except Exception as hash_error:
                self.logger.error(f"Error calculating hash for {module}/{filename}: {hash_error}")
                return ""

        except Exception as e:
            self.logger.error(f"Critical error in get_file_hash for {module}/{filename}: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return ""
    
    def get_file_modified_time(self, module: str, filename: str) -> str:
        """Get file modification time with comprehensive error handling"""
        try:
            self.logger.debug(f"Getting file modified time for {module}/{filename}")

            # Get file path with error handling
            try:
                file_path = self.data_manager.get_file_path(module, filename)
            except Exception as path_error:
                self.logger.error(f"Error getting file path for {module}/{filename}: {path_error}")
                return ""

            # Check if file exists
            try:
                if not file_path.exists():
                    self.logger.debug(f"File does not exist: {file_path}")
                    return ""
            except Exception as exists_error:
                self.logger.error(f"Error checking file existence for {file_path}: {exists_error}")
                return ""

            # Get file stats with error handling
            try:
                mtime = file_path.stat().st_mtime
            except Exception as stat_error:
                self.logger.error(f"Error getting file stats for {file_path}: {stat_error}")
                return ""

            # Convert timestamp with error handling
            try:
                modified_time = datetime.fromtimestamp(mtime).isoformat()
                self.logger.debug(f"Successfully got modified time for {module}/{filename}: {modified_time}")
                return modified_time
            except Exception as timestamp_error:
                self.logger.error(f"Error converting timestamp for {module}/{filename}: {timestamp_error}")
                return ""

        except Exception as e:
            self.logger.error(f"Critical error in get_file_modified_time for {module}/{filename}: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return ""
    
    def get_remote_hash(self, module: str, filename: str) -> str:
        """Get hash of remote file"""
        try:
            if not FIREBASE_AVAILABLE or firebase_manager is None:
                return ""

            database = firebase_manager.get_database()
            if not database:
                return ""

            if firebase_auth is None:
                return ""

            # Get authentication token
            id_token = firebase_auth.id_token
            if not id_token:
                return ""

            user_id = firebase_auth.current_user.uid
            path = f"users/{user_id}/data/{module}/{filename.replace('.csv', '')}/timestamp"

            timestamp = database.child(path).get(id_token).val()
            return hashlib.md5(str(timestamp).encode()).hexdigest() if timestamp else ""
        except Exception:
            return ""
    
    def update_metadata(self, module: str, filename: str, 
                       local_hash: str, local_modified: str):
        """Update sync metadata"""
        file_key = f"{module}/{filename}"
        remote_hash = self.get_remote_hash(module, filename)
        
        if file_key in self.sync_metadata:
            metadata = self.sync_metadata[file_key]
            metadata.last_sync = datetime.now().isoformat()
            metadata.local_hash = local_hash
            metadata.remote_hash = remote_hash
            metadata.last_modified = local_modified
            metadata.sync_count += 1
        else:
            metadata = SyncMetadata(
                module=module,
                filename=filename,
                last_sync=datetime.now().isoformat(),
                local_hash=local_hash,
                remote_hash=remote_hash,
                last_modified=local_modified,
                sync_count=1
            )
            self.sync_metadata[file_key] = metadata
    
    def load_metadata(self):
        """Load sync metadata from file"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.sync_metadata = {
                    key: SyncMetadata.from_dict(value)
                    for key, value in data.items()
                }
                
                self.logger.debug(f"Loaded metadata for {len(self.sync_metadata)} files")
        except Exception as e:
            self.logger.error(f"Error loading sync metadata: {e}")
            self.sync_metadata = {}
    
    def save_metadata(self):
        """Save sync metadata to file"""
        try:
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                key: metadata.to_dict()
                for key, metadata in self.sync_metadata.items()
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug("Sync metadata saved")
        except Exception as e:
            self.logger.error(f"Error saving sync metadata: {e}")
    
    def _ensure_database_exists(self) -> bool:
        """Ensure the database exists and is properly initialized"""
        try:
            # In secure backend mode, database initialization is handled by the backend
            # We just need to verify that the secure client is authenticated

            # Get detailed authentication status for debugging
            auth_status = self.secure_client.get_session_status()
            self.logger.debug(f"Database initialization - Auth status: {auth_status}")

            if not self.secure_client.is_authenticated():
                self.logger.warning(f"User not authenticated for database initialization. Status: {auth_status}")
                return False

            # Additional check: verify we have a valid user and token
            if not self.secure_client.current_user:
                self.logger.warning("No current user available for database initialization")
                return False

            if not self.secure_client.id_token:
                self.logger.warning("No ID token available for database initialization")
                return False

            # For secure backend mode, assume database exists if user is authenticated
            # The backend handles database creation and management
            self.logger.info(f"Database initialization verified - user: {self.secure_client.current_user.email}")
            return True

        except Exception as e:
            self.logger.error(f"Error ensuring database exists: {e}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _create_database_structure(self) -> bool:
        """Create the initial database structure using secure backend"""
        try:
            # In secure backend mode, database structure creation is handled by the backend
            # We don't need to create it manually from the client side
            if not self.secure_client.is_authenticated():
                self.logger.error("User not authenticated for database creation")
                return False

            self.logger.info("Database structure creation handled by secure backend")
            return True

        except Exception as e:
            self.logger.error(f"Error creating database structure: {e}")
            return False

    def _create_with_admin_sdk(self, admin_db) -> bool:
        """Create database structure using Firebase Admin SDK"""
        try:
            user_id = firebase_auth.current_user.uid

            # Create initial database structure using Admin SDK
            initial_structure = {
                "users": {
                    user_id: {
                        "profile": {
                            "created_at": datetime.now().isoformat(),
                            "email": firebase_auth.current_user.email,
                            "uid": user_id
                        },
                        "data": {
                            "expenses": {"_initialized": True},
                            "income": {"_initialized": True},
                            "habits": {"_initialized": True},
                            "attendance": {"_initialized": True},
                            "todos": {"_initialized": True},
                            "investments": {"_initialized": True},
                            "budget": {"_initialized": True}
                        }
                    }
                },
                "_metadata": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "Personal Finance Dashboard",
                    "version": "1.0",
                    "created_with": "Admin SDK"
                }
            }

            # Use Admin SDK to set the structure - this can create the database
            admin_db.set(initial_structure)

            self.logger.info("Database structure created successfully using Admin SDK")
            return True

        except Exception as e:
            self.logger.error(f"Error creating database with Admin SDK: {e}")
            return False

    def _create_with_client_sdk(self, database) -> bool:
        """Create database structure using client SDK (fallback)"""
        try:
            user_id = firebase_auth.current_user.uid

            # Get authentication token
            id_token = firebase_auth.id_token
            if not id_token:
                self.logger.error("No authentication token available")
                return False

            # Create initial database structure
            initial_structure = {
                "users": {
                    user_id: {
                        "profile": {
                            "created_at": datetime.now().isoformat(),
                            "email": firebase_auth.current_user.email,
                            "uid": user_id
                        },
                        "data": {
                            "expenses": {"_initialized": True},
                            "income": {"_initialized": True},
                            "habits": {"_initialized": True},
                            "attendance": {"_initialized": True},
                            "todos": {"_initialized": True},
                            "investments": {"_initialized": True},
                            "budget": {"_initialized": True}
                        }
                    }
                },
                "_metadata": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "Personal Finance Dashboard",
                    "version": "1.0",
                    "created_with": "Client SDK"
                }
            }

            # Set the initial structure
            database.set(initial_structure, id_token)
            self.logger.info("Database structure created successfully using Client SDK")
            return True

        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                self.logger.error("Realtime Database doesn't exist in Firebase project")
                self.logger.error("Admin SDK should be able to create it, but it failed")
                return False
            else:
                self.logger.error(f"Error creating database with Client SDK: {e}")
                return False

    def _prepare_dataframe_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame for Firebase upload by converting non-serializable types"""
        df_copy = df.copy()

        # Convert timestamp columns to ISO format strings
        for col in df_copy.columns:
            if df_copy[col].dtype == 'datetime64[ns]' or 'datetime' in str(df_copy[col].dtype):
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            elif hasattr(df_copy[col].dtype, 'name') and 'timestamp' in df_copy[col].dtype.name.lower():
                # Handle pandas Timestamp objects
                df_copy[col] = pd.to_datetime(df_copy[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
            elif df_copy[col].dtype == 'object':
                # Check if object column contains timestamps
                try:
                    # Try to convert to datetime and back to string
                    sample_val = df_copy[col].dropna().iloc[0] if not df_copy[col].dropna().empty else None
                    if sample_val is not None and hasattr(sample_val, 'strftime'):
                        df_copy[col] = pd.to_datetime(df_copy[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    # If conversion fails, leave as is
                    pass

        # Handle NaN, infinity, and other non-JSON-serializable values
        import numpy as np

        # Replace infinity values with None (more comprehensive)
        df_copy = df_copy.replace([float('inf'), float('-inf'), np.inf, -np.inf], None)

        # Replace NaN values with None
        df_copy = df_copy.where(pd.notnull(df_copy), None)

        # Additional cleanup for any remaining problematic values
        for col in df_copy.columns:
            if df_copy[col].dtype in ['float64', 'float32']:
                # Check for any remaining inf or nan values in float columns
                mask_inf = np.isinf(df_copy[col].astype(float, errors='ignore'))
                mask_nan = np.isnan(df_copy[col].astype(float, errors='ignore'))
                df_copy.loc[mask_inf | mask_nan, col] = None

        # Convert numpy types to native Python types for JSON serialization
        for col in df_copy.columns:
            if df_copy[col].dtype == 'float64':
                df_copy[col] = df_copy[col].astype('object').where(df_copy[col].notnull(), None)
            elif df_copy[col].dtype == 'int64':
                df_copy[col] = df_copy[col].astype('object').where(df_copy[col].notnull(), None)
            elif df_copy[col].dtype == 'bool':
                df_copy[col] = df_copy[col].astype('object').where(df_copy[col].notnull(), None)

        return df_copy

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return {
            "status": self.status,
            "available": self.is_available(),
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "synced_files": len(self.sync_metadata),
            "auto_sync_enabled": firebase_manager.config.auto_sync if firebase_manager else False
        }
