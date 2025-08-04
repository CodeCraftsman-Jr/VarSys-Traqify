"""
Habit Tracker UI Widgets
Contains all UI components for the habit tracking module
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QCheckBox, QFrame, QGroupBox, QScrollArea, QTabWidget,
    QProgressBar, QSpinBox, QColorDialog, QMessageBox, QDialog,
    QDialogButtonBox, QCalendarWidget, QSizePolicy, QSplitter
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QPainter, QBrush

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

from .models import HabitDefinition, HabitRecord, HabitDataModel


class HabitCheckBox(QCheckBox):
    """Custom checkbox for habit completion with enhanced styling"""
    
    habit_toggled = Signal(int, bool)  # habit_id, is_completed
    
    def __init__(self, habit_record: HabitRecord, parent=None):
        super().__init__(parent)
        
        self.habit_record = habit_record
        self.setObjectName("habitCheckBox")
        
        # Set initial state
        self.setChecked(habit_record.is_completed)
        
        # Set tooltip
        self.setToolTip(f"{habit_record.habit_name}\nTarget: {habit_record.target_count}")
        
        # Connect signal
        self.toggled.connect(self.on_toggled)
    
    def on_toggled(self, checked: bool):
        """Handle checkbox toggle"""
        self.habit_toggled.emit(self.habit_record.habit_id, checked)


class HabitCard(QFrame):
    """Card widget for displaying a single habit"""
    
    habit_clicked = Signal(int)  # habit_id
    habit_toggled = Signal(int, bool)  # habit_id, is_completed
    
    def __init__(self, habit_record: HabitRecord, habit_definition: Dict[str, Any], parent=None):
        super().__init__(parent)

        self.habit_record = habit_record
        self.habit_definition = habit_definition
        self._checkbox = None  # Track checkbox for cleanup

        self.setObjectName("habitCard")
        self.setMinimumHeight(80)
        self.setMaximumHeight(80)
        self.setCursor(Qt.PointingHandCursor)

        self.setup_ui()
        self.update_appearance()

    def __del__(self):
        """Destructor to ensure proper cleanup"""
        try:
            if self._checkbox:
                self._checkbox.toggled.disconnect()
        except:
            # Ignore errors during destruction
            pass
    
    def setup_ui(self):
        """Setup the card UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Icon/Emoji
        self.icon_label = QLabel(self.habit_definition.get('icon', '✓'))
        self.icon_label.setObjectName("habitIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setMinimumSize(30, 30)
        self.icon_label.setMaximumSize(30, 30)
        font = QFont()
        font.setPointSize(16)
        self.icon_label.setFont(font)
        layout.addWidget(self.icon_label)
        
        # Habit info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Habit name
        self.name_label = QLabel(self.habit_record.habit_name)
        self.name_label.setObjectName("habitName")
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        self.name_label.setFont(font)
        info_layout.addWidget(self.name_label)
        
        # Progress info
        progress_text = f"{self.habit_record.completed_count}/{self.habit_record.target_count}"
        if self.habit_record.target_count > 1:
            progress_text += f" ({self.habit_record.get_completion_percentage():.0f}%)"
        
        self.progress_label = QLabel(progress_text)
        self.progress_label.setObjectName("habitProgress")
        info_layout.addWidget(self.progress_label)
        
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # Completion checkbox
        self._checkbox = HabitCheckBox(self.habit_record, parent=self)
        self._checkbox.habit_toggled.connect(self.habit_toggled.emit)
        layout.addWidget(self._checkbox)

        # Keep reference for external access
        self.checkbox = self._checkbox
    
    def update_appearance(self):
        """Update card appearance based on completion status"""
        # Remove inline styles and use CSS classes that work with global themes
        if self.habit_record.is_completed:
            # Use completed state class
            self.setObjectName("habitCardCompleted")
            self.name_label.setObjectName("habitNameCompleted")

            # Store the habit color as a property for CSS access if needed
            habit_color = self.habit_definition.get('color', '#0e639c')
            self.setProperty("habitColor", habit_color)

            # Apply dynamic styling using CSS variables approach
            # This allows the global theme to control base colors while allowing custom accent colors
            self.setStyleSheet(f"""
                #habitCardCompleted {{
                    background-color: rgba({self._hex_to_rgb(habit_color)}, 0.1);
                    border: 2px solid {habit_color};
                }}
                #habitNameCompleted {{
                    color: {habit_color};
                }}
            """)
        else:
            # Use default state class - let global styles handle this
            self.setObjectName("habitCard")
            self.name_label.setObjectName("habitName")
            # Clear any custom styling to let global styles take over
            self.setStyleSheet("")

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB values for rgba() CSS function"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return f"{int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}"
        return "14, 99, 156"  # Default blue RGB values
    
    def mousePressEvent(self, event):
        """Handle mouse press for card click"""
        if event.button() == Qt.LeftButton:
            self.habit_clicked.emit(self.habit_record.habit_id)
        super().mousePressEvent(event)
    
    def update_record(self, habit_record: HabitRecord):
        """Update the card with new habit record data"""
        self.habit_record = habit_record
        
        # Update progress text
        progress_text = f"{habit_record.completed_count}/{habit_record.target_count}"
        if habit_record.target_count > 1:
            progress_text += f" ({habit_record.get_completion_percentage():.0f}%)"
        
        self.progress_label.setText(progress_text)
        
        # Update checkbox
        self.checkbox.habit_record = habit_record
        self.checkbox.setChecked(habit_record.is_completed)
        
        # Update appearance
        self.update_appearance()


class HabitGridWidget(QWidget):
    """Grid widget for displaying habits in a grid layout"""
    
    habit_toggled = Signal(int, bool)  # habit_id, is_completed
    habit_details_requested = Signal(int)  # habit_id
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.habit_cards = {}
        self.setup_ui()

    def __del__(self):
        """Destructor to ensure proper cleanup"""
        try:
            self._clear_habit_cards()
        except:
            # Ignore errors during destruction
            pass
    
    def setup_ui(self):
        """Setup the grid UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setObjectName("habitScrollArea")
        
        # Grid widget
        self.grid_widget = QWidget()
        self.grid_widget.setObjectName("habitGridWidget")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        
        scroll_area.setWidget(self.grid_widget)
        main_layout.addWidget(scroll_area)
    
    def update_habits(self, habit_records: List[HabitRecord], habit_definitions: Dict[int, Dict[str, Any]]):
        """Update the grid with habit records using safe Qt memory management"""
        # Clear existing cards with proper Qt cleanup
        self._clear_habit_cards()

        # Add habit cards
        columns = 3  # Number of columns in grid

        for i, record in enumerate(habit_records):
            row = i // columns
            col = i % columns

            habit_def = habit_definitions.get(record.habit_id, {})

            card = HabitCard(record, habit_def, parent=self.grid_widget)
            card.habit_toggled.connect(self.habit_toggled.emit)
            card.habit_clicked.connect(self.habit_details_requested.emit)

            self.grid_layout.addWidget(card, row, col)
            self.habit_cards[record.habit_id] = card

        # Add stretch to fill remaining space
        self.grid_layout.setRowStretch(len(habit_records) // columns + 1, 1)

    def _clear_habit_cards(self):
        """Safely clear all habit cards with proper Qt memory management"""
        for habit_id, card in self.habit_cards.items():
            try:
                # Disconnect signals to prevent dangling connections
                card.habit_toggled.disconnect()
                card.habit_clicked.disconnect()
            except (RuntimeError, TypeError):
                # Signals may already be disconnected or object deleted
                pass

            try:
                # Remove from layout first
                self.grid_layout.removeWidget(card)
            except (RuntimeError, TypeError):
                # Widget may already be removed
                pass

            try:
                # Properly delete the widget
                card.deleteLater()
            except (RuntimeError, TypeError):
                # Widget may already be deleted
                pass

        # Clear the dictionary
        self.habit_cards.clear()
    
    def update_habit_record(self, habit_record: HabitRecord):
        """Update a specific habit record in the grid"""
        if habit_record.habit_id in self.habit_cards:
            self.habit_cards[habit_record.habit_id].update_record(habit_record)


class HabitStatsWidget(QWidget):
    """Widget displaying habit statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the statistics UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Habit Statistics")
        title_label.setObjectName("habitStatsTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # Stats frame
        stats_frame = QFrame()
        stats_frame.setObjectName("habitStatsFrame")
        stats_layout = QGridLayout(stats_frame)
        
        # Create stat labels
        self.total_habits_label = QLabel("0")
        self.today_completion_label = QLabel("0%")
        self.overall_completion_label = QLabel("0%")
        self.best_streak_label = QLabel("0 days")
        
        # Style stat labels
        for label in [self.total_habits_label, self.today_completion_label,
                     self.overall_completion_label, self.best_streak_label]:
            label.setObjectName("habitStatValue")
            font = QFont()
            font.setBold(True)
            font.setPointSize(11)
            label.setFont(font)
            label.setAlignment(Qt.AlignCenter)
        
        # Add to layout
        stats_layout.addWidget(QLabel("Total Habits:"), 0, 0)
        stats_layout.addWidget(self.total_habits_label, 0, 1)
        
        stats_layout.addWidget(QLabel("Today's Progress:"), 1, 0)
        stats_layout.addWidget(self.today_completion_label, 1, 1)
        
        stats_layout.addWidget(QLabel("Overall Rate:"), 2, 0)
        stats_layout.addWidget(self.overall_completion_label, 2, 1)
        
        stats_layout.addWidget(QLabel("Best Streak:"), 3, 0)
        stats_layout.addWidget(self.best_streak_label, 3, 1)
        
        layout.addWidget(stats_frame)
        layout.addStretch()
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update the statistics display"""
        self.total_habits_label.setText(str(stats.get('total_habits', 0)))
        self.today_completion_label.setText(f"{stats.get('today_completion_rate', 0):.0f}%")
        self.overall_completion_label.setText(f"{stats.get('overall_completion_rate', 0):.0f}%")
        self.best_streak_label.setText(f"{stats.get('best_streak', 0)} days")


class HabitProgressWidget(QWidget):
    """Widget showing today's overall progress"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the progress widget UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Today's Progress")
        title_label.setObjectName("habitProgressTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # Progress frame
        progress_frame = QFrame()
        progress_frame.setObjectName("habitProgressFrame")
        progress_layout = QVBoxLayout(progress_frame)
        
        # Completion count
        self.completion_label = QLabel("0 / 0 habits completed")
        self.completion_label.setObjectName("habitCompletionLabel")
        self.completion_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.completion_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("habitMainProgressBar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        # Motivational message
        self.message_label = QLabel("Start your day by completing your habits!")
        self.message_label.setObjectName("habitMessageLabel")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        progress_layout.addWidget(self.message_label)
        
        layout.addWidget(progress_frame)
        layout.addStretch()
    
    def update_progress(self, completed: int, total: int):
        """Update progress display"""
        self.completion_label.setText(f"{completed} / {total} habits completed")
        
        if total > 0:
            percentage = (completed / total) * 100
            self.progress_bar.setValue(int(percentage))
            self.progress_bar.setFormat(f"{percentage:.0f}%")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0%")
        
        # Update motivational message
        if total == 0:
            message = "No habits configured. Add some habits to get started!"
        elif completed == 0:
            message = "Start your day by completing your habits!"
        elif completed == total:
            message = "🎉 Congratulations! All habits completed today!"
        elif completed >= total * 0.8:
            message = "Great progress! You're almost there!"
        elif completed >= total * 0.5:
            message = "Good work! Keep going!"
        else:
            message = "You've got this! Every habit counts!"
        
        self.message_label.setText(message)


class HabitEditDialog(QDialog):
    """Dialog for editing habit definitions"""

    def __init__(self, habit: HabitDefinition, data_model: HabitDataModel, parent=None):
        super().__init__(parent)

        self.habit = habit
        self.data_model = data_model
        self.setup_ui()
        self.setup_connections()
        self.load_habit_data()

        self.setModal(True)

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Edit Habit")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., 'Morning Workout'")
        form_layout.addRow("Name:", self.name_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Brief description...")
        form_layout.addRow("Description:", self.description_edit)

        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Health & Wellness", "Productivity", "Learning & Development",
            "Personal Care", "Fitness", "Mindfulness", "Other"
        ])
        form_layout.addRow("Category:", self.category_combo)

        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Daily", "Weekly", "Custom"])
        form_layout.addRow("Frequency:", self.frequency_combo)

        self.target_spinbox = QSpinBox()
        self.target_spinbox.setRange(1, 10)
        form_layout.addRow("Target Count:", self.target_spinbox)

        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("e.g., ✓, 💪, 📚")
        form_layout.addRow("Icon/Emoji:", self.icon_edit)

        # Color picker
        color_layout = QHBoxLayout()
        self.color_value = "#0e639c"
        self.color_button = QPushButton()
        self.color_button.setFixedSize(30, 30)
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(QLabel("Click to choose color"))
        color_layout.addStretch()
        form_layout.addRow("Color:", color_layout)

        self.active_checkbox = QCheckBox("Active")
        form_layout.addRow("Status:", self.active_checkbox)

        layout.addLayout(form_layout)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        layout.addWidget(button_box)

        # Store references
        self.button_box = button_box

    def setup_connections(self):
        """Setup signal connections"""
        self.button_box.accepted.connect(self.save_habit)
        self.button_box.rejected.connect(self.reject)

    def choose_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(QColor(self.color_value), self)
        if color.isValid():
            self.color_value = color.name()
            self.color_button.setStyleSheet(f"background-color: {self.color_value}; border: 1px solid #ccc;")

    def load_habit_data(self):
        """Load habit data into the form"""
        self.name_edit.setText(self.habit.name)
        self.description_edit.setText(self.habit.description)

        # Set category
        category_index = self.category_combo.findText(self.habit.category)
        if category_index >= 0:
            self.category_combo.setCurrentIndex(category_index)

        # Set frequency
        frequency_index = self.frequency_combo.findText(self.habit.frequency)
        if frequency_index >= 0:
            self.frequency_combo.setCurrentIndex(frequency_index)

        self.target_spinbox.setValue(self.habit.target_count)
        self.icon_edit.setText(self.habit.icon)
        self.active_checkbox.setChecked(self.habit.is_active)

        # Set color
        self.color_value = self.habit.color
        self.color_button.setStyleSheet(f"background-color: {self.color_value}; border: 1px solid #ccc;")

    def save_habit(self):
        """Save the edited habit"""
        name = self.name_edit.text().strip()
        description = self.description_edit.text().strip()
        category = self.category_combo.currentText()
        frequency = self.frequency_combo.currentText()
        target_count = self.target_spinbox.value()
        icon = self.icon_edit.text().strip()
        is_active = self.active_checkbox.isChecked()

        if not name:
            QMessageBox.warning(self, "Error", "Habit name is required")
            return

        if not icon:
            icon = "✓"

        # Update habit
        self.habit.name = name
        self.habit.description = description
        self.habit.category = category
        self.habit.frequency = frequency
        self.habit.target_count = target_count
        self.habit.icon = icon
        self.habit.color = self.color_value
        self.habit.is_active = is_active

        if self.data_model.update_habit(self.habit.id, self.habit):
            QMessageBox.information(self, "Success", "Habit updated successfully!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to update habit!")


class HabitManagementDialog(QDialog):
    """Dialog for managing habit definitions"""

    habits_updated = Signal()

    def __init__(self, data_model: HabitDataModel, parent=None):
        super().__init__(parent)

        self.data_model = data_model
        self.setup_ui()
        self.setup_connections()
        self.load_habits()

        self.setModal(True)

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Manage Habits")
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout(self)

        # Add new habit section
        add_frame = QGroupBox("Add New Habit")
        add_layout = QFormLayout(add_frame)

        self.new_habit_name = QLineEdit()
        self.new_habit_name.setPlaceholderText("e.g., 'Morning Workout'")
        add_layout.addRow("Name:", self.new_habit_name)

        self.new_habit_description = QLineEdit()
        self.new_habit_description.setPlaceholderText("Brief description...")
        add_layout.addRow("Description:", self.new_habit_description)

        self.new_habit_category = QComboBox()
        self.new_habit_category.addItems([
            "Health & Wellness", "Productivity", "Learning & Development",
            "Personal Care", "Fitness", "Mindfulness", "Other"
        ])
        add_layout.addRow("Category:", self.new_habit_category)

        self.new_habit_frequency = QComboBox()
        self.new_habit_frequency.addItems(["Daily", "Weekly", "Custom"])
        add_layout.addRow("Frequency:", self.new_habit_frequency)

        self.new_habit_target = QSpinBox()
        self.new_habit_target.setRange(1, 10)
        self.new_habit_target.setValue(1)
        add_layout.addRow("Target Count:", self.new_habit_target)

        self.new_habit_icon = QLineEdit()
        self.new_habit_icon.setPlaceholderText("e.g., ✓, 💪, 📚")
        self.new_habit_icon.setText("✓")
        add_layout.addRow("Icon/Emoji:", self.new_habit_icon)

        # Color picker
        color_layout = QHBoxLayout()
        self.new_habit_color = "#0e639c"
        self.color_button = QPushButton()
        self.color_button.setFixedSize(30, 30)
        self.color_button.setStyleSheet(f"background-color: {self.new_habit_color}; border: 1px solid #ccc;")
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(QLabel("Click to choose color"))
        color_layout.addStretch()
        add_layout.addRow("Color:", color_layout)

        add_button = QPushButton("Add Habit")
        add_button.setObjectName("habitAddButton")
        add_button.clicked.connect(self.add_habit)
        add_layout.addRow("", add_button)

        layout.addWidget(add_frame)

        # Existing habits section
        habits_frame = QGroupBox("Existing Habits")
        habits_layout = QVBoxLayout(habits_frame)

        # Habits scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)

        self.habits_widget = QWidget()
        self.habits_layout = QVBoxLayout(self.habits_widget)
        scroll_area.setWidget(self.habits_widget)

        habits_layout.addWidget(scroll_area)
        layout.addWidget(habits_frame)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def setup_connections(self):
        """Setup signal connections"""
        pass

    def choose_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(QColor(self.new_habit_color), self)
        if color.isValid():
            self.new_habit_color = color.name()
            self.color_button.setStyleSheet(f"background-color: {self.new_habit_color}; border: 1px solid #ccc;")

    def load_habits(self):
        """Load habits into the interface"""
        # Clear existing habit widgets
        for i in reversed(range(self.habits_layout.count())):
            self.habits_layout.itemAt(i).widget().setParent(None)

        # Load habits
        df = self.data_model.get_all_habits()

        if df.empty:
            no_habits_label = QLabel("No habits configured")
            no_habits_label.setAlignment(Qt.AlignCenter)
            self.habits_layout.addWidget(no_habits_label)
            return

        for _, habit in df.iterrows():
            habit_widget = self.create_habit_widget(habit)
            self.habits_layout.addWidget(habit_widget)

        self.habits_layout.addStretch()

    def create_habit_widget(self, habit: Dict[str, Any]) -> QWidget:
        """Create widget for a single habit"""
        widget = QFrame()
        widget.setObjectName("habitManagementItem")
        widget.setFrameStyle(QFrame.Box)
        layout = QHBoxLayout(widget)

        # Icon
        icon_label = QLabel(habit['icon'])
        icon_label.setMinimumSize(30, 30)
        icon_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        icon_label.setFont(font)
        layout.addWidget(icon_label)

        # Info
        info_layout = QVBoxLayout()

        name_label = QLabel(habit['name'])
        name_label.setObjectName("habitManagementName")
        font = QFont()
        font.setBold(True)
        name_label.setFont(font)
        info_layout.addWidget(name_label)

        details_label = QLabel(f"{habit['category']} • {habit['frequency']} • Target: {habit['target_count']}")
        details_label.setObjectName("habitManagementDetails")
        info_layout.addWidget(details_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Active checkbox
        active_checkbox = QCheckBox("Active")
        active_checkbox.setChecked(bool(habit['is_active']))
        active_checkbox.toggled.connect(lambda checked, h_id=habit['id']: self.toggle_habit_active(h_id, checked))
        layout.addWidget(active_checkbox)

        # Edit button
        edit_button = QPushButton("Edit")
        edit_button.setObjectName("habitEditButton")
        edit_button.setMaximumWidth(60)
        edit_button.clicked.connect(lambda _, h_id=habit['id']: self.edit_habit(h_id))
        layout.addWidget(edit_button)

        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setObjectName("habitDeleteButton")
        delete_button.setMaximumWidth(60)
        delete_button.clicked.connect(lambda _, h_id=habit['id']: self.delete_habit(h_id))
        layout.addWidget(delete_button)

        return widget

    def toggle_habit_active(self, habit_id: int, is_active: bool):
        """Toggle habit active status"""
        # Get the habit and update its active status
        df = self.data_model.get_all_habits()
        habit_data = df[df['id'] == habit_id]

        if not habit_data.empty:
            habit_dict = habit_data.iloc[0].to_dict()
            habit = HabitDefinition.from_dict(habit_dict)
            habit.is_active = is_active

            if self.data_model.update_habit(habit_id, habit):
                self.habits_updated.emit()
            else:
                QMessageBox.warning(self, "Error", "Failed to update habit status")

    def edit_habit(self, habit_id: int):
        """Edit an existing habit"""
        # Get the habit data
        df = self.data_model.get_all_habits()
        habit_data = df[df['id'] == habit_id]

        if habit_data.empty:
            QMessageBox.warning(self, "Error", "Habit not found")
            return

        habit_dict = habit_data.iloc[0].to_dict()
        habit = HabitDefinition.from_dict(habit_dict)

        # Open edit dialog
        dialog = HabitEditDialog(habit, self.data_model, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_habits()
            self.habits_updated.emit()

    def delete_habit(self, habit_id: int):
        """Delete a habit"""
        # Get habit name for confirmation
        df = self.data_model.get_all_habits()
        habit_data = df[df['id'] == habit_id]

        if habit_data.empty:
            QMessageBox.warning(self, "Error", "Habit not found")
            return

        habit_name = habit_data.iloc[0]['name']

        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the habit '{habit_name}'?\n\n"
            f"This will also delete all associated records and cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.data_model.delete_habit(habit_id):
                QMessageBox.information(self, "Success", "Habit deleted successfully!")
                self.load_habits()
                self.habits_updated.emit()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete habit!")

    def add_habit(self):
        """Add a new habit"""
        name = self.new_habit_name.text().strip()
        description = self.new_habit_description.text().strip()
        category = self.new_habit_category.currentText()
        frequency = self.new_habit_frequency.currentText()
        target_count = self.new_habit_target.value()
        icon = self.new_habit_icon.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Habit name is required")
            return

        if not icon:
            icon = "✓"

        # Create habit
        habit = HabitDefinition(
            name=name,
            description=description,
            category=category,
            frequency=frequency,
            target_count=target_count,
            icon=icon,
            color=self.new_habit_color,
            is_active=True
        )

        if self.data_model.add_habit(habit):
            # Clear form
            self.new_habit_name.clear()
            self.new_habit_description.clear()
            self.new_habit_target.setValue(1)
            self.new_habit_icon.setText("✓")
            self.new_habit_color = "#0e639c"
            self.color_button.setStyleSheet(f"background-color: {self.new_habit_color}; border: 1px solid #ccc;")

            self.load_habits()
            self.habits_updated.emit()
            QMessageBox.information(self, "Success", "Habit added successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to add habit")


class HabitTrackerWidget(QWidget):
    """Main habit tracker widget"""

    # Define signals for safe error reporting
    error_occurred = Signal(str, str)  # error_message, title

    def __init__(self, data_manager, config, parent=None):
        super().__init__(parent)

        import logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.data_manager = data_manager
        self.config = config
        self.habit_model = HabitDataModel(data_manager)
        self.current_date = date.today()

        self.setup_ui()
        self.setup_connections()
        self.refresh_data()

        # Setup auto-refresh timer (reduced frequency to prevent excessive widget recreation)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes instead of 1 minute

        # Connect error signal to safe error display
        self.error_occurred.connect(self.show_error_message)

    def __del__(self):
        """Destructor to ensure proper cleanup"""
        try:
            if hasattr(self, 'refresh_timer') and self.refresh_timer:
                self.refresh_timer.stop()
            if hasattr(self, 'habit_grid') and self.habit_grid:
                self.habit_grid._clear_habit_cards()
        except:
            # Ignore errors during destruction
            pass

    def show_error_message(self, message: str, title: str = "Error"):
        """Safely display error messages using QTimer to avoid crashes from signal handlers"""
        def safe_show_message():
            try:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, title, message)
            except Exception as e:
                self.logger.error(f"Failed to show error message: {e}")

        # Use QTimer.singleShot to safely show message from main thread
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, safe_show_message)

    def setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # Reduced from 20px to 10px
        layout.setSpacing(8)  # Reduced from 15px to 8px

        # Header
        self.create_header(layout)

        # Main content
        main_splitter = QSplitter(Qt.Horizontal)

        # Left panel - Habit grid
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)

        # Right panel - Progress and stats
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set splitter proportions
        main_splitter.setSizes([700, 300])
        layout.addWidget(main_splitter)

    def create_header(self, layout):
        """Create header with title and action buttons"""
        header_frame = QFrame()
        header_frame.setObjectName("habitHeader")
        header_frame.setMaximumHeight(50)  # Standardized header height
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(5, 5, 5, 5)  # Standardized margins
        header_layout.setSpacing(8)  # Standardized spacing

        # Title and date section
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)

        title_label = QLabel("Habit Tracker")
        title_label.setObjectName("habitTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)  # Standardized font size
        title_label.setFont(font)
        title_layout.addWidget(title_label)

        self.date_label = QLabel(self.current_date.strftime("%A, %B %d, %Y"))
        self.date_label.setObjectName("habitDateLabel")
        title_layout.addWidget(self.date_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Date navigation buttons
        nav_layout = QHBoxLayout()

        self.prev_day_button = QPushButton("◀ Previous")
        self.prev_day_button.setObjectName("habitNavButton")
        self.prev_day_button.setMinimumHeight(32)  # Standardized button height
        self.prev_day_button.setMaximumHeight(32)
        nav_layout.addWidget(self.prev_day_button)

        self.today_button = QPushButton("Today")
        self.today_button.setObjectName("habitTodayButton")
        self.today_button.setMinimumHeight(32)  # Standardized button height
        self.today_button.setMaximumHeight(32)
        nav_layout.addWidget(self.today_button)

        self.next_day_button = QPushButton("Next ▶")
        self.next_day_button.setObjectName("habitNavButton")
        self.next_day_button.setMinimumHeight(32)  # Standardized button height
        self.next_day_button.setMaximumHeight(32)
        nav_layout.addWidget(self.next_day_button)

        header_layout.addLayout(nav_layout)

        # Action buttons
        self.manage_habits_button = QPushButton("Manage Habits")
        self.manage_habits_button.setObjectName("habitManageButton")
        self.manage_habits_button.setMinimumHeight(32)  # Standardized button height
        self.manage_habits_button.setMaximumHeight(32)
        header_layout.addWidget(self.manage_habits_button)

        layout.addWidget(header_frame)

    def create_left_panel(self):
        """Create left panel with habit grid"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Habit grid
        self.habit_grid = HabitGridWidget()
        layout.addWidget(self.habit_grid)

        return panel

    def create_right_panel(self):
        """Create right panel with progress and statistics"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Progress widget
        self.progress_widget = HabitProgressWidget()
        layout.addWidget(self.progress_widget)

        # Statistics widget
        self.stats_widget = HabitStatsWidget()
        layout.addWidget(self.stats_widget)

        layout.addStretch()
        return panel

    def setup_connections(self):
        """Setup signal connections"""
        # Navigation buttons
        self.prev_day_button.clicked.connect(self.prev_day)
        self.today_button.clicked.connect(self.go_to_today)
        self.next_day_button.clicked.connect(self.next_day)
        self.manage_habits_button.clicked.connect(self.manage_habits)

        # Habit grid connections
        self.habit_grid.habit_toggled.connect(self.toggle_habit)
        self.habit_grid.habit_details_requested.connect(self.show_habit_details)

        # Data model connections
        self.data_manager.data_changed.connect(self.on_data_changed)

    def refresh_data(self):
        """Refresh all data with enhanced error handling"""
        try:
            self.logger.debug(f"Refreshing habit data for date: {self.current_date}")
            self.load_habits_for_date()
            self.update_statistics()
            self.logger.debug("Habit data refresh completed successfully")
        except Exception as e:
            self.logger.error(f"Error refreshing habit data: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")

            # Show user-friendly message using safe signal
            error_message = "There was an issue refreshing the habit data."

            # Provide more specific error information if possible
            if "habit" in str(e).lower():
                error_message += " There may be an issue with your habit configuration."
            elif "date" in str(e).lower():
                error_message += " There may be an issue with the date format."
            elif "database" in str(e).lower() or "csv" in str(e).lower():
                error_message += " There may be an issue accessing the data files."

            error_message += " Please try again or restart the application if the problem persists."

            self.error_occurred.emit(error_message, "Data Refresh Error")

            # Set safe default values to prevent UI issues
            try:
                self.progress_widget.update_progress(0, 1)
                # Clear the habit grid to prevent display issues
                self.habit_grid.update_habits([], {})
            except Exception as ui_error:
                self.logger.error(f"Error setting safe default values: {ui_error}")

        # Always update date display, even if data refresh failed
        try:
            self.update_date_display()
        except Exception as date_error:
            self.logger.error(f"Error updating date display: {date_error}")

    def load_habits_for_date(self):
        """Load habits for the current date with enhanced error handling"""
        try:
            self.logger.debug(f"Loading habits for date: {self.current_date}")

            # Get habit records for the current date
            habit_records = self.habit_model.get_or_create_daily_records(self.current_date)
            self.logger.debug(f"Retrieved {len(habit_records)} habit records")

            # Get habit definitions
            habits_df = self.habit_model.get_active_habits()
            habit_definitions = {}

            if not habits_df.empty:
                for _, habit in habits_df.iterrows():
                    try:
                        habit_id = habit['id']
                        if not pd.isna(habit_id):
                            habit_definitions[int(float(habit_id))] = habit.to_dict()
                    except (ValueError, TypeError, KeyError) as e:
                        self.logger.warning(f"Error processing habit definition: {e}")
                        continue

            self.logger.debug(f"Processed {len(habit_definitions)} habit definitions")

            # Update grid
            self.habit_grid.update_habits(habit_records, habit_definitions)

            # Update progress
            completed = sum(1 for record in habit_records if record.is_completed)
            total = len(habit_records)
            self.progress_widget.update_progress(completed, total)

            self.logger.debug(f"Progress updated: {completed}/{total} habits completed")

        except Exception as e:
            self.logger.error(f"Error in load_habits_for_date: {e}")
            # Re-raise the exception so it can be handled by refresh_data
            raise

    def update_statistics(self):
        """Update statistics display"""
        stats = self.habit_model.get_habit_summary()
        self.stats_widget.update_stats(stats)

    def update_date_display(self):
        """Update date display"""
        self.date_label.setText(self.current_date.strftime("%A, %B %d, %Y"))

        # Disable next button if current date is today or future
        self.next_day_button.setEnabled(self.current_date < date.today())

    def prev_day(self):
        """Navigate to previous day"""
        self.current_date -= timedelta(days=1)
        self.refresh_data()

    def next_day(self):
        """Navigate to next day"""
        if self.current_date < date.today():
            self.current_date += timedelta(days=1)
            self.refresh_data()

    def go_to_today(self):
        """Navigate to today"""
        self.current_date = date.today()
        self.refresh_data()

    def toggle_habit(self, habit_id: int, is_completed: bool):
        """Toggle habit completion status with comprehensive error handling"""
        try:
            # Get current records
            habit_records = self.habit_model.get_or_create_daily_records(self.current_date)

            # Find and update the specific habit record
            record_found = False
            for record in habit_records:
                if record.habit_id == habit_id:
                    record_found = True
                    try:
                        if is_completed:
                            record.completed_count = record.target_count
                        else:
                            record.completed_count = 0

                        record.update_completion_status()

                        # Save the record with error handling
                        save_success = self.habit_model.save_habit_record(record)
                        if not save_success:
                            self.logger.error(f"Failed to save habit record for habit_id: {habit_id}")
                            # Show user-friendly error message using safe signal
                            self.error_occurred.emit(
                                "Failed to save habit completion status. Please try again.",
                                "Save Error"
                            )
                            return

                        # Update the grid
                        self.habit_grid.update_habit_record(record)
                        self.logger.debug(f"Successfully toggled habit {habit_id} to {'completed' if is_completed else 'incomplete'}")
                        break

                    except Exception as record_error:
                        self.logger.error(f"Error updating habit record {habit_id}: {record_error}")
                        # Show user-friendly error message using safe signal
                        self.error_occurred.emit(
                            f"Failed to update habit status: {str(record_error)}",
                            "Update Error"
                        )
                        return

            if not record_found:
                self.logger.warning(f"Habit record not found for habit_id: {habit_id}")
                # Show user-friendly error message using safe signal
                self.error_occurred.emit(
                    "Could not find habit record to update.",
                    "Habit Not Found"
                )
                return

            # Update progress without full widget recreation
            try:
                # Just update the progress display, not all widgets
                habit_records = self.habit_model.get_or_create_daily_records(self.current_date)
                completed = sum(1 for record in habit_records if record.is_completed)
                total = len(habit_records)
                self.progress_widget.update_progress(completed, total)
                self.logger.debug(f"Progress updated: {completed}/{total} habits completed")
            except Exception as refresh_error:
                self.logger.error(f"Error updating progress display: {refresh_error}")
                # Don't show error to user for display refresh issues

        except Exception as e:
            self.logger.error(f"Critical error in toggle_habit for habit_id {habit_id}: {e}")
            # Show critical error message using safe signal
            self.error_occurred.emit(
                f"A critical error occurred while updating the habit. "
                f"Please restart the application if problems persist.\n\n"
                f"Error: {str(e)}",
                "Critical Error"
            )
            # Don't re-raise the exception to prevent application crash

    def show_habit_details(self, habit_id: int):
        """Show detailed information about a habit"""
        # This could open a detailed view or edit dialog
        # For now, just show a simple message using safe signal
        self.error_occurred.emit(f"Detailed view for habit ID: {habit_id}", "Habit Details")

    def manage_habits(self):
        """Open habit management dialog"""
        dialog = HabitManagementDialog(self.habit_model, parent=self)
        dialog.habits_updated.connect(self.refresh_data)
        dialog.exec()

    def on_data_changed(self, module: str, operation: str):
        """Handle data changes"""
        if module == "habits":
            self.refresh_data()
