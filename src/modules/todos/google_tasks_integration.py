"""
Google Tasks API Integration
Provides synchronization between local todos and Google Tasks
"""

import os
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_TASKS_AVAILABLE = True
except ImportError:
    GOOGLE_TASKS_AVAILABLE = False

from .models import TodoItem, Status, Priority, Category


class GoogleTasksIntegration:
    """Google Tasks API integration for todo synchronization"""
    
    # If modifying these scopes, delete the file token.json.
    SCOPES = [
        'https://www.googleapis.com/auth/tasks'
    ]
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger(__name__)
        self.service = None
        self.credentials = None
        self.auth_attempted = False

        # Google API credentials - load from external configuration
        self.client_config = self._load_google_credentials()

        # Initialize with existing credentials if available
        if GOOGLE_TASKS_AVAILABLE and self.client_config:
            self.try_initialize_with_existing_credentials()

    def _load_google_credentials(self) -> Dict[str, Any]:
        """Load Google OAuth credentials from environment variables with secure fallbacks"""
        try:
            # Import environment config loader
            from ...core.env_config import get_env_config
            env_config = get_env_config()

            # Try to load from environment variables first (most secure)
            if env_config.is_google_oauth_configured():
                self.logger.info("Loading Google OAuth credentials from environment variables")
                return env_config.to_google_oauth_config()

            # Legacy environment variable check
            client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
            project_id = os.getenv('GOOGLE_OAUTH_PROJECT_ID')

            if client_id and client_secret and project_id:
                self.logger.info("Loading Google OAuth credentials from individual environment variables")
                return {
                    "installed": {
                        "client_id": client_id,
                        "project_id": project_id,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_secret": client_secret,
                        "redirect_uris": ["http://localhost:8080", "http://localhost"]
                    }
                }

            # Try to load from external credentials file (ONLY for development)
            credentials_file = self.data_dir / "config" / "google_oauth_credentials.json"
            if credentials_file.exists():
                self.logger.warning(f"Loading Google OAuth credentials from file: {credentials_file}")
                self.logger.warning("WARNING: Using file-based credentials is not recommended for production!")
                try:
                    with open(credentials_file, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    self.logger.error(f"Failed to load Google credentials from file: {e}")

            # Return None if no credentials found
            self.logger.warning("Google OAuth credentials not configured. Google Tasks integration will be disabled.")
            self.logger.info("Please set GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, and GOOGLE_OAUTH_PROJECT_ID environment variables")
            self.logger.info("See .env.example for configuration details")
            return None

        except Exception as e:
            self.logger.error(f"Error loading Google OAuth credentials: {e}")
            return None

    def try_initialize_with_existing_credentials(self):
        """Try to initialize with existing credentials without triggering OAuth"""
        try:
            token_file = self.data_dir / "google_tasks_token.json"

            if token_file.exists():
                creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)

                # Only proceed if credentials are valid or can be refreshed
                if creds and creds.valid:
                    self.credentials = creds
                    self.service = build('tasks', 'v1', credentials=creds)
                    self.logger.info("✅ Google Tasks service initialized with existing valid credentials")
                elif creds and creds.expired and creds.refresh_token:
                    try:
                        self.logger.info("🔄 Refreshing expired Google Tasks credentials...")
                        creds.refresh(Request())
                        self.credentials = creds
                        self.service = build('tasks', 'v1', credentials=creds)
                        self.logger.info("✅ Google Tasks service initialized with refreshed credentials")

                        # Save refreshed credentials
                        with open(token_file, 'w') as token:
                            token.write(creds.to_json())
                    except Exception as e:
                        self.logger.warning(f"❌ Failed to refresh Google Tasks credentials: {e}")
                        # Delete the invalid token file to force re-authentication
                        try:
                            if token_file.exists():
                                token_file.unlink()
                                self.logger.info("🗑️ Removed invalid token file")
                        except Exception as delete_error:
                            self.logger.error(f"Failed to delete invalid token file: {delete_error}")
                        self.service = None
                elif creds:
                    # Credentials exist but are invalid and can't be refreshed
                    self.logger.warning("⚠️ Google Tasks credentials exist but are invalid and cannot be refreshed")
                    self.service = None
                else:
                    self.logger.info("⚠️ Google Tasks credentials file exists but contains invalid data")
                    self.service = None
            else:
                self.logger.info("ℹ️ No Google Tasks credentials found - manual authentication required")
                self.service = None

        except Exception as e:
            self.logger.warning(f"❌ Failed to initialize Google Tasks with existing credentials: {e}")
            self.service = None

    def initialize_service(self, force_auth: bool = False):
        """Initialize Google Tasks service with optional OAuth authentication"""
        if not force_auth and self.auth_attempted and self.service is not None:
            self.logger.info("Google Tasks service already initialized and available")
            return

        # Reset auth_attempted flag if force_auth is True or service is None
        if force_auth or self.service is None:
            self.auth_attempted = False

        self.auth_attempted = True

        try:
            creds = None
            token_file = self.data_dir / "google_tasks_token.json"

            # The file token.json stores the user's access and refresh tokens.
            if token_file.exists():
                creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)

            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        self.logger.info("🔄 Attempting to refresh expired credentials...")
                        creds.refresh(Request())
                        self.logger.info("✅ Credentials refreshed successfully")
                    except Exception as e:
                        self.logger.warning(f"❌ Failed to refresh credentials: {e}")
                        # Delete the invalid token file
                        try:
                            if token_file.exists():
                                token_file.unlink()
                                self.logger.info("🗑️ Removed invalid token file")
                        except Exception as delete_error:
                            self.logger.error(f"Failed to delete invalid token file: {delete_error}")

                        if not force_auth:
                            self.logger.info("Skipping OAuth authentication - use manual authentication if needed")
                            self.service = None
                            return
                        creds = None

                if not creds and force_auth:
                    # Only trigger OAuth if explicitly requested and credentials are configured
                    if not self.client_config:
                        self.logger.error("Google OAuth credentials not configured. Cannot authenticate.")
                        self.service = None
                        return

                    self.logger.info("Starting OAuth authentication flow...")

                    # Create credentials file temporarily
                    temp_creds_file = self.data_dir / "temp_credentials.json"
                    with open(temp_creds_file, 'w') as f:
                        json.dump(self.client_config, f)

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(temp_creds_file), self.SCOPES)
                    creds = flow.run_local_server(port=0)

                    # Clean up temp file
                    temp_creds_file.unlink()
                elif not creds:
                    self.logger.info("No valid credentials and OAuth not forced - Google Tasks unavailable")
                    self.service = None
                    return

                # Save the credentials for the next run
                if creds:
                    with open(token_file, 'w') as token:
                        token.write(creds.to_json())

            if creds:
                self.credentials = creds
                self.service = build('tasks', 'v1', credentials=creds)
                self.logger.info("Google Tasks service initialized successfully")
            else:
                self.service = None
                self.logger.info("Google Tasks service not available - no valid credentials")

        except Exception as e:
            self.logger.error(f"Failed to initialize Google Tasks service: {e}")
            self.service = None
    
    def is_available(self) -> bool:
        """Check if Google Tasks integration is available"""
        return GOOGLE_TASKS_AVAILABLE and self.service is not None



    def authenticate(self) -> bool:
        """Manually trigger Google Tasks authentication"""
        try:
            self.initialize_service(force_auth=True)
            return self.is_available()
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False

    def validate_and_refresh_token(self) -> bool:
        """Validate current token and refresh if needed"""
        try:
            token_file = self.data_dir / "google_tasks_token.json"

            if not token_file.exists():
                self.logger.info("No token file found")
                return False

            # Load credentials
            creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)

            if not creds:
                self.logger.warning("Invalid credentials in token file")
                return False

            # Check if credentials are valid
            if creds.valid:
                self.credentials = creds
                self.service = build('tasks', 'v1', credentials=creds)
                self.logger.info("✅ Token is valid")
                return True

            # Try to refresh if expired
            if creds.expired and creds.refresh_token:
                try:
                    self.logger.info("🔄 Token expired, attempting refresh...")
                    creds.refresh(Request())

                    # Save refreshed credentials
                    with open(token_file, 'w') as token:
                        token.write(creds.to_json())

                    self.credentials = creds
                    self.service = build('tasks', 'v1', credentials=creds)
                    self.logger.info("✅ Token refreshed successfully")
                    return True

                except Exception as e:
                    self.logger.warning(f"❌ Failed to refresh token: {e}")
                    # Delete invalid token file
                    try:
                        token_file.unlink()
                        self.logger.info("🗑️ Removed invalid token file")
                    except Exception as delete_error:
                        self.logger.error(f"Failed to delete invalid token file: {delete_error}")
                    return False
            else:
                self.logger.warning("Token expired and no refresh token available")
                return False

        except Exception as e:
            self.logger.error(f"Error validating token: {e}")
            return False

    def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication status information"""
        token_file = self.data_dir / "google_tasks_token.json"
        credentials_exist = token_file.exists()

        # Check if credentials are valid
        credentials_valid = False
        credentials_expired = False
        token_expiry = None

        if credentials_exist:
            try:
                creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)
                if creds:
                    credentials_valid = creds.valid
                    credentials_expired = creds.expired
                    if hasattr(creds, 'expiry') and creds.expiry:
                        token_expiry = creds.expiry.isoformat()
            except Exception as e:
                self.logger.warning(f"Error reading token file: {e}")

        return {
            'libraries_available': GOOGLE_TASKS_AVAILABLE,
            'service_available': self.service is not None,
            'credentials_exist': credentials_exist,
            'credentials_valid': credentials_valid,
            'credentials_expired': credentials_expired,
            'token_expiry': token_expiry,
            'auth_attempted': self.auth_attempted,
            'is_connected': self.is_available(),
            'status_message': self._get_status_message(),
            'client_config_loaded': self.client_config is not None
        }

    def _get_status_message(self) -> str:
        """Get a human-readable status message"""
        if not GOOGLE_TASKS_AVAILABLE:
            return "❌ Google Tasks libraries not installed"

        if not self.client_config:
            return "⚙️ OAuth credentials not configured"

        token_file = self.data_dir / "google_tasks_token.json"
        if not token_file.exists():
            return "🔗 Ready to connect - Click 'Connect Google Tasks'"

        if self.service is not None:
            return "✅ Connected to Google Tasks"

        # Check token status more thoroughly
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)
            if creds and creds.expired:
                if creds.refresh_token:
                    return "🔄 Token expired - Will refresh automatically"
                else:
                    return "⚠️ Token expired - Reconnection needed"
            elif creds and not creds.valid:
                return "⚠️ Invalid token - Reconnection needed"
        except Exception:
            return "⚠️ Token file corrupted - Reconnection needed"

        return "⚠️ Connection issue - Try reconnecting"
    
    def get_task_lists(self) -> List[Dict[str, Any]]:
        """Get all task lists from Google Tasks"""
        if not self.is_available():
            return []
        
        try:
            results = self.service.tasklists().list().execute()
            items = results.get('items', [])
            return items
        except HttpError as e:
            self.logger.error(f"Error getting task lists: {e}")
            return []
    
    def get_tasks(self, tasklist_id: str = '@default', include_completed: bool = True) -> List[Dict[str, Any]]:
        """Get tasks from a specific task list with pagination support"""
        if not self.is_available():
            return []

        try:
            all_tasks = []
            page_token = None
            page_count = 0

            while True:
                # Get both completed and incomplete tasks with pagination
                params = {
                    'tasklist': tasklist_id,
                    'maxResults': 100  # Increase from default
                }

                if include_completed:
                    params['showCompleted'] = True
                    params['showHidden'] = True

                if page_token:
                    params['pageToken'] = page_token

                results = self.service.tasks().list(**params).execute()
                items = results.get('items', [])
                all_tasks.extend(items)
                page_count += 1

                self.logger.debug(f"Retrieved page {page_count}: {len(items)} tasks from {tasklist_id}")

                # Check for next page
                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            self.logger.info(f"Retrieved {len(all_tasks)} total tasks from task list {tasklist_id} across {page_count} pages (completed: {include_completed})")
            return all_tasks

        except HttpError as e:
            self.logger.error(f"Error getting tasks: {e}")
            return []
    
    def create_task(self, todo_item: TodoItem, tasklist_id: str = '@default') -> Optional[str]:
        """Create a task in Google Tasks"""
        if not self.is_available():
            return None
        
        try:
            task = {
                'title': str(todo_item.title) if todo_item.title else 'Untitled',
                'status': 'completed' if todo_item.status == Status.COMPLETED.value else 'needsAction'
            }

            # Only add notes if it's not empty/null/NaN
            if todo_item.description and str(todo_item.description).strip() and str(todo_item.description) != 'nan':
                task['notes'] = str(todo_item.description)

            if todo_item.due_date:
                # Convert date to RFC 3339 format
                if isinstance(todo_item.due_date, date):
                    task['due'] = todo_item.due_date.strftime('%Y-%m-%dT00:00:00.000Z')
                elif isinstance(todo_item.due_date, datetime):
                    task['due'] = todo_item.due_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')

            result = self.service.tasks().insert(tasklist=tasklist_id, body=task).execute()
            task_id = result.get('id')

            self.logger.info(f"Created Google Task: {todo_item.title} (ID: {task_id})")
            return task_id
            
        except HttpError as e:
            self.logger.error(f"Error creating task: {e}")
            return None
    
    def update_task(self, google_task_id: str, todo_item: TodoItem, tasklist_id: str = '@default') -> bool:
        """Update a task in Google Tasks"""
        if not self.is_available():
            return False
        
        try:
            task = {
                'id': google_task_id,
                'title': str(todo_item.title) if todo_item.title else 'Untitled',
                'status': 'completed' if todo_item.status == Status.COMPLETED.value else 'needsAction'
            }

            # Only add notes if it's not empty/null/NaN
            if todo_item.description and str(todo_item.description).strip() and str(todo_item.description) != 'nan':
                task['notes'] = str(todo_item.description)

            if todo_item.due_date:
                if isinstance(todo_item.due_date, date):
                    task['due'] = todo_item.due_date.strftime('%Y-%m-%dT00:00:00.000Z')
                elif isinstance(todo_item.due_date, datetime):
                    task['due'] = todo_item.due_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')

            self.service.tasks().update(tasklist=tasklist_id, task=google_task_id, body=task).execute()
            self.logger.info(f"Updated Google Task: {todo_item.title}")
            return True
            
        except HttpError as e:
            self.logger.error(f"Error updating task: {e}")
            return False
    
    def delete_task(self, google_task_id: str, tasklist_id: str = '@default') -> bool:
        """Delete a task from Google Tasks"""
        if not self.is_available():
            return False
        
        try:
            self.service.tasks().delete(tasklist=tasklist_id, task=google_task_id).execute()
            self.logger.info(f"Deleted Google Task ID: {google_task_id}")
            return True
            
        except HttpError as e:
            self.logger.error(f"Error deleting task: {e}")
            return False
    
    def sync_from_google(self, tasklist_id: str = '@default') -> List[TodoItem]:
        """Sync tasks from Google Tasks to local format"""
        if not self.is_available():
            return []

        google_tasks = self.get_tasks(tasklist_id)
        local_todos = []

        for task in google_tasks:
            try:
                # Convert Google Task to TodoItem
                todo_item = TodoItem(
                    title=task.get('title', 'Untitled'),
                    description=task.get('notes', ''),
                    status=Status.COMPLETED.value if task.get('status') == 'completed' else Status.PENDING.value,
                    priority=Priority.MEDIUM.value,  # Default priority
                    google_task_id=task.get('id')
                )

                # Parse due date
                if 'due' in task:
                    try:
                        due_str = task['due']
                        # Remove timezone info for simplicity
                        if 'T' in due_str:
                            due_str = due_str.split('T')[0]
                        todo_item.due_date = datetime.strptime(due_str, '%Y-%m-%d').date()
                    except ValueError:
                        pass

                # Parse completed date
                if 'completed' in task and task.get('status') == 'completed':
                    try:
                        completed_str = task['completed']
                        if 'T' in completed_str:
                            completed_str = completed_str.split('T')[0]
                        todo_item.completed_at = datetime.strptime(completed_str, '%Y-%m-%d')
                    except ValueError:
                        pass

                # Parse updated date as created_at if not available
                if 'updated' in task:
                    try:
                        updated_str = task['updated']
                        if 'T' in updated_str:
                            updated_str = updated_str.split('T')[0]
                        if not todo_item.created_at:
                            todo_item.created_at = datetime.strptime(updated_str, '%Y-%m-%d')
                    except ValueError:
                        pass

                local_todos.append(todo_item)

            except Exception as e:
                self.logger.warning(f"Error converting Google Task: {e}")

        return local_todos

    def sync_from_all_lists(self) -> List[TodoItem]:
        """Sync tasks from ALL Google Task lists with detailed logging"""
        if not self.is_available():
            self.logger.warning("❌ Google Tasks integration not available")
            return []

        all_todos = []

        try:
            task_lists = self.get_task_lists()
            self.logger.info(f"📋 Found {len(task_lists)} Google Task lists to sync")

            # Log all available task lists
            for i, task_list in enumerate(task_lists):
                list_title = task_list.get('title', 'Unknown')
                list_id = task_list.get('id', 'Unknown')
                self.logger.debug(f"   {i+1}. '{list_title}' (ID: {list_id})")

            for i, task_list in enumerate(task_lists):
                list_id = task_list['id']
                list_title = task_list['title']

                try:
                    self.logger.info(f"🔄 [{i+1}/{len(task_lists)}] Syncing from task list: '{list_title}'")
                    todos_from_list = self.sync_from_google(list_id)
                    all_todos.extend(todos_from_list)
                    self.logger.info(f"✅ [{i+1}/{len(task_lists)}] Retrieved {len(todos_from_list)} tasks from '{list_title}'")

                except Exception as e:
                    self.logger.error(f"❌ Error syncing from task list '{list_title}': {e}")

            # Log final summary
            self.logger.info(f"📊 GOOGLE TASKS SYNC SUMMARY:")
            self.logger.info(f"   📋 Task Lists Processed: {len(task_lists)}")
            self.logger.info(f"   📈 Total Tasks Retrieved: {len(all_todos)}")

            # Log status breakdown
            if all_todos:
                status_counts = {}
                for todo in all_todos:
                    status = getattr(todo, 'status', 'Unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                self.logger.info(f"   📊 Status breakdown: {status_counts}")

            return all_todos

        except Exception as e:
            self.logger.error(f"❌ Error in sync_from_all_lists: {e}")
            return []










    
    def sync_to_google(self, todo_items: List[TodoItem], tasklist_id: str = '@default') -> Dict[str, str]:
        """Sync local todos to Google Tasks"""
        if not self.is_available():
            return {}

        sync_results = {}

        for todo_item in todo_items:
            try:


                if hasattr(todo_item, 'google_task_id') and todo_item.google_task_id:
                    # Update existing task
                    success = self.update_task(todo_item.google_task_id, todo_item, tasklist_id)
                    sync_results[str(todo_item.id)] = 'updated' if success else 'failed'
                else:
                    # Create new task
                    google_task_id = self.create_task(todo_item, tasklist_id)
                    if google_task_id:
                        todo_item.google_task_id = google_task_id
                        sync_results[str(todo_item.id)] = 'created'
                    else:
                        sync_results[str(todo_item.id)] = 'failed'

            except Exception as e:
                self.logger.error(f"Error syncing todo {todo_item.title}: {e}")
                sync_results[str(todo_item.id)] = 'failed'

        return sync_results
