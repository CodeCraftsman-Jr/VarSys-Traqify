#!/usr/bin/env python3
"""
Initialization Tracker Module
Tracks and manages the initialization process of application components
"""

import logging
import time
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QTimer


@dataclass
class InitializationStep:
    """Represents a single initialization step"""
    id: str
    name: str
    description: str
    function: Optional[Callable] = None
    weight: int = 1
    dependencies: List[str] = None
    timeout: int = 30  # seconds
    completed: bool = False
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class InitializationTracker(QObject):
    """
    Tracks and coordinates the initialization of application components
    """
    
    # Signals
    step_started = Signal(str, str)  # step_id, description
    step_completed = Signal(str, str, float)  # step_id, description, duration
    step_failed = Signal(str, str, str)  # step_id, description, error
    progress_updated = Signal(int, str, str)  # progress, current_step, detail
    initialization_complete = Signal()
    initialization_failed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialization state
        self.steps: Dict[str, InitializationStep] = {}
        self.step_order: List[str] = []
        self.completed_steps: List[str] = []
        self.failed_steps: List[str] = []
        self.current_step: Optional[str] = None
        
        # Progress tracking
        self.total_weight = 0
        self.completed_weight = 0
        self.is_running = False
        self.start_time = None
        
        # Timeout handling
        self.step_timeout_timer = QTimer()
        self.step_timeout_timer.setSingleShot(True)
        self.step_timeout_timer.timeout.connect(self._handle_step_timeout)
        
    def add_step(self, step_id: str, name: str, description: str, 
                 function: Optional[Callable] = None, weight: int = 1,
                 dependencies: List[str] = None, timeout: int = 30):
        """Add an initialization step"""
        if step_id in self.steps:
            self.logger.warning(f"Step '{step_id}' already exists, replacing")
            
        step = InitializationStep(
            id=step_id,
            name=name,
            description=description,
            function=function,
            weight=weight,
            dependencies=dependencies or [],
            timeout=timeout
        )
        
        self.steps[step_id] = step
        self.total_weight += weight
        
        self.logger.debug(f"Added initialization step: {step_id} (weight: {weight})")
        
    def remove_step(self, step_id: str):
        """Remove an initialization step"""
        if step_id in self.steps:
            step = self.steps[step_id]
            self.total_weight -= step.weight
            del self.steps[step_id]
            
            # Remove from order if present
            if step_id in self.step_order:
                self.step_order.remove(step_id)
                
            self.logger.debug(f"Removed initialization step: {step_id}")
            
    def set_step_order(self, order: List[str]):
        """Set the order of step execution"""
        # Validate that all steps exist
        for step_id in order:
            if step_id not in self.steps:
                raise ValueError(f"Step '{step_id}' not found in registered steps")
                
        self.step_order = order.copy()
        self.logger.debug(f"Set step execution order: {order}")
        
    def _resolve_dependencies(self) -> List[str]:
        """Resolve step dependencies and return execution order"""
        if self.step_order:
            return self.step_order
            
        # Simple dependency resolution (topological sort)
        resolved = []
        remaining = set(self.steps.keys())
        
        while remaining:
            # Find steps with no unresolved dependencies
            ready = []
            for step_id in remaining:
                step = self.steps[step_id]
                if all(dep in resolved for dep in step.dependencies):
                    ready.append(step_id)
                    
            if not ready:
                # Circular dependency or missing dependency
                missing_deps = []
                for step_id in remaining:
                    step = self.steps[step_id]
                    for dep in step.dependencies:
                        if dep not in self.steps:
                            missing_deps.append(f"{step_id} -> {dep}")
                            
                if missing_deps:
                    raise ValueError(f"Missing dependencies: {missing_deps}")
                else:
                    raise ValueError(f"Circular dependency detected in steps: {remaining}")
                    
            # Add ready steps to resolved list
            for step_id in ready:
                resolved.append(step_id)
                remaining.remove(step_id)
                
        return resolved
        
    def start_initialization(self):
        """Start the initialization process"""
        if self.is_running:
            self.logger.warning("Initialization already running")
            return
            
        if not self.steps:
            self.logger.warning("No initialization steps defined")
            self.initialization_complete.emit()
            return
            
        try:
            # Resolve execution order
            execution_order = self._resolve_dependencies()
            
            self.is_running = True
            self.start_time = time.time()
            self.completed_steps.clear()
            self.failed_steps.clear()
            self.completed_weight = 0
            
            self.logger.info(f"Starting initialization with {len(self.steps)} steps")
            self.logger.debug(f"Execution order: {execution_order}")
            
            # Start executing steps
            self._execute_next_step(execution_order)
            
        except Exception as e:
            error_msg = f"Failed to start initialization: {e}"
            self.logger.error(error_msg)
            self.initialization_failed.emit(error_msg)
            self.is_running = False
            
    def _execute_next_step(self, execution_order: List[str]):
        """Execute the next step in the sequence"""
        if not execution_order:
            # All steps completed
            self._finalize_initialization()
            return
            
        step_id = execution_order[0]
        remaining_steps = execution_order[1:]
        
        if step_id in self.failed_steps:
            # Skip failed steps
            self._execute_next_step(remaining_steps)
            return
            
        step = self.steps[step_id]
        self.current_step = step_id
        
        # Update progress
        progress = int((self.completed_weight / self.total_weight) * 100) if self.total_weight > 0 else 0
        self.progress_updated.emit(progress, step.name, step.description)
        
        # Start step timeout timer
        self.step_timeout_timer.start(step.timeout * 1000)
        
        # Execute step
        self.logger.debug(f"Executing step: {step_id}")
        step.start_time = time.time()
        
        self.step_started.emit(step_id, step.description)
        
        try:
            if step.function and callable(step.function):
                # Execute the step function
                result = step.function()
                
                # Handle async results if needed
                if hasattr(result, 'finished'):
                    # Qt signal-based async operation
                    result.finished.connect(lambda: self._step_completed(step_id, remaining_steps))
                    result.error.connect(lambda error: self._step_failed(step_id, str(error), remaining_steps))
                else:
                    # Synchronous operation
                    self._step_completed(step_id, remaining_steps)
            else:
                # No function to execute, mark as completed
                self._step_completed(step_id, remaining_steps)
                
        except Exception as e:
            self._step_failed(step_id, str(e), remaining_steps)
            
    def _step_completed(self, step_id: str, remaining_steps: List[str]):
        """Handle step completion"""
        self.step_timeout_timer.stop()
        
        step = self.steps[step_id]
        step.completed = True
        step.end_time = time.time()
        
        duration = step.end_time - step.start_time if step.start_time else 0
        
        self.completed_steps.append(step_id)
        self.completed_weight += step.weight
        
        self.logger.debug(f"Step completed: {step_id} (duration: {duration:.2f}s)")
        self.step_completed.emit(step_id, step.description, duration)
        
        # Continue with next step
        self._execute_next_step(remaining_steps)
        
    def _step_failed(self, step_id: str, error: str, remaining_steps: List[str]):
        """Handle step failure"""
        self.step_timeout_timer.stop()
        
        step = self.steps[step_id]
        step.error = error
        step.end_time = time.time()
        
        self.failed_steps.append(step_id)
        
        self.logger.error(f"Step failed: {step_id} - {error}")
        self.step_failed.emit(step_id, step.description, error)
        
        # Continue with next step (non-critical failure)
        self._execute_next_step(remaining_steps)
        
    def _handle_step_timeout(self):
        """Handle step timeout"""
        if self.current_step:
            error_msg = f"Step '{self.current_step}' timed out"
            self.logger.error(error_msg)
            # This will be handled by the step failure mechanism
            
    def _finalize_initialization(self):
        """Finalize the initialization process"""
        self.is_running = False
        self.current_step = None
        
        total_time = time.time() - self.start_time if self.start_time else 0
        
        # Final progress update
        self.progress_updated.emit(100, "Complete", "Initialization finished")
        
        if self.failed_steps:
            error_msg = f"Initialization completed with {len(self.failed_steps)} failed steps: {self.failed_steps}"
            self.logger.warning(error_msg)
            self.initialization_failed.emit(error_msg)
        else:
            self.logger.info(f"Initialization completed successfully in {total_time:.2f}s")
            self.initialization_complete.emit()
            
    def get_progress(self) -> Dict[str, Any]:
        """Get current initialization progress"""
        progress = int((self.completed_weight / self.total_weight) * 100) if self.total_weight > 0 else 0
        
        return {
            'progress': progress,
            'total_steps': len(self.steps),
            'completed_steps': len(self.completed_steps),
            'failed_steps': len(self.failed_steps),
            'current_step': self.current_step,
            'is_running': self.is_running,
            'steps': {step_id: {
                'name': step.name,
                'completed': step.completed,
                'error': step.error,
                'duration': (step.end_time - step.start_time) if step.start_time and step.end_time else None
            } for step_id, step in self.steps.items()}
        }
        
    def reset(self):
        """Reset the initialization tracker"""
        self.step_timeout_timer.stop()
        self.completed_steps.clear()
        self.failed_steps.clear()
        self.completed_weight = 0
        self.current_step = None
        self.is_running = False
        self.start_time = None
        
        # Reset step states
        for step in self.steps.values():
            step.completed = False
            step.error = None
            step.start_time = None
            step.end_time = None
            
        self.logger.debug("Initialization tracker reset")
