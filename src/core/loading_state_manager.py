"""
Loading State Manager

Centralized manager for coordinating loading screen, authentication, and main window transitions.
Ensures proper sequencing and prevents overlapping screens.
"""

import logging
import time
from typing import Optional, Callable, Dict, Any
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtWidgets import QApplication


class LoadingState:
    """Enumeration of loading states"""
    INITIALIZING = "initializing"
    LOADING = "loading"
    AUTHENTICATING = "authenticating"
    FINALIZING = "finalizing"
    COMPLETE = "complete"
    ERROR = "error"


class LoadingStateManager(QObject):
    """
    Centralized manager for coordinating all loading-related screen transitions.
    Ensures proper sequencing: loading screen → authentication → main application
    """
    
    # Signals
    state_changed = Signal(str)  # state
    progress_updated = Signal(int, str, str)  # progress, message, detail
    authentication_required = Signal()
    authentication_complete = Signal()
    loading_complete = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # State management
        self.current_state = LoadingState.INITIALIZING
        self.loading_screen = None
        self.main_window = None
        self.authentication_callback = None
        
        # Progress tracking
        self.current_progress = 0
        self.initialization_steps = []
        self.completed_steps = []
        self.step_weights = {}
        self.total_weight = 0
        
        # Timing control
        self.min_loading_time = 2.0  # Minimum time to show loading screen
        self.start_time = None
        self.authentication_start_time = None
        
        # Flags
        self.authentication_required_flag = False
        self.main_window_ready = False
        self.can_close_loading = False
        
    def set_loading_screen(self, loading_screen):
        """Set the loading screen instance"""
        self.loading_screen = loading_screen
        if self.loading_screen:
            # Connect loading screen signals
            self.loading_screen.loading_complete.connect(self._on_loading_screen_closed)
            
    def set_main_window(self, main_window):
        """Set the main window instance"""
        self.main_window = main_window
        self.main_window_ready = True
        self.logger.info("Main window is ready")
        self._check_completion_conditions()
        
    def set_authentication_callback(self, callback: Callable[[], bool]):
        """Set the authentication callback function"""
        self.authentication_callback = callback
        
    def add_initialization_step(self, step_id: str, name: str, weight: int = 1):
        """Add an initialization step with weight"""
        self.initialization_steps.append({
            'id': step_id,
            'name': name,
            'weight': weight,
            'completed': False
        })
        self.step_weights[step_id] = weight
        self.total_weight += weight
        self.logger.debug(f"Added initialization step: {step_id} (weight: {weight})")
        
    def start_loading(self):
        """Start the loading process"""
        self.start_time = time.time()
        self.current_state = LoadingState.LOADING
        self.state_changed.emit(self.current_state)

        if self.loading_screen:
            self.loading_screen.show_loading()
            # Add initial loading steps
            self.loading_screen.add_loading_step("Application startup initiated", "complete")
            self.loading_screen.add_loading_step("Loading screen displayed", "complete")
            self.loading_screen.add_loading_step("Preparing initialization sequence", "loading")

        self.logger.info("Loading process started")
        self._update_progress(0, "Starting application...", "Initializing Traqify")
        
    def complete_step(self, step_id: str, message: str = "", detail: str = "", step_details: list = None):
        """Mark a step as completed and update progress with detailed information"""
        for step in self.initialization_steps:
            if step['id'] == step_id and not step['completed']:
                step['completed'] = True
                self.completed_steps.append(step_id)

                # Calculate progress
                completed_weight = sum(self.step_weights[s] for s in self.completed_steps)
                progress = int((completed_weight / self.total_weight) * 85) if self.total_weight > 0 else 0

                step_message = message or f"Completed {step['name']}"
                self.logger.debug(f"Step completed: {step_id} - Progress: {progress}%")

                # Add detailed step information if provided
                if step_details and self.loading_screen:
                    for step_detail in step_details:
                        self.loading_screen.add_loading_step(step_detail, "complete")

                self._update_progress(progress, step_message, detail)
                break

    def update_step_progress(self, step_id: str, sub_step: str, message: str = "", detail: str = ""):
        """Update progress within a step with sub-step details"""
        if self.loading_screen:
            self.loading_screen.add_loading_step(sub_step, "loading")

        # Update main progress message if provided
        if message:
            self._update_progress(self.current_progress, message, detail)
                
    def require_authentication(self):
        """Signal that authentication is required"""
        if self.current_state != LoadingState.LOADING:
            self.logger.warning("Authentication required but not in loading state")
            return
            
        self.authentication_required_flag = True
        self.authentication_start_time = time.time()
        self.current_state = LoadingState.AUTHENTICATING
        self.state_changed.emit(self.current_state)
        
        # Hide loading screen during authentication
        if self.loading_screen:
            self.loading_screen.hide()
            
        self.logger.info("Authentication required - loading screen hidden")
        self.authentication_required.emit()
        
    def authentication_completed(self, success: bool):
        """Signal that authentication has completed"""
        if self.current_state != LoadingState.AUTHENTICATING:
            self.logger.warning("Authentication completed but not in authenticating state")
            return
            
        if success:
            self.current_state = LoadingState.LOADING
            self.state_changed.emit(self.current_state)
            
            # Restore loading screen after authentication
            if self.loading_screen:
                self.loading_screen.show()
                self.loading_screen.raise_()
                self.loading_screen.activateWindow()
                
            self.logger.info("Authentication successful - loading screen restored")
            self._update_progress(10, "Authentication complete", "Proceeding with initialization")
            self.authentication_complete.emit()
        else:
            self.current_state = LoadingState.ERROR
            self.state_changed.emit(self.current_state)
            self.error_occurred.emit("Authentication failed")
            
    def finalize_loading(self):
        """Begin the finalization phase"""
        if self.current_state not in [LoadingState.LOADING]:
            self.logger.warning(f"Cannot finalize from state: {self.current_state}")
            return
            
        self.current_state = LoadingState.FINALIZING
        self.state_changed.emit(self.current_state)
        
        self.logger.info("Finalizing loading process")
        self._update_progress(90, "Finalizing startup...", "Preparing application for use")
        
        # Check if we can complete immediately
        self._check_completion_conditions()
        
    def _check_completion_conditions(self):
        """Check if all conditions are met to complete loading"""
        if self.current_state != LoadingState.FINALIZING:
            return
            
        # Ensure minimum loading time has passed
        if self.start_time:
            elapsed_time = time.time() - self.start_time
            if elapsed_time < self.min_loading_time:
                remaining_time = self.min_loading_time - elapsed_time
                self.logger.debug(f"Waiting {remaining_time:.1f}s more for minimum loading time")
                QTimer.singleShot(int(remaining_time * 1000), self._check_completion_conditions)
                return
                
        # Check if main window is ready
        if not self.main_window_ready:
            self.logger.debug("Waiting for main window to be ready")
            return
            
        # All conditions met - complete loading
        self._complete_loading()
        
    def _complete_loading(self):
        """Complete the loading process"""
        self.current_state = LoadingState.COMPLETE
        self.state_changed.emit(self.current_state)
        
        self._update_progress(100, "Ready!", "Application loaded successfully")
        
        # Allow a brief moment to show completion
        QTimer.singleShot(800, self._close_loading_screen)
        
    def _close_loading_screen(self):
        """Close the loading screen and show main window"""
        if self.loading_screen:
            self.loading_screen.close_when_ready()
            
        self.logger.info("Loading process complete")
        self.loading_complete.emit()
        
    def _update_progress(self, progress: int, message: str, detail: str = ""):
        """Update progress and emit signal"""
        self.current_progress = progress
        
        if self.loading_screen:
            self.loading_screen.update_progress(progress, message, detail)
            
        self.progress_updated.emit(progress, message, detail)
        
    def _on_loading_screen_closed(self):
        """Handle loading screen closed signal"""
        if self.main_window and self.main_window_ready:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            # Trigger post-loading dialogs
            if hasattr(self.main_window, 'trigger_post_loading_dialogs'):
                self.main_window.trigger_post_loading_dialogs()
                
        self.logger.info("Main window shown, loading sequence complete")
        
    def get_current_state(self) -> str:
        """Get the current loading state"""
        return self.current_state
        
    def is_loading_complete(self) -> bool:
        """Check if loading is complete"""
        return self.current_state == LoadingState.COMPLETE
        
    def handle_error(self, error_message: str):
        """Handle an error during loading"""
        self.current_state = LoadingState.ERROR
        self.state_changed.emit(self.current_state)
        
        if self.loading_screen:
            self.loading_screen.update_progress(0, "Error", error_message)
            
        self.logger.error(f"Loading error: {error_message}")
        self.error_occurred.emit(error_message)
