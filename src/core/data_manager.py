"""
Data Manager Module
Handles all CSV data operations for the Personal Finance Dashboard
"""

import os
import csv
import json
import shutil
import logging
import shutil
import threading
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union
from PySide6.QtCore import QObject, Signal


class DataManager(QObject):
    """Manages all data operations for the application"""
    
    # Signals for data changes
    data_changed = Signal(str, str)  # module, operation
    error_occurred = Signal(str)     # error message
    
    def __init__(self, data_directory: str = "data"):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initializing DataManager with directory: {data_directory}")

        self.data_dir = Path(data_directory)
        self.logger.debug(f"Data directory path: {self.data_dir.absolute()}")

        self.ensure_directories()
        self._auto_save_enabled = True

        # Firebase sync integration
        self.sync_engine = None
        self._sync_enabled = False

        # Sync coordination to prevent overlapping operations
        self._pending_syncs = set()  # Track modules with pending sync operations
        self._active_syncs = set()   # Track modules currently being synced
        self._sync_timers = {}       # Track QTimer objects for each module

        self.logger.info("DataManager initialization complete")
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        self.logger.debug("Ensuring data directories exist")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Main data directory created/verified: {self.data_dir}")

        # Create module-specific directories
        modules = [
            "expenses", "income", "habits", "attendance",
            "todos", "investments", "budget", "config"
        ]

        for module in modules:
            module_dir = self.data_dir / module
            module_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Module directory created/verified: {module_dir}")

        self.logger.info(f"All {len(modules)} module directories ensured")
    
    def get_file_path(self, module: str, filename: str) -> Path:
        """Get the full path for a data file"""
        return self.data_dir / module / filename
    
    def file_exists(self, module: str, filename: str) -> bool:
        """Check if a data file exists"""
        return self.get_file_path(module, filename).exists()
    
    def read_csv(self, module: str, filename: str,
                 default_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Read CSV file and return DataFrame with enhanced error handling"""
        try:
            file_path = self.get_file_path(module, filename)

            if file_path.exists() and file_path.stat().st_size > 0:
                # File exists and is not empty
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')

                    # Validate DataFrame
                    if df.empty:
                        print(f"Warning: {module}/{filename} is empty")
                        return self._create_empty_dataframe(default_columns)

                    # Convert date columns safely
                    self._convert_date_columns(df)

                    # Validate required columns if specified
                    if default_columns:
                        missing_cols = set(default_columns) - set(df.columns)
                        if missing_cols:
                            print(f"Warning: Missing columns in {module}/{filename}: {missing_cols}")
                            # Add missing columns with default values
                            for col in missing_cols:
                                df[col] = None

                    return df

                except pd.errors.EmptyDataError:
                    print(f"Warning: {module}/{filename} is empty or corrupted")
                    # Create empty DataFrame directly to avoid recursion
                    if default_columns:
                        df = pd.DataFrame()
                        for col in default_columns:
                            df[col] = pd.Series(dtype=object)
                        return df
                    return pd.DataFrame()
                except pd.errors.ParserError as pe:
                    print(f"Error parsing {module}/{filename}: {pe}")
                    # Create empty DataFrame directly to avoid recursion
                    if default_columns:
                        df = pd.DataFrame()
                        for col in default_columns:
                            df[col] = pd.Series(dtype=object)
                        return df
                    return pd.DataFrame()
            else:
                # File doesn't exist or is empty, create new one
                if default_columns:
                    df = pd.DataFrame()
                    for col in default_columns:
                        df[col] = pd.Series(dtype=object)
                    return df
                return pd.DataFrame()

        except Exception as e:
            print(f"Unexpected error reading {module}/{filename}: {str(e)}")
            self.error_occurred.emit(f"Error reading {module}/{filename}: {str(e)}")
            # Create empty DataFrame directly to avoid recursion
            if default_columns:
                df = pd.DataFrame()
                for col in default_columns:
                    df[col] = pd.Series(dtype=object)
                return df
            return pd.DataFrame()

    def load_data(self, module: str, filename: str) -> Optional[pd.DataFrame]:
        """Load data from a CSV file for the specified module and filename

        This method is used by the sync engine to load data for uploading to the backend.
        Returns None if the file doesn't exist or is empty.
        """
        try:
            file_path = self.get_file_path(module, filename)

            if not file_path.exists():
                self.logger.debug(f"File does not exist: {file_path}")
                return None

            if file_path.stat().st_size == 0:
                self.logger.debug(f"File is empty: {file_path}")
                return None

            # Use the existing read_csv method to load the data
            df = self.read_csv(module, filename)

            if df.empty:
                self.logger.debug(f"Loaded DataFrame is empty for {module}/{filename}")
                return None

            self.logger.debug(f"Successfully loaded {len(df)} rows from {module}/{filename}")
            return df

        except Exception as e:
            self.logger.error(f"Error loading data from {module}/{filename}: {e}")
            return None

    def _create_empty_dataframe(self, default_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Create an empty DataFrame with safe column handling"""
        if default_columns:
            try:
                # Ensure column names are safe strings
                safe_columns = [str(col) for col in default_columns if col is not None and col != '']
                # Create DataFrame directly without any recursive calls
                df = pd.DataFrame()
                for col in safe_columns:
                    df[col] = pd.Series(dtype=object)
                return df
            except Exception as df_error:
                print(f"Error creating DataFrame with columns {default_columns}: {df_error}")
                # Return basic empty DataFrame without recursion
                return pd.DataFrame()
        return pd.DataFrame()
    
    def write_csv(self, module: str, filename: str, data: pd.DataFrame):
        """Write DataFrame to CSV file with backup and recovery"""
        try:
            file_path = self.get_file_path(module, filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup of existing file if it exists
            backup_created = False
            if file_path.exists():
                backup_created = self._create_file_backup(file_path)

            # Convert datetime columns to string for CSV storage
            df_copy = data.copy()
            self._prepare_for_csv(df_copy)

            # Write to temporary file first
            temp_path = file_path.with_suffix('.tmp')
            df_copy.to_csv(temp_path, index=False, encoding='utf-8')

            # Verify the temporary file was written correctly
            if temp_path.exists() and temp_path.stat().st_size > 0:
                # Replace original file with temporary file
                if file_path.exists():
                    file_path.unlink()
                temp_path.rename(file_path)

                self.logger.debug(f"Successfully wrote {len(data)} rows to {module}/{filename}")

                if self._auto_save_enabled:
                    self.data_changed.emit(module, "write")
                    # Trigger sync if enabled
                    self.trigger_sync_for_module(module)
            else:
                raise Exception("Temporary file was not created properly")

        except Exception as e:
            error_msg = f"Error writing {module}/{filename}: {str(e)}"
            self.logger.error(error_msg)

            # Try to restore from backup if write failed
            if backup_created:
                self._restore_from_backup(file_path)

            self.error_occurred.emit(error_msg)

    def _create_file_backup(self, file_path: Path) -> bool:
        """Create a backup of the file"""
        try:
            backup_dir = file_path.parent / ".backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name

            shutil.copy2(file_path, backup_path)
            self.logger.debug(f"Created backup: {backup_path}")

            # Keep only last 5 backups per file
            self._cleanup_old_backups(backup_dir, file_path.name)

            return True
        except Exception as e:
            self.logger.warning(f"Failed to create backup for {file_path}: {e}")
            return False

    def _restore_from_backup(self, file_path: Path) -> bool:
        """Restore file from most recent backup"""
        try:
            backup_dir = file_path.parent / ".backups"
            if not backup_dir.exists():
                return False

            # Find most recent backup
            pattern = f"{file_path.stem}_*{file_path.suffix}"
            backups = list(backup_dir.glob(pattern))

            if not backups:
                return False

            # Sort by modification time, get most recent
            latest_backup = max(backups, key=lambda p: p.stat().st_mtime)

            shutil.copy2(latest_backup, file_path)
            self.logger.info(f"Restored {file_path} from backup {latest_backup}")

            return True
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            return False

    def _cleanup_old_backups(self, backup_dir: Path, filename: str, keep_count: int = 5):
        """Keep only the most recent backups"""
        try:
            base_name = Path(filename).stem
            pattern = f"{base_name}_*{Path(filename).suffix}"
            backups = list(backup_dir.glob(pattern))

            if len(backups) > keep_count:
                # Sort by modification time, keep newest
                backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)

                # Remove old backups
                for old_backup in backups[keep_count:]:
                    old_backup.unlink()
                    self.logger.debug(f"Removed old backup: {old_backup}")

        except Exception as e:
            self.logger.warning(f"Failed to cleanup old backups: {e}")
    
    def append_row(self, module: str, filename: str, row_data: Dict[str, Any],
                   default_columns: Optional[List[str]] = None) -> bool:
        """Append a new row to CSV file with enhanced validation"""
        try:
            # Validate input data
            if not row_data or not isinstance(row_data, dict):
                self.error_occurred.emit("Invalid row data provided")
                return False

            df = self.read_csv(module, filename, default_columns)

            # Add ID if not present or invalid
            if 'id' not in row_data or pd.isna(row_data['id']) or row_data['id'] == '' or row_data['id'] is None:
                row_data['id'] = self._generate_id(df)

            # Validate ID uniqueness
            if not df.empty and 'id' in df.columns:
                if row_data['id'] in df['id'].values:
                    print(f"Warning: ID {row_data['id']} already exists, generating new one")
                    row_data['id'] = self._generate_id(df)

            # Add timestamps if not present
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if 'created_at' in default_columns and 'created_at' not in row_data:
                row_data['created_at'] = current_time
            if 'updated_at' in default_columns and 'updated_at' not in row_data:
                row_data['updated_at'] = current_time

            # Clean data - remove None values and convert to appropriate types
            cleaned_data = self._clean_row_data(row_data, default_columns)

            # Create new row DataFrame
            new_row = pd.DataFrame([cleaned_data])

            # Concatenate with existing data
            df = pd.concat([df, new_row], ignore_index=True)

            # Write back to file
            self.write_csv(module, filename, df)

            self.data_changed.emit(module, "append")
            # Trigger sync if enabled
            self.trigger_sync_for_module(module)
            return True

        except Exception as e:
            print(f"Error appending to {module}/{filename}: {str(e)}")
            self.error_occurred.emit(f"Error appending to {module}/{filename}: {str(e)}")
            return False
    
    def update_row(self, module: str, filename: str, row_id: Union[int, str],
                   update_data: Dict[str, Any], id_column: str = 'id') -> bool:
        """Update a specific row in CSV file"""
        try:
            # Validate row_id is not NaN, None, or empty
            if pd.isna(row_id) or row_id is None or row_id == '' or str(row_id).lower() == 'nan':
                self.error_occurred.emit(f"Invalid {id_column} provided: {row_id}")
                return False

            df = self.read_csv(module, filename)

            if df.empty:
                return False

            # Convert row_id to appropriate type for comparison
            try:
                # Try to convert to int if it's numeric
                if isinstance(row_id, str) and row_id.isdigit():
                    row_id = int(row_id)
                elif isinstance(row_id, float):
                    row_id = int(row_id)
            except (ValueError, TypeError):
                pass  # Keep original type if conversion fails

            # Find the row to update
            mask = df[id_column] == row_id

            if not mask.any():
                self.error_occurred.emit(f"Row with {id_column}={row_id} not found")
                return False
            
            # Update the row with proper dtype handling
            for column, value in update_data.items():
                if column in df.columns:
                    # Handle dtype compatibility for numeric columns
                    if df[column].dtype in ['float64', 'int64'] and value == '':
                        # Convert empty string to NaN for numeric columns
                        import numpy as np
                        df.loc[mask, column] = np.nan
                    else:
                        df.loc[mask, column] = value
            
            # Write back to file
            self.write_csv(module, filename, df)
            
            self.data_changed.emit(module, "update")
            # Trigger sync if enabled
            self.trigger_sync_for_module(module)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Error updating {module}/{filename}: {str(e)}")
            return False

    def update_record(self, module: str, record_id: Union[int, str], update_data: Dict[str, Any]) -> bool:
        """Update a record in the module's CSV file (alias for update_row)"""
        return self.update_row(module, f"{module}.csv", record_id, update_data)

    def delete_row(self, module: str, filename: str, row_id: Union[int, str],
                   id_column: str = 'id') -> bool:
        """Delete a specific row from CSV file"""
        try:
            # Validate row_id is not NaN, None, or empty
            if pd.isna(row_id) or row_id is None or row_id == '' or str(row_id).lower() == 'nan':
                self.error_occurred.emit(f"Invalid {id_column} provided for deletion: {row_id}")
                return False

            df = self.read_csv(module, filename)

            if df.empty:
                return False

            # Convert row_id to appropriate type for comparison
            try:
                # Try to convert to int if it's numeric
                if isinstance(row_id, str) and row_id.isdigit():
                    row_id = int(row_id)
                elif isinstance(row_id, float):
                    row_id = int(row_id)
            except (ValueError, TypeError):
                pass  # Keep original type if conversion fails

            # Check if row exists before deletion
            if not (df[id_column] == row_id).any():
                self.error_occurred.emit(f"Row with {id_column}={row_id} not found for deletion")
                return False

            # Remove the row
            df = df[df[id_column] != row_id]
            
            # Write back to file
            self.write_csv(module, filename, df)
            
            self.data_changed.emit(module, "delete")
            # Trigger sync if enabled
            self.trigger_sync_for_module(module)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Error deleting from {module}/{filename}: {str(e)}")
            return False
    
    def search_data(self, module: str, filename: str, 
                    search_term: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Search for data across specified columns"""
        try:
            df = self.read_csv(module, filename)
            
            if df.empty or not search_term:
                return df
            
            if columns is None:
                columns = df.columns.tolist()
            
            # Create search mask
            mask = pd.Series([False] * len(df))
            
            for column in columns:
                if column in df.columns:
                    mask |= df[column].astype(str).str.contains(
                        search_term, case=False, na=False
                    )
            
            return df[mask]
            
        except Exception as e:
            self.error_occurred.emit(f"Error searching {module}/{filename}: {str(e)}")
            return pd.DataFrame()
    
    def backup_data(self, backup_name: Optional[str] = None) -> bool:
        """Create a backup of all data"""
        try:
            if backup_name is None:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_dir = self.data_dir.parent / "backups" / backup_name
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all data files
            shutil.copytree(self.data_dir, backup_dir / "data", dirs_exist_ok=True)
            
            # Create backup info file
            backup_info = {
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "description": f"Automatic backup created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            with open(backup_dir / "backup_info.json", 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Error creating backup: {str(e)}")
            return False

    def set_sync_engine(self, sync_engine):
        """Set the Firebase sync engine"""
        self.sync_engine = sync_engine
        self._sync_enabled = True
        self.logger.info("Firebase sync engine connected to DataManager")

    def enable_sync(self, enabled: bool = True):
        """Enable or disable sync integration"""
        self._sync_enabled = enabled and self.sync_engine is not None
        self.logger.info(f"Sync integration {'enabled' if self._sync_enabled else 'disabled'}")

    def trigger_sync_for_module(self, module: str):
        """Trigger sync for a specific module after data changes with coordination"""
        if not self._sync_enabled:
            self.logger.debug(f"Sync disabled, skipping sync for {module}")
            return

        if not self.sync_engine:
            self.logger.debug(f"Sync engine not available, skipping sync for {module}")
            return

        # Check if sync is already active or pending for this module
        if module in self._active_syncs:
            self.logger.debug(f"Sync already active for {module}, skipping duplicate request")
            return

        if module in self._pending_syncs:
            self.logger.debug(f"Sync already pending for {module}, skipping duplicate request")
            return

        try:
            # Mark module as having a pending sync
            self._pending_syncs.add(module)

            # Cancel any existing timer for this module
            if module in self._sync_timers:
                old_timer = self._sync_timers[module]
                try:
                    if hasattr(old_timer, 'isActive') and old_timer.isActive():
                        old_timer.stop()
                        self.logger.debug(f"Cancelled previous sync timer for {module}")
                    elif hasattr(old_timer, 'cancel'):
                        old_timer.cancel()
                        self.logger.debug(f"Cancelled previous sync timer for {module}")
                except Exception as timer_error:
                    self.logger.warning(f"Error cancelling timer for {module}: {timer_error}")

            # Use simple threading timer to avoid Qt threading issues completely
            import threading

            def safe_sync():
                """Safely execute sync with comprehensive error handling and coordination"""
                try:
                    # Remove from pending and add to active
                    self._pending_syncs.discard(module)
                    self._active_syncs.add(module)

                    # Clean up timer reference
                    self._sync_timers.pop(module, None)

                    if self.sync_engine and hasattr(self.sync_engine, 'sync_module'):
                        self.logger.debug(f"Starting background sync for module: {module}")
                        self.sync_engine.sync_module(module)
                        self.logger.debug(f"Completed background sync for module: {module}")
                    else:
                        self.logger.warning(f"Sync engine not available or missing sync_module method")

                except Exception as sync_error:
                    self.logger.error(f"Background sync failed for {module}: {sync_error}")
                    # Don't emit Qt signals from background threads to prevent crashes
                finally:
                    # Always remove from active syncs when done
                    self._active_syncs.discard(module)
                    self.logger.debug(f"Sync operation completed for {module}")

            # Create and start threading timer (completely thread-safe, no Qt dependencies)
            timer = threading.Timer(2.0, safe_sync)
            timer.daemon = True  # Don't prevent application shutdown
            self._sync_timers[module] = timer
            timer.start()
            self.logger.debug(f"Scheduled background sync for {module} in 2 seconds (threading.Timer)")

        except Exception as e:
            # Clean up state on error
            self._pending_syncs.discard(module)
            self._sync_timers.pop(module, None)

            self.logger.error(f"Error scheduling sync for {module}: {e}")
            # Don't let sync errors crash the application
            try:
                self.error_occurred.emit(f"Failed to schedule sync for {module}: {str(e)}")
            except Exception as emit_error:
                self.logger.error(f"Failed to emit sync scheduling error signal: {emit_error}")





    def get_sync_status(self) -> dict:
        """Get current sync status"""
        if self.sync_engine:
            status = self.sync_engine.get_sync_status()
            # Add coordination status
            status.update({
                "pending_syncs": list(self._pending_syncs),
                "active_syncs": list(self._active_syncs),
                "scheduled_timers": list(self._sync_timers.keys())
            })
            return status
        return {"available": False, "enabled": False}

    def cleanup_sync_operations(self):
        """Clean up all pending sync operations"""
        try:
            # Stop all active timers
            for module, timer in self._sync_timers.items():
                if timer and timer.isActive():
                    timer.stop()
                    self.logger.debug(f"Stopped sync timer for {module}")

            # Clear all tracking sets and dictionaries
            self._sync_timers.clear()
            self._pending_syncs.clear()
            self._active_syncs.clear()

            self.logger.info("All sync operations cleaned up")

        except Exception as e:
            self.logger.error(f"Error during sync cleanup: {e}")

    def __del__(self):
        """Cleanup when DataManager is destroyed"""
        try:
            self.cleanup_sync_operations()
        except Exception as e:
            # Don't raise exceptions in destructor
            pass
    
    def _generate_id(self, df: pd.DataFrame) -> int:
        """Generate a new unique ID for a DataFrame"""
        if df.empty or 'id' not in df.columns:
            return 1

        # Filter out NaN values and convert to numeric
        valid_ids = df['id'].dropna()
        if valid_ids.empty:
            return 1

        try:
            # Convert to numeric, handling any string IDs
            numeric_ids = pd.to_numeric(valid_ids, errors='coerce').dropna()
            if numeric_ids.empty:
                return 1
            return int(numeric_ids.max()) + 1
        except (ValueError, TypeError):
            return 1
    
    def _convert_date_columns(self, df: pd.DataFrame):
        """Convert string date columns to datetime"""
        date_columns = ['date', 'created_at', 'updated_at', 'deadline', 'due_date']
        
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    def _prepare_for_csv(self, df: pd.DataFrame):
        """Prepare DataFrame for CSV storage"""
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]':
                df[col] = df[col].dt.strftime('%Y-%m-%d')
            elif df[col].dtype == 'object':
                # Handle NaN values in object columns
                df[col] = df[col].fillna('')

    def _clean_row_data(self, row_data: Dict[str, Any], default_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Clean and validate row data with enhanced sanitization"""
        cleaned = {}

        for key, value in row_data.items():
            # Handle None values
            if value is None or (isinstance(value, str) and value.lower() in ['none', 'null', 'nan', '']):
                cleaned[key] = self._get_default_value_for_column(key)
            # Handle numeric values with enhanced validation
            elif key in ['id', 'amount', 'goal_inc', 'zomato', 'swiggy', 'shadow_fax', 'other_sources',
                        'earned', 'progress', 'extra', 'target_count', 'completed_count']:
                cleaned[key] = self._clean_numeric_value(key, value)
            # Handle boolean values with enhanced validation
            elif key in ['is_active', 'is_completed', 'is_holiday', 'is_unofficial_leave']:
                cleaned[key] = self._clean_boolean_value(value)
            # Handle date values
            elif key in ['date', 'created_at', 'updated_at', 'deadline', 'due_date']:
                cleaned[key] = self._clean_date_value(value)
            # Handle string values with sanitization
            else:
                cleaned[key] = self._clean_string_value(value)

        # Validate required fields
        if default_columns:
            for col in default_columns:
                if col not in cleaned:
                    cleaned[col] = self._get_default_value_for_column(col)

        return cleaned

    def _get_default_value_for_column(self, column_name: str) -> Any:
        """Get appropriate default value for a column"""
        if column_name in ['id', 'amount', 'goal_inc', 'zomato', 'swiggy', 'shadow_fax', 'other_sources',
                          'earned', 'progress', 'extra', 'target_count', 'completed_count']:
            return 0
        elif column_name in ['is_active', 'is_completed', 'is_holiday', 'is_unofficial_leave']:
            return False
        elif column_name in ['date', 'created_at', 'updated_at']:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            return ''

    def _clean_numeric_value(self, column_name: str, value: Any) -> Union[int, float]:
        """Clean and validate numeric values"""
        try:
            # Handle string representations
            if isinstance(value, str):
                value = value.strip().replace(',', '')  # Remove commas
                if value == '':
                    return 0

            # Convert to appropriate numeric type
            if column_name == 'id':
                return max(1, int(float(value)))  # IDs must be positive
            elif column_name in ['amount', 'goal_inc', 'zomato', 'swiggy', 'shadow_fax', 'other_sources', 'earned']:
                return max(0, float(value))  # Money values must be non-negative
            elif column_name in ['progress']:
                return max(0, min(100, float(value)))  # Progress is 0-100%
            else:
                return max(0, int(float(value)))  # Other numeric values must be non-negative
        except (ValueError, TypeError, OverflowError):
            return 0

    def _clean_boolean_value(self, value: Any) -> bool:
        """Clean and validate boolean values"""
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower().strip() in ['true', '1', 'yes', 'on', 'active', 'completed']
        elif isinstance(value, (int, float)):
            return bool(value)
        else:
            return False

    def _clean_date_value(self, value: Any) -> str:
        """Clean and validate date values"""
        if isinstance(value, str) and value.strip():
            # Try to parse and reformat date
            try:
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y']:
                    try:
                        parsed_date = datetime.strptime(value.strip(), fmt)
                        return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        continue
                # If no format matches, return current time
                return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            except:
                return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _clean_string_value(self, value: Any) -> str:
        """Clean and validate string values"""
        if value is None:
            return ''

        # Convert to string and sanitize
        str_value = str(value).strip()

        # Remove potentially harmful characters
        import re
        # Remove control characters except newlines and tabs
        str_value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str_value)

        # Limit length to prevent excessive data
        max_length = 1000  # Reasonable limit for most text fields
        if len(str_value) > max_length:
            str_value = str_value[:max_length] + '...'

        return str_value
    
    def get_module_summary(self, module: str) -> Dict[str, Any]:
        """Get summary statistics for a module"""
        try:
            module_dir = self.data_dir / module
            if not module_dir.exists():
                return {}
            
            summary = {
                "total_files": 0,
                "total_records": 0,
                "last_modified": None,
                "files": []
            }
            
            for file_path in module_dir.glob("*.csv"):
                df = pd.read_csv(file_path)
                file_info = {
                    "name": file_path.name,
                    "records": len(df),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime)
                }
                
                summary["files"].append(file_info)
                summary["total_records"] += len(df)
                
                if (summary["last_modified"] is None or 
                    file_info["modified"] > summary["last_modified"]):
                    summary["last_modified"] = file_info["modified"]
            
            summary["total_files"] = len(summary["files"])
            return summary
            
        except Exception as e:
            self.error_occurred.emit(f"Error getting summary for {module}: {str(e)}")
            return {}
    
    def set_auto_save(self, enabled: bool):
        """Enable or disable auto-save"""
        self._auto_save_enabled = enabled
