"""
Budget Planning UI Widgets
Contains all UI components for the budget planning module
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QCheckBox, QFrame, QGroupBox, QScrollArea, QTabWidget,
    QProgressBar, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QButtonGroup, QDoubleSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

from .models import BudgetPlan, BudgetCategory, BudgetDataModel, BudgetType, CategoryType
from ..income.models import IncomeDataModel


class SimplifiedBudgetWidget(QWidget):
    """Simplified budget planning widget with predefined categories and income integration"""

    def __init__(self, budget_model: BudgetDataModel, data_manager=None, parent=None):
        super().__init__(parent)
        self.budget_model = budget_model
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        self.category_widgets = {}

        # Initialize income model for integration
        if self.data_manager:
            self.income_model = IncomeDataModel(self.data_manager)
        else:
            self.income_model = None

        self.setup_ui()

        # Clean up any invalid IDs before loading
        self.cleanup_invalid_category_ids()

        self.load_categories()

        # Auto-refresh income integration every 30 seconds
        self.income_refresh_timer = QTimer()
        self.income_refresh_timer.timeout.connect(self.refresh_income_integration)
        self.income_refresh_timer.start(30000)  # 30 seconds

    def cleanup_invalid_category_ids(self):
        """Clean up any invalid category IDs using the comprehensive ID management system"""
        try:
            self.logger.info("Starting comprehensive ID cleanup...")

            # Get current ID statistics
            stats = self.budget_model.get_id_statistics()
            self.logger.info(f"ID Statistics: {stats}")

            # Assign missing IDs if needed
            if stats['invalid_ids'] > 0:
                self.logger.warning(f"Found {stats['invalid_ids']} categories with invalid IDs")
                result = self.budget_model.assign_missing_ids()

                if result['success']:
                    self.logger.info(f"Successfully assigned {result['ids_assigned']} missing IDs")

                    # Show user notification
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self,
                        "ID Cleanup Complete",
                        f"Successfully assigned {result['ids_assigned']} missing IDs to budget categories.\n"
                        f"All categories now have valid IDs for database operations."
                    )
                else:
                    self.logger.error(f"Failed to assign missing IDs: {result['message']}")

            # Handle ID gaps and duplicates
            if stats['id_gaps'] or stats['duplicate_ids']:
                self.logger.info("Compacting ID sequence to resolve gaps and duplicates...")
                compact_result = self.budget_model.compact_id_sequence()

                if compact_result['success']:
                    self.logger.info("Successfully compacted ID sequence")
                else:
                    self.logger.error(f"Failed to compact ID sequence: {compact_result['message']}")

            self.logger.info("ID cleanup completed successfully")

        except Exception as e:
            self.logger.error(f"Error during comprehensive ID cleanup: {e}")

    def setup_ui(self):
        """Setup the simplified budget UI"""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("💰 Budget Planning")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Total budget display
        self.total_budget_label = QLabel("Total Budget: ₹0")
        self.total_budget_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_budget_label.setStyleSheet("color: #2e7d32; padding: 5px;")
        header_layout.addWidget(self.total_budget_label)

        layout.addLayout(header_layout)

        # Budget overview
        overview_frame = QFrame()
        overview_frame.setFrameStyle(QFrame.Box)
        overview_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0px;
            }
        """)

        overview_layout = QHBoxLayout(overview_frame)

        # Planned vs Actual
        self.planned_label = QLabel("Planned: ₹0")
        self.planned_label.setFont(QFont("Arial", 12, QFont.Bold))
        overview_layout.addWidget(self.planned_label)

        self.actual_label = QLabel("Actual: ₹0")
        self.actual_label.setFont(QFont("Arial", 12, QFont.Bold))
        overview_layout.addWidget(self.actual_label)

        self.remaining_label = QLabel("Remaining: ₹0")
        self.remaining_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.remaining_label.setStyleSheet("color: #2e7d32;")
        overview_layout.addWidget(self.remaining_label)

        layout.addWidget(overview_frame)

        # Categories section
        categories_frame = QFrame()
        categories_frame.setFrameStyle(QFrame.Box)
        categories_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        categories_layout = QVBoxLayout(categories_frame)

        # Categories header
        categories_header = QHBoxLayout()
        categories_title = QLabel("Budget Categories")
        categories_title.setFont(QFont("Arial", 14, QFont.Bold))
        categories_header.addWidget(categories_title)

        categories_header.addStretch()

        # Add/Remove category buttons
        add_category_btn = QPushButton("➕ Add Category")
        add_category_btn.clicked.connect(self.add_custom_category)
        categories_header.addWidget(add_category_btn)

        categories_layout.addLayout(categories_header)

        # Scroll area for categories with improved styling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                border-radius: 4px;
                min-height: 20px;
            }
        """)

        self.categories_widget = QWidget()
        # Use vertical layout with better spacing for card-style layout
        self.categories_layout = QVBoxLayout(self.categories_widget)
        self.categories_layout.setSpacing(8)
        self.categories_layout.setContentsMargins(4, 4, 4, 4)

        # Add stretch at the end to push cards to the top
        self.categories_layout.addStretch()

        scroll_area.setWidget(self.categories_widget)
        categories_layout.addWidget(scroll_area)

        layout.addWidget(categories_frame)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("💾 Save Budget")
        save_btn.clicked.connect(self.save_budget)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(save_btn)

        reset_btn = QPushButton("🔄 Reset")
        reset_btn.clicked.connect(self.reset_budget)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        buttons_layout.addWidget(reset_btn)

        layout.addLayout(buttons_layout)

    def create_category_widget(self, category: BudgetCategory) -> QWidget:
        """Create a modern card-style widget for a budget category"""
        # Main card container
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 0px;
                margin: 4px;
            }
            QFrame:hover {
                border: 2px solid #2196f3;
            }
        """)

        # Main vertical layout for the card
        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)

        # Header section with category name and controls
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Category name with essential indicator
        name_container = QHBoxLayout()
        name_container.setSpacing(6)

        name_label = QLabel(category.name)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        name_label.setStyleSheet("color: #333333;")
        name_container.addWidget(name_label)

        # Essential indicator (star icon)
        if category.is_essential:
            essential_label = QLabel("⭐")
            essential_label.setToolTip("Essential category")
            essential_label.setStyleSheet("font-size: 14px;")
            name_container.addWidget(essential_label)

        name_container.addStretch()
        header_layout.addLayout(name_container)

        # Delete button (now available for ALL categories)
        remove_btn = QPushButton("🗑️")
        remove_btn.setToolTip("Delete category")
        remove_btn.clicked.connect(lambda: self.remove_category(category.name))
        remove_btn.setFixedSize(32, 32)
        remove_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff5722;
                color: white;
                border: 1px solid #ff5722;
            }
        """)
        header_layout.addWidget(remove_btn)

        main_layout.addLayout(header_layout)

        # Amount inputs section
        amounts_layout = QHBoxLayout()
        amounts_layout.setSpacing(12)

        # Planned amount section with edit protection
        planned_section = QVBoxLayout()
        planned_section.setSpacing(4)

        planned_header_layout = QHBoxLayout()
        planned_label = QLabel("Planned Amount")
        planned_label.setFont(QFont("Arial", 9))
        planned_label.setStyleSheet("color: #666666; font-weight: bold;")
        planned_header_layout.addWidget(planned_label)

        # Edit button for planned amount
        planned_edit_btn = QPushButton("✏️")
        planned_edit_btn.setFixedSize(20, 20)
        planned_edit_btn.setToolTip("Click to edit planned amount")
        planned_edit_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #ddd;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2196f3;
                color: white;
            }
        """)
        planned_header_layout.addWidget(planned_edit_btn)
        planned_header_layout.addStretch()
        planned_section.addLayout(planned_header_layout)

        planned_spinbox = QDoubleSpinBox()
        planned_spinbox.setRange(0.0, 50000.0)
        planned_spinbox.setValue(category.planned_amount)
        planned_spinbox.setPrefix("₹ ")
        planned_spinbox.setReadOnly(True)  # Start in read-only mode
        planned_spinbox.setButtonSymbols(QDoubleSpinBox.NoButtons)  # Hide spin buttons
        planned_spinbox.valueChanged.connect(self.update_totals)
        planned_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #2196f3;
            }
            QDoubleSpinBox[readOnly="true"] {
                color: #666;
            }
        """)
        # Disable mouse wheel events to prevent accidental changes
        planned_spinbox.wheelEvent = lambda event: None
        planned_section.addWidget(planned_spinbox)
        amounts_layout.addLayout(planned_section)

        # Actual amount section with edit protection
        actual_section = QVBoxLayout()
        actual_section.setSpacing(4)

        actual_header_layout = QHBoxLayout()
        actual_label = QLabel("Actual Amount")
        actual_label.setFont(QFont("Arial", 9))
        actual_label.setStyleSheet("color: #666666; font-weight: bold;")
        actual_header_layout.addWidget(actual_label)

        # Edit button for actual amount
        actual_edit_btn = QPushButton("✏️")
        actual_edit_btn.setFixedSize(20, 20)
        actual_edit_btn.setToolTip("Click to edit actual amount")
        actual_edit_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #ddd;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2196f3;
                color: white;
            }
        """)
        actual_header_layout.addWidget(actual_edit_btn)
        actual_header_layout.addStretch()
        actual_section.addLayout(actual_header_layout)

        actual_spinbox = QDoubleSpinBox()
        actual_spinbox.setRange(0.0, 50000.0)
        actual_spinbox.setValue(category.actual_amount)
        actual_spinbox.setPrefix("₹ ")
        actual_spinbox.setReadOnly(True)  # Start in read-only mode
        actual_spinbox.setButtonSymbols(QDoubleSpinBox.NoButtons)  # Hide spin buttons
        actual_spinbox.valueChanged.connect(self.update_totals)
        actual_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #2196f3;
            }
            QDoubleSpinBox[readOnly="true"] {
                color: #666;
            }
        """)
        # Disable mouse wheel events to prevent accidental changes
        actual_spinbox.wheelEvent = lambda event: None
        actual_section.addWidget(actual_spinbox)
        amounts_layout.addLayout(actual_section)

        main_layout.addLayout(amounts_layout)

        # Progress section
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(4)

        # Progress label with percentage
        progress_percentage = 0
        if category.planned_amount > 0:
            progress_percentage = min(100, int((category.actual_amount / category.planned_amount) * 100))

        progress_label = QLabel(f"Progress: {progress_percentage}%")
        progress_label.setFont(QFont("Arial", 9))
        progress_label.setStyleSheet("color: #666666; font-weight: bold;")
        progress_layout.addWidget(progress_label)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(progress_percentage)
        progress_bar.setFixedHeight(8)

        # Color-code progress bar based on percentage
        if progress_percentage <= 50:
            progress_color = "#4caf50"  # Green for low usage
        elif progress_percentage <= 80:
            progress_color = "#ff9800"  # Orange for moderate usage
        else:
            progress_color = "#f44336"  # Red for high usage

        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {progress_color};
                border-radius: 3px;
            }}
        """)
        progress_layout.addWidget(progress_bar)

        main_layout.addLayout(progress_layout)

        # Connect edit buttons
        planned_edit_btn.clicked.connect(lambda: self.toggle_edit_mode(category.name, 'planned'))
        actual_edit_btn.clicked.connect(lambda: self.toggle_edit_mode(category.name, 'actual'))

        # Store references including edit buttons
        self.category_widgets[category.name] = {
            'widget': card,
            'planned_spinbox': planned_spinbox,
            'actual_spinbox': actual_spinbox,
            'planned_edit_btn': planned_edit_btn,
            'actual_edit_btn': actual_edit_btn,
            'progress_bar': progress_bar,
            'progress_label': progress_label,
            'category': category,
            'planned_editing': False,
            'actual_editing': False
        }

        return card

    def toggle_edit_mode(self, category_name: str, field_type: str):
        """Toggle edit mode for planned or actual amount fields"""
        if category_name not in self.category_widgets:
            return

        widget_data = self.category_widgets[category_name]

        if field_type == 'planned':
            spinbox = widget_data['planned_spinbox']
            edit_btn = widget_data['planned_edit_btn']
            editing_key = 'planned_editing'
        else:  # actual
            spinbox = widget_data['actual_spinbox']
            edit_btn = widget_data['actual_edit_btn']
            editing_key = 'actual_editing'

        is_editing = widget_data[editing_key]

        if not is_editing:
            # Enter edit mode
            spinbox.setReadOnly(False)
            spinbox.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
            spinbox.setStyleSheet("""
                QDoubleSpinBox {
                    border: 2px solid #2196f3;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 11px;
                }
            """)
            edit_btn.setText("💾")
            edit_btn.setToolTip("Click to save changes")
            edit_btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #4caf50;
                    border-radius: 3px;
                    background-color: #4caf50;
                    color: white;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            spinbox.setFocus()
            spinbox.selectAll()
            widget_data[editing_key] = True
        else:
            # Exit edit mode and save
            spinbox.setReadOnly(True)
            spinbox.setButtonSymbols(QDoubleSpinBox.NoButtons)
            spinbox.setStyleSheet("""
                QDoubleSpinBox {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 11px;
                    color: #666;
                }
            """)
            edit_btn.setText("✏️")
            edit_btn.setToolTip(f"Click to edit {field_type} amount")
            edit_btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #2196f3;
                    color: white;
                }
            """)
            widget_data[editing_key] = False

            # Update the category data and save to database
            category = widget_data['category']
            if field_type == 'planned':
                category.planned_amount = spinbox.value()
            else:
                category.actual_amount = spinbox.value()

            # Save to database
            self.save_category_to_database(category_name, category)

            # Update totals
            self.update_totals()

    def save_category_to_database(self, category_name: str, category):
        """Save category changes to database using comprehensive ID management"""
        try:
            categories_df = self.budget_model.get_all_budget_categories()
            category_row = categories_df[categories_df['name'] == category_name]

            if not category_row.empty:
                category_id = category_row.iloc[0]['id']

                # Use the ID manager for validation
                if not self.budget_model.id_manager.validate_id(category_id):
                    self.logger.warning(f"Invalid category ID for {category_name}: {category_id}")

                    # Try to assign a new valid ID
                    self.logger.info(f"Attempting to assign new ID for category {category_name}")
                    result = self.budget_model.assign_missing_ids()

                    if result['success'] and result['ids_assigned'] > 0:
                        # Reload category data to get new ID
                        categories_df = self.budget_model.get_all_budget_categories()
                        category_row = categories_df[categories_df['name'] == category_name]

                        if not category_row.empty:
                            category_id = category_row.iloc[0]['id']
                            self.logger.info(f"Assigned new ID {category_id} to category {category_name}")
                        else:
                            QMessageBox.warning(self, "Error", f"Could not find category {category_name} after ID assignment")
                            return
                    else:
                        QMessageBox.warning(self, "Error", f"Could not assign valid ID to category {category_name}")
                        return

                # Convert to int to ensure proper type
                try:
                    category_id = int(float(category_id))
                except (ValueError, TypeError):
                    self.logger.error(f"Cannot convert category ID to integer: {category_id}")
                    QMessageBox.warning(self, "Error", f"Invalid category ID format for {category_name}")
                    return

                # Update category using the enhanced method
                if self.budget_model.update_budget_category(category_id, category):
                    # Show brief success indication
                    widget_data = self.category_widgets[category_name]
                    card = widget_data['widget']
                    original_style = card.styleSheet()
                    card.setStyleSheet(original_style + """
                        QFrame {
                            border: 2px solid #4caf50;
                        }
                    """)
                    # Reset style after 1 second
                    QTimer.singleShot(1000, lambda: card.setStyleSheet(original_style))

                    self.logger.info(f"Successfully saved category {category_name} with ID {category_id}")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to save changes for {category_name}")
            else:
                self.logger.warning(f"Category {category_name} not found in database")
                QMessageBox.warning(self, "Warning", f"Category {category_name} not found in database")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving category: {str(e)}")
            self.logger.error(f"Error saving category {category_name}: {e}")

    def refresh_income_integration(self):
        """Refresh income integration for budget categories"""
        if not self.income_model:
            return

        try:
            # Get current month's total income
            current_month_income = self.get_current_month_income()

            # Update budget categories with cumulative achievement logic
            self.update_budget_achievements(current_month_income)

        except Exception as e:
            self.logger.error(f"Error refreshing income integration: {e}")

    def get_current_month_income(self) -> float:
        """Get total income for current month"""
        if not self.income_model:
            return 0.0

        try:
            from datetime import date
            current_month = date.today().replace(day=1)
            monthly_summary = self.income_model.get_monthly_summary(current_month)
            return monthly_summary.get('total_earned', 0.0)
        except Exception as e:
            self.logger.error(f"Error getting current month income: {e}")
            return 0.0

    def update_budget_achievements(self, total_income: float):
        """Update budget categories with progressive achievement system"""
        try:
            # Sort categories by planned amount (ascending) for cumulative logic
            sorted_categories = sorted(
                self.category_widgets.items(),
                key=lambda x: x[1]['category'].planned_amount
            )

            cumulative_target = 0.0

            for category_name, widget_data in sorted_categories:
                category = widget_data['category']
                planned_amount = category.planned_amount

                # Calculate cumulative target
                cumulative_target += planned_amount

                # Determine achievement amount for this category
                if total_income >= cumulative_target:
                    # Fully achieved
                    achievement_amount = planned_amount
                elif total_income > (cumulative_target - planned_amount):
                    # Partially achieved
                    achievement_amount = total_income - (cumulative_target - planned_amount)
                else:
                    # Not achieved
                    achievement_amount = 0.0

                # Update actual amount in the widget (but don't save to database automatically)
                actual_spinbox = widget_data['actual_spinbox']
                if not widget_data.get('actual_editing', False):  # Only update if not being edited
                    actual_spinbox.setValue(achievement_amount)

                # Update category object
                category.actual_amount = achievement_amount

                # Update progress display
                self.update_category_progress(category_name, widget_data)

        except Exception as e:
            self.logger.error(f"Error updating budget achievements: {e}")

    def update_category_progress(self, category_name: str, widget_data: dict):
        """Update progress display for a specific category"""
        try:
            category = widget_data['category']
            planned = category.planned_amount
            actual = category.actual_amount

            if planned > 0:
                progress_percentage = min(100, int((actual / planned) * 100))
            else:
                progress_percentage = 0

            # Update progress bar
            progress_bar = widget_data['progress_bar']
            progress_bar.setValue(progress_percentage)

            # Update progress label if it exists
            if 'progress_label' in widget_data:
                progress_label = widget_data['progress_label']
                progress_label.setText(f"Progress: {progress_percentage}% (Auto-updated from income)")

            # Color-code progress bar
            if progress_percentage >= 100:
                color = "#4caf50"  # Green for achieved
            elif progress_percentage >= 80:
                color = "#ff9800"  # Orange for close
            else:
                color = "#f44336"  # Red for far from target

            progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)

        except Exception as e:
            self.logger.error(f"Error updating category progress for {category_name}: {e}")

    def load_categories(self):
        """Load and display budget categories with improved layout"""
        try:
            categories_df = self.budget_model.get_all_budget_categories()

            # Clear existing widgets
            for category_name in list(self.category_widgets.keys()):
                self.remove_category_widget(category_name)

            if categories_df.empty:
                # Show empty state message
                empty_label = QLabel("No budget categories found.\nClick 'Add Category' to get started.")
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setStyleSheet("""
                    QLabel {
                        color: #666666;
                        font-size: 14px;
                        padding: 40px;
                        border: 2px dashed #dee2e6;
                        border-radius: 8px;
                    }
                """)
                # Insert before the stretch
                self.categories_layout.insertWidget(0, empty_label)
                self.update_totals()
                return

            # Create widgets for each category
            # Sort categories: essential first, then by name
            sorted_categories = sorted(
                categories_df.iterrows(),
                key=lambda x: (not x[1].get('is_essential', False), x[1]['name'])
            )

            for _, row in sorted_categories:
                category = BudgetCategory.from_dict(row.to_dict())
                widget = self.create_category_widget(category)
                # Insert before the stretch (which is always the last item)
                self.categories_layout.insertWidget(self.categories_layout.count() - 1, widget)

            self.update_totals()

        except Exception as e:
            self.logger.error(f"Error loading categories: {e}")

    def update_totals(self):
        """Update total planned, actual, and remaining amounts"""
        try:
            total_planned = 0.0
            total_actual = 0.0

            for category_data in self.category_widgets.values():
                planned = category_data['planned_spinbox'].value()
                actual = category_data['actual_spinbox'].value()

                total_planned += planned
                total_actual += actual

                # Update progress bar and label
                if planned > 0:
                    progress = min(100, int((actual / planned) * 100))
                    category_data['progress_bar'].setValue(progress)

                    # Update progress label if it exists
                    if 'progress_label' in category_data:
                        category_data['progress_label'].setText(f"Progress: {progress}%")

                    # Enhanced color coding with better styling
                    if progress <= 50:
                        progress_color = "#4caf50"  # Green for low usage
                    elif progress <= 80:
                        progress_color = "#ff9800"  # Orange for moderate usage
                    else:
                        progress_color = "#f44336"  # Red for high usage

                    category_data['progress_bar'].setStyleSheet(f"""
                        QProgressBar {{
                            border: 1px solid #ddd;
                            border-radius: 4px;
                            text-align: center;
                        }}
                        QProgressBar::chunk {{
                            background-color: {progress_color};
                            border-radius: 3px;
                        }}
                    """)
                else:
                    # Handle zero planned amount
                    category_data['progress_bar'].setValue(0)
                    if 'progress_label' in category_data:
                        category_data['progress_label'].setText("Progress: 0%")

            remaining = total_planned - total_actual

            # Update labels
            self.planned_label.setText(f"Planned: ₹{total_planned:,.0f}")
            self.actual_label.setText(f"Actual: ₹{total_actual:,.0f}")
            self.remaining_label.setText(f"Remaining: ₹{remaining:,.0f}")

            # Update total budget label
            self.total_budget_label.setText(f"Total Budget: ₹{total_planned:,.0f}")

            # Color coding for remaining
            if remaining < 0:
                self.remaining_label.setStyleSheet("color: #f44336; font-weight: bold;")
            elif remaining < 1000:
                self.remaining_label.setStyleSheet("color: #ff9800; font-weight: bold;")
            else:
                self.remaining_label.setStyleSheet("color: #2e7d32; font-weight: bold;")

        except Exception as e:
            self.logger.error(f"Error updating totals: {e}")

    def add_custom_category(self):
        """Add a custom budget category"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Budget Category")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # Category name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Category Name:"))
        name_edit = QLineEdit()
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)

        # Planned amount
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("Planned Amount:"))
        amount_spinbox = QDoubleSpinBox()
        amount_spinbox.setRange(0.0, 50000.0)
        amount_spinbox.setPrefix("₹ ")
        amount_layout.addWidget(amount_spinbox)
        layout.addLayout(amount_layout)

        # Essential checkbox
        essential_checkbox = QCheckBox("Essential Category")
        layout.addWidget(essential_checkbox)

        # Description
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        desc_edit = QTextEdit()
        desc_edit.setMaximumHeight(60)
        desc_layout.addWidget(desc_edit)
        layout.addLayout(desc_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            name = name_edit.text().strip()
            if name and name not in self.category_widgets:
                category = BudgetCategory(
                    name=name,
                    category_type=CategoryType.EXPENSE.value,
                    planned_amount=amount_spinbox.value(),
                    description=desc_edit.toPlainText(),
                    is_essential=essential_checkbox.isChecked()
                )

                # Add to database
                if self.budget_model.add_budget_category(category):
                    # Add to UI - insert before the stretch (which is always the last item)
                    widget = self.create_category_widget(category)
                    self.categories_layout.insertWidget(self.categories_layout.count() - 1, widget)
                    self.update_totals()

                    # Show success message
                    QMessageBox.information(
                        self,
                        "Category Added",
                        f"Budget category '{name}' has been successfully added."
                    )
                else:
                    QMessageBox.critical(self, "Error", "Failed to add category. Please try again.")
            elif name in self.category_widgets:
                QMessageBox.warning(self, "Error", "Category already exists")

    def remove_category(self, category_name: str):
        """Remove a budget category with enhanced confirmation dialog"""
        # Get category details for confirmation
        category_data = self.category_widgets.get(category_name)
        if not category_data:
            return

        category = category_data['category']
        planned_amount = category_data['planned_spinbox'].value()
        actual_amount = category_data['actual_spinbox'].value()

        # Create detailed confirmation message
        message = f"""Are you sure you want to delete the budget category '{category_name}'?

Category Details:
• Planned Amount: ₹{planned_amount:,.2f}
• Actual Amount: ₹{actual_amount:,.2f}
• Essential Category: {'Yes' if category.is_essential else 'No'}

This action cannot be undone."""

        # Create custom message box with warning icon
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Delete Budget Category")
        msg_box.setText("Delete Budget Category?")
        msg_box.setInformativeText(message)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        # Style the message box
        msg_box.setStyleSheet("""
            QMessageBox QLabel {
                color: #333333;
            }
        """)

        reply = msg_box.exec()

        if reply == QMessageBox.Yes:
            # Remove from database
            categories_df = self.budget_model.get_all_budget_categories()
            category_row = categories_df[categories_df['name'] == category_name]

            if not category_row.empty:
                category_id = category_row.iloc[0]['id']

                # Validate category_id
                if pd.isna(category_id) or category_id is None or category_id == '':
                    self.logger.warning(f"Invalid category ID for {category_name}, removing from UI only")
                    self.remove_category_widget(category_name)
                    self.update_totals()
                    QMessageBox.warning(
                        self,
                        "Category Removed",
                        f"Category '{category_name}' removed from display (had invalid database ID)."
                    )
                    return

                try:
                    category_id = int(float(category_id))  # Handle potential float conversion
                    if self.budget_model.delete_budget_category(category_id):
                        self.remove_category_widget(category_name)
                        self.update_totals()

                        # Show success message
                        QMessageBox.information(
                            self,
                            "Category Deleted",
                            f"Budget category '{category_name}' has been successfully deleted."
                        )
                    else:
                        QMessageBox.critical(
                            self,
                            "Delete Failed",
                            f"Failed to delete category '{category_name}'. Please try again."
                        )
                except (ValueError, TypeError):
                    self.logger.error(f"Cannot convert category ID to integer: {category_id}")
                    QMessageBox.critical(
                        self,
                        "Delete Failed",
                        f"Invalid category ID format for '{category_name}'. Cannot delete."
                    )
            else:
                self.logger.warning(f"Category {category_name} not found in database")
                # Remove from UI anyway since it's not in database
                self.remove_category_widget(category_name)
                self.update_totals()
                QMessageBox.warning(
                    self,
                    "Category Removed",
                    f"Category '{category_name}' was not found in database but removed from display."
                )

    def remove_category_widget(self, category_name: str):
        """Remove category widget from UI and handle empty state"""
        if category_name in self.category_widgets:
            widget_data = self.category_widgets[category_name]
            widget_data['widget'].setParent(None)
            del self.category_widgets[category_name]

            # If no categories left, show empty state
            if not self.category_widgets:
                empty_label = QLabel("No budget categories found.\nClick 'Add Category' to get started.")
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setStyleSheet("""
                    QLabel {
                        color: #666666;
                        font-size: 14px;
                        padding: 40px;
                        border: 2px dashed #dee2e6;
                        border-radius: 8px;
                    }
                """)
                # Insert before the stretch
                self.categories_layout.insertWidget(0, empty_label)

    def save_budget(self):
        """Save current budget settings with proper ID validation"""
        try:
            saved_count = 0
            failed_count = 0

            # Update all categories with current values
            for category_name, widget_data in self.category_widgets.items():
                category = widget_data['category']
                category.planned_amount = widget_data['planned_spinbox'].value()
                category.actual_amount = widget_data['actual_spinbox'].value()

                # Update in database with validation
                categories_df = self.budget_model.get_all_budget_categories()
                category_row = categories_df[categories_df['name'] == category_name]

                if not category_row.empty:
                    category_id = category_row.iloc[0]['id']

                    # Validate category_id
                    if pd.isna(category_id) or category_id is None or category_id == '':
                        self.logger.warning(f"Invalid category ID for {category_name}, skipping")
                        failed_count += 1
                        continue

                    try:
                        category_id = int(float(category_id))  # Handle potential float conversion
                        if self.budget_model.update_budget_category(category_id, category):
                            saved_count += 1
                        else:
                            failed_count += 1
                    except (ValueError, TypeError):
                        self.logger.error(f"Cannot convert category ID to integer: {category_id}")
                        failed_count += 1
                else:
                    self.logger.warning(f"Category {category_name} not found in database")
                    failed_count += 1

            # Show appropriate message based on results
            if failed_count == 0:
                QMessageBox.information(self, "Success", f"Budget saved successfully! ({saved_count} categories updated)")
            elif saved_count > 0:
                QMessageBox.warning(self, "Partial Success",
                                  f"Budget partially saved: {saved_count} categories updated, {failed_count} failed")
            else:
                QMessageBox.critical(self, "Error", "Failed to save any budget categories")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save budget: {str(e)}")
            self.logger.error(f"Error saving budget: {e}")

    def reset_budget(self):
        """Reset budget to default values"""
        reply = QMessageBox.question(
            self,
            "Reset Budget",
            "Are you sure you want to reset all budget values to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for widget_data in self.category_widgets.values():
                widget_data['actual_spinbox'].setValue(0.0)
            self.update_totals()


class BudgetSummaryWidget(QFrame):
    """Widget for displaying budget summary"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the summary UI"""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        
        layout = QGridLayout(self)
        
        # Title
        title_label = QLabel("💰 Budget Overview")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label, 0, 0, 1, 4)
        
        # Summary metrics
        self.total_plans_label = QLabel("Total Plans: 0")
        layout.addWidget(self.total_plans_label, 1, 0)
        
        self.active_plans_label = QLabel("Active Plans: 0")
        layout.addWidget(self.active_plans_label, 1, 1)
        
        self.health_score_label = QLabel("Avg Health Score: 0%")
        layout.addWidget(self.health_score_label, 1, 2)
        
        self.on_track_label = QLabel("Plans On Track: 0")
        layout.addWidget(self.on_track_label, 1, 3)
        
        # Financial metrics
        self.planned_income_label = QLabel("Planned Income: ₹0.00")
        layout.addWidget(self.planned_income_label, 2, 0)
        
        self.actual_income_label = QLabel("Actual Income: ₹0.00")
        layout.addWidget(self.actual_income_label, 2, 1)
        
        self.planned_expenses_label = QLabel("Planned Expenses: ₹0.00")
        layout.addWidget(self.planned_expenses_label, 2, 2)
        
        self.actual_expenses_label = QLabel("Actual Expenses: ₹0.00")
        layout.addWidget(self.actual_expenses_label, 2, 3)
    
    def update_summary(self, summary: Dict[str, Any]):
        """Update summary display"""
        self.total_plans_label.setText(f"Total Plans: {summary['total_plans']}")
        self.active_plans_label.setText(f"Active Plans: {summary['active_plans']}")
        
        health_score = summary['average_health_score']
        health_color = "#28a745" if health_score >= 80 else "#ffc107" if health_score >= 60 else "#dc3545"
        self.health_score_label.setText(f"Avg Health Score: {health_score:.1f}%")
        self.health_score_label.setStyleSheet(f"color: {health_color}; font-weight: bold;")
        
        self.on_track_label.setText(f"Plans On Track: {summary['plans_on_track']}")
        
        self.planned_income_label.setText(f"Planned Income: ₹{summary['total_planned_income']:,.2f}")
        self.actual_income_label.setText(f"Actual Income: ₹{summary['total_actual_income']:,.2f}")
        self.planned_expenses_label.setText(f"Planned Expenses: ₹{summary['total_planned_expenses']:,.2f}")
        self.actual_expenses_label.setText(f"Actual Expenses: ₹{summary['total_actual_expenses']:,.2f}")


class BudgetPlanTableWidget(QTableWidget):
    """Table widget for displaying budget plans"""
    
    plan_selected = Signal(int)  # Emits plan ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
    
    def setup_table(self):
        """Setup the table"""
        # Define columns
        self.columns = [
            'Name', 'Type', 'Period Start', 'Period End', 'Planned Income',
            'Actual Income', 'Planned Expenses', 'Actual Expenses',
            'Health Score', 'On Track'
        ]
        
        self.setColumnCount(len(self.columns))
        self.setHorizontalHeaderLabels(self.columns)
        
        # Table settings
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # Resize columns
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(len(self.columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Connect selection
        self.itemSelectionChanged.connect(self.on_selection_changed)
    
    def update_plans(self, df: pd.DataFrame):
        """Update table with budget plan data"""
        self.setRowCount(len(df))
        
        for row_idx, (_, row) in enumerate(df.iterrows()):
            # Name
            self.setItem(row_idx, 0, QTableWidgetItem(str(row['name'])))
            
            # Type
            self.setItem(row_idx, 1, QTableWidgetItem(str(row['budget_type'])))
            
            # Period Start
            self.setItem(row_idx, 2, QTableWidgetItem(str(row['period_start'])))
            
            # Period End
            self.setItem(row_idx, 3, QTableWidgetItem(str(row['period_end'])))
            
            # Planned Income
            self.setItem(row_idx, 4, QTableWidgetItem(f"₹{row['total_income_planned']:,.2f}"))
            
            # Actual Income
            self.setItem(row_idx, 5, QTableWidgetItem(f"₹{row['total_income_actual']:,.2f}"))
            
            # Planned Expenses
            self.setItem(row_idx, 6, QTableWidgetItem(f"₹{row['total_expenses_planned']:,.2f}"))
            
            # Actual Expenses
            self.setItem(row_idx, 7, QTableWidgetItem(f"₹{row['total_expenses_actual']:,.2f}"))
            
            # Health Score
            health_score = row['budget_health_score']
            health_item = QTableWidgetItem(f"{health_score:.1f}%")
            health_color = "#28a745" if health_score >= 80 else "#ffc107" if health_score >= 60 else "#dc3545"
            health_item.setForeground(QColor(health_color))
            self.setItem(row_idx, 8, health_item)
            
            # On Track
            on_track = "✅ Yes" if row['is_on_track'] else "❌ No"
            on_track_item = QTableWidgetItem(on_track)
            on_track_color = "#28a745" if row['is_on_track'] else "#dc3545"
            on_track_item.setForeground(QColor(on_track_color))
            self.setItem(row_idx, 9, on_track_item)
            
            # Store plan ID in first column
            self.item(row_idx, 0).setData(Qt.UserRole, row['id'])
    
    def on_selection_changed(self):
        """Handle selection change"""
        current_row = self.currentRow()
        if current_row >= 0:
            item = self.item(current_row, 0)
            if item:
                plan_id = item.data(Qt.UserRole)
                if plan_id:
                    self.plan_selected.emit(plan_id)


class BudgetPlanEditDialog(QDialog):
    """Dialog for editing budget plans"""
    
    def __init__(self, plan: BudgetPlan = None, parent=None):
        super().__init__(parent)
        self.plan = plan or BudgetPlan()
        self.setup_ui()
        self.populate_fields()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Edit Budget Plan")
        self.setModal(True)
        self.resize(600, 700)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., January 2024 Budget")
        form_layout.addRow("Plan Name:", self.name_edit)
        
        # Budget Type
        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in BudgetType])
        form_layout.addRow("Budget Type:", self.type_combo)
        
        # Period dates
        period_layout = QHBoxLayout()
        self.period_start_edit = QDateEdit()
        self.period_start_edit.setCalendarPopup(True)
        self.period_start_edit.setDate(QDate.currentDate())
        period_layout.addWidget(self.period_start_edit)
        
        period_layout.addWidget(QLabel("to"))
        
        self.period_end_edit = QDateEdit()
        self.period_end_edit.setCalendarPopup(True)
        self.period_end_edit.setDate(QDate.currentDate().addDays(30))
        period_layout.addWidget(self.period_end_edit)
        
        form_layout.addRow("Period:", period_layout)
        
        # Income section
        income_group = QGroupBox("Income")
        income_layout = QFormLayout(income_group)
        
        self.planned_income_spin = QDoubleSpinBox()
        self.planned_income_spin.setRange(0, 9999999)
        self.planned_income_spin.setPrefix("₹")
        income_layout.addRow("Planned Income:", self.planned_income_spin)
        
        self.actual_income_spin = QDoubleSpinBox()
        self.actual_income_spin.setRange(0, 9999999)
        self.actual_income_spin.setPrefix("₹")
        income_layout.addRow("Actual Income:", self.actual_income_spin)
        
        layout.addWidget(income_group)
        
        # Expenses section
        expenses_group = QGroupBox("Expenses")
        expenses_layout = QFormLayout(expenses_group)
        
        self.planned_expenses_spin = QDoubleSpinBox()
        self.planned_expenses_spin.setRange(0, 9999999)
        self.planned_expenses_spin.setPrefix("₹")
        expenses_layout.addRow("Planned Expenses:", self.planned_expenses_spin)
        
        self.actual_expenses_spin = QDoubleSpinBox()
        self.actual_expenses_spin.setRange(0, 9999999)
        self.actual_expenses_spin.setPrefix("₹")
        expenses_layout.addRow("Actual Expenses:", self.actual_expenses_spin)
        
        layout.addWidget(expenses_group)
        
        # Savings section
        savings_group = QGroupBox("Savings")
        savings_layout = QFormLayout(savings_group)
        
        self.planned_savings_spin = QDoubleSpinBox()
        self.planned_savings_spin.setRange(0, 9999999)
        self.planned_savings_spin.setPrefix("₹")
        savings_layout.addRow("Planned Savings:", self.planned_savings_spin)
        
        self.actual_savings_spin = QDoubleSpinBox()
        self.actual_savings_spin.setRange(0, 9999999)
        self.actual_savings_spin.setPrefix("₹")
        savings_layout.addRow("Actual Savings:", self.actual_savings_spin)
        
        layout.addWidget(savings_group)
        
        layout.addLayout(form_layout)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Additional notes about this budget plan...")
        form_layout.addRow("Notes:", self.notes_edit)
        
        # Calculated fields (read-only)
        calc_group = QGroupBox("Calculated Metrics")
        calc_layout = QFormLayout(calc_group)
        
        self.net_income_label = QLabel("₹0.00")
        calc_layout.addRow("Net Income:", self.net_income_label)
        
        self.savings_rate_label = QLabel("0.00%")
        calc_layout.addRow("Savings Rate:", self.savings_rate_label)
        
        self.health_score_label = QLabel("0.0")
        calc_layout.addRow("Health Score:", self.health_score_label)
        
        layout.addWidget(calc_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect value changes to update calculations
        for spin in [self.planned_income_spin, self.actual_income_spin, 
                    self.planned_expenses_spin, self.actual_expenses_spin,
                    self.planned_savings_spin, self.actual_savings_spin]:
            spin.valueChanged.connect(self.update_calculations)
    
    def populate_fields(self):
        """Populate fields with plan data"""
        self.name_edit.setText(self.plan.name)
        self.type_combo.setCurrentText(self.plan.budget_type)
        
        if self.plan.period_start:
            self.period_start_edit.setDate(QDate.fromString(str(self.plan.period_start), "yyyy-MM-dd"))
        if self.plan.period_end:
            self.period_end_edit.setDate(QDate.fromString(str(self.plan.period_end), "yyyy-MM-dd"))
        
        self.planned_income_spin.setValue(self.plan.total_income_planned)
        self.actual_income_spin.setValue(self.plan.total_income_actual)
        self.planned_expenses_spin.setValue(self.plan.total_expenses_planned)
        self.actual_expenses_spin.setValue(self.plan.total_expenses_actual)
        self.planned_savings_spin.setValue(self.plan.total_savings_planned)
        self.actual_savings_spin.setValue(self.plan.total_savings_actual)
        
        self.notes_edit.setPlainText(self.plan.notes)
        
        self.update_calculations()
    
    def update_calculations(self):
        """Update calculated fields"""
        planned_income = self.planned_income_spin.value()
        actual_income = self.actual_income_spin.value()
        planned_expenses = self.planned_expenses_spin.value()
        actual_expenses = self.actual_expenses_spin.value()
        planned_savings = self.planned_savings_spin.value()
        actual_savings = self.actual_savings_spin.value()
        
        # Update plan object for calculations
        self.plan.total_income_planned = planned_income
        self.plan.total_income_actual = actual_income
        self.plan.total_expenses_planned = planned_expenses
        self.plan.total_expenses_actual = actual_expenses
        self.plan.total_savings_planned = planned_savings
        self.plan.total_savings_actual = actual_savings
        
        # Calculate metrics
        net_income = self.plan.get_net_income_actual()
        savings_rate = self.plan.get_savings_rate_actual()
        health_score = self.plan.get_budget_health_score()
        
        self.net_income_label.setText(f"₹{net_income:,.2f}")
        self.savings_rate_label.setText(f"{savings_rate:.2f}%")
        
        # Color code health score
        health_color = "#28a745" if health_score >= 80 else "#ffc107" if health_score >= 60 else "#dc3545"
        self.health_score_label.setText(f"{health_score:.1f}")
        self.health_score_label.setStyleSheet(f"color: {health_color}; font-weight: bold;")
    
    def get_budget_plan(self) -> BudgetPlan:
        """Get the budget plan from form data"""
        self.plan.name = self.name_edit.text().strip()
        self.plan.budget_type = self.type_combo.currentText()
        self.plan.period_start = self.period_start_edit.date().toPython()
        self.plan.period_end = self.period_end_edit.date().toPython()
        self.plan.total_income_planned = self.planned_income_spin.value()
        self.plan.total_income_actual = self.actual_income_spin.value()
        self.plan.total_expenses_planned = self.planned_expenses_spin.value()
        self.plan.total_expenses_actual = self.actual_expenses_spin.value()
        self.plan.total_savings_planned = self.planned_savings_spin.value()
        self.plan.total_savings_actual = self.actual_savings_spin.value()
        self.plan.notes = self.notes_edit.toPlainText().strip()
        self.plan.updated_at = datetime.now()
        
        return self.plan


class BudgetPlannerWidget(QWidget):
    """Main budget planner widget"""

    def __init__(self, data_manager, config, parent=None):
        super().__init__(parent)

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("="*50)
        self.logger.info("INITIALIZING BUDGET PLANNER WIDGET")
        self.logger.info("="*50)

        try:
            self.data_manager = data_manager
            self.config = config
            self.budget_model = BudgetDataModel(data_manager)

            self.setup_ui()
            self.setup_connections()
            self.refresh_data()

            self.logger.info("✅ BudgetPlannerWidget initialization SUCCESSFUL")

        except Exception as e:
            self.logger.error(f"❌ CRITICAL ERROR in BudgetPlannerWidget.__init__: {e}")
            raise

    def setup_ui(self):
        """Setup the main UI with tabs"""
        layout = QVBoxLayout(self)

        # Create tab widget for budget sections
        self.tab_widget = QTabWidget()

        # Main budget tab
        main_budget_tab = QWidget()
        main_budget_layout = QVBoxLayout(main_budget_tab)

        # Use the simplified budget widget with income integration
        self.simplified_budget_widget = SimplifiedBudgetWidget(self.budget_model, self.data_manager)
        main_budget_layout.addWidget(self.simplified_budget_widget)

        self.tab_widget.addTab(main_budget_tab, "💰 Budget Categories")

        # Achievement History tab
        self.achievement_history_tab = self.create_achievement_history_tab()
        self.tab_widget.addTab(self.achievement_history_tab, "🏆 Achievement History")

        layout.addWidget(self.tab_widget)

    def create_achievement_history_tab(self):
        """Create the achievement history tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🏆 Budget Achievement History")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_achievement_history)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Achievement summary cards
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)

        # Current month achievement
        self.current_month_card = self.create_achievement_card("Current Month", "0%", "#2196f3")
        summary_layout.addWidget(self.current_month_card)

        # Best month achievement
        self.best_month_card = self.create_achievement_card("Best Month", "0%", "#4caf50")
        summary_layout.addWidget(self.best_month_card)

        # Average achievement
        self.avg_achievement_card = self.create_achievement_card("Average", "0%", "#ff9800")
        summary_layout.addWidget(self.avg_achievement_card)

        # Total categories achieved
        self.total_achieved_card = self.create_achievement_card("Categories Achieved", "0", "#9c27b0")
        summary_layout.addWidget(self.total_achieved_card)

        layout.addWidget(summary_frame)

        # Achievement history table
        history_group = QGroupBox("Monthly Achievement History")
        history_layout = QVBoxLayout(history_group)

        self.achievement_table = QTableWidget()
        self.achievement_table.setColumnCount(6)
        self.achievement_table.setHorizontalHeaderLabels([
            "Month", "Total Income", "Categories Achieved", "Achievement %", "Best Category", "Status"
        ])
        self.achievement_table.horizontalHeader().setStretchLastSection(True)
        self.achievement_table.setAlternatingRowColors(True)
        self.achievement_table.setSortingEnabled(True)

        history_layout.addWidget(self.achievement_table)
        layout.addWidget(history_group)

        # Load initial data
        self.refresh_achievement_history()

        return tab

    def create_achievement_card(self, title: str, value: str, color: str):
        """Create an achievement summary card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
                min-width: 150px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {color};")
        layout.addWidget(title_label)

        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 18, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)

        # Store reference to value label for updates
        card.value_label = value_label

        return card

    def refresh_achievement_history(self):
        """Refresh achievement history data"""
        try:
            if not self.income_model:
                return

            # Get historical achievement data
            achievement_data = self.calculate_historical_achievements()

            # Update summary cards
            self.update_achievement_summary_cards(achievement_data)

            # Update achievement table
            self.update_achievement_table(achievement_data)

        except Exception as e:
            self.logger.error(f"Error refreshing achievement history: {e}")

    def calculate_historical_achievements(self):
        """Calculate historical achievement data"""
        try:
            from datetime import date, timedelta
            import calendar

            achievement_data = []
            current_date = date.today()

            # Get data for last 12 months
            for i in range(12):
                # Calculate month date
                if current_date.month - i <= 0:
                    month_year = current_date.year - 1
                    month_num = 12 + (current_date.month - i)
                else:
                    month_year = current_date.year
                    month_num = current_date.month - i

                month_date = date(month_year, month_num, 1)

                # Get monthly income
                monthly_summary = self.income_model.get_monthly_summary(month_date)
                total_income = monthly_summary.get('total_earned', 0.0)

                # Calculate achievements for this month
                month_achievements = self.calculate_month_achievements(total_income)

                achievement_data.append({
                    'month': month_date.strftime('%B %Y'),
                    'month_date': month_date,
                    'total_income': total_income,
                    'categories_achieved': month_achievements['categories_achieved'],
                    'achievement_percentage': month_achievements['achievement_percentage'],
                    'best_category': month_achievements['best_category'],
                    'status': month_achievements['status']
                })

            return achievement_data

        except Exception as e:
            self.logger.error(f"Error calculating historical achievements: {e}")
            return []

    def calculate_month_achievements(self, total_income: float):
        """Calculate achievements for a specific month's income"""
        try:
            # Get all budget categories sorted by planned amount
            categories = sorted(
                [(name, data['category']) for name, data in self.category_widgets.items()],
                key=lambda x: x[1].planned_amount
            )

            cumulative_target = 0.0
            categories_achieved = 0
            best_category = "None"
            best_achievement = 0.0

            for category_name, category in categories:
                planned_amount = category.planned_amount
                cumulative_target += planned_amount

                if total_income >= cumulative_target:
                    categories_achieved += 1
                    achievement_rate = 100.0
                    if achievement_rate > best_achievement:
                        best_achievement = achievement_rate
                        best_category = category_name
                elif total_income > (cumulative_target - planned_amount):
                    # Partial achievement
                    partial_achievement = ((total_income - (cumulative_target - planned_amount)) / planned_amount) * 100
                    if partial_achievement > best_achievement:
                        best_achievement = partial_achievement
                        best_category = f"{category_name} ({partial_achievement:.1f}%)"

            # Calculate overall achievement percentage
            total_budget = sum(cat[1].planned_amount for cat in categories)
            achievement_percentage = min(100.0, (total_income / total_budget * 100)) if total_budget > 0 else 0.0

            # Determine status
            if achievement_percentage >= 100:
                status = "🏆 Excellent"
            elif achievement_percentage >= 80:
                status = "✅ Good"
            elif achievement_percentage >= 60:
                status = "⚠️ Fair"
            else:
                status = "❌ Needs Improvement"

            return {
                'categories_achieved': categories_achieved,
                'achievement_percentage': achievement_percentage,
                'best_category': best_category,
                'status': status
            }

        except Exception as e:
            self.logger.error(f"Error calculating month achievements: {e}")
            return {
                'categories_achieved': 0,
                'achievement_percentage': 0.0,
                'best_category': "Error",
                'status': "❌ Error"
            }

    def update_achievement_summary_cards(self, achievement_data):
        """Update achievement summary cards"""
        try:
            if not achievement_data:
                return

            # Current month (first item in data)
            current_month = achievement_data[0]
            self.current_month_card.value_label.setText(f"{current_month['achievement_percentage']:.1f}%")

            # Best month
            best_month = max(achievement_data, key=lambda x: x['achievement_percentage'])
            self.best_month_card.value_label.setText(f"{best_month['achievement_percentage']:.1f}%")

            # Average achievement
            avg_achievement = sum(data['achievement_percentage'] for data in achievement_data) / len(achievement_data)
            self.avg_achievement_card.value_label.setText(f"{avg_achievement:.1f}%")

            # Total categories achieved (current month)
            total_categories = len(self.category_widgets)
            self.total_achieved_card.value_label.setText(f"{current_month['categories_achieved']}/{total_categories}")

        except Exception as e:
            self.logger.error(f"Error updating achievement summary cards: {e}")

    def update_achievement_table(self, achievement_data):
        """Update achievement history table"""
        try:
            self.achievement_table.setRowCount(len(achievement_data))

            for row, data in enumerate(achievement_data):
                # Month
                self.achievement_table.setItem(row, 0, QTableWidgetItem(data['month']))

                # Total Income
                income_item = QTableWidgetItem(f"₹{data['total_income']:,.2f}")
                income_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.achievement_table.setItem(row, 1, income_item)

                # Categories Achieved
                categories_item = QTableWidgetItem(f"{data['categories_achieved']}/{len(self.category_widgets)}")
                categories_item.setTextAlignment(Qt.AlignCenter)
                self.achievement_table.setItem(row, 2, categories_item)

                # Achievement %
                achievement_item = QTableWidgetItem(f"{data['achievement_percentage']:.1f}%")
                achievement_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                # Color code achievement percentage
                if data['achievement_percentage'] >= 100:
                    achievement_item.setBackground(QColor("#d4edda"))  # Light green
                elif data['achievement_percentage'] >= 80:
                    achievement_item.setBackground(QColor("#fff3cd"))  # Light yellow
                elif data['achievement_percentage'] >= 60:
                    achievement_item.setBackground(QColor("#ffeaa7"))  # Light orange
                else:
                    achievement_item.setBackground(QColor("#f8d7da"))  # Light red

                self.achievement_table.setItem(row, 3, achievement_item)

                # Best Category
                self.achievement_table.setItem(row, 4, QTableWidgetItem(data['best_category']))

                # Status
                status_item = QTableWidgetItem(data['status'])
                status_item.setTextAlignment(Qt.AlignCenter)
                self.achievement_table.setItem(row, 5, status_item)

        except Exception as e:
            self.logger.error(f"Error updating achievement table: {e}")

    def setup_connections(self):
        """Setup signal connections"""
        pass

    def refresh_data(self):
        """Refresh budget data and update display"""
        try:
            # Refresh the simplified budget widget
            self.simplified_budget_widget.load_categories()
        except Exception as e:
            self.logger.error(f"Error refreshing budget data: {e}")
