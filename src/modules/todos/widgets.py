"""
To-Do List UI Widgets
Contains all UI components for the todo list module
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QCheckBox, QFrame, QGroupBox, QScrollArea, QTabWidget,
    QProgressBar, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QButtonGroup, QDoubleSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QSplitter, QProgressDialog,
    QCalendarWidget, QListWidget, QListWidgetItem, QStackedWidget,
    QInputDialog
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QBrush, QPainter, QTextCharFormat

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

from .models import TodoItem, TodoDataModel, Priority, Status, Category
from .sync_worker import SyncProgressDialog
from src.ui.themes.utils import get_calendar_color_for_state, get_calendar_color_with_alpha, get_current_theme


class TodoItemWidget(QFrame):
    """Widget for displaying a single todo item"""
    
    item_updated = Signal(int)  # Emits todo ID when updated
    item_deleted = Signal(int)  # Emits todo ID when deleted
    
    def __init__(self, todo_item: TodoItem, parent=None):
        super().__init__(parent)
        self.todo_item = todo_item
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Setup the UI for todo item"""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin: 2px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        # Checkbox for completion
        self.completed_checkbox = QCheckBox()
        self.completed_checkbox.setChecked(self.todo_item.status == Status.COMPLETED.value)
        self.completed_checkbox.toggled.connect(self.toggle_completion)
        header_layout.addWidget(self.completed_checkbox)
        
        # Title with calendar event indicator
        title_text = self.todo_item.title
        if (hasattr(self.todo_item, 'google_task_id') and
            self.todo_item.google_task_id and
            str(self.todo_item.google_task_id).startswith('cal_')):
            title_text = f"📅 {title_text}"  # Add calendar emoji for calendar events

        self.title_label = QLabel(title_text)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Priority badge
        self.priority_label = QLabel(self.todo_item.priority)
        self.priority_label.setStyleSheet(self.get_priority_style())
        header_layout.addWidget(self.priority_label)
        
        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_item)
        header_layout.addWidget(edit_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_item)
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # Description
        if self.todo_item.description:
            desc_label = QLabel(self.todo_item.description)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        # Details row
        details_layout = QHBoxLayout()
        
        # Category
        cat_label = QLabel(f"Category: {self.todo_item.category}")
        details_layout.addWidget(cat_label)
        
        # Due date
        if self.todo_item.due_date:
            due_label = QLabel(f"Due: {self.todo_item.due_date}")
            if self.todo_item.is_overdue():
                due_label.setStyleSheet("color: red; font-weight: bold;")
            details_layout.addWidget(due_label)
        
        details_layout.addStretch()
        layout.addLayout(details_layout)
    
    def get_priority_style(self) -> str:
        """Get CSS style for priority badge"""
        styles = {
            Priority.LOW.value: "background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px;",
            Priority.MEDIUM.value: "background-color: #ffc107; color: white; padding: 2px 8px; border-radius: 3px;",
            Priority.HIGH.value: "background-color: #fd7e14; color: white; padding: 2px 8px; border-radius: 3px;",
            Priority.URGENT.value: "background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 3px;"
        }
        return styles.get(self.todo_item.priority, styles[Priority.MEDIUM.value])
    
    def update_display(self):
        """Update the display based on current item state"""
        if self.todo_item.status == Status.COMPLETED.value:
            # Use theme-neutral styling for completed items
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #555;
                    border-radius: 5px;
                    margin: 2px;
                    padding: 5px;
                    opacity: 0.7;
                }
            """)
            self.title_label.setStyleSheet("text-decoration: line-through; color: #888;")
        else:
            # Use theme-neutral styling for active items
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #555;
                    border-radius: 5px;
                    margin: 2px;
                    padding: 5px;
                }
            """)
            self.title_label.setStyleSheet("text-decoration: none;")
    
    def toggle_completion(self, checked: bool):
        """Toggle completion status"""
        if checked:
            self.todo_item.mark_completed()
        else:
            self.todo_item.status = Status.PENDING.value
            self.todo_item.completed_at = None
            self.todo_item.updated_at = datetime.now()
        
        self.update_display()
        self.item_updated.emit(self.todo_item.id)
    
    def edit_item(self):
        """Open edit dialog"""
        dialog = TodoEditDialog(self.todo_item, self)
        if dialog.exec() == QDialog.Accepted:
            self.todo_item = dialog.get_todo_item()
            self.setup_ui()
            self.update_display()
            self.item_updated.emit(self.todo_item.id)
    
    def delete_item(self):
        """Delete the item"""
        reply = QMessageBox.question(
            self, "Delete Todo", 
            f"Are you sure you want to delete '{self.todo_item.title}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.item_deleted.emit(self.todo_item.id)


class TodoEditDialog(QDialog):
    """Dialog for editing todo items"""
    
    def __init__(self, todo_item: TodoItem = None, parent=None):
        super().__init__(parent)
        self.todo_item = todo_item or TodoItem()
        self.setup_ui()
        self.populate_fields()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Edit Todo Item")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Title
        self.title_edit = QLineEdit()
        form_layout.addRow("Title:", self.title_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_edit)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.addItems([c.value for c in Category])
        form_layout.addRow("Category:", self.category_combo)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([p.value for p in Priority])
        form_layout.addRow("Priority:", self.priority_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems([s.value for s in Status])
        form_layout.addRow("Status:", self.status_combo)
        
        # Due date
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(QDate.currentDate())
        self.due_date_checkbox = QCheckBox("Set due date")
        due_layout = QHBoxLayout()
        due_layout.addWidget(self.due_date_checkbox)
        due_layout.addWidget(self.due_date_edit)
        form_layout.addRow("Due Date:", due_layout)
        
        # Estimated hours
        self.estimated_hours_spin = QDoubleSpinBox()
        self.estimated_hours_spin.setRange(0, 999)
        self.estimated_hours_spin.setSuffix(" hours")
        form_layout.addRow("Estimated Hours:", self.estimated_hours_spin)
        
        # Actual hours
        self.actual_hours_spin = QDoubleSpinBox()
        self.actual_hours_spin.setRange(0, 999)
        self.actual_hours_spin.setSuffix(" hours")
        form_layout.addRow("Actual Hours:", self.actual_hours_spin)
        
        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma-separated tags")
        form_layout.addRow("Tags:", self.tags_edit)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect due date checkbox
        self.due_date_checkbox.toggled.connect(self.due_date_edit.setEnabled)
        self.due_date_edit.setEnabled(False)
    
    def populate_fields(self):
        """Populate fields with todo item data"""
        self.title_edit.setText(self.todo_item.title)
        self.description_edit.setPlainText(self.todo_item.description)
        self.category_combo.setCurrentText(self.todo_item.category)
        self.priority_combo.setCurrentText(self.todo_item.priority)
        self.status_combo.setCurrentText(self.todo_item.status)
        
        if self.todo_item.due_date:
            self.due_date_checkbox.setChecked(True)
            self.due_date_edit.setEnabled(True)
            self.due_date_edit.setDate(QDate.fromString(str(self.todo_item.due_date), "yyyy-MM-dd"))
        
        self.estimated_hours_spin.setValue(self.todo_item.estimated_hours)
        self.actual_hours_spin.setValue(self.todo_item.actual_hours)
        self.tags_edit.setText(self.todo_item.tags)
        self.notes_edit.setPlainText(self.todo_item.notes)
    
    def get_todo_item(self) -> TodoItem:
        """Get the todo item from form data"""
        self.todo_item.title = self.title_edit.text().strip()
        self.todo_item.description = self.description_edit.toPlainText().strip()
        self.todo_item.category = self.category_combo.currentText()
        self.todo_item.priority = self.priority_combo.currentText()
        self.todo_item.status = self.status_combo.currentText()
        
        if self.due_date_checkbox.isChecked():
            self.todo_item.due_date = self.due_date_edit.date().toPython()
        else:
            self.todo_item.due_date = None
        
        self.todo_item.estimated_hours = self.estimated_hours_spin.value()
        self.todo_item.actual_hours = self.actual_hours_spin.value()
        self.todo_item.tags = self.tags_edit.text().strip()
        self.todo_item.notes = self.notes_edit.toPlainText().strip()
        self.todo_item.updated_at = datetime.now()
        
        return self.todo_item


class CustomTodoCalendar(QCalendarWidget):
    """Custom calendar widget with todo highlighting using paintCell"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_data = {}  # date_string -> task_info
        self.current_theme = 'dark'

    def set_task_data(self, task_dates, theme='dark'):
        """Set task data for calendar highlighting"""
        self.task_data = {}
        self.current_theme = theme

        # Convert task dates to a dictionary for quick lookup
        for task_date, tasks in task_dates.items():
            date_str = task_date.strftime('%Y-%m-%d')

            # Count task statuses
            completed_count = sum(1 for task in tasks if task['status'] == 'Completed')
            total_count = len(tasks)

            self.task_data[date_str] = {
                'completed': completed_count,
                'total': total_count,
                'tasks': tasks
            }

        # Force repaint
        self.updateCells()

    def paintCell(self, painter, rect, date):
        """Custom paint method to highlight cells based on task status"""
        # Call parent paint first
        super().paintCell(painter, rect, date)

        # Get date string in YYYY-MM-DD format
        date_str = date.toString('yyyy-MM-dd')
        task_info = self.task_data.get(date_str)

        if task_info:
            completed = task_info['completed']
            total = task_info['total']

            # Determine color based on task completion status
            color = None

            if completed == total:
                # All tasks completed - success color (bright green)
                color = get_calendar_color_with_alpha('success', 200, self.current_theme)
            elif completed > 0:
                # Some tasks completed - warning color (bright orange)
                color = get_calendar_color_with_alpha('warning', 200, self.current_theme)
            else:
                # No tasks completed - error color (bright red)
                color = get_calendar_color_with_alpha('error', 200, self.current_theme)

            if color:
                # Draw colored overlay with proper margins to avoid overlap
                margin = 2
                adjusted_rect = rect.adjusted(margin, margin, -margin, -margin)
                painter.fillRect(adjusted_rect, color)

                # Show task count and completion info in bottom part of cell
                if total > 1:  # Only show count if more than 1 task
                    painter.setPen(QColor(255, 255, 255))  # White text for better visibility on colored backgrounds
                    # Set smaller font for the additional info
                    font = painter.font()
                    font.setPointSize(8)
                    painter.setFont(font)
                    # Position text in bottom part of cell to avoid overlapping with date number
                    text_rect = adjusted_rect.adjusted(0, adjusted_rect.height() // 2, 0, 0)
                    painter.drawText(text_rect, Qt.AlignCenter, f"{completed}/{total}")
                elif total == 1:
                    # For single tasks, show completion status
                    painter.setPen(QColor(255, 255, 255))
                    font = painter.font()
                    font.setPointSize(10)
                    painter.setFont(font)
                    text_rect = adjusted_rect.adjusted(0, adjusted_rect.height() // 2, 0, 0)
                    status_text = "✓" if completed == 1 else "○"
                    painter.drawText(text_rect, Qt.AlignCenter, status_text)


class TodoCalendarWidget(QWidget):
    """Calendar view widget for displaying todos by date"""

    date_selected = Signal(QDate)
    task_clicked = Signal(int)  # Emits todo ID

    def __init__(self, todo_model, parent=None):
        super().__init__(parent)
        self.todo_model = todo_model
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.setup_ui()
        self.refresh_calendar()

    def setup_ui(self):
        """Setup the calendar UI"""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("📅 Calendar View")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Month navigation
        self.prev_month_btn = QPushButton("◀ Previous")
        self.prev_month_btn.clicked.connect(self.previous_month)
        header_layout.addWidget(self.prev_month_btn)

        self.current_month_label = QLabel()
        self.current_month_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.current_month_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.current_month_label)

        self.next_month_btn = QPushButton("Next ▶")
        self.next_month_btn.clicked.connect(self.next_month)
        header_layout.addWidget(self.next_month_btn)

        layout.addLayout(header_layout)

        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)

        # Calendar widget - use custom calendar for better highlighting
        self.calendar = CustomTodoCalendar()
        self.calendar.setMinimumWidth(400)
        self.calendar.clicked.connect(self.on_date_clicked)
        self.calendar.currentPageChanged.connect(self.on_month_changed)
        splitter.addWidget(self.calendar)

        # Task list for selected date
        task_panel = QWidget()
        task_layout = QVBoxLayout(task_panel)

        self.selected_date_label = QLabel("Select a date to view tasks")
        self.selected_date_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.selected_date_label.setAlignment(Qt.AlignCenter)
        task_layout.addWidget(self.selected_date_label)

        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.on_task_clicked)
        task_layout.addWidget(self.task_list)

        # Add task button for selected date
        self.add_task_btn = QPushButton("➕ Add Task for Selected Date")
        self.add_task_btn.clicked.connect(self.add_task_for_date)
        self.add_task_btn.setEnabled(False)
        task_layout.addWidget(self.add_task_btn)

        splitter.addWidget(task_panel)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter)

        # Initialize current month label
        self.update_month_label()

    def refresh_calendar(self):
        """Refresh calendar with task indicators using custom calendar widget"""
        try:
            # Get all todos
            df = self.todo_model.get_all_todos()

            # Group tasks by date
            task_dates = {}
            for _, row in df.iterrows():
                if pd.notna(row['due_date']):
                    try:
                        # Handle different date types
                        if isinstance(row['due_date'], str):
                            due_date = datetime.strptime(row['due_date'], '%Y-%m-%d').date()
                        elif hasattr(row['due_date'], 'date'):
                            # pandas Timestamp
                            due_date = row['due_date'].date()
                        elif isinstance(row['due_date'], date):
                            due_date = row['due_date']
                        elif isinstance(row['due_date'], datetime):
                            due_date = row['due_date'].date()
                        else:
                            continue

                        if due_date not in task_dates:
                            task_dates[due_date] = []
                        task_dates[due_date].append(row)
                    except (ValueError, TypeError, AttributeError) as e:
                        self.logger.debug(f"Error parsing date for task {row.get('title', 'Unknown')}: {e}")
                        continue

            # Get current theme
            current_theme = get_current_theme()

            # Set task data on the custom calendar widget
            self.calendar.set_task_data(task_dates, current_theme)

            print(f"🎨 DEBUG: Todo calendar highlighting with theme '{current_theme}'")
            print(f"🎨 DEBUG: Highlighted {len(task_dates)} dates with tasks")

        except Exception as e:
            self.logger.error(f"Error refreshing calendar: {e}")
            print(f"❌ ERROR: Todo calendar highlighting failed: {e}")

    def on_date_clicked(self, date):
        """Handle date selection"""
        self.selected_date = date.toPython()
        self.selected_date_label.setText(f"Tasks for {self.selected_date.strftime('%B %d, %Y')}")
        self.add_task_btn.setEnabled(True)
        self.load_tasks_for_date(self.selected_date)
        self.date_selected.emit(date)

    def load_tasks_for_date(self, date):
        """Load tasks for the selected date"""
        self.task_list.clear()

        try:
            df = self.todo_model.get_all_todos()

            # Filter tasks for the selected date
            date_tasks = []
            for _, row in df.iterrows():
                if pd.notna(row['due_date']):
                    try:
                        # Handle different date types
                        if isinstance(row['due_date'], str):
                            due_date = datetime.strptime(row['due_date'], '%Y-%m-%d').date()
                        elif hasattr(row['due_date'], 'date'):
                            # pandas Timestamp
                            due_date = row['due_date'].date()
                        elif isinstance(row['due_date'], date):
                            due_date = row['due_date']
                        elif isinstance(row['due_date'], datetime):
                            due_date = row['due_date'].date()
                        else:
                            continue

                        if due_date == date:
                            date_tasks.append(row)
                    except (ValueError, TypeError, AttributeError) as e:
                        self.logger.debug(f"Error parsing date for task {row.get('title', 'Unknown')}: {e}")
                        continue

            # Add tasks to list
            for task in date_tasks:
                item = QListWidgetItem()

                # Create task display text
                status_icon = "✅" if task['status'] == 'Completed' else "⏳" if task['status'] == 'In Progress' else "📋"
                priority_icon = "🔴" if task['priority'] == 'High' else "🟡" if task['priority'] == 'Medium' else "🟢"

                text = f"{status_icon} {priority_icon} {task['title']}"
                if pd.notna(task['description']) and task['description']:
                    text += f"\n   {task['description'][:50]}{'...' if len(str(task['description'])) > 50 else ''}"

                item.setText(text)
                item.setData(Qt.UserRole, task['id'])  # Store task ID

                # Set color based on status
                if task['status'] == 'Completed':
                    item.setBackground(QBrush(QColor(45, 90, 45)))    # Dark green
                    item.setForeground(QBrush(QColor(144, 238, 144))) # Light green text
                elif task['status'] == 'In Progress':
                    item.setBackground(QBrush(QColor(90, 90, 45)))    # Dark yellow
                    item.setForeground(QBrush(QColor(255, 255, 224))) # Light yellow text

                self.task_list.addItem(item)

        except Exception as e:
            self.logger.error(f"Error loading tasks for date: {e}")

    def on_task_clicked(self, item):
        """Handle task item click"""
        task_id = item.data(Qt.UserRole)
        if task_id:
            self.task_clicked.emit(task_id)

    def add_task_for_date(self):
        """Add a new task for the selected date"""
        if hasattr(self, 'selected_date'):
            # Emit signal to parent to handle task creation
            self.date_selected.emit(QDate(self.selected_date))

    def previous_month(self):
        """Navigate to previous month"""
        current_date = self.calendar.selectedDate()
        new_date = current_date.addMonths(-1)
        self.calendar.setSelectedDate(new_date)
        self.calendar.showMonth(new_date.year(), new_date.month())

    def next_month(self):
        """Navigate to next month"""
        current_date = self.calendar.selectedDate()
        new_date = current_date.addMonths(1)
        self.calendar.setSelectedDate(new_date)
        self.calendar.showMonth(new_date.year(), new_date.month())

    def on_month_changed(self, year, month):
        """Handle month change"""
        self.update_month_label()
        self.refresh_calendar()

    def update_month_label(self):
        """Update the current month label"""
        current_date = self.calendar.selectedDate()
        month_year = current_date.toString("MMMM yyyy")
        self.current_month_label.setText(month_year)

    def apply_theme(self, theme_name: str = 'dark'):
        """Apply theme to todo calendar widget"""
        try:
            print(f"🎨 DEBUG: TodoCalendarWidget.apply_theme called with theme: {theme_name}")

            # Refresh calendar highlighting with new theme
            self.refresh_calendar()

            print(f"✅ SUCCESS: Applied theme '{theme_name}' to TodoCalendarWidget")

        except Exception as e:
            print(f"❌ ERROR: Failed to apply theme to TodoCalendarWidget: {e}")


class TodoHistoryWidget(QWidget):
    """Task history widget with comprehensive filtering"""

    task_selected = Signal(int)  # Emits todo ID

    def __init__(self, todo_model, parent=None):
        super().__init__(parent)
        self.todo_model = todo_model
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.setup_ui()
        self.refresh_history()

    def setup_ui(self):
        """Setup the history UI"""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("📊 Task History")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_history)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Filter panel
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.StyledPanel)
        filter_layout = QGridLayout(filter_frame)

        # Date filters
        filter_layout.addWidget(QLabel("Date Filter:"), 0, 0)
        self.date_filter = QComboBox()
        self.date_filter.addItems([
            "All Time", "Today", "This Week", "This Month",
            "Last Week", "Last Month", "This Year", "Last Year",
            "Last 30 Days", "Last 90 Days", "Last 6 Months", "Custom Range"
        ])
        self.date_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.date_filter, 0, 1)

        # Custom date range (initially hidden)
        filter_layout.addWidget(QLabel("From:"), 0, 2)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setVisible(False)
        self.start_date.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.start_date, 0, 3)

        filter_layout.addWidget(QLabel("To:"), 0, 4)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setVisible(False)
        self.end_date.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.end_date, 0, 5)

        # Status filter
        filter_layout.addWidget(QLabel("Status:"), 1, 0)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Completed", "In Progress", "Cancelled", "Pending"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter, 1, 1)

        # Priority filter
        filter_layout.addWidget(QLabel("Priority:"), 1, 2)
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All", "High", "Medium", "Low"])
        self.priority_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.priority_filter, 1, 3)

        # Category filter
        filter_layout.addWidget(QLabel("Category:"), 1, 4)
        self.category_filter = QComboBox()
        self.category_filter.addItem("All")
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_filter, 1, 5)

        layout.addWidget(filter_frame)

        # Statistics summary
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                margin: 5px 0;
            }
        """)
        layout.addWidget(self.stats_label)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setSortingEnabled(True)
        self.history_table.itemDoubleClicked.connect(self.on_task_double_clicked)

        # Set up table columns
        columns = ["Title", "Category", "Priority", "Status", "Due Date", "Created", "Completed", "Duration"]
        self.history_table.setColumnCount(len(columns))
        self.history_table.setHorizontalHeaderLabels(columns)

        # Configure column widths
        header = self.history_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 200)  # Title
        header.resizeSection(1, 100)  # Category
        header.resizeSection(2, 80)   # Priority
        header.resizeSection(3, 100)  # Status
        header.resizeSection(4, 100)  # Due Date
        header.resizeSection(5, 100)  # Created
        header.resizeSection(6, 100)  # Completed

        layout.addWidget(self.history_table)

        # Connect date filter change to show/hide custom date inputs
        self.date_filter.currentTextChanged.connect(self.on_date_filter_changed)

    def on_date_filter_changed(self, filter_text):
        """Handle date filter change to show/hide custom date inputs"""
        show_custom = filter_text == "Custom Range"
        self.start_date.setVisible(show_custom)
        self.end_date.setVisible(show_custom)

        # Update labels visibility
        for i in range(self.layout().itemAt(2).widget().layout().count()):
            item = self.layout().itemAt(2).widget().layout().itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QLabel):
                    if widget.text() in ["From:", "To:"]:
                        widget.setVisible(show_custom)

    def refresh_history(self):
        """Refresh the history data"""
        try:
            # Update category filter with current categories
            self.update_category_filter()

            # Apply current filters
            self.apply_filters()

        except Exception as e:
            self.logger.error(f"Error refreshing history: {e}")

    def update_category_filter(self):
        """Update category filter with available categories"""
        try:
            df = self.todo_model.get_all_todos()
            categories = df['category'].dropna().unique().tolist()

            current_selection = self.category_filter.currentText()
            self.category_filter.clear()
            self.category_filter.addItem("All")
            self.category_filter.addItems(sorted(categories))

            # Restore selection if it still exists
            index = self.category_filter.findText(current_selection)
            if index >= 0:
                self.category_filter.setCurrentIndex(index)

        except Exception as e:
            self.logger.error(f"Error updating category filter: {e}")

    def apply_filters(self):
        """Apply current filters to the history table"""
        try:
            # Show loading indicator
            self.history_table.setRowCount(0)
            self.history_table.setSortingEnabled(False)

            # Get all todos
            df = self.todo_model.get_all_todos()

            if df.empty:
                self.update_statistics(df)
                return

            # Apply date filter
            df = self.apply_date_filter(df)

            # Apply status filter
            status_filter = self.status_filter.currentText()
            if status_filter != "All":
                df = df[df['status'] == status_filter]

            # Apply priority filter
            priority_filter = self.priority_filter.currentText()
            if priority_filter != "All":
                df = df[df['priority'] == priority_filter]

            # Apply category filter
            category_filter = self.category_filter.currentText()
            if category_filter != "All":
                df = df[df['category'] == category_filter]

            # Populate table
            self.populate_table(df)

            # Update statistics
            self.update_statistics(df)

            # Re-enable sorting
            self.history_table.setSortingEnabled(True)

        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")

    def apply_date_filter(self, df):
        """Apply date filter to dataframe"""
        date_filter = self.date_filter.currentText()
        today = date.today()

        if date_filter == "All Time":
            return df
        elif date_filter == "Today":
            start_date = today
            end_date = today
        elif date_filter == "This Week":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif date_filter == "This Month":
            start_date = today.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        elif date_filter == "Last Week":
            end_date = today - timedelta(days=today.weekday() + 1)
            start_date = end_date - timedelta(days=6)
        elif date_filter == "Last Month":
            end_date = today.replace(day=1) - timedelta(days=1)
            start_date = end_date.replace(day=1)
        elif date_filter == "This Year":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        elif date_filter == "Last Year":
            start_date = today.replace(year=today.year-1, month=1, day=1)
            end_date = today.replace(year=today.year-1, month=12, day=31)
        elif date_filter == "Last 30 Days":
            start_date = today - timedelta(days=30)
            end_date = today
        elif date_filter == "Last 90 Days":
            start_date = today - timedelta(days=90)
            end_date = today
        elif date_filter == "Last 6 Months":
            start_date = today - timedelta(days=180)
            end_date = today
        elif date_filter == "Custom Range":
            start_date = self.start_date.date().toPython()
            end_date = self.end_date.date().toPython()
        else:
            return df

        # Filter by due date, created date, or completed date
        try:
            # Import safe datetime utilities to prevent comparison errors
            from core.datetime_utils import safe_datetime_comparison

            # Convert dates to datetime for comparison
            due_dates = pd.to_datetime(df['due_date'], errors='coerce')
            created_dates = pd.to_datetime(df['created_at'], errors='coerce')
            completed_dates = pd.to_datetime(df['completed_at'], errors='coerce')

            # Create boolean masks for each date column using safe comparison
            # Use .dt.date for compatibility, but also provide safe fallback
            try:
                due_mask = (due_dates.dt.date >= start_date) & (due_dates.dt.date <= end_date)
                created_mask = (created_dates.dt.date >= start_date) & (created_dates.dt.date <= end_date)
                completed_mask = (completed_dates.dt.date >= start_date) & (completed_dates.dt.date <= end_date)
            except (TypeError, ValueError) as date_error:
                # Fallback to safe comparison if .dt.date fails
                self.logger.warning(f"Date comparison error, using safe fallback: {date_error}")
                due_mask = safe_datetime_comparison(due_dates, start_date, '>=') & safe_datetime_comparison(due_dates, end_date, '<=')
                created_mask = safe_datetime_comparison(created_dates, start_date, '>=') & safe_datetime_comparison(created_dates, end_date, '<=')
                completed_mask = safe_datetime_comparison(completed_dates, start_date, '>=') & safe_datetime_comparison(completed_dates, end_date, '<=')

            # Combine masks with OR logic (task matches if any date falls in range)
            combined_mask = due_mask | created_mask | completed_mask

            # Handle NaN values
            combined_mask = combined_mask.fillna(False)

            filtered_df = df[combined_mask]
        except Exception as e:
            self.logger.error(f"Error filtering by date: {e}")
            filtered_df = df  # Return all data if filtering fails

        return filtered_df

    def populate_table(self, df):
        """Populate the history table with filtered data"""
        self.history_table.setRowCount(len(df))

        for row_idx, (_, row) in enumerate(df.iterrows()):
            # Title
            self.history_table.setItem(row_idx, 0, QTableWidgetItem(str(row['title'])))

            # Category
            category = str(row['category']) if pd.notna(row['category']) else ""
            self.history_table.setItem(row_idx, 1, QTableWidgetItem(category))

            # Priority
            self.history_table.setItem(row_idx, 2, QTableWidgetItem(str(row['priority'])))

            # Status
            status_item = QTableWidgetItem(str(row['status']))
            if row['status'] == 'Completed':
                status_item.setBackground(QBrush(QColor(144, 238, 144)))
            elif row['status'] == 'In Progress':
                status_item.setBackground(QBrush(QColor(255, 255, 224)))
            elif row['status'] == 'Cancelled':
                status_item.setBackground(QBrush(QColor(255, 182, 193)))
            self.history_table.setItem(row_idx, 3, status_item)

            # Due Date
            due_date = ""
            if pd.notna(row['due_date']):
                try:
                    if isinstance(row['due_date'], str):
                        due_date = datetime.strptime(row['due_date'], '%Y-%m-%d').strftime('%Y-%m-%d')
                    else:
                        due_date = row['due_date'].strftime('%Y-%m-%d')
                except:
                    due_date = str(row['due_date'])
            self.history_table.setItem(row_idx, 4, QTableWidgetItem(due_date))

            # Created Date
            created_date = ""
            if pd.notna(row['created_at']):
                try:
                    if isinstance(row['created_at'], str):
                        created_date = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                    else:
                        created_date = row['created_at'].strftime('%Y-%m-%d')
                except:
                    created_date = str(row['created_at'])
            self.history_table.setItem(row_idx, 5, QTableWidgetItem(created_date))

            # Completed Date
            completed_date = ""
            if pd.notna(row['completed_at']):
                try:
                    if isinstance(row['completed_at'], str):
                        completed_date = datetime.strptime(row['completed_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                    else:
                        completed_date = row['completed_at'].strftime('%Y-%m-%d')
                except:
                    completed_date = str(row['completed_at'])
            self.history_table.setItem(row_idx, 6, QTableWidgetItem(completed_date))

            # Duration (if completed)
            duration = ""
            if pd.notna(row['completed_at']) and pd.notna(row['created_at']):
                try:
                    if isinstance(row['completed_at'], str):
                        completed = datetime.strptime(row['completed_at'], '%Y-%m-%d %H:%M:%S')
                    else:
                        completed = row['completed_at']

                    if isinstance(row['created_at'], str):
                        created = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                    else:
                        created = row['created_at']

                    duration_delta = completed - created
                    duration = f"{duration_delta.days} days"
                except:
                    duration = ""
            self.history_table.setItem(row_idx, 7, QTableWidgetItem(duration))

            # Store task ID in first column for reference
            self.history_table.item(row_idx, 0).setData(Qt.UserRole, row['id'])

    def update_statistics(self, df):
        """Update statistics summary"""
        if df.empty:
            self.stats_label.setText("No tasks found matching the current filters.")
            return

        total_tasks = len(df)
        completed_tasks = len(df[df['status'] == 'Completed'])
        in_progress_tasks = len(df[df['status'] == 'In Progress'])
        pending_tasks = len(df[df['status'] == 'Pending'])
        cancelled_tasks = len(df[df['status'] == 'Cancelled'])

        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        stats_text = f"""
        📊 <b>Statistics:</b> Total: {total_tasks} |
        ✅ Completed: {completed_tasks} ({completion_rate:.1f}%) |
        ⏳ In Progress: {in_progress_tasks} |
        📋 Pending: {pending_tasks} |
        ❌ Cancelled: {cancelled_tasks}
        """

        self.stats_label.setText(stats_text)

    def on_task_double_clicked(self, item):
        """Handle task double-click"""
        if item.column() == 0:  # Title column
            task_id = item.data(Qt.UserRole)
            if task_id:
                self.task_selected.emit(task_id)


class TodoTrackerWidget(QWidget):
    """Main todo tracker widget"""

    def __init__(self, data_manager, config, parent=None):
        super().__init__(parent)

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("="*50)
        self.logger.info("INITIALIZING TODO TRACKER WIDGET")
        self.logger.info("="*50)

        try:
            self.data_manager = data_manager
            self.config = config
            self.todo_model = TodoDataModel(data_manager)

            self.setup_ui()
            self.setup_connections()
            self.refresh_data()

            self.logger.info("✅ TodoTrackerWidget initialization SUCCESSFUL")

        except Exception as e:
            self.logger.error(f"❌ CRITICAL ERROR in TodoTrackerWidget.__init__: {e}")
            raise

    def setup_ui(self):
        """Setup the main UI with multi-tab structure"""
        layout = QVBoxLayout(self)

        # Header with title and global controls
        header_layout = QHBoxLayout()

        title_label = QLabel("📝 To-Do List Manager")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)

        # Google Tasks status indicator
        status = self.todo_model.get_google_tasks_status()
        self.status_label = QLabel(status.get('status_message', 'Unknown status'))
        self.status_label.setObjectName('google_tasks_status')
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;

                border: 1px solid #ddd;
            }
        """)
        header_layout.addWidget(self.status_label)

        header_layout.addStretch()

        # Google Tasks sync buttons
        if self.todo_model.is_google_tasks_available():
            sync_from_btn = QPushButton("⬇️ Sync from Google")
            sync_from_btn.setToolTip("Import tasks from Google Tasks")
            sync_from_btn.clicked.connect(self.sync_from_google_tasks)
            header_layout.addWidget(sync_from_btn)

            sync_to_btn = QPushButton("⬆️ Sync to Google")
            sync_to_btn.setToolTip("Export tasks to Google Tasks")
            sync_to_btn.clicked.connect(self.sync_to_google_tasks)
            header_layout.addWidget(sync_to_btn)

            full_sync_btn = QPushButton("🔄 Full Sync")
            full_sync_btn.setToolTip("Bidirectional sync with Google Tasks")
            full_sync_btn.clicked.connect(self.full_sync_google_tasks)
            header_layout.addWidget(full_sync_btn)











            # Calendar diagnostic button removed - no longer needed after calendar sync removal
        else:
            # Show authentication button if Google Tasks is not available
            if status.get('libraries_available', False):
                auth_btn = QPushButton("🔗 Connect Google Tasks")
                auth_btn.setToolTip("Authenticate with Google Tasks to enable synchronization")
                auth_btn.clicked.connect(self.authenticate_google_tasks)
                header_layout.addWidget(auth_btn)
            else:
                info_btn = QPushButton("ℹ️ Google Tasks Info")
                info_btn.setToolTip("Information about Google Tasks integration")
                info_btn.clicked.connect(self.show_google_tasks_info)
                header_layout.addWidget(info_btn)

        # Add new todo button
        add_btn = QPushButton("➕ Add New Todo")
        add_btn.clicked.connect(self.add_new_todo)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Create main tab widget
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setObjectName("todoMainTabs")

        # Create tabs
        self.create_calendar_tab()
        self.create_task_management_tab()
        self.create_history_tab()

        layout.addWidget(self.main_tab_widget)

    def create_calendar_tab(self):
        """Create the calendar view tab"""
        self.calendar_widget = TodoCalendarWidget(self.todo_model)
        self.calendar_widget.date_selected.connect(self.on_calendar_date_selected)
        self.calendar_widget.task_clicked.connect(self.on_calendar_task_clicked)
        self.main_tab_widget.addTab(self.calendar_widget, "📅 Calendar View")

    def create_task_management_tab(self):
        """Create the enhanced task management tab with sub-tabs"""
        task_management_widget = QWidget()
        task_layout = QVBoxLayout(task_management_widget)

        # Statistics panel for task management
        self.stats_widget = self.create_stats_widget()
        task_layout.addWidget(self.stats_widget)

        # Create sub-tab widget for task management
        self.task_sub_tabs = QTabWidget()

        # Create sub-tabs
        self.create_all_tasks_tab()
        self.create_today_tasks_tab()
        self.create_week_tasks_tab()
        self.create_month_tasks_tab()

        task_layout.addWidget(self.task_sub_tabs)

        self.main_tab_widget.addTab(task_management_widget, "📋 Task Management")

    def create_all_tasks_tab(self):
        """Create the all tasks sub-tab (original functionality)"""
        all_tasks_widget = QWidget()
        layout = QVBoxLayout(all_tasks_widget)

        # Filter controls
        filter_layout = QHBoxLayout()

        # Status filter
        filter_layout.addWidget(QLabel("Filter by Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "In Progress", "Completed"])
        # Set default to "All" to show all tasks
        self.status_filter.setCurrentText("All")
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter)

        # Priority filter
        filter_layout.addWidget(QLabel("Priority:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All"] + [p.value for p in Priority])
        self.priority_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.priority_filter)

        # Category filter
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All"] + [c.value for c in Category])
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_filter)

        filter_layout.addStretch()

        # Show overdue checkbox
        self.show_overdue_only = QCheckBox("Show Overdue Only")
        self.show_overdue_only.toggled.connect(self.apply_filters)
        filter_layout.addWidget(self.show_overdue_only)

        # Show completed tasks checkbox (for calendar events visibility)
        self.show_completed = QCheckBox("Show Completed Tasks")
        self.show_completed.setChecked(True)  # Default to showing completed tasks
        self.show_completed.toggled.connect(self.apply_filters)
        filter_layout.addWidget(self.show_completed)

        layout.addLayout(filter_layout)

        # Todo list area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.todo_container = QWidget()
        self.todo_layout = QVBoxLayout(self.todo_container)
        self.todo_layout.addStretch()

        self.scroll_area.setWidget(self.todo_container)
        layout.addWidget(self.scroll_area)

        self.task_sub_tabs.addTab(all_tasks_widget, "All Tasks")

    def create_today_tasks_tab(self):
        """Create the today's tasks sub-tab"""
        today_widget = QWidget()
        layout = QVBoxLayout(today_widget)

        # Header
        header_layout = QHBoxLayout()
        today_label = QLabel(f"📅 Today's Tasks - {date.today().strftime('%B %d, %Y')}")
        today_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(today_label)

        header_layout.addStretch()

        # Quick add for today
        quick_add_btn = QPushButton("➕ Quick Add for Today")
        quick_add_btn.clicked.connect(self.quick_add_today)
        header_layout.addWidget(quick_add_btn)

        layout.addLayout(header_layout)

        # Today's tasks list
        self.today_scroll_area = QScrollArea()
        self.today_scroll_area.setWidgetResizable(True)

        self.today_container = QWidget()
        self.today_layout = QVBoxLayout(self.today_container)
        self.today_layout.addStretch()

        self.today_scroll_area.setWidget(self.today_container)
        layout.addWidget(self.today_scroll_area)

        self.task_sub_tabs.addTab(today_widget, "Today")

    def create_week_tasks_tab(self):
        """Create the this week's tasks sub-tab"""
        week_widget = QWidget()
        layout = QVBoxLayout(week_widget)

        # Header
        header_layout = QHBoxLayout()

        # Calculate week range
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        week_label = QLabel(f"📅 This Week - {start_of_week.strftime('%b %d')} to {end_of_week.strftime('%b %d, %Y')}")
        week_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(week_label)

        header_layout.addStretch()

        # Week navigation
        prev_week_btn = QPushButton("◀ Previous Week")
        prev_week_btn.clicked.connect(self.previous_week)
        header_layout.addWidget(prev_week_btn)

        next_week_btn = QPushButton("Next Week ▶")
        next_week_btn.clicked.connect(self.next_week)
        header_layout.addWidget(next_week_btn)

        layout.addLayout(header_layout)

        # Week's tasks list
        self.week_scroll_area = QScrollArea()
        self.week_scroll_area.setWidgetResizable(True)

        self.week_container = QWidget()
        self.week_layout = QVBoxLayout(self.week_container)
        self.week_layout.addStretch()

        self.week_scroll_area.setWidget(self.week_container)
        layout.addWidget(self.week_scroll_area)

        self.task_sub_tabs.addTab(week_widget, "This Week")

    def create_month_tasks_tab(self):
        """Create the this month's tasks sub-tab"""
        month_widget = QWidget()
        layout = QVBoxLayout(month_widget)

        # Header
        header_layout = QHBoxLayout()

        today = date.today()
        month_label = QLabel(f"📅 This Month - {today.strftime('%B %Y')}")
        month_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(month_label)

        header_layout.addStretch()

        # Month navigation
        prev_month_btn = QPushButton("◀ Previous Month")
        prev_month_btn.clicked.connect(self.previous_month_tasks)
        header_layout.addWidget(prev_month_btn)

        next_month_btn = QPushButton("Next Month ▶")
        next_month_btn.clicked.connect(self.next_month_tasks)
        header_layout.addWidget(next_month_btn)

        layout.addLayout(header_layout)

        # Month's tasks list
        self.month_scroll_area = QScrollArea()
        self.month_scroll_area.setWidgetResizable(True)

        self.month_container = QWidget()
        self.month_layout = QVBoxLayout(self.month_container)
        self.month_layout.addStretch()

        self.month_scroll_area.setWidget(self.month_container)
        layout.addWidget(self.month_scroll_area)

        self.task_sub_tabs.addTab(month_widget, "This Month")

    def create_history_tab(self):
        """Create the task history tab"""
        self.history_widget = TodoHistoryWidget(self.todo_model)
        self.history_widget.task_selected.connect(self.on_history_task_selected)
        self.main_tab_widget.addTab(self.history_widget, "📊 Task History")

    def create_stats_widget(self) -> QWidget:
        """Create statistics widget"""
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Box)
        stats_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;

            }
        """)

        layout = QHBoxLayout(stats_frame)

        # Total todos
        self.total_label = QLabel("Total: 0")
        self.total_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.total_label)

        # Completed
        self.completed_label = QLabel("Completed: 0")
        self.completed_label.setStyleSheet("color: #28a745;")
        layout.addWidget(self.completed_label)

        # Pending
        self.pending_label = QLabel("Pending: 0")
        self.pending_label.setStyleSheet("color: #ffc107;")
        layout.addWidget(self.pending_label)

        # In Progress
        self.in_progress_label = QLabel("In Progress: 0")
        self.in_progress_label.setStyleSheet("color: #17a2b8;")
        layout.addWidget(self.in_progress_label)

        # Overdue
        self.overdue_label = QLabel("Overdue: 0")
        self.overdue_label.setStyleSheet("color: #dc3545;")
        layout.addWidget(self.overdue_label)

        # Completion rate
        self.completion_rate_label = QLabel("Completion Rate: 0%")
        layout.addWidget(self.completion_rate_label)

        layout.addStretch()

        return stats_frame

    def setup_connections(self):
        """Setup signal connections"""
        pass

    def refresh_data(self):
        """Refresh todo data and update all displays"""
        try:
            self.logger.debug("🔄 Starting UI data refresh...")

            # Get current task count for logging
            current_tasks = self.todo_model.get_all_todos()
            task_count = len(current_tasks)
            self.logger.debug(f"📋 Refreshing UI with {task_count} total tasks")

            # Refresh all task views
            self.refresh_all_tasks()
            self.refresh_today_tasks()
            self.refresh_week_tasks()
            self.refresh_month_tasks()

            # Refresh calendar view
            if hasattr(self, 'calendar_widget'):
                self.calendar_widget.refresh_calendar()

            # Refresh history view
            if hasattr(self, 'history_widget'):
                self.history_widget.refresh_history()

            # Update statistics
            self.update_statistics()

            # Update Google Tasks status if status label exists
            self.update_google_tasks_status()

            # Update historical data status
            self.update_historical_data_status()

            self.logger.debug("✅ UI data refresh completed")

        except Exception as e:
            self.logger.error(f"Error refreshing todo data: {e}")

    def refresh_all_tasks(self):
        """Refresh the all tasks view"""
        try:
            # Clear existing todos
            for i in reversed(range(self.todo_layout.count() - 1)):  # -1 to keep the stretch
                child = self.todo_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            # Get todos and apply filters
            df = self.todo_model.get_all_todos()
            filtered_df = self.apply_current_filters(df)

            # Count calendar events for debugging
            calendar_events_total = 0
            calendar_events_filtered = 0

            if not df.empty and 'google_task_id' in df.columns:
                calendar_events_total = len(df[
                    df['google_task_id'].notna() &
                    df['google_task_id'].str.startswith('cal_', na=False)
                ])

            if not filtered_df.empty and 'google_task_id' in filtered_df.columns:
                calendar_events_filtered = len(filtered_df[
                    filtered_df['google_task_id'].notna() &
                    filtered_df['google_task_id'].str.startswith('cal_', na=False)
                ])

            self.logger.debug(f"📋 Refreshing all tasks view: {len(df)} total ({calendar_events_total} calendar events), {len(filtered_df)} after filters ({calendar_events_filtered} calendar events)")

            # Create todo widgets
            widget_count = 0
            calendar_widget_count = 0
            for _, row in filtered_df.iterrows():
                todo_item = TodoItem.from_dict(row.to_dict())
                todo_widget = TodoItemWidget(todo_item)
                todo_widget.item_updated.connect(self.on_todo_updated)
                todo_widget.item_deleted.connect(self.on_todo_deleted)

                # Insert before the stretch
                self.todo_layout.insertWidget(self.todo_layout.count() - 1, todo_widget)
                widget_count += 1

                # Count calendar event widgets
                if todo_item.google_task_id and str(todo_item.google_task_id).startswith('cal_'):
                    calendar_widget_count += 1

            self.logger.debug(f"✅ Created {widget_count} task widgets in all tasks view ({calendar_widget_count} calendar event widgets)")

        except Exception as e:
            self.logger.error(f"Error refreshing all tasks: {e}")

    def refresh_today_tasks(self):
        """Refresh today's tasks view"""
        try:
            # Clear existing todos
            for i in reversed(range(self.today_layout.count() - 1)):
                child = self.today_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            # Get today's todos
            df = self.todo_model.get_all_todos()
            today = date.today()

            today_tasks = []
            for _, row in df.iterrows():
                if pd.notna(row['due_date']):
                    try:
                        # Handle different date types
                        if isinstance(row['due_date'], str):
                            due_date = datetime.strptime(row['due_date'], '%Y-%m-%d').date()
                        elif hasattr(row['due_date'], 'date'):
                            # pandas Timestamp
                            due_date = row['due_date'].date()
                        elif isinstance(row['due_date'], date):
                            due_date = row['due_date']
                        elif isinstance(row['due_date'], datetime):
                            due_date = row['due_date'].date()
                        else:
                            continue

                        if due_date == today:
                            today_tasks.append(row)
                    except (ValueError, TypeError, AttributeError) as e:
                        self.logger.debug(f"Error parsing date for task {row.get('title', 'Unknown')}: {e}")
                        continue

            # Create todo widgets for today
            for row in today_tasks:
                todo_item = TodoItem.from_dict(row.to_dict())
                todo_widget = TodoItemWidget(todo_item)
                todo_widget.item_updated.connect(self.on_todo_updated)
                todo_widget.item_deleted.connect(self.on_todo_deleted)
                self.today_layout.insertWidget(self.today_layout.count() - 1, todo_widget)

            self.logger.debug(f"Found {len(today_tasks)} tasks for today")

        except Exception as e:
            self.logger.error(f"Error refreshing today's tasks: {e}")

    def refresh_week_tasks(self):
        """Refresh this week's tasks view"""
        try:
            # Clear existing todos
            for i in reversed(range(self.week_layout.count() - 1)):
                child = self.week_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            # Get this week's todos
            df = self.todo_model.get_all_todos()
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)

            week_tasks = []
            for _, row in df.iterrows():
                if pd.notna(row['due_date']):
                    try:
                        # Handle different date types
                        if isinstance(row['due_date'], str):
                            due_date = datetime.strptime(row['due_date'], '%Y-%m-%d').date()
                        elif hasattr(row['due_date'], 'date'):
                            # pandas Timestamp
                            due_date = row['due_date'].date()
                        elif isinstance(row['due_date'], date):
                            due_date = row['due_date']
                        elif isinstance(row['due_date'], datetime):
                            due_date = row['due_date'].date()
                        else:
                            continue

                        if start_of_week <= due_date <= end_of_week:
                            week_tasks.append(row)
                    except (ValueError, TypeError, AttributeError) as e:
                        self.logger.debug(f"Error parsing date for task {row.get('title', 'Unknown')}: {e}")
                        continue

            # Create todo widgets for this week
            for row in week_tasks:
                todo_item = TodoItem.from_dict(row.to_dict())
                todo_widget = TodoItemWidget(todo_item)
                todo_widget.item_updated.connect(self.on_todo_updated)
                todo_widget.item_deleted.connect(self.on_todo_deleted)
                self.week_layout.insertWidget(self.week_layout.count() - 1, todo_widget)

            self.logger.debug(f"Found {len(week_tasks)} tasks for this week ({start_of_week} to {end_of_week})")

        except Exception as e:
            self.logger.error(f"Error refreshing week's tasks: {e}")

    def refresh_month_tasks(self):
        """Refresh this month's tasks view"""
        try:
            # Clear existing todos
            for i in reversed(range(self.month_layout.count() - 1)):
                child = self.month_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            # Get this month's todos
            df = self.todo_model.get_all_todos()
            today = date.today()
            start_of_month = today.replace(day=1)
            end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            month_tasks = []
            for _, row in df.iterrows():
                if pd.notna(row['due_date']):
                    try:
                        # Handle different date types
                        if isinstance(row['due_date'], str):
                            due_date = datetime.strptime(row['due_date'], '%Y-%m-%d').date()
                        elif hasattr(row['due_date'], 'date'):
                            # pandas Timestamp
                            due_date = row['due_date'].date()
                        elif isinstance(row['due_date'], date):
                            due_date = row['due_date']
                        elif isinstance(row['due_date'], datetime):
                            due_date = row['due_date'].date()
                        else:
                            continue

                        if start_of_month <= due_date <= end_of_month:
                            month_tasks.append(row)
                    except (ValueError, TypeError, AttributeError) as e:
                        self.logger.debug(f"Error parsing date for task {row.get('title', 'Unknown')}: {e}")
                        continue

            # Create todo widgets for this month
            for row in month_tasks:
                todo_item = TodoItem.from_dict(row.to_dict())
                todo_widget = TodoItemWidget(todo_item)
                todo_widget.item_updated.connect(self.on_todo_updated)
                todo_widget.item_deleted.connect(self.on_todo_deleted)
                self.month_layout.insertWidget(self.month_layout.count() - 1, todo_widget)

            self.logger.debug(f"Found {len(month_tasks)} tasks for this month ({start_of_month} to {end_of_month})")

        except Exception as e:
            self.logger.error(f"Error refreshing month's tasks: {e}")

    def update_google_tasks_status(self):
        """Update the Google Tasks status display"""
        try:
            # Update the status label directly
            if hasattr(self, 'status_label'):
                status = self.todo_model.get_google_tasks_status()
                self.status_label.setText(status.get('status_message', 'Unknown status'))
        except Exception as e:
            self.logger.debug(f"Could not update Google Tasks status: {e}")

    def update_historical_data_status(self):
        """Update historical data availability status"""
        try:
            # Check if we have calendar events (historical data)
            df = self.todo_model.get_all_todos()
            if not df.empty and 'google_task_id' in df.columns:
                calendar_events = df[df['google_task_id'].str.startswith('cal_', na=False)]
                calendar_count = len(calendar_events)

                # Count regular tasks (non-calendar)
                regular_tasks = df[~df['google_task_id'].str.startswith('cal_', na=False) | df['google_task_id'].isna()]
                tasks_count = len(regular_tasks)

                # Check date range of data
                years_back = 0
                if 'created_at' in df.columns:
                    df_with_dates = df[df['created_at'].notna()]
                    if not df_with_dates.empty:
                        oldest_date = pd.to_datetime(df_with_dates['created_at']).min()
                        years_back = (datetime.now() - oldest_date).days / 365.25

                # Update status label to include historical data info
                if hasattr(self, 'status_label'):
                    # Get current Google Tasks status
                    status = self.todo_model.get_google_tasks_status()
                    base_status = status.get('status_message', 'Unknown status')

                    # Add historical data info
                    if calendar_count > 0 or tasks_count > 0:
                        historical_info = f" | 📊 Data: {tasks_count} tasks + {calendar_count} calendar events"
                        if years_back > 0:
                            historical_info += f" ({years_back:.1f} years)"
                        full_status = base_status + historical_info
                    else:
                        full_status = base_status

                    self.status_label.setText(full_status)

                    # Log detailed info
                    self.logger.debug(f"📚 Historical Data Status: {tasks_count} tasks, {calendar_count} calendar events, {years_back:.1f} years back")

        except Exception as e:
            self.logger.debug(f"Could not update historical data status: {e}")

    def update_header_buttons(self):
        """Update header buttons based on Google Tasks availability without recreating entire UI"""
        try:
            # Find the header layout (first layout in the main layout)
            main_layout = self.layout()
            if main_layout and main_layout.count() > 0:
                header_layout_item = main_layout.itemAt(0)
                if header_layout_item and hasattr(header_layout_item, 'layout'):
                    header_layout = header_layout_item.layout()

                    # Remove existing Google Tasks buttons (keep title, status, stretch, and add button)
                    # We need to identify and remove only the Google Tasks sync buttons
                    items_to_remove = []
                    for i in range(header_layout.count()):
                        item = header_layout.itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            if isinstance(widget, QPushButton):
                                button_text = widget.text()
                                # Remove Google Tasks related buttons
                                if any(keyword in button_text for keyword in ['Google', 'Sync', 'Connect', 'Historical', 'Multi-Account', 'Comprehensive']):
                                    if 'Add New Todo' not in button_text:  # Keep the Add New Todo button
                                        items_to_remove.append((i, widget))

                    # Remove the buttons (in reverse order to maintain indices)
                    for i, widget in reversed(items_to_remove):
                        header_layout.removeWidget(widget)
                        widget.setParent(None)

                    # Add appropriate buttons based on current Google Tasks status
                    status = self.todo_model.get_google_tasks_status()

                    # Find the position before the "Add New Todo" button
                    add_button_index = -1
                    for i in range(header_layout.count()):
                        item = header_layout.itemAt(i)
                        if item and item.widget() and isinstance(item.widget(), QPushButton):
                            if 'Add New Todo' in item.widget().text():
                                add_button_index = i
                                break

                    insert_index = add_button_index if add_button_index >= 0 else header_layout.count()

                    if status.get('available', False):
                        # Google Tasks is available - add sync buttons
                        sync_btn = QPushButton("🔄 Sync from Google")
                        sync_btn.setToolTip("Sync todos from Google Tasks")
                        sync_btn.clicked.connect(self.sync_from_google_tasks)
                        header_layout.insertWidget(insert_index, sync_btn)
                        insert_index += 1





                    elif status.get('libraries_available', False):
                        # Libraries available but not authenticated
                        auth_btn = QPushButton("🔗 Connect Google Tasks")
                        auth_btn.setToolTip("Authenticate with Google Tasks to enable synchronization")
                        auth_btn.clicked.connect(self.authenticate_google_tasks)
                        header_layout.insertWidget(insert_index, auth_btn)

                    else:
                        # Libraries not available
                        info_btn = QPushButton("ℹ️ Google Tasks Info")
                        info_btn.setToolTip("Information about Google Tasks integration")
                        info_btn.clicked.connect(self.show_google_tasks_info)
                        header_layout.insertWidget(insert_index, info_btn)

        except Exception as e:
            self.logger.debug(f"Could not update header buttons: {e}")

    def apply_current_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply current filter settings to dataframe"""
        if df.empty:
            return df

        filtered_df = df.copy()

        # Status filter
        status_filter = self.status_filter.currentText()
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]

        # Show completed tasks filter (overrides status filter for completed tasks)
        if not self.show_completed.isChecked():
            # Hide completed tasks unless specifically selected in status filter
            if status_filter != "Completed":
                filtered_df = filtered_df[filtered_df['status'] != Status.COMPLETED.value]

        # Priority filter
        priority_filter = self.priority_filter.currentText()
        if priority_filter != "All":
            filtered_df = filtered_df[filtered_df['priority'] == priority_filter]

        # Category filter
        category_filter = self.category_filter.currentText()
        if category_filter != "All":
            filtered_df = filtered_df[filtered_df['category'] == category_filter]

        # Overdue filter
        if self.show_overdue_only.isChecked():
            today = date.today().strftime('%Y-%m-%d')
            filtered_df = filtered_df[
                (filtered_df['due_date'].notna()) &
                (filtered_df['due_date'] != '') &
                (filtered_df['due_date'] < today) &
                (filtered_df['status'] != Status.COMPLETED.value)
            ]

        return filtered_df

    def apply_filters(self):
        """Apply filters and refresh display"""
        self.refresh_data()

    def update_statistics(self):
        """Update statistics display"""
        stats = self.todo_model.get_statistics()

        self.total_label.setText(f"Total: {stats['total_todos']}")
        self.completed_label.setText(f"Completed: {stats['completed']}")
        self.pending_label.setText(f"Pending: {stats['pending']}")
        self.in_progress_label.setText(f"In Progress: {stats['in_progress']}")
        self.overdue_label.setText(f"Overdue: {stats['overdue']}")
        self.completion_rate_label.setText(f"Completion Rate: {stats['completion_rate']:.1f}%")

    def add_new_todo(self):
        """Add a new todo item"""
        dialog = TodoEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            todo_item = dialog.get_todo_item()
            if self.todo_model.add_todo(todo_item):
                self.refresh_data()
                self.logger.info(f"Added new todo: {todo_item.title}")
            else:
                QMessageBox.warning(self, "Error", "Failed to add todo item")

    def quick_add_today(self):
        """Quick add a task for today"""
        dialog = TodoEditDialog(parent=self)
        # Pre-set due date to today
        dialog.due_date_edit.setDate(QDate.currentDate())
        if dialog.exec() == QDialog.Accepted:
            todo_item = dialog.get_todo_item()
            if self.todo_model.add_todo(todo_item):
                self.refresh_data()
                self.logger.info(f"Added new todo for today: {todo_item.title}")
            else:
                QMessageBox.warning(self, "Error", "Failed to add todo item")

    def on_calendar_date_selected(self, date):
        """Handle date selection from calendar"""
        # Switch to task management tab and show tasks for the selected date
        self.main_tab_widget.setCurrentIndex(1)  # Task Management tab
        # Could add filtering by date here if needed

    def on_calendar_task_clicked(self, task_id):
        """Handle task click from calendar"""
        # Open task edit dialog
        todo = self.todo_model.get_todo_by_id(task_id)
        if todo:
            dialog = TodoEditDialog(todo, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_todo = dialog.get_todo_item()
                if self.todo_model.update_todo(task_id, updated_todo):
                    self.refresh_data()
                    self.logger.info(f"Updated todo: {updated_todo.title}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to update todo item")

    def on_history_task_selected(self, task_id):
        """Handle task selection from history"""
        # Open task view/edit dialog
        todo = self.todo_model.get_todo_by_id(task_id)
        if todo:
            dialog = TodoEditDialog(todo, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_todo = dialog.get_todo_item()
                if self.todo_model.update_todo(task_id, updated_todo):
                    self.refresh_data()
                    self.logger.info(f"Updated todo: {updated_todo.title}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to update todo item")

    def previous_week(self):
        """Navigate to previous week"""
        # This could be enhanced to actually change the week being viewed
        # For now, just refresh the current week view
        self.refresh_week_tasks()

    def next_week(self):
        """Navigate to next week"""
        # This could be enhanced to actually change the week being viewed
        # For now, just refresh the current week view
        self.refresh_week_tasks()

    def previous_month_tasks(self):
        """Navigate to previous month"""
        # This could be enhanced to actually change the month being viewed
        # For now, just refresh the current month view
        self.refresh_month_tasks()

    def next_month_tasks(self):
        """Navigate to next month"""
        # This could be enhanced to actually change the month being viewed
        # For now, just refresh the current month view
        self.refresh_month_tasks()

    def on_todo_updated(self, todo_id: int):
        """Handle todo item update"""
        # Find the widget and update the database
        for i in range(self.todo_layout.count() - 1):
            widget = self.todo_layout.itemAt(i).widget()
            if isinstance(widget, TodoItemWidget) and widget.todo_item.id == todo_id:
                if self.todo_model.update_todo(todo_id, widget.todo_item):
                    self.update_statistics()
                    self.logger.info(f"Updated todo: {widget.todo_item.title}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to update todo item")
                break

    def on_todo_deleted(self, todo_id: int):
        """Handle todo item deletion"""
        if self.todo_model.delete_todo(todo_id):
            self.refresh_data()
            self.logger.info(f"Deleted todo ID: {todo_id}")
        else:
            QMessageBox.warning(self, "Error", "Failed to delete todo item")

    # Google Tasks Synchronization Methods
    def sync_from_google_tasks(self):
        """Sync todos from Google Tasks"""
        if not self.todo_model.is_google_tasks_available():
            QMessageBox.warning(self, "Google Tasks", "Google Tasks integration is not available.\n\nPlease install required packages:\npip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return

        try:
            # Show progress dialog
            progress = QProgressDialog("Syncing from Google Tasks...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            # Perform sync
            added_count = self.todo_model.sync_from_google_tasks()

            progress.close()

            # Show result
            if added_count > 0:
                QMessageBox.information(self, "Sync Complete", f"Successfully imported {added_count} tasks from Google Tasks!")
                self.refresh_data()
            else:
                QMessageBox.information(self, "Sync Complete", "No new tasks found in Google Tasks.")

            # Always refresh to update status
            self.update_google_tasks_status()

        except Exception as e:
            QMessageBox.critical(self, "Sync Error", f"Failed to sync from Google Tasks:\n{str(e)}")
            self.logger.error(f"Error syncing from Google Tasks: {e}")

    def sync_to_google_tasks(self):
        """Sync todos to Google Tasks"""
        if not self.todo_model.is_google_tasks_available():
            QMessageBox.warning(self, "Google Tasks", "Google Tasks integration is not available.\n\nPlease install required packages:\npip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return

        try:
            # Show progress dialog
            progress = QProgressDialog("Syncing to Google Tasks...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            # Perform sync
            results = self.todo_model.sync_to_google_tasks()

            progress.close()

            # Show result
            if results:
                success_count = sum(1 for status in results.values() if status in ['created', 'updated'])
                failed_count = sum(1 for status in results.values() if status == 'failed')

                message = f"Sync completed!\n\nSuccessful: {success_count}\nFailed: {failed_count}"
                QMessageBox.information(self, "Sync Complete", message)
                self.refresh_data()
            else:
                QMessageBox.information(self, "Sync Complete", "No todos to sync.")

            # Always refresh status
            self.update_google_tasks_status()

        except Exception as e:
            QMessageBox.critical(self, "Sync Error", f"Failed to sync to Google Tasks:\n{str(e)}")
            self.logger.error(f"Error syncing to Google Tasks: {e}")

    def full_sync_google_tasks(self):
        """Perform full bidirectional sync with Google Tasks"""
        if not self.todo_model.is_google_tasks_available():
            QMessageBox.warning(self, "Google Tasks", "Google Tasks integration is not available.\n\nPlease install required packages:\npip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return

        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Full Sync",
            "This will perform a bidirectional sync with Google Tasks.\n\nThis may create duplicate tasks if not managed properly.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # Show progress dialog
            progress = QProgressDialog("Performing full sync with Google Tasks...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            # Perform full sync
            results = self.todo_model.full_sync_google_tasks()

            progress.close()

            # Show result
            if 'error' in results:
                QMessageBox.critical(self, "Sync Error", f"Full sync failed:\n{results['error']}")
            else:
                message = f"Full sync completed!\n\nFrom Google: {results['from_google']} tasks\nTo Google: {results['to_google']} tasks"
                QMessageBox.information(self, "Sync Complete", message)
                self.refresh_data()

            # Always refresh status
            self.update_google_tasks_status()

        except Exception as e:
            QMessageBox.critical(self, "Sync Error", f"Failed to perform full sync:\n{str(e)}")
            self.logger.error(f"Error in full sync: {e}")

















    def authenticate_google_tasks(self):
        """Authenticate with Google Tasks"""
        try:
            # Show info dialog first
            reply = QMessageBox.question(
                self,
                "Google Tasks Authentication",
                "This will open a web browser for Google authentication.\n\n"
                "You'll need to:\n"
                "1. Sign in to your Google account\n"
                "2. Grant permission to access Google Tasks\n"
                "3. Complete the authorization process\n\n"
                "Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply != QMessageBox.Yes:
                return

            # Show progress dialog
            progress = QProgressDialog("Authenticating with Google Tasks...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            # Attempt authentication
            success = self.todo_model.authenticate_google_tasks()

            progress.close()

            if success:
                # Automatically perform initial sync after successful authentication
                try:
                    self.logger.info("🔄 Performing automatic sync after authentication...")

                    # Show sync progress
                    sync_progress = QProgressDialog("Syncing tasks from Google Tasks...", "Cancel", 0, 0, self)
                    sync_progress.setWindowModality(Qt.WindowModal)
                    sync_progress.show()

                    # Perform sync from Google Tasks
                    synced_count = self.todo_model.sync_from_google_tasks(full_sync=True)

                    sync_progress.close()

                    self.logger.info(f"📊 Sync completed: {synced_count} tasks synced")

                    # Check current task count for verification
                    current_tasks = self.todo_model.get_all_todos()
                    total_tasks = len(current_tasks)
                    self.logger.info(f"📋 Total tasks in database after sync: {total_tasks}")

                    # Show success message with sync results
                    if synced_count > 0:
                        QMessageBox.information(
                            self,
                            "Authentication & Sync Successful",
                            f"Successfully connected to Google Tasks!\n\n"
                            f"✅ Synced {synced_count} tasks from your Google Tasks lists.\n"
                            f"📋 Total tasks in database: {total_tasks}\n\n"
                            "Your tasks are now available in the Todo tab."
                        )
                    else:
                        QMessageBox.information(
                            self,
                            "Authentication Successful",
                            "Successfully connected to Google Tasks!\n\n"
                            "No new tasks found in your Google Tasks lists.\n"
                            f"📋 Total tasks in database: {total_tasks}\n\n"
                            "You can now use the sync features to synchronize your todos."
                        )

                except Exception as sync_error:
                    self.logger.warning(f"Authentication successful but sync failed: {sync_error}")
                    QMessageBox.information(
                        self,
                        "Authentication Successful",
                        f"Successfully connected to Google Tasks!\n\n"
                        f"However, initial sync encountered an issue:\n{str(sync_error)}\n\n"
                        "You can manually sync using the sync buttons."
                    )

                # Refresh data to show any synced tasks
                self.refresh_data()
                # Update Google Tasks status and refresh header buttons
                self.update_google_tasks_status()
                self.update_header_buttons()
            else:
                QMessageBox.warning(
                    self,
                    "Authentication Failed",
                    "Failed to authenticate with Google Tasks.\n\n"
                    "This might be due to:\n"
                    "• Network connectivity issues\n"
                    "• Google account access restrictions\n"
                    "• App verification requirements\n\n"
                    "Please try again later or check your internet connection."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Authentication Error",
                f"An error occurred during authentication:\n{str(e)}"
            )
            self.logger.error(f"Error during Google Tasks authentication: {e}")

    def show_google_tasks_info(self):
        """Show information about Google Tasks integration"""
        status = self.todo_model.get_google_tasks_status()

        if not status.get('libraries_available', False):
            message = (
                "Google Tasks Integration\n\n"
                "❌ Required libraries not installed\n\n"
                "To enable Google Tasks synchronization, install:\n"
                "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib\n\n"
                "After installation, restart the application."
            )
        else:
            message = (
                "Google Tasks Integration\n\n"
                "✅ Libraries installed\n"
                f"🔐 Credentials: {'✅ Available' if status.get('credentials_exist') else '❌ Not found'}\n"
                f"🔗 Service: {'✅ Connected' if status.get('available') else '❌ Not connected'}\n\n"
                "Click 'Connect Google Tasks' to authenticate and enable synchronization."
            )

        QMessageBox.information(self, "Google Tasks Integration", message)

    def apply_theme(self, theme_name: str = 'dark'):
        """Apply theme to todo tracker widget"""
        try:
            print(f"🎨 DEBUG: TodoTrackerWidget.apply_theme called with theme: {theme_name}")

            # Apply theme to calendar widget if it exists
            if hasattr(self, 'calendar_widget') and self.calendar_widget:
                self.calendar_widget.apply_theme(theme_name)

            print(f"✅ SUCCESS: Applied theme '{theme_name}' to TodoTrackerWidget")

        except Exception as e:
            print(f"❌ ERROR: Failed to apply theme to TodoTrackerWidget: {e}")


