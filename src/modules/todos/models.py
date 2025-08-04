"""
To-Do List Data Models
Handles task management data structure and validation
"""

import logging
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class Priority(Enum):
    """Task priority levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class Status(Enum):
    """Task status"""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Category(Enum):
    """Task categories"""
    PERSONAL = "Personal"
    WORK = "Work"
    STUDY = "Study"
    HEALTH = "Health"
    FINANCE = "Finance"
    SHOPPING = "Shopping"
    PROJECTS = "Projects"
    OTHER = "Other"


@dataclass
class TodoItem:
    """Data class for individual todo items"""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    category: str = Category.PERSONAL.value
    priority: str = Priority.MEDIUM.value
    status: str = Status.PENDING.value
    due_date: Optional[Union[str, datetime, date]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    tags: str = ""  # Comma-separated tags
    notes: str = ""
    google_task_id: Optional[str] = None  # Google Tasks synchronization ID
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        self.updated_at = datetime.now()
        
        # Handle due_date conversion
        if self.due_date and isinstance(self.due_date, str):
            try:
                self.due_date = datetime.strptime(self.due_date, '%Y-%m-%d').date()
            except ValueError:
                self.due_date = None
        elif isinstance(self.due_date, datetime):
            self.due_date = self.due_date.date()
    
    def mark_completed(self):
        """Mark task as completed"""
        self.status = Status.COMPLETED.value
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def mark_in_progress(self):
        """Mark task as in progress"""
        self.status = Status.IN_PROGRESS.value
        self.updated_at = datetime.now()
    
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if not self.due_date or self.status == Status.COMPLETED.value:
            return False
        return self.due_date < date.today()
    
    def days_until_due(self) -> Optional[int]:
        """Get days until due date"""
        if not self.due_date:
            return None
        delta = self.due_date - date.today()
        return delta.days
    
    def get_priority_weight(self) -> int:
        """Get numeric weight for priority sorting"""
        weights = {
            Priority.LOW.value: 1,
            Priority.MEDIUM.value: 2,
            Priority.HIGH.value: 3,
            Priority.URGENT.value: 4
        }
        return weights.get(self.priority, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        data = asdict(self)
        
        # Convert date objects to strings
        if isinstance(data['due_date'], date):
            data['due_date'] = data['due_date'].strftime('%Y-%m-%d')
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(data['completed_at'], datetime):
            data['completed_at'] = data['completed_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TodoItem':
        """Create from dictionary"""
        import pandas as pd

        # Clean data - handle NaN and empty values
        cleaned_data = {}
        for key, value in data.items():
            if pd.isna(value) or value == '' or str(value).lower() == 'nan':
                if key in ['title', 'description', 'category', 'priority', 'status', 'tags', 'notes']:
                    cleaned_data[key] = ''
                elif key in ['estimated_hours', 'actual_hours']:
                    cleaned_data[key] = 0.0
                elif key in ['id']:
                    cleaned_data[key] = None
                else:
                    cleaned_data[key] = None
            else:
                cleaned_data[key] = value

        # Handle datetime strings
        for field in ['created_at', 'updated_at', 'completed_at']:
            if field in cleaned_data and isinstance(cleaned_data[field], str) and cleaned_data[field]:
                try:
                    cleaned_data[field] = datetime.strptime(cleaned_data[field], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    cleaned_data[field] = None

        # Ensure required string fields have default values
        if not cleaned_data.get('title'):
            cleaned_data['title'] = 'Untitled'
        if not cleaned_data.get('category'):
            cleaned_data['category'] = Category.PERSONAL.value
        if not cleaned_data.get('priority'):
            cleaned_data['priority'] = Priority.MEDIUM.value
        if not cleaned_data.get('status'):
            cleaned_data['status'] = Status.PENDING.value

        return cls(**cleaned_data)
    
    def validate(self) -> List[str]:
        """Validate the todo item"""
        errors = []
        
        if not self.title.strip():
            errors.append("Title is required")
        
        if self.priority not in [p.value for p in Priority]:
            errors.append(f"Invalid priority: {self.priority}")
        
        if self.status not in [s.value for s in Status]:
            errors.append(f"Invalid status: {self.status}")
        
        if self.category not in [c.value for c in Category]:
            errors.append(f"Invalid category: {self.category}")
        
        if self.estimated_hours < 0:
            errors.append("Estimated hours cannot be negative")
        
        if self.actual_hours < 0:
            errors.append("Actual hours cannot be negative")
        
        return errors


class TodoDataModel:
    """Data model for todo list management"""
    
    def __init__(self, data_manager):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("="*40)
        self.logger.info("INITIALIZING TODO DATA MODEL")
        self.logger.info("="*40)
        
        try:
            self.data_manager = data_manager
            self.module_name = "todos"
            self.filename = "todo_items.csv"
            
            # Default columns for CSV
            self.columns = [
                'id', 'title', 'description', 'category', 'priority', 'status',
                'due_date', 'created_at', 'updated_at', 'completed_at',
                'estimated_hours', 'actual_hours', 'tags', 'notes', 'google_task_id'
            ]
            
            # Initialize Google Tasks integration
            try:
                from .google_tasks_integration import GoogleTasksIntegration
                self.google_tasks = GoogleTasksIntegration(str(data_manager.data_dir))

                auth_status = self.google_tasks.get_auth_status()
                if self.google_tasks.is_available():
                    self.logger.info("✅ Google Tasks integration initialized and authenticated")
                elif auth_status['libraries_available']:
                    if auth_status['credentials_exist']:
                        self.logger.info("ℹ️ Google Tasks libraries available, credentials exist but not authenticated")
                    else:
                        self.logger.info("ℹ️ Google Tasks libraries available, no credentials - manual authentication required")
                else:
                    self.logger.warning("⚠️ Google Tasks libraries not available")

            except Exception as e:
                self.logger.warning(f"⚠️ Google Tasks integration failed: {e}")
                self.google_tasks = None



            # Automatically sync from Google Tasks if available
            if self.is_google_tasks_available():
                self.logger.info("🔄 Attempting automatic sync from Google Tasks...")
                try:
                    # Sync from Google Tasks
                    tasks_synced = self.sync_from_google_tasks()
                    self.logger.info(f"📋 Synced {tasks_synced} tasks from Google Tasks")

                    if tasks_synced > 0:
                        self.logger.info(f"✅ Automatically synced {tasks_synced} tasks")
                    else:
                        self.logger.info("ℹ️ No new tasks found during automatic sync")

                except Exception as e:
                    self.logger.warning(f"⚠️ Automatic sync failed: {e}")
                    # Fallback to basic Google Tasks sync
                    try:
                        synced_count = self.sync_from_google_tasks()
                        if synced_count > 0:
                            self.logger.info(f"✅ Fallback: Synced {synced_count} tasks from Google Tasks only")
                    except Exception as fallback_error:
                        self.logger.warning(f"⚠️ Fallback sync also failed: {fallback_error}")

            # Clean up any invalid IDs in the data
            try:
                fixed_count = self.cleanup_invalid_ids()
                if fixed_count > 0:
                    self.logger.info(f"🔧 Data cleanup: Fixed {fixed_count} todos with invalid IDs")
            except Exception as e:
                self.logger.warning(f"⚠️ Data cleanup failed: {e}")

            self.logger.info("✅ TodoDataModel initialization SUCCESSFUL")

        except Exception as e:
            self.logger.error(f"❌ CRITICAL ERROR in TodoDataModel.__init__: {e}")
            raise
    
    def get_all_todos(self) -> pd.DataFrame:
        """Get all todo items"""
        try:
            df = self.data_manager.read_csv(self.module_name, self.filename, self.columns)
            return df
        except Exception as e:
            self.logger.error(f"Error getting todos: {e}")
            return pd.DataFrame(columns=self.columns)
    
    def add_todo(self, todo: TodoItem) -> bool:
        """Add a new todo item with Google Tasks integration"""
        errors = todo.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False

        # Set creation timestamp if not set
        if not todo.created_at:
            todo.created_at = datetime.now()

        # If Google Tasks is available and this todo doesn't have a Google Task ID, create it in Google Tasks first
        if self.is_google_tasks_available() and not todo.google_task_id:
            try:
                google_task_id = self.google_tasks.create_task(todo)
                if google_task_id:
                    todo.google_task_id = google_task_id
                    self.logger.info(f"Created task in Google Tasks: {todo.title} (ID: {google_task_id})")
                else:
                    self.logger.warning(f"Failed to create task in Google Tasks: {todo.title}")
            except Exception as e:
                self.logger.warning(f"Error creating task in Google Tasks: {e}")

        # Add to local storage
        success = self.data_manager.append_row(
            self.module_name,
            self.filename,
            todo.to_dict(),
            self.columns
        )

        if success:
            self.logger.info(f"Successfully added todo: {todo.title}")

        return success
    
    def update_todo(self, todo_id: int, todo: TodoItem) -> bool:
        """Update an existing todo item with Google Tasks integration"""
        errors = todo.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False

        # Set update timestamp
        todo.updated_at = datetime.now()

        # If status changed to completed, set completed timestamp
        if todo.status == Status.COMPLETED.value and not todo.completed_at:
            todo.completed_at = datetime.now()

        # Update in Google Tasks if available and has Google Task ID
        if self.is_google_tasks_available() and todo.google_task_id:
            try:
                success = self.google_tasks.update_task(todo.google_task_id, todo)
                if success:
                    self.logger.info(f"Updated task in Google Tasks: {todo.title}")
                else:
                    self.logger.warning(f"Failed to update task in Google Tasks: {todo.title}")
            except Exception as e:
                self.logger.warning(f"Error updating task in Google Tasks: {e}")
        elif self.is_google_tasks_available() and not todo.google_task_id:
            # If no Google Task ID but Google Tasks is available, create it
            try:
                google_task_id = self.google_tasks.create_task(todo)
                if google_task_id:
                    todo.google_task_id = google_task_id
                    self.logger.info(f"Created task in Google Tasks during update: {todo.title}")
            except Exception as e:
                self.logger.warning(f"Error creating task in Google Tasks during update: {e}")

        # Update local storage
        success = self.data_manager.update_row(
            self.module_name,
            self.filename,
            todo_id,
            todo.to_dict()
        )

        if success:
            self.logger.info(f"Successfully updated todo: {todo.title}")

        return success
    
    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo item with Google Tasks integration"""
        try:
            # Get the todo first to check for Google Task ID
            todo = self.get_todo_by_id(todo_id)
            if not todo:
                self.logger.warning(f"Todo with ID {todo_id} not found")
                return False

            # Delete from Google Tasks if available and has Google Task ID
            if self.is_google_tasks_available() and todo.google_task_id:
                try:
                    success = self.google_tasks.delete_task(todo.google_task_id)
                    if success:
                        self.logger.info(f"Deleted task from Google Tasks: {todo.title}")
                    else:
                        self.logger.warning(f"Failed to delete task from Google Tasks: {todo.title}")
                except Exception as e:
                    self.logger.warning(f"Error deleting task from Google Tasks: {e}")

            # Delete from local storage
            success = self.data_manager.delete_row(
                self.module_name,
                self.filename,
                todo_id
            )

            if success:
                self.logger.info(f"Successfully deleted todo: {todo.title}")

            return success

        except Exception as e:
            self.logger.error(f"Error deleting todo {todo_id}: {e}")
            return False

    def get_todo_by_id(self, todo_id: int) -> Optional[TodoItem]:
        """Get a specific todo item by ID"""
        try:
            df = self.get_all_todos()
            if df.empty:
                return None

            todo_row = df[df['id'] == todo_id]
            if todo_row.empty:
                return None

            return TodoItem.from_dict(todo_row.iloc[0].to_dict())

        except Exception as e:
            self.logger.error(f"Error getting todo by ID {todo_id}: {e}")
            return None

    def cleanup_invalid_ids(self) -> int:
        """Clean up todos with invalid (NaN/None) IDs by assigning new valid IDs"""
        try:
            df = self.get_all_todos()
            if df.empty:
                return 0

            # Find rows with invalid IDs
            invalid_mask = pd.isna(df['id']) | (df['id'] == '') | (df['id'].isnull())
            invalid_rows = df[invalid_mask]

            if invalid_rows.empty:
                self.logger.info("No invalid IDs found - data is clean")
                return 0

            self.logger.info(f"Found {len(invalid_rows)} rows with invalid IDs - fixing...")

            # Get the maximum valid ID to start from
            valid_ids = df[~invalid_mask]['id'].dropna()
            if not valid_ids.empty:
                max_id = int(valid_ids.max())
            else:
                max_id = 0

            # Assign new IDs to invalid rows
            fixed_count = 0
            for idx in invalid_rows.index:
                max_id += 1
                df.loc[idx, 'id'] = max_id
                fixed_count += 1

                # Log the fix
                title = df.loc[idx, 'title']
                google_task_id = df.loc[idx, 'google_task_id']
                self.logger.debug(f"Assigned ID {max_id} to todo: '{title}' (Google ID: {google_task_id})")

            # Save the cleaned data
            self.data_manager.write_csv(self.module_name, self.filename, df)

            self.logger.info(f"✅ Fixed {fixed_count} todos with invalid IDs")
            return fixed_count

        except Exception as e:
            self.logger.error(f"Error cleaning up invalid IDs: {e}")
            return 0

    def get_todos_by_status(self, status: str) -> pd.DataFrame:
        """Get todos filtered by status"""
        df = self.get_all_todos()
        if df.empty:
            return df
        return df[df['status'] == status]
    
    def get_todos_by_priority(self, priority: str) -> pd.DataFrame:
        """Get todos filtered by priority"""
        df = self.get_all_todos()
        if df.empty:
            return df
        return df[df['priority'] == priority]
    
    def get_todos_by_category(self, category: str) -> pd.DataFrame:
        """Get todos filtered by category"""
        df = self.get_all_todos()
        if df.empty:
            return df
        return df[df['category'] == category]
    
    def get_overdue_todos(self) -> pd.DataFrame:
        """Get overdue todos"""
        df = self.get_all_todos()
        if df.empty:
            return df
        
        today = date.today().strftime('%Y-%m-%d')
        overdue = df[
            (df['due_date'].notna()) & 
            (df['due_date'] != '') & 
            (df['due_date'] < today) & 
            (df['status'] != Status.COMPLETED.value)
        ]
        return overdue
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get todo statistics"""
        df = self.get_all_todos()
        
        if df.empty:
            return {
                'total_todos': 0,
                'completed': 0,
                'pending': 0,
                'in_progress': 0,
                'overdue': 0,
                'completion_rate': 0.0,
                'by_priority': {},
                'by_category': {}
            }
        
        total = len(df)
        completed = len(df[df['status'] == Status.COMPLETED.value])
        pending = len(df[df['status'] == Status.PENDING.value])
        in_progress = len(df[df['status'] == Status.IN_PROGRESS.value])
        
        # Count overdue
        today = date.today().strftime('%Y-%m-%d')
        overdue = len(df[
            (df['due_date'].notna()) & 
            (df['due_date'] != '') & 
            (df['due_date'] < today) & 
            (df['status'] != Status.COMPLETED.value)
        ])
        
        completion_rate = (completed / total * 100) if total > 0 else 0.0
        
        # Group by priority and category
        by_priority = df['priority'].value_counts().to_dict()
        by_category = df['category'].value_counts().to_dict()
        
        return {
            'total_todos': total,
            'completed': completed,
            'pending': pending,
            'in_progress': in_progress,
            'overdue': overdue,
            'completion_rate': completion_rate,
            'by_priority': by_priority,
            'by_category': by_category
        }

    # Google Tasks Synchronization Methods
    def is_google_tasks_available(self) -> bool:
        """Check if Google Tasks integration is available"""
        return self.google_tasks is not None and self.google_tasks.is_available()

    def authenticate_google_tasks(self) -> bool:
        """Manually authenticate with Google Tasks"""
        if self.google_tasks is None:
            self.logger.warning("Google Tasks integration not initialized")
            return False

        try:
            success = self.google_tasks.authenticate()
            if success:
                self.logger.info("✅ Google Tasks authentication successful")
            else:
                self.logger.warning("❌ Google Tasks authentication failed")
            return success
        except Exception as e:
            self.logger.error(f"Error during Google Tasks authentication: {e}")
            return False

    def get_google_tasks_status(self) -> Dict[str, Any]:
        """Get Google Tasks integration status"""
        if self.google_tasks is None:
            return {
                'available': False,
                'error': 'Google Tasks integration not initialized'
            }

        status = self.google_tasks.get_auth_status()
        status['available'] = self.google_tasks.is_available()

        return status



    def sync_to_google_tasks(self) -> Dict[str, str]:
        """Sync local todos to Google Tasks"""
        if not self.is_google_tasks_available():
            self.logger.warning("Google Tasks not available for sync")
            return {}

        try:
            # Get all local todos
            df = self.get_all_todos()
            if df.empty:
                return {}

            # Convert to TodoItem objects
            todo_items = []
            for _, row in df.iterrows():
                todo_item = TodoItem.from_dict(row.to_dict())
                todo_items.append(todo_item)

            # Sync to Google Tasks
            results = self.google_tasks.sync_to_google(todo_items)

            # Update local records with Google Task IDs
            for todo_item in todo_items:
                if hasattr(todo_item, 'google_task_id') and todo_item.google_task_id:
                    self.update_todo(todo_item.id, todo_item)

            self.logger.info(f"Synced {len(results)} todos to Google Tasks")
            return results

        except Exception as e:
            self.logger.error(f"Error syncing to Google Tasks: {e}")
            return {}

    def sync_from_google_tasks(self, full_sync: bool = False) -> int:
        """Sync todos from Google Tasks to local storage"""
        if not self.is_google_tasks_available():
            self.logger.warning("Google Tasks not available for sync")
            return 0

        try:
            # Get todos from Google Tasks - use full sync for all lists or default list only
            if full_sync:
                self.logger.info("Performing full sync from ALL Google Task lists")
                google_todos = self.google_tasks.sync_from_all_lists()
            else:
                self.logger.info("Performing sync from default Google Task list")
                google_todos = self.google_tasks.sync_from_google()

            self.logger.info(f"Retrieved {len(google_todos)} tasks from Google Tasks")

            if not google_todos:
                self.logger.info("No tasks found in Google Tasks")
                return 0

            # Get existing local todos
            local_df = self.get_all_todos()
            existing_google_ids = set()

            if not local_df.empty and 'google_task_id' in local_df.columns:
                existing_google_ids = set(local_df['google_task_id'].dropna().tolist())

            added_count = 0
            updated_count = 0

            for todo_item in google_todos:
                try:
                    # Skip if already exists locally
                    if todo_item.google_task_id in existing_google_ids:
                        self.logger.debug(f"Task already exists locally: {todo_item.title}")
                        continue

                    # Set creation timestamp if not set
                    if not todo_item.created_at:
                        todo_item.created_at = datetime.now()

                    # Add new todo from Google Tasks
                    if self.add_todo(todo_item):
                        added_count += 1
                        self.logger.debug(f"Added task from Google: {todo_item.title}")
                    else:
                        self.logger.warning(f"Failed to add task: {todo_item.title}")

                except Exception as e:
                    self.logger.warning(f"Error processing Google Task '{todo_item.title}': {e}")

            self.logger.info(f"Sync from Google Tasks completed: {added_count} added, {updated_count} updated")
            return added_count

        except Exception as e:
            self.logger.error(f"Error syncing from Google Tasks: {e}")
            return 0

    def full_sync_google_tasks(self) -> Dict[str, Any]:
        """Perform full bidirectional sync with Google Tasks"""
        if not self.is_google_tasks_available():
            return {'error': 'Google Tasks not available'}

        try:
            # First sync from Google to get any new tasks (full sync from all lists)
            from_google = self.sync_from_google_tasks(full_sync=True)

            # Then sync to Google to update any local changes
            to_google = self.sync_to_google_tasks()

            return {
                'from_google': from_google,
                'to_google': len(to_google),
                'sync_results': to_google
            }

        except Exception as e:
            self.logger.error(f"Error in full sync: {e}")
            return {'error': str(e)}


















