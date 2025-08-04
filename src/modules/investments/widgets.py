"""
Investment Portfolio UI Widgets
Contains all UI components for the investment tracking module
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QCheckBox, QFrame, QGroupBox, QScrollArea, QTabWidget,
    QProgressBar, QProgressDialog, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QButtonGroup, QDoubleSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QSplitter, QApplication
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QSize, QThread, QObject
from PySide6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import threading
import calendar
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import (
    Investment, InvestmentDataModel, InvestmentType,
    CurrentResource, AssetLiability, FinancialGoal, InsurancePolicy, LICPolicy,
    LoanDetails, LoanPayment, MutualFundStock, MutualFundPurchaseHistory, PortfolioSnapshot,
    TransactionHistory, PortfolioGrowthSnapshot, IndividualInvestmentGrowth, AllocationSettings, OwnedAsset, InvestmentCSVManager,
    MonthlySavingsTarget
)
from .price_fetcher import price_fetcher
from .progressive_fetcher import progressive_fetcher
from .loading_widget import InvestmentLoadingWidget
from .data_storage import investment_data_storage
from .data_availability_analyzer import data_availability_analyzer, UnavailabilityReason
from .unavailability_widgets import UnavailabilityContainer
from .price_fetcher import price_fetcher

# Chart imports
try:
    import matplotlib
    # Try to set backend for PySide6 (Qt6), but don't fail if it doesn't work
    try:
        # Use Qt6 backend for PySide6 compatibility
        matplotlib.use('QtAgg')  # QtAgg is the modern backend for Qt6
    except:
        try:
            # Fallback to Qt5Agg if QtAgg is not available
            matplotlib.use('Qt5Agg')
        except:
            pass  # Backend might already be set

    import matplotlib.pyplot as plt
    try:
        # Try Qt6 backend first
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    except ImportError:
        try:
            # Fallback to Qt5 backend
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        except ImportError:
            # Final fallback - use any available backend
            FigureCanvas = None

    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
    print("Matplotlib successfully imported")
except ImportError as e:
    MATPLOTLIB_AVAILABLE = False
    FigureCanvas = None
    Figure = None
    print(f"Matplotlib not available: {e}")
    plt = None
    mdates = None
    print(f"Matplotlib not available: {e}")  # Debug info
except Exception as e:
    MATPLOTLIB_AVAILABLE = False
    FigureCanvas = None
    Figure = None
    plt = None
    mdates = None
    print(f"Matplotlib error: {e}")  # Debug info











class CurrentResourceTableWidget(QTableWidget):
    """Table widget for current resource tracking"""

    resource_selected = Signal(int)  # Emits row index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
        self.resources = []

    def setup_table(self):
        """Setup the table"""
        # Define columns
        self.columns = ['Category', 'Amount (In Lakhs)', 'Allocation %']

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

        # Connect selection signal
        self.itemSelectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        """Handle selection change"""
        current_row = self.currentRow()
        if current_row >= 0:
            self.resource_selected.emit(current_row)

    def load_resources(self, resources):
        """Load resources into the table"""
        self.resources = resources
        self.setRowCount(len(resources))

        total_amount = 0.0
        total_allocation = 0.0

        for row, resource in enumerate(resources):
            # Category
            self.setItem(row, 0, QTableWidgetItem(resource.category))

            # Amount (In Lakhs)
            amount_item = QTableWidgetItem(f"{resource.amount_lakhs:.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row, 1, amount_item)
            total_amount += resource.amount_lakhs

            # Allocation %
            allocation_item = QTableWidgetItem(f"{resource.allocation_percent:.2f}%")
            allocation_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row, 2, allocation_item)
            total_allocation += resource.allocation_percent

        # Add totals row
        if resources:
            self.add_totals_row(total_amount, total_allocation)

    def add_totals_row(self, total_amount, total_allocation):
        """Add a totals row at the bottom"""
        row_count = self.rowCount()
        self.setRowCount(row_count + 1)

        # Total label
        total_item = QTableWidgetItem("TOTAL")
        total_item.setFont(QFont("Arial", 9, QFont.Bold))
        total_item.setBackground(QColor("#f0f0f0"))
        self.setItem(row_count, 0, total_item)

        # Total amount
        amount_item = QTableWidgetItem(f"{total_amount:.2f}")
        amount_item.setFont(QFont("Arial", 9, QFont.Bold))
        amount_item.setBackground(QColor("#f0f0f0"))
        amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(row_count, 1, amount_item)

        # Total allocation with color coding
        allocation_item = QTableWidgetItem(f"{total_allocation:.2f}%")
        allocation_item.setFont(QFont("Arial", 9, QFont.Bold))
        allocation_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Color code based on whether total equals 100%
        if abs(total_allocation - 100.0) < 0.01:  # Within 0.01% of 100%
            allocation_item.setBackground(QColor("#2d5a2d"))  # Dark green - perfect
            allocation_item.setForeground(QColor("#90ee90"))  # Light green text
            allocation_item.setToolTip("Allocation percentages sum to 100%")
        elif total_allocation > 0:
            allocation_item.setBackground(QColor("#5a5a2d"))  # Dark yellow - warning
            allocation_item.setForeground(QColor("#ffff90"))  # Light yellow text
            allocation_item.setToolTip(f"Allocation percentages sum to {total_allocation:.2f}% (not exactly 100%)")
        else:
            allocation_item.setBackground(QColor("#3e3e42"))  # Dark gray
            allocation_item.setForeground(QColor("#cccccc"))  # Light gray text
            allocation_item.setToolTip("No allocations defined")

        self.setItem(row_count, 2, allocation_item)

    def get_selected_resource(self):
        """Get the selected resource"""
        current_row = self.currentRow()
        if current_row >= 0 and current_row < len(self.resources):
            return self.resources[current_row]
        return None


class CurrentResourceDialog(QDialog):
    """Dialog for adding/editing current resource entries"""

    def __init__(self, resource=None, parent=None):
        super().__init__(parent)
        self.resource = resource if resource else CurrentResource()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Add/Edit Current Resource")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        # Category
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("e.g., Savings, Fixed Deposits, Stocks")
        form_layout.addRow("Category:", self.category_edit)

        # Amount (In Lakhs)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.0, 999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSuffix(" Lakhs")
        self.amount_spin.valueChanged.connect(self.calculate_allocation)
        form_layout.addRow("Amount (In Lakhs):", self.amount_spin)

        # Allocation % (read-only, auto-calculated)
        self.allocation_spin = QDoubleSpinBox()
        self.allocation_spin.setRange(0.0, 100.0)
        self.allocation_spin.setDecimals(2)
        self.allocation_spin.setSuffix("%")
        self.allocation_spin.setReadOnly(True)
        self.allocation_spin.setStyleSheet("QDoubleSpinBox:read-only { color: #666; }")
        form_layout.addRow("Allocation % (Auto):", self.allocation_spin)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def calculate_allocation(self):
        """Auto-calculate allocation percentage based on total portfolio value"""
        try:
            # Get current amount from the spin box
            current_amount = self.amount_spin.value()

            # Get parent widget to access current resources
            parent_widget = self.parent()
            if hasattr(parent_widget, 'current_resources'):
                # Calculate total amount excluding current resource being edited
                total_amount = 0.0
                for resource in parent_widget.current_resources:
                    if hasattr(self, 'resource') and self.resource.id and resource.id == self.resource.id:
                        # Skip current resource being edited
                        continue
                    total_amount += resource.amount_lakhs

                # Add current amount being entered
                total_amount += current_amount

                # Calculate allocation percentage
                if total_amount > 0:
                    allocation_percent = (current_amount / total_amount) * 100
                    self.allocation_spin.setValue(allocation_percent)
                else:
                    self.allocation_spin.setValue(0.0)
            else:
                # If no parent resources available, set to 100% if amount > 0
                if current_amount > 0:
                    self.allocation_spin.setValue(100.0)
                else:
                    self.allocation_spin.setValue(0.0)

        except Exception as e:
            # If calculation fails, don't update allocation
            pass

    def load_data(self):
        """Load resource data into form"""
        if self.resource.id:
            self.category_edit.setText(self.resource.category)
            self.amount_spin.setValue(self.resource.amount_lakhs)
            self.allocation_spin.setValue(self.resource.allocation_percent)

    def get_resource(self):
        """Get the resource from form data"""
        self.resource.category = self.category_edit.text().strip()
        self.resource.amount_lakhs = self.amount_spin.value()
        self.resource.allocation_percent = self.allocation_spin.value()
        self.resource.last_updated = datetime.now()

        return self.resource


class AssetLiabilityTableWidget(QTableWidget):
    """Enhanced table widget for integrated asset/liability tracking with investments and loans"""

    item_selected = Signal(int)  # Emits row index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
        self.items = []

    def setup_table(self):
        """Setup the enhanced table with additional columns"""
        # Define columns for integrated view
        self.columns = ['Name', 'Type', 'Category', 'Sub-Category', 'Geographic Classification', 'Amount', 'Percentage', 'Amount to be Spent']

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
        # Set specific column widths
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Category
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Sub-Category
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Geographic Classification
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Amount
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Percentage

        # Connect selection signal
        self.itemSelectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        """Handle selection change"""
        current_row = self.currentRow()
        if current_row >= 0:
            self.item_selected.emit(current_row)

    def load_integrated_data(self, asset_liability_items, loan_details, mutual_funds_stocks, allocation_settings=None):
        """Load integrated data from asset/liability items (CSV structure now matches GUI exactly)"""
        self.items = []

        # Add all asset/liability items from CSV - structure now matches GUI exactly
        for item in asset_liability_items:
            self.items.append({
                'source': 'asset_liability',
                'data': item,
                'name': item.name,  # Direct mapping - no parsing needed
                'type': item.type,  # Direct mapping - no parsing needed
                'category': item.category,  # Direct mapping - no parsing needed
                'sub_category': item.sub_category,  # Direct mapping - no parsing needed
                'geographic_classification': item.geographic_classification,  # Direct mapping - no parsing needed
                'amount': item.amount,  # Direct mapping - no lookup needed
                'percentage': item.percentage  # Direct mapping - no parsing needed
            })

        # Calculate percentages using allocation settings
        self._calculate_percentages(allocation_settings)

        # Update table display
        self._update_table_display()

    def _calculate_percentages(self, allocation_settings=None):
        """Calculate allocation percentages for assets only (liabilities get 0%)"""
        # Only calculate percentages for assets
        assets = [item for item in self.items if item['type'] == 'Asset']

        if not assets:
            return

        # Group assets by Category + Geographic Classification only (ignoring sub_category)
        asset_groups = {}
        for item in assets:
            key = (item['category'], item['geographic_classification'])
            if key not in asset_groups:
                asset_groups[key] = []
            asset_groups[key].append(item)

        # Apply allocation logic using predefined settings
        for item in self.items:
            if item['type'] == 'Asset':
                # Find allocation setting for this category + geographic classification
                category_allocation = self._get_category_allocation(item, allocation_settings)
                if category_allocation is not None:
                    # Find how many assets are in this category + geographic classification
                    key = (item['category'], item['geographic_classification'])
                    group_size = len(asset_groups.get(key, []))
                    if group_size > 0:
                        # Divide the category allocation equally among assets in the category
                        item['percentage'] = category_allocation / group_size
                    else:
                        item['percentage'] = category_allocation
                else:
                    # Default to 0% if no allocation setting found
                    item['percentage'] = 0.0
            else:
                # Liabilities get 0% allocation
                item['percentage'] = 0.0

        # Validate that total allocation equals 100% for assets
        total_asset_percentage = sum(item['percentage'] for item in self.items if item['type'] == 'Asset')

        # Log allocation summary for debugging
        if hasattr(self, 'logger'):
            self.logger.info(f"📊 Allocation Summary:")
            for key, group in asset_groups.items():
                category, geo_class = key
                category_allocation = self._get_category_allocation(group[0], allocation_settings) if group else 0
                individual_allocation = category_allocation / len(group) if group and category_allocation else 0
                self.logger.info(f"  {category} ({geo_class}): {len(group)} assets, {category_allocation}% total, {individual_allocation:.2f}% each")
            self.logger.info(f"📈 Total Asset Allocation: {total_asset_percentage:.2f}%")

    def _get_category_allocation(self, item, allocation_settings):
        """Get allocation percentage for a category + geographic classification combination"""
        if not allocation_settings:
            return None

        for setting in allocation_settings:
            if (setting.category == item['category'] and
                setting.geographic_classification == item['geographic_classification']):
                return setting.allocation_percent
        return None

    def _update_table_display(self):
        """Update the table display with current items"""
        self.setRowCount(len(self.items))

        for row, item in enumerate(self.items):
            # Name
            self.setItem(row, 0, QTableWidgetItem(item['name']))

            # Type with color coding
            type_item = QTableWidgetItem(item['type'])
            if item['type'] == "Asset":
                type_item.setBackground(QColor("#2d5a2d"))  # Dark green
                type_item.setForeground(QColor("#90ee90"))  # Light green text
            else:  # Liability
                type_item.setBackground(QColor("#5a2d2d"))  # Dark red
                type_item.setForeground(QColor("#ffb3b3"))  # Light red text
            self.setItem(row, 1, type_item)

            # Category
            self.setItem(row, 2, QTableWidgetItem(item['category']))

            # Sub-Category
            self.setItem(row, 3, QTableWidgetItem(item['sub_category']))

            # Geographic Classification
            self.setItem(row, 4, QTableWidgetItem(item['geographic_classification']))

            # Amount
            if item['amount'] > 0:
                amount_item = QTableWidgetItem(f"₹{item['amount']:,.2f}")
            else:
                amount_item = QTableWidgetItem("-")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row, 5, amount_item)

            # Percentage - only show for assets, not liabilities in Ideal Allocation tab
            if item['type'] == "Asset":
                percentage_item = QTableWidgetItem(f"{item['percentage']:.2f}%")
            else:  # Liability
                percentage_item = QTableWidgetItem("-")
            percentage_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row, 6, percentage_item)

            # Amount to be Spent - calculate based on monthly savings target and percentage
            if item['type'] == "Asset" and item['percentage'] > 0:
                monthly_target = self.get_monthly_savings_target()
                amount_to_spend = (monthly_target * item['percentage']) / 100
                amount_item = QTableWidgetItem(f"₹{amount_to_spend:,.2f}")
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                amount_item.setBackground(QColor("#e8f5e8"))  # Light green background
            else:
                amount_item = QTableWidgetItem("-")
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row, 7, amount_item)

        # Resize columns to content
        self.resizeColumnsToContents()

    def get_monthly_savings_target(self):
        """Get the monthly savings target from parent widget"""
        try:
            # Find the parent InvestmentTrackerWidget
            parent = self.parent()
            search_depth = 0
            while parent and search_depth < 10:
                if hasattr(parent, 'monthly_savings_target'):
                    return parent.monthly_savings_target.target_amount
                parent = parent.parent()
                search_depth += 1

            # Default fallback
            return 3000.0
        except Exception:
            return 3000.0

    def load_items(self, items):
        """Legacy method for backward compatibility"""
        # Convert to display format
        self.items = []
        for item in items:
            self.items.append({
                'source': 'asset_liability',
                'data': item,
                'name': item.name,
                'type': item.type,
                'category': item.category,
                'sub_category': item.sub_category,
                'geographic_classification': item.geographic_classification,
                'amount': item.amount,
                'percentage': item.percentage
            })
        self._update_table_display()

    def get_selected_item(self):
        """Get the selected item's data"""
        current_row = self.currentRow()
        if current_row >= 0 and current_row < len(self.items):
            return self.items[current_row]['data']
        return None


class AllocationSettingsWidget(QWidget):
    """Widget for managing custom allocation percentages"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.allocation_settings = []
        self.setup_ui()

    def setup_ui(self):
        """Setup the allocation settings UI"""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🎯 Custom Allocation Settings")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Add Setting button
        add_btn = QPushButton("➕ Add Custom Allocation")
        add_btn.clicked.connect(self.add_allocation_setting)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Monthly Savings Target KPI Card
        self.create_monthly_savings_kpi_card(layout)

        # Instructions
        instructions = QLabel(
            "Define custom allocation percentages for specific investment categories. "
            "If no custom allocation is set, investments will use equal distribution within their category."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-style: italic; margin: 10px 0;")
        layout.addWidget(instructions)

        # Allocation settings table
        self.allocation_table = QTableWidget()
        self.allocation_table.setColumnCount(5)
        self.allocation_table.setHorizontalHeaderLabels([
            'Category', 'Sub-Category', 'Geographic Classification', 'Allocation %', 'Actions'
        ])

        # Table settings
        self.allocation_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.allocation_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.allocation_table.setAlternatingRowColors(True)

        # Resize columns
        header = self.allocation_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Category
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Sub-Category
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Geographic Classification
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Allocation %
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Actions

        layout.addWidget(self.allocation_table)

        # Summary section
        summary_layout = QHBoxLayout()
        summary_layout.addStretch()

        self.total_allocation_label = QLabel("Total Custom Allocation: 0.00%")
        self.total_allocation_label.setFont(QFont("Arial", 10, QFont.Bold))
        summary_layout.addWidget(self.total_allocation_label)

        layout.addLayout(summary_layout)

    def create_monthly_savings_kpi_card(self, layout):
        """Create the Monthly Savings Target KPI card"""
        # KPI Card Frame
        kpi_frame = QFrame()
        kpi_frame.setFrameStyle(QFrame.Box)
        kpi_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #4CAF50;
                border-radius: 8px;
                background-color: #f8f9fa;
                margin: 10px 0;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #e8f5e8;
                cursor: pointer;
            }
        """)

        kpi_layout = QVBoxLayout(kpi_frame)
        kpi_layout.setContentsMargins(15, 10, 15, 10)

        # Title
        title_label = QLabel("💰 Monthly Savings Target")
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        kpi_layout.addWidget(title_label)

        # Amount display
        self.savings_target_label = QLabel("₹3,000")
        self.savings_target_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.savings_target_label.setAlignment(Qt.AlignCenter)
        self.savings_target_label.setStyleSheet("color: #2E7D32; margin: 5px 0;")
        kpi_layout.addWidget(self.savings_target_label)

        # Click instruction
        instruction_label = QLabel("Click to edit target amount")
        instruction_label.setFont(QFont("Arial", 9))
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("color: #666; font-style: italic;")
        kpi_layout.addWidget(instruction_label)

        # Make the frame clickable
        kpi_frame.mousePressEvent = self.on_savings_target_clicked

        layout.addWidget(kpi_frame)

    def on_savings_target_clicked(self, event):
        """Handle click on the savings target KPI card"""
        self.edit_monthly_savings_target()

    def edit_monthly_savings_target(self):
        """Open dialog to edit monthly savings target"""
        # Get current target from parent widget
        current_target = self.get_current_monthly_savings_target()

        dialog = MonthlySavingsTargetDialog(current_target, self)
        if dialog.exec() == QDialog.Accepted:
            updated_target = dialog.get_target()

            # Save the target
            success = self.save_monthly_savings_target(updated_target)
            if success:
                # Update the display
                self.update_savings_target_display(updated_target.target_amount)

                # Notify parent widget if it has a refresh method
                parent_widget = self.get_parent_investment_widget()
                if parent_widget and hasattr(parent_widget, 'on_monthly_savings_target_changed'):
                    parent_widget.on_monthly_savings_target_changed(updated_target)
            else:
                QMessageBox.warning(self, "Save Error", "Failed to save monthly savings target.")

    def get_current_monthly_savings_target(self):
        """Get the current monthly savings target from parent widget"""
        parent_widget = self.get_parent_investment_widget()
        if parent_widget and hasattr(parent_widget, 'monthly_savings_target'):
            return parent_widget.monthly_savings_target
        else:
            # Return default target
            return MonthlySavingsTarget()

    def save_monthly_savings_target(self, target):
        """Save monthly savings target to CSV"""
        try:
            parent_widget = self.get_parent_investment_widget()
            if parent_widget and hasattr(parent_widget, 'csv_manager'):
                # Save as a single-item list (only one target should exist)
                success = parent_widget.csv_manager.save_data('monthly_savings_target', [target])
                if success:
                    # Update parent widget's target
                    parent_widget.monthly_savings_target = target
                return success
            return False
        except Exception as e:
            print(f"Error saving monthly savings target: {e}")
            return False

    def get_parent_investment_widget(self):
        """Get the parent InvestmentTrackerWidget"""
        parent = self.parent()
        search_depth = 0
        while parent and search_depth < 10:
            if hasattr(parent, 'csv_manager') and hasattr(parent, 'monthly_savings_target'):
                return parent
            parent = parent.parent()
            search_depth += 1
        return None

    def update_savings_target_display(self, amount):
        """Update the savings target display"""
        if hasattr(self, 'savings_target_label'):
            self.savings_target_label.setText(f"₹{amount:,.0f}")

    def load_monthly_savings_target(self, target):
        """Load and display the monthly savings target"""
        if target:
            self.update_savings_target_display(target.target_amount)

    def add_allocation_setting(self):
        """Add new allocation setting"""
        dialog = AllocationSettingDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            setting = dialog.get_setting()
            print(f"Adding new allocation setting: {setting.category} - {setting.sub_category} - {setting.geographic_classification}: {setting.allocation_percent}%")
            self.allocation_settings.append(setting)
            self.refresh_table()
            self.update_total_allocation()
            # Save to CSV
            success = self.save_allocation_settings()
            if success:
                print("✅ New allocation setting added and saved successfully")
            else:
                print("❌ Failed to save new allocation setting")

    def edit_allocation_setting(self, row):
        """Edit allocation setting"""
        if row < len(self.allocation_settings):
            setting = self.allocation_settings[row]
            dialog = AllocationSettingDialog(setting, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_setting = dialog.get_setting()
                self.allocation_settings[row] = updated_setting
                self.refresh_table()
                self.update_total_allocation()
                # Save to CSV
                self.save_allocation_settings()

    def delete_allocation_setting(self, row):
        """Delete allocation setting"""
        if row < len(self.allocation_settings):
            setting = self.allocation_settings[row]
            reply = QMessageBox.question(
                self, "Delete Allocation Setting",
                f"Are you sure you want to delete the allocation setting for "
                f"{setting.category} - {setting.sub_category} - {setting.geographic_classification}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                del self.allocation_settings[row]
                self.refresh_table()
                self.update_total_allocation()
                # Save to CSV
                self.save_allocation_settings()

    def refresh_table(self):
        """Refresh the allocation settings table"""
        self.allocation_table.setRowCount(len(self.allocation_settings))

        for row, setting in enumerate(self.allocation_settings):
            # Category
            self.allocation_table.setItem(row, 0, QTableWidgetItem(setting.category))

            # Sub-Category
            self.allocation_table.setItem(row, 1, QTableWidgetItem(setting.sub_category))

            # Geographic Classification
            self.allocation_table.setItem(row, 2, QTableWidgetItem(setting.geographic_classification))

            # Allocation %
            percentage_item = QTableWidgetItem(f"{setting.allocation_percent:.2f}%")
            percentage_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.allocation_table.setItem(row, 3, percentage_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Edit")
            edit_btn.setMaximumWidth(30)
            edit_btn.clicked.connect(lambda checked, r=row: self.edit_allocation_setting(r))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Delete")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_allocation_setting(r))
            actions_layout.addWidget(delete_btn)

            actions_layout.addStretch()
            self.allocation_table.setCellWidget(row, 4, actions_widget)

    def update_total_allocation(self):
        """Update the total allocation display"""
        total = sum(setting.allocation_percent for setting in self.allocation_settings)
        self.total_allocation_label.setText(f"Total Custom Allocation: {total:.2f}%")

        # Color code based on total
        if total > 100:
            self.total_allocation_label.setStyleSheet("color: red; font-weight: bold;")
        elif total == 100:
            self.total_allocation_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.total_allocation_label.setStyleSheet("color: orange; font-weight: bold;")

    def load_settings(self, settings):
        """Load allocation settings"""
        self.allocation_settings = settings
        self.refresh_table()
        self.update_total_allocation()

    def get_settings(self):
        """Get current allocation settings"""
        return self.allocation_settings

    def save_allocation_settings(self):
        """Save allocation settings to CSV"""
        try:
            # Get the parent widget's CSV manager
            parent_widget = self.parent()
            search_depth = 0
            while parent_widget and not hasattr(parent_widget, 'csv_manager') and search_depth < 10:
                parent_widget = parent_widget.parent()
                search_depth += 1

            if not parent_widget:
                print("Error: Could not find parent widget")
                return False

            if not hasattr(parent_widget, 'csv_manager'):
                print("Error: Parent widget does not have csv_manager")
                return False

            print(f"Saving {len(self.allocation_settings)} allocation settings to CSV...")

            # Save to CSV
            success = parent_widget.csv_manager.save_data('allocation_settings', self.allocation_settings)

            if success:
                print("✅ Allocation settings saved successfully to CSV")
                # Also update the parent's allocation_settings list
                parent_widget.allocation_settings = self.allocation_settings
                # Refresh the integrated portfolio to apply new settings
                if hasattr(parent_widget, 'refresh_integrated_portfolio'):
                    parent_widget.refresh_integrated_portfolio()
                    print("✅ Integrated portfolio refreshed with new settings")
                return True
            else:
                print("❌ Failed to save allocation settings to CSV")
                return False

        except Exception as e:
            print(f"❌ Error saving allocation settings: {e}")
            import traceback
            traceback.print_exc()
            return False


class AllocationSettingDialog(QDialog):
    """Dialog for adding/editing allocation settings"""

    def __init__(self, setting=None, parent=None):
        super().__init__(parent)
        self.setting = setting if setting else AllocationSettings()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Allocation Setting")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(["Equity", "Debt", "Gold", "Hybrid", "ELSS", "International", "Sectoral", "Loan"])
        form_layout.addRow("Category:", self.category_combo)

        # Sub-Category
        self.sub_category_combo = QComboBox()
        self.sub_category_combo.setEditable(True)
        self.sub_category_combo.addItems([
            "Large Cap", "Mid Cap", "Small Cap", "Multi Cap", "Value", "Growth",
            "Corporate", "Banking & PSU", "Index", "ETF", "Stock"
        ])
        form_layout.addRow("Sub-Category:", self.sub_category_combo)

        # Geographic Classification
        self.geographic_combo = QComboBox()
        self.geographic_combo.addItems(["", "Indian", "International"])
        form_layout.addRow("Geographic Classification:", self.geographic_combo)

        # Allocation Percentage
        self.allocation_spin = QDoubleSpinBox()
        self.allocation_spin.setRange(0.0, 100.0)
        self.allocation_spin.setDecimals(2)
        self.allocation_spin.setSuffix("%")
        form_layout.addRow("Allocation Percentage:", self.allocation_spin)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def load_data(self):
        """Load setting data into form"""
        if self.setting.id:
            self.category_combo.setCurrentText(self.setting.category)
            self.sub_category_combo.setCurrentText(self.setting.sub_category)
            self.geographic_combo.setCurrentText(self.setting.geographic_classification)
            self.allocation_spin.setValue(self.setting.allocation_percent)

    def get_setting(self):
        """Get the setting from form data"""
        self.setting.category = self.category_combo.currentText().strip()
        self.setting.sub_category = self.sub_category_combo.currentText().strip()
        self.setting.geographic_classification = self.geographic_combo.currentText().strip()
        self.setting.allocation_percent = self.allocation_spin.value()
        self.setting.last_updated = datetime.now()

        return self.setting


class MonthlySavingsTargetDialog(QDialog):
    """Dialog for editing monthly savings target"""

    def __init__(self, target=None, parent=None):
        super().__init__(parent)
        self.target = target if target else MonthlySavingsTarget()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Monthly Savings Target")
        self.setModal(True)
        self.resize(400, 250)

        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("💰 Set Monthly Savings Target")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        # Description
        desc_label = QLabel(
            "Set your monthly savings target amount. This will be used to calculate "
            "recommended allocation amounts for each investment category."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(desc_label)

        # Form layout
        form_layout = QFormLayout()

        # Target Amount
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.0, 9999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("₹ ")
        self.amount_spin.setValue(3000.0)  # Default value
        form_layout.addRow("Monthly Target Amount:", self.amount_spin)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Optional notes about your savings target...")
        form_layout.addRow("Notes:", self.notes_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Target")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def load_data(self):
        """Load data into form"""
        if self.target:
            self.amount_spin.setValue(self.target.target_amount)
            self.notes_edit.setPlainText(self.target.notes)

    def get_target(self) -> MonthlySavingsTarget:
        """Get the monthly savings target from form"""
        self.target.target_amount = self.amount_spin.value()
        self.target.notes = self.notes_edit.toPlainText()
        self.target.last_updated = datetime.now()
        return self.target


class AllocationCalculator:
    """Helper class for calculating portfolio allocations"""

    @staticmethod
    def calculate_allocations(investments, loans, other_assets, allocation_settings=None):
        """
        Calculate allocation percentages for all portfolio items

        Args:
            investments: List of MutualFundStock objects
            loans: List of LoanDetails objects
            other_assets: List of AssetLiability objects (excluding loans)
            allocation_settings: List of AllocationSettings objects

        Returns:
            Dictionary with calculated allocations for each item
        """
        allocations = {}

        # Calculate total portfolio value
        total_value = 0.0

        # Add investment values
        for investment in investments:
            total_value += investment.current_amount

        # Add loan values (as negative for liabilities)
        for loan in loans:
            total_value += loan.outstanding_amount  # Loans are liabilities but count toward total

        # Add other asset values (if they have amounts)
        for asset in other_assets:
            # Other assets might not have amounts in current structure
            total_value += 0.0  # Placeholder for now

        if total_value == 0:
            return allocations

        # Group investments by category for equal distribution
        investment_groups = {}
        for investment in investments:
            key = (investment.category, investment.sub_category, investment.geographic_classification)
            if key not in investment_groups:
                investment_groups[key] = []
            investment_groups[key].append(investment)

        # Calculate allocations for investments
        for investment in investments:
            key = (investment.category, investment.sub_category, investment.geographic_classification)

            # Check for custom allocation
            custom_allocation = AllocationCalculator._get_custom_allocation(
                investment.category, investment.sub_category,
                investment.geographic_classification, allocation_settings
            )

            if custom_allocation is not None:
                # Use custom allocation
                allocations[f"investment_{investment.id}"] = custom_allocation
            else:
                # Use equal distribution within category or proportional to amount
                group = investment_groups[key]
                if len(group) == 1:
                    # Single item in category, use proportional allocation
                    allocations[f"investment_{investment.id}"] = (investment.current_amount / total_value) * 100
                else:
                    # Multiple items in category, use equal distribution within category
                    category_total = sum(inv.current_amount for inv in group)
                    category_percentage = (category_total / total_value) * 100
                    equal_share = category_percentage / len(group)
                    allocations[f"investment_{investment.id}"] = equal_share

        # Calculate allocations for loans (proportional to outstanding amount)
        for loan in loans:
            allocations[f"loan_{loan.id}"] = (loan.outstanding_amount / total_value) * 100

        # Calculate allocations for other assets
        for asset in other_assets:
            if asset.category.lower() != "loans":  # Skip loans as they're handled separately
                # Use existing percentage or calculate based on total
                if asset.percentage > 0:
                    allocations[f"asset_{asset.id}"] = asset.percentage
                else:
                    # Default small allocation for assets without amounts
                    allocations[f"asset_{asset.id}"] = 1.0

        return allocations

    @staticmethod
    def _get_custom_allocation(category, sub_category, geographic_classification, allocation_settings):
        """Get custom allocation for specific criteria"""
        if not allocation_settings:
            return None

        for setting in allocation_settings:
            if (setting.category == category and
                setting.sub_category == sub_category and
                setting.geographic_classification == geographic_classification):
                return setting.allocation_percent
        return None

    @staticmethod
    def validate_allocations(allocations):
        """Validate that allocations are reasonable"""
        total = sum(allocations.values())

        validation_result = {
            'total': total,
            'is_valid': True,
            'warnings': [],
            'errors': []
        }

        if total > 105:  # Allow 5% tolerance
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Total allocation ({total:.2f}%) exceeds 100%")
        elif total > 100:
            validation_result['warnings'].append(f"Total allocation ({total:.2f}%) slightly exceeds 100%")
        elif total < 95:  # Allow 5% tolerance
            validation_result['warnings'].append(f"Total allocation ({total:.2f}%) is less than 100%")

        return validation_result


class AssetLiabilityDialog(QDialog):
    """Dialog for adding/editing asset/liability entries"""

    def __init__(self, item=None, categories=None, parent=None):
        super().__init__(parent)
        self.item = item if item else AssetLiability()
        self.categories = categories if categories else []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Add/Edit Asset/Liability")
        self.setModal(True)
        self.resize(400, 350)

        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., House, Car, Credit Card Debt")
        form_layout.addRow("Name:", self.name_edit)

        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Asset", "Liability"])
        form_layout.addRow("Type:", self.type_combo)

        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(self.categories)
        form_layout.addRow("Category:", self.category_combo)

        # Percentage
        self.percentage_spin = QDoubleSpinBox()
        self.percentage_spin.setRange(0.0, 100.0)
        self.percentage_spin.setDecimals(2)
        self.percentage_spin.setSuffix("%")
        form_layout.addRow("Percentage:", self.percentage_spin)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_data(self):
        """Load item data into form"""
        if self.item.id:
            self.name_edit.setText(self.item.name)
            self.type_combo.setCurrentText(self.item.type)
            self.category_combo.setCurrentText(self.item.category)
            self.percentage_spin.setValue(self.item.percentage)

    def get_item(self):
        """Get the asset/liability item from form data"""
        self.item.name = self.name_edit.text().strip()
        self.item.type = self.type_combo.currentText()
        self.item.category = self.category_combo.currentText().strip()
        self.item.percentage = self.percentage_spin.value()
        self.item.last_updated = datetime.now()

        return self.item


class CategoryManagementDialog(QDialog):
    """Dialog for managing categories"""

    def __init__(self, categories=None, parent=None):
        super().__init__(parent)
        self.categories = categories if categories else []
        self.setup_ui()
        self.load_categories()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Manage Categories")
        self.setModal(True)
        self.resize(400, 500)

        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Manage Categories")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(header_label)

        # Add new category
        add_layout = QHBoxLayout()
        self.new_category_edit = QLineEdit()
        self.new_category_edit.setPlaceholderText("Enter new category name")
        add_layout.addWidget(self.new_category_edit)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_category)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        # Categories list with proper column resize functionality
        self.categories_list = QTableWidget()
        self.categories_list.setColumnCount(2)
        self.categories_list.setHorizontalHeaderLabels(["Category", "Action"])

        # Table settings
        self.categories_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.categories_list.setAlternatingRowColors(True)

        # Proper column resize functionality
        categories_header = self.categories_list.horizontalHeader()
        categories_header.setSectionResizeMode(0, QHeaderView.Stretch)          # Category stretches
        categories_header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Action fits content

        layout.addWidget(self.categories_list)

        # Buttons
        button_layout = QHBoxLayout()

        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_categories(self):
        """Load categories into the list"""
        self.categories_list.setRowCount(len(self.categories))

        for row, category in enumerate(self.categories):
            # Category name
            self.categories_list.setItem(row, 0, QTableWidgetItem(category))

            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_category(r))
            self.categories_list.setCellWidget(row, 1, delete_btn)

    def add_category(self):
        """Add new category"""
        new_category = self.new_category_edit.text().strip()
        if new_category and new_category not in self.categories:
            self.categories.append(new_category)
            self.new_category_edit.clear()
            self.load_categories()

    def delete_category(self, row):
        """Delete category"""
        if 0 <= row < len(self.categories):
            category = self.categories[row]
            reply = QMessageBox.question(
                self, "Delete Category",
                f"Are you sure you want to delete the category '{category}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.categories.pop(row)
                self.load_categories()

    def get_categories(self):
        """Get the updated categories list"""
        return self.categories


class GoalPlanningTableWidget(QTableWidget):
    """Table widget for goal planning and SIP calculator"""

    goal_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
        self.goals = []

    def setup_table(self):
        """Setup the table"""
        self.columns = ['Goal Name', 'Current Cost', 'Years Until Goal', 'Future Value',
                       'Monthly SIP Required', 'Time Horizon', 'Action for Plan']

        self.setColumnCount(len(self.columns))
        self.setHorizontalHeaderLabels(self.columns)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(len(self.columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.itemSelectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        current_row = self.currentRow()
        if current_row >= 0:
            self.goal_selected.emit(current_row)

    def load_goals(self, goals):
        """Load goals into the table"""
        self.goals = goals
        self.setRowCount(len(goals))

        for row, goal in enumerate(goals):
            self.setItem(row, 0, QTableWidgetItem(goal.goal_name))
            self.setItem(row, 1, QTableWidgetItem(f"₹{goal.current_cost:,.2f}"))
            self.setItem(row, 2, QTableWidgetItem(str(goal.years_until_goal)))
            self.setItem(row, 3, QTableWidgetItem(f"₹{goal.future_value:,.2f}"))
            self.setItem(row, 4, QTableWidgetItem(f"₹{goal.monthly_sip_required:,.2f}"))
            self.setItem(row, 5, QTableWidgetItem(goal.time_horizon))
            self.setItem(row, 6, QTableWidgetItem(goal.action_plan))

    def get_selected_goal(self):
        current_row = self.currentRow()
        if current_row >= 0 and current_row < len(self.goals):
            return self.goals[current_row]
        return None


class GoalPlanningDialog(QDialog):
    """Dialog for adding/editing financial goals"""

    def __init__(self, goal=None, parent=None):
        super().__init__(parent)
        self.goal = goal if goal else FinancialGoal()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Add/Edit Financial Goal")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Goal Name
        self.goal_name_edit = QLineEdit()
        form_layout.addRow("Goal Name:", self.goal_name_edit)

        # Current Cost
        self.current_cost_spin = QDoubleSpinBox()
        self.current_cost_spin.setRange(0.0, 99999999.99)
        self.current_cost_spin.setPrefix("₹")
        self.current_cost_spin.valueChanged.connect(self.calculate_sip)
        form_layout.addRow("Current Cost:", self.current_cost_spin)

        # Years Until Goal
        self.years_spin = QSpinBox()
        self.years_spin.setRange(1, 50)
        self.years_spin.valueChanged.connect(self.calculate_sip)
        form_layout.addRow("Years Until Goal:", self.years_spin)

        # Future Value (calculated)
        self.future_value_spin = QDoubleSpinBox()
        self.future_value_spin.setRange(0.0, 99999999.99)
        self.future_value_spin.setPrefix("₹")
        self.future_value_spin.setReadOnly(True)
        form_layout.addRow("Future Value:", self.future_value_spin)

        # Monthly SIP Required (calculated)
        self.monthly_sip_spin = QDoubleSpinBox()
        self.monthly_sip_spin.setRange(0.0, 99999999.99)
        self.monthly_sip_spin.setPrefix("₹")
        self.monthly_sip_spin.setReadOnly(True)
        form_layout.addRow("Monthly SIP Required:", self.monthly_sip_spin)

        # Time Horizon
        self.time_horizon_combo = QComboBox()
        self.time_horizon_combo.addItems(["Short Term", "Medium Term", "Long Term"])
        form_layout.addRow("Time Horizon:", self.time_horizon_combo)

        # Action Plan
        self.action_plan_edit = QTextEdit()
        self.action_plan_edit.setMaximumHeight(80)
        form_layout.addRow("Action for Plan:", self.action_plan_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def calculate_sip(self):
        """Calculate future value and monthly SIP required"""
        current_cost = self.current_cost_spin.value()
        years = self.years_spin.value()

        if current_cost > 0 and years > 0:
            # Assume 7% inflation rate for future value
            inflation_rate = 0.07
            future_value = current_cost * ((1 + inflation_rate) ** years)
            self.future_value_spin.setValue(future_value)

            # Assume 12% return rate for SIP calculation
            return_rate = 0.12
            monthly_rate = return_rate / 12
            months = years * 12

            # SIP calculation formula
            if monthly_rate > 0:
                sip_required = future_value * monthly_rate / (((1 + monthly_rate) ** months) - 1)
                self.monthly_sip_spin.setValue(sip_required)

    def load_data(self):
        """Load goal data into form"""
        if self.goal.id:
            self.goal_name_edit.setText(self.goal.goal_name)
            self.current_cost_spin.setValue(self.goal.current_cost)
            self.years_spin.setValue(self.goal.years_until_goal)
            self.future_value_spin.setValue(self.goal.future_value)
            self.monthly_sip_spin.setValue(self.goal.monthly_sip_required)
            self.time_horizon_combo.setCurrentText(self.goal.time_horizon)
            self.action_plan_edit.setPlainText(self.goal.action_plan)

    def get_goal(self):
        """Get the goal from form data"""
        self.goal.goal_name = self.goal_name_edit.text().strip()
        self.goal.current_cost = self.current_cost_spin.value()
        self.goal.years_until_goal = self.years_spin.value()
        self.goal.future_value = self.future_value_spin.value()
        self.goal.monthly_sip_required = self.monthly_sip_spin.value()
        self.goal.time_horizon = self.time_horizon_combo.currentText()
        self.goal.action_plan = self.action_plan_edit.toPlainText().strip()
        self.goal.last_updated = datetime.now()

        return self.goal


class OwnedAssetDialog(QDialog):
    """Dialog for adding/editing owned assets"""

    def __init__(self, asset=None, categories=None, parent=None):
        super().__init__(parent)
        self.asset = asset if asset else OwnedAsset()
        self.categories = categories if categories else []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Add/Edit Owned Asset")
        self.setModal(True)
        self.resize(500, 600)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Asset name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Primary Residence, Honda City, Gold Jewelry")
        form_layout.addRow("Asset Name:", self.name_edit)

        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(self.categories)
        form_layout.addRow("Category:", self.category_combo)

        # Sub-category
        self.sub_category_edit = QLineEdit()
        self.sub_category_edit.setPlaceholderText("e.g., House, Car, Jewelry, Savings Account")
        form_layout.addRow("Sub-Category:", self.sub_category_edit)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Brief description of the asset")
        form_layout.addRow("Description:", self.description_edit)

        # Purchase date
        self.purchase_date_edit = QDateEdit()
        self.purchase_date_edit.setDate(QDate.currentDate())
        self.purchase_date_edit.setCalendarPopup(True)
        form_layout.addRow("Purchase Date:", self.purchase_date_edit)

        # Purchase value
        self.purchase_value_spin = QDoubleSpinBox()
        self.purchase_value_spin.setRange(0, 999999999)
        self.purchase_value_spin.setDecimals(2)
        self.purchase_value_spin.setSuffix(" ₹")
        form_layout.addRow("Purchase Value:", self.purchase_value_spin)

        # Current value
        self.current_value_spin = QDoubleSpinBox()
        self.current_value_spin.setRange(0, 999999999)
        self.current_value_spin.setDecimals(2)
        self.current_value_spin.setSuffix(" ₹")
        form_layout.addRow("Current Value:", self.current_value_spin)

        # Location
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., Mumbai, Garage, Bank Locker")
        form_layout.addRow("Location:", self.location_edit)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Additional notes about the asset")
        form_layout.addRow("Notes:", self.notes_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.ok_btn = QPushButton("Save")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_data(self):
        """Load asset data into form"""
        if self.asset.id:
            self.name_edit.setText(self.asset.name)
            self.category_combo.setCurrentText(self.asset.category)
            self.sub_category_edit.setText(self.asset.sub_category)
            self.description_edit.setPlainText(self.asset.description)

            if self.asset.purchase_date:
                self.purchase_date_edit.setDate(QDate(self.asset.purchase_date))

            self.purchase_value_spin.setValue(self.asset.purchase_value)
            self.current_value_spin.setValue(self.asset.current_value)
            self.location_edit.setText(self.asset.location)
            self.notes_edit.setPlainText(self.asset.notes)

    def get_asset(self):
        """Get the asset from form data"""
        self.asset.name = self.name_edit.text().strip()
        self.asset.category = self.category_combo.currentText().strip()
        self.asset.sub_category = self.sub_category_edit.text().strip()
        self.asset.description = self.description_edit.toPlainText().strip()
        self.asset.purchase_date = self.purchase_date_edit.date().toPython()
        self.asset.purchase_value = self.purchase_value_spin.value()
        self.asset.current_value = self.current_value_spin.value()
        self.asset.location = self.location_edit.text().strip()
        self.asset.notes = self.notes_edit.toPlainText().strip()
        self.asset.last_updated = datetime.now()

        return self.asset


class LoanDetailsDialog(QDialog):
    """Dialog for adding/editing loan details"""

    def __init__(self, loan=None, parent=None):
        super().__init__(parent)
        self.loan = loan if loan else LoanDetails()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Add/Edit Loan Details")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Loan Name
        self.loan_name_edit = QLineEdit()
        self.loan_name_edit.setPlaceholderText("e.g., Home Loan, Car Loan, Personal Loan")
        form_layout.addRow("Loan Name:", self.loan_name_edit)

        # Outstanding Amount
        self.outstanding_amount_spin = QDoubleSpinBox()
        self.outstanding_amount_spin.setRange(0.0, 99999999.99)
        self.outstanding_amount_spin.setPrefix("₹")
        form_layout.addRow("Outstanding Amount:", self.outstanding_amount_spin)

        # Interest Rate
        self.interest_rate_spin = QDoubleSpinBox()
        self.interest_rate_spin.setRange(0.0, 100.0)
        self.interest_rate_spin.setDecimals(2)
        self.interest_rate_spin.setSuffix("%")
        form_layout.addRow("Interest Rate:", self.interest_rate_spin)

        # Remaining Period (in months)
        self.remaining_period_spin = QSpinBox()
        self.remaining_period_spin.setRange(0, 600)  # Up to 50 years
        self.remaining_period_spin.setSuffix(" months")
        form_layout.addRow("Remaining Period:", self.remaining_period_spin)

        # EMI Amount
        self.emi_amount_spin = QDoubleSpinBox()
        self.emi_amount_spin.setRange(0.0, 99999999.99)
        self.emi_amount_spin.setPrefix("₹")
        form_layout.addRow("EMI Amount:", self.emi_amount_spin)

        # EMI Start Date
        self.emi_start_date_edit = QDateEdit()
        self.emi_start_date_edit.setCalendarPopup(True)
        self.emi_start_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("EMI Start Date:", self.emi_start_date_edit)

        # EMI End Date
        self.emi_end_date_edit = QDateEdit()
        self.emi_end_date_edit.setCalendarPopup(True)
        self.emi_end_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("EMI End Date:", self.emi_end_date_edit)

        # Last Paid Date
        self.last_paid_date_edit = QDateEdit()
        self.last_paid_date_edit.setCalendarPopup(True)
        self.last_paid_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Last Paid Date:", self.last_paid_date_edit)

        # Net Tenure
        self.net_tenure_spin = QSpinBox()
        self.net_tenure_spin.setRange(0, 999)
        self.net_tenure_spin.setSuffix(" months")
        form_layout.addRow("Net Tenure:", self.net_tenure_spin)

        # Loan Holder
        self.loan_holder_edit = QLineEdit()
        self.loan_holder_edit.setPlaceholderText("e.g., SBI, HDFC Bank, ICICI Bank")
        form_layout.addRow("Loan Holder:", self.loan_holder_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_data(self):
        """Load loan data into form"""
        if self.loan.id:
            self.loan_name_edit.setText(self.loan.loan_name)
            self.outstanding_amount_spin.setValue(self.loan.outstanding_amount)
            self.interest_rate_spin.setValue(self.loan.interest_rate)
            self.remaining_period_spin.setValue(self.loan.remaining_period_months)
            self.emi_amount_spin.setValue(self.loan.emi_amount)

            # Handle date fields with proper conversion
            if self.loan.emi_start_date:
                if isinstance(self.loan.emi_start_date, datetime):
                    self.emi_start_date_edit.setDate(QDate(self.loan.emi_start_date.date()))
                elif isinstance(self.loan.emi_start_date, date):
                    self.emi_start_date_edit.setDate(QDate(self.loan.emi_start_date))

            if self.loan.emi_end_date:
                if isinstance(self.loan.emi_end_date, datetime):
                    self.emi_end_date_edit.setDate(QDate(self.loan.emi_end_date.date()))
                elif isinstance(self.loan.emi_end_date, date):
                    self.emi_end_date_edit.setDate(QDate(self.loan.emi_end_date))

            if self.loan.last_paid_date:
                if isinstance(self.loan.last_paid_date, datetime):
                    self.last_paid_date_edit.setDate(QDate(self.loan.last_paid_date.date()))
                elif isinstance(self.loan.last_paid_date, date):
                    self.last_paid_date_edit.setDate(QDate(self.loan.last_paid_date))

            self.net_tenure_spin.setValue(self.loan.net_tenure)
            self.loan_holder_edit.setText(self.loan.loan_holder)

    def get_loan(self):
        """Get the loan from form data"""
        self.loan.loan_name = self.loan_name_edit.text().strip()
        self.loan.outstanding_amount = self.outstanding_amount_spin.value()
        self.loan.interest_rate = self.interest_rate_spin.value()
        self.loan.remaining_period_months = self.remaining_period_spin.value()
        self.loan.emi_amount = self.emi_amount_spin.value()

        # Convert QDate to datetime for consistency
        self.loan.emi_start_date = datetime.combine(self.emi_start_date_edit.date().toPython(), datetime.min.time())
        self.loan.emi_end_date = datetime.combine(self.emi_end_date_edit.date().toPython(), datetime.min.time())
        self.loan.last_paid_date = datetime.combine(self.last_paid_date_edit.date().toPython(), datetime.min.time())

        self.loan.net_tenure = self.net_tenure_spin.value()
        self.loan.loan_holder = self.loan_holder_edit.text().strip()
        self.loan.last_updated = datetime.now()

        return self.loan

    def validate_data(self):
        """Validate form data"""
        errors = []

        if not self.loan_name_edit.text().strip():
            errors.append("Loan name is required")

        if self.outstanding_amount_spin.value() < 0:
            errors.append("Outstanding amount cannot be negative")

        if self.interest_rate_spin.value() < 0:
            errors.append("Interest rate cannot be negative")

        if self.emi_amount_spin.value() < 0:
            errors.append("EMI amount cannot be negative")

        if self.remaining_period_spin.value() < 0:
            errors.append("Remaining period cannot be negative")

        if self.net_tenure_spin.value() < 0:
            errors.append("Net tenure cannot be negative")

        # Date validation - EMI end date should be after start date
        start_date = self.emi_start_date_edit.date().toPython()
        end_date = self.emi_end_date_edit.date().toPython()
        if end_date < start_date:
            errors.append("EMI end date must be after EMI start date")

        return errors

    def accept(self):
        """Override accept to validate data first"""
        errors = self.validate_data()
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        super().accept()


class LoanPaymentEntryDialog(QDialog):
    """Dialog for adding/editing loan payment entries"""

    def __init__(self, payment=None, loan=None, parent=None):
        super().__init__(parent)
        self.payment = payment if payment else LoanPayment()
        self.loan = loan  # Parent loan for context and calculations
        self.payment_methods = ["Cash", "Check", "Bank Transfer", "Online Payment", "UPI", "Credit Card", "Debit Card"]
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Add/Edit Payment Entry")
        self.setModal(True)
        self.resize(450, 400)

        layout = QVBoxLayout(self)

        # Loan context information
        if self.loan:
            context_group = QGroupBox(f"Loan: {self.loan.loan_name}")
            context_layout = QFormLayout(context_group)

            context_layout.addRow("Outstanding Amount:", QLabel(f"₹{self.loan.outstanding_amount:,.2f}"))
            context_layout.addRow("Interest Rate:", QLabel(f"{self.loan.interest_rate:.2f}%"))
            context_layout.addRow("EMI Amount:", QLabel(f"₹{self.loan.emi_amount:,.2f}"))

            layout.addWidget(context_group)

        # Payment form
        form_layout = QFormLayout()

        # Payment Date
        self.payment_date_edit = QDateEdit()
        self.payment_date_edit.setDate(QDate.currentDate())
        self.payment_date_edit.setCalendarPopup(True)
        form_layout.addRow("Payment Date:", self.payment_date_edit)

        # Total Payment Amount
        self.total_payment_spin = QDoubleSpinBox()
        self.total_payment_spin.setRange(0.01, 99999999.99)
        self.total_payment_spin.setPrefix("₹")
        self.total_payment_spin.setDecimals(2)
        if self.loan and self.loan.emi_amount > 0:
            self.total_payment_spin.setValue(self.loan.emi_amount)
        form_layout.addRow("Total Payment:", self.total_payment_spin)

        # Principal Amount
        self.principal_amount_spin = QDoubleSpinBox()
        self.principal_amount_spin.setRange(0.0, 99999999.99)
        self.principal_amount_spin.setPrefix("₹")
        self.principal_amount_spin.setDecimals(2)
        form_layout.addRow("Principal Amount:", self.principal_amount_spin)

        # Interest Amount
        self.interest_amount_spin = QDoubleSpinBox()
        self.interest_amount_spin.setRange(0.0, 99999999.99)
        self.interest_amount_spin.setPrefix("₹")
        self.interest_amount_spin.setDecimals(2)
        form_layout.addRow("Interest Amount:", self.interest_amount_spin)

        # Auto-calculate button
        calc_btn = QPushButton("🧮 Auto-Calculate Interest/Principal")
        calc_btn.clicked.connect(self.auto_calculate_amounts)
        form_layout.addRow("", calc_btn)

        # Remaining Balance
        self.remaining_balance_spin = QDoubleSpinBox()
        self.remaining_balance_spin.setRange(0.0, 99999999.99)
        self.remaining_balance_spin.setPrefix("₹")
        self.remaining_balance_spin.setDecimals(2)
        form_layout.addRow("Remaining Balance:", self.remaining_balance_spin)

        # Payment Method
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(self.payment_methods)
        self.payment_method_combo.setEditable(True)
        form_layout.addRow("Payment Method:", self.payment_method_combo)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Optional notes or comments about this payment...")
        form_layout.addRow("Notes:", self.notes_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("💾 Save Payment")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Connect signals for auto-calculation
        self.total_payment_spin.valueChanged.connect(self.on_total_payment_changed)
        self.principal_amount_spin.valueChanged.connect(self.on_amounts_changed)
        self.interest_amount_spin.valueChanged.connect(self.on_amounts_changed)

    def auto_calculate_amounts(self):
        """Auto-calculate interest and principal amounts based on loan terms"""
        if not self.loan:
            QMessageBox.information(self, "Info", "No loan context available for auto-calculation.")
            return

        total_payment = self.total_payment_spin.value()
        if total_payment <= 0:
            QMessageBox.warning(self, "Warning", "Please enter a valid total payment amount first.")
            return

        # Simple interest calculation for monthly payment
        # In a real application, you might want more sophisticated amortization calculations
        current_balance = self.loan.outstanding_amount
        monthly_interest_rate = self.loan.interest_rate / 100 / 12

        # Calculate interest portion
        interest_amount = current_balance * monthly_interest_rate

        # Principal is the remainder
        principal_amount = max(0, total_payment - interest_amount)

        # Update the fields
        self.interest_amount_spin.setValue(interest_amount)
        self.principal_amount_spin.setValue(principal_amount)

        # Calculate remaining balance
        new_balance = max(0, current_balance - principal_amount)
        self.remaining_balance_spin.setValue(new_balance)

    def on_total_payment_changed(self):
        """Handle total payment amount changes"""
        total = self.total_payment_spin.value()
        principal = self.principal_amount_spin.value()
        interest = self.interest_amount_spin.value()

        # If principal and interest are both 0, try auto-calculation
        if principal == 0 and interest == 0 and total > 0:
            self.auto_calculate_amounts()

    def on_amounts_changed(self):
        """Handle principal/interest amount changes"""
        principal = self.principal_amount_spin.value()
        interest = self.interest_amount_spin.value()

        # Update total payment
        total = principal + interest
        self.total_payment_spin.blockSignals(True)
        self.total_payment_spin.setValue(total)
        self.total_payment_spin.blockSignals(False)

    def load_data(self):
        """Load payment data into form"""
        if self.payment.id:
            if self.payment.payment_date:
                if isinstance(self.payment.payment_date, date):
                    self.payment_date_edit.setDate(QDate(self.payment.payment_date))
                elif isinstance(self.payment.payment_date, datetime):
                    self.payment_date_edit.setDate(QDate(self.payment.payment_date.date()))

            self.total_payment_spin.setValue(self.payment.total_payment)
            self.principal_amount_spin.setValue(self.payment.principal_amount)
            self.interest_amount_spin.setValue(self.payment.interest_amount)
            self.remaining_balance_spin.setValue(self.payment.remaining_balance)

            if self.payment.payment_method in self.payment_methods:
                self.payment_method_combo.setCurrentText(self.payment.payment_method)
            else:
                self.payment_method_combo.setCurrentText(self.payment.payment_method)

            self.notes_edit.setPlainText(self.payment.notes)

    def get_payment(self):
        """Get the payment from form data"""
        if self.loan:
            self.payment.loan_id = self.loan.id

        self.payment.payment_date = self.payment_date_edit.date().toPython()
        self.payment.total_payment = self.total_payment_spin.value()
        self.payment.principal_amount = self.principal_amount_spin.value()
        self.payment.interest_amount = self.interest_amount_spin.value()
        self.payment.remaining_balance = self.remaining_balance_spin.value()
        self.payment.payment_method = self.payment_method_combo.currentText().strip()
        self.payment.notes = self.notes_edit.toPlainText().strip()
        self.payment.last_updated = datetime.now()

        return self.payment

    def accept(self):
        """Override accept to validate data first"""
        errors = self.validate_data()
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        super().accept()

    def validate_data(self):
        """Validate form data"""
        errors = []

        if self.total_payment_spin.value() <= 0:
            errors.append("Total payment amount must be greater than 0")

        if self.principal_amount_spin.value() < 0:
            errors.append("Principal amount cannot be negative")

        if self.interest_amount_spin.value() < 0:
            errors.append("Interest amount cannot be negative")

        # Check if total equals principal + interest (with small tolerance for floating point)
        total = self.total_payment_spin.value()
        principal = self.principal_amount_spin.value()
        interest = self.interest_amount_spin.value()

        if abs(total - (principal + interest)) > 0.01:
            errors.append("Total payment must equal principal + interest amounts")

        if self.remaining_balance_spin.value() < 0:
            errors.append("Remaining balance cannot be negative")

        # Date validation
        payment_date = self.payment_date_edit.date().toPython()
        if self.loan and self.loan.emi_start_date:
            loan_start = self.loan.emi_start_date.date() if isinstance(self.loan.emi_start_date, datetime) else self.loan.emi_start_date
            if payment_date < loan_start:
                errors.append("Payment date cannot be before loan start date")

        return errors


class LoanPaymentHistoryDialog(QDialog):
    """Comprehensive dialog for viewing and managing loan payment history"""

    def __init__(self, loan, csv_manager, parent=None):
        super().__init__(parent)
        self.loan = loan
        self.csv_manager = csv_manager
        self.payment_history = []
        self.setup_ui()
        self.load_payment_history()
        self.refresh_payment_table()

    def setup_ui(self):
        """Setup the dialog UI with tabbed interface"""
        self.setWindowTitle(f"Payment History - {self.loan.loan_name}")
        self.setModal(True)
        self.resize(1000, 700)

        layout = QVBoxLayout(self)

        # Loan context information header
        self.create_loan_context_header(layout)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Payment History tab
        self.create_payment_history_tab()

        # Summary/Statistics tab (future enhancement)
        self.create_summary_tab()

        # Loan Amortization tab
        self.create_amortization_tab()

        # Loan Visualization tab
        self.create_visualization_tab()

        layout.addWidget(self.tab_widget)

        # Dialog buttons
        button_layout = QHBoxLayout()

        close_btn = QPushButton("✅ Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def create_loan_context_header(self, layout):
        """Create loan context information header"""
        context_group = QGroupBox("Loan Information")
        context_layout = QGridLayout(context_group)

        # Row 1
        context_layout.addWidget(QLabel("Loan Name:"), 0, 0)
        context_layout.addWidget(QLabel(f"<b>{self.loan.loan_name}</b>"), 0, 1)

        context_layout.addWidget(QLabel("Original Amount:"), 0, 2)
        context_layout.addWidget(QLabel(f"<b>₹{self.loan.outstanding_amount:,.2f}</b>"), 0, 3)

        # Row 2
        context_layout.addWidget(QLabel("Interest Rate:"), 1, 0)
        context_layout.addWidget(QLabel(f"<b>{self.loan.interest_rate:.2f}%</b>"), 1, 1)

        context_layout.addWidget(QLabel("EMI Amount:"), 1, 2)
        context_layout.addWidget(QLabel(f"<b>₹{self.loan.emi_amount:,.2f}</b>"), 1, 3)

        # Row 3
        context_layout.addWidget(QLabel("Start Date:"), 2, 0)
        start_date_str = self.loan.emi_start_date.strftime('%Y-%m-%d') if self.loan.emi_start_date else "N/A"
        context_layout.addWidget(QLabel(f"<b>{start_date_str}</b>"), 2, 1)

        context_layout.addWidget(QLabel("Current Balance:"), 2, 2)
        current_balance = self.calculate_current_balance()
        context_layout.addWidget(QLabel(f"<b>₹{current_balance:,.2f}</b>"), 2, 3)

        layout.addWidget(context_group)

    def create_payment_history_tab(self):
        """Create the payment history tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Action buttons
        action_layout = QHBoxLayout()

        self.add_payment_btn = QPushButton("➕ Add Payment")
        self.add_payment_btn.clicked.connect(self.add_payment)
        action_layout.addWidget(self.add_payment_btn)

        self.edit_payment_btn = QPushButton("✏️ Edit Payment")
        self.edit_payment_btn.clicked.connect(self.edit_payment)
        self.edit_payment_btn.setEnabled(False)
        action_layout.addWidget(self.edit_payment_btn)

        self.delete_payment_btn = QPushButton("🗑️ Delete Payment")
        self.delete_payment_btn.clicked.connect(self.delete_payment)
        self.delete_payment_btn.setEnabled(False)
        action_layout.addWidget(self.delete_payment_btn)

        # Generate payment history button
        self.generate_payments_btn = QPushButton("🔄 Generate Payment History")
        self.generate_payments_btn.clicked.connect(self.generate_payment_history)
        action_layout.addWidget(self.generate_payments_btn)

        action_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_payment_table)
        action_layout.addWidget(refresh_btn)

        layout.addLayout(action_layout)

        # Payment history table
        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(8)
        self.payment_table.setHorizontalHeaderLabels([
            'Payment Date', 'Principal Amount', 'Interest Amount',
            'Total Payment', 'Remaining Balance', 'Payment Method',
            'Notes', 'Created Date'
        ])

        # Table settings
        self.payment_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.payment_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.payment_table.setAlternatingRowColors(True)
        self.payment_table.setSortingEnabled(True)
        self.payment_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Column resize settings
        header = self.payment_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(6):  # First 6 columns get ResizeToContents
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        # Connect selection signal
        self.payment_table.itemSelectionChanged.connect(self.on_payment_selected)

        layout.addWidget(self.payment_table)

        # Summary statistics
        self.create_summary_statistics(layout)

        self.tab_widget.addTab(tab, "💳 Payment History")

    def create_summary_tab(self):
        """Create summary/statistics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Summary statistics
        stats_group = QGroupBox("Payment Summary")
        stats_layout = QFormLayout(stats_group)

        self.total_payments_label = QLabel("₹0.00")
        self.total_principal_label = QLabel("₹0.00")
        self.total_interest_label = QLabel("₹0.00")
        self.payment_count_label = QLabel("0")
        self.avg_payment_label = QLabel("₹0.00")

        stats_layout.addRow("Total Payments Made:", self.total_payments_label)
        stats_layout.addRow("Total Principal Paid:", self.total_principal_label)
        stats_layout.addRow("Total Interest Paid:", self.total_interest_label)
        stats_layout.addRow("Number of Payments:", self.payment_count_label)
        stats_layout.addRow("Average Payment:", self.avg_payment_label)

        layout.addWidget(stats_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "📊 Summary")

    def create_amortization_tab(self):
        """Create loan amortization tab with comprehensive payment breakdown"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header with loan information
        header_group = QGroupBox("Loan Amortization Schedule")
        header_layout = QFormLayout(header_group)

        # Calculate and display key loan metrics
        emi_calculated = self.loan.calculate_emi()
        stats = self.loan.get_loan_summary_stats()

        header_layout.addRow("Loan Amount:", QLabel(f"₹{self.loan.outstanding_amount:,.2f}"))
        header_layout.addRow("Interest Rate:", QLabel(f"{self.loan.interest_rate:.2f}% per annum"))
        header_layout.addRow("Total Loan Tenure:", QLabel(f"{self.loan.net_tenure} months"))
        header_layout.addRow("Remaining Period:", QLabel(f"{self.loan.remaining_period_months} months"))
        header_layout.addRow("EMI Amount:", QLabel(f"₹{emi_calculated:,.2f}"))
        header_layout.addRow("Total Interest:", QLabel(f"₹{stats['total_interest']:,.2f}"))
        header_layout.addRow("Total Amount Payable:", QLabel(f"₹{stats['total_amount_payable']:,.2f}"))

        layout.addWidget(header_group)

        # Export and Search Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout(controls_group)

        # Search functionality
        search_label = QLabel("Search Payment:")
        self.payment_search_box = QLineEdit()
        self.payment_search_box.setPlaceholderText("Enter payment number or date (e.g., '12' or 'Jan 2024')")
        self.payment_search_box.textChanged.connect(self.filter_amortization_table)

        controls_layout.addWidget(search_label)
        controls_layout.addWidget(self.payment_search_box)

        # Export buttons
        export_csv_btn = QPushButton("📄 Export CSV")
        export_csv_btn.clicked.connect(self.export_amortization_csv)
        export_csv_btn.setToolTip("Export amortization schedule to CSV file")

        export_pdf_btn = QPushButton("📑 Export PDF")
        export_pdf_btn.clicked.connect(self.export_amortization_pdf)
        export_pdf_btn.setToolTip("Export amortization schedule to PDF file")

        print_btn = QPushButton("🖨️ Print")
        print_btn.clicked.connect(self.print_amortization_schedule)
        print_btn.setToolTip("Print amortization schedule")

        controls_layout.addStretch()
        controls_layout.addWidget(export_csv_btn)
        controls_layout.addWidget(export_pdf_btn)
        controls_layout.addWidget(print_btn)

        layout.addWidget(controls_group)

        # Amortization table
        self.amortization_table = QTableWidget()
        self.amortization_table.setColumnCount(6)
        self.amortization_table.setHorizontalHeaderLabels([
            "Payment #", "Payment Date", "Principal (₹)", "Interest (₹)", "Total Payment (₹)", "Remaining Balance (₹)"
        ])
        self.amortization_table.setAlternatingRowColors(True)
        self.amortization_table.setSortingEnabled(True)
        self.amortization_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Set column widths
        header = self.amortization_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Payment #
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Payment Date
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Principal
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Interest
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Total Payment
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Remaining Balance

        layout.addWidget(self.amortization_table)

        # Summary statistics
        summary_group = QGroupBox("Cumulative Totals")
        summary_layout = QHBoxLayout(summary_group)

        self.cumulative_principal_label = QLabel("Total Principal: ₹0")
        self.cumulative_interest_label = QLabel("Total Interest: ₹0")
        self.cumulative_payments_label = QLabel("Total Payments: ₹0")

        self.cumulative_principal_label.setStyleSheet("font-weight: bold; color: #2E8B57;")
        self.cumulative_interest_label.setStyleSheet("font-weight: bold; color: #DC143C;")
        self.cumulative_payments_label.setStyleSheet("font-weight: bold; color: #4169E1;")

        summary_layout.addWidget(self.cumulative_principal_label)
        summary_layout.addWidget(QLabel("|"))
        summary_layout.addWidget(self.cumulative_interest_label)
        summary_layout.addWidget(QLabel("|"))
        summary_layout.addWidget(self.cumulative_payments_label)
        summary_layout.addStretch()

        layout.addWidget(summary_group)

        # Validation status
        validation_group = QGroupBox("Schedule Validation")
        validation_layout = QHBoxLayout(validation_group)

        self.validation_status_label = QLabel("⏳ Validating schedule...")
        self.validation_status_label.setStyleSheet("font-weight: bold; color: #666;")
        validation_layout.addWidget(self.validation_status_label)
        validation_layout.addStretch()

        layout.addWidget(validation_group)

        # Load amortization data
        self.load_amortization_data()

        self.tab_widget.addTab(tab, "📅 Amortization Schedule")

    def create_visualization_tab(self):
        """Create loan visualization tab with multiple chart types"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create scroll area for charts
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Principal vs Interest Pie Chart
        self.create_pie_chart_section(scroll_layout)

        # Payment Schedule Line Graph
        self.create_line_chart_section(scroll_layout)

        # Balance Reduction Chart
        self.create_balance_chart_section(scroll_layout)

        # Interest vs Principal Bar Chart
        self.create_bar_chart_section(scroll_layout)

        # Set scroll widget
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Load visualization data
        self.load_visualization_data()

        self.tab_widget.addTab(tab, "📊 Loan Visualizations")

    def create_summary_statistics(self, layout):
        """Create summary statistics at bottom of payment history"""
        stats_group = QGroupBox("Quick Statistics")
        stats_layout = QHBoxLayout(stats_group)

        self.quick_total_label = QLabel("Total Paid: ₹0.00")
        self.quick_count_label = QLabel("Payments: 0")
        self.quick_balance_label = QLabel("Balance: ₹0.00")

        stats_layout.addWidget(self.quick_total_label)
        stats_layout.addWidget(QLabel("|"))
        stats_layout.addWidget(self.quick_count_label)
        stats_layout.addWidget(QLabel("|"))
        stats_layout.addWidget(self.quick_balance_label)
        stats_layout.addStretch()

        layout.addWidget(stats_group)

    def load_payment_history(self):
        """Load payment history from CSV"""
        try:
            all_payments = self.csv_manager.load_data('loan_payment_history', LoanPayment)
            # Filter payments for this specific loan
            self.payment_history = [p for p in all_payments if p.loan_id == self.loan.id]
            # Sort by payment date (most recent first)
            self.payment_history.sort(key=lambda x: x.payment_date if x.payment_date else date.min, reverse=True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load payment history: {str(e)}")
            self.payment_history = []

    def refresh_payment_table(self):
        """Refresh the payment history table"""
        self.payment_table.setRowCount(len(self.payment_history))

        for row, payment in enumerate(self.payment_history):
            # Payment Date
            date_str = payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else ""
            self.payment_table.setItem(row, 0, QTableWidgetItem(date_str))

            # Principal Amount
            self.payment_table.setItem(row, 1, QTableWidgetItem(f"₹{payment.principal_amount:,.2f}"))

            # Interest Amount
            self.payment_table.setItem(row, 2, QTableWidgetItem(f"₹{payment.interest_amount:,.2f}"))

            # Total Payment
            self.payment_table.setItem(row, 3, QTableWidgetItem(f"₹{payment.total_payment:,.2f}"))

            # Remaining Balance
            self.payment_table.setItem(row, 4, QTableWidgetItem(f"₹{payment.remaining_balance:,.2f}"))

            # Payment Method
            self.payment_table.setItem(row, 5, QTableWidgetItem(payment.payment_method))

            # Notes
            notes_text = payment.notes[:50] + "..." if len(payment.notes) > 50 else payment.notes
            self.payment_table.setItem(row, 6, QTableWidgetItem(notes_text))

            # Created Date
            created_str = payment.created_date.strftime('%Y-%m-%d') if payment.created_date else ""
            self.payment_table.setItem(row, 7, QTableWidgetItem(created_str))

        # Update statistics
        self.update_statistics()

    def update_statistics(self):
        """Update all statistics displays"""
        if not self.payment_history:
            # Reset all statistics to zero
            self.quick_total_label.setText("Total Paid: ₹0.00")
            self.quick_count_label.setText("Payments: 0")
            self.quick_balance_label.setText("Balance: ₹0.00")

            if hasattr(self, 'total_payments_label'):
                self.total_payments_label.setText("₹0.00")
                self.total_principal_label.setText("₹0.00")
                self.total_interest_label.setText("₹0.00")
                self.payment_count_label.setText("0")
                self.avg_payment_label.setText("₹0.00")
            return

        # Calculate statistics
        total_payments = sum(p.total_payment for p in self.payment_history)
        total_principal = sum(p.principal_amount for p in self.payment_history)
        total_interest = sum(p.interest_amount for p in self.payment_history)
        payment_count = len(self.payment_history)
        avg_payment = total_payments / payment_count if payment_count > 0 else 0
        current_balance = self.calculate_current_balance()

        # Update quick statistics
        self.quick_total_label.setText(f"Total Paid: ₹{total_payments:,.2f}")
        self.quick_count_label.setText(f"Payments: {payment_count}")
        self.quick_balance_label.setText(f"Balance: ₹{current_balance:,.2f}")

        # Update detailed statistics if available
        if hasattr(self, 'total_payments_label'):
            self.total_payments_label.setText(f"₹{total_payments:,.2f}")
            self.total_principal_label.setText(f"₹{total_principal:,.2f}")
            self.total_interest_label.setText(f"₹{total_interest:,.2f}")
            self.payment_count_label.setText(str(payment_count))
            self.avg_payment_label.setText(f"₹{avg_payment:,.2f}")

    def calculate_current_balance(self):
        """Calculate current loan balance based on payment history"""
        if not self.payment_history:
            return self.loan.outstanding_amount

        # Get the most recent payment's remaining balance
        # Payments are sorted by date (most recent first)
        return self.payment_history[0].remaining_balance if self.payment_history else self.loan.outstanding_amount

    def on_payment_selected(self):
        """Handle payment selection"""
        current_row = self.payment_table.currentRow()
        if current_row >= 0 and current_row < len(self.payment_history):
            self.edit_payment_btn.setEnabled(True)
            self.delete_payment_btn.setEnabled(True)
        else:
            self.edit_payment_btn.setEnabled(False)
            self.delete_payment_btn.setEnabled(False)

    def add_payment(self):
        """Add new payment entry"""
        dialog = LoanPaymentEntryDialog(loan=self.loan, parent=self)
        if dialog.exec() == QDialog.Accepted:
            payment = dialog.get_payment()

            # Validate payment
            errors = payment.validate()
            if errors:
                QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                return

            # Add to payment history
            self.payment_history.append(payment)

            # Save to CSV
            self.save_payment_history()

            # Refresh display
            self.refresh_payment_table()

            QMessageBox.information(self, "Success", "Payment added successfully!")

    def edit_payment(self):
        """Edit selected payment"""
        current_row = self.payment_table.currentRow()
        if current_row >= 0 and current_row < len(self.payment_history):
            selected_payment = self.payment_history[current_row]
            dialog = LoanPaymentEntryDialog(payment=selected_payment, loan=self.loan, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_payment = dialog.get_payment()

                # Validate payment
                errors = updated_payment.validate()
                if errors:
                    QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                    return

                # Update payment history
                self.payment_history[current_row] = updated_payment

                # Save to CSV
                self.save_payment_history()

                # Refresh display
                self.refresh_payment_table()

                QMessageBox.information(self, "Success", "Payment updated successfully!")

    def delete_payment(self):
        """Delete selected payment"""
        current_row = self.payment_table.currentRow()
        if current_row >= 0 and current_row < len(self.payment_history):
            selected_payment = self.payment_history[current_row]

            reply = QMessageBox.question(
                self, "Delete Payment",
                f"Are you sure you want to delete the payment of ₹{selected_payment.total_payment:,.2f} "
                f"made on {selected_payment.payment_date}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Remove from payment history
                self.payment_history.pop(current_row)

                # Save to CSV
                self.save_payment_history()

                # Refresh display
                self.refresh_payment_table()

                # Disable buttons
                self.edit_payment_btn.setEnabled(False)
                self.delete_payment_btn.setEnabled(False)

                QMessageBox.information(self, "Success", "Payment deleted successfully!")

    def save_payment_history(self):
        """Save payment history to CSV"""
        try:
            # Load all payments from CSV
            all_payments = self.csv_manager.load_data('loan_payment_history', LoanPayment)

            # Remove existing payments for this loan
            other_loan_payments = [p for p in all_payments if p.loan_id != self.loan.id]

            # Combine with current loan's payments
            updated_payments = other_loan_payments + self.payment_history

            # Save back to CSV
            self.csv_manager.save_data('loan_payment_history', updated_payments)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save payment history: {str(e)}")

    def generate_payment_history(self):
        """Generate payment history using the PaymentGenerationDialog"""
        try:
            # Show generation dialog
            dialog = PaymentGenerationDialog(self.loan, self.payment_history, parent=self)
            if dialog.exec() == QDialog.Accepted:
                params = dialog.get_generation_params()

                if params['preview_count'] > 0:
                    # Show progress dialog for large number of payments
                    if params['preview_count'] > 12:
                        progress = QProgressDialog(
                            "Generating payment records...", "Cancel",
                            0, params['preview_count'], self
                        )
                        progress.setWindowModality(Qt.WindowModal)
                        progress.show()
                    else:
                        progress = None

                    # Generate the payments
                    generated_count = self.generate_payments_to_date(params['end_date'], progress)

                    if progress:
                        progress.close()

                    if generated_count > 0:
                        # Save the updated payment history
                        self.save_payment_history()

                        # Refresh the display
                        self.refresh_payment_table()

                        # Show success message
                        end_month_year = params['end_date'].strftime('%B %Y')
                        QMessageBox.information(
                            self, "Success",
                            f"Generated {generated_count} new payment records up to {end_month_year}!"
                        )
                    else:
                        QMessageBox.information(
                            self, "Info",
                            "No new payment records were generated."
                        )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate payment history: {str(e)}")

    def generate_payments_to_date(self, end_date, progress=None):
        """Generate monthly EMI payments from loan start to end date"""
        try:
            if not self.loan.emi_start_date or not self.loan.emi_amount:
                raise ValueError("Loan EMI start date and amount must be set")

            # Get loan start date
            start_date = self.loan.emi_start_date.date() if isinstance(self.loan.emi_start_date, datetime) else self.loan.emi_start_date

            # Create set of existing payment months for quick lookup
            existing_payment_months = set()
            for payment in self.payment_history:
                if payment.payment_date:
                    month_key = (payment.payment_date.year, payment.payment_date.month)
                    existing_payment_months.add(month_key)

            # Calculate monthly interest rate
            monthly_interest_rate = self.loan.interest_rate / 100 / 12

            # Start with original loan amount
            current_balance = self.loan.outstanding_amount

            # Generate payments month by month
            generated_count = 0
            current_date = start_date.replace(day=1)  # Start from first day of start month

            # If we have existing payments, we need to calculate the current balance
            # based on the most recent payment
            if self.payment_history:
                # Sort existing payments by date
                sorted_payments = sorted(self.payment_history, key=lambda x: x.payment_date if x.payment_date else date.min)

                # Find the most recent payment to get current balance
                if sorted_payments:
                    current_balance = sorted_payments[-1].remaining_balance

                    # Start generation from the month after the most recent payment
                    last_payment_date = sorted_payments[-1].payment_date
                    if last_payment_date:
                        if last_payment_date.month == 12:
                            current_date = date(last_payment_date.year + 1, 1, 1)
                        else:
                            current_date = date(last_payment_date.year, last_payment_date.month + 1, 1)

            payment_number = 0
            while current_date <= end_date and current_balance > 0.01:  # Stop when balance is essentially zero
                month_key = (current_date.year, current_date.month)

                # Only generate if payment doesn't already exist for this month
                if month_key not in existing_payment_months:
                    # Calculate interest for this month
                    interest_amount = current_balance * monthly_interest_rate

                    # Calculate principal amount
                    principal_amount = min(self.loan.emi_amount - interest_amount, current_balance)

                    # Ensure principal is not negative
                    if principal_amount < 0:
                        principal_amount = current_balance
                        interest_amount = self.loan.emi_amount - principal_amount

                    # Calculate total payment (might be less than EMI for final payment)
                    total_payment = principal_amount + interest_amount

                    # Update remaining balance
                    new_balance = max(0, current_balance - principal_amount)

                    # Create payment record
                    # Set payment date to a reasonable day in the month (e.g., loan start day or 1st)
                    payment_day = start_date.day if start_date.day <= 28 else 1  # Avoid issues with months having fewer days
                    try:
                        payment_date = current_date.replace(day=payment_day)
                    except ValueError:
                        # Handle case where day doesn't exist in current month (e.g., Feb 30)
                        payment_date = current_date.replace(day=1)

                    payment = LoanPayment(
                        loan_id=self.loan.id,
                        payment_date=payment_date,
                        principal_amount=round(principal_amount, 2),
                        interest_amount=round(interest_amount, 2),
                        total_payment=round(total_payment, 2),
                        remaining_balance=round(new_balance, 2),
                        payment_method="Auto-Generated",
                        notes="Generated payment record"
                    )

                    # Add to payment history
                    self.payment_history.append(payment)
                    generated_count += 1

                    # Update current balance for next iteration
                    current_balance = new_balance

                    # Update progress if provided
                    if progress:
                        progress.setValue(generated_count)
                        if progress.wasCanceled():
                            break

                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

                payment_number += 1

                # Safety check to prevent infinite loops
                if payment_number > 1000:  # Max 1000 payments (about 83 years)
                    break

            return generated_count

        except Exception as e:
            raise Exception(f"Error generating payments: {str(e)}")

    def load_amortization_data(self):
        """Load and display amortization schedule data with progress indicator and validation"""
        try:
            # Show progress dialog for long-term loans
            if self.loan.net_tenure > 60:  # More than 5 years
                progress = QProgressDialog(
                    "Generating amortization schedule...", "Cancel",
                    0, 100, self
                )
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
                progress.setValue(10)
            else:
                progress = None

            # Generate schedule
            schedule = self.loan.generate_amortization_schedule()

            if progress:
                progress.setValue(50)

            if not schedule:
                if progress:
                    progress.close()
                self.amortization_table.setRowCount(1)
                self.amortization_table.setItem(0, 0, QTableWidgetItem("No data"))
                self.amortization_table.setItem(0, 1, QTableWidgetItem("Unable to generate"))
                self.amortization_table.setItem(0, 2, QTableWidgetItem("₹0"))
                self.amortization_table.setItem(0, 3, QTableWidgetItem("₹0"))
                self.amortization_table.setItem(0, 4, QTableWidgetItem("₹0"))
                self.amortization_table.setItem(0, 5, QTableWidgetItem("₹0"))
                return

            # Validate the schedule
            validation = self.loan.validate_amortization_schedule(schedule)

            if progress:
                progress.setValue(70)

            # Display validation results if there are errors
            if not validation['valid']:
                QMessageBox.warning(
                    self, "Amortization Validation Warning",
                    f"Schedule validation found issues:\n" + "\n".join(validation['errors'])
                )

            # Populate the table with ALL payments
            self.amortization_table.setRowCount(len(schedule))

            cumulative_principal = 0
            cumulative_interest = 0
            cumulative_payments = 0

            # Use batch updates for better performance with large tables
            self.amortization_table.setUpdatesEnabled(False)

            try:
                for row, payment in enumerate(schedule):
                    if progress and row % 50 == 0:  # Update progress every 50 rows
                        progress.setValue(70 + (row / len(schedule)) * 25)
                        if progress.wasCanceled():
                            return

                    # Payment Number
                    self.amortization_table.setItem(row, 0, QTableWidgetItem(str(payment['payment_number'])))

                    # Payment Date
                    date_str = payment['payment_date'].strftime('%b %Y')
                    self.amortization_table.setItem(row, 1, QTableWidgetItem(date_str))

                    # Principal Amount
                    principal_item = QTableWidgetItem(f"₹{payment['principal_amount']:,.2f}")
                    principal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.amortization_table.setItem(row, 2, principal_item)

                    # Interest Amount
                    interest_item = QTableWidgetItem(f"₹{payment['interest_amount']:,.2f}")
                    interest_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.amortization_table.setItem(row, 3, interest_item)

                    # Total Payment
                    total_item = QTableWidgetItem(f"₹{payment['total_payment']:,.2f}")
                    total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.amortization_table.setItem(row, 4, total_item)

                    # Remaining Balance
                    balance_item = QTableWidgetItem(f"₹{payment['remaining_balance']:,.2f}")
                    balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                    # Color code the remaining balance
                    if payment['remaining_balance'] == 0.00:
                        balance_item.setBackground(QColor("#2d5a2d"))  # Dark green for final payment
                        balance_item.setForeground(QColor("#90ee90"))  # Light green text
                        balance_item.setFont(QFont("Arial", 10, QFont.Bold))
                    elif payment['remaining_balance'] < self.loan.outstanding_amount * 0.25:
                        balance_item.setBackground(QColor("#5a5a2d"))  # Dark yellow for last quarter
                        balance_item.setForeground(QColor("#ffff90"))  # Light yellow text

                    self.amortization_table.setItem(row, 5, balance_item)

                    # Update cumulative totals
                    cumulative_principal += payment['principal_amount']
                    cumulative_interest += payment['interest_amount']
                    cumulative_payments += payment['total_payment']

            finally:
                self.amortization_table.setUpdatesEnabled(True)

            if progress:
                progress.setValue(95)

            # Update summary labels with validation info
            self.cumulative_principal_label.setText(f"Total Principal: ₹{cumulative_principal:,.2f}")
            self.cumulative_interest_label.setText(f"Total Interest: ₹{cumulative_interest:,.2f}")
            self.cumulative_payments_label.setText(f"Total Payments: ₹{cumulative_payments:,.2f}")

            # Add validation status
            if hasattr(self, 'validation_status_label'):
                if validation['valid']:
                    self.validation_status_label.setText("✅ Schedule validated successfully")
                    self.validation_status_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.validation_status_label.setText(f"⚠️ Validation issues found ({len(validation['errors'])})")
                    self.validation_status_label.setStyleSheet("color: orange; font-weight: bold;")

            if progress:
                progress.setValue(100)
                progress.close()

        except Exception as e:
            if 'progress' in locals() and progress:
                progress.close()
            QMessageBox.warning(self, "Error", f"Failed to load amortization data: {str(e)}")

    def create_pie_chart_section(self, layout):
        """Create principal vs interest pie chart section with interactive chart"""
        chart_group = QGroupBox("💰 Principal vs Interest Distribution")
        chart_layout = QVBoxLayout(chart_group)

        # Create interactive chart widget
        self.pie_chart_widget = LoanChartWidget()
        self.pie_chart_widget.setMinimumHeight(400)

        chart_layout.addWidget(self.pie_chart_widget)
        layout.addWidget(chart_group)

    def create_line_chart_section(self, layout):
        """Create payment schedule line graph section with interactive chart"""
        chart_group = QGroupBox("📈 Monthly Payment Schedule")
        chart_layout = QVBoxLayout(chart_group)

        # Create interactive chart widget
        self.line_chart_widget = LoanChartWidget()
        self.line_chart_widget.setMinimumHeight(400)

        chart_layout.addWidget(self.line_chart_widget)
        layout.addWidget(chart_group)

    def create_balance_chart_section(self, layout):
        """Create balance reduction area chart section with interactive chart"""
        chart_group = QGroupBox("📉 Outstanding Balance Reduction")
        chart_layout = QVBoxLayout(chart_group)

        # Create interactive chart widget
        self.balance_chart_widget = LoanChartWidget()
        self.balance_chart_widget.setMinimumHeight(400)

        chart_layout.addWidget(self.balance_chart_widget)
        layout.addWidget(chart_group)

    def create_bar_chart_section(self, layout):
        """Create interest vs principal stacked bar chart section with interactive chart"""
        chart_group = QGroupBox("📊 Monthly Principal vs Interest Breakdown")
        chart_layout = QVBoxLayout(chart_group)

        # Create interactive chart widget
        self.bar_chart_widget = LoanChartWidget()
        self.bar_chart_widget.setMinimumHeight(400)

        chart_layout.addWidget(self.bar_chart_widget)
        layout.addWidget(chart_group)

    def load_visualization_data(self):
        """Load and display interactive visualization data"""
        try:
            chart_data = self.loan.get_chart_data()
            stats = self.loan.get_loan_summary_stats()

            # Update pie chart with interactive matplotlib chart
            if chart_data['pie_chart_data'] and hasattr(self, 'pie_chart_widget'):
                if MATPLOTLIB_AVAILABLE:
                    self.pie_chart_widget.create_pie_chart(
                        chart_data['pie_chart_data'],
                        f"Total Payment Breakdown\n₹{stats['total_amount_payable']:,.0f}"
                    )
                else:
                    # Fallback text representation
                    pie_text = "Principal vs Interest Distribution:\n\n"
                    for label, value in chart_data['pie_chart_data']:
                        percentage = (value / stats['total_amount_payable'] * 100) if stats['total_amount_payable'] > 0 else 0
                        pie_text += f"{label}: ₹{value:,.2f} ({percentage:.1f}%)\n"
                    self.pie_chart_widget.set_fallback_text(pie_text)

            # Update line chart with interactive matplotlib chart
            if chart_data['line_chart_data'] and hasattr(self, 'line_chart_widget'):
                if MATPLOTLIB_AVAILABLE:
                    self.line_chart_widget.create_line_chart(
                        chart_data['line_chart_data'],
                        "Monthly Payment Schedule",
                        "Payment Date",
                        "Payment Amount (₹)"
                    )
                else:
                    # Fallback text representation
                    line_text = "Monthly EMI Payments:\n\n"
                    for i, (date, payment) in enumerate(chart_data['line_chart_data'][:12]):
                        line_text += f"{date.strftime('%b %Y')}: ₹{payment:,.2f}\n"
                    if len(chart_data['line_chart_data']) > 12:
                        line_text += f"... and {len(chart_data['line_chart_data']) - 12} more payments"
                    self.line_chart_widget.set_fallback_text(line_text)

            # Update balance chart with interactive area chart
            if chart_data['balance_chart_data'] and hasattr(self, 'balance_chart_widget'):
                if MATPLOTLIB_AVAILABLE:
                    self.balance_chart_widget.create_area_chart(
                        chart_data['balance_chart_data'],
                        "Outstanding Balance Reduction",
                        "Payment Date",
                        "Remaining Balance (₹)"
                    )
                else:
                    # Fallback text representation
                    balance_text = "Balance Reduction Milestones:\n\n"
                    milestones = [0, len(chart_data['balance_chart_data'])//4, len(chart_data['balance_chart_data'])//2,
                                 3*len(chart_data['balance_chart_data'])//4, len(chart_data['balance_chart_data'])-1]
                    for i in milestones:
                        if i < len(chart_data['balance_chart_data']):
                            date, balance = chart_data['balance_chart_data'][i]
                            balance_text += f"{date.strftime('%b %Y')}: ₹{balance:,.2f}\n"
                    self.balance_chart_widget.set_fallback_text(balance_text)

            # Update bar chart with interactive stacked bar chart
            if chart_data['bar_chart_data'] and hasattr(self, 'bar_chart_widget'):
                if MATPLOTLIB_AVAILABLE:
                    self.bar_chart_widget.create_stacked_bar_chart(
                        chart_data['bar_chart_data'],
                        "Monthly Principal vs Interest (First 24 Months)"
                    )
                else:
                    # Fallback text representation
                    bar_text = "Principal vs Interest Breakdown:\n\n"
                    for payment in chart_data['bar_chart_data']:
                        bar_text += f"{payment['month']}: P:₹{payment['principal']:,.0f} I:₹{payment['interest']:,.0f}\n"
                    self.bar_chart_widget.set_fallback_text(bar_text)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load visualization data: {str(e)}")

    def filter_amortization_table(self):
        """Filter the amortization table based on search text"""
        try:
            if not hasattr(self, 'payment_search_box') or not hasattr(self, 'amortization_table'):
                return

            search_text = self.payment_search_box.text().lower()
            if not search_text:
                # Show all rows if search is empty
                for row in range(self.amortization_table.rowCount()):
                    self.amortization_table.setRowHidden(row, False)
                return

            # Hide rows that don't match the search
            for row in range(self.amortization_table.rowCount()):
                payment_num_item = self.amortization_table.item(row, 0)
                payment_date_item = self.amortization_table.item(row, 1)

                if payment_num_item and payment_date_item:
                    payment_num = payment_num_item.text().lower()
                    payment_date = payment_date_item.text().lower()

                    if search_text in payment_num or search_text in payment_date:
                        self.amortization_table.setRowHidden(row, False)
                    else:
                        self.amortization_table.setRowHidden(row, True)
        except Exception as e:
            print(f"Error filtering amortization table: {e}")

    def export_amortization_csv(self):
        """Export amortization schedule to CSV file"""
        try:
            from PySide6.QtWidgets import QFileDialog
            import csv

            # Get file path from user
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Amortization Schedule",
                f"{self.loan.loan_name}_amortization.csv",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # Show progress dialog for large schedules
            if self.amortization_table.rowCount() > 100:
                progress = QProgressDialog(
                    "Exporting amortization schedule...", "Cancel",
                    0, self.amortization_table.rowCount(), self
                )
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
            else:
                progress = None

            # Write to CSV
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header row with loan details
                writer.writerow([f"Loan Amortization Schedule - {self.loan.loan_name}"])
                writer.writerow([f"Loan Amount: ₹{self.loan.outstanding_amount:,.2f}"])
                writer.writerow([f"Interest Rate: {self.loan.interest_rate:.2f}% per annum"])
                writer.writerow([f"Total Loan Tenure: {self.loan.net_tenure} months"])
                writer.writerow([f"Remaining Period: {self.loan.remaining_period_months} months"])
                writer.writerow([])

                # Write column headers
                headers = []
                for col in range(self.amortization_table.columnCount()):
                    headers.append(self.amortization_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)

                # Write data rows
                for row in range(self.amortization_table.rowCount()):
                    if progress:
                        progress.setValue(row)
                        if progress.wasCanceled():
                            break

                    row_data = []
                    for col in range(self.amortization_table.columnCount()):
                        # Remove currency symbols and formatting for CSV
                        text = self.amortization_table.item(row, col).text()
                        if col >= 2:  # Columns with currency
                            text = text.replace('₹', '').replace(',', '')
                        row_data.append(text)
                    writer.writerow(row_data)

            if progress:
                progress.close()

            QMessageBox.information(self, "Export Successful",
                                   f"Amortization schedule exported to:\n{file_path}")

        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export CSV: {str(e)}")

    def export_amortization_pdf(self):
        """Export amortization schedule to PDF file"""
        try:
            from PySide6.QtWidgets import QFileDialog
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtGui import QTextDocument

            # Get file path from user
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Amortization Schedule",
                f"{self.loan.loan_name}_amortization.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            # Show progress dialog
            progress = QProgressDialog(
                "Generating PDF...", "Cancel", 0, 100, self
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            progress.setValue(10)

            # Create HTML content
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    h1 {{ color: #333366; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #dddddd; text-align: right; padding: 8px; }}
                    th {{ background-color: #f2f2f2; }}
                    .header {{ background-color: #eeeeff; font-weight: bold; }}
                    .zero-balance {{ background-color: #e6ffe6; }}
                </style>
            </head>
            <body>
                <h1>Loan Amortization Schedule - {self.loan.loan_name}</h1>
                <p><b>Loan Amount:</b> ₹{self.loan.outstanding_amount:,.2f}</p>
                <p><b>Interest Rate:</b> {self.loan.interest_rate:.2f}% per annum</p>
                <p><b>Total Loan Tenure:</b> {self.loan.net_tenure} months</p>
                <p><b>Remaining Period:</b> {self.loan.remaining_period_months} months</p>
                <p><b>EMI Amount:</b> ₹{self.loan.emi_amount:,.2f}</p>
                <p><b>Total Interest:</b> ₹{self.loan.get_loan_summary_stats()['total_interest']:,.2f}</p>
                <p><b>Total Amount Payable:</b> ₹{self.loan.get_loan_summary_stats()['total_amount_payable']:,.2f}</p>

                <h2>Amortization Table</h2>
                <table>
                    <tr class="header">
            """

            # Add table headers
            for col in range(self.amortization_table.columnCount()):
                html += f"<th>{self.amortization_table.horizontalHeaderItem(col).text()}</th>"
            html += "</tr>"

            progress.setValue(30)

            # Add table rows (limit to first 300 rows for PDF performance)
            max_rows = min(300, self.amortization_table.rowCount())
            for row in range(max_rows):
                if progress and row % 20 == 0:
                    progress.setValue(30 + (row / max_rows) * 60)
                    if progress.wasCanceled():
                        return

                # Check if this is the final payment (zero balance)
                is_final = False
                if row < self.amortization_table.rowCount():
                    balance_text = self.amortization_table.item(row, 5).text()
                    if balance_text == "₹0.00":
                        is_final = True

                html += f'<tr class="{"zero-balance" if is_final else ""}">'
                for col in range(self.amortization_table.columnCount()):
                    if row < self.amortization_table.rowCount():
                        cell_text = self.amortization_table.item(row, col).text()
                        html += f"<td>{cell_text}</td>"
                    else:
                        html += "<td></td>"
                html += "</tr>"

            # Add note if we limited the rows
            if self.amortization_table.rowCount() > max_rows:
                html += f"""
                <tr>
                    <td colspan="{self.amortization_table.columnCount()}" style="text-align: center;">
                        <i>Note: PDF limited to first {max_rows} payments. Export to CSV for complete schedule.</i>
                    </td>
                </tr>
                """

            html += """
                </table>
                <p><i>Generated by Traqify Investment Tracker</i></p>
            </body>
            </html>
            """

            progress.setValue(90)

            # Create printer and print to PDF
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)

            document = QTextDocument()
            document.setHtml(html)
            document.print_(printer)

            progress.setValue(100)
            progress.close()

            QMessageBox.information(self, "Export Successful",
                                   f"Amortization schedule exported to:\n{file_path}")

        except Exception as e:
            if 'progress' in locals() and progress:
                progress.close()
            QMessageBox.warning(self, "Export Error", f"Failed to export PDF: {str(e)}")

    def print_amortization_schedule(self):
        """Print the amortization schedule"""
        try:
            from PySide6.QtPrintSupport import QPrintDialog, QPrinter
            from PySide6.QtGui import QTextDocument

            # Create printer
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)

            if dialog.exec() != QDialog.Accepted:
                return

            # Show progress dialog
            progress = QProgressDialog(
                "Preparing document for printing...", "Cancel", 0, 100, self
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            progress.setValue(10)

            # Create HTML content (similar to PDF export)
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    h1 {{ color: #333366; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #dddddd; text-align: right; padding: 8px; }}
                    th {{ background-color: #f2f2f2; }}
                    .header {{ background-color: #eeeeff; font-weight: bold; }}
                    .zero-balance {{ background-color: #e6ffe6; }}
                </style>
            </head>
            <body>
                <h1>Loan Amortization Schedule - {self.loan.loan_name}</h1>
                <p><b>Loan Amount:</b> ₹{self.loan.outstanding_amount:,.2f}</p>
                <p><b>Interest Rate:</b> {self.loan.interest_rate:.2f}% per annum</p>
                <p><b>Total Loan Tenure:</b> {self.loan.net_tenure} months</p>
                <p><b>Remaining Period:</b> {self.loan.remaining_period_months} months</p>
                <p><b>EMI Amount:</b> ₹{self.loan.emi_amount:,.2f}</p>

                <h2>Amortization Table</h2>
                <table>
                    <tr class="header">
            """

            # Add table headers
            for col in range(self.amortization_table.columnCount()):
                html += f"<th>{self.amortization_table.horizontalHeaderItem(col).text()}</th>"
            html += "</tr>"

            progress.setValue(30)

            # Add table rows (limit to first 200 rows for printing performance)
            max_rows = min(200, self.amortization_table.rowCount())
            for row in range(max_rows):
                if progress and row % 20 == 0:
                    progress.setValue(30 + (row / max_rows) * 60)
                    if progress.wasCanceled():
                        return

                # Check if this is the final payment (zero balance)
                is_final = False
                if row < self.amortization_table.rowCount():
                    balance_text = self.amortization_table.item(row, 5).text()
                    if balance_text == "₹0.00":
                        is_final = True

                html += f'<tr class="{"zero-balance" if is_final else ""}">'
                for col in range(self.amortization_table.columnCount()):
                    if row < self.amortization_table.rowCount():
                        cell_text = self.amortization_table.item(row, col).text()
                        html += f"<td>{cell_text}</td>"
                    else:
                        html += "<td></td>"
                html += "</tr>"

            # Add note if we limited the rows
            if self.amortization_table.rowCount() > max_rows:
                html += f"""
                <tr>
                    <td colspan="{self.amortization_table.columnCount()}" style="text-align: center;">
                        <i>Note: Print limited to first {max_rows} payments. Export to CSV for complete schedule.</i>
                    </td>
                </tr>
                """

            html += """
                </table>
                <p><i>Generated by Traqify Investment Tracker</i></p>
            </body>
            </html>
            """

            progress.setValue(90)

            # Print the document
            document = QTextDocument()
            document.setHtml(html)
            document.print_(printer)

            progress.setValue(100)
            progress.close()

        except Exception as e:
            if 'progress' in locals() and progress:
                progress.close()
            QMessageBox.warning(self, "Print Error", f"Failed to print schedule: {str(e)}")


class PaymentGenerationDialog(QDialog):
    """Dialog for selecting month range and generating payment history"""

    def __init__(self, loan, existing_payments, parent=None):
        super().__init__(parent)
        self.loan = loan
        self.existing_payments = existing_payments
        self.selected_end_date = None
        self.preview_count = 0
        self.setup_ui()
        self.calculate_preview()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Generate Payment History")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Header information
        header_group = QGroupBox("Loan Information")
        header_layout = QFormLayout(header_group)

        header_layout.addRow("Loan Name:", QLabel(f"<b>{self.loan.loan_name}</b>"))
        header_layout.addRow("EMI Amount:", QLabel(f"<b>₹{self.loan.emi_amount:,.2f}</b>"))
        header_layout.addRow("Interest Rate:", QLabel(f"<b>{self.loan.interest_rate:.2f}%</b>"))

        start_date_str = self.loan.emi_start_date.strftime('%B %Y') if self.loan.emi_start_date else "N/A"
        header_layout.addRow("EMI Start Date:", QLabel(f"<b>{start_date_str}</b>"))

        layout.addWidget(header_group)

        # Generation settings
        settings_group = QGroupBox("Generation Settings")
        settings_layout = QFormLayout(settings_group)

        # End month selection
        month_layout = QHBoxLayout()

        self.end_month_combo = QComboBox()
        self.end_month_combo.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])

        self.end_year_spin = QSpinBox()
        self.end_year_spin.setRange(2020, 2030)
        self.end_year_spin.setValue(datetime.now().year)

        # Set current month as default
        current_month = datetime.now().month - 1  # 0-based index
        self.end_month_combo.setCurrentIndex(current_month)

        month_layout.addWidget(QLabel("Month:"))
        month_layout.addWidget(self.end_month_combo)
        month_layout.addWidget(QLabel("Year:"))
        month_layout.addWidget(self.end_year_spin)
        month_layout.addStretch()

        settings_layout.addRow("Generate up to:", month_layout)

        # Connect signals for preview update
        self.end_month_combo.currentIndexChanged.connect(self.calculate_preview)
        self.end_year_spin.valueChanged.connect(self.calculate_preview)

        layout.addWidget(settings_group)

        # Preview information
        self.preview_group = QGroupBox("Generation Preview")
        preview_layout = QVBoxLayout(self.preview_group)

        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_label)

        # Existing payments info
        self.existing_info_label = QLabel()
        self.existing_info_label.setWordWrap(True)
        self.existing_info_label.setStyleSheet("color: #666; font-style: italic;")
        preview_layout.addWidget(self.existing_info_label)

        layout.addWidget(self.preview_group)

        # Warning/Info section
        warning_group = QGroupBox("Important Notes")
        warning_layout = QVBoxLayout(warning_group)

        warning_text = QLabel(
            "• Only missing payment records will be generated\n"
            "• Existing manual payments will not be modified\n"
            "• Generated payments will be marked as 'Auto-Generated'\n"
            "• Interest calculations are based on reducing balance method"
        )
        warning_text.setWordWrap(True)
        warning_text.setStyleSheet("color: #444;")
        warning_layout.addWidget(warning_text)

        layout.addWidget(warning_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.generate_btn = QPushButton("🔄 Generate Payments")
        self.generate_btn.clicked.connect(self.accept)
        self.generate_btn.setEnabled(False)  # Will be enabled when preview shows records to generate
        button_layout.addWidget(self.generate_btn)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def calculate_preview(self):
        """Calculate and display preview of payments to be generated"""
        try:
            # Get selected end date
            end_month = self.end_month_combo.currentIndex() + 1  # Convert to 1-based
            end_year = self.end_year_spin.value()

            # Create end date (last day of selected month)
            last_day = calendar.monthrange(end_year, end_month)[1]
            self.selected_end_date = date(end_year, end_month, last_day)

            # Get loan start date
            if not self.loan.emi_start_date:
                self.preview_label.setText("❌ Loan EMI start date is not set. Cannot generate payments.")
                self.generate_btn.setEnabled(False)
                return

            start_date = self.loan.emi_start_date.date() if isinstance(self.loan.emi_start_date, datetime) else self.loan.emi_start_date

            # Check if end date is after start date
            if self.selected_end_date < start_date:
                self.preview_label.setText("❌ Selected end date is before loan start date.")
                self.generate_btn.setEnabled(False)
                return

            # Calculate months between start and end
            months_diff = (self.selected_end_date.year - start_date.year) * 12 + (self.selected_end_date.month - start_date.month)
            total_possible_payments = months_diff + 1

            # Count existing payments
            existing_payment_months = set()
            for payment in self.existing_payments:
                if payment.payment_date:
                    payment_month_key = (payment.payment_date.year, payment.payment_date.month)
                    existing_payment_months.add(payment_month_key)

            # Calculate missing payments
            missing_payments = 0
            current_date = start_date.replace(day=1)  # Start from first day of start month

            while current_date <= self.selected_end_date:
                month_key = (current_date.year, current_date.month)
                if month_key not in existing_payment_months:
                    missing_payments += 1

                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

            self.preview_count = missing_payments

            # Update preview text
            if missing_payments > 0:
                self.preview_label.setText(
                    f"✅ <b>{missing_payments}</b> new payment records will be generated\n"
                    f"📅 From: <b>{start_date.strftime('%B %Y')}</b> to <b>{self.selected_end_date.strftime('%B %Y')}</b>\n"
                    f"💰 Total amount: <b>₹{missing_payments * self.loan.emi_amount:,.2f}</b>"
                )
                self.generate_btn.setEnabled(True)
            else:
                self.preview_label.setText(
                    f"ℹ️ No new payments to generate. All payment records already exist\n"
                    f"up to <b>{self.selected_end_date.strftime('%B %Y')}</b>."
                )
                self.generate_btn.setEnabled(False)

            # Update existing payments info
            existing_count = len(existing_payment_months)
            if existing_count > 0:
                self.existing_info_label.setText(
                    f"📋 {existing_count} existing payment record(s) will be preserved unchanged."
                )
            else:
                self.existing_info_label.setText("📋 No existing payment records found.")

        except Exception as e:
            self.preview_label.setText(f"❌ Error calculating preview: {str(e)}")
            self.generate_btn.setEnabled(False)

    def get_generation_params(self):
        """Get the parameters for payment generation"""
        return {
            'end_date': self.selected_end_date,
            'preview_count': self.preview_count
        }


class InsurancePolicyDialog(QDialog):
    """Enhanced dialog for adding/editing insurance policies"""

    def __init__(self, policy=None, policy_types=None, parent=None):
        super().__init__(parent)
        self.policy = policy if policy else InsurancePolicy()
        self.policy_types = policy_types if policy_types else [
            "Vehicle Insurance", "Health Insurance", "Life Insurance", "Property Insurance"
        ]
        self.payment_frequencies = ["Monthly", "Quarterly", "Semi-Annual", "Annual"]
        self.status_options = ["Active", "Expired", "Pending Renewal", "Cancelled", "Lapsed"]
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the enhanced dialog UI"""
        self.setWindowTitle("Add/Edit Insurance Policy")
        self.setModal(True)
        self.resize(650, 700)

        main_layout = QVBoxLayout(self)

        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Basic Information Section
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)

        # Policy Name/Description
        self.policy_name_edit = QLineEdit()
        self.policy_name_edit.setPlaceholderText("Enter policy name or description")
        basic_layout.addRow("Policy Name/Description*:", self.policy_name_edit)

        # Insurance Provider/Company
        self.insurance_provider_edit = QLineEdit()
        self.insurance_provider_edit.setPlaceholderText("e.g., LIC, HDFC ERGO, ICICI Lombard")
        basic_layout.addRow("Insurance Provider/Company*:", self.insurance_provider_edit)

        # Policy Type
        self.policy_type_combo = QComboBox()
        self.policy_type_combo.setEditable(True)
        self.policy_type_combo.addItems(self.policy_types)
        basic_layout.addRow("Policy Type*:", self.policy_type_combo)

        # Policy Number
        self.policy_number_edit = QLineEdit()
        self.policy_number_edit.setPlaceholderText("Enter policy number")
        basic_layout.addRow("Policy Number:", self.policy_number_edit)

        # Current Status
        self.current_status_combo = QComboBox()
        self.current_status_combo.addItems(self.status_options)
        basic_layout.addRow("Current Status:", self.current_status_combo)

        scroll_layout.addWidget(basic_group)

        # Coverage Information Section
        coverage_group = QGroupBox("Coverage Information")
        coverage_layout = QFormLayout(coverage_group)

        # Coverage Type
        self.coverage_type_edit = QLineEdit()
        self.coverage_type_edit.setPlaceholderText("e.g., Comprehensive, Third Party, Term Life")
        coverage_layout.addRow("Coverage Type:", self.coverage_type_edit)

        # Coverage Amount
        self.coverage_amount_spin = QDoubleSpinBox()
        self.coverage_amount_spin.setRange(0.0, 999999999.99)
        self.coverage_amount_spin.setPrefix("₹")
        self.coverage_amount_spin.setGroupSeparatorShown(True)
        coverage_layout.addRow("Coverage Amount:", self.coverage_amount_spin)

        # Deductible Amount
        self.deductible_amount_spin = QDoubleSpinBox()
        self.deductible_amount_spin.setRange(0.0, 9999999.99)
        self.deductible_amount_spin.setPrefix("₹")
        self.deductible_amount_spin.setGroupSeparatorShown(True)
        coverage_layout.addRow("Deductible Amount:", self.deductible_amount_spin)

        scroll_layout.addWidget(coverage_group)

        # Premium Information Section
        premium_group = QGroupBox("Premium Information")
        premium_layout = QFormLayout(premium_group)

        # Premium Amount
        self.premium_amount_spin = QDoubleSpinBox()
        self.premium_amount_spin.setRange(0.0, 9999999.99)
        self.premium_amount_spin.setPrefix("₹")
        self.premium_amount_spin.setGroupSeparatorShown(True)
        premium_layout.addRow("Premium Amount:", self.premium_amount_spin)

        # Payment Frequency
        self.payment_frequency_combo = QComboBox()
        self.payment_frequency_combo.addItems(self.payment_frequencies)
        premium_layout.addRow("Payment Frequency:", self.payment_frequency_combo)

        # Premium Due Date
        self.premium_due_date = QDateEdit()
        self.premium_due_date.setCalendarPopup(True)
        self.premium_due_date.setDate(QDate.currentDate().addMonths(1))
        premium_layout.addRow("Premium Due Date:", self.premium_due_date)

        scroll_layout.addWidget(premium_group)

        # Policy Dates Section
        dates_group = QGroupBox("Policy Dates")
        dates_layout = QFormLayout(dates_group)

        # Policy Start Date
        self.policy_start_date = QDateEdit()
        self.policy_start_date.setCalendarPopup(True)
        self.policy_start_date.setDate(QDate.currentDate())
        dates_layout.addRow("Policy Start Date:", self.policy_start_date)

        # Policy End Date (Valid Till)
        self.valid_till_date = QDateEdit()
        self.valid_till_date.setCalendarPopup(True)
        self.valid_till_date.setDate(QDate.currentDate().addYears(1))
        dates_layout.addRow("Policy End Date (Valid Till):", self.valid_till_date)

        scroll_layout.addWidget(dates_group)

        # Beneficiaries Section
        beneficiaries_group = QGroupBox("Beneficiaries & Legacy")
        beneficiaries_layout = QFormLayout(beneficiaries_group)

        # Beneficiaries
        self.beneficiaries_edit = QLineEdit()
        self.beneficiaries_edit.setPlaceholderText("Enter beneficiaries separated by commas")
        beneficiaries_layout.addRow("Beneficiaries:", self.beneficiaries_edit)

        # Nominee (Legacy field)
        self.nominee_edit = QLineEdit()
        self.nominee_edit.setPlaceholderText("Primary nominee (for backward compatibility)")
        beneficiaries_layout.addRow("Primary Nominee:", self.nominee_edit)

        # Amount Insured (Legacy field)
        self.amount_insured_spin = QDoubleSpinBox()
        self.amount_insured_spin.setRange(0.0, 999999999.99)
        self.amount_insured_spin.setPrefix("₹")
        self.amount_insured_spin.setGroupSeparatorShown(True)
        beneficiaries_layout.addRow("Amount Insured (Legacy):", self.amount_insured_spin)

        scroll_layout.addWidget(beneficiaries_group)

        # Remarks Section
        remarks_group = QGroupBox("Additional Information")
        remarks_layout = QFormLayout(remarks_group)

        # Remarks
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMaximumHeight(80)
        self.remarks_edit.setPlaceholderText("Enter any additional notes or remarks")
        remarks_layout.addRow("Remarks:", self.remarks_edit)

        scroll_layout.addWidget(remarks_group)

        # Set up scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("💾 Save Policy")
        self.save_btn.clicked.connect(self.validate_and_accept)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(button_layout)

    def validate_and_accept(self):
        """Validate form data before accepting"""
        # Check required fields
        if not self.policy_name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Policy Name is required.")
            self.policy_name_edit.setFocus()
            return

        if not self.insurance_provider_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Insurance Provider is required.")
            self.insurance_provider_edit.setFocus()
            return

        if not self.policy_type_combo.currentText().strip():
            QMessageBox.warning(self, "Validation Error", "Policy Type is required.")
            self.policy_type_combo.setFocus()
            return

        self.accept()

    def load_data(self):
        """Load policy data into form"""
        if self.policy.id:
            self.policy_name_edit.setText(self.policy.policy_name)
            self.insurance_provider_edit.setText(self.policy.insurance_provider)
            self.policy_type_combo.setCurrentText(self.policy.policy_type)
            self.policy_number_edit.setText(self.policy.policy_number)
            self.current_status_combo.setCurrentText(self.policy.current_status)
            self.coverage_type_edit.setText(self.policy.coverage_type)
            self.coverage_amount_spin.setValue(self.policy.coverage_amount)
            self.deductible_amount_spin.setValue(self.policy.deductible_amount)
            self.premium_amount_spin.setValue(self.policy.premium_amount)
            self.payment_frequency_combo.setCurrentText(self.policy.payment_frequency)

            if self.policy.policy_start_date:
                self.policy_start_date.setDate(QDate(self.policy.policy_start_date))
            if self.policy.valid_till:
                self.valid_till_date.setDate(QDate(self.policy.valid_till))
            if self.policy.premium_due_date:
                self.premium_due_date.setDate(QDate(self.policy.premium_due_date))

            self.beneficiaries_edit.setText(self.policy.beneficiaries)
            self.nominee_edit.setText(self.policy.nominee)
            self.amount_insured_spin.setValue(self.policy.amount_insured)
            self.remarks_edit.setPlainText(self.policy.remarks)

    def get_policy(self):
        """Get the policy from form data"""
        self.policy.policy_name = self.policy_name_edit.text().strip()
        self.policy.insurance_provider = self.insurance_provider_edit.text().strip()
        self.policy.policy_type = self.policy_type_combo.currentText().strip()
        self.policy.policy_number = self.policy_number_edit.text().strip()
        self.policy.current_status = self.current_status_combo.currentText()
        self.policy.coverage_type = self.coverage_type_edit.text().strip()
        self.policy.coverage_amount = self.coverage_amount_spin.value()
        self.policy.deductible_amount = self.deductible_amount_spin.value()
        self.policy.premium_amount = self.premium_amount_spin.value()
        self.policy.payment_frequency = self.payment_frequency_combo.currentText()
        self.policy.policy_start_date = self.policy_start_date.date().toPython()
        self.policy.valid_till = self.valid_till_date.date().toPython()
        self.policy.premium_due_date = self.premium_due_date.date().toPython()
        self.policy.beneficiaries = self.beneficiaries_edit.text().strip()
        self.policy.nominee = self.nominee_edit.text().strip()
        self.policy.amount_insured = self.amount_insured_spin.value()
        self.policy.remarks = self.remarks_edit.toPlainText().strip()
        self.policy.last_updated = datetime.now()

        return self.policy


class LICPolicyDialog(QDialog):
    """Enhanced dialog for adding/editing LIC policies"""

    def __init__(self, policy=None, policy_types=None, family_members=None, parent=None):
        super().__init__(parent)
        self.policy = policy if policy else LICPolicy()
        self.policy_types = policy_types if policy_types else [
            "Endowment", "Term", "ULIP", "Pension", "Money Back", "Whole Life"
        ]
        self.family_members = family_members if family_members else []
        self.premium_frequencies = ["Monthly", "Quarterly", "Half-Yearly", "Annual"]
        self.status_options = ["Active", "Paid-up", "Lapsed", "Matured", "Surrendered"]
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the enhanced dialog UI"""
        self.setWindowTitle("Add/Edit LIC Policy")
        self.setModal(True)
        self.resize(700, 800)

        main_layout = QVBoxLayout(self)

        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Policy Holder Information Section
        holder_group = QGroupBox("Policy Holder Information")
        holder_layout = QFormLayout(holder_group)

        # Policy Holder Name (Family Member)
        self.policy_holder_edit = QComboBox()
        self.policy_holder_edit.setEditable(True)
        self.policy_holder_edit.setPlaceholderText("Select or enter family member name")
        if self.family_members:
            self.policy_holder_edit.addItems(self.family_members)
        holder_layout.addRow("Policy Holder Name*:", self.policy_holder_edit)

        scroll_layout.addWidget(holder_group)

        # Basic Policy Information Section
        basic_group = QGroupBox("Basic Policy Information")
        basic_layout = QFormLayout(basic_group)

        # Policy Number
        self.policy_number_edit = QLineEdit()
        self.policy_number_edit.setPlaceholderText("Enter LIC policy number")
        basic_layout.addRow("Policy Number*:", self.policy_number_edit)

        # Policy Type
        self.policy_type_combo = QComboBox()
        self.policy_type_combo.addItems(self.policy_types)
        basic_layout.addRow("Policy Type*:", self.policy_type_combo)

        # Plan Name
        self.plan_name_edit = QLineEdit()
        self.plan_name_edit.setPlaceholderText("Enter LIC plan name (e.g., Jeevan Anand)")
        basic_layout.addRow("Plan Name:", self.plan_name_edit)

        # Sum Assured
        self.sum_assured_edit = QLineEdit()
        self.sum_assured_edit.setPlaceholderText("Enter sum assured amount")
        basic_layout.addRow("Sum Assured*:", self.sum_assured_edit)

        scroll_layout.addWidget(basic_group)

        # Premium Information Section
        premium_group = QGroupBox("Premium Information")
        premium_layout = QFormLayout(premium_group)

        # Premium Amount
        self.premium_amount_edit = QLineEdit()
        self.premium_amount_edit.setPlaceholderText("Enter premium amount")
        premium_layout.addRow("Premium Amount*:", self.premium_amount_edit)

        # Premium Frequency
        self.premium_frequency_combo = QComboBox()
        self.premium_frequency_combo.addItems(self.premium_frequencies)
        premium_layout.addRow("Premium Frequency:", self.premium_frequency_combo)

        # Premium Due Date
        self.premium_due_date = QDateEdit()
        self.premium_due_date.setCalendarPopup(True)
        self.premium_due_date.setDate(QDate.currentDate())
        premium_layout.addRow("Premium Due Date:", self.premium_due_date)

        # Last Premium Paid Date
        self.last_premium_paid_date = QDateEdit()
        self.last_premium_paid_date.setCalendarPopup(True)
        self.last_premium_paid_date.setDate(QDate.currentDate())
        premium_layout.addRow("Last Premium Paid Date:", self.last_premium_paid_date)

        # Next Premium Due Date
        self.next_premium_due_date = QDateEdit()
        self.next_premium_due_date.setCalendarPopup(True)
        self.next_premium_due_date.setDate(QDate.currentDate())
        premium_layout.addRow("Next Premium Due Date:", self.next_premium_due_date)

        scroll_layout.addWidget(premium_group)

        # Policy Dates Section
        dates_group = QGroupBox("Policy Dates")
        dates_layout = QFormLayout(dates_group)

        # Policy Start Date
        self.policy_start_date = QDateEdit()
        self.policy_start_date.setCalendarPopup(True)
        self.policy_start_date.setDate(QDate.currentDate())
        dates_layout.addRow("Policy Start Date:", self.policy_start_date)

        # Maturity Date
        self.maturity_date = QDateEdit()
        self.maturity_date.setCalendarPopup(True)
        self.maturity_date.setDate(QDate.currentDate().addYears(20))  # Default 20 years
        dates_layout.addRow("Maturity Date:", self.maturity_date)

        scroll_layout.addWidget(dates_group)

        # Additional Information Section
        additional_group = QGroupBox("Additional Information")
        additional_layout = QFormLayout(additional_group)

        # Bonus Amount
        self.bonus_amount_edit = QLineEdit()
        self.bonus_amount_edit.setPlaceholderText("Enter accumulated bonus amount")
        additional_layout.addRow("Bonus Amount:", self.bonus_amount_edit)

        # Surrender Value
        self.surrender_value_edit = QLineEdit()
        self.surrender_value_edit.setPlaceholderText("Enter current surrender value")
        additional_layout.addRow("Surrender Value:", self.surrender_value_edit)

        # Loan Amount
        self.loan_amount_edit = QLineEdit()
        self.loan_amount_edit.setPlaceholderText("Enter outstanding loan amount")
        additional_layout.addRow("Loan Amount:", self.loan_amount_edit)

        # Current Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(self.status_options)
        additional_layout.addRow("Current Status:", self.status_combo)

        scroll_layout.addWidget(additional_group)

        # Nominee Information Section
        nominee_group = QGroupBox("Nominee Information")
        nominee_layout = QFormLayout(nominee_group)

        # Nominee Name
        self.nominee_name_edit = QLineEdit()
        self.nominee_name_edit.setPlaceholderText("Enter nominee name")
        nominee_layout.addRow("Nominee Name:", self.nominee_name_edit)

        # Nominee Relationship
        self.nominee_relationship_edit = QLineEdit()
        self.nominee_relationship_edit.setPlaceholderText("Enter relationship with nominee")
        nominee_layout.addRow("Nominee Relationship:", self.nominee_relationship_edit)

        scroll_layout.addWidget(nominee_group)

        # Agent Information Section
        agent_group = QGroupBox("Agent Information")
        agent_layout = QFormLayout(agent_group)

        # Agent Name
        self.agent_name_edit = QLineEdit()
        self.agent_name_edit.setPlaceholderText("Enter agent name")
        agent_layout.addRow("Agent Name:", self.agent_name_edit)

        # Agent Code
        self.agent_code_edit = QLineEdit()
        self.agent_code_edit.setPlaceholderText("Enter agent code")
        agent_layout.addRow("Agent Code:", self.agent_code_edit)

        # Branch Office
        self.branch_office_edit = QLineEdit()
        self.branch_office_edit.setPlaceholderText("Enter branch office")
        agent_layout.addRow("Branch Office:", self.branch_office_edit)

        # Policy Document Number
        self.policy_document_edit = QLineEdit()
        self.policy_document_edit.setPlaceholderText("Enter physical document reference")
        agent_layout.addRow("Policy Document Number:", self.policy_document_edit)

        scroll_layout.addWidget(agent_group)

        # Remarks Section
        remarks_group = QGroupBox("Remarks")
        remarks_layout = QVBoxLayout(remarks_group)

        self.remarks_edit = QTextEdit()
        self.remarks_edit.setPlaceholderText("Enter any additional remarks or notes...")
        self.remarks_edit.setMaximumHeight(80)
        remarks_layout.addWidget(self.remarks_edit)

        scroll_layout.addWidget(remarks_group)

        # Set scroll widget
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)

        main_layout.addLayout(button_layout)

    def load_data(self):
        """Load policy data into form fields"""
        if self.policy:
            # Policy Holder Information
            self.policy_holder_edit.setCurrentText(self.policy.policy_holder_name)

            # Basic Policy Information
            self.policy_number_edit.setText(self.policy.policy_number)
            if self.policy.policy_type in self.policy_types:
                self.policy_type_combo.setCurrentText(self.policy.policy_type)
            self.plan_name_edit.setText(self.policy.plan_name)
            self.sum_assured_edit.setText(str(self.policy.sum_assured) if self.policy.sum_assured else "")

            # Premium Information
            self.premium_amount_edit.setText(str(self.policy.premium_amount) if self.policy.premium_amount else "")
            if self.policy.premium_frequency in self.premium_frequencies:
                self.premium_frequency_combo.setCurrentText(self.policy.premium_frequency)

            # Set dates
            if self.policy.premium_due_date:
                if isinstance(self.policy.premium_due_date, str):
                    try:
                        date_obj = datetime.strptime(self.policy.premium_due_date, "%Y-%m-%d").date()
                        self.premium_due_date.setDate(QDate(date_obj))
                    except:
                        pass
                elif isinstance(self.policy.premium_due_date, (date, datetime)):
                    date_obj = self.policy.premium_due_date.date() if isinstance(self.policy.premium_due_date, datetime) else self.policy.premium_due_date
                    self.premium_due_date.setDate(QDate(date_obj))

            if self.policy.last_premium_paid_date:
                if isinstance(self.policy.last_premium_paid_date, str):
                    try:
                        date_obj = datetime.strptime(self.policy.last_premium_paid_date, "%Y-%m-%d").date()
                        self.last_premium_paid_date.setDate(QDate(date_obj))
                    except:
                        pass
                elif isinstance(self.policy.last_premium_paid_date, (date, datetime)):
                    date_obj = self.policy.last_premium_paid_date.date() if isinstance(self.policy.last_premium_paid_date, datetime) else self.policy.last_premium_paid_date
                    self.last_premium_paid_date.setDate(QDate(date_obj))

            if self.policy.next_premium_due_date:
                if isinstance(self.policy.next_premium_due_date, str):
                    try:
                        date_obj = datetime.strptime(self.policy.next_premium_due_date, "%Y-%m-%d").date()
                        self.next_premium_due_date.setDate(QDate(date_obj))
                    except:
                        pass
                elif isinstance(self.policy.next_premium_due_date, (date, datetime)):
                    date_obj = self.policy.next_premium_due_date.date() if isinstance(self.policy.next_premium_due_date, datetime) else self.policy.next_premium_due_date
                    self.next_premium_due_date.setDate(QDate(date_obj))

            if self.policy.policy_start_date:
                if isinstance(self.policy.policy_start_date, str):
                    try:
                        date_obj = datetime.strptime(self.policy.policy_start_date, "%Y-%m-%d").date()
                        self.policy_start_date.setDate(QDate(date_obj))
                    except:
                        pass
                elif isinstance(self.policy.policy_start_date, (date, datetime)):
                    date_obj = self.policy.policy_start_date.date() if isinstance(self.policy.policy_start_date, datetime) else self.policy.policy_start_date
                    self.policy_start_date.setDate(QDate(date_obj))

            if self.policy.maturity_date:
                if isinstance(self.policy.maturity_date, str):
                    try:
                        date_obj = datetime.strptime(self.policy.maturity_date, "%Y-%m-%d").date()
                        self.maturity_date.setDate(QDate(date_obj))
                    except:
                        pass
                elif isinstance(self.policy.maturity_date, (date, datetime)):
                    date_obj = self.policy.maturity_date.date() if isinstance(self.policy.maturity_date, datetime) else self.policy.maturity_date
                    self.maturity_date.setDate(QDate(date_obj))

            # Additional Information
            self.bonus_amount_edit.setText(str(self.policy.bonus_amount) if self.policy.bonus_amount else "")
            self.surrender_value_edit.setText(str(self.policy.surrender_value) if self.policy.surrender_value else "")
            self.loan_amount_edit.setText(str(self.policy.loan_amount) if self.policy.loan_amount else "")
            if self.policy.current_status in self.status_options:
                self.status_combo.setCurrentText(self.policy.current_status)

            # Nominee Information
            self.nominee_name_edit.setText(self.policy.nominee_name)
            self.nominee_relationship_edit.setText(self.policy.nominee_relationship)

            # Agent Information
            self.agent_name_edit.setText(self.policy.agent_name)
            self.agent_code_edit.setText(self.policy.agent_code)
            self.branch_office_edit.setText(self.policy.branch_office)
            self.policy_document_edit.setText(self.policy.policy_document_number)

            # Remarks
            self.remarks_edit.setPlainText(self.policy.remarks)

    def get_policy(self):
        """Get the policy from form data"""
        # Policy Holder Information
        self.policy.policy_holder_name = self.policy_holder_edit.currentText().strip()

        # Basic Policy Information
        self.policy.policy_number = self.policy_number_edit.text().strip()
        self.policy.policy_type = self.policy_type_combo.currentText()
        self.policy.plan_name = self.plan_name_edit.text().strip()

        try:
            self.policy.sum_assured = float(self.sum_assured_edit.text()) if self.sum_assured_edit.text().strip() else 0.0
        except ValueError:
            self.policy.sum_assured = 0.0

        # Premium Information
        try:
            self.policy.premium_amount = float(self.premium_amount_edit.text()) if self.premium_amount_edit.text().strip() else 0.0
        except ValueError:
            self.policy.premium_amount = 0.0

        self.policy.premium_frequency = self.premium_frequency_combo.currentText()

        # Dates
        self.policy.premium_due_date = self.premium_due_date.date().toPython()
        self.policy.last_premium_paid_date = self.last_premium_paid_date.date().toPython()
        self.policy.next_premium_due_date = self.next_premium_due_date.date().toPython()
        self.policy.policy_start_date = self.policy_start_date.date().toPython()
        self.policy.maturity_date = self.maturity_date.date().toPython()

        # Additional Information
        try:
            self.policy.bonus_amount = float(self.bonus_amount_edit.text()) if self.bonus_amount_edit.text().strip() else 0.0
        except ValueError:
            self.policy.bonus_amount = 0.0

        try:
            self.policy.surrender_value = float(self.surrender_value_edit.text()) if self.surrender_value_edit.text().strip() else 0.0
        except ValueError:
            self.policy.surrender_value = 0.0

        try:
            self.policy.loan_amount = float(self.loan_amount_edit.text()) if self.loan_amount_edit.text().strip() else 0.0
        except ValueError:
            self.policy.loan_amount = 0.0

        self.policy.current_status = self.status_combo.currentText()

        # Nominee Information
        self.policy.nominee_name = self.nominee_name_edit.text().strip()
        self.policy.nominee_relationship = self.nominee_relationship_edit.text().strip()

        # Agent Information
        self.policy.agent_name = self.agent_name_edit.text().strip()
        self.policy.agent_code = self.agent_code_edit.text().strip()
        self.policy.branch_office = self.branch_office_edit.text().strip()
        self.policy.policy_document_number = self.policy_document_edit.text().strip()

        # Remarks
        self.policy.remarks = self.remarks_edit.toPlainText().strip()

        # Update timestamps
        self.policy.last_updated = datetime.now()

        return self.policy


class LICBenefitCalculatorDialog(QDialog):
    """Dialog for calculating LIC policy benefits and maturity projections"""

    def __init__(self, policy, parent=None):
        super().__init__(parent)
        self.policy = policy

        # Validate and initialize policy data
        if not self.policy:
            raise ValueError("Policy data is required")

        # Ensure essential fields have default values
        if not hasattr(self.policy, 'sum_assured') or self.policy.sum_assured is None:
            self.policy.sum_assured = 0.0
        if not hasattr(self.policy, 'bonus_amount') or self.policy.bonus_amount is None:
            self.policy.bonus_amount = 0.0
        if not hasattr(self.policy, 'policy_number') or not self.policy.policy_number:
            self.policy.policy_number = "Unknown"

        self.setup_ui()
        self.load_policy_data()
        self.calculate_benefits()

    def setup_ui(self):
        """Setup the benefit calculator dialog UI with tabbed interface"""
        self.setWindowTitle(f"LIC Benefit Calculator - {self.policy.policy_number}")
        self.setModal(True)
        self.resize(1000, 750)  # Slightly larger for tabbed interface

        main_layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🏛️ LIC Policy Benefit Calculator")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("benefitCalculatorTabs")

        # Create tabs
        self.create_benefit_analysis_tab()
        self.create_sum_assured_breakdown_tab()

        main_layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        calculate_btn = QPushButton("🔄 Recalculate")
        calculate_btn.clicked.connect(self.calculate_benefits)
        button_layout.addWidget(calculate_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)

    def create_benefit_analysis_tab(self):
        """Create the main benefit analysis tab with existing functionality"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create scroll area for the content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Current Policy Summary Section
        self.create_policy_summary_section(scroll_layout)

        # Maturity Benefit Projection Section
        self.create_maturity_projection_section(scroll_layout)

        # Bonus Simulation Section
        self.create_bonus_simulation_section(scroll_layout)

        # Set scroll widget
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        self.tab_widget.addTab(tab, "📊 Benefit Analysis")

    def create_sum_assured_breakdown_tab(self):
        """Create the sum assured breakdown tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create scroll area for the content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Sum Assured Components Section
        self.create_sum_assured_components_section(scroll_layout)

        # Visual Graph Section
        self.create_visual_graph_section(scroll_layout)

        # Set scroll widget
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        self.tab_widget.addTab(tab, "💰 Sum Assured Breakdown")

    def create_policy_summary_section(self, layout):
        """Create the current policy summary section"""
        summary_group = QGroupBox("📋 Current Policy Summary")
        summary_group.setFont(QFont("Arial", 12, QFont.Bold))
        summary_layout = QFormLayout(summary_group)

        # Policy holder and basic info
        self.holder_label = QLabel()
        self.holder_label.setFont(QFont("Arial", 10))
        summary_layout.addRow("Policy Holder:", self.holder_label)

        self.policy_number_label = QLabel()
        self.policy_number_label.setFont(QFont("Arial", 10))
        summary_layout.addRow("Policy Number:", self.policy_number_label)

        self.plan_name_label = QLabel()
        self.plan_name_label.setFont(QFont("Arial", 10))
        summary_layout.addRow("Plan Name:", self.plan_name_label)

        self.policy_type_label = QLabel()
        self.policy_type_label.setFont(QFont("Arial", 10))
        summary_layout.addRow("Policy Type:", self.policy_type_label)

        # Financial details
        self.sum_assured_label = QLabel()
        self.sum_assured_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.sum_assured_label.setStyleSheet("color: #2E8B57;")
        summary_layout.addRow("Sum Assured:", self.sum_assured_label)

        self.bonus_amount_label = QLabel()
        self.bonus_amount_label.setFont(QFont("Arial", 10))
        summary_layout.addRow("Current Bonus:", self.bonus_amount_label)

        self.surrender_value_label = QLabel()
        self.surrender_value_label.setFont(QFont("Arial", 10))
        summary_layout.addRow("Surrender Value:", self.surrender_value_label)

        # Dates
        self.start_date_label = QLabel()
        self.start_date_label.setFont(QFont("Arial", 10))
        summary_layout.addRow("Policy Start Date:", self.start_date_label)

        self.maturity_date_label = QLabel()
        self.maturity_date_label.setFont(QFont("Arial", 10))
        summary_layout.addRow("Maturity Date:", self.maturity_date_label)

        self.years_remaining_label = QLabel()
        self.years_remaining_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.years_remaining_label.setStyleSheet("color: #FF6347;")
        summary_layout.addRow("Years Remaining:", self.years_remaining_label)

        layout.addWidget(summary_group)

    def create_maturity_projection_section(self, layout):
        """Create the maturity benefit projection section"""
        projection_group = QGroupBox("💰 Maturity Benefit Projection")
        projection_group.setFont(QFont("Arial", 12, QFont.Bold))
        projection_layout = QVBoxLayout(projection_group)

        # Calculation breakdown
        breakdown_layout = QFormLayout()

        self.guaranteed_amount_label = QLabel()
        self.guaranteed_amount_label.setFont(QFont("Arial", 10))
        breakdown_layout.addRow("Guaranteed Sum Assured:", self.guaranteed_amount_label)

        self.current_bonus_label = QLabel()
        self.current_bonus_label.setFont(QFont("Arial", 10))
        breakdown_layout.addRow("Accumulated Bonus (Current):", self.current_bonus_label)

        self.estimated_future_bonus_label = QLabel()
        self.estimated_future_bonus_label.setFont(QFont("Arial", 10))
        breakdown_layout.addRow("Estimated Future Bonus:", self.estimated_future_bonus_label)

        # Total maturity amount
        total_layout = QHBoxLayout()
        total_label = QLabel("Total Projected Maturity Amount:")
        total_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_maturity_label = QLabel()
        self.total_maturity_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_maturity_label.setStyleSheet("color: #228B22; background-color: #F0FFF0; padding: 5px; border: 2px solid #228B22; border-radius: 5px;")
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_maturity_label)
        total_layout.addStretch()

        projection_layout.addLayout(breakdown_layout)
        projection_layout.addLayout(total_layout)

        layout.addWidget(projection_group)

    def create_bonus_simulation_section(self, layout):
        """Create the bonus simulation section"""
        simulation_group = QGroupBox("📊 Bonus Rate Simulation")
        simulation_group.setFont(QFont("Arial", 12, QFont.Bold))
        simulation_layout = QVBoxLayout(simulation_group)

        # Bonus rate input section
        input_layout = QHBoxLayout()

        bonus_label = QLabel("Annual Bonus Rate (%):")
        bonus_label.setToolTip("Enter the expected annual bonus rate for simulation.\nHistorical LIC bonus rates typically range from 2% to 4%.")
        input_layout.addWidget(bonus_label)

        self.bonus_rate_spin = QDoubleSpinBox()
        self.bonus_rate_spin.setRange(0.0, 10.0)
        self.bonus_rate_spin.setSingleStep(0.1)
        self.bonus_rate_spin.setValue(3.0)  # Default 3%
        self.bonus_rate_spin.setDecimals(1)
        self.bonus_rate_spin.setSuffix("%")
        self.bonus_rate_spin.setToolTip("Adjust the bonus rate to see different maturity projections.\nTypical LIC bonus rates: 2-4% annually.")
        self.bonus_rate_spin.valueChanged.connect(self.calculate_benefits)
        input_layout.addWidget(self.bonus_rate_spin)

        # Preset buttons for common rates
        preset_label = QLabel("Quick Presets:")
        preset_label.setToolTip("Click on common bonus rates used by LIC historically")
        input_layout.addWidget(preset_label)

        for rate in [2.0, 2.5, 3.0, 3.5, 4.0]:
            preset_btn = QPushButton(f"{rate}%")
            preset_btn.setToolTip(f"Set bonus rate to {rate}% (common LIC rate)")
            preset_btn.clicked.connect(lambda checked, r=rate: self.set_bonus_rate(r))
            preset_btn.setMaximumWidth(50)
            input_layout.addWidget(preset_btn)

        input_layout.addStretch()
        simulation_layout.addLayout(input_layout)

        # Results table
        self.simulation_table = QTableWidget()
        self.simulation_table.setColumnCount(4)
        self.simulation_table.setHorizontalHeaderLabels([
            "Year", "Annual Bonus", "Cumulative Bonus", "Total Value"
        ])
        self.simulation_table.setAlternatingRowColors(True)
        self.simulation_table.setSortingEnabled(False)
        self.simulation_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Set column widths
        header = self.simulation_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        simulation_layout.addWidget(self.simulation_table)

        # Add help text
        help_text = QLabel(
            "💡 <b>Calculation Notes:</b><br>"
            "• Bonus calculations are estimates based on the selected rate<br>"
            "• Actual LIC bonuses may vary based on company performance<br>"
            "• Historical LIC bonus rates typically range from 2% to 4% annually<br>"
            "• Final maturity amount = Sum Assured + Total Accumulated Bonus"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; font-size: 9pt; padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        simulation_layout.addWidget(help_text)

        layout.addWidget(simulation_group)

    def create_sum_assured_components_section(self, layout):
        """Create the sum assured components breakdown section"""
        components_group = QGroupBox("💰 Sum Assured Components Breakdown")
        components_group.setFont(QFont("Arial", 12, QFont.Bold))
        components_layout = QVBoxLayout(components_group)

        # Components table
        self.components_table = QTableWidget()
        self.components_table.setColumnCount(4)
        self.components_table.setHorizontalHeaderLabels([
            "Component Type", "Amount (₹)", "Percentage (%)", "Description"
        ])
        self.components_table.setAlternatingRowColors(True)
        self.components_table.setSortingEnabled(False)
        self.components_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Set column widths
        header = self.components_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Component Type
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Amount
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Percentage
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Description

        components_layout.addWidget(self.components_table)

        # Summary section
        summary_layout = QHBoxLayout()
        summary_label = QLabel("Total Sum Assured:")
        summary_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_sum_assured_label = QLabel()
        self.total_sum_assured_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_sum_assured_label.setStyleSheet("color: #228B22; background-color: #F0FFF0; padding: 5px; border: 2px solid #228B22; border-radius: 5px;")
        summary_layout.addWidget(summary_label)
        summary_layout.addWidget(self.total_sum_assured_label)
        summary_layout.addStretch()

        components_layout.addLayout(summary_layout)

        # Add help text
        help_text = QLabel(
            "💡 <b>Component Information:</b><br>"
            "• Base Sum Assured: Core guaranteed coverage amount<br>"
            "• Additional Coverage: Extra coverage purchased or added<br>"
            "• Rider Benefits: Coverage from attached riders (accident, disability, etc.)<br>"
            "• Loyalty Addition: Benefits for long-term policyholders<br>"
            "• Terminal Bonus: One-time bonus payable at maturity"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; font-size: 9pt; padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        components_layout.addWidget(help_text)

        layout.addWidget(components_group)

    def create_visual_graph_section(self, layout):
        """Create the visual graph representation section"""
        graph_group = QGroupBox("📊 Visual Breakdown")
        graph_group.setFont(QFont("Arial", 12, QFont.Bold))
        graph_layout = QVBoxLayout(graph_group)

        # Graph placeholder (we'll implement a simple text-based representation)
        self.graph_widget = QWidget()
        self.graph_widget.setMinimumHeight(300)
        self.graph_widget.setStyleSheet("background-color: #252526; border: 1px solid #3e3e42; border-radius: 5px; color: #ffffff;")

        # Create a layout for the graph widget
        graph_widget_layout = QVBoxLayout(self.graph_widget)

        # Title for the graph
        graph_title = QLabel("Sum Assured Distribution")
        graph_title.setFont(QFont("Arial", 14, QFont.Bold))
        graph_title.setAlignment(Qt.AlignCenter)
        graph_widget_layout.addWidget(graph_title)

        # Graph content area
        self.graph_content = QLabel()
        self.graph_content.setAlignment(Qt.AlignCenter)
        self.graph_content.setWordWrap(True)
        self.graph_content.setStyleSheet("padding: 20px; font-size: 11pt;")
        graph_widget_layout.addWidget(self.graph_content)

        graph_layout.addWidget(self.graph_widget)

        # Legend section
        legend_layout = QHBoxLayout()
        legend_label = QLabel("Legend:")
        legend_label.setFont(QFont("Arial", 10, QFont.Bold))
        legend_layout.addWidget(legend_label)

        self.legend_content = QLabel()
        self.legend_content.setWordWrap(True)
        self.legend_content.setStyleSheet("font-size: 9pt; color: #666;")
        legend_layout.addWidget(self.legend_content)
        legend_layout.addStretch()

        graph_layout.addLayout(legend_layout)

        layout.addWidget(graph_group)

    def load_policy_data(self):
        """Load policy data into the summary section"""
        # Policy holder and basic info
        self.holder_label.setText(self.policy.policy_holder_name or "Not specified")
        self.policy_number_label.setText(self.policy.policy_number or "Not specified")
        self.plan_name_label.setText(self.policy.plan_name or "Not specified")
        self.policy_type_label.setText(self.policy.policy_type or "Not specified")

        # Financial details
        self.sum_assured_label.setText(f"₹{self.policy.sum_assured:,.0f}" if self.policy.sum_assured else "₹0")
        self.bonus_amount_label.setText(f"₹{self.policy.bonus_amount:,.0f}" if self.policy.bonus_amount else "₹0")
        self.surrender_value_label.setText(f"₹{self.policy.surrender_value:,.0f}" if self.policy.surrender_value else "₹0")

        # Dates
        self.start_date_label.setText(str(self.policy.policy_start_date) if self.policy.policy_start_date else "Not specified")
        self.maturity_date_label.setText(str(self.policy.maturity_date) if self.policy.maturity_date else "Not specified")

        # Calculate years remaining
        years_remaining = self.calculate_years_remaining()
        if years_remaining is not None:
            self.years_remaining_label.setText(f"{years_remaining:.1f} years")
        else:
            self.years_remaining_label.setText("Cannot calculate")

        # Load sum assured breakdown if components table exists
        if hasattr(self, 'components_table'):
            self.load_sum_assured_breakdown()

    def calculate_years_remaining(self):
        """Calculate years remaining until maturity"""
        if not self.policy.maturity_date:
            return None

        try:
            from datetime import date
            today = date.today()

            if isinstance(self.policy.maturity_date, str):
                maturity_date = datetime.strptime(self.policy.maturity_date, '%Y-%m-%d').date()
            elif isinstance(self.policy.maturity_date, datetime):
                maturity_date = self.policy.maturity_date.date()
            else:
                maturity_date = self.policy.maturity_date

            if maturity_date <= today:
                return 0.0  # Policy already matured

            # Calculate years remaining
            years_remaining = (maturity_date - today).days / 365.25
            return max(0.0, years_remaining)

        except Exception:
            return None

    def calculate_benefits(self):
        """Calculate and display maturity benefits"""
        # Get basic values with validation
        sum_assured = max(0, self.policy.sum_assured or 0)
        current_bonus = max(0, self.policy.bonus_amount or 0)
        bonus_rate = max(0, min(10, self.bonus_rate_spin.value())) / 100  # Convert percentage to decimal, cap at 10%
        years_remaining = self.calculate_years_remaining()

        # Validate inputs
        if sum_assured <= 0:
            QMessageBox.warning(self, "Invalid Data", "Sum Assured must be greater than zero for benefit calculations.")
            return

        if years_remaining is None or years_remaining <= 0:
            # Policy already matured or invalid dates
            estimated_future_bonus = 0
            total_maturity = sum_assured + current_bonus
        else:
            # Calculate estimated future bonus
            # Simple compound bonus calculation: sum_assured * bonus_rate * years_remaining
            estimated_future_bonus = sum_assured * bonus_rate * years_remaining
            total_maturity = sum_assured + current_bonus + estimated_future_bonus

        # Update maturity projection labels
        self.guaranteed_amount_label.setText(f"₹{sum_assured:,.0f}")
        self.current_bonus_label.setText(f"₹{current_bonus:,.0f}")
        self.estimated_future_bonus_label.setText(f"₹{estimated_future_bonus:,.0f}")
        self.total_maturity_label.setText(f"₹{total_maturity:,.0f}")

        # Update simulation table
        self.update_simulation_table(sum_assured, current_bonus, bonus_rate, years_remaining)

        # Update sum assured breakdown if we're on that tab
        if hasattr(self, 'components_table'):
            self.load_sum_assured_breakdown()

    def update_simulation_table(self, sum_assured, current_bonus, bonus_rate, years_remaining):
        """Update the year-by-year simulation table"""
        if years_remaining is None or years_remaining <= 0:
            self.simulation_table.setRowCount(1)
            self.simulation_table.setItem(0, 0, QTableWidgetItem("Policy Matured"))
            self.simulation_table.setItem(0, 1, QTableWidgetItem("₹0"))
            self.simulation_table.setItem(0, 2, QTableWidgetItem(f"₹{current_bonus:,.0f}"))
            self.simulation_table.setItem(0, 3, QTableWidgetItem(f"₹{sum_assured + current_bonus:,.0f}"))
            return

        # Calculate year-by-year projections
        years_to_show = min(int(years_remaining) + 1, 20)  # Show max 20 years
        self.simulation_table.setRowCount(years_to_show)

        cumulative_bonus = current_bonus

        for year in range(years_to_show):
            # Calculate annual bonus for this year
            annual_bonus = sum_assured * bonus_rate
            cumulative_bonus += annual_bonus
            total_value = sum_assured + cumulative_bonus

            # Add row to table
            self.simulation_table.setItem(year, 0, QTableWidgetItem(f"Year {year + 1}"))
            self.simulation_table.setItem(year, 1, QTableWidgetItem(f"₹{annual_bonus:,.0f}"))
            self.simulation_table.setItem(year, 2, QTableWidgetItem(f"₹{cumulative_bonus:,.0f}"))

            # Highlight the final maturity year
            total_item = QTableWidgetItem(f"₹{total_value:,.0f}")
            if year == years_to_show - 1 or year >= int(years_remaining):
                total_item.setBackground(QColor(144, 238, 144))  # Light green for maturity
                total_item.setFont(QFont("Arial", 10, QFont.Bold))

            self.simulation_table.setItem(year, 3, total_item)

    def set_bonus_rate(self, rate):
        """Set the bonus rate from preset buttons"""
        self.bonus_rate_spin.setValue(rate)

    def load_sum_assured_breakdown(self):
        """Load and display sum assured breakdown data"""
        # Get breakdown from policy
        breakdown = self.policy.get_sum_assured_breakdown()

        if not breakdown:
            # Show message if no breakdown available
            self.components_table.setRowCount(1)
            self.components_table.setItem(0, 0, QTableWidgetItem("No breakdown available"))
            self.components_table.setItem(0, 1, QTableWidgetItem("₹0"))
            self.components_table.setItem(0, 2, QTableWidgetItem("0%"))
            self.components_table.setItem(0, 3, QTableWidgetItem("Sum assured breakdown data not available"))
            self.total_sum_assured_label.setText("₹0")
            return

        # Calculate total for percentage calculations
        total_amount = sum(amount for _, amount, _ in breakdown)

        # Populate the table
        self.components_table.setRowCount(len(breakdown))

        for row, (component_type, amount, description) in enumerate(breakdown):
            # Component Type
            type_item = QTableWidgetItem(component_type)
            type_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.components_table.setItem(row, 0, type_item)

            # Amount
            amount_item = QTableWidgetItem(f"₹{amount:,.0f}")
            amount_item.setFont(QFont("Arial", 10))
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.components_table.setItem(row, 1, amount_item)

            # Percentage
            percentage = (amount / total_amount * 100) if total_amount > 0 else 0
            percentage_item = QTableWidgetItem(f"{percentage:.1f}%")
            percentage_item.setFont(QFont("Arial", 10))
            percentage_item.setTextAlignment(Qt.AlignCenter)

            # Color code based on percentage
            if percentage >= 50:
                percentage_item.setBackground(QColor("#2d5a2d"))  # Dark green
                percentage_item.setForeground(QColor("#90ee90"))  # Light green text
            elif percentage >= 25:
                percentage_item.setBackground(QColor("#5a5a2d"))  # Dark yellow
                percentage_item.setForeground(QColor("#ffff90"))  # Light yellow text
            else:
                percentage_item.setBackground(QColor("#5a2d2d"))  # Dark pink
                percentage_item.setForeground(QColor("#ffb3b3"))  # Light pink text

            self.components_table.setItem(row, 2, percentage_item)

            # Description
            desc_item = QTableWidgetItem(description)
            desc_item.setFont(QFont("Arial", 9))
            desc_item.setToolTip(description)
            self.components_table.setItem(row, 3, desc_item)

        # Update total
        self.total_sum_assured_label.setText(f"₹{total_amount:,.0f}")

        # Update visual graph
        self.update_visual_graph(breakdown, total_amount)

    def update_visual_graph(self, breakdown, total_amount):
        """Update the visual graph representation"""
        if not breakdown or total_amount <= 0:
            self.graph_content.setText("No data available for visualization")
            self.legend_content.setText("")
            return

        # Create a simple text-based bar chart
        graph_text = ""
        legend_text = ""
        colors = ["🟢", "🔵", "🟡", "🟠", "🔴", "🟣", "🟤"]

        for i, (component_type, amount, _) in enumerate(breakdown):
            percentage = (amount / total_amount * 100)
            bar_length = int(percentage / 2)  # Scale down for display
            color = colors[i % len(colors)]

            # Create bar representation
            bar = color * max(1, bar_length)
            graph_text += f"{component_type:<20} {bar} {percentage:.1f}%\n"

            # Add to legend
            legend_text += f"{color} {component_type}  "

        self.graph_content.setText(graph_text)
        self.legend_content.setText(legend_text)

    def calculate_benefits_with_breakdown(self):
        """Original calculate benefits method"""
        # Get basic values with validation
        sum_assured = max(0, self.policy.sum_assured or 0)
        current_bonus = max(0, self.policy.bonus_amount or 0)
        bonus_rate = max(0, min(10, self.bonus_rate_spin.value())) / 100  # Convert percentage to decimal, cap at 10%
        years_remaining = self.calculate_years_remaining()

        # Validate inputs
        if sum_assured <= 0:
            QMessageBox.warning(self, "Invalid Data", "Sum Assured must be greater than zero for benefit calculations.")
            return

        if years_remaining is None or years_remaining <= 0:
            # Policy already matured or invalid dates
            estimated_future_bonus = 0
            total_maturity = sum_assured + current_bonus
        else:
            # Calculate estimated future bonus
            # Simple compound bonus calculation: sum_assured * bonus_rate * years_remaining
            estimated_future_bonus = sum_assured * bonus_rate * years_remaining
            total_maturity = sum_assured + current_bonus + estimated_future_bonus

        # Update maturity projection labels
        self.guaranteed_amount_label.setText(f"₹{sum_assured:,.0f}")
        self.current_bonus_label.setText(f"₹{current_bonus:,.0f}")
        self.estimated_future_bonus_label.setText(f"₹{estimated_future_bonus:,.0f}")
        self.total_maturity_label.setText(f"₹{total_maturity:,.0f}")

        # Update simulation table
        self.update_simulation_table(sum_assured, current_bonus, bonus_rate, years_remaining)


class MutualFundStockDialog(QDialog):
    """Dialog for adding/editing mutual fund/stock entries"""

    def __init__(self, fund=None, categories=None, subcategories=None, parent=None):
        super().__init__(parent)
        self.fund = fund if fund else MutualFundStock()
        self.categories = categories if categories else ["Equity", "Debt", "Hybrid", "ELSS", "International", "Sectoral"]
        self.subcategories = subcategories if subcategories else ["Large Cap", "Mid Cap", "Small Cap", "Multi Cap", "Value", "Growth"]
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Add/Edit Mutual Fund/Stock")
        self.setModal(True)
        self.resize(500, 450)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., HDFC Top 100 Fund, Reliance Industries")
        form_layout.addRow("Name:", self.name_edit)

        # Symbol
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setPlaceholderText("e.g., HDFC100, RELIANCE")
        form_layout.addRow("Symbol:", self.symbol_edit)

        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(self.categories)
        form_layout.addRow("Category:", self.category_combo)

        # Sub Category
        self.subcategory_combo = QComboBox()
        self.subcategory_combo.setEditable(True)
        self.subcategory_combo.addItems(self.subcategories)
        form_layout.addRow("Sub Category:", self.subcategory_combo)

        # Geographic Classification
        self.geographic_combo = QComboBox()
        self.geographic_combo.addItems(["Indian", "International"])
        form_layout.addRow("Geographic Classification:", self.geographic_combo)

        # Unit Price
        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setRange(0.0, 999999.99)
        self.unit_price_spin.setDecimals(2)
        self.unit_price_spin.setPrefix("₹")
        self.unit_price_spin.valueChanged.connect(self.calculate_amount)
        form_layout.addRow("Unit Price:", self.unit_price_spin)

        # Units
        self.units_spin = QDoubleSpinBox()
        self.units_spin.setRange(0.0, 999999.99)
        self.units_spin.setDecimals(3)
        self.units_spin.valueChanged.connect(self.calculate_amount)
        form_layout.addRow("Units:", self.units_spin)

        # Amount (calculated)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.0, 99999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("₹")
        self.amount_spin.setReadOnly(True)
        form_layout.addRow("Amount:", self.amount_spin)

        # Allocation %
        self.allocation_spin = QDoubleSpinBox()
        self.allocation_spin.setRange(0.0, 100.0)
        self.allocation_spin.setDecimals(2)
        self.allocation_spin.setSuffix("%")
        form_layout.addRow("Allocation %:", self.allocation_spin)

        # Remarks
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMaximumHeight(60)
        form_layout.addRow("Remarks:", self.remarks_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def calculate_amount(self):
        """Calculate amount based on unit price and units"""
        unit_price = self.unit_price_spin.value()
        units = self.units_spin.value()
        amount = unit_price * units
        self.amount_spin.setValue(amount)

    def load_data(self):
        """Load fund data into form"""
        if self.fund.id:
            self.name_edit.setText(self.fund.name)
            self.symbol_edit.setText(self.fund.symbol)
            self.category_combo.setCurrentText(self.fund.category)
            self.subcategory_combo.setCurrentText(self.fund.sub_category)
            self.geographic_combo.setCurrentText(self.fund.geographic_classification)
            self.unit_price_spin.setValue(self.fund.unit_price)
            self.units_spin.setValue(self.fund.units)
            self.amount_spin.setValue(self.fund.amount)
            self.allocation_spin.setValue(self.fund.allocation_percent)
            self.remarks_edit.setPlainText(self.fund.remarks)

    def get_fund(self):
        """Get the fund from form data"""
        self.fund.name = self.name_edit.text().strip()
        self.fund.symbol = self.symbol_edit.text().strip()
        self.fund.category = self.category_combo.currentText().strip()
        self.fund.sub_category = self.subcategory_combo.currentText().strip()
        self.fund.geographic_classification = self.geographic_combo.currentText().strip()
        self.fund.unit_price = self.unit_price_spin.value()
        self.fund.units = self.units_spin.value()
        self.fund.amount = self.amount_spin.value()
        self.fund.allocation_percent = self.allocation_spin.value()
        self.fund.remarks = self.remarks_edit.toPlainText().strip()
        self.fund.last_updated = datetime.now()

        return self.fund


class PortfolioSnapshotDialog(QDialog):
    """Dialog for adding/editing portfolio snapshots"""

    def __init__(self, snapshot=None, parent=None):
        super().__init__(parent)
        self.snapshot = snapshot if snapshot else PortfolioSnapshot()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Add/Edit Portfolio Snapshot")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Category
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("e.g., Equity, Debt, Gold, Real Estate")
        form_layout.addRow("Category:", self.category_edit)

        # Item
        self.item_edit = QLineEdit()
        self.item_edit.setPlaceholderText("e.g., Mutual Funds, Stocks, FD, Physical Gold")
        form_layout.addRow("Item:", self.item_edit)

        # Amount
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.0, 99999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("₹")
        form_layout.addRow("Amount:", self.amount_spin)

        # Snapshot Date
        self.snapshot_date = QDateEdit()
        self.snapshot_date.setCalendarPopup(True)
        self.snapshot_date.setDate(QDate.currentDate())
        form_layout.addRow("Snapshot Date:", self.snapshot_date)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_data(self):
        """Load snapshot data into form"""
        if self.snapshot.id:
            self.category_edit.setText(self.snapshot.category)
            self.item_edit.setText(self.snapshot.item)
            self.amount_spin.setValue(self.snapshot.amount)
            if self.snapshot.snapshot_date:
                self.snapshot_date.setDate(QDate(self.snapshot.snapshot_date))

    def get_snapshot(self):
        """Get the snapshot from form data"""
        self.snapshot.category = self.category_edit.text().strip()
        self.snapshot.item = self.item_edit.text().strip()
        self.snapshot.amount = self.amount_spin.value()
        self.snapshot.snapshot_date = self.snapshot_date.date().toPython()

        return self.snapshot


class LoanChartWidget(QWidget):
    """Widget for displaying loan charts using matplotlib"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = None
        self.canvas = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the chart widget UI"""
        layout = QVBoxLayout(self)

        if MATPLOTLIB_AVAILABLE:
            # Create matplotlib figure and canvas
            self.figure = Figure(figsize=(10, 6), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            layout.addWidget(self.canvas)
        else:
            # Fallback to text-based representation
            self.text_label = QLabel("Matplotlib not available. Install matplotlib for interactive charts.")
            self.text_label.setAlignment(Qt.AlignCenter)
            self.text_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            layout.addWidget(self.text_label)

    def create_pie_chart(self, data, title="Pie Chart"):
        """Create a pie chart"""
        if not MATPLOTLIB_AVAILABLE or not data:
            return

        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            labels, values = zip(*data)
            colors = ['#2E8B57', '#DC143C', '#4169E1', '#FF8C00', '#9932CC']

            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                             colors=colors[:len(data)], startangle=90)

            # Make percentage text bold and white
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            print(f"Error creating pie chart: {e}")
            if hasattr(self, 'text_label'):
                self.text_label.setText(f"Chart error: {str(e)}")
            else:
                # Create error label if it doesn't exist
                self.text_label = QLabel(f"Chart error: {str(e)}")
                self.layout().addWidget(self.text_label)

    def create_line_chart(self, data, title="Line Chart", xlabel="Time", ylabel="Amount"):
        """Create a line chart"""
        if not MATPLOTLIB_AVAILABLE or not data:
            return

        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            x_values, y_values = zip(*data)
            ax.plot(x_values, y_values, marker='o', linewidth=2, markersize=4, color='#2E8B57')

            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.grid(True, alpha=0.3)

            # Format x-axis for dates
            if data and hasattr(x_values[0], 'strftime'):
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, len(data)//12)))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            print(f"Error creating line chart: {e}")
            if hasattr(self, 'text_label'):
                self.text_label.setText(f"Chart error: {str(e)}")
            else:
                self.text_label = QLabel(f"Chart error: {str(e)}")
                self.layout().addWidget(self.text_label)

    def create_area_chart(self, data, title="Area Chart", xlabel="Time", ylabel="Amount"):
        """Create an area chart"""
        if not MATPLOTLIB_AVAILABLE or not data:
            return

        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            x_values, y_values = zip(*data)
            ax.fill_between(x_values, y_values, alpha=0.7, color='#4169E1')
            ax.plot(x_values, y_values, color='#1E3A8A', linewidth=2)

            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.grid(True, alpha=0.3)

            # Format x-axis for dates
            if data and hasattr(x_values[0], 'strftime'):
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, len(data)//12)))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            print(f"Error creating area chart: {e}")
            if hasattr(self, 'text_label'):
                self.text_label.setText(f"Chart error: {str(e)}")
            else:
                self.text_label = QLabel(f"Chart error: {str(e)}")
                self.layout().addWidget(self.text_label)

    def create_stacked_bar_chart(self, data, title="Stacked Bar Chart"):
        """Create a stacked bar chart"""
        if not MATPLOTLIB_AVAILABLE or not data:
            return

        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            months = [item['month'] for item in data]
            principal_values = [item['principal'] for item in data]
            interest_values = [item['interest'] for item in data]

            width = 0.8
            ax.bar(months, principal_values, width, label='Principal', color='#2E8B57')
            ax.bar(months, interest_values, width, bottom=principal_values, label='Interest', color='#DC143C')

            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('Month', fontsize=12)
            ax.set_ylabel('Amount (₹)', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')

            # Rotate x-axis labels for better readability
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            print(f"Error creating stacked bar chart: {e}")
            if hasattr(self, 'text_label'):
                self.text_label.setText(f"Chart error: {str(e)}")
            else:
                self.text_label = QLabel(f"Chart error: {str(e)}")
                self.layout().addWidget(self.text_label)

    def set_fallback_text(self, text):
        """Set fallback text when matplotlib is not available"""
        if not MATPLOTLIB_AVAILABLE:
            if hasattr(self, 'text_label'):
                self.text_label.setText(text)
            else:
                # Create text label if it doesn't exist
                self.text_label = QLabel(text)
                self.text_label.setAlignment(Qt.AlignCenter)
                self.text_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
                self.text_label.setWordWrap(True)
                if self.layout():
                    self.layout().addWidget(self.text_label)


class PriceUpdateWorker(QObject):
    """Worker class for updating prices in a separate thread"""

    # Signals
    progress_updated = Signal(int)
    price_update_complete = Signal(int, list)  # updated_count, failed_updates

    def __init__(self, mutual_funds_stocks, logger):
        super().__init__()
        self.mutual_funds_stocks = mutual_funds_stocks
        self.logger = logger

    def update_prices(self):
        """Update prices for all mutual funds and stocks"""
        updated_count = 0
        failed_updates = []

        try:
            self.logger.info("🔄 Price update worker thread started")

            # Extract symbols for batch processing
            symbols = [fund.symbol.strip() for fund in self.mutual_funds_stocks if fund.symbol and fund.symbol.strip()]

            if not symbols:
                self.logger.error("❌ No valid symbols found in worker")
                self.price_update_complete.emit(0, ["No valid symbols found"])
                return

            self.logger.info(f"🔍 Starting price fetch for {len(symbols)} symbols: {symbols}")

            # Fetch prices one by one to show progress
            price_results = {}
            total_symbols = len(symbols)

            try:
                for i, symbol in enumerate(symbols):
                    # Update progress bar for each symbol being fetched
                    progress_value = i + 1
                    self.logger.debug(f"📊 Updating progress to {progress_value}/{total_symbols}")

                    # Emit signal to update progress bar in main thread
                    self.progress_updated.emit(progress_value)

                    self.logger.debug(f"🔍 Fetching price for symbol {i+1}/{total_symbols}: {symbol}")

                    # Fetch individual price
                    try:
                        price = price_fetcher.get_current_price(symbol)
                        if price is not None:
                            price_results[symbol] = price
                            self.logger.debug(f"✅ Got price for {symbol}: ₹{price:.2f}")
                        else:
                            self.logger.debug(f"❌ No price data for {symbol}")
                    except Exception as symbol_error:
                        self.logger.warning(f"❌ Failed to fetch price for {symbol}: {symbol_error}")

                    # Small delay to make progress visible and avoid rate limiting
                    import time
                    time.sleep(0.5)  # Increased delay for better visibility

                self.logger.info(f"✅ Price fetch completed, got {len(price_results)} results out of {total_symbols} symbols")

            except Exception as e:
                self.logger.error(f"❌ Price fetch process failed: {e}")
                import traceback
                self.logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                self.price_update_complete.emit(0, [f"Network error: Unable to fetch prices - {str(e)}"])
                return

            # Update each fund with the fetched price
            for i, fund in enumerate(self.mutual_funds_stocks):
                try:
                    if not fund.symbol or not fund.symbol.strip():
                        failed_updates.append(f"{fund.name}: No symbol defined")
                        continue

                    symbol = fund.symbol.strip()

                    if symbol in price_results:
                        new_price = price_results[symbol]
                        if new_price is not None and new_price > 0:
                            old_price = fund.current_price
                            fund.update_current_price(new_price)
                            updated_count += 1

                            # Log significant price changes
                            if old_price > 0:
                                change_pct = ((new_price - old_price) / old_price) * 100
                                if abs(change_pct) > 10:  # Log changes > 10%
                                    self.logger.warning(f"Large price change for {symbol}: {old_price:.2f} → {new_price:.2f} ({change_pct:+.1f}%)")

                            self.logger.debug(f"✅ Updated {fund.name} ({symbol}): ₹{old_price:.2f} → ₹{new_price:.2f}")
                        else:
                            failed_updates.append(f"{fund.name}: Invalid price data")
                    else:
                        failed_updates.append(f"{fund.name}: No price data available")

                except Exception as fund_error:
                    self.logger.error(f"❌ Error updating fund {fund.name}: {fund_error}")
                    failed_updates.append(f"{fund.name}: Update error - {str(fund_error)}")

            self.logger.info(f"✅ Price update completed: {updated_count} updated, {len(failed_updates)} failed")

            # Emit completion signal
            self.price_update_complete.emit(updated_count, failed_updates)

        except Exception as e:
            self.logger.error(f"Critical error in price update worker: {e}")
            self.price_update_complete.emit(0, [f"Critical system error: {str(e)}"])


class InvestmentTrackerWidget(QWidget):
    """Main investment tracker widget with multiple tabs"""

    def __init__(self, data_manager, config, parent=None):
        super().__init__(parent)

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("="*50)
        self.logger.info("INITIALIZING INVESTMENT TRACKER WIDGET")
        self.logger.info("="*50)

        try:
            self.data_manager = data_manager
            self.config = config

            # Initialize data model with error handling
            try:
                self.investment_model = InvestmentDataModel(data_manager)
                self.logger.info("✅ Investment data model initialized")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize investment data model: {e}")
                raise

            # Initialize CSV manager for data persistence
            try:
                self.csv_manager = InvestmentCSVManager(str(data_manager.data_dir))
                self.logger.info("✅ CSV manager initialized")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize CSV manager: {e}")
                raise

            # Setup UI with error handling
            try:
                self.setup_ui()
                self.logger.info("✅ UI setup completed")
            except Exception as e:
                self.logger.error(f"❌ Failed to setup UI: {e}")
                raise

            # Setup connections with error handling
            try:
                self.setup_connections()
                self.logger.info("✅ Connections setup completed")
            except Exception as e:
                self.logger.error(f"❌ Failed to setup connections: {e}")
                raise



            # Refresh data with error handling
            try:
                self.refresh_data()
                self.logger.info("✅ Data refresh completed")
            except Exception as e:
                self.logger.error(f"❌ Failed to refresh data: {e}")
                # This is not critical for initialization, continue without raising

            self.logger.info("✅ InvestmentTrackerWidget initialization SUCCESSFUL")

        except Exception as e:
            self.logger.error(f"❌ CRITICAL ERROR in InvestmentTrackerWidget.__init__: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise

    def setup_ui(self):
        """Setup the main UI with tabs"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Main header
        header_layout = QHBoxLayout()
        title_label = QLabel("📈 Investment Management Dashboard")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("investmentTabWidget")

        # Create all tabs with error handling
        tabs_to_create = [
            ("Current Resource", self.create_current_resource_tab),
            ("Asset/Liability Tracking", self.create_asset_liability_tab),
            ("Owned Assets", self.create_owned_assets_tab),
            ("Goal Planning & SIP Calculator", self.create_goal_planning_tab),
            ("Policy Tracking", self.create_policy_tracking_tab),
            ("Loan Details Tracking", self.create_loan_details_tab),
            ("Mutual Funds and Stock Tracking", self.create_mutual_funds_tab),
            ("Portfolio Allocation Analysis", self.create_portfolio_analysis_tab)
        ]

        for tab_name, tab_method in tabs_to_create:
            try:
                tab_method()
                self.logger.info(f"✅ {tab_name} tab created successfully")
            except Exception as e:
                self.logger.error(f"❌ Failed to create {tab_name} tab: {e}")
                # Create a placeholder tab instead of failing completely
                self.create_error_tab(tab_name, str(e))

        layout.addWidget(self.tab_widget)

    def create_error_tab(self, tab_name, error_message):
        """Create an error placeholder tab when a tab fails to load"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignCenter)

        # Error icon and message
        error_label = QLabel("⚠️ Tab Loading Error")
        error_label.setFont(QFont("Arial", 16, QFont.Bold))
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #d32f2f; margin: 20px;")
        layout.addWidget(error_label)

        # Tab name
        tab_name_label = QLabel(f"Failed to load: {tab_name}")
        tab_name_label.setFont(QFont("Arial", 12))
        tab_name_label.setAlignment(Qt.AlignCenter)
        tab_name_label.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(tab_name_label)

        # Error details
        error_details = QLabel(f"Error: {error_message}")
        error_details.setFont(QFont("Arial", 10))
        error_details.setAlignment(Qt.AlignCenter)
        error_details.setStyleSheet("color: #999; margin: 10px;")
        error_details.setWordWrap(True)
        layout.addWidget(error_details)

        # Retry button
        retry_button = QPushButton("🔄 Retry Loading")
        retry_button.clicked.connect(lambda: self.retry_tab_creation(tab_name))
        layout.addWidget(retry_button)

        # Add the error tab
        self.tab_widget.addTab(tab, f"❌ {tab_name}")

    def retry_tab_creation(self, tab_name):
        """Retry creating a failed tab"""
        self.logger.info(f"Retrying creation of {tab_name} tab")
        # For now, just show a message - could implement actual retry logic
        QMessageBox.information(self, "Retry", f"Retry functionality for {tab_name} tab is not yet implemented.")

    def create_current_resource_tab(self):
        """Create Tab 2: Current Resource"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("💰 Current Resource")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Add Resource button
        add_btn = QPushButton("➕ Add Resource")
        add_btn.clicked.connect(self.add_current_resource)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Current Resource table
        self.current_resource_table = CurrentResourceTableWidget()
        self.current_resource_table.resource_selected.connect(self.on_resource_selected)
        layout.addWidget(self.current_resource_table)

        # Action buttons
        action_layout = QHBoxLayout()

        self.edit_resource_btn = QPushButton("✏️ Edit Resource")
        self.edit_resource_btn.clicked.connect(self.edit_selected_resource)
        self.edit_resource_btn.setEnabled(False)
        action_layout.addWidget(self.edit_resource_btn)

        self.delete_resource_btn = QPushButton("🗑️ Delete Resource")
        self.delete_resource_btn.clicked.connect(self.delete_selected_resource)
        self.delete_resource_btn.setEnabled(False)
        action_layout.addWidget(self.delete_resource_btn)

        action_layout.addStretch()

        layout.addLayout(action_layout)

        self.tab_widget.addTab(tab, "Current Resource")

    def create_asset_liability_tab(self):
        """Create Tab 3: Enhanced Asset/Liability Tracking with Portfolio Management"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("⚖️ Portfolio Management")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Refresh Portfolio button
        refresh_btn = QPushButton("🔄 Refresh Portfolio")
        refresh_btn.clicked.connect(self.refresh_integrated_portfolio)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Sub-tabs for portfolio management
        sub_tab_widget = QTabWidget()

        # Main Portfolio View tab
        portfolio_tab = QWidget()
        portfolio_layout = QVBoxLayout(portfolio_tab)

        # Portfolio controls
        controls_layout = QHBoxLayout()

        # Add Asset/Liability button
        add_asset_btn = QPushButton("➕ Add Asset/Liability")
        add_asset_btn.clicked.connect(self.add_asset_liability)
        controls_layout.addWidget(add_asset_btn)

        # Manage Categories button
        manage_categories_btn = QPushButton("🏷️ Manage Categories")
        manage_categories_btn.clicked.connect(self.manage_categories)
        controls_layout.addWidget(manage_categories_btn)

        controls_layout.addStretch()

        # Export Portfolio button
        export_btn = QPushButton("📊 Export Portfolio")
        export_btn.clicked.connect(self.export_portfolio_data)
        controls_layout.addWidget(export_btn)

        portfolio_layout.addLayout(controls_layout)

        # Enhanced Asset/Liability table
        self.asset_liability_table = AssetLiabilityTableWidget()
        self.asset_liability_table.item_selected.connect(self.on_asset_liability_selected)
        portfolio_layout.addWidget(self.asset_liability_table)

        # Action buttons
        action_layout = QHBoxLayout()

        self.edit_asset_liability_btn = QPushButton("✏️ Edit Item")
        self.edit_asset_liability_btn.clicked.connect(self.edit_selected_asset_liability)
        self.edit_asset_liability_btn.setEnabled(False)
        action_layout.addWidget(self.edit_asset_liability_btn)

        self.delete_asset_liability_btn = QPushButton("🗑️ Delete Item")
        self.delete_asset_liability_btn.clicked.connect(self.delete_selected_asset_liability)
        self.delete_asset_liability_btn.setEnabled(False)
        action_layout.addWidget(self.delete_asset_liability_btn)

        action_layout.addStretch()

        # Portfolio summary
        self.portfolio_summary_label = QLabel("Portfolio Summary: Loading...")
        self.portfolio_summary_label.setFont(QFont("Arial", 10, QFont.Bold))
        action_layout.addWidget(self.portfolio_summary_label)

        portfolio_layout.addLayout(action_layout)

        sub_tab_widget.addTab(portfolio_tab, "Portfolio Overview")

        # Allocation Settings tab
        self.allocation_settings_widget = AllocationSettingsWidget()
        sub_tab_widget.addTab(self.allocation_settings_widget, "Allocation Settings")

        layout.addWidget(sub_tab_widget)

        self.tab_widget.addTab(tab, "Ideal Allocation")

    def create_owned_assets_tab(self):
        """Create Owned Assets tab for managing physical assets"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🏠 Owned Assets Management")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Add Asset button
        add_asset_btn = QPushButton("➕ Add Asset")
        add_asset_btn.clicked.connect(self.add_owned_asset)
        header_layout.addWidget(add_asset_btn)

        layout.addLayout(header_layout)

        # Description
        desc_label = QLabel("Manage your physical assets to get accurate net worth calculations for portfolio analysis.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 5px 0px;")
        layout.addWidget(desc_label)

        # Assets table
        self.owned_assets_table = QTableWidget()
        self.owned_assets_table.setColumnCount(8)
        self.owned_assets_table.setHorizontalHeaderLabels([
            "Name", "Category", "Sub-Category", "Purchase Value", "Current Value",
            "Location", "Purchase Date", "Notes"
        ])

        # Configure table
        header = self.owned_assets_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Category
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Sub-Category
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Purchase Value
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Current Value
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Location
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Purchase Date

        self.owned_assets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.owned_assets_table.setAlternatingRowColors(True)
        self.owned_assets_table.itemSelectionChanged.connect(self.on_owned_asset_selected)

        layout.addWidget(self.owned_assets_table)

        # Action buttons
        action_layout = QHBoxLayout()

        self.edit_owned_asset_btn = QPushButton("✏️ Edit Asset")
        self.edit_owned_asset_btn.clicked.connect(self.edit_selected_owned_asset)
        self.edit_owned_asset_btn.setEnabled(False)
        action_layout.addWidget(self.edit_owned_asset_btn)

        self.delete_owned_asset_btn = QPushButton("🗑️ Delete Asset")
        self.delete_owned_asset_btn.clicked.connect(self.delete_selected_owned_asset)
        self.delete_owned_asset_btn.setEnabled(False)
        action_layout.addWidget(self.delete_owned_asset_btn)

        action_layout.addStretch()

        # Summary
        self.owned_assets_summary_label = QLabel("Total Assets Value: ₹0")
        self.owned_assets_summary_label.setFont(QFont("Arial", 10, QFont.Bold))
        action_layout.addWidget(self.owned_assets_summary_label)

        layout.addLayout(action_layout)

        self.tab_widget.addTab(tab, "Owned Assets")

    def create_goal_planning_tab(self):
        """Create Tab 4: Goal Planning & SIP Calculator"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🎯 Goal Planning & SIP Calculator")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Add Goal button
        add_btn = QPushButton("➕ Add Goal")
        add_btn.clicked.connect(self.add_goal)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Goal Planning table
        self.goal_planning_table = GoalPlanningTableWidget()
        self.goal_planning_table.goal_selected.connect(self.on_goal_selected)
        layout.addWidget(self.goal_planning_table)

        # Action buttons
        action_layout = QHBoxLayout()

        self.edit_goal_btn = QPushButton("✏️ Edit Goal")
        self.edit_goal_btn.clicked.connect(self.edit_selected_goal)
        self.edit_goal_btn.setEnabled(False)
        action_layout.addWidget(self.edit_goal_btn)

        self.delete_goal_btn = QPushButton("🗑️ Delete Goal")
        self.delete_goal_btn.clicked.connect(self.delete_selected_goal)
        self.delete_goal_btn.setEnabled(False)
        action_layout.addWidget(self.delete_goal_btn)

        action_layout.addStretch()

        layout.addLayout(action_layout)

        self.tab_widget.addTab(tab, "Goal Planning")

    def create_policy_tracking_tab(self):
        """Create Tab 5: Policy Tracking with sub-tabs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🛡️ Policy Tracking")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Create sub-tab widget for policy tracking
        self.policy_sub_tabs = QTabWidget()

        # Create sub-tabs
        self.create_general_insurance_tab()
        self.create_lic_policy_tab()

        layout.addWidget(self.policy_sub_tabs)

        self.tab_widget.addTab(tab, "Policy Tracking")

    def create_general_insurance_tab(self):
        """Create General Insurance sub-tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header with action buttons
        header_layout = QHBoxLayout()
        header_layout.addStretch()

        # Add Policy button
        add_btn = QPushButton("➕ Add Policy")
        add_btn.clicked.connect(self.add_policy)
        header_layout.addWidget(add_btn)

        # Manage Policy Types button
        manage_btn = QPushButton("📋 Manage Policy Types")
        manage_btn.clicked.connect(self.manage_policy_types)
        header_layout.addWidget(manage_btn)

        layout.addLayout(header_layout)

        # Filter and Search Section
        filter_group = QGroupBox("Filter & Search")
        filter_layout = QHBoxLayout(filter_group)

        # Policy Type Filter
        filter_layout.addWidget(QLabel("Filter by Type:"))
        self.policy_type_filter = QComboBox()
        self.policy_type_filter.addItem("All Types")
        self.policy_type_filter.addItems([
            "Vehicle Insurance", "Health Insurance", "Life Insurance", "Property Insurance"
        ])
        self.policy_type_filter.currentTextChanged.connect(self.filter_policies)
        filter_layout.addWidget(self.policy_type_filter)

        # Status Filter
        filter_layout.addWidget(QLabel("Filter by Status:"))
        self.policy_status_filter = QComboBox()
        self.policy_status_filter.addItem("All Status")
        self.policy_status_filter.addItems([
            "Active", "Expired", "Pending Renewal", "Cancelled", "Lapsed"
        ])
        self.policy_status_filter.currentTextChanged.connect(self.filter_policies)
        filter_layout.addWidget(self.policy_status_filter)

        # Search Box
        filter_layout.addWidget(QLabel("Search:"))
        self.policy_search_box = QLineEdit()
        self.policy_search_box.setPlaceholderText("Search by policy name, provider, or number...")
        self.policy_search_box.textChanged.connect(self.filter_policies)
        filter_layout.addWidget(self.policy_search_box)

        # Clear Filters Button
        clear_filter_btn = QPushButton("🔄 Clear Filters")
        clear_filter_btn.clicked.connect(self.clear_policy_filters)
        filter_layout.addWidget(clear_filter_btn)

        layout.addWidget(filter_group)

        # Enhanced Policy table with comprehensive columns
        self.policy_table = QTableWidget()
        self.policy_table.setColumnCount(14)
        self.policy_table.setHorizontalHeaderLabels([
            'Policy Name', 'Provider', 'Type', 'Policy Number', 'Coverage Type',
            'Coverage Amount', 'Premium', 'Frequency', 'Start Date', 'End Date',
            'Status', 'Deductible', 'Beneficiaries', 'Remarks'
        ])

        # Table settings
        self.policy_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.policy_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.policy_table.setAlternatingRowColors(True)
        self.policy_table.setSortingEnabled(True)
        self.policy_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Disable direct editing

        # Enhanced column resize functionality
        policy_header = self.policy_table.horizontalHeader()
        policy_header.setStretchLastSection(True)  # Last column (Remarks) stretches

        # Set specific column widths for better display
        column_widths = {
            0: 150,  # Policy Name
            1: 120,  # Provider
            2: 100,  # Type
            3: 120,  # Policy Number
            4: 120,  # Coverage Type
            5: 100,  # Coverage Amount
            6: 80,   # Premium
            7: 80,   # Frequency
            8: 90,   # Start Date
            9: 90,   # End Date
            10: 80,  # Status
            11: 80,  # Deductible
            12: 120, # Beneficiaries
        }

        for col, width in column_widths.items():
            policy_header.setSectionResizeMode(col, QHeaderView.Interactive)
            self.policy_table.setColumnWidth(col, width)

        # Last column (Remarks) stretches
        policy_header.setSectionResizeMode(13, QHeaderView.Stretch)

        # Connect selection signal
        self.policy_table.itemSelectionChanged.connect(self.on_policy_selected)

        layout.addWidget(self.policy_table)

        # Action buttons for policy table
        policy_action_layout = QHBoxLayout()

        self.edit_policy_btn = QPushButton("✏️ Edit Policy")
        self.edit_policy_btn.clicked.connect(self.edit_selected_policy)
        self.edit_policy_btn.setEnabled(False)
        policy_action_layout.addWidget(self.edit_policy_btn)

        self.delete_policy_btn = QPushButton("🗑️ Delete Policy")
        self.delete_policy_btn.clicked.connect(self.delete_selected_policy)
        self.delete_policy_btn.setEnabled(False)
        policy_action_layout.addWidget(self.delete_policy_btn)

        policy_action_layout.addStretch()

        layout.addLayout(policy_action_layout)

        self.policy_sub_tabs.addTab(tab, "🏥 General Insurance")

    def create_lic_policy_tab(self):
        """Create LIC Policy Tracking sub-tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header with action buttons
        header_layout = QHBoxLayout()
        header_layout.addStretch()

        # Add LIC Policy button
        add_lic_btn = QPushButton("➕ Add LIC Policy")
        add_lic_btn.clicked.connect(self.add_lic_policy)
        header_layout.addWidget(add_lic_btn)

        layout.addLayout(header_layout)

        # Filter and Search Section for LIC policies
        filter_group = QGroupBox("Filter & Search LIC Policies")
        filter_layout = QHBoxLayout(filter_group)

        # Family Member Filter
        filter_layout.addWidget(QLabel("Filter by Family Member:"))
        self.lic_family_filter = QComboBox()
        self.lic_family_filter.addItem("All Family Members")
        self.lic_family_filter.currentTextChanged.connect(self.filter_lic_policies)
        filter_layout.addWidget(self.lic_family_filter)

        # Policy Type Filter
        filter_layout.addWidget(QLabel("Filter by Type:"))
        self.lic_type_filter = QComboBox()
        self.lic_type_filter.addItem("All Types")
        self.lic_type_filter.addItems([
            "Endowment", "Term", "ULIP", "Pension", "Money Back", "Whole Life"
        ])
        self.lic_type_filter.currentTextChanged.connect(self.filter_lic_policies)
        filter_layout.addWidget(self.lic_type_filter)

        # Status Filter
        filter_layout.addWidget(QLabel("Filter by Status:"))
        self.lic_status_filter = QComboBox()
        self.lic_status_filter.addItem("All Status")
        self.lic_status_filter.addItems([
            "Active", "Paid-up", "Lapsed", "Matured", "Surrendered"
        ])
        self.lic_status_filter.currentTextChanged.connect(self.filter_lic_policies)
        filter_layout.addWidget(self.lic_status_filter)

        # Search Box
        filter_layout.addWidget(QLabel("Search:"))
        self.lic_search_box = QLineEdit()
        self.lic_search_box.setPlaceholderText("Search by policy number, holder name, or plan...")
        self.lic_search_box.textChanged.connect(self.filter_lic_policies)
        filter_layout.addWidget(self.lic_search_box)

        # Clear Filters Button
        clear_lic_filter_btn = QPushButton("🔄 Clear Filters")
        clear_lic_filter_btn.clicked.connect(self.clear_lic_filters)
        filter_layout.addWidget(clear_lic_filter_btn)

        layout.addWidget(filter_group)

        # LIC Policy table with comprehensive columns
        self.lic_policy_table = QTableWidget()
        self.lic_policy_table.setColumnCount(12)
        self.lic_policy_table.setHorizontalHeaderLabels([
            'Policy Holder', 'Policy Number', 'Policy Type', 'Plan Name',
            'Premium Amount', 'Premium Frequency', 'Sum Assured', 'Maturity Date',
            'Status', 'Nominee', 'Agent', 'Remarks'
        ])

        # Table settings
        self.lic_policy_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lic_policy_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lic_policy_table.setAlternatingRowColors(True)
        self.lic_policy_table.setSortingEnabled(True)
        self.lic_policy_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Enhanced column resize functionality
        lic_header = self.lic_policy_table.horizontalHeader()
        lic_header.setStretchLastSection(True)  # Last column (Remarks) stretches

        # Set specific column widths for better display
        lic_column_widths = {
            0: 120,  # Policy Holder
            1: 120,  # Policy Number
            2: 100,  # Policy Type
            3: 150,  # Plan Name
            4: 100,  # Premium Amount
            5: 100,  # Premium Frequency
            6: 100,  # Sum Assured
            7: 100,  # Maturity Date
            8: 80,   # Status
            9: 100,  # Nominee
            10: 100, # Agent
        }

        for col, width in lic_column_widths.items():
            lic_header.setSectionResizeMode(col, QHeaderView.Interactive)
            self.lic_policy_table.setColumnWidth(col, width)

        # Last column (Remarks) stretches
        lic_header.setSectionResizeMode(11, QHeaderView.Stretch)

        # Connect selection signal
        self.lic_policy_table.itemSelectionChanged.connect(self.on_lic_policy_selected)

        # Connect double-click signal for benefit calculator
        self.lic_policy_table.itemDoubleClicked.connect(self.open_benefit_calculator)

        layout.addWidget(self.lic_policy_table)

        # Action buttons for LIC policy table
        lic_action_layout = QHBoxLayout()

        self.edit_lic_policy_btn = QPushButton("✏️ Edit LIC Policy")
        self.edit_lic_policy_btn.clicked.connect(self.edit_selected_lic_policy)
        self.edit_lic_policy_btn.setEnabled(False)
        lic_action_layout.addWidget(self.edit_lic_policy_btn)

        self.delete_lic_policy_btn = QPushButton("🗑️ Delete LIC Policy")
        self.delete_lic_policy_btn.clicked.connect(self.delete_selected_lic_policy)
        self.delete_lic_policy_btn.setEnabled(False)
        lic_action_layout.addWidget(self.delete_lic_policy_btn)

        lic_action_layout.addStretch()

        layout.addLayout(lic_action_layout)

        self.policy_sub_tabs.addTab(tab, "🏛️ LIC Policy Tracking")

    def create_loan_details_tab(self):
        """Create Tab 6: Loan Details Tracking"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🏦 Loan Details Tracking")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Add Loan button
        add_btn = QPushButton("➕ Add Loan")
        add_btn.clicked.connect(self.add_loan)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Loan table with proper column resize functionality
        self.loan_table = QTableWidget()
        self.loan_table.setColumnCount(10)
        self.loan_table.setHorizontalHeaderLabels([
            'Loan Name', 'Current Balance', 'Interest Rate', 'Remaining Period',
            'EMI Amount', 'EMI Start Date', 'EMI End Date', 'Last Paid Date',
            'Net Tenure', 'Loan Holder'
        ])

        # Table settings
        self.loan_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.loan_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.loan_table.setAlternatingRowColors(True)
        self.loan_table.setSortingEnabled(True)
        self.loan_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Disable direct editing

        # Proper column resize functionality
        loan_header = self.loan_table.horizontalHeader()
        loan_header.setStretchLastSection(True)  # Last column stretches
        for i in range(3):  # First 3 columns get ResizeToContents
            loan_header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        loan_header.setSectionResizeMode(3, QHeaderView.Stretch)  # Remaining Period column stretches

        # Connect selection signal
        self.loan_table.itemSelectionChanged.connect(self.on_loan_selected)

        # Connect double-click signal for payment history
        self.loan_table.itemDoubleClicked.connect(self.open_loan_payment_history)

        layout.addWidget(self.loan_table)

        # Action buttons for loan table
        loan_action_layout = QHBoxLayout()

        self.edit_loan_btn = QPushButton("✏️ Edit Loan")
        self.edit_loan_btn.clicked.connect(self.edit_selected_loan)
        self.edit_loan_btn.setEnabled(False)
        loan_action_layout.addWidget(self.edit_loan_btn)

        self.delete_loan_btn = QPushButton("🗑️ Delete Loan")
        self.delete_loan_btn.clicked.connect(self.delete_selected_loan)
        self.delete_loan_btn.setEnabled(False)
        loan_action_layout.addWidget(self.delete_loan_btn)

        loan_action_layout.addStretch()

        layout.addLayout(loan_action_layout)

        self.tab_widget.addTab(tab, "Loan Details")

    def create_mutual_funds_tab(self):
        """Create Tab 7: Mutual Funds and Stock Tracking"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("📈 Mutual Funds & Stocks")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Add Fund/Stock button
        add_btn = QPushButton("➕ Add Fund/Stock")
        add_btn.clicked.connect(self.add_mutual_fund)
        header_layout.addWidget(add_btn)

        # Manage Categories button
        manage_cat_btn = QPushButton("🏷️ Manage Categories")
        manage_cat_btn.clicked.connect(self.manage_fund_categories)
        header_layout.addWidget(manage_cat_btn)

        # Manage Sub-Categories button
        manage_subcat_btn = QPushButton("🏷️ Manage Sub-Categories")
        manage_subcat_btn.clicked.connect(self.manage_fund_subcategories)
        header_layout.addWidget(manage_subcat_btn)

        # Update Prices button
        self.update_prices_btn = QPushButton("🔄 Update Prices")
        self.update_prices_btn.clicked.connect(self.update_all_prices)
        self.update_prices_btn.setToolTip("Click to fetch current market prices for all investments")
        header_layout.addWidget(self.update_prices_btn)

        layout.addLayout(header_layout)

        # Portfolio summary section
        summary_layout = QHBoxLayout()

        # Total portfolio value
        self.total_portfolio_label = QLabel("Total Portfolio Value: ₹0.00")
        self.total_portfolio_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_portfolio_label.setStyleSheet("color: #2E7D32; padding: 5px;")
        summary_layout.addWidget(self.total_portfolio_label)

        # Last update timestamp
        self.last_update_label = QLabel("Last Updated: Never")
        self.last_update_label.setFont(QFont("Arial", 10))
        self.last_update_label.setStyleSheet("color: #666; padding: 5px;")
        summary_layout.addWidget(self.last_update_label)

        summary_layout.addStretch()

        # Progress bar for price updates - make it more prominent
        self.price_update_progress = QProgressBar()
        self.price_update_progress.setVisible(False)
        self.price_update_progress.setMinimumWidth(400)  # Even wider
        self.price_update_progress.setMaximumWidth(600)  # Allow it to be much wider
        self.price_update_progress.setMinimumHeight(30)  # Make it taller for visibility

        # Add more prominent styling
        self.price_update_progress.setStyleSheet("""
            QProgressBar {
                border: 3px solid #e74c3c;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                font-size: 14px;
                background-color: #fff;
                color: #2c3e50;
                padding: 2px;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 7px;
                margin: 1px;
            }
        """)

        summary_layout.addWidget(self.price_update_progress)

        layout.addLayout(summary_layout)

        # Additional progress bar section for better visibility
        progress_section = QHBoxLayout()
        progress_section.addStretch()

        # Create a second progress bar that's more prominent
        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setVisible(False)
        self.main_progress_bar.setMinimumWidth(500)
        self.main_progress_bar.setMinimumHeight(35)
        self.main_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 3px solid #27ae60;
                border-radius: 12px;
                text-align: center;
                font-weight: bold;
                font-size: 16px;
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 3px;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 9px;
                margin: 2px;
            }
        """)

        progress_section.addWidget(self.main_progress_bar)
        progress_section.addStretch()
        layout.addLayout(progress_section)

        # Mutual Funds & Stocks table with proper column resize functionality
        self.mutual_funds_table = QTableWidget()
        self.mutual_funds_table.setColumnCount(10)
        self.mutual_funds_table.setHorizontalHeaderLabels([
            'Name', 'Symbol', 'Category', 'Sub Category', 'Geographic Classification',
            'Units', 'Current Price', 'Current Amount', 'Current Allocation', 'Remarks'
        ])

        # Table settings
        self.mutual_funds_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.mutual_funds_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.mutual_funds_table.setAlternatingRowColors(True)
        self.mutual_funds_table.setSortingEnabled(True)
        self.mutual_funds_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Disable direct editing

        # Proper column resize functionality
        funds_header = self.mutual_funds_table.horizontalHeader()
        funds_header.setStretchLastSection(True)  # Last column (Remarks) stretches
        for i in range(9):  # All columns except last get ResizeToContents
            funds_header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        funds_header.setSectionResizeMode(9, QHeaderView.Stretch)  # Remarks column stretches

        # Connect selection signal
        self.mutual_funds_table.itemSelectionChanged.connect(self.on_mutual_fund_selected)

        # Connect double-click signal for investment details
        self.mutual_funds_table.itemDoubleClicked.connect(self.on_mutual_fund_double_clicked)

        layout.addWidget(self.mutual_funds_table)

        # Action buttons for mutual funds table
        funds_action_layout = QHBoxLayout()

        self.edit_fund_btn = QPushButton("✏️ Edit Fund/Stock")
        self.edit_fund_btn.clicked.connect(self.edit_selected_mutual_fund)
        self.edit_fund_btn.setEnabled(False)
        funds_action_layout.addWidget(self.edit_fund_btn)

        self.delete_fund_btn = QPushButton("🗑️ Delete Fund/Stock")
        self.delete_fund_btn.clicked.connect(self.delete_selected_mutual_fund)
        self.delete_fund_btn.setEnabled(False)
        funds_action_layout.addWidget(self.delete_fund_btn)

        funds_action_layout.addStretch()

        layout.addLayout(funds_action_layout)

        # Create sub-tabs for mutual funds
        mutual_funds_sub_tabs = QTabWidget()

        # Main mutual funds tab
        main_funds_tab = QWidget()
        main_funds_layout = QVBoxLayout(main_funds_tab)

        # Move all the existing content to the main tab
        # (The content is already in the main layout, so we need to reparent it)
        # Create a new widget to hold the existing content
        existing_content = QWidget()
        existing_content.setLayout(layout)
        main_funds_layout.addWidget(existing_content)

        mutual_funds_sub_tabs.addTab(main_funds_tab, "📈 Holdings")

        # Purchase History tab
        self.create_purchase_history_tab(mutual_funds_sub_tabs)

        # Create a new main layout for the tab
        tab_main_layout = QVBoxLayout(tab)
        tab_main_layout.addWidget(mutual_funds_sub_tabs)

        self.tab_widget.addTab(tab, "Mutual Funds & Stocks")

    def create_purchase_history_tab(self, parent_tab_widget):
        """Create Purchase History tab for mutual funds"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("📋 Purchase History")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Add Transaction button
        add_transaction_btn = QPushButton("➕ Add Transaction")
        add_transaction_btn.clicked.connect(self.add_purchase_transaction)
        header_layout.addWidget(add_transaction_btn)

        layout.addLayout(header_layout)

        # Purchase History table
        self.purchase_history_table = QTableWidget()
        self.purchase_history_table.setColumnCount(9)
        self.purchase_history_table.setHorizontalHeaderLabels([
            'Fund/Stock Name', 'Transaction Type', 'Date', 'Units',
            'Unit Price', 'Total Amount', 'Fees', 'Net Amount', 'Notes'
        ])

        # Table settings
        self.purchase_history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.purchase_history_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.purchase_history_table.setAlternatingRowColors(True)
        self.purchase_history_table.setSortingEnabled(True)
        self.purchase_history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Column resize settings
        history_header = self.purchase_history_table.horizontalHeader()
        history_header.setStretchLastSection(True)  # Notes column stretches
        for i in range(8):  # All columns except last get ResizeToContents
            history_header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        history_header.setSectionResizeMode(8, QHeaderView.Stretch)  # Notes column stretches

        # Connect selection signal
        self.purchase_history_table.itemSelectionChanged.connect(self.on_purchase_history_selected)

        layout.addWidget(self.purchase_history_table)

        # Action buttons
        history_action_layout = QHBoxLayout()

        self.edit_transaction_btn = QPushButton("✏️ Edit Transaction")
        self.edit_transaction_btn.clicked.connect(self.edit_selected_transaction)
        self.edit_transaction_btn.setEnabled(False)
        history_action_layout.addWidget(self.edit_transaction_btn)

        self.delete_transaction_btn = QPushButton("🗑️ Delete Transaction")
        self.delete_transaction_btn.clicked.connect(self.delete_selected_transaction)
        self.delete_transaction_btn.setEnabled(False)
        history_action_layout.addWidget(self.delete_transaction_btn)

        history_action_layout.addStretch()

        layout.addLayout(history_action_layout)

        parent_tab_widget.addTab(tab, "📋 Purchase History")

    def create_portfolio_analysis_tab(self):
        """Create Tab 8: Portfolio Allocation Analysis"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("📊 Portfolio Allocation Analysis")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Net Worth display
        self.net_worth_label = QLabel("Net Worth: ₹0.00")
        self.net_worth_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.net_worth_label.setStyleSheet("color: #2E7D32; padding: 5px; border: 2px solid #4CAF50; border-radius: 5px; background-color: #E8F5E8;")
        header_layout.addWidget(self.net_worth_label)

        # Refresh Analysis button
        refresh_btn = QPushButton("🔄 Refresh Analysis")
        refresh_btn.clicked.connect(self.refresh_portfolio_analysis)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Sub-tabs for main analysis and snapshots
        sub_tab_widget = QTabWidget()

        # Main Analysis tab
        main_analysis_tab = QWidget()
        main_layout = QVBoxLayout(main_analysis_tab)

        # Portfolio Analysis table with enhanced column structure
        self.portfolio_analysis_table = QTableWidget()
        self.portfolio_analysis_table.setColumnCount(9)
        self.portfolio_analysis_table.setHorizontalHeaderLabels([
            'Name', 'Type', 'Category', 'Sub-Category', 'Geographic Classification',
            'Ideal Allocation %', 'Current Allocation %', 'Difference %', 'Difference Amount'
        ])

        # Table settings
        self.portfolio_analysis_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.portfolio_analysis_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.portfolio_analysis_table.setAlternatingRowColors(True)
        self.portfolio_analysis_table.setSortingEnabled(True)

        # Proper column resize functionality for enhanced structure
        analysis_header = self.portfolio_analysis_table.horizontalHeader()
        analysis_header.setStretchLastSection(True)  # Last column stretches
        # Set specific resize modes for better visibility
        analysis_header.setSectionResizeMode(0, QHeaderView.Stretch)          # Name (stretches)
        analysis_header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Type
        analysis_header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Category
        analysis_header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Sub-Category
        analysis_header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Geographic Classification
        analysis_header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Ideal Allocation %
        analysis_header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Current Allocation %
        analysis_header.setSectionResizeMode(7, QHeaderView.ResizeToContents) # Difference %
        analysis_header.setSectionResizeMode(8, QHeaderView.Stretch)          # Difference Amount (stretches)

        main_layout.addWidget(self.portfolio_analysis_table)
        sub_tab_widget.addTab(main_analysis_tab, "Analysis")

        # Enhanced Snapshots tab with historical tracking and growth visualization
        snapshots_tab = QWidget()
        snapshots_layout = QVBoxLayout(snapshots_tab)

        # Create sub-tabs for different views
        snapshots_sub_tabs = QTabWidget()

        # Transaction History tab
        transaction_history_tab = QWidget()
        transaction_layout = QVBoxLayout(transaction_history_tab)

        # Transaction history controls
        transaction_controls_layout = QHBoxLayout()
        refresh_transactions_btn = QPushButton("🔄 Refresh Transactions")
        refresh_transactions_btn.clicked.connect(self.refresh_transaction_history_table)
        transaction_controls_layout.addWidget(refresh_transactions_btn)
        transaction_controls_layout.addStretch()
        transaction_layout.addLayout(transaction_controls_layout)

        # Transaction history table
        self.transaction_history_table = QTableWidget()
        self.transaction_history_table.setColumnCount(8)
        self.transaction_history_table.setHorizontalHeaderLabels([
            'Date', 'Asset Name', 'Type', 'Units', 'Price/Unit', 'Total Amount', 'Previous Units', 'New Units'
        ])

        # Table settings
        self.transaction_history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.transaction_history_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.transaction_history_table.setAlternatingRowColors(True)
        self.transaction_history_table.setSortingEnabled(True)
        # Allow editing only for the "New Units" column (column 7)
        self.transaction_history_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

        # Connect item changed signal to handle unit updates
        self.transaction_history_table.itemChanged.connect(self.on_transaction_history_item_changed)

        # Column resize settings
        transaction_header = self.transaction_history_table.horizontalHeader()
        transaction_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        transaction_header.setSectionResizeMode(1, QHeaderView.Stretch)          # Asset Name
        transaction_header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Type
        transaction_header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Units
        transaction_header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Price/Unit
        transaction_header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Total Amount
        transaction_header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Previous Units
        transaction_header.setSectionResizeMode(7, QHeaderView.ResizeToContents) # New Units

        transaction_layout.addWidget(self.transaction_history_table)
        snapshots_sub_tabs.addTab(transaction_history_tab, "📋 Transaction History")

        # Portfolio Growth tab
        growth_tab = QWidget()
        growth_layout = QVBoxLayout(growth_tab)

        # Growth controls with time filters
        growth_controls_layout = QHBoxLayout()
        refresh_growth_btn = QPushButton("🔄 Refresh Growth Data")
        refresh_growth_btn.clicked.connect(self.refresh_portfolio_growth_table)
        growth_controls_layout.addWidget(refresh_growth_btn)

        # Add button to create initial growth records if missing
        create_records_btn = QPushButton("📊 Create Growth Records")
        create_records_btn.clicked.connect(self.force_create_individual_growth_records)
        create_records_btn.setToolTip("Create individual investment growth records if missing")
        growth_controls_layout.addWidget(create_records_btn)

        # Time filter controls
        time_filter_label = QLabel("Time Filter:")
        growth_controls_layout.addWidget(time_filter_label)

        self.time_filter_combo = QComboBox()
        self.time_filter_combo.addItems(["All Time", "Last Month", "Last Year"])
        self.time_filter_combo.currentTextChanged.connect(self.on_time_filter_changed)
        growth_controls_layout.addWidget(self.time_filter_combo)

        growth_controls_layout.addStretch()
        growth_layout.addLayout(growth_controls_layout)

        # Portfolio growth table - modified for individual investments
        self.portfolio_growth_table = QTableWidget()
        self.portfolio_growth_table.setColumnCount(6)
        self.portfolio_growth_table.setHorizontalHeaderLabels([
            'Date', 'Investment Name', 'Units', 'Unit Price', 'Current Value', 'Notes'
        ])

        # Table settings
        self.portfolio_growth_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.portfolio_growth_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.portfolio_growth_table.setAlternatingRowColors(True)
        self.portfolio_growth_table.setSortingEnabled(True)
        self.portfolio_growth_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Column resize settings
        growth_header = self.portfolio_growth_table.horizontalHeader()
        growth_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        growth_header.setSectionResizeMode(1, QHeaderView.Stretch)           # Investment Name
        growth_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Units
        growth_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Unit Price
        growth_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Current Value
        growth_header.setSectionResizeMode(5, QHeaderView.Stretch)           # Notes

        # Add growth visualization chart
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            from ...ui.plotly_theme import apply_dark_theme_to_figure

            # Create chart widget (following working pattern from other modules)
            self.growth_chart_widget = QWebEngineView()
            self.growth_chart_widget.setMinimumHeight(400)
            # CRITICAL FIX: Add size policy like working charts
            self.growth_chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            # Create initial chart immediately (following working pattern)
            self._create_initial_growth_chart()

            growth_layout.addWidget(self.growth_chart_widget)

            # Add refresh chart button
            refresh_chart_btn = QPushButton("📊 Refresh Growth Chart")
            refresh_chart_btn.clicked.connect(self.refresh_portfolio_growth_chart)
            growth_controls_layout.addWidget(refresh_chart_btn)

        except ImportError:
            # Fallback if web engine or plotly not available
            chart_placeholder = QLabel("📊 Growth Chart (Requires Plotly and WebEngine)")
            chart_placeholder.setAlignment(Qt.AlignCenter)
            chart_placeholder.setMinimumHeight(400)
            chart_placeholder.setStyleSheet("border: 2px dashed #666; color: #666; font-size: 14px;")
            growth_layout.addWidget(chart_placeholder)

        growth_layout.addWidget(self.portfolio_growth_table)
        snapshots_sub_tabs.addTab(growth_tab, "📈 Portfolio Growth")

        snapshots_layout.addWidget(snapshots_sub_tabs)
        sub_tab_widget.addTab(snapshots_tab, "Historical Tracking")

        layout.addWidget(sub_tab_widget)

        # Connect tab change signal to refresh data
        sub_tab_widget.currentChanged.connect(self.on_portfolio_analysis_tab_changed)

        # Store reference to sub-tab widget for later access
        self.portfolio_analysis_sub_tabs = sub_tab_widget

        self.tab_widget.addTab(tab, "Portfolio Analysis")

    def setup_connections(self):
        """Setup signal connections and load data from CSV files"""
        # Initialize data lists for new tabs and load from CSV
        self.current_resources = self.csv_manager.load_data('current_resources', CurrentResource)
        self.asset_liability_items = self.csv_manager.load_data('asset_liability', AssetLiability)
        self.asset_liability_categories = [
            "Real Estate", "Vehicles", "Investments", "Cash & Bank",
            "Personal Property", "Credit Cards", "Loans", "Mortgages",
            "Plots", "Cars", "Bikes", "Gold", "Crypto", "Equity", "Debt",
            "Physical Assets", "Other"
        ]
        self.financial_goals = self.csv_manager.load_data('financial_goals', FinancialGoal)
        self.insurance_policies = self.csv_manager.load_data('insurance_policies', InsurancePolicy)
        self.policy_types = ["Vehicle Insurance", "Health Insurance", "Life Insurance", "Property Insurance"]
        self.lic_policies = self.csv_manager.load_data('lic_policies', LICPolicy)
        self.lic_policy_types = ["Endowment", "Term", "ULIP", "Pension", "Money Back", "Whole Life"]
        self.loan_details = self.csv_manager.load_data('loan_details', LoanDetails)
        self.mutual_funds_stocks = self.csv_manager.load_data('mutual_funds_stocks', MutualFundStock)
        self.mutual_fund_purchase_history = self.csv_manager.load_data('mutual_fund_purchase_history', MutualFundPurchaseHistory)
        self.fund_categories = ["Equity", "Debt", "Hybrid", "ELSS", "International", "Sectoral", "Index", "ETF"]
        self.fund_subcategories = ["Large Cap", "Mid Cap", "Small Cap", "Multi Cap", "Value", "Growth", "Dividend Yield", "Contra"]

        # Load enhanced portfolio tracking data
        self.portfolio_snapshots = self.csv_manager.load_data('portfolio_snapshots', PortfolioSnapshot)
        self.transaction_history = self.csv_manager.load_data('transaction_history', TransactionHistory)
        self.portfolio_growth_snapshots = self.csv_manager.load_data('portfolio_growth_snapshots', PortfolioGrowthSnapshot)
        self.individual_investment_growth = self.csv_manager.load_data('individual_investment_growth', IndividualInvestmentGrowth)

        # Initialize transaction history with all mutual funds/stocks if not already present
        self.initialize_transaction_history()

        # Create daily portfolio growth snapshot if needed
        self.create_daily_portfolio_snapshot()

        # Load allocation settings for portfolio management
        self.allocation_settings = self.csv_manager.load_data('allocation_settings', AllocationSettings)

        # Load monthly savings target
        monthly_targets = self.csv_manager.load_data('monthly_savings_target', MonthlySavingsTarget)
        if monthly_targets:
            self.monthly_savings_target = monthly_targets[0]  # Only one target should exist
        else:
            # Create default target
            self.monthly_savings_target = MonthlySavingsTarget()
            # Save the default target
            self.csv_manager.save_data('monthly_savings_target', [self.monthly_savings_target])

        # Load owned assets for comprehensive net worth calculation
        self.owned_assets = self.csv_manager.load_data('owned_assets', OwnedAsset)
        self.owned_asset_categories = [
            "Real Estate", "Vehicle", "Gold & Jewelry", "Cash & Bank",
            "Electronics", "Furniture", "Art & Collectibles", "Other"
        ]

        # Initialize default allocation settings if none exist
        self.initialize_default_allocation_settings()

        # Load categories from CSV (will use defaults if CSV doesn't exist)
        self.load_categories_from_csv()

        # Connect main tab widget to refresh portfolio data when Portfolio Analysis tab is accessed
        self.tab_widget.currentChanged.connect(self.on_main_tab_changed)
        self.portfolio_snapshots = self.csv_manager.load_data('portfolio_snapshots', PortfolioSnapshot)

        self.logger.info(f"Loaded data: {len(self.current_resources)} resources, {len(self.asset_liability_items)} assets/liabilities, "
                        f"{len(self.financial_goals)} goals, {len(self.insurance_policies)} policies, "
                        f"{len(self.loan_details)} loans, {len(self.mutual_funds_stocks)} funds/stocks, "
                        f"{len(self.portfolio_snapshots)} snapshots")

        # Refresh all tables with loaded data
        self.refresh_policy_table()
        self.refresh_lic_policy_table()
        self.refresh_loan_table()
        self.refresh_mutual_funds_table()
        self.refresh_purchase_history_table()

        # Initialize portfolio summary
        self.update_portfolio_summary()
        self.update_last_price_update_display()

        # Initialize Net Worth display
        self.update_net_worth_display()

    def refresh_data(self):
        """Refresh investment data and update display"""
        # Refresh tab data
        self.refresh_current_resource_table()
        self.refresh_asset_liability_table()
        self.refresh_goal_planning_table()
        self.refresh_policy_table()
        self.refresh_lic_policy_table()
        self.refresh_loan_table()
        self.refresh_mutual_funds_table()
        self.refresh_purchase_history_table()

        # Refresh integrated portfolio view
        self.refresh_integrated_portfolio()

        # Load allocation settings into the widget
        if hasattr(self, 'allocation_settings_widget') and hasattr(self, 'allocation_settings'):
            self.allocation_settings_widget.load_settings(self.allocation_settings)

        # Load monthly savings target into the allocation settings widget
        if hasattr(self, 'allocation_settings_widget') and hasattr(self, 'monthly_savings_target'):
            self.allocation_settings_widget.load_monthly_savings_target(self.monthly_savings_target)

        # Update Net Worth display after all data refreshes
        self.update_net_worth_display()

    def on_monthly_savings_target_changed(self, updated_target):
        """Handle changes to monthly savings target"""
        try:
            self.monthly_savings_target = updated_target
            self.logger.info(f"Monthly savings target updated to ₹{updated_target.target_amount:,.2f}")

            # Refresh portfolio analysis to reflect new target in difference calculations
            if hasattr(self, 'refresh_portfolio_analysis'):
                self.refresh_portfolio_analysis()

        except Exception as e:
            self.logger.error(f"Error handling monthly savings target change: {e}")

    def initialize_transaction_history(self):
        """Initialize transaction history with all mutual funds/stocks if not already present"""
        try:
            if not hasattr(self, 'mutual_funds_stocks') or not self.mutual_funds_stocks:
                return

            # Get existing transaction asset names
            existing_assets = set()
            if hasattr(self, 'transaction_history') and self.transaction_history:
                existing_assets = {t.asset_name.strip().lower() for t in self.transaction_history}

            # Track if we need to save changes
            changes_made = False

            # Initialize transaction history list if it doesn't exist
            if not hasattr(self, 'transaction_history'):
                self.transaction_history = []

            # Add initial transaction for each mutual fund/stock that doesn't have one
            for fund in self.mutual_funds_stocks:
                fund_name_key = fund.name.strip().lower()

                if fund_name_key not in existing_assets:
                    # Create initial transaction with 1 unit
                    initial_transaction = TransactionHistory(
                        asset_name=fund.name,
                        symbol=fund.symbol,
                        transaction_date=datetime.now(),
                        transaction_type="INITIAL",
                        units_purchased=1.0,
                        price_per_unit=fund.current_price if fund.current_price > 0 else fund.unit_price,
                        total_amount=fund.current_price if fund.current_price > 0 else fund.unit_price,
                        previous_units=0.0,
                        new_units=1.0,
                        notes=f"Initial entry for {fund.name}"
                    )

                    self.transaction_history.append(initial_transaction)
                    changes_made = True

                    # Update the fund's units to 1 if it's currently 0
                    if fund.units == 0:
                        fund.units = 1.0
                        fund.amount = fund.current_price if fund.current_price > 0 else fund.unit_price
                        fund.current_amount = fund.current_price if fund.current_price > 0 else fund.unit_price

                        self.logger.info(f"Initialized {fund.name} with 1 unit")

            # Save changes if any were made
            if changes_made:
                self.csv_manager.save_data('transaction_history', self.transaction_history)
                self.csv_manager.save_data('mutual_funds_stocks', self.mutual_funds_stocks)
                self.logger.info(f"Initialized transaction history with {len([f for f in self.mutual_funds_stocks if f.name.strip().lower() not in existing_assets])} new entries")

        except Exception as e:
            self.logger.error(f"Error initializing transaction history: {e}")

    def create_daily_portfolio_snapshot(self):
        """Create a daily portfolio snapshot if one doesn't exist for today"""
        try:
            if not hasattr(self, 'mutual_funds_stocks') or not self.mutual_funds_stocks:
                return

            # Check if any funds have units > 0
            has_investments = any(fund.units > 0 for fund in self.mutual_funds_stocks)
            if not has_investments:
                return

            # Create snapshot (will check internally if one already exists for today)
            snapshot_created = self.create_portfolio_growth_snapshot(force_create=False)

            # Also ensure individual investment growth records exist
            if not hasattr(self, 'individual_investment_growth') or not self.individual_investment_growth:
                self.logger.info("No individual investment growth data found, creating initial records...")
                self.create_individual_investment_growth_records()

            if snapshot_created:
                self.logger.info("Created daily portfolio growth snapshot")

        except Exception as e:
            self.logger.error(f"Error creating daily portfolio snapshot: {e}")

    def initialize_default_allocation_settings(self):
        """Initialize default allocation settings if none exist"""
        # Define the default allocation settings as specified
        # Note: Using "All" as sub_category since we group by Category + Geographic Classification only
        default_settings = [
            {"category": "Equity", "sub_category": "All", "geographic_classification": "Indian", "allocation_percent": 46.0},
            {"category": "Equity", "sub_category": "All", "geographic_classification": "International", "allocation_percent": 20.0},
            {"category": "Gold", "sub_category": "All", "geographic_classification": "Indian", "allocation_percent": 6.0},
            {"category": "Debt", "sub_category": "All", "geographic_classification": "Indian", "allocation_percent": 16.0},
            {"category": "Crypto", "sub_category": "All", "geographic_classification": "Indian", "allocation_percent": 4.0},
            {"category": "Cash", "sub_category": "All", "geographic_classification": "Indian", "allocation_percent": 8.0}
        ]

        # Check if we need to initialize or update allocation settings
        needs_update = False

        if not self.allocation_settings:
            needs_update = True
            self.logger.info("Initializing default allocation settings...")
        else:
            # Check if current settings match the expected default settings
            expected_keys = {(s["category"], s["geographic_classification"]) for s in default_settings}
            current_keys = {(s.category, s.geographic_classification) for s in self.allocation_settings}

            if expected_keys != current_keys:
                needs_update = True
                self.logger.info("Updating allocation settings to match new configuration...")

        if needs_update:
            # Clear existing settings and add new ones
            self.allocation_settings = []

            for setting_data in default_settings:
                setting = AllocationSettings(
                    category=setting_data["category"],
                    sub_category=setting_data["sub_category"],
                    geographic_classification=setting_data["geographic_classification"],
                    allocation_percent=setting_data["allocation_percent"]
                )
                self.allocation_settings.append(setting)

            # Save the default settings to CSV
            success = self.csv_manager.save_data('allocation_settings', self.allocation_settings)
            if success:
                self.logger.info("✅ Default allocation settings initialized and saved successfully")
            else:
                self.logger.error("❌ Failed to save default allocation settings")

    # Current Resource tab methods
    def add_current_resource(self):
        """Add new current resource entry"""
        dialog = CurrentResourceDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            resource = dialog.get_resource()
            if not hasattr(self, 'current_resources'):
                self.current_resources = []
            self.current_resources.append(resource)
            # Refresh table (which will recalculate allocations and auto-save)
            self.refresh_current_resource_table()
            self.logger.info(f"Added new current resource: {resource.category}")

    def on_resource_selected(self, row):
        """Handle resource selection"""
        self.edit_resource_btn.setEnabled(True)
        self.delete_resource_btn.setEnabled(True)

    def edit_selected_resource(self):
        """Edit selected resource"""
        selected_resource = self.current_resource_table.get_selected_resource()
        if selected_resource:
            dialog = CurrentResourceDialog(selected_resource, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_resource = dialog.get_resource()
                # Update the resource in the list
                for i, resource in enumerate(self.current_resources):
                    if resource.id == updated_resource.id:
                        self.current_resources[i] = updated_resource
                        break
                # Refresh table (which will recalculate allocations and auto-save)
                self.refresh_current_resource_table()
                self.logger.info(f"Updated current resource: {updated_resource.category}")

    def delete_selected_resource(self):
        """Delete selected resource"""
        selected_resource = self.current_resource_table.get_selected_resource()
        if selected_resource:
            reply = QMessageBox.question(
                self, "Delete Resource",
                f"Are you sure you want to delete the resource '{selected_resource.category}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.current_resources = [r for r in self.current_resources if r.id != selected_resource.id]
                # Refresh table (which will recalculate allocations and auto-save)
                self.refresh_current_resource_table()
                self.edit_resource_btn.setEnabled(False)
                self.delete_resource_btn.setEnabled(False)
                self.logger.info(f"Deleted current resource: {selected_resource.category}")

    def refresh_current_resource_table(self):
        """Refresh the current resource table"""
        if hasattr(self, 'current_resources'):
            # Recalculate allocation percentages before loading
            self.recalculate_allocation_percentages()
            self.current_resource_table.load_resources(self.current_resources)
        else:
            self.current_resources = []
            self.current_resource_table.load_resources([])

    def recalculate_allocation_percentages(self):
        """Recalculate allocation percentages for all current resources"""
        if not hasattr(self, 'current_resources') or not self.current_resources:
            return

        # Calculate total amount in lakhs
        total_amount = sum(resource.amount_lakhs for resource in self.current_resources)

        if total_amount > 0:
            # Calculate allocation percentage for each resource
            total_calculated_percentage = 0.0
            for i, resource in enumerate(self.current_resources):
                if i == len(self.current_resources) - 1:
                    # For the last resource, use remaining percentage to ensure total = 100%
                    resource.allocation_percent = 100.0 - total_calculated_percentage
                else:
                    # Calculate percentage and round to 2 decimal places
                    allocation_percent = (resource.amount_lakhs / total_amount) * 100
                    resource.allocation_percent = round(allocation_percent, 2)
                    total_calculated_percentage += resource.allocation_percent

                # Update last_updated timestamp
                resource.last_updated = datetime.now()

            # Save updated data to CSV
            self.csv_manager.save_data('current_resources', self.current_resources)

            # Log the recalculation
            self.logger.info(f"Recalculated allocation percentages for {len(self.current_resources)} resources. Total amount: ₹{total_amount:.2f} lakhs")
        else:
            # If total amount is 0, set all allocations to 0
            for resource in self.current_resources:
                resource.allocation_percent = 0.0
                resource.last_updated = datetime.now()

    def add_asset_liability(self):
        """Add new asset/liability entry"""
        dialog = AssetLiabilityDialog(categories=self.asset_liability_categories, parent=self)
        if dialog.exec() == QDialog.Accepted:
            item = dialog.get_item()
            # Add new category if it doesn't exist
            if item.category and item.category not in self.asset_liability_categories:
                self.asset_liability_categories.append(item.category)
            # Add to list
            if not hasattr(self, 'asset_liability_items'):
                self.asset_liability_items = []
            self.asset_liability_items.append(item)
            # Auto-save to CSV
            self.csv_manager.save_data('asset_liability', self.asset_liability_items)
            self.refresh_asset_liability_table()
            self.logger.info(f"Added new asset/liability: {item.name}")

    def manage_categories(self):
        """Manage asset/liability categories"""
        dialog = CategoryManagementDialog(self.asset_liability_categories.copy(), parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.asset_liability_categories = dialog.get_categories()

    def on_asset_liability_selected(self, row):
        """Handle asset/liability selection"""
        self.edit_asset_liability_btn.setEnabled(True)
        self.delete_asset_liability_btn.setEnabled(True)

    def edit_selected_asset_liability(self):
        """Edit selected asset/liability"""
        selected_item = self.asset_liability_table.get_selected_item()
        if selected_item:
            dialog = AssetLiabilityDialog(selected_item, self.asset_liability_categories, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_item = dialog.get_item()
                # Update the item in the list
                for i, item in enumerate(self.asset_liability_items):
                    if item.id == updated_item.id:
                        self.asset_liability_items[i] = updated_item
                        break
                # Auto-save to CSV
                self.csv_manager.save_data('asset_liability', self.asset_liability_items)
                self.refresh_asset_liability_table()
                self.logger.info(f"Updated asset/liability: {updated_item.name}")

    def delete_selected_asset_liability(self):
        """Delete selected asset/liability"""
        selected_item = self.asset_liability_table.get_selected_item()
        if selected_item:
            reply = QMessageBox.question(
                self, "Delete Item",
                f"Are you sure you want to delete the item '{selected_item.name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.asset_liability_items = [i for i in self.asset_liability_items if i.id != selected_item.id]
                # Auto-save to CSV
                self.csv_manager.save_data('asset_liability', self.asset_liability_items)
                self.refresh_asset_liability_table()
                self.edit_asset_liability_btn.setEnabled(False)
                self.delete_asset_liability_btn.setEnabled(False)
                self.logger.info(f"Deleted asset/liability: {selected_item.name}")

    def refresh_asset_liability_table(self):
        """Refresh the asset/liability table with allocation settings"""
        if hasattr(self, 'asset_liability_items'):
            # Use the new integrated data loading method with allocation settings
            self.asset_liability_table.load_integrated_data(
                self.asset_liability_items,
                getattr(self, 'loan_details', []),
                getattr(self, 'mutual_funds_stocks', []),
                getattr(self, 'allocation_settings', [])
            )
        else:
            self.asset_liability_items = []
            self.asset_liability_table.load_integrated_data([], [], [], [])

    # Owned Assets Methods
    def add_owned_asset(self):
        """Add new owned asset entry"""
        dialog = OwnedAssetDialog(categories=self.owned_asset_categories, parent=self)
        if dialog.exec() == QDialog.Accepted:
            asset = dialog.get_asset()
            self.owned_assets.append(asset)

            # Auto-save to CSV
            self.csv_manager.save_data('owned_assets', self.owned_assets)
            self.refresh_owned_assets_table()
            self.logger.info(f"Added owned asset: {asset.name}")

    def on_owned_asset_selected(self):
        """Handle owned asset selection"""
        self.edit_owned_asset_btn.setEnabled(True)
        self.delete_owned_asset_btn.setEnabled(True)

    def edit_selected_owned_asset(self):
        """Edit selected owned asset"""
        current_row = self.owned_assets_table.currentRow()
        if current_row >= 0 and current_row < len(self.owned_assets):
            asset = self.owned_assets[current_row]
            dialog = OwnedAssetDialog(asset, self.owned_asset_categories, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_asset = dialog.get_asset()
                self.owned_assets[current_row] = updated_asset

                # Auto-save to CSV
                self.csv_manager.save_data('owned_assets', self.owned_assets)
                self.refresh_owned_assets_table()
                self.logger.info(f"Updated owned asset: {updated_asset.name}")

    def delete_selected_owned_asset(self):
        """Delete selected owned asset"""
        current_row = self.owned_assets_table.currentRow()
        if current_row >= 0 and current_row < len(self.owned_assets):
            asset = self.owned_assets[current_row]
            reply = QMessageBox.question(
                self, "Delete Asset",
                f"Are you sure you want to delete '{asset.name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                del self.owned_assets[current_row]

                # Auto-save to CSV
                self.csv_manager.save_data('owned_assets', self.owned_assets)
                self.refresh_owned_assets_table()
                self.edit_owned_asset_btn.setEnabled(False)
                self.delete_owned_asset_btn.setEnabled(False)
                self.logger.info(f"Deleted owned asset: {asset.name}")

    def refresh_owned_assets_table(self):
        """Refresh the owned assets table"""
        if not hasattr(self, 'owned_assets'):
            self.owned_assets = []

        self.owned_assets_table.setRowCount(len(self.owned_assets))

        total_value = 0.0
        for row, asset in enumerate(self.owned_assets):
            self.owned_assets_table.setItem(row, 0, QTableWidgetItem(asset.name))
            self.owned_assets_table.setItem(row, 1, QTableWidgetItem(asset.category))
            self.owned_assets_table.setItem(row, 2, QTableWidgetItem(asset.sub_category))
            self.owned_assets_table.setItem(row, 3, QTableWidgetItem(f"₹{asset.purchase_value:,.2f}"))
            self.owned_assets_table.setItem(row, 4, QTableWidgetItem(f"₹{asset.current_value:,.2f}"))
            self.owned_assets_table.setItem(row, 5, QTableWidgetItem(asset.location))

            purchase_date_str = asset.purchase_date.strftime("%Y-%m-%d") if asset.purchase_date else ""
            self.owned_assets_table.setItem(row, 6, QTableWidgetItem(purchase_date_str))
            self.owned_assets_table.setItem(row, 7, QTableWidgetItem(asset.notes))

            total_value += asset.current_value

        # Update summary
        self.owned_assets_summary_label.setText(f"Total Assets Value: ₹{total_value:,.2f}")

    def refresh_integrated_portfolio(self):
        """Refresh the integrated portfolio view with loans and investments"""
        try:
            # Ensure all data is loaded
            if not hasattr(self, 'asset_liability_items'):
                self.asset_liability_items = []
            if not hasattr(self, 'loan_details'):
                self.loan_details = []
            if not hasattr(self, 'mutual_funds_stocks'):
                self.mutual_funds_stocks = []

            # Generate integrated asset/liability items from fetched data
            self.generate_integrated_asset_liability_items()

            # Use the main allocation settings
            allocation_settings = getattr(self, 'allocation_settings', [])

            # Load integrated data into the table
            self.asset_liability_table.load_integrated_data(
                self.asset_liability_items,
                self.loan_details,
                self.mutual_funds_stocks,
                allocation_settings
            )

            # Update portfolio summary
            self.update_portfolio_summary()

            self.logger.info("Integrated portfolio refreshed successfully")

        except Exception as e:
            self.logger.error(f"Error refreshing integrated portfolio: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to refresh portfolio: {str(e)}")

    def generate_integrated_asset_liability_items(self):
        """Generate AssetLiability items from fetched loan and investment data and save to CSV"""
        try:
            self.logger.info("Generating integrated asset/liability items from fetched data...")

            # Clear existing asset_liability_items to rebuild from scratch
            self.asset_liability_items = []

            # Calculate total portfolio value for percentage calculations
            total_value = 0.0

            # Add investment values
            for investment in self.mutual_funds_stocks:
                total_value += investment.current_amount

            # Add loan values
            for loan in self.loan_details:
                total_value += loan.outstanding_amount

            # Create AssetLiability entries for investments
            for investment in self.mutual_funds_stocks:
                # Calculate percentage allocation
                percentage = (investment.current_amount / total_value * 100) if total_value > 0 else 0.0

                # Create AssetLiability entry with new structure
                asset_item = AssetLiability(
                    name=investment.name,
                    type="Asset",
                    category=investment.category,
                    sub_category=investment.sub_category,
                    geographic_classification=investment.geographic_classification,
                    amount=investment.current_amount,
                    percentage=percentage
                )
                self.asset_liability_items.append(asset_item)

            # Create AssetLiability entries for loans
            for loan in self.loan_details:
                # Calculate percentage allocation
                percentage = (loan.outstanding_amount / total_value * 100) if total_value > 0 else 0.0

                # Create AssetLiability entry with new structure
                liability_item = AssetLiability(
                    name=loan.loan_name,
                    type="Liability",
                    category="Loan",
                    sub_category="",
                    geographic_classification="",
                    amount=loan.outstanding_amount,
                    percentage=percentage
                )
                self.asset_liability_items.append(liability_item)

            # Save the generated items to CSV
            success = self.csv_manager.save_data('asset_liability', self.asset_liability_items)

            if success:
                self.logger.info(f"✅ Successfully saved {len(self.asset_liability_items)} integrated items to asset_liability.csv")
                self.logger.info(f"   - {len(self.mutual_funds_stocks)} investment assets")
                self.logger.info(f"   - {len(self.loan_details)} loan liabilities")
            else:
                self.logger.warning("⚠️ Failed to save integrated items to CSV")

        except Exception as e:
            self.logger.error(f"Error generating integrated asset/liability items: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def update_portfolio_summary(self):
        """Update the portfolio summary display"""
        try:
            # Calculate totals
            total_assets = 0.0
            total_liabilities = 0.0
            investment_count = 0
            loan_count = 0

            # Count investments
            if hasattr(self, 'mutual_funds_stocks'):
                investment_count = len(self.mutual_funds_stocks)
                total_assets += sum(fund.current_amount for fund in self.mutual_funds_stocks)

            # Count loans
            if hasattr(self, 'loan_details'):
                loan_count = len(self.loan_details)
                total_liabilities += sum(loan.outstanding_amount for loan in self.loan_details)

            # Count other assets
            if hasattr(self, 'asset_liability_items'):
                for item in self.asset_liability_items:
                    if item.category.lower() != "loans":  # Skip loans as they're counted separately
                        if item.type == "Asset":
                            # Other assets don't have amounts in current structure
                            pass
                        else:
                            # Other liabilities
                            pass

            net_worth = total_assets - total_liabilities

            # Update summary label
            summary_text = (f"Assets: ₹{total_assets:,.2f} | "
                          f"Liabilities: ₹{total_liabilities:,.2f} | "
                          f"Net Worth: ₹{net_worth:,.2f} | "
                          f"Investments: {investment_count} | "
                          f"Loans: {loan_count}")

            if hasattr(self, 'portfolio_summary_label'):
                self.portfolio_summary_label.setText(summary_text)

                # Color code net worth
                if net_worth > 0:
                    self.portfolio_summary_label.setStyleSheet("color: green; font-weight: bold;")
                elif net_worth < 0:
                    self.portfolio_summary_label.setStyleSheet("color: red; font-weight: bold;")
                else:
                    self.portfolio_summary_label.setStyleSheet("color: orange; font-weight: bold;")

        except Exception as e:
            self.logger.error(f"Error updating portfolio summary: {str(e)}")

    def export_portfolio_data(self):
        """Export portfolio data to CSV"""
        try:
            from PySide6.QtWidgets import QFileDialog
            import csv
            from datetime import datetime

            # Get save location
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Portfolio Data",
                f"portfolio_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )

            if not filename:
                return

            # Prepare data for export
            export_data = []

            # Add investments
            if hasattr(self, 'mutual_funds_stocks'):
                for investment in self.mutual_funds_stocks:
                    export_data.append({
                        'Name': investment.name,
                        'Type': 'Asset',
                        'Category': investment.category,
                        'Sub-Category': investment.sub_category,
                        'Geographic Classification': investment.geographic_classification,
                        'Amount': investment.current_amount,
                        'Units': investment.units,
                        'Unit Price': investment.unit_price,
                        'Current Price': investment.current_price,
                        'Symbol': investment.symbol,
                        'Remarks': investment.remarks
                    })

            # Add loans
            if hasattr(self, 'loan_details'):
                for loan in self.loan_details:
                    export_data.append({
                        'Name': loan.loan_name,
                        'Type': 'Liability',
                        'Category': 'Loan',
                        'Sub-Category': '',
                        'Geographic Classification': '',
                        'Amount': loan.outstanding_amount,
                        'Units': '',
                        'Unit Price': '',
                        'Current Price': '',
                        'Symbol': '',
                        'Remarks': f"Interest: {loan.interest_rate}%, EMI: ₹{loan.emi_amount}, Remaining: {loan.remaining_period_months} months"
                    })

            # Add other assets/liabilities
            if hasattr(self, 'asset_liability_items'):
                for item in self.asset_liability_items:
                    if item.category.lower() != "loans":  # Skip loans as they're added separately
                        export_data.append({
                            'Name': item.name,
                            'Type': item.type,
                            'Category': item.category,
                            'Sub-Category': '',
                            'Geographic Classification': '',
                            'Amount': 0.0,  # No amount in current structure
                            'Units': '',
                            'Unit Price': '',
                            'Current Price': '',
                            'Symbol': '',
                            'Remarks': f"Allocation: {item.percentage}%"
                        })

            # Write to CSV
            if export_data:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Name', 'Type', 'Category', 'Sub-Category', 'Geographic Classification',
                                'Amount', 'Units', 'Unit Price', 'Current Price', 'Symbol', 'Remarks']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(export_data)

                QMessageBox.information(self, "Export Successful",
                                      f"Portfolio data exported successfully to:\n{filename}")
                self.logger.info(f"Portfolio data exported to: {filename}")
            else:
                QMessageBox.warning(self, "No Data", "No portfolio data available to export.")

        except Exception as e:
            self.logger.error(f"Error exporting portfolio data: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"Failed to export portfolio data:\n{str(e)}")

    def add_goal(self):
        """Add new financial goal"""
        dialog = GoalPlanningDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            goal = dialog.get_goal()
            if not hasattr(self, 'financial_goals'):
                self.financial_goals = []
            self.financial_goals.append(goal)
            # Auto-save to CSV
            self.csv_manager.save_data('financial_goals', self.financial_goals)
            self.refresh_goal_planning_table()
            self.logger.info(f"Added new financial goal: {goal.goal_name}")

    def on_goal_selected(self, row):
        """Handle goal selection"""
        self.edit_goal_btn.setEnabled(True)
        self.delete_goal_btn.setEnabled(True)

    def edit_selected_goal(self):
        """Edit selected goal"""
        selected_goal = self.goal_planning_table.get_selected_goal()
        if selected_goal:
            dialog = GoalPlanningDialog(selected_goal, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_goal = dialog.get_goal()
                for i, goal in enumerate(self.financial_goals):
                    if goal.id == updated_goal.id:
                        self.financial_goals[i] = updated_goal
                        break
                # Auto-save to CSV
                self.csv_manager.save_data('financial_goals', self.financial_goals)
                self.refresh_goal_planning_table()
                self.logger.info(f"Updated financial goal: {updated_goal.goal_name}")

    def delete_selected_goal(self):
        """Delete selected goal"""
        selected_goal = self.goal_planning_table.get_selected_goal()
        if selected_goal:
            reply = QMessageBox.question(
                self, "Delete Goal",
                f"Are you sure you want to delete the goal '{selected_goal.goal_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.financial_goals = [g for g in self.financial_goals if g.id != selected_goal.id]
                # Auto-save to CSV
                self.csv_manager.save_data('financial_goals', self.financial_goals)
                self.refresh_goal_planning_table()
                self.edit_goal_btn.setEnabled(False)
                self.delete_goal_btn.setEnabled(False)
                self.logger.info(f"Deleted financial goal: {selected_goal.goal_name}")

    def refresh_goal_planning_table(self):
        """Refresh the goal planning table"""
        if hasattr(self, 'financial_goals'):
            self.goal_planning_table.load_goals(self.financial_goals)
        else:
            self.financial_goals = []
            self.goal_planning_table.load_goals([])

    def add_policy(self):
        """Add new insurance policy"""
        dialog = InsurancePolicyDialog(policy_types=self.policy_types, parent=self)
        if dialog.exec() == QDialog.Accepted:
            policy = dialog.get_policy()
            if not hasattr(self, 'insurance_policies'):
                self.insurance_policies = []
            self.insurance_policies.append(policy)
            # Auto-save to CSV
            self.csv_manager.save_data('insurance_policies', self.insurance_policies)
            self.refresh_policy_table()
            self.logger.info(f"Added new insurance policy: {policy.policy_name}")

    def on_policy_selected(self):
        """Handle policy selection"""
        current_row = self.policy_table.currentRow()
        if current_row >= 0 and current_row < len(self.insurance_policies):
            self.edit_policy_btn.setEnabled(True)
            self.delete_policy_btn.setEnabled(True)
        else:
            self.edit_policy_btn.setEnabled(False)
            self.delete_policy_btn.setEnabled(False)

    def edit_selected_policy(self):
        """Edit selected policy"""
        current_row = self.policy_table.currentRow()
        if current_row >= 0 and current_row < len(self.insurance_policies):
            selected_policy = self.insurance_policies[current_row]
            dialog = InsurancePolicyDialog(selected_policy, self.policy_types, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_policy = dialog.get_policy()
                self.insurance_policies[current_row] = updated_policy
                # Auto-save to CSV
                self.csv_manager.save_data('insurance_policies', self.insurance_policies)
                self.refresh_policy_table()
                self.logger.info(f"Updated insurance policy: {updated_policy.policy_name}")

    def delete_selected_policy(self):
        """Delete selected policy"""
        current_row = self.policy_table.currentRow()
        if current_row >= 0 and current_row < len(self.insurance_policies):
            selected_policy = self.insurance_policies[current_row]
            reply = QMessageBox.question(
                self, "Delete Policy",
                f"Are you sure you want to delete the policy '{selected_policy.policy_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.insurance_policies.pop(current_row)
                # Auto-save to CSV
                self.csv_manager.save_data('insurance_policies', self.insurance_policies)
                self.refresh_policy_table()
                self.edit_policy_btn.setEnabled(False)
                self.delete_policy_btn.setEnabled(False)
                self.logger.info(f"Deleted insurance policy: {selected_policy.policy_name}")

    def manage_policy_types(self):
        """Manage policy types"""
        dialog = CategoryManagementDialog(self.policy_types.copy(), parent=self)
        dialog.setWindowTitle("Manage Policy Types")
        if dialog.exec() == QDialog.Accepted:
            self.policy_types = dialog.get_categories()

    def filter_policies(self):
        """Filter policies based on type, status, and search criteria"""
        if not hasattr(self, 'insurance_policies') or not hasattr(self, 'policy_table'):
            return

        type_filter = self.policy_type_filter.currentText()
        status_filter = self.policy_status_filter.currentText()
        search_text = self.policy_search_box.text().lower().strip()

        # Show all rows initially
        for row in range(self.policy_table.rowCount()):
            self.policy_table.setRowHidden(row, False)

        # Apply filters
        for row in range(self.policy_table.rowCount()):
            if row >= len(self.insurance_policies):
                continue

            policy = self.insurance_policies[row]
            hide_row = False

            # Type filter
            if type_filter != "All Types" and policy.policy_type != type_filter:
                hide_row = True

            # Status filter
            if status_filter != "All Status" and policy.current_status != status_filter:
                hide_row = True

            # Search filter
            if search_text:
                searchable_text = f"{policy.policy_name} {policy.insurance_provider} {policy.policy_number}".lower()
                if search_text not in searchable_text:
                    hide_row = True

            self.policy_table.setRowHidden(row, hide_row)

    def clear_policy_filters(self):
        """Clear all policy filters"""
        self.policy_type_filter.setCurrentText("All Types")
        self.policy_status_filter.setCurrentText("All Status")
        self.policy_search_box.clear()
        # Show all rows
        for row in range(self.policy_table.rowCount()):
            self.policy_table.setRowHidden(row, False)

    # LIC Policy Management Functions
    def add_lic_policy(self):
        """Add new LIC policy"""
        # Get unique family members from existing LIC policies
        family_members = list(set([policy.policy_holder_name for policy in self.lic_policies if policy.policy_holder_name]))

        dialog = LICPolicyDialog(policy_types=self.lic_policy_types, family_members=family_members, parent=self)
        if dialog.exec() == QDialog.Accepted:
            policy = dialog.get_policy()
            if not hasattr(self, 'lic_policies'):
                self.lic_policies = []
            self.lic_policies.append(policy)
            # Auto-save to CSV
            self.csv_manager.save_data('lic_policies', self.lic_policies)
            self.refresh_lic_policy_table()
            self.update_lic_family_filter()
            self.logger.info(f"Added new LIC policy: {policy.policy_number} for {policy.policy_holder_name}")

    def on_lic_policy_selected(self):
        """Handle LIC policy selection"""
        current_row = self.lic_policy_table.currentRow()
        if current_row >= 0 and current_row < len(self.lic_policies):
            self.edit_lic_policy_btn.setEnabled(True)
            self.delete_lic_policy_btn.setEnabled(True)
        else:
            self.edit_lic_policy_btn.setEnabled(False)
            self.delete_lic_policy_btn.setEnabled(False)

    def edit_selected_lic_policy(self):
        """Edit selected LIC policy"""
        current_row = self.lic_policy_table.currentRow()
        if current_row >= 0 and current_row < len(self.lic_policies):
            selected_policy = self.lic_policies[current_row]
            # Get unique family members from existing LIC policies
            family_members = list(set([policy.policy_holder_name for policy in self.lic_policies if policy.policy_holder_name]))

            dialog = LICPolicyDialog(selected_policy, self.lic_policy_types, family_members, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_policy = dialog.get_policy()
                self.lic_policies[current_row] = updated_policy
                # Auto-save to CSV
                self.csv_manager.save_data('lic_policies', self.lic_policies)
                self.refresh_lic_policy_table()
                self.update_lic_family_filter()
                self.logger.info(f"Updated LIC policy: {updated_policy.policy_number} for {updated_policy.policy_holder_name}")

    def delete_selected_lic_policy(self):
        """Delete selected LIC policy"""
        current_row = self.lic_policy_table.currentRow()
        if current_row >= 0 and current_row < len(self.lic_policies):
            selected_policy = self.lic_policies[current_row]
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete the LIC policy {selected_policy.policy_number} for {selected_policy.policy_holder_name}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.lic_policies.pop(current_row)
                # Auto-save to CSV
                self.csv_manager.save_data('lic_policies', self.lic_policies)
                self.refresh_lic_policy_table()
                self.update_lic_family_filter()
                self.edit_lic_policy_btn.setEnabled(False)
                self.delete_lic_policy_btn.setEnabled(False)
                self.logger.info(f"Deleted LIC policy: {selected_policy.policy_number} for {selected_policy.policy_holder_name}")

    def filter_lic_policies(self):
        """Filter LIC policies based on family member, type, status, and search criteria"""
        if not hasattr(self, 'lic_policies') or not hasattr(self, 'lic_policy_table'):
            return

        family_filter = self.lic_family_filter.currentText()
        type_filter = self.lic_type_filter.currentText()
        status_filter = self.lic_status_filter.currentText()
        search_text = self.lic_search_box.text().lower().strip()

        # Show all rows initially
        for row in range(self.lic_policy_table.rowCount()):
            self.lic_policy_table.setRowHidden(row, False)

        # Apply filters
        for row in range(self.lic_policy_table.rowCount()):
            if row >= len(self.lic_policies):
                continue

            policy = self.lic_policies[row]
            hide_row = False

            # Family member filter
            if family_filter != "All Family Members" and policy.policy_holder_name != family_filter:
                hide_row = True

            # Type filter
            if type_filter != "All Types" and policy.policy_type != type_filter:
                hide_row = True

            # Status filter
            if status_filter != "All Status" and policy.current_status != status_filter:
                hide_row = True

            # Search filter
            if search_text:
                searchable_text = f"{policy.policy_holder_name} {policy.policy_number} {policy.plan_name} {policy.agent_name}".lower()
                if search_text not in searchable_text:
                    hide_row = True

            self.lic_policy_table.setRowHidden(row, hide_row)

    def clear_lic_filters(self):
        """Clear all LIC policy filters"""
        self.lic_family_filter.setCurrentText("All Family Members")
        self.lic_type_filter.setCurrentText("All Types")
        self.lic_status_filter.setCurrentText("All Status")
        self.lic_search_box.clear()
        # Show all rows
        for row in range(self.lic_policy_table.rowCount()):
            self.lic_policy_table.setRowHidden(row, False)

    def update_lic_family_filter(self):
        """Update the family member filter dropdown with unique family members"""
        if hasattr(self, 'lic_family_filter') and hasattr(self, 'lic_policies'):
            current_selection = self.lic_family_filter.currentText()
            self.lic_family_filter.clear()
            self.lic_family_filter.addItem("All Family Members")

            # Get unique family members
            family_members = list(set([policy.policy_holder_name for policy in self.lic_policies if policy.policy_holder_name]))
            family_members.sort()
            self.lic_family_filter.addItems(family_members)

            # Restore previous selection if it still exists
            if current_selection in [self.lic_family_filter.itemText(i) for i in range(self.lic_family_filter.count())]:
                self.lic_family_filter.setCurrentText(current_selection)

    def open_benefit_calculator(self, item):
        """Open the LIC Benefit Calculator dialog for the selected policy"""
        if not hasattr(self, 'lic_policies') or not hasattr(self, 'lic_policy_table'):
            return

        current_row = item.row()
        if current_row >= 0 and current_row < len(self.lic_policies):
            selected_policy = self.lic_policies[current_row]

            try:
                # Open the benefit calculator dialog
                calculator_dialog = LICBenefitCalculatorDialog(selected_policy, parent=self)
                calculator_dialog.exec()
                self.logger.info(f"Opened benefit calculator for LIC policy: {selected_policy.policy_number}")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to open benefit calculator: {str(e)}"
                )
                self.logger.error(f"Error opening benefit calculator: {e}")

    def add_loan(self):
        """Add new loan entry"""
        dialog = LoanDetailsDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            loan = dialog.get_loan()
            if not hasattr(self, 'loan_details'):
                self.loan_details = []
            self.loan_details.append(loan)
            # Auto-save to CSV
            self.csv_manager.save_data('loan_details', self.loan_details)
            self.refresh_loan_table()
            self.logger.info(f"Added new loan: {loan.loan_name}")

    def on_loan_selected(self):
        """Handle loan selection"""
        current_row = self.loan_table.currentRow()
        if current_row >= 0 and current_row < len(self.loan_details):
            self.edit_loan_btn.setEnabled(True)
            self.delete_loan_btn.setEnabled(True)
        else:
            self.edit_loan_btn.setEnabled(False)
            self.delete_loan_btn.setEnabled(False)

    def edit_selected_loan(self):
        """Edit selected loan"""
        current_row = self.loan_table.currentRow()
        if current_row >= 0 and current_row < len(self.loan_details):
            selected_loan = self.loan_details[current_row]
            dialog = LoanDetailsDialog(selected_loan, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_loan = dialog.get_loan()
                self.loan_details[current_row] = updated_loan
                # Auto-save to CSV
                self.csv_manager.save_data('loan_details', self.loan_details)
                self.refresh_loan_table()
                self.logger.info(f"Updated loan: {updated_loan.loan_name}")

    def delete_selected_loan(self):
        """Delete selected loan"""
        current_row = self.loan_table.currentRow()
        if current_row >= 0 and current_row < len(self.loan_details):
            selected_loan = self.loan_details[current_row]
            reply = QMessageBox.question(
                self, "Delete Loan",
                f"Are you sure you want to delete the loan '{selected_loan.loan_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.loan_details.pop(current_row)
                # Auto-save to CSV
                self.csv_manager.save_data('loan_details', self.loan_details)
                self.refresh_loan_table()
                self.edit_loan_btn.setEnabled(False)
                self.delete_loan_btn.setEnabled(False)
                self.logger.info(f"Deleted loan: {selected_loan.loan_name}")

    def open_loan_payment_history(self, item):
        """Open payment history dialog for the selected loan (double-click handler)"""
        row = item.row()
        if row >= 0 and row < len(self.loan_details):
            selected_loan = self.loan_details[row]
            try:
                dialog = LoanPaymentHistoryDialog(selected_loan, self.csv_manager, parent=self)
                dialog.exec()

                # Refresh the loan table in case the current balance was updated
                self.refresh_loan_table()

                self.logger.info(f"Opened payment history for loan: {selected_loan.loan_name}")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to open payment history: {str(e)}"
                )
                self.logger.error(f"Error opening payment history: {e}")

    def calculate_loan_current_balance(self, loan):
        """Calculate current loan balance based on payment history"""
        try:
            # Load payment history for this loan
            all_payments = self.csv_manager.load_data('loan_payment_history', LoanPayment)
            loan_payments = [p for p in all_payments if p.loan_id == loan.id]

            if not loan_payments:
                # No payments made, return original outstanding amount
                return loan.outstanding_amount

            # Sort payments by date (most recent first)
            loan_payments.sort(key=lambda x: x.payment_date if x.payment_date else date.min, reverse=True)

            # Return the remaining balance from the most recent payment
            return loan_payments[0].remaining_balance

        except Exception as e:
            self.logger.error(f"Error calculating current balance for loan {loan.loan_name}: {e}")
            # Fallback to original outstanding amount
            return loan.outstanding_amount

    def add_mutual_fund(self):
        """Add new mutual fund/stock entry with automatic transaction tracking"""
        dialog = MutualFundStockDialog(categories=self.fund_categories, subcategories=self.fund_subcategories, parent=self)
        if dialog.exec() == QDialog.Accepted:
            fund = dialog.get_fund()

            # Create transaction record for new addition if units > 0
            if fund.units > 0:
                transaction = TransactionHistory(
                    asset_name=fund.name,
                    symbol=fund.symbol,
                    transaction_date=datetime.now(),
                    units_purchased=fund.units,
                    price_per_unit=fund.unit_price,
                    total_amount=fund.units * fund.unit_price,
                    transaction_type="BUY",
                    previous_units=0.0,
                    new_units=fund.units,
                    notes=f"Initial purchase of {fund.name}"
                )

                # Add to transaction history
                if not hasattr(self, 'transaction_history'):
                    self.transaction_history = []
                self.transaction_history.append(transaction)

                # Save transaction history to CSV
                self.csv_manager.save_data('transaction_history', self.transaction_history)

            # Add new categories if they don't exist
            if fund.category and fund.category not in self.fund_categories:
                self.fund_categories.append(fund.category)
                self.save_categories_to_csv()  # Save new category
            if fund.sub_category and fund.sub_category not in self.fund_subcategories:
                self.fund_subcategories.append(fund.sub_category)
                self.save_categories_to_csv()  # Save new subcategory

            # Add to list
            if not hasattr(self, 'mutual_funds_stocks'):
                self.mutual_funds_stocks = []
            self.mutual_funds_stocks.append(fund)

            # Auto-save to CSV
            self.csv_manager.save_data('mutual_funds_stocks', self.mutual_funds_stocks)
            self.refresh_mutual_funds_table()

            # Create portfolio growth snapshot if units > 0
            if fund.units > 0:
                self.create_portfolio_growth_snapshot()

            # Refresh Portfolio Analysis to reflect new addition
            self.refresh_portfolio_analysis()

            self.logger.info(f"Added new mutual fund/stock: {fund.name}")

    def on_mutual_fund_selected(self):
        """Handle mutual fund selection"""
        current_row = self.mutual_funds_table.currentRow()
        if current_row >= 0 and current_row < len(self.mutual_funds_stocks):
            self.edit_fund_btn.setEnabled(True)
            self.delete_fund_btn.setEnabled(True)
        else:
            self.edit_fund_btn.setEnabled(False)
            self.delete_fund_btn.setEnabled(False)

    def on_mutual_fund_double_clicked(self, item):
        """Handle double-click on mutual fund/stock row to show detailed information"""
        if not item:
            return

        row = item.row()
        if row >= 0 and row < len(self.mutual_funds_stocks):
            selected_fund = self.mutual_funds_stocks[row]

            # Open investment details dialog
            try:
                dialog = InvestmentDetailsDialog(selected_fund, parent=self)
                dialog.exec()
            except Exception as e:
                self.logger.error(f"Error opening investment details dialog: {e}")
                QMessageBox.warning(
                    self, "Error",
                    f"Could not open investment details: {str(e)}"
                )

    def edit_selected_mutual_fund(self):
        """Edit selected mutual fund/stock with automatic transaction tracking"""
        current_row = self.mutual_funds_table.currentRow()
        if current_row >= 0 and current_row < len(self.mutual_funds_stocks):
            selected_fund = self.mutual_funds_stocks[current_row]
            original_units = selected_fund.units  # Store original units for transaction tracking

            dialog = MutualFundStockDialog(selected_fund, self.fund_categories, self.fund_subcategories, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_fund = dialog.get_fund()

                # Check if units have changed to create transaction history
                if updated_fund.units != original_units:
                    self.create_transaction_record(selected_fund, updated_fund, original_units)

                # Add new categories if they don't exist
                if updated_fund.category and updated_fund.category not in self.fund_categories:
                    self.fund_categories.append(updated_fund.category)
                    self.save_categories_to_csv()  # Save new category
                if updated_fund.sub_category and updated_fund.sub_category not in self.fund_subcategories:
                    self.fund_subcategories.append(updated_fund.sub_category)
                    self.save_categories_to_csv()  # Save new subcategory

                self.mutual_funds_stocks[current_row] = updated_fund

                # Auto-save to CSV
                self.csv_manager.save_data('mutual_funds_stocks', self.mutual_funds_stocks)
                self.refresh_mutual_funds_table()

                # Refresh Purchase History tab to show new transaction
                self.refresh_purchase_history_table()

                # Automatically create portfolio growth snapshot if units changed
                if updated_fund.units != original_units:
                    self.create_portfolio_growth_snapshot()

                # Refresh Portfolio Analysis to reflect changes
                self.refresh_portfolio_analysis()

                self.logger.info(f"Updated mutual fund/stock: {updated_fund.name}")

    def create_transaction_record(self, original_fund, updated_fund, original_units):
        """Create a transaction history record when units are changed"""
        try:
            units_difference = updated_fund.units - original_units
            transaction_type = "BUY" if units_difference > 0 else "SELL" if units_difference < 0 else "UPDATE"

            # Create transaction record
            transaction = TransactionHistory(
                asset_name=updated_fund.name,
                symbol=updated_fund.symbol,
                transaction_date=datetime.now(),
                units_purchased=abs(units_difference),
                price_per_unit=updated_fund.unit_price,
                total_amount=abs(units_difference) * updated_fund.unit_price,
                transaction_type=transaction_type,
                previous_units=original_units,
                new_units=updated_fund.units,
                notes=f"Units updated from {original_units} to {updated_fund.units}"
            )

            # Add to transaction history
            if not hasattr(self, 'transaction_history'):
                self.transaction_history = []
            self.transaction_history.append(transaction)

            # Save to CSV
            self.csv_manager.save_data('transaction_history', self.transaction_history)

            # Also create a purchase history record for the Purchase History tab
            self.create_purchase_history_record(updated_fund, units_difference, transaction_type)

            self.logger.info(f"Created transaction record: {transaction_type} {abs(units_difference)} units of {updated_fund.name}")

        except Exception as e:
            self.logger.error(f"Error creating transaction record: {e}")

    def create_purchase_history_record(self, fund, units_difference, transaction_type):
        """Create a purchase history record for the Purchase History tab"""
        try:
            # Calculate transaction details
            unit_price = fund.current_price if fund.current_price > 0 else fund.unit_price
            total_amount = abs(units_difference) * unit_price
            fees = 0.0  # Default fees to 0, can be updated manually later
            net_amount = total_amount + fees if transaction_type == "BUY" else total_amount - fees

            # Create purchase history record
            purchase_record = MutualFundPurchaseHistory(
                fund_id=fund.id,
                transaction_type=transaction_type,
                transaction_date=datetime.now(),
                units=abs(units_difference),
                unit_price=unit_price,
                total_amount=total_amount,
                fees=fees,
                net_amount=net_amount,
                notes=f"Auto-generated from units update: {transaction_type} {abs(units_difference)} units"
            )

            # Add to purchase history
            if not hasattr(self, 'mutual_fund_purchase_history'):
                self.mutual_fund_purchase_history = []
            self.mutual_fund_purchase_history.append(purchase_record)

            # Save to CSV
            self.csv_manager.save_data('mutual_fund_purchase_history', self.mutual_fund_purchase_history)

            self.logger.info(f"Created purchase history record: {transaction_type} {abs(units_difference)} units of {fund.name}")

        except Exception as e:
            self.logger.error(f"Error creating purchase history record: {e}")

    def create_portfolio_growth_snapshot(self, force_create=False):
        """Create a portfolio growth snapshot with current portfolio state"""
        try:
            # Calculate current portfolio metrics based on transaction history
            total_portfolio_value = 0.0
            total_invested = 0.0
            asset_count = 0

            # Calculate values based on current units and prices
            for fund in self.mutual_funds_stocks:
                if fund.units > 0:
                    current_value = fund.current_amount if fund.current_amount > 0 else (fund.units * fund.current_price)
                    invested_value = fund.units * fund.unit_price if fund.unit_price > 0 else fund.amount

                    total_portfolio_value += current_value
                    total_invested += invested_value
                    asset_count += 1

            total_gains = total_portfolio_value - total_invested
            gains_percentage = (total_gains / total_invested * 100) if total_invested > 0 else 0.0

            # Check if we should create a new snapshot (avoid duplicates on same day unless forced)
            today = datetime.now().date()
            should_create = force_create

            if not should_create and hasattr(self, 'portfolio_growth_snapshots') and self.portfolio_growth_snapshots:
                # Check if we already have a snapshot for today
                today_snapshots = [s for s in self.portfolio_growth_snapshots if s.snapshot_date.date() == today]
                should_create = len(today_snapshots) == 0
            else:
                should_create = True

            if should_create:
                # Create growth snapshot (keep for backward compatibility)
                growth_snapshot = PortfolioGrowthSnapshot(
                    snapshot_date=datetime.now(),
                    total_portfolio_value=total_portfolio_value,
                    total_invested=total_invested,
                    total_gains=total_gains,
                    gains_percentage=gains_percentage,
                    asset_count=asset_count,
                    notes=f"Daily snapshot - Portfolio value: ₹{total_portfolio_value:,.2f}"
                )

                # Add to growth snapshots
                if not hasattr(self, 'portfolio_growth_snapshots'):
                    self.portfolio_growth_snapshots = []
                self.portfolio_growth_snapshots.append(growth_snapshot)

                # Save to CSV
                self.csv_manager.save_data('portfolio_growth_snapshots', self.portfolio_growth_snapshots)

                # Create individual investment growth records
                self.create_individual_investment_growth_records()

                self.logger.info(f"Created portfolio growth snapshot: ₹{total_portfolio_value:,.2f} total value, ₹{total_gains:+,.2f} gains ({gains_percentage:+.2f}%)")
                return True
            else:
                self.logger.debug(f"Skipped creating duplicate snapshot for today")
                return False

        except Exception as e:
            self.logger.error(f"Error creating portfolio growth snapshot: {e}")
            return False

    def create_individual_investment_growth_records(self):
        """Create individual investment growth records for each fund/stock"""
        try:
            self.logger.info("Starting create_individual_investment_growth_records...")

            if not hasattr(self, 'mutual_funds_stocks') or not self.mutual_funds_stocks:
                self.logger.warning("No mutual_funds_stocks data available")
                return

            self.logger.info(f"Found {len(self.mutual_funds_stocks)} mutual funds/stocks")

            # Initialize individual investment growth list if it doesn't exist
            if not hasattr(self, 'individual_investment_growth'):
                self.individual_investment_growth = []

            snapshot_date = datetime.now()
            records_created = 0

            # Create growth record for each investment with units > 0
            for fund in self.mutual_funds_stocks:
                self.logger.debug(f"Processing fund: {fund.name}, units: {fund.units}")
                if fund.units > 0:
                    current_value = fund.current_amount if fund.current_amount > 0 else (fund.units * fund.current_price)
                    invested_amount = fund.units * fund.unit_price if fund.unit_price > 0 else fund.amount

                    self.logger.debug(f"Creating growth record for {fund.name}: current_value={current_value}, invested_amount={invested_amount}")

                    # Generate unique ID for each record
                    unique_id = int(datetime.now().timestamp() * 1000000) + records_created

                    growth_record = IndividualInvestmentGrowth(
                        id=unique_id,
                        snapshot_date=snapshot_date,
                        investment_name=fund.name,
                        investment_symbol=fund.symbol,
                        units=fund.units,
                        unit_price=fund.current_price if fund.current_price > 0 else fund.unit_price,
                        current_value=current_value,
                        invested_amount=invested_amount,
                        notes=f"Growth snapshot for {fund.name}"
                    )

                    self.individual_investment_growth.append(growth_record)
                    records_created += 1

            self.logger.info(f"Created {records_created} individual investment growth records")

            # Save to CSV
            if records_created > 0:
                save_result = self.csv_manager.save_data('individual_investment_growth', self.individual_investment_growth)
                self.logger.info(f"Save result: {save_result}")
            else:
                self.logger.warning("No records to save")

            self.logger.info(f"Completed creating individual investment growth records for {records_created} investments")

        except Exception as e:
            self.logger.error(f"Error creating individual investment growth records: {e}")

    def force_create_individual_growth_records(self):
        """Force creation of individual investment growth records"""
        try:
            self.logger.info("Force creating individual investment growth records...")

            # Check if we have mutual funds data
            if not hasattr(self, 'mutual_funds_stocks') or not self.mutual_funds_stocks:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "No Data",
                                  "No mutual funds/stocks data found. Please add some investments first.")
                return

            # Check if any investments have units > 0
            investments_with_units = [f for f in self.mutual_funds_stocks if f.units > 0]
            if not investments_with_units:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "No Investments",
                                  "No investments with units > 0 found. Please add some investment units first.")
                return

            self.logger.info(f"Found {len(investments_with_units)} investments with units > 0")

            # Create records for current state
            self.create_individual_investment_growth_records()

            # Check if records were actually created
            if hasattr(self, 'individual_investment_growth') and self.individual_investment_growth:
                self.logger.info(f"Created {len(self.individual_investment_growth)} individual investment growth records")

                # Refresh the display
                self.refresh_portfolio_growth_table()
                self.refresh_portfolio_growth_chart()

                # Show success message
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success",
                                      f"Successfully created {len(self.individual_investment_growth)} individual investment growth records!")
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Creation Failed",
                                  "Failed to create individual investment growth records. Check the logs for details.")

        except Exception as e:
            self.logger.error(f"Error force creating individual growth records: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error",
                               f"Failed to create growth records: {str(e)}")

    def delete_selected_mutual_fund(self):
        """Delete selected mutual fund/stock"""
        current_row = self.mutual_funds_table.currentRow()
        if current_row >= 0 and current_row < len(self.mutual_funds_stocks):
            selected_fund = self.mutual_funds_stocks[current_row]
            reply = QMessageBox.question(
                self, "Delete Fund/Stock",
                f"Are you sure you want to delete '{selected_fund.name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.mutual_funds_stocks.pop(current_row)
                # Auto-save to CSV
                self.csv_manager.save_data('mutual_funds_stocks', self.mutual_funds_stocks)
                self.refresh_mutual_funds_table()
                self.edit_fund_btn.setEnabled(False)
                self.delete_fund_btn.setEnabled(False)
                self.logger.info(f"Deleted mutual fund/stock: {selected_fund.name}")

    def save_categories_to_csv(self):
        """Save categories and subcategories to CSV for persistence"""
        try:
            categories_data = []

            # Save categories
            for category in self.fund_categories:
                categories_data.append({
                    'type': 'category',
                    'name': category,
                    'created_date': datetime.now().isoformat()
                })

            # Save subcategories
            for subcategory in self.fund_subcategories:
                categories_data.append({
                    'type': 'subcategory',
                    'name': subcategory,
                    'created_date': datetime.now().isoformat()
                })

            # Save to CSV
            self.csv_manager.save_data('fund_categories', categories_data)
            self.logger.info(f"Saved {len(self.fund_categories)} categories and {len(self.fund_subcategories)} subcategories")

        except Exception as e:
            self.logger.error(f"Error saving categories: {e}")

    def load_categories_from_csv(self):
        """Load categories and subcategories from CSV"""
        try:
            categories_data = self.csv_manager.load_data('fund_categories', dict)

            loaded_categories = []
            loaded_subcategories = []

            for item in categories_data:
                if isinstance(item, dict):
                    if item.get('type') == 'category':
                        loaded_categories.append(item.get('name', ''))
                    elif item.get('type') == 'subcategory':
                        loaded_subcategories.append(item.get('name', ''))

            # Update categories if loaded successfully
            if loaded_categories:
                self.fund_categories = loaded_categories
            if loaded_subcategories:
                self.fund_subcategories = loaded_subcategories

            self.logger.info(f"Loaded {len(loaded_categories)} categories and {len(loaded_subcategories)} subcategories")

        except Exception as e:
            self.logger.warning(f"Could not load categories from CSV, using defaults: {e}")

    def manage_fund_categories(self):
        """Manage fund categories"""
        dialog = CategoryManagementDialog(self.fund_categories.copy(), parent=self)
        dialog.setWindowTitle("Manage Fund Categories")
        if dialog.exec() == QDialog.Accepted:
            self.fund_categories = dialog.get_categories()
            # Save updated categories persistently
            self.save_categories_to_csv()
            self.logger.info(f"Updated fund categories: {self.fund_categories}")

    def manage_fund_subcategories(self):
        """Manage fund sub-categories"""
        dialog = CategoryManagementDialog(self.fund_subcategories.copy(), parent=self)
        dialog.setWindowTitle("Manage Fund Sub-Categories")
        if dialog.exec() == QDialog.Accepted:
            self.fund_subcategories = dialog.get_categories()
            # Save updated subcategories persistently
            self.save_categories_to_csv()
            self.logger.info(f"Updated fund subcategories: {self.fund_subcategories}")

    # Purchase History methods
    def add_purchase_transaction(self):
        """Add new purchase transaction"""
        dialog = PurchaseTransactionDialog(mutual_funds=self.mutual_funds_stocks, parent=self)
        if dialog.exec() == QDialog.Accepted:
            transaction = dialog.get_transaction()
            if not hasattr(self, 'mutual_fund_purchase_history'):
                self.mutual_fund_purchase_history = []
            self.mutual_fund_purchase_history.append(transaction)
            # Auto-save to CSV
            self.csv_manager.save_data('mutual_fund_purchase_history', self.mutual_fund_purchase_history)
            self.refresh_purchase_history_table()
            self.logger.info(f"Added new purchase transaction for fund ID: {transaction.fund_id}")

    def on_purchase_history_selected(self):
        """Handle purchase history selection"""
        current_row = self.purchase_history_table.currentRow()
        if current_row >= 0 and current_row < len(self.mutual_fund_purchase_history):
            self.edit_transaction_btn.setEnabled(True)
            self.delete_transaction_btn.setEnabled(True)
        else:
            self.edit_transaction_btn.setEnabled(False)
            self.delete_transaction_btn.setEnabled(False)

    def edit_selected_transaction(self):
        """Edit selected purchase transaction"""
        current_row = self.purchase_history_table.currentRow()
        if current_row >= 0 and current_row < len(self.mutual_fund_purchase_history):
            selected_transaction = self.mutual_fund_purchase_history[current_row]
            dialog = PurchaseTransactionDialog(transaction=selected_transaction, mutual_funds=self.mutual_funds_stocks, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_transaction = dialog.get_transaction()
                self.mutual_fund_purchase_history[current_row] = updated_transaction
                # Auto-save to CSV
                self.csv_manager.save_data('mutual_fund_purchase_history', self.mutual_fund_purchase_history)
                self.refresh_purchase_history_table()
                self.logger.info(f"Updated purchase transaction for fund ID: {updated_transaction.fund_id}")

    def delete_selected_transaction(self):
        """Delete selected purchase transaction"""
        current_row = self.purchase_history_table.currentRow()
        if current_row >= 0 and current_row < len(self.mutual_fund_purchase_history):
            selected_transaction = self.mutual_fund_purchase_history[current_row]
            reply = QMessageBox.question(
                self, "Delete Transaction",
                f"Are you sure you want to delete this transaction?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.mutual_fund_purchase_history.pop(current_row)
                # Auto-save to CSV
                self.csv_manager.save_data('mutual_fund_purchase_history', self.mutual_fund_purchase_history)
                self.refresh_purchase_history_table()
                self.edit_transaction_btn.setEnabled(False)
                self.delete_transaction_btn.setEnabled(False)
                self.logger.info(f"Deleted purchase transaction")



    # Additional refresh methods for CSV data persistence
    def refresh_policy_table(self):
        """Refresh the enhanced policy table with comprehensive data"""
        if hasattr(self, 'insurance_policies') and hasattr(self, 'policy_table'):
            self.policy_table.setRowCount(len(self.insurance_policies))
            for row, policy in enumerate(self.insurance_policies):
                # Column 0: Policy Name
                self.policy_table.setItem(row, 0, QTableWidgetItem(policy.policy_name))

                # Column 1: Provider
                self.policy_table.setItem(row, 1, QTableWidgetItem(policy.insurance_provider))

                # Column 2: Type
                self.policy_table.setItem(row, 2, QTableWidgetItem(policy.policy_type))

                # Column 3: Policy Number
                self.policy_table.setItem(row, 3, QTableWidgetItem(policy.policy_number))

                # Column 4: Coverage Type
                self.policy_table.setItem(row, 4, QTableWidgetItem(policy.coverage_type))

                # Column 5: Coverage Amount
                coverage_amount = f"₹{policy.coverage_amount:,.0f}" if policy.coverage_amount > 0 else "-"
                self.policy_table.setItem(row, 5, QTableWidgetItem(coverage_amount))

                # Column 6: Premium
                premium = f"₹{policy.premium_amount:,.0f}" if policy.premium_amount > 0 else "-"
                self.policy_table.setItem(row, 6, QTableWidgetItem(premium))

                # Column 7: Frequency
                self.policy_table.setItem(row, 7, QTableWidgetItem(policy.payment_frequency))

                # Column 8: Start Date
                start_date = str(policy.policy_start_date) if policy.policy_start_date else "-"
                self.policy_table.setItem(row, 8, QTableWidgetItem(start_date))

                # Column 9: End Date
                end_date = str(policy.valid_till) if policy.valid_till else "-"
                self.policy_table.setItem(row, 9, QTableWidgetItem(end_date))

                # Column 10: Status
                status_item = QTableWidgetItem(policy.current_status)
                # Color code status
                if policy.current_status == "Active":
                    status_item.setBackground(QColor(144, 238, 144))  # Light green
                elif policy.current_status == "Expired":
                    status_item.setBackground(QColor(255, 182, 193))  # Light red
                elif policy.current_status == "Pending Renewal":
                    status_item.setBackground(QColor(255, 255, 224))  # Light yellow
                self.policy_table.setItem(row, 10, status_item)

                # Column 11: Deductible
                deductible = f"₹{policy.deductible_amount:,.0f}" if policy.deductible_amount > 0 else "-"
                self.policy_table.setItem(row, 11, QTableWidgetItem(deductible))

                # Column 12: Beneficiaries
                beneficiaries = policy.beneficiaries if policy.beneficiaries else policy.nominee
                self.policy_table.setItem(row, 12, QTableWidgetItem(beneficiaries))

                # Column 13: Remarks
                self.policy_table.setItem(row, 13, QTableWidgetItem(policy.remarks))

    def refresh_lic_policy_table(self):
        """Refresh the LIC policy table with comprehensive data"""
        if hasattr(self, 'lic_policies') and hasattr(self, 'lic_policy_table'):
            self.lic_policy_table.setRowCount(len(self.lic_policies))
            for row, policy in enumerate(self.lic_policies):
                # Column 0: Policy Holder
                self.lic_policy_table.setItem(row, 0, QTableWidgetItem(policy.policy_holder_name))

                # Column 1: Policy Number
                self.lic_policy_table.setItem(row, 1, QTableWidgetItem(policy.policy_number))

                # Column 2: Policy Type
                self.lic_policy_table.setItem(row, 2, QTableWidgetItem(policy.policy_type))

                # Column 3: Plan Name
                self.lic_policy_table.setItem(row, 3, QTableWidgetItem(policy.plan_name))

                # Column 4: Premium Amount
                premium = f"₹{policy.premium_amount:,.0f}" if policy.premium_amount > 0 else "-"
                self.lic_policy_table.setItem(row, 4, QTableWidgetItem(premium))

                # Column 5: Premium Frequency
                self.lic_policy_table.setItem(row, 5, QTableWidgetItem(policy.premium_frequency))

                # Column 6: Sum Assured
                sum_assured = f"₹{policy.sum_assured:,.0f}" if policy.sum_assured > 0 else "-"
                self.lic_policy_table.setItem(row, 6, QTableWidgetItem(sum_assured))

                # Column 7: Maturity Date
                maturity_date = str(policy.maturity_date) if policy.maturity_date else "-"
                self.lic_policy_table.setItem(row, 7, QTableWidgetItem(maturity_date))

                # Column 8: Status
                status_item = QTableWidgetItem(policy.current_status)
                # Color code status
                if policy.current_status == "Active":
                    status_item.setBackground(QColor(45, 90, 45))    # Dark green
                    status_item.setForeground(QColor(144, 238, 144)) # Light green text
                elif policy.current_status == "Lapsed":
                    status_item.setBackground(QColor(90, 45, 45))    # Dark red
                    status_item.setForeground(QColor(255, 182, 193)) # Light red text
                elif policy.current_status == "Paid-up":
                    status_item.setBackground(QColor(90, 90, 45))    # Dark yellow
                    status_item.setForeground(QColor(255, 255, 224)) # Light yellow text
                elif policy.current_status == "Matured":
                    status_item.setBackground(QColor(45, 60, 90))    # Dark blue
                    status_item.setForeground(QColor(173, 216, 230)) # Light blue text
                self.lic_policy_table.setItem(row, 8, status_item)

                # Column 9: Nominee
                self.lic_policy_table.setItem(row, 9, QTableWidgetItem(policy.nominee_name))

                # Column 10: Agent
                agent_info = f"{policy.agent_name} ({policy.agent_code})" if policy.agent_name and policy.agent_code else policy.agent_name
                self.lic_policy_table.setItem(row, 10, QTableWidgetItem(agent_info))

                # Column 11: Remarks
                self.lic_policy_table.setItem(row, 11, QTableWidgetItem(policy.remarks))

    def refresh_loan_table(self):
        """Refresh the loan table with data from CSV and current balance from payment history"""
        if hasattr(self, 'loan_details') and hasattr(self, 'loan_table'):
            self.loan_table.setRowCount(len(self.loan_details))
            for row, loan in enumerate(self.loan_details):
                # Original columns
                self.loan_table.setItem(row, 0, QTableWidgetItem(loan.loan_name))

                # Calculate current balance based on payment history
                current_balance = self.calculate_loan_current_balance(loan)
                self.loan_table.setItem(row, 1, QTableWidgetItem(f"₹{current_balance:,.2f}"))

                self.loan_table.setItem(row, 2, QTableWidgetItem(f"{loan.interest_rate:.2f}%"))
                self.loan_table.setItem(row, 3, QTableWidgetItem(f"{loan.remaining_period_months} months"))

                # New columns with proper formatting and null handling
                self.loan_table.setItem(row, 4, QTableWidgetItem(f"₹{loan.emi_amount:,.2f}" if hasattr(loan, 'emi_amount') else "₹0.00"))

                # Format dates as YYYY-MM-DD
                emi_start_str = ""
                if hasattr(loan, 'emi_start_date') and loan.emi_start_date:
                    if isinstance(loan.emi_start_date, datetime):
                        emi_start_str = loan.emi_start_date.strftime("%Y-%m-%d")
                    elif isinstance(loan.emi_start_date, date):
                        emi_start_str = loan.emi_start_date.strftime("%Y-%m-%d")
                self.loan_table.setItem(row, 5, QTableWidgetItem(emi_start_str))

                emi_end_str = ""
                if hasattr(loan, 'emi_end_date') and loan.emi_end_date:
                    if isinstance(loan.emi_end_date, datetime):
                        emi_end_str = loan.emi_end_date.strftime("%Y-%m-%d")
                    elif isinstance(loan.emi_end_date, date):
                        emi_end_str = loan.emi_end_date.strftime("%Y-%m-%d")
                self.loan_table.setItem(row, 6, QTableWidgetItem(emi_end_str))

                last_paid_str = ""
                if hasattr(loan, 'last_paid_date') and loan.last_paid_date:
                    if isinstance(loan.last_paid_date, datetime):
                        last_paid_str = loan.last_paid_date.strftime("%Y-%m-%d")
                    elif isinstance(loan.last_paid_date, date):
                        last_paid_str = loan.last_paid_date.strftime("%Y-%m-%d")
                self.loan_table.setItem(row, 7, QTableWidgetItem(last_paid_str))

                # Net tenure and loan holder
                net_tenure = getattr(loan, 'net_tenure', 0)
                self.loan_table.setItem(row, 8, QTableWidgetItem(f"{net_tenure} months"))

                loan_holder = getattr(loan, 'loan_holder', "")
                self.loan_table.setItem(row, 9, QTableWidgetItem(loan_holder))

        # Update Net Worth display after loan data changes
        self.update_net_worth_display()

    def refresh_mutual_funds_table(self):
        """Refresh the mutual funds table with enhanced data display"""
        if not hasattr(self, 'mutual_funds_stocks') or not hasattr(self, 'mutual_funds_table'):
            self.logger.warning("⚠️ refresh_mutual_funds_table: Missing required attributes")
            return

        self.logger.info(f"🔄 refresh_mutual_funds_table: Refreshing table with {len(self.mutual_funds_stocks)} investments")



        # Calculate portfolio allocations before displaying
        self.calculate_portfolio_allocations()

        self.mutual_funds_table.setRowCount(len(self.mutual_funds_stocks))

        for row, fund in enumerate(self.mutual_funds_stocks):
            # Column 0: Name
            name_item = QTableWidgetItem(fund.name)
            self.mutual_funds_table.setItem(row, 0, name_item)

            # Column 1: Symbol
            symbol_item = QTableWidgetItem(fund.symbol)
            self.mutual_funds_table.setItem(row, 1, symbol_item)

            # Column 2: Category
            self.mutual_funds_table.setItem(row, 2, QTableWidgetItem(fund.category))

            # Column 3: Sub Category
            self.mutual_funds_table.setItem(row, 3, QTableWidgetItem(fund.sub_category))

            # Column 4: Geographic Classification
            self.mutual_funds_table.setItem(row, 4, QTableWidgetItem(fund.geographic_classification))

            # Column 5: Units (Unit Price column removed)
            self.mutual_funds_table.setItem(row, 5, QTableWidgetItem(f"{fund.units:.3f}"))

            # Column 6: Current Price (moved from Column 6)
            current_price_item = QTableWidgetItem()
            if fund.current_price > 0:
                current_price_text = f"₹{fund.current_price:.2f}"
                self.logger.debug(f"📊 Table refresh - {fund.symbol}: current_price = ₹{fund.current_price:.2f}")

                # Add visual indicator for stale prices
                if fund.is_price_stale():
                    current_price_text += " ⚠️"
                    current_price_item.setBackground(QColor(255, 255, 224))  # Light yellow

                current_price_item.setText(current_price_text)
            else:
                current_price_item.setText("N/A")
                current_price_item.setBackground(QColor(245, 245, 245))  # Light gray
                self.logger.debug(f"📊 Table refresh - {fund.symbol}: current_price = 0.0 (showing N/A)")

            self.mutual_funds_table.setItem(row, 6, current_price_item)

            # Column 7: Current Amount (Market Value) - moved from Column 7
            current_amount_item = QTableWidgetItem()

            # Calculate current market value: current_price × units
            if fund.current_price > 0 and fund.units > 0:
                calculated_current_amount = fund.current_price * fund.units
                current_amount_item.setText(f"₹{calculated_current_amount:,.2f}")

                self.logger.debug(f"📊 Table refresh - {fund.symbol}: current_amount = ₹{calculated_current_amount:.2f} (price: ₹{fund.current_price:.2f} × units: {fund.units:.3f})")

                # Color coding for profit/loss
                if fund.amount > 0:  # Only calculate P&L if we have original investment amount
                    profit_loss = calculated_current_amount - fund.amount
                    if profit_loss > 0:
                        current_amount_item.setBackground(QColor(200, 255, 200))  # Light green
                    elif profit_loss < 0:
                        current_amount_item.setBackground(QColor(255, 200, 200))  # Light red
            else:
                # Use original amount if no current price available
                current_amount_item.setText(f"₹{fund.amount:,.2f}")
                current_amount_item.setBackground(QColor(245, 245, 245))  # Light gray
                self.logger.debug(f"📊 Table refresh - {fund.symbol}: using original amount ₹{fund.amount:.2f} (no current price)")

            self.mutual_funds_table.setItem(row, 7, current_amount_item)

            # Column 8: Current Allocation - calculate dynamically based on current portfolio value
            total_portfolio_value = self.calculate_total_portfolio_value()
            if total_portfolio_value > 0 and fund.units > 0:
                current_value = fund.current_amount if fund.current_amount > 0 else (fund.units * fund.current_price)
                current_allocation_pct = (current_value / total_portfolio_value * 100)
                allocation_item = QTableWidgetItem(f"{current_allocation_pct:.2f}%")
            else:
                allocation_item = QTableWidgetItem("0.00%")
            self.mutual_funds_table.setItem(row, 8, allocation_item)

            # Column 9: Remarks (with profit/loss info) - moved from Column 9
            remarks_text = fund.remarks
            if fund.current_amount > 0 and fund.amount > 0:
                profit_loss = fund.get_profit_loss()
                profit_loss_pct = fund.get_profit_loss_percentage()

                if profit_loss != 0:
                    sign = "+" if profit_loss > 0 else ""
                    profit_info = f" | P&L: {sign}₹{profit_loss:,.2f} ({sign}{profit_loss_pct:.2f}%)"
                    remarks_text = (remarks_text + profit_info) if remarks_text else profit_info[3:]  # Remove " | "

            remarks_item = QTableWidgetItem(remarks_text)
            self.mutual_funds_table.setItem(row, 9, remarks_item)

        # Force comprehensive table display update
        self.mutual_funds_table.resizeColumnsToContents()  # Resize columns to fit content
        self.mutual_funds_table.viewport().update()  # Update table viewport

        # Note: Removed QCoreApplication.processEvents() to prevent processing quit events
        # that could cause application termination during price updates

        self.logger.info(f"✅ Table refresh completed - {self.mutual_funds_table.rowCount()} rows displayed")

        # Update Net Worth display after mutual funds data changes
        self.update_net_worth_display()

    def refresh_purchase_history_table(self):
        """Refresh the purchase history table"""
        if not hasattr(self, 'mutual_fund_purchase_history') or not hasattr(self, 'purchase_history_table'):
            return

        self.purchase_history_table.setRowCount(len(self.mutual_fund_purchase_history))

        for row, transaction in enumerate(self.mutual_fund_purchase_history):
            # Find the fund name by fund_id
            fund_name = "Unknown Fund"
            if hasattr(self, 'mutual_funds_stocks'):
                for fund in self.mutual_funds_stocks:
                    if fund.id == transaction.fund_id:
                        fund_name = fund.name
                        break

            # Column 0: Fund/Stock Name
            self.purchase_history_table.setItem(row, 0, QTableWidgetItem(fund_name))

            # Column 1: Transaction Type
            self.purchase_history_table.setItem(row, 1, QTableWidgetItem(transaction.transaction_type))

            # Column 2: Date
            date_str = ""
            if transaction.transaction_date:
                if isinstance(transaction.transaction_date, date):
                    date_str = transaction.transaction_date.strftime("%Y-%m-%d")
                else:
                    date_str = str(transaction.transaction_date)
            self.purchase_history_table.setItem(row, 2, QTableWidgetItem(date_str))

            # Column 3: Units
            self.purchase_history_table.setItem(row, 3, QTableWidgetItem(f"{transaction.units:.3f}"))

            # Column 4: Unit Price
            self.purchase_history_table.setItem(row, 4, QTableWidgetItem(f"₹{transaction.unit_price:.2f}"))

            # Column 5: Total Amount
            self.purchase_history_table.setItem(row, 5, QTableWidgetItem(f"₹{transaction.total_amount:.2f}"))

            # Column 6: Fees
            self.purchase_history_table.setItem(row, 6, QTableWidgetItem(f"₹{transaction.fees:.2f}"))

            # Column 7: Net Amount
            self.purchase_history_table.setItem(row, 7, QTableWidgetItem(f"₹{transaction.net_amount:.2f}"))

            # Column 8: Notes
            self.purchase_history_table.setItem(row, 8, QTableWidgetItem(transaction.notes))



    def calculate_net_worth(self):
        """Calculate Net Worth: Sum of all assets (Mutual Funds + Owned Assets) - Sum of all liabilities (Loans)"""
        try:
            # Calculate total current amount from mutual funds
            total_mutual_funds = 0.0
            if hasattr(self, 'mutual_funds_stocks') and self.mutual_funds_stocks:
                for fund in self.mutual_funds_stocks:
                    if fund.current_price > 0 and fund.units > 0:
                        # Use calculated current amount (current_price * units)
                        total_mutual_funds += fund.current_price * fund.units
                    elif fund.current_amount > 0:
                        # Fallback to stored current_amount
                        total_mutual_funds += fund.current_amount
                    elif fund.amount > 0:
                        # Fallback to original investment amount
                        total_mutual_funds += fund.amount

            # Calculate total value from owned assets
            total_owned_assets = 0.0
            if hasattr(self, 'owned_assets') and self.owned_assets:
                for asset in self.owned_assets:
                    total_owned_assets += asset.current_value

            # Calculate total current balance from loans
            total_loan_balance = 0.0
            if hasattr(self, 'loan_details') and self.loan_details:
                for loan in self.loan_details:
                    # Use the same calculation method as in the loan table
                    current_balance = self.calculate_loan_current_balance(loan)
                    total_loan_balance += current_balance

            # Total Assets = Mutual Funds + Owned Assets
            total_assets = total_mutual_funds + total_owned_assets

            # Total Liabilities = Loans
            total_liabilities = total_loan_balance

            # Net Worth = Total Assets - Total Liabilities
            net_worth = total_assets - total_liabilities

            self.logger.info(f"💰 Net Worth Calculation: Mutual Funds: ₹{total_mutual_funds:,.2f}, Owned Assets: ₹{total_owned_assets:,.2f}, Total Assets: ₹{total_assets:,.2f}, Loans: ₹{total_loan_balance:,.2f}, Net Worth: ₹{net_worth:,.2f}")

            return net_worth, total_assets, total_liabilities

        except Exception as e:
            self.logger.error(f"❌ Error calculating net worth: {e}")
            return 0.0, 0.0, 0.0

    def update_net_worth_display(self):
        """Update the Net Worth display in Portfolio Analysis header"""
        try:
            net_worth, total_assets, total_liabilities = self.calculate_net_worth()

            # Update the label with color coding
            if net_worth >= 0:
                color_style = "color: #2E7D32; background-color: #E8F5E8; border: 2px solid #4CAF50;"
                sign = "+"
            else:
                color_style = "color: #C62828; background-color: #FFEBEE; border: 2px solid #F44336;"
                sign = ""

            if hasattr(self, 'net_worth_label'):
                self.net_worth_label.setText(f"Net Worth: {sign}₹{net_worth:,.2f}")
                self.net_worth_label.setStyleSheet(f"{color_style} padding: 5px; border-radius: 5px; font-weight: bold;")
                self.net_worth_label.setToolTip(f"Assets: ₹{total_assets:,.2f}\nLiabilities: ₹{total_liabilities:,.2f}\nNet Worth: {sign}₹{net_worth:,.2f}")

        except Exception as e:
            self.logger.error(f"❌ Error updating net worth display: {e}")

    def calculate_total_portfolio_value(self):
        """Calculate total current portfolio value for allocation calculations"""
        try:
            total_value = 0.0

            # Add mutual funds/stocks value
            if hasattr(self, 'mutual_funds_stocks') and self.mutual_funds_stocks:
                for fund in self.mutual_funds_stocks:
                    if fund.units > 0:  # Only consider holdings with actual units
                        current_value = fund.current_amount if fund.current_amount > 0 else (fund.units * fund.current_price)
                        total_value += current_value

            # Add loan values (as liabilities) - these contribute to total portfolio value
            if hasattr(self, 'loan_details') and self.loan_details:
                for loan in self.loan_details:
                    current_balance = self.calculate_loan_current_balance(loan)
                    total_value += current_balance

            return total_value

        except Exception as e:
            self.logger.error(f"Error calculating total portfolio value: {e}")
            return 0.0

    def refresh_portfolio_analysis(self):
        """Refresh portfolio allocation analysis integrating Ideal Allocation and Current Allocation data"""
        # Update Net Worth first
        self.update_net_worth_display()

        # Get monthly savings target for difference amount calculations
        monthly_savings_target = self.monthly_savings_target.target_amount if hasattr(self, 'monthly_savings_target') else 3000.0

        # Create a comprehensive analysis by integrating Ideal Allocation and Current Allocation data
        portfolio_data = []

        # Calculate ideal allocation percentages using the same method as Portfolio Overview tab
        # This applies category-level allocations to individual assets, dividing equally within each category
        ideal_allocation_data = {}

        # Create asset items from mutual funds for allocation calculation (same as Portfolio Overview)
        asset_items = []
        if hasattr(self, 'mutual_funds_stocks') and self.mutual_funds_stocks:
            for fund in self.mutual_funds_stocks:
                if fund.units > 0:  # Only consider holdings with actual units
                    asset_items.append({
                        'name': fund.name,
                        'type': 'Asset',
                        'category': fund.category,
                        'sub_category': fund.sub_category,
                        'geographic_classification': fund.geographic_classification,
                        'amount': fund.current_amount
                    })

        # Apply the same allocation calculation logic as Portfolio Overview tab
        if asset_items and hasattr(self, 'allocation_settings') and self.allocation_settings:
            # Group assets by Category + Geographic Classification (same as Portfolio Overview)
            asset_groups = {}
            for item in asset_items:
                key = (item['category'], item['geographic_classification'])
                if key not in asset_groups:
                    asset_groups[key] = []
                asset_groups[key].append(item)

            # Apply allocation logic using allocation settings (same as Portfolio Overview)
            for item in asset_items:
                # Find allocation setting for this category + geographic classification
                category_allocation = self._get_category_allocation_for_analysis(item)
                if category_allocation is not None:
                    # Find how many assets are in this category + geographic classification
                    key = (item['category'], item['geographic_classification'])
                    group_size = len(asset_groups.get(key, []))
                    if group_size > 0:
                        # Divide the category allocation equally among assets in the category
                        item['ideal_percentage'] = category_allocation / group_size
                    else:
                        item['ideal_percentage'] = category_allocation
                else:
                    # Default to 0% if no allocation setting found
                    item['ideal_percentage'] = 0.0

                # Store in ideal_allocation_data with individual asset name as key
                # Use same case-insensitive key format as current allocation data
                key = item['name'].strip().lower().replace(' ', '').replace('-', '').replace('_', '')
                ideal_allocation_data[key] = {
                    'name': item['name'],
                    'type': item['type'],
                    'category': item['category'],
                    'sub_category': item['sub_category'],
                    'geographic_classification': item['geographic_classification'],
                    'ideal_percentage': item['ideal_percentage']
                }

        # Get current allocation data for individual assets (same as Portfolio Overview approach)
        current_allocation_data = {}

        # Calculate total current portfolio value including all assets and liabilities
        total_current_value = 0.0

        # Add mutual funds/stocks value
        if hasattr(self, 'mutual_funds_stocks') and self.mutual_funds_stocks:
            for fund in self.mutual_funds_stocks:
                if fund.units > 0:  # Only consider holdings with actual units
                    total_current_value += fund.current_amount

        # Add loan values (as liabilities) - these contribute to total portfolio value
        if hasattr(self, 'loan_details') and self.loan_details:
            for loan in self.loan_details:
                current_balance = self.calculate_loan_current_balance(loan)
                total_current_value += current_balance

        # Calculate current allocation percentages for individual mutual funds/stocks
        # This ensures we get the most up-to-date allocation based on current market values
        if hasattr(self, 'mutual_funds_stocks') and self.mutual_funds_stocks:
            for fund in self.mutual_funds_stocks:
                if fund.units > 0:  # Only consider holdings with actual units
                    # Use case-insensitive key for better matching
                    key = fund.name.strip().lower().replace(' ', '').replace('-', '').replace('_', '')

                    # Calculate current percentage based on current market value
                    current_value = fund.current_amount if fund.current_amount > 0 else (fund.units * fund.current_price)
                    current_percentage = (current_value / total_current_value * 100) if total_current_value > 0 else 0.0

                    # Update the fund's allocation_percent field for consistency
                    fund.allocation_percent = current_percentage

                    current_allocation_data[key] = {
                        'name': fund.name,
                        'type': 'Asset',  # All mutual funds/stocks are assets
                        'category': fund.category,
                        'sub_category': fund.sub_category,
                        'geographic_classification': fund.geographic_classification,
                        'current_percentage': current_percentage,
                        'current_amount': current_value
                    }

        # Create unified analysis by combining individual asset ideal allocations with current allocations
        all_assets = set()
        all_assets.update(ideal_allocation_data.keys())
        all_assets.update(current_allocation_data.keys())

        for asset_key in all_assets:
            ideal_data = ideal_allocation_data.get(asset_key, {})
            current_data = current_allocation_data.get(asset_key, {})

            # Use data from whichever source is available, preferring current data for basic info
            name = current_data.get('name') or ideal_data.get('name', asset_key.title())
            item_type = current_data.get('type') or ideal_data.get('type', 'Asset')
            category = current_data.get('category') or ideal_data.get('category', 'Unknown')
            sub_category = current_data.get('sub_category') or ideal_data.get('sub_category', 'Unknown')
            geographic_classification = current_data.get('geographic_classification') or ideal_data.get('geographic_classification', 'Unknown')

            # Get allocation percentages
            ideal_percentage = ideal_data.get('ideal_percentage', 0.0)
            current_percentage = current_data.get('current_percentage', 0.0)

            # Calculate difference (ideal - current)
            difference_percentage = ideal_percentage - current_percentage

            # Calculate difference amount based on monthly savings target
            difference_amount = (monthly_savings_target * difference_percentage) / 100 if monthly_savings_target > 0 else 0.0

            # Format values for display
            ideal_allocation_str = f"{ideal_percentage:.2f}%"
            current_allocation_str = f"{current_percentage:.2f}%"
            difference_str = f"{difference_percentage:+.2f}%"
            difference_amount_str = f"₹{difference_amount:+,.2f}" if difference_amount != 0 else "₹0"

            portfolio_data.append((
                name,
                item_type,
                category,
                sub_category,
                geographic_classification,
                ideal_allocation_str,
                current_allocation_str,
                difference_str,
                difference_amount_str
            ))

        # Sort by difference percentage (descending) to show largest gaps first
        portfolio_data.sort(key=lambda x: float(x[7].replace('%', '').replace('+', '')), reverse=True)

        # Populate the table
        if portfolio_data:
            self.portfolio_analysis_table.setRowCount(len(portfolio_data))
            for row, data in enumerate(portfolio_data):
                for col, value in enumerate(data):
                    item = QTableWidgetItem(str(value))

                    # Color code the difference columns for better visualization
                    if col == 7:  # Difference % column
                        diff_val = float(value.replace('%', '').replace('+', ''))
                        if diff_val > 0:
                            item.setBackground(QColor(255, 235, 235))  # Light red for under-allocated
                        elif diff_val < 0:
                            item.setBackground(QColor(235, 255, 235))  # Light green for over-allocated
                    elif col == 8:  # Difference Amount column
                        if '+' in value and value != "₹0":
                            item.setBackground(QColor(255, 235, 235))  # Light red for under-allocated
                        elif '-' in value:
                            item.setBackground(QColor(235, 255, 235))  # Light green for over-allocated

                    self.portfolio_analysis_table.setItem(row, col, item)
        else:
            # Fallback to message if no data available
            sample_data = [
                ("No Data", "Asset", "No data found", "Configure Ideal Allocation", "Unknown", "0.00%", "0.00%", "0.00%", "₹0")
            ]

            self.portfolio_analysis_table.setRowCount(len(sample_data))
            for row, data in enumerate(sample_data):
                for col, value in enumerate(data):
                    self.portfolio_analysis_table.setItem(row, col, QTableWidgetItem(str(value)))

    def _get_category_allocation_for_analysis(self, item):
        """Get allocation percentage for a category + geographic classification combination (for portfolio analysis)"""
        if not hasattr(self, 'allocation_settings') or not self.allocation_settings:
            return None

        for setting in self.allocation_settings:
            if (setting.category == item['category'] and
                setting.geographic_classification == item['geographic_classification']):
                return setting.allocation_percent
        return None



    def refresh_transaction_history_table(self):
        """Refresh the transaction history table"""
        # Temporarily disconnect the signal to avoid triggering during refresh
        self.transaction_history_table.itemChanged.disconnect()

        if hasattr(self, 'transaction_history') and self.transaction_history:
            # Sort by date (most recent first)
            sorted_transactions = sorted(self.transaction_history, key=lambda x: x.transaction_date, reverse=True)

            self.transaction_history_table.setRowCount(len(sorted_transactions))
            for row, transaction in enumerate(sorted_transactions):
                # Format date (read-only)
                date_str = transaction.transaction_date.strftime("%Y-%m-%d %H:%M") if transaction.transaction_date else ""
                date_item = QTableWidgetItem(date_str)
                date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
                self.transaction_history_table.setItem(row, 0, date_item)

                # Asset name (read-only)
                name_item = QTableWidgetItem(transaction.asset_name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.transaction_history_table.setItem(row, 1, name_item)

                # Transaction type with color coding (read-only)
                type_item = QTableWidgetItem(transaction.transaction_type)
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                if transaction.transaction_type == "BUY":
                    type_item.setBackground(QColor(235, 255, 235))  # Light green
                elif transaction.transaction_type == "SELL":
                    type_item.setBackground(QColor(255, 235, 235))  # Light red
                elif transaction.transaction_type == "INITIAL":
                    type_item.setBackground(QColor(235, 235, 255))  # Light blue
                self.transaction_history_table.setItem(row, 2, type_item)

                # Units (read-only)
                units_item = QTableWidgetItem(f"{transaction.units_purchased:.4f}")
                units_item.setFlags(units_item.flags() & ~Qt.ItemIsEditable)
                self.transaction_history_table.setItem(row, 3, units_item)

                # Price per unit (read-only)
                price_item = QTableWidgetItem(f"₹{transaction.price_per_unit:.2f}")
                price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
                self.transaction_history_table.setItem(row, 4, price_item)

                # Total amount (read-only)
                total_item = QTableWidgetItem(f"₹{transaction.total_amount:,.2f}")
                total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                self.transaction_history_table.setItem(row, 5, total_item)

                # Previous units (read-only)
                prev_units_item = QTableWidgetItem(f"{transaction.previous_units:.4f}")
                prev_units_item.setFlags(prev_units_item.flags() & ~Qt.ItemIsEditable)
                self.transaction_history_table.setItem(row, 6, prev_units_item)

                # New units (editable) - this is where users can update quantities
                new_units_item = QTableWidgetItem(f"{transaction.new_units:.4f}")
                new_units_item.setBackground(QColor(255, 255, 235))  # Light yellow to indicate editable
                new_units_item.setToolTip("Double-click to edit unit quantity")
                self.transaction_history_table.setItem(row, 7, new_units_item)
        else:
            self.transaction_history_table.setRowCount(0)

        # Reconnect the signal
        self.transaction_history_table.itemChanged.connect(self.on_transaction_history_item_changed)

    def on_transaction_history_item_changed(self, item):
        """Handle changes to transaction history table items"""
        try:
            # Only allow editing of the "New Units" column (column 7)
            if item.column() != 7:
                return

            row = item.row()
            if row >= len(self.transaction_history):
                return

            # Get the transaction being edited
            sorted_transactions = sorted(self.transaction_history, key=lambda x: x.transaction_date, reverse=True)
            transaction = sorted_transactions[row]

            # Parse the new unit value
            try:
                new_units = float(item.text())
                if new_units < 0:
                    raise ValueError("Units cannot be negative")
            except ValueError as e:
                QMessageBox.warning(self, "Invalid Input", f"Please enter a valid positive number for units.\nError: {e}")
                # Restore original value
                item.setText(f"{transaction.new_units:.4f}")
                return

            # Update the transaction
            old_units = transaction.new_units
            transaction.new_units = new_units
            transaction.units_purchased = abs(new_units - transaction.previous_units)
            transaction.total_amount = transaction.units_purchased * transaction.price_per_unit
            transaction.transaction_type = "BUY" if new_units > transaction.previous_units else "SELL" if new_units < transaction.previous_units else "UPDATE"
            transaction.notes = f"Units updated from {old_units} to {new_units} via Transaction History"

            # Create corresponding purchase history record for the change
            units_difference = new_units - old_units
            if units_difference != 0:
                # Find the corresponding fund
                corresponding_fund = None
                for fund in self.mutual_funds_stocks:
                    if fund.name.strip().lower() == transaction.asset_name.strip().lower():
                        corresponding_fund = fund
                        break

                if corresponding_fund:
                    change_type = "BUY" if units_difference > 0 else "SELL"
                    self.create_purchase_history_record(corresponding_fund, units_difference, change_type)

            # Find and update the corresponding mutual fund/stock
            fund_updated = False
            for fund in self.mutual_funds_stocks:
                if fund.name.strip().lower() == transaction.asset_name.strip().lower():
                    fund.units = new_units
                    # Recalculate amounts
                    if fund.current_price > 0:
                        fund.current_amount = fund.units * fund.current_price
                    if fund.unit_price > 0:
                        fund.amount = fund.units * fund.unit_price
                    fund_updated = True
                    break

            if fund_updated:
                # Save changes
                self.csv_manager.save_data('transaction_history', self.transaction_history)
                self.csv_manager.save_data('mutual_funds_stocks', self.mutual_funds_stocks)

                # Create portfolio growth snapshot for the change
                self.create_portfolio_growth_snapshot()

                # Refresh related displays
                self.refresh_mutual_funds_table()
                self.refresh_purchase_history_table()
                self.refresh_portfolio_analysis()
                self.refresh_portfolio_growth_table()
                self.refresh_portfolio_growth_chart()

                self.logger.info(f"Updated {transaction.asset_name} units from {old_units} to {new_units} via Transaction History")

                # Show success message
                QMessageBox.information(self, "Update Successful",
                                      f"Successfully updated {transaction.asset_name} units to {new_units:.4f}")
            else:
                QMessageBox.warning(self, "Update Failed",
                                  f"Could not find corresponding mutual fund/stock for {transaction.asset_name}")
                # Restore original value
                item.setText(f"{old_units:.4f}")

        except Exception as e:
            self.logger.error(f"Error updating transaction history: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update transaction: {str(e)}")

    def refresh_portfolio_growth_table(self):
        """Refresh the portfolio growth table with individual investment data"""
        # Check if individual investment growth data exists, create if missing
        if not hasattr(self, 'individual_investment_growth') or not self.individual_investment_growth:
            self.logger.info("Individual investment growth data missing, attempting to load/create...")
            try:
                # Try to load from CSV first
                self.individual_investment_growth = self.csv_manager.load_data('individual_investment_growth', IndividualInvestmentGrowth)
                self.logger.info(f"Loaded {len(self.individual_investment_growth) if self.individual_investment_growth else 0} individual investment growth records from CSV")

                # If still empty and we have mutual funds data, create initial records
                if not self.individual_investment_growth and hasattr(self, 'mutual_funds_stocks') and self.mutual_funds_stocks:
                    has_investments = any(fund.units > 0 for fund in self.mutual_funds_stocks)
                    if has_investments:
                        self.logger.info("Creating initial individual investment growth records...")
                        self.create_individual_investment_growth_records()

            except Exception as e:
                self.logger.error(f"Error loading/creating individual investment growth data: {e}")

        if not hasattr(self, 'individual_investment_growth') or not self.individual_investment_growth:
            self.logger.warning("No individual investment growth data available after load/create attempt")
            self.portfolio_growth_table.setRowCount(0)
            return

        self.logger.info(f"Refreshing portfolio growth table with {len(self.individual_investment_growth)} records")

        # Apply time filter
        filtered_data = self.apply_time_filter(self.individual_investment_growth)

        # Sort by date (most recent first)
        sorted_growth = sorted(filtered_data, key=lambda x: x.snapshot_date, reverse=True)

        self.portfolio_growth_table.setRowCount(len(sorted_growth))
        for row, growth_record in enumerate(sorted_growth):
            # Format date
            date_str = growth_record.snapshot_date.strftime("%Y-%m-%d %H:%M") if growth_record.snapshot_date else ""
            self.portfolio_growth_table.setItem(row, 0, QTableWidgetItem(date_str))

            # Investment name
            self.portfolio_growth_table.setItem(row, 1, QTableWidgetItem(growth_record.investment_name))

            # Units
            self.portfolio_growth_table.setItem(row, 2, QTableWidgetItem(f"{growth_record.units:.4f}"))

            # Unit price
            self.portfolio_growth_table.setItem(row, 3, QTableWidgetItem(f"₹{growth_record.unit_price:.2f}"))

            # Current value
            self.portfolio_growth_table.setItem(row, 4, QTableWidgetItem(f"₹{growth_record.current_value:,.2f}"))

            # Notes
            self.portfolio_growth_table.setItem(row, 5, QTableWidgetItem(growth_record.notes))

    def apply_time_filter(self, data):
        """Apply time filter to the data based on selected filter"""
        if not hasattr(self, 'time_filter_combo'):
            return data

        filter_text = self.time_filter_combo.currentText()
        if filter_text == "All Time":
            return data

        from datetime import timedelta
        now = datetime.now()

        if filter_text == "Last Month":
            cutoff_date = now - timedelta(days=30)
        elif filter_text == "Last Year":
            cutoff_date = now - timedelta(days=365)
        else:
            return data

        return [record for record in data if record.snapshot_date >= cutoff_date]

    def on_time_filter_changed(self):
        """Handle time filter change"""
        self.refresh_portfolio_growth_table()
        self.refresh_portfolio_growth_chart()

    def refresh_portfolio_growth_chart(self):
        """Refresh the portfolio growth visualization chart with individual investment lines"""
        try:
            self.logger.info("🔄 Starting portfolio growth chart refresh...")

            # Check if chart widget exists first
            if not hasattr(self, 'growth_chart_widget'):
                self.logger.error("❌ Growth chart widget not found!")
                return

            # Show loading message
            loading_html = """
            <html>
            <head>
                <style>
                    body {
                        background-color: #1e1e1e;
                        color: #ffffff;
                        font-family: Arial;
                        text-align: center;
                        padding: 50px;
                        margin: 0;
                    }
                    .loading-box {
                        background-color: #252526;
                        padding: 30px;
                        border-radius: 10px;
                        border: 2px solid #FFA500;
                        margin: 20px;
                    }
                    .spinner {
                        border: 4px solid #3e3e42;
                        border-top: 4px solid #FFA500;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            </head>
            <body>
                <div class="loading-box">
                    <div class="spinner"></div>
                    <h2>📈 Loading Portfolio Growth Chart...</h2>
                    <p>Generating your investment growth visualization</p>
                </div>
            </body>
            </html>
            """
            self.growth_chart_widget.setHtml(loading_html)

            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            import plotly.offline as pyo
            from datetime import datetime
            from ...ui.plotly_theme import apply_dark_theme_to_figure, get_dark_theme_html_template

            if not hasattr(self, 'individual_investment_growth') or not self.individual_investment_growth:
                # Try to load data first
                self.logger.info("Loading individual investment growth data...")
                try:
                    # Ensure we have the csv_manager attribute
                    if hasattr(self, 'csv_manager'):
                        self.individual_investment_growth = self.csv_manager.load_data('individual_investment_growth', IndividualInvestmentGrowth)
                        self.logger.info(f"Loaded {len(self.individual_investment_growth) if self.individual_investment_growth else 0} growth records")
                    else:
                        self.logger.error("CSV manager not available - cannot load growth data")
                        self.individual_investment_growth = []
                except Exception as e:
                    self.logger.error(f"Error loading individual investment growth data for chart: {e}")
                    self.individual_investment_growth = []

                # If still no data, show empty chart message
                if not hasattr(self, 'individual_investment_growth') or not self.individual_investment_growth:
                    self.logger.warning("No individual investment growth data available for chart")
                    empty_html = """
                    <html>
                    <body style="background-color: #1e1e1e; color: #ffffff; font-family: Arial; text-align: center; padding: 50px;">
                        <h2>📈 Individual Investment Growth Chart</h2>
                        <p>No growth data available yet. Click "Create Growth Records" button to generate initial data!</p>
                        <p style="font-size: 14px; color: #cccccc;">Note: Growth records are created automatically when you make changes to your investments.</p>
                    </body>
                    </html>
                    """
                    self.growth_chart_widget.setHtml(empty_html)
                    return

            # Apply time filter
            filtered_data = self.apply_time_filter(self.individual_investment_growth)
            self.logger.info(f"After time filter: {len(filtered_data)} records")

            # CRITICAL FIX: Filter out zero-value records (setup records that shouldn't be charted)
            meaningful_data = [r for r in filtered_data if r.current_value > 0.0] if filtered_data else []
            self.logger.info(f"After zero-value filtering: {len(meaningful_data)} meaningful records")

            if not meaningful_data:
                self.logger.warning("No meaningful data available after filtering")
                empty_html = """
                <html>
                <body style="background-color: #1e1e1e; color: #ffffff; font-family: Arial; text-align: center; padding: 50px;">
                    <h2>📈 Individual Investment Growth Chart</h2>
                    <p>No meaningful data available for the selected time period.</p>
                    <p style="font-size: 14px; color: #cccccc;">Only setup records with zero values found. Try updating investment values or creating growth records.</p>
                </body>
                </html>
                """
                self.growth_chart_widget.setHtml(empty_html)
                return

            # Group data by investment name
            investment_data = {}
            for record in meaningful_data:
                if record.investment_name not in investment_data:
                    investment_data[record.investment_name] = []
                investment_data[record.investment_name].append(record)

            self.logger.info(f"Grouped data into {len(investment_data)} investments: {list(investment_data.keys())}")

            # Sort each investment's data by date
            for investment_name in investment_data:
                investment_data[investment_name].sort(key=lambda x: x.snapshot_date)

            # Create the chart
            fig = go.Figure()

            # Color palette for different investments
            colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4', '#FFEB3B', '#795548']

            # Add a line for each investment
            traces_added = 0
            for i, (investment_name, records) in enumerate(investment_data.items()):
                dates = [record.snapshot_date for record in records]
                values = [record.current_value for record in records]

                self.logger.info(f"Processing {investment_name}: {len(dates)} dates, {len(values)} values")
                if dates and values:
                    self.logger.info(f"  Date range: {min(dates)} to {max(dates)}")
                    self.logger.info(f"  Value range: ₹{min(values):,.2f} to ₹{max(values):,.2f}")

                color = colors[i % len(colors)]

                if dates and values:  # Only add trace if we have data
                    fig.add_trace(
                        go.Scatter(
                            x=dates,
                            y=values,
                            mode='lines+markers',
                            name=investment_name,
                            line=dict(color=color, width=2),
                            marker=dict(size=4),
                            hovertemplate=f'<b>{investment_name}</b><br>Date: %{{x}}<br>Value: ₹%{{y:,.2f}}<extra></extra>'
                        )
                    )
                    traces_added += 1
                else:
                    self.logger.warning(f"No data for {investment_name}")

            self.logger.info(f"Added {traces_added} traces to chart")

            # Update layout
            fig.update_layout(
                title={
                    'text': '📈 Individual Investment Growth Over Time',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 20, 'family': 'Arial, sans-serif'}
                },
                height=600,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                ),
                margin=dict(l=60, r=200, t=100, b=60),
                xaxis_title="Date",
                yaxis_title="Investment Value (₹)"
            )

            # Apply dark theme
            fig = apply_dark_theme_to_figure(fig)

            # Generate HTML and display
            self.logger.info("Generating chart HTML...")
            try:
                # CRITICAL FIX: Use same HTML generation method as working charts
                html_content = fig.to_html(include_plotlyjs='cdn')
                self.logger.info(f"Generated HTML content length: {len(html_content)}")

                self.logger.info("Setting chart HTML to widget...")

                # Debug widget state
                self.logger.info(f"🔍 Widget debug info:")
                self.logger.info(f"  - Widget exists: {hasattr(self, 'growth_chart_widget')}")
                if hasattr(self, 'growth_chart_widget'):
                    self.logger.info(f"  - Widget visible: {self.growth_chart_widget.isVisible()}")
                    self.logger.info(f"  - Widget size: {self.growth_chart_widget.size()}")
                    self.logger.info(f"  - Widget geometry: {self.growth_chart_widget.geometry()}")

                # Set the chart HTML directly (using working method)
                self.logger.info("📊 Setting chart HTML...")
                self.growth_chart_widget.setHtml(html_content)

                # Force widget update
                self.growth_chart_widget.update()
                self.growth_chart_widget.repaint()

                self.logger.info("✅ Portfolio growth chart refresh completed successfully")
            except Exception as html_error:
                self.logger.error(f"Error generating or setting HTML: {html_error}")
                import traceback
                self.logger.error(f"Full error traceback: {traceback.format_exc()}")

                # Try a simple test chart with enhanced debugging
                test_html = """
                <html>
                <head>
                    <title>Portfolio Growth Chart Test</title>
                    <style>
                        body {
                            background-color: #1e1e1e;
                            color: #ffffff;
                            font-family: Arial, sans-serif;
                            text-align: center;
                            padding: 20px;
                            margin: 0;
                        }
                        .test-container {
                            background-color: #252526;
                            padding: 30px;
                            margin: 20px;
                            border-radius: 8px;
                            border: 2px solid #007ACC;
                        }
                        .error-info {
                            background-color: #3c1e1e;
                            color: #ff6b6b;
                            padding: 15px;
                            margin: 10px;
                            border-radius: 5px;
                            border-left: 4px solid #ff6b6b;
                        }
                    </style>
                </head>
                <body>
                    <div class="test-container">
                        <h2>🚨 Portfolio Growth Chart Error</h2>
                        <p><strong>Chart generation failed, but QWebEngineView is working!</strong></p>
                        <div class="error-info">
                            <p><strong>Error:</strong> Chart generation or HTML setting failed</p>
                            <p><strong>Time:</strong> """ + str(datetime.now()) + """</p>
                        </div>
                        <p>If you can see this styled message, the WebEngine widget is functioning correctly.</p>
                        <p>The issue is likely with Plotly chart generation or JavaScript execution.</p>
                    </div>
                </body>
                </html>
                """
                self.growth_chart_widget.setHtml(test_html)
                raise html_error

        except ImportError as e:
            self.logger.warning(f"Could not create growth chart - missing imports: {e}")
            # Show fallback message
            fallback_html = """
            <html>
            <body style="background-color: #1e1e1e; color: #ffffff; font-family: Arial; text-align: center; padding: 50px;">
                <h2>📈 Individual Investment Growth Chart</h2>
                <p style="color: #ff9800;">Chart requires Plotly library. Please install plotly to view charts.</p>
            </body>
            </html>
            """
            if hasattr(self, 'growth_chart_widget'):
                self.growth_chart_widget.setHtml(fallback_html)
        except Exception as e:
            self.logger.error(f"Error creating portfolio growth chart: {e}")
            # Show error message
            error_html = f"""
            <html>
            <body style="background-color: #1e1e1e; color: #ffffff; font-family: Arial; text-align: center; padding: 50px;">
                <h2>📈 Individual Investment Growth Chart</h2>
                <p style="color: #f44336;">Error generating chart: {str(e)}</p>
                <p style="font-size: 14px; color: #cccccc;">Please check the logs for more details.</p>
            </body>
            </html>
            """
            if hasattr(self, 'growth_chart_widget'):
                self.growth_chart_widget.setHtml(error_html)

    def _create_initial_growth_chart(self):
        """Create initial empty chart (following working pattern from other modules)"""
        try:
            import plotly.graph_objects as go

            # Create empty figure with waiting message
            fig = go.Figure()
            fig.add_annotation(
                text="📈 Portfolio Growth Chart<br>Waiting for data...",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title="Portfolio Growth Chart",
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor='#252526',
                paper_bgcolor='#1e1e1e',
                font=dict(color='white'),
                height=400
            )

            # Use the same HTML generation method as working charts
            html_content = fig.to_html(include_plotlyjs='cdn')
            self.growth_chart_widget.setHtml(html_content)

            self.logger.info("✅ Initial growth chart created successfully")

        except Exception as e:
            self.logger.error(f"❌ Error creating initial growth chart: {e}")
            # Fallback to simple HTML
            fallback_html = """
            <html>
            <head>
                <style>
                    body {
                        background-color: #1e1e1e;
                        color: #ffffff;
                        font-family: Arial;
                        text-align: center;
                        padding: 50px;
                        margin: 0;
                    }
                    .ready-box {
                        background-color: #252526;
                        padding: 30px;
                        border-radius: 10px;
                        border: 2px solid #007ACC;
                        margin: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="ready-box">
                    <h2>📈 Portfolio Growth Chart</h2>
                    <p>Ready to display your investment growth over time</p>
                    <p style="font-size: 14px; color: #cccccc;">Click "📊 Refresh Growth Chart" button to load the chart</p>
                </div>
            </body>
            </html>
            """
            self.growth_chart_widget.setHtml(fallback_html)

    def on_portfolio_analysis_tab_changed(self, index):
        """Handle Portfolio Analysis sub-tab changes to refresh data"""
        try:
            # Refresh Portfolio Analysis when switching to Analysis tab (index 0)
            if index == 0:
                self.refresh_portfolio_analysis()

            # Refresh Transaction History when switching to Transaction History tab (index 1)
            elif index == 1:
                self.refresh_transaction_history_table()

            # Refresh Portfolio Growth when switching to Portfolio Growth tab (index 2)
            elif index == 2:
                self.refresh_portfolio_growth_table()
                self.refresh_portfolio_growth_chart()

        except Exception as e:
            self.logger.error(f"Error refreshing Portfolio Analysis tab data: {e}")

    def refresh_all_portfolio_data(self):
        """Refresh all portfolio-related data and visualizations"""
        try:
            # Refresh main Portfolio Analysis
            self.refresh_portfolio_analysis()

            # Refresh historical tracking data
            self.refresh_transaction_history_table()
            self.refresh_portfolio_growth_table()
            self.refresh_portfolio_growth_chart()

            # Refresh owned assets table
            self.refresh_owned_assets_table()

            self.logger.info("All portfolio data refreshed successfully")

        except Exception as e:
            self.logger.error(f"Error refreshing all portfolio data: {e}")

    def on_main_tab_changed(self, index):
        """Handle main tab changes to refresh data when tabs are accessed"""
        try:
            # Check if the Owned Assets tab is being accessed (index 2)
            if index == 2:  # Owned Assets tab index
                self.refresh_owned_assets_table()
            # Check if the Portfolio Analysis tab is being accessed (index 7 after adding Owned Assets tab)
            elif index == 7:  # Portfolio Analysis tab index
                self.refresh_all_portfolio_data()

        except Exception as e:
            self.logger.error(f"Error handling main tab change: {e}")



    def update_all_prices(self):
        """Update prices for all mutual funds and stocks with crash-free synchronous approach"""
        try:
            # Add detailed logging for debugging
            self.logger.info("🔄 Price update button clicked - starting crash-free synchronous update...")

            # Check if a price update is already in progress
            if getattr(self, '_price_update_in_progress', False):
                self.logger.warning("❌ Price update already in progress")
                self._safe_show_message(
                    "Update In Progress",
                    "A price update is already in progress. Please wait for it to complete.",
                    "information"
                )
                return

            # Set the flag to prevent concurrent updates
            self._price_update_in_progress = True

            # Check if yfinance is available
            if not hasattr(price_fetcher, 'YFINANCE_AVAILABLE') or not price_fetcher.YFINANCE_AVAILABLE:
                self.logger.error("❌ yfinance not available")
                self._safe_show_message(
                    "Missing Dependency",
                    "The yfinance library is not installed. Please install it using:\n\n"
                    "pip install yfinance\n\n"
                    "This library is required for fetching current stock and mutual fund prices.",
                    "error"
                )
                self._price_update_in_progress = False  # Clear flag before returning
                return
            else:
                self.logger.info("✅ yfinance is available")

            if not hasattr(self, 'mutual_funds_stocks') or not self.mutual_funds_stocks:
                self.logger.error("❌ No mutual funds/stocks data loaded")
                self._safe_show_message("No Data", "No mutual funds or stocks to update.", "information")
                self._price_update_in_progress = False  # Clear flag before returning
                return
            else:
                self.logger.info(f"✅ Found {len(self.mutual_funds_stocks)} investments")

            # Check for symbols
            symbols_count = sum(1 for fund in self.mutual_funds_stocks if fund.symbol and fund.symbol.strip())
            if symbols_count == 0:
                self.logger.error("❌ No valid symbols found")
                self._safe_show_message(
                    "No Symbols",
                    "No valid symbols found in your investments. Please add symbols to enable price updates.",
                    "warning"
                )
                self._price_update_in_progress = False  # Clear flag before returning
                return
            else:
                self.logger.info(f"✅ Found {symbols_count} valid symbols")

            # Check internet connectivity by trying a simple request
            try:
                import urllib.request
                import ssl

                # Create SSL context that doesn't verify certificates (for testing)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                # Try with SSL verification disabled first
                try:
                    urllib.request.urlopen('https://finance.yahoo.com', timeout=5, context=ssl_context)
                    self.logger.info("✅ Internet connectivity confirmed (SSL verification bypassed)")
                except Exception:
                    # If that fails, try with normal SSL
                    urllib.request.urlopen('https://finance.yahoo.com', timeout=5)
                    self.logger.info("✅ Internet connectivity confirmed")

            except Exception as e:
                self.logger.warning(f"⚠️ Network connectivity issue: {e}")

                # Check if it's an SSL certificate issue
                if "CERTIFICATE_VERIFY_FAILED" in str(e) or "SSL" in str(e).upper():
                    # For SSL issues, automatically continue with disabled verification
                    # to avoid blocking the user with a dialog that could cause crashes
                    self.logger.warning("🔧 SSL certificate issue detected, automatically disabling SSL verification")
                    import os
                    os.environ['PYTHONHTTPSVERIFY'] = '0'
                    self.logger.info("🔧 SSL verification disabled for this session")

                    # Show informational message about the SSL workaround
                    self._safe_show_message(
                        "SSL Certificate Issue",
                        "SSL certificate verification failed when connecting to Yahoo Finance.\n\n"
                        "SSL verification has been automatically disabled for this session.\n"
                        "Your data remains secure - this only affects the Yahoo Finance connection.",
                        "information"
                    )
                else:
                    # For other network issues, show warning but continue
                    self.logger.warning("🌐 Network connectivity issue, continuing with price update attempt")
                    self._safe_show_message(
                        "Network Issue",
                        "Unable to connect to Yahoo Finance initially. This could be due to:\n\n"
                        "• Temporary network issues\n"
                        "• Firewall blocking the connection\n"
                        "• Yahoo Finance temporarily unavailable\n\n"
                        "The price update will continue and may still succeed.",
                        "warning"
                    )

            # Disable the update button during processing
            self.update_prices_btn.setEnabled(False)
            self.update_prices_btn.setText("🔄 Updating...")
            self.logger.info("🔄 Starting crash-free synchronous price update...")

            # Show both progress bars with better formatting
            total_investments = len(self.mutual_funds_stocks)
            self.logger.info(f"📊 Initializing progress bars for {total_investments} investments")

            # Initialize both progress bars
            for progress_bar in [self.price_update_progress, self.main_progress_bar]:
                progress_bar.setVisible(True)
                progress_bar.setRange(0, total_investments)
                progress_bar.setValue(0)
                progress_bar.setFormat(f"Starting update for {total_investments} investments... 0%")
                progress_bar.repaint()

            self.logger.info(f"✅ Progress bars initialized - Small: {self.price_update_progress.isVisible()}, Main: {self.main_progress_bar.isVisible()}")

            # Use synchronous approach instead of threading to eliminate crashes
            self._update_prices_synchronously()

        except Exception as e:
            self.logger.error(f"❌ Error starting price update: {e}")
            import traceback
            self.logger.error(f"❌ Full traceback: {traceback.format_exc()}")

            # Use safe message display instead of direct QMessageBox
            self._show_error_safely(f"Failed to start price update: {str(e)}")

            # Restore button state and hide progress bars
            self.reset_price_update_button()
            if hasattr(self, 'price_update_progress'):
                self.price_update_progress.setVisible(False)
            if hasattr(self, 'main_progress_bar'):
                self.main_progress_bar.setVisible(False)

            # Clear the progress flag to allow future updates
            self._price_update_in_progress = False

    def _update_prices_synchronously(self):
        """Update prices synchronously without threading to eliminate crashes"""
        updated_count = 0
        failed_updates = []

        try:
            self.logger.info("🔄 Starting synchronous price update...")

            # Extract symbols for processing
            symbols = [fund.symbol.strip() for fund in self.mutual_funds_stocks if fund.symbol and fund.symbol.strip()]

            if not symbols:
                self.logger.error("❌ No valid symbols found")
                self._finalize_price_update(0, ["No valid symbols found"])
                return

            self.logger.info(f"🔍 Processing {len(symbols)} symbols: {symbols}")

            # Process each symbol with UI updates
            total_symbols = len(symbols)
            price_results = {}

            for i, symbol in enumerate(symbols):
                try:
                    # Update progress bars
                    progress_value = i + 1
                    progress_percent = int((progress_value / total_symbols) * 100)

                    # Update both progress bars
                    for progress_bar in [self.price_update_progress, self.main_progress_bar]:
                        progress_bar.setValue(progress_value)
                        progress_bar.setFormat(f"Fetching {symbol}... {progress_percent}%")
                        progress_bar.repaint()

                    # Process events to keep UI responsive
                    QApplication.processEvents()

                    self.logger.debug(f"🔍 Fetching price for symbol {i+1}/{total_symbols}: {symbol}")

                    # Fetch individual price
                    price = price_fetcher.get_current_price(symbol)
                    if price is not None:
                        price_results[symbol] = price
                        self.logger.debug(f"✅ Got price for {symbol}: ₹{price:.2f}")
                    else:
                        self.logger.debug(f"❌ No price data for {symbol}")

                    # Small delay to make progress visible
                    import time
                    time.sleep(0.1)

                except Exception as symbol_error:
                    self.logger.warning(f"❌ Failed to fetch price for {symbol}: {symbol_error}")

            self.logger.info(f"✅ Price fetch completed, got {len(price_results)} results out of {total_symbols} symbols")

            # Update each fund with the fetched price
            for fund in self.mutual_funds_stocks:
                try:
                    if not fund.symbol or not fund.symbol.strip():
                        failed_updates.append(f"{fund.name}: No symbol defined")
                        continue

                    symbol = fund.symbol.strip()

                    if symbol in price_results:
                        new_price = price_results[symbol]
                        if new_price is not None and new_price > 0:
                            old_price = fund.current_price
                            fund.update_current_price(new_price)
                            updated_count += 1

                            # Log significant price changes
                            if old_price > 0:
                                change_pct = ((new_price - old_price) / old_price) * 100
                                if abs(change_pct) > 10:  # Log changes > 10%
                                    self.logger.warning(f"Large price change for {symbol}: {old_price:.2f} → {new_price:.2f} ({change_pct:+.1f}%)")

                            self.logger.debug(f"✅ Updated {fund.name} ({symbol}): ₹{old_price:.2f} → ₹{new_price:.2f}")
                        else:
                            failed_updates.append(f"{fund.name}: Invalid price data")
                    else:
                        failed_updates.append(f"{fund.name}: No price data available")

                except Exception as fund_error:
                    self.logger.error(f"❌ Error updating fund {fund.name}: {fund_error}")
                    failed_updates.append(f"{fund.name}: Update error - {str(fund_error)}")

            self.logger.info(f"✅ Price update completed: {updated_count} updated, {len(failed_updates)} failed")

            # Finalize the update
            self._finalize_price_update(updated_count, failed_updates)

        except Exception as e:
            self.logger.error(f"Critical error in synchronous price update: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            self._finalize_price_update(0, [f"Critical system error: {str(e)}"])

    def reset_price_update_button(self):
        """Reset the price update button to its default state"""
        try:
            self.update_prices_btn.setEnabled(True)
            self.update_prices_btn.setText("🔄 Update Prices")
            self.logger.debug("Price update button reset to default state")
        except Exception as e:
            self.logger.error(f"Error resetting price update button: {e}")

    def _update_progress_bar(self, value):
        """Update progress bar value in main thread"""
        try:
            if hasattr(self, 'mutual_funds_stocks'):
                total = len(self.mutual_funds_stocks)
                format_text = f"Updating {value}/{total} investments... %p%"
                percentage = (value / total) * 100

                self.logger.info(f"🔄 _update_progress_bar called with value={value}, total={total}")

                # Update both progress bars
                progress_bars = []
                if hasattr(self, 'price_update_progress'):
                    progress_bars.append(('small', self.price_update_progress))
                if hasattr(self, 'main_progress_bar'):
                    progress_bars.append(('main', self.main_progress_bar))

                for name, progress_bar in progress_bars:
                    old_value = progress_bar.value()
                    progress_bar.setValue(value)
                    progress_bar.setFormat(format_text)

                    # Ensure progress bar is visible and force a repaint
                    if not progress_bar.isVisible():
                        progress_bar.setVisible(True)
                        self.logger.debug(f"🔍 {name} progress bar was hidden, making it visible")

                    progress_bar.repaint()
                    new_value = progress_bar.value()

                    self.logger.info(f"📊 {name} progress bar: {old_value} → {new_value} ({percentage:.1f}%)")

                self.logger.info(f"✅ Progress bars updated successfully: {value}/{total}")

        except Exception as e:
            self.logger.error(f"Error updating progress bars: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")



    def _on_price_update_complete(self, updated_count, failed_updates):
        """Handle completion of price update process"""
        try:
            # Clean up the thread and worker properly to prevent crashes
            self._cleanup_price_update_thread()

            # Save updated data to CSV if any updates were made
            if updated_count > 0:
                try:
                    self.logger.info(f"🔄 Attempting to save {updated_count} updated prices to CSV...")
                    save_success = self.csv_manager.save_data('mutual_funds_stocks', self.mutual_funds_stocks)
                    if save_success:
                        self.logger.info(f"✅ Successfully saved {updated_count} updated prices to CSV")
                    else:
                        self.logger.warning(f"⚠️ CSV save returned False - data may not have been saved properly")
                except Exception as csv_error:
                    import traceback
                    self.logger.error(f"❌ Critical error saving to CSV: {csv_error}")
                    self.logger.error(f"❌ CSV save traceback: {traceback.format_exc()}")
                    # Don't let CSV save errors crash the application
                    # The price updates were successful, so continue with UI updates
                    self.logger.warning("⚠️ Continuing with UI updates despite CSV save failure")

                    # Store the CSV error to show in the final message
                    if not hasattr(self, '_csv_save_error'):
                        self._csv_save_error = str(csv_error)

            # Finalize the UI update
            self._finalize_price_update(updated_count, failed_updates)

        except Exception as e:
            self.logger.error(f"Error in _on_price_update_complete: {e}")
            # Still try to cleanup and finalize the UI
            self._cleanup_price_update_thread()
            self._finalize_price_update(updated_count, failed_updates)

    def _cleanup_price_update_thread(self):
        """Properly clean up the price update thread and worker to prevent crashes"""
        try:
            self.logger.debug("🔄 Starting safe price update thread cleanup...")

            # Block signals first to prevent any callbacks during cleanup
            if hasattr(self, 'price_update_worker') and self.price_update_worker:
                try:
                    # Block signals to prevent emission during cleanup
                    self.price_update_worker.blockSignals(True)
                    self.logger.debug("✅ Blocked price update worker signals")
                except Exception as e:
                    self.logger.warning(f"Error blocking worker signals: {e}")

            # Clean up the thread
            if hasattr(self, 'price_update_thread') and self.price_update_thread:
                if self.price_update_thread.isRunning():
                    self.logger.debug("🔄 Stopping price update thread...")
                    self.price_update_thread.quit()

                    # Wait for thread to finish gracefully - avoid terminate() to prevent crashes
                    if not self.price_update_thread.wait(3000):  # Wait up to 3 seconds
                        self.logger.warning("Price update thread did not stop gracefully within 3 seconds")
                        # Don't use terminate() as it can cause application crashes
                        # Instead, just log the warning and continue with cleanup
                        self.logger.warning("Continuing with cleanup without terminating thread")
                    else:
                        self.logger.debug("✅ Price update thread stopped gracefully")

                # Clear reference without calling deleteLater to avoid crashes
                self.price_update_thread = None

            # Clean up the worker
            if hasattr(self, 'price_update_worker') and self.price_update_worker:
                self.price_update_worker = None

            self.logger.debug("✅ Price update thread and worker cleanup completed safely")

        except Exception as e:
            self.logger.error(f"Error during price update thread cleanup: {e}")
            # Ensure objects are cleared even if cleanup fails
            if hasattr(self, 'price_update_thread'):
                self.price_update_thread = None
            if hasattr(self, 'price_update_worker'):
                self.price_update_worker = None

        finally:
            # Always clear the progress flag to allow future updates
            self._price_update_in_progress = False

    def _finalize_price_update(self, updated_count, failed_updates):
        """Finalize the price update process in the main thread with simplified safety checks"""
        try:
            # Simple safety check to ensure widget is in stable state
            if getattr(self, '_closing', False):
                self.logger.warning("Widget is closing, skipping price update finalization")
                return
            # Hide both progress bars and re-enable button
            progress_bars = []
            if hasattr(self, 'price_update_progress'):
                progress_bars.append(self.price_update_progress)
            if hasattr(self, 'main_progress_bar'):
                progress_bars.append(self.main_progress_bar)

            for progress_bar in progress_bars:
                progress_bar.setVisible(False)
                progress_bar.setValue(0)  # Reset to 0
                progress_bar.setFormat("%p%")  # Reset format
                self.logger.debug(f"✅ Progress bar hidden and reset to 0")

            self.reset_price_update_button()

            # Save updated data to CSV if any updates were made
            csv_save_success = True
            if updated_count > 0:
                try:
                    self.logger.info(f"🔄 Attempting to save {updated_count} updated prices to CSV...")
                    csv_save_success = self.csv_manager.save_data('mutual_funds_stocks', self.mutual_funds_stocks)
                    if csv_save_success:
                        self.logger.info(f"✅ Successfully saved {updated_count} updated prices to CSV")
                    else:
                        self.logger.warning(f"⚠️ CSV save returned False - data may not have been saved properly")
                        self._csv_save_error = "CSV save operation returned False"
                except Exception as csv_error:
                    import traceback
                    self.logger.error(f"❌ Critical error saving to CSV: {csv_error}")
                    self.logger.error(f"❌ CSV save traceback: {traceback.format_exc()}")
                    csv_save_success = False
                    self._csv_save_error = str(csv_error)

            # Force update the table display and portfolio summary
            self.logger.info("🔄 Refreshing UI after price update...")
            self.refresh_mutual_funds_table()

            self.update_portfolio_summary()

            # Update last update timestamp display
            self.update_last_price_update_display()

            # Force comprehensive UI updates to ensure visibility
            self.mutual_funds_table.clearSelection()  # Clear selection to force refresh
            self.mutual_funds_table.viewport().update()  # Update table viewport
            self.mutual_funds_table.repaint()  # Force repaint
            self.update()  # Update entire widget

            # Note: Removed QCoreApplication.processEvents() as it can process quit events
            # and cause application termination after thread cleanup

            self.logger.info("✅ UI refresh completed with enhanced table update")

            # Show results to user with safer messaging approach
            total_investments = len(self.mutual_funds_stocks) if hasattr(self, 'mutual_funds_stocks') else 0

            # Use safer approach to show completion message - avoid QMessageBox that might cause crashes
            self._show_price_update_completion_safely(updated_count, failed_updates, total_investments)

            self.logger.info(f"Price update completed: {updated_count} updated, {len(failed_updates)} failed")

        except Exception as e:
            self.logger.error(f"Error finalizing price update: {e}")
            # Use safer error reporting to avoid crashes
            self._show_error_safely(f"Error completing price update: {str(e)}")

    def _show_price_update_completion_safely(self, updated_count, failed_updates, total_investments):
        """Safely show price update completion message without causing application crashes"""
        try:
            # Build the completion message
            if updated_count > 0:
                message = f"Price Update Complete!\n\n"
                message += f"📊 Summary:\n"
                message += f"• Total investments: {total_investments}\n"
                message += f"• Successfully updated: {updated_count}\n"
                message += f"• Failed to update: {len(failed_updates)}\n"

                # Check if CSV save had issues
                if hasattr(self, '_csv_save_error'):
                    message += f"⚠️ Data updated in memory but CSV save failed\n"
                    message += f"   Error: {self._csv_save_error}\n"
                    delattr(self, '_csv_save_error')  # Clean up the error flag
                else:
                    message += f"• All investment data saved to CSV\n"

                if failed_updates:
                    message += f"\n❌ Failed updates:\n"
                    message += "\n".join(failed_updates[:5])  # Show first 5 failures
                    if len(failed_updates) > 5:
                        message += f"\n... and {len(failed_updates) - 5} more"

                self.logger.info(f"✅ {message}")

                # Show message immediately without timer to avoid crashes
                self._safe_show_message("Price Update Complete", message, "information")

            else:
                message = f"Price Update Complete (No New Prices)\n\n"
                message += f"📊 Summary:\n"
                message += f"• Total investments: {total_investments}\n"
                message += f"• Successfully updated: 0\n"
                message += f"• Failed to update: {len(failed_updates)}\n"
                message += f"• All investment data preserved in CSV\n"

                if failed_updates:
                    message += f"\n❌ Issues encountered:\n"
                    message += "\n".join(failed_updates[:5])
                    if len(failed_updates) > 5:
                        message += f"\n... and {len(failed_updates) - 5} more"

                self.logger.info(f"⚠️ {message}")

                # Show message immediately without timer to avoid crashes
                self._safe_show_message("Price Update Results", message, "warning")

        except Exception as e:
            self.logger.error(f"Error showing completion message: {e}")
            # Fallback to just logging if message display fails
            self.logger.info(f"Price update completed: {updated_count} updated, {len(failed_updates)} failed")

    def _safe_show_message(self, title, message, message_type="information"):
        """Safely show a message dialog with comprehensive error handling"""
        try:
            # Always log the message first for debugging
            self.logger.info(f"Message ({title}): {message}")

            # Multiple safety checks to prevent crashes
            if getattr(self, '_closing', False):
                self.logger.debug("Widget is closing, skipping message display")
                return

            # Simplified approach - just use None as parent to avoid widget state issues
            # This is the safest approach to prevent memory access violations
            parent = None

            # Show the message dialog with None parent (creates independent dialog)
            if message_type == "information":
                QMessageBox.information(parent, title, message)
            elif message_type == "warning":
                QMessageBox.warning(parent, title, message)
            elif message_type == "error":
                QMessageBox.critical(parent, title, message)
            else:
                QMessageBox.information(parent, title, message)

        except Exception as e:
            self.logger.error(f"Error displaying message dialog: {e}")
            # If dialog fails, at least log the message
            self.logger.info(f"Fallback - Message ({title}): {message}")

            # Try to show a simple notification as fallback
            try:
                print(f"NOTIFICATION: {title} - {message}")
            except:
                pass

    def _show_error_safely(self, error_message):
        """Safely show an error message without causing crashes"""
        try:
            self.logger.error(error_message)
            # Show error immediately without timer to avoid crashes
            self._safe_show_message("Error", error_message, "error")
        except Exception as e:
            self.logger.error(f"Error showing error message: {e}")
            self.logger.error(f"Original error: {error_message}")

    def update_portfolio_summary(self):
        """Update the portfolio summary display"""
        if not hasattr(self, 'mutual_funds_stocks') or not self.mutual_funds_stocks:
            self.total_portfolio_label.setText("Total Portfolio Value: ₹0.00")
            return

        total_current_value = 0.0
        total_invested_value = 0.0

        for fund in self.mutual_funds_stocks:
            if fund.current_amount > 0:
                total_current_value += fund.current_amount
            if fund.amount > 0:
                total_invested_value += fund.amount

        # Calculate overall profit/loss
        profit_loss = total_current_value - total_invested_value
        profit_loss_pct = (profit_loss / total_invested_value * 100) if total_invested_value > 0 else 0

        # Update display with color coding
        if profit_loss >= 0:
            color = "#2E7D32"  # Green for profit
            sign = "+"
        else:
            color = "#C62828"  # Red for loss
            sign = ""

        self.total_portfolio_label.setText(
            f"Total Portfolio Value: ₹{total_current_value:,.2f} "
            f"({sign}₹{profit_loss:,.2f}, {sign}{profit_loss_pct:.2f}%)"
        )
        self.total_portfolio_label.setStyleSheet(f"color: {color}; padding: 5px; font-weight: bold;")

    def calculate_portfolio_allocations(self):
        """Calculate allocation percentages for all investments"""
        if not hasattr(self, 'mutual_funds_stocks') or not self.mutual_funds_stocks:
            return

        self.logger.debug("🔢 Starting portfolio allocation calculation...")

        # Calculate current market values for each investment
        total_current_value = 0.0
        investment_values = []

        for fund in self.mutual_funds_stocks:
            # Calculate current market value: current_price × units
            if fund.current_price > 0 and fund.units > 0:
                current_market_value = fund.current_price * fund.units
                investment_values.append((fund, current_market_value, 'current'))
                total_current_value += current_market_value
                self.logger.debug(f"📊 {fund.symbol}: Market Value = ₹{current_market_value:,.2f} (₹{fund.current_price:.2f} × {fund.units:.3f})")
            elif fund.amount > 0:
                # Fallback to original investment amount if no current price
                investment_values.append((fund, fund.amount, 'original'))
                total_current_value += fund.amount
                self.logger.debug(f"📊 {fund.symbol}: Original Amount = ₹{fund.amount:,.2f} (no current price)")
            else:
                # No value available
                investment_values.append((fund, 0.0, 'none'))
                self.logger.debug(f"📊 {fund.symbol}: No value available")

        self.logger.info(f"💰 Total Portfolio Value: ₹{total_current_value:,.2f}")

        # Calculate allocation percentages
        total_percentage = 0.0
        for fund, value, value_type in investment_values:
            if total_current_value > 0 and value > 0:
                allocation_percent = (value / total_current_value) * 100
                fund.allocation_percent = allocation_percent
                total_percentage += allocation_percent
                self.logger.debug(f"📈 {fund.symbol}: {allocation_percent:.2f}% (₹{value:,.2f} / ₹{total_current_value:,.2f}) [{value_type}]")
            else:
                fund.allocation_percent = 0.0
                self.logger.debug(f"📈 {fund.symbol}: 0.00% (no value)")

        self.logger.info(f"✅ Portfolio allocation calculation complete. Total percentage: {total_percentage:.2f}%")

    def get_portfolio_statistics(self):
        """Get comprehensive portfolio statistics"""
        if not hasattr(self, 'mutual_funds_stocks') or not self.mutual_funds_stocks:
            return {
                'total_invested': 0.0,
                'total_current': 0.0,
                'total_profit_loss': 0.0,
                'total_profit_loss_pct': 0.0,
                'best_performer': None,
                'worst_performer': None,
                'stale_prices_count': 0
            }

        total_invested = sum(fund.amount for fund in self.mutual_funds_stocks if fund.amount > 0)
        total_current = sum(fund.current_amount for fund in self.mutual_funds_stocks if fund.current_amount > 0)
        total_profit_loss = total_current - total_invested
        total_profit_loss_pct = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0

        # Find best and worst performers
        performers = []
        stale_prices_count = 0

        for fund in self.mutual_funds_stocks:
            if fund.amount > 0 and fund.current_amount > 0:
                pct_change = fund.get_profit_loss_percentage()
                performers.append((fund, pct_change))

            if fund.is_price_stale():
                stale_prices_count += 1

        performers.sort(key=lambda x: x[1], reverse=True)

        return {
            'total_invested': total_invested,
            'total_current': total_current,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_pct': total_profit_loss_pct,
            'best_performer': performers[0] if performers else None,
            'worst_performer': performers[-1] if performers else None,
            'stale_prices_count': stale_prices_count,
            'total_investments': len(self.mutual_funds_stocks)
        }

    def update_single_price(self, fund_index):
        """Update price for a single investment"""
        if not hasattr(self, 'mutual_funds_stocks') or fund_index >= len(self.mutual_funds_stocks):
            return

        fund = self.mutual_funds_stocks[fund_index]
        if not fund.symbol:
            self._safe_show_message("No Symbol", f"No symbol defined for {fund.name}", "warning")
            return

        try:
            # Show loading state
            original_text = self.update_prices_btn.text()
            self.update_prices_btn.setText("🔄 Updating...")
            self.update_prices_btn.setEnabled(False)

            # Fetch price
            new_price = price_fetcher.get_current_price(fund.symbol)

            if new_price is not None:
                fund.update_current_price(new_price)
                self.csv_manager.save_data('mutual_funds_stocks', self.mutual_funds_stocks)
                self.refresh_mutual_funds_table()
                self.update_portfolio_summary()

                self._safe_show_message(
                    "Price Updated",
                    f"Updated {fund.name}: ₹{new_price:.2f}",
                    "information"
                )
            else:
                self._safe_show_message(
                    "Update Failed",
                    f"Could not fetch price for {fund.symbol}",
                    "warning"
                )

        except Exception as e:
            self.logger.error(f"Error updating single price: {e}")
            self._safe_show_message("Error", f"Error updating price: {str(e)}", "error")

        finally:
            # Restore button state
            self.update_prices_btn.setText(original_text)
            self.update_prices_btn.setEnabled(True)

    def update_last_price_update_display(self):
        """Update the display showing when prices were last updated"""
        if not hasattr(self, 'mutual_funds_stocks') or not self.mutual_funds_stocks:
            self.last_update_label.setText("Last Updated: No data")
            return

        # Find the most recent price update
        latest_update = None
        updated_count = 0

        for fund in self.mutual_funds_stocks:
            if fund.price_last_updated:
                updated_count += 1
                if latest_update is None or fund.price_last_updated > latest_update:
                    latest_update = fund.price_last_updated

        if latest_update:
            # Calculate time since last update
            time_diff = datetime.now() - latest_update

            if time_diff.days > 0:
                time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff.seconds > 60:
                minutes = time_diff.seconds // 60
                time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                time_str = "Just now"

            # Color code based on staleness
            if time_diff.days > 1:
                color = "#C62828"  # Red for very stale
            elif time_diff.days > 0 or time_diff.seconds > 86400:  # > 24 hours
                color = "#FF8F00"  # Orange for stale
            else:
                color = "#2E7D32"  # Green for fresh

            self.last_update_label.setText(f"Last Updated: {time_str} ({updated_count}/{len(self.mutual_funds_stocks)} items)")
            self.last_update_label.setStyleSheet(f"color: {color}; padding: 5px;")
        else:
            self.last_update_label.setText("Last Updated: Never")
            self.last_update_label.setStyleSheet("color: #666; padding: 5px;")

    def get_price_update_statistics(self):
        """Get statistics about price updates"""
        if not hasattr(self, 'mutual_funds_stocks') or not self.mutual_funds_stocks:
            return {
                'total_investments': 0,
                'with_prices': 0,
                'stale_prices': 0,
                'never_updated': 0,
                'last_update': None
            }

        total = len(self.mutual_funds_stocks)
        with_prices = 0
        stale_prices = 0
        never_updated = 0
        latest_update = None

        for fund in self.mutual_funds_stocks:
            if fund.current_price > 0:
                with_prices += 1

                if fund.is_price_stale():
                    stale_prices += 1

                if fund.price_last_updated:
                    if latest_update is None or fund.price_last_updated > latest_update:
                        latest_update = fund.price_last_updated
            else:
                never_updated += 1

        return {
            'total_investments': total,
            'with_prices': with_prices,
            'stale_prices': stale_prices,
            'never_updated': never_updated,
            'last_update': latest_update
        }


class InvestmentDetailsDialog(QDialog):
    """Dialog for displaying detailed investment information with multiple tabs"""

    def __init__(self, fund: MutualFundStock, parent=None):
        super().__init__(parent)
        self.fund = fund
        self.detailed_data = {}
        self.loading_widget = None
        self.is_loading = False

        # Initialize logger
        import logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.setup_ui()
        self.setup_progressive_fetcher()

        # Flag to track if dialog is being closed
        self._closing = False

        # Flag to track price update state
        self._price_update_in_progress = False

    def closeEvent(self, event):
        """Handle dialog close event to prevent widget access after deletion"""
        self.logger.info("Dialog close event triggered")

        # If data is still loading, ask for confirmation
        if self.is_loading and not getattr(self, '_force_close', False):
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Data Loading in Progress",
                "Investment data is still being loaded. Closing now will cancel the operation.\n\nAre you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

        self._closing = True

        # Clean up price update thread if running
        try:
            self._cleanup_price_update_thread()
            self.logger.info("Price update thread cleanup completed during close")
        except Exception as e:
            self.logger.warning(f"Error during price update thread cleanup: {e}")

        # Disconnect signals to prevent callbacks after dialog destruction
        if hasattr(self, 'fetcher') and self.fetcher:
            try:
                # Cancel ongoing data fetching
                self.fetcher.cancel_requested = True

                # Disconnect all signals to prevent callbacks
                self.fetcher.progress_updated.disconnect(self.on_progress_updated)
                self.fetcher.data_category_completed.disconnect(self.on_category_completed)
                self.fetcher.all_data_loaded.disconnect(self.on_data_loaded)
                self.fetcher.error_occurred.disconnect(self.on_fetch_error)

                self.logger.info("Cancelled ongoing data fetching and disconnected signals")
            except Exception as e:
                self.logger.warning(f"Error during fetcher cleanup: {e}")

        # Stop any timers
        if hasattr(self, 'token_refresh_timer'):
            try:
                self.token_refresh_timer.stop()
            except Exception:
                pass

        # Hide loading widget safely
        if hasattr(self, 'loading_widget') and self.loading_widget:
            try:
                self.loading_widget.setVisible(False)
            except RuntimeError:
                pass  # Widget already deleted

        self.logger.info("Dialog close event completed")
        super().closeEvent(event)

    def safe_set_widget_text(self, widget, text: str) -> bool:
        """Safely set text on a widget, handling deleted widgets gracefully"""
        # Check if dialog is being closed
        if getattr(self, '_closing', False):
            self.logger.debug("Dialog is closing, skipping widget text update")
            return False

        try:
            if widget is not None:
                widget.setText(text)
                return True
        except RuntimeError:
            self.logger.warning(f"Widget was deleted, skipping text update: {text[:50]}...")
        except Exception as e:
            self.logger.error(f"Error setting widget text: {e}")
        return False

    def safe_table_operation(self, table_widget, operation_name: str, operation_func) -> bool:
        """Safely perform table operations, handling deleted widgets gracefully"""
        # Check if dialog is being closed
        if getattr(self, '_closing', False):
            self.logger.debug(f"Dialog is closing, skipping table operation: {operation_name}")
            return False

        try:
            if table_widget is not None:
                operation_func()
                return True
        except RuntimeError as e:
            if "already deleted" in str(e):
                self.logger.warning(f"Table widget was deleted, skipping {operation_name}: {str(e)}")
            else:
                self.logger.error(f"RuntimeError in table operation {operation_name}: {e}")
        except Exception as e:
            self.logger.error(f"Error in table operation {operation_name}: {e}")
        return False

    def safe_set_table_row_count(self, table_widget, row_count: int) -> bool:
        """Safely set table row count"""
        return self.safe_table_operation(
            table_widget,
            f"setRowCount({row_count})",
            lambda: table_widget.setRowCount(row_count)
        )

    def safe_set_table_item(self, table_widget, row: int, col: int, item) -> bool:
        """Safely set table item"""
        return self.safe_table_operation(
            table_widget,
            f"setItem({row}, {col})",
            lambda: table_widget.setItem(row, col, item)
        )
        self.load_investment_data()

    def setup_ui(self):
        """Setup the dialog UI with tabbed interface"""
        self.setWindowTitle(f"Investment Details - {self.fund.name}")
        self.setModal(True)
        self.resize(1200, 800)

        layout = QVBoxLayout(self)

        # Header with investment basic info
        self.create_header(layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("investmentDetailsTabs")

        # Create all tabs
        self.create_real_time_tab()
        self.create_historical_tab()
        self.create_performance_tab()
        self.create_financials_tab()
        self.create_portfolio_tab()
        self.create_regulatory_tab()
        self.create_dividends_tab()
        self.create_fees_tab()
        self.create_data_sources_tab()

        layout.addWidget(self.tab_widget)

        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_btn = QPushButton("🔄 Refresh Data")
        refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(refresh_btn)

        # Debug network button (for troubleshooting)
        debug_btn = QPushButton("🔍 Debug Network")
        debug_btn.clicked.connect(self.debug_network_connectivity)
        button_layout.addWidget(debug_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def setup_progressive_fetcher(self):
        """Setup progressive data fetcher with signal connections"""
        self.fetcher = progressive_fetcher

        # Connect signals
        self.fetcher.progress_updated.connect(self.on_progress_updated)
        self.fetcher.data_category_completed.connect(self.on_category_completed)
        self.fetcher.all_data_loaded.connect(self.on_data_loaded)
        self.fetcher.error_occurred.connect(self.on_fetch_error)

    def create_header(self, layout):
        """Create header with basic investment information"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header_frame)

        # Title
        title_label = QLabel(f"📈 {self.fund.name}")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)

        # Basic info in a grid
        info_layout = QGridLayout()

        info_layout.addWidget(QLabel("Symbol:"), 0, 0)
        info_layout.addWidget(QLabel(self.fund.symbol), 0, 1)

        info_layout.addWidget(QLabel("Category:"), 0, 2)
        info_layout.addWidget(QLabel(self.fund.category), 0, 3)

        info_layout.addWidget(QLabel("Sub Category:"), 1, 0)
        info_layout.addWidget(QLabel(self.fund.sub_category), 1, 1)

        info_layout.addWidget(QLabel("Units:"), 1, 2)
        info_layout.addWidget(QLabel(f"{self.fund.units:.2f}"), 1, 3)

        header_layout.addLayout(info_layout)
        layout.addWidget(header_frame)

    def create_real_time_tab(self):
        """Create Tab 1: Real-time Data"""
        self.real_time_tab = QWidget()
        layout = QVBoxLayout(self.real_time_tab)

        # Status indicator
        self.real_time_status = QLabel("Loading real-time data...")
        layout.addWidget(self.real_time_status)

        # Real-time data table
        self.real_time_table = QTableWidget()
        self.real_time_table.setColumnCount(2)
        self.real_time_table.setHorizontalHeaderLabels(['Metric', 'Value'])
        self.real_time_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.real_time_table)

        self.tab_widget.addTab(self.real_time_tab, "📊 Real-time Data")

    def create_historical_tab(self):
        """Create Tab 2: Historical Prices"""
        self.historical_tab = QWidget()
        layout = QVBoxLayout(self.historical_tab)

        # Status indicator
        self.historical_status = QLabel("Loading historical data...")
        layout.addWidget(self.historical_status)

        # Period selector
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Period:"))

        self.period_combo = QComboBox()
        self.period_combo.addItems(['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'])
        self.period_combo.setCurrentText('1y')
        self.period_combo.currentTextChanged.connect(self.load_historical_data)
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()

        layout.addLayout(period_layout)

        # Historical data table
        self.historical_table = QTableWidget()
        self.historical_table.setColumnCount(7)
        self.historical_table.setHorizontalHeaderLabels([
            'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change %'
        ])
        self.historical_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.historical_table)

        self.tab_widget.addTab(self.historical_tab, "📈 Historical Prices")

    def create_performance_tab(self):
        """Create Tab 3: Performance"""
        self.performance_tab = QWidget()
        layout = QVBoxLayout(self.performance_tab)

        # Status indicator
        self.performance_status = QLabel("Loading performance data...")
        layout.addWidget(self.performance_status)

        # Performance metrics table
        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(2)
        self.performance_table.setHorizontalHeaderLabels(['Metric', 'Value'])
        self.performance_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.performance_table)

        self.tab_widget.addTab(self.performance_tab, "📊 Performance")

    def create_financials_tab(self):
        """Create Tab 4: Financials"""
        self.financials_tab = QWidget()
        layout = QVBoxLayout(self.financials_tab)

        # Status indicator
        self.financials_status = QLabel("Loading financial data...")
        layout.addWidget(self.financials_status)

        # Financials table
        self.financials_table = QTableWidget()
        self.financials_table.setColumnCount(2)
        self.financials_table.setHorizontalHeaderLabels(['Metric', 'Value'])
        self.financials_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.financials_table)

        self.tab_widget.addTab(self.financials_tab, "💰 Financials")

    def create_portfolio_tab(self):
        """Create Tab 5: Portfolio (Stocks only)"""
        self.portfolio_tab = QWidget()
        layout = QVBoxLayout(self.portfolio_tab)

        # Status indicator
        self.portfolio_status = QLabel("Loading portfolio data...")
        layout.addWidget(self.portfolio_status)

        # Portfolio data table
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(2)
        self.portfolio_table.setHorizontalHeaderLabels(['Attribute', 'Value'])
        self.portfolio_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.portfolio_table)

        self.tab_widget.addTab(self.portfolio_tab, "📊 Portfolio")

    def create_regulatory_tab(self):
        """Create Tab 6: Regulatory Filings"""
        self.regulatory_tab = QWidget()
        layout = QVBoxLayout(self.regulatory_tab)

        # Status indicator
        self.regulatory_status = QLabel("Loading regulatory data...")
        layout.addWidget(self.regulatory_status)

        # Regulatory data display
        self.regulatory_text = QTextEdit()
        self.regulatory_text.setReadOnly(True)
        layout.addWidget(self.regulatory_text)

        self.tab_widget.addTab(self.regulatory_tab, "📋 Regulatory Filings")

    def create_dividends_tab(self):
        """Create Tab 7: Dividends"""
        self.dividends_tab = QWidget()
        layout = QVBoxLayout(self.dividends_tab)

        # Status indicator
        self.dividends_status = QLabel("Loading dividend data...")
        layout.addWidget(self.dividends_status)

        # Dividend summary
        summary_layout = QHBoxLayout()
        self.dividend_yield_label = QLabel("Dividend Yield: N/A")
        self.dividend_rate_label = QLabel("Dividend Rate: N/A")
        summary_layout.addWidget(self.dividend_yield_label)
        summary_layout.addWidget(self.dividend_rate_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Dividend history table
        self.dividends_table = QTableWidget()
        self.dividends_table.setColumnCount(2)
        self.dividends_table.setHorizontalHeaderLabels(['Date', 'Amount'])
        self.dividends_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.dividends_table)

        self.tab_widget.addTab(self.dividends_tab, "💰 Dividends")

    def create_fees_tab(self):
        """Create Tab 8: Fees/Expense Ratio (Mutual Funds only)"""
        self.fees_tab = QWidget()
        layout = QVBoxLayout(self.fees_tab)

        # Status indicator
        self.fees_status = QLabel("Loading fees data...")
        layout.addWidget(self.fees_status)

        # Fees data table
        self.fees_table = QTableWidget()
        self.fees_table.setColumnCount(2)
        self.fees_table.setHorizontalHeaderLabels(['Fee Type', 'Value'])
        self.fees_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.fees_table)

        self.tab_widget.addTab(self.fees_tab, "💳 Fees/Expense Ratio")

    def create_data_sources_tab(self):
        """Create Tab 9: Data Sources Information"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Status indicator
        self.data_sources_status = QLabel("Loading data sources information...")
        layout.addWidget(self.data_sources_status)

        # Symbol information section
        symbol_frame = QFrame()
        symbol_frame.setFrameStyle(QFrame.StyledPanel)
        symbol_layout = QVBoxLayout(symbol_frame)

        symbol_title = QLabel("🔍 Symbol Recognition")
        symbol_title.setFont(QFont("Arial", 12, QFont.Bold))
        symbol_layout.addWidget(symbol_title)

        self.symbol_info_table = QTableWidget()
        self.symbol_info_table.setColumnCount(2)
        self.symbol_info_table.setHorizontalHeaderLabels(['Property', 'Value'])
        self.symbol_info_table.horizontalHeader().setStretchLastSection(True)
        symbol_layout.addWidget(self.symbol_info_table)

        layout.addWidget(symbol_frame)

        # Data sources section
        sources_frame = QFrame()
        sources_frame.setFrameStyle(QFrame.StyledPanel)
        sources_layout = QVBoxLayout(sources_frame)

        sources_title = QLabel("📊 Data Sources Used")
        sources_title.setFont(QFont("Arial", 12, QFont.Bold))
        sources_layout.addWidget(sources_title)

        self.data_sources_table = QTableWidget()
        self.data_sources_table.setColumnCount(4)
        self.data_sources_table.setHorizontalHeaderLabels(['Category', 'Source', 'Status', 'Last Updated'])
        self.data_sources_table.horizontalHeader().setStretchLastSection(True)
        sources_layout.addWidget(self.data_sources_table)

        layout.addWidget(sources_frame)

        # Source reliability section
        reliability_frame = QFrame()
        reliability_frame.setFrameStyle(QFrame.StyledPanel)
        reliability_layout = QVBoxLayout(reliability_frame)

        reliability_title = QLabel("📈 Source Reliability")
        reliability_title.setFont(QFont("Arial", 12, QFont.Bold))
        reliability_layout.addWidget(reliability_title)

        self.reliability_table = QTableWidget()
        self.reliability_table.setColumnCount(4)
        self.reliability_table.setHorizontalHeaderLabels(['Source', 'Reliability %', 'Records', 'Coverage'])
        self.reliability_table.horizontalHeader().setStretchLastSection(True)
        reliability_layout.addWidget(self.reliability_table)

        layout.addWidget(reliability_frame)

        self.tab_widget.addTab(tab, "🔍 Data Sources")

    def load_investment_data(self, force_refresh: bool = False):
        """Load detailed investment data using progressive fetcher"""
        if self.is_loading:
            return

        self.logger.info(f"Starting data load for symbol: {self.fund.symbol}")
        self.is_loading = True
        self._closing = False  # Reset closing flag when starting new load

        # Show loading widget
        self.show_loading_screen()

        # Start progressive data fetching
        self.fetcher.fetch_investment_data(self.fund.symbol, force_refresh)

    def show_loading_screen(self):
        """Show the loading screen widget"""
        if not self.loading_widget:
            self.loading_widget = InvestmentLoadingWidget(self.fund.symbol, self.fund.name)
            self.loading_widget.cancel_requested.connect(self.cancel_loading)

        # Update freshness information
        freshness_info = self.fetcher.get_data_freshness_info(self.fund.symbol)
        self.loading_widget.update_freshness_info(freshness_info)

        # Update cache status
        cached_count = sum(1 for info in freshness_info.values() if info.get('last_updated'))
        self.loading_widget.update_cache_status(cached_count, len(freshness_info))

        # Set network status
        network_available = self.fetcher.check_network_connectivity()
        if network_available:
            self.loading_widget.set_network_status("Connected", "#4CAF50")
        else:
            self.loading_widget.set_network_status("Offline - using cache", "#FF9800")

        # Replace tab widget with loading widget temporarily
        self.tab_widget.setVisible(False)

        # Add loading widget to layout if not already added
        if self.loading_widget.parent() != self:
            layout = self.layout()
            # Insert loading widget before buttons
            layout.insertWidget(layout.count() - 1, self.loading_widget)

        self.loading_widget.setVisible(True)

    def hide_loading_screen(self):
        """Hide the loading screen and show tabs"""
        # Check if dialog is still valid before hiding loading screen
        if getattr(self, '_closing', False):
            self.logger.debug("Dialog is closing, skipping loading screen hide")
            return

        try:
            if self.loading_widget and not getattr(self, '_closing', False):
                self.loading_widget.setVisible(False)

            # Safely show tab widget
            if hasattr(self, 'tab_widget') and self.tab_widget:
                self.tab_widget.setVisible(True)

        except RuntimeError as e:
            self.logger.warning(f"Widget was deleted while hiding loading screen: {e}")
        except Exception as e:
            self.logger.error(f"Error hiding loading screen: {e}")

        self.is_loading = False

    def cancel_loading(self):
        """Cancel the loading process"""
        self.fetcher.cancel_fetch()
        self.hide_loading_screen()

    def on_progress_updated(self, progress: int, status: str):
        """Handle progress updates from fetcher"""
        # Check if dialog is still valid before updating progress
        if getattr(self, '_closing', False):
            return

        try:
            if self.loading_widget and not getattr(self, '_closing', False):
                self.loading_widget.update_progress(progress, status)
        except RuntimeError:
            self.logger.debug("Loading widget was deleted, skipping progress update")

    def on_category_completed(self, category: str, success: bool):
        """Handle category completion from fetcher"""
        # Check if dialog is still valid before updating category status
        if getattr(self, '_closing', False):
            return

        try:
            if self.loading_widget and not getattr(self, '_closing', False):
                message = "Completed" if success else "Failed"
                self.loading_widget.update_category_status(category, success, message)
        except RuntimeError:
            self.logger.debug("Loading widget was deleted, skipping category status update")

    def on_data_loaded(self, data: dict):
        """Handle data loaded from fetcher"""
        # Check if dialog is being closed before updating UI
        if getattr(self, '_closing', False):
            self.logger.info("Dialog is closing, skipping UI update with fetched data")
            return

        # Check if dialog is still visible and valid
        try:
            if not self.isVisible():
                self.logger.info("Dialog is not visible, skipping UI update")
                return
        except RuntimeError:
            self.logger.warning("Dialog widget was deleted, cannot update UI")
            return

        self.detailed_data = data
        self.update_ui_with_data()

    def on_fetch_error(self, error_message: str):
        """Handle fetch errors"""
        # Check if dialog is still valid before showing error
        if getattr(self, '_closing', False):
            self.logger.info("Dialog is closing, skipping error display")
            return

        try:
            if self.loading_widget and not getattr(self, '_closing', False):
                # Determine error type for better user guidance
                error_type = "Data Loading Error"
                if "network" in error_message.lower() or "connection" in error_message.lower():
                    error_type = "Network Error"
                elif "symbol" in error_message.lower():
                    error_type = "Symbol Error"
                elif "api" in error_message.lower() or "rate" in error_message.lower():
                    error_type = "API Error"

                self.loading_widget.show_detailed_error(error_type, error_message)
        except RuntimeError:
            self.logger.debug("Loading widget was deleted, skipping error display")

        # Only show error dialog if dialog is still valid
        if not getattr(self, '_closing', False):
            self.show_error(error_message)

    def update_ui_with_data(self):
        """Update UI with fetched data"""
        # Double-check if dialog is still valid before UI updates
        if getattr(self, '_closing', False):
            self.logger.info("Dialog is closing, aborting UI update")
            return

        try:
            # Verify dialog is still accessible
            if not self.isVisible():
                self.logger.info("Dialog is not visible, aborting UI update")
                return
        except RuntimeError:
            self.logger.warning("Dialog widget was deleted during UI update")
            return

        self.logger.info("Starting UI update with fetched data")

        # Hide loading screen and show tabs
        self.hide_loading_screen()

        # Update all tabs with data - each method has its own safety checks
        self.populate_real_time_data()
        self.populate_historical_data()
        self.populate_performance_data()
        self.populate_financials_data()
        self.populate_portfolio_data()
        self.populate_regulatory_data()
        self.populate_dividends_data()
        self.populate_fees_data()
        self.populate_data_sources_info()

        # Mark loading as complete
        if self.loading_widget and not getattr(self, '_closing', False):
            try:
                self.loading_widget.set_completed()
                self.logger.info("UI update completed successfully")
            except RuntimeError:
                self.logger.warning("Loading widget was deleted, cannot mark as completed")

        # Mark loading as no longer in progress
        self.is_loading = False

        # Ensure dialog is visible and brought to front after data loading
        try:
            if not getattr(self, '_closing', False):
                self.show()
                self.raise_()
                self.activateWindow()
                self.logger.info("Dialog brought to front after data loading completion")
        except RuntimeError:
            self.logger.warning("Could not bring dialog to front - widget was deleted")

    def populate_real_time_data(self):
        """Populate real-time data tab"""
        real_time_data = self.detailed_data.get('real_time_data', {})

        if not real_time_data.get('available', False):
            # Safely update status widget
            if not self.safe_set_widget_text(getattr(self, 'real_time_status', None),
                                           "❌ Real-time data not available - see detailed explanation below"):
                return

            # Create detailed unavailability explanation
            if hasattr(self, 'real_time_tab') and self.real_time_tab is not None:
                self.create_unavailability_explanation('real_time', self.real_time_tab)
            return

        # Add freshness and source indicator
        status_text = "✅ Real-time data loaded successfully"

        # Add data source information
        data_source = real_time_data.get('data_source', 'Unknown')
        status_text += f" (Source: {data_source})"

        # Add freshness information
        if 'last_updated' in real_time_data:
            try:
                last_updated = datetime.fromisoformat(real_time_data['last_updated'])
                age = datetime.now() - last_updated
                if age.total_seconds() < 300:  # Less than 5 minutes
                    status_text += " - Fresh"
                elif age.total_seconds() < 3600:  # Less than 1 hour
                    status_text += f" - {int(age.total_seconds() / 60)} min ago"
                else:
                    status_text += f" - {int(age.total_seconds() / 3600)} hr ago"
            except:
                pass

        if 'staleness_warning' in real_time_data:
            status_text += f" ⚠️ {real_time_data['staleness_warning']}"

        self.safe_set_widget_text(getattr(self, 'real_time_status', None), status_text)

        # Populate table
        metrics = [
            ('Current Price', real_time_data.get('current_price')),
            ('NAV', real_time_data.get('nav')),
            ('Previous Close', real_time_data.get('previous_close')),
            ('Open', real_time_data.get('open')),
            ('Day High', real_time_data.get('day_high')),
            ('Day Low', real_time_data.get('day_low')),
            ('Volume', real_time_data.get('volume')),
            ('Market Cap', real_time_data.get('market_cap')),
            ('Currency', real_time_data.get('currency'))
        ]

        # Safely set table row count
        if not self.safe_set_table_row_count(getattr(self, 'real_time_table', None), len(metrics)):
            return

        for i, (metric, value) in enumerate(metrics):
            # Safely set metric name
            if not self.safe_set_table_item(getattr(self, 'real_time_table', None), i, 0, QTableWidgetItem(metric)):
                return

            if value is not None:
                if isinstance(value, (int, float)):
                    if metric in ['Current Price', 'NAV', 'Previous Close', 'Open', 'Day High', 'Day Low']:
                        formatted_value = f"₹{value:.2f}"
                    elif metric == 'Market Cap':
                        formatted_value = f"₹{value:,.0f}"
                    elif metric == 'Volume':
                        formatted_value = f"{value:,}"
                    else:
                        formatted_value = str(value)
                else:
                    formatted_value = str(value)
            else:
                formatted_value = "N/A"

            # Safely set formatted value
            if not self.safe_set_table_item(getattr(self, 'real_time_table', None), i, 1, QTableWidgetItem(formatted_value)):
                return

    def populate_historical_data(self):
        """Populate historical data tab"""
        historical_data = self.detailed_data.get('historical_data', {})

        if not historical_data.get('available', False):
            # Safely update status widget
            if not self.safe_set_widget_text(getattr(self, 'historical_status', None),
                                           f"❌ Historical data not available: {historical_data.get('error', 'Unknown error')}"):
                return
            return

        self.safe_set_widget_text(getattr(self, 'historical_status', None),
                                 f"✅ Historical data loaded ({historical_data.get('total_records', 0)} records)")

        # Populate table
        data_list = historical_data.get('data', [])

        # Safely set table row count
        if not self.safe_set_table_row_count(getattr(self, 'historical_table', None), len(data_list)):
            return

        for i, record in enumerate(data_list):
            # Safely set each column
            if not self.safe_set_table_item(getattr(self, 'historical_table', None), i, 0, QTableWidgetItem(record.get('date', ''))):
                return
            if not self.safe_set_table_item(getattr(self, 'historical_table', None), i, 1, QTableWidgetItem(f"₹{record.get('open', 0):.2f}")):
                return
            if not self.safe_set_table_item(getattr(self, 'historical_table', None), i, 2, QTableWidgetItem(f"₹{record.get('high', 0):.2f}")):
                return
            if not self.safe_set_table_item(getattr(self, 'historical_table', None), i, 3, QTableWidgetItem(f"₹{record.get('low', 0):.2f}")):
                return
            if not self.safe_set_table_item(getattr(self, 'historical_table', None), i, 4, QTableWidgetItem(f"₹{record.get('close', 0):.2f}")):
                return
            if not self.safe_set_table_item(getattr(self, 'historical_table', None), i, 5, QTableWidgetItem(f"{record.get('volume', 0):,}")):
                return

            change_percent = record.get('change_percent', 0)
            change_text = f"{change_percent:+.2f}%"
            change_item = QTableWidgetItem(change_text)
            if change_percent > 0:
                change_item.setForeground(QColor('green'))
            elif change_percent < 0:
                change_item.setForeground(QColor('red'))

            if not self.safe_set_table_item(getattr(self, 'historical_table', None), i, 6, change_item):
                return

    def populate_performance_data(self):
        """Populate performance data tab"""
        performance_data = self.detailed_data.get('performance_data', {})

        if not performance_data.get('available', False):
            if not self.safe_set_widget_text(getattr(self, 'performance_status', None),
                                           "❌ Performance data not available - see detailed explanation below"):
                return
            # Create detailed unavailability explanation
            if hasattr(self, 'performance_tab') and self.performance_tab is not None:
                self.create_unavailability_explanation('performance', self.performance_tab)
            return

        self.safe_set_widget_text(getattr(self, 'performance_status', None), "✅ Performance data loaded successfully")

        # Populate table
        metrics = [
            ('Beta', performance_data.get('beta')),
            ('Trailing P/E', performance_data.get('trailing_pe')),
            ('Forward P/E', performance_data.get('forward_pe')),
            ('Price to Book', performance_data.get('price_to_book')),
            ('Return on Equity', performance_data.get('return_on_equity')),
            ('Return on Assets', performance_data.get('return_on_assets')),
            ('Profit Margins', performance_data.get('profit_margins')),
            ('Operating Margins', performance_data.get('operating_margins')),
            ('Earnings Growth', performance_data.get('earnings_growth')),
            ('Revenue Growth', performance_data.get('revenue_growth')),
            ('52 Week High', performance_data.get('52_week_high')),
            ('52 Week Low', performance_data.get('52_week_low')),
            ('50 Day Average', performance_data.get('moving_avg_50')),
            ('200 Day Average', performance_data.get('moving_avg_200'))
        ]

        # Safely set table row count
        if not self.safe_set_table_row_count(getattr(self, 'performance_table', None), len(metrics)):
            return

        for i, (metric, value) in enumerate(metrics):
            # Safely set metric name
            if not self.safe_set_table_item(getattr(self, 'performance_table', None), i, 0, QTableWidgetItem(metric)):
                return

            if value is not None:
                if isinstance(value, (int, float)):
                    if metric in ['52 Week High', '52 Week Low', '50 Day Average', '200 Day Average']:
                        formatted_value = f"₹{value:.2f}"
                    elif metric in ['Return on Equity', 'Return on Assets', 'Profit Margins', 'Operating Margins', 'Earnings Growth', 'Revenue Growth']:
                        formatted_value = f"{value:.2%}" if value < 1 else f"{value:.2f}%"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
            else:
                formatted_value = "N/A"

            # Safely set formatted value
            if not self.safe_set_table_item(getattr(self, 'performance_table', None), i, 1, QTableWidgetItem(formatted_value)):
                return

    def populate_financials_data(self):
        """Populate financials data tab"""
        financial_data = self.detailed_data.get('financial_data', {})

        if not financial_data.get('available', False):
            if not self.safe_set_widget_text(getattr(self, 'financials_status', None),
                                           "❌ Financial data not available - see detailed explanation below"):
                return
            # Create detailed unavailability explanation
            if hasattr(self, 'financials_tab') and self.financials_tab is not None:
                self.create_unavailability_explanation('financial', self.financials_tab)
            return

        self.safe_set_widget_text(getattr(self, 'financials_status', None), "✅ Financial data loaded successfully")

        # Populate table
        metrics = [
            ('Total Revenue', financial_data.get('total_revenue')),
            ('Gross Profits', financial_data.get('gross_profits')),
            ('EBITDA', financial_data.get('ebitda')),
            ('Net Income', financial_data.get('net_income')),
            ('Total Cash', financial_data.get('total_cash')),
            ('Total Debt', financial_data.get('total_debt')),
            ('Book Value', financial_data.get('book_value')),
            ('Shares Outstanding', financial_data.get('shares_outstanding')),
            ('Enterprise Value', financial_data.get('enterprise_value')),
            ('Price to Sales', financial_data.get('price_to_sales')),
            ('Enterprise to Revenue', financial_data.get('enterprise_to_revenue')),
            ('Enterprise to EBITDA', financial_data.get('enterprise_to_ebitda')),
            ('Debt to Equity', financial_data.get('debt_to_equity')),
            ('Current Ratio', financial_data.get('current_ratio')),
            ('Quick Ratio', financial_data.get('quick_ratio'))
        ]

        # Safely set table row count
        if not self.safe_set_table_row_count(getattr(self, 'financials_table', None), len(metrics)):
            return

        for i, (metric, value) in enumerate(metrics):
            # Safely set metric name
            if not self.safe_set_table_item(getattr(self, 'financials_table', None), i, 0, QTableWidgetItem(metric)):
                return

            if value is not None:
                if isinstance(value, (int, float)):
                    if metric in ['Total Revenue', 'Gross Profits', 'EBITDA', 'Net Income', 'Total Cash', 'Total Debt', 'Enterprise Value']:
                        formatted_value = f"₹{value:,.0f}"
                    elif metric == 'Shares Outstanding':
                        formatted_value = f"{value:,.0f}"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
            else:
                formatted_value = "N/A"

            # Safely set formatted value
            if not self.safe_set_table_item(getattr(self, 'financials_table', None), i, 1, QTableWidgetItem(formatted_value)):
                return

    def load_historical_data(self):
        """Load historical data for selected period with progress indicator"""
        period = self.period_combo.currentText()

        # Initialize progress tracking
        self.historical_progress_step = 0
        self.historical_progress_steps = [
            f"Preparing to fetch historical data for {period} period...",
            "Connecting to data source...",
            f"Fetching historical data from Yahoo Finance...",
            "Processing and validating data...",
            "Updating charts and tables...",
            "Historical data loaded successfully"
        ]

        # Start progress indicator
        self.update_historical_progress()

        # Disable period combo during loading
        self.period_combo.setEnabled(False)

        # Start background thread to fetch historical data
        thread = threading.Thread(target=self._fetch_historical_background, args=(period,))
        thread.daemon = True
        thread.start()

    def _fetch_historical_background(self, period):
        """Fetch historical data in background thread with progress updates"""
        try:
            # Step 1: Connecting to data source
            self.advance_historical_progress()

            # Step 2: Fetching data
            import time
            time.sleep(0.1)  # Brief delay for UI responsiveness
            self.advance_historical_progress()

            # Actual data fetching - use the progressive fetcher's price fetcher
            if hasattr(self, 'fetcher') and hasattr(self.fetcher, 'fetcher'):
                historical_data = self.fetcher.fetcher._get_historical_data(self.fund.symbol, period)
            else:
                # Fallback: create a temporary price fetcher
                from src.modules.investments.price_fetcher import PriceFetcher
                temp_fetcher = PriceFetcher()
                historical_data = temp_fetcher._get_historical_data(self.fund.symbol, period)

            # Step 3: Processing data
            self.advance_historical_progress()

            # Store the data
            self.detailed_data['historical_data'] = historical_data

            # Step 4: Updating UI
            self.advance_historical_progress()

            # Step 5: Complete
            self.complete_historical_loading()

        except Exception as e:
            self.handle_historical_error(str(e))

    def update_historical_progress(self):
        """Update historical data loading progress"""
        if hasattr(self, 'historical_progress_step') and hasattr(self, 'historical_progress_steps'):
            if self.historical_progress_step < len(self.historical_progress_steps):
                message = self.historical_progress_steps[self.historical_progress_step]
                self.safe_set_widget_text(getattr(self, 'historical_status', None), f"🔄 {message}")

    def advance_historical_progress(self):
        """Advance to next progress step"""
        if hasattr(self, 'historical_progress_step'):
            self.historical_progress_step += 1
            self.update_historical_progress()

    def complete_historical_loading(self):
        """Complete historical data loading"""
        # Final progress step
        self.advance_historical_progress()

        # Re-enable period combo
        self.period_combo.setEnabled(True)

        # Populate the data
        self.populate_historical_data()

    def handle_historical_error(self, error_message):
        """Handle historical data loading error"""
        self.safe_set_widget_text(getattr(self, 'historical_status', None),
                                 f"❌ Error loading historical data: {error_message}")
        if hasattr(self, 'period_combo') and self.period_combo is not None:
            try:
                self.period_combo.setEnabled(True)
            except RuntimeError:
                self.logger.warning("Period combo widget was deleted, skipping enable")

        # Create detailed unavailability explanation for historical data
        self.create_unavailability_explanation('historical', self.historical_tab)

    def refresh_data(self):
        """Refresh all data"""
        # Clear local storage cache for this symbol
        investment_data_storage.clear_symbol_data(self.fund.symbol)

        # Clear price fetcher cache
        cache_key = f"detailed_{self.fund.symbol}"
        if cache_key in price_fetcher.detailed_cache:
            del price_fetcher.detailed_cache[cache_key]
        if cache_key in price_fetcher.detailed_cache_expiry:
            del price_fetcher.detailed_cache_expiry[cache_key]

        # Reload data with force refresh
        self.load_investment_data(force_refresh=True)

    def populate_portfolio_data(self):
        """Populate portfolio data tab"""
        portfolio_data = self.detailed_data.get('portfolio_data', {})

        if not portfolio_data.get('available', False):
            if not self.safe_set_widget_text(getattr(self, 'portfolio_status', None),
                                           "❌ Portfolio data not available - see detailed explanation below"):
                return
            # Create detailed unavailability explanation
            if hasattr(self, 'portfolio_tab') and self.portfolio_tab is not None:
                self.create_unavailability_explanation('portfolio', self.portfolio_tab)
            return

        self.safe_set_widget_text(getattr(self, 'portfolio_status', None), "✅ Portfolio data loaded successfully")

        # Populate table
        attributes = [
            ('Sector', portfolio_data.get('sector')),
            ('Industry', portfolio_data.get('industry')),
            ('Full Time Employees', portfolio_data.get('full_time_employees')),
            ('Website', portfolio_data.get('website')),
            ('City', portfolio_data.get('headquarters', {}).get('city')),
            ('State', portfolio_data.get('headquarters', {}).get('state')),
            ('Country', portfolio_data.get('headquarters', {}).get('country'))
        ]

        # Safely set table row count
        if not self.safe_set_table_row_count(getattr(self, 'portfolio_table', None), len(attributes) + 1):  # +1 for business summary
            return

        for i, (attr, value) in enumerate(attributes):
            # Safely set attribute name
            if not self.safe_set_table_item(getattr(self, 'portfolio_table', None), i, 0, QTableWidgetItem(attr)):
                return

            formatted_value = str(value) if value is not None else "N/A"
            if attr == 'Full Time Employees' and value:
                formatted_value = f"{value:,}"

            # Safely set formatted value
            if not self.safe_set_table_item(getattr(self, 'portfolio_table', None), i, 1, QTableWidgetItem(formatted_value)):
                return

        # Add business summary as last row
        if not self.safe_set_table_item(getattr(self, 'portfolio_table', None), len(attributes), 0, QTableWidgetItem("Business Summary")):
            return

        business_summary = portfolio_data.get('business_summary', 'N/A')
        if len(business_summary) > 200:
            business_summary = business_summary[:200] + "..."

        if not self.safe_set_table_item(getattr(self, 'portfolio_table', None), len(attributes), 1, QTableWidgetItem(business_summary)):
            return

    def populate_regulatory_data(self):
        """Populate regulatory data tab"""
        regulatory_data = self.detailed_data.get('regulatory_data', {})

        if not regulatory_data.get('available', False):
            if not self.safe_set_widget_text(getattr(self, 'regulatory_status', None),
                                           f"❌ Regulatory data not available: {regulatory_data.get('error', 'Unknown error')}"):
                return
            return

        self.safe_set_widget_text(getattr(self, 'regulatory_status', None), "✅ Regulatory data loaded successfully")

        # Display regulatory information
        text = "📋 Regulatory Filings and Documents\n\n"
        text += f"Note: {regulatory_data.get('note', 'No additional information available')}\n\n"

        sec_filings = regulatory_data.get('sec_filings', [])
        if sec_filings:
            text += "SEC Filings:\n"
            for filing in sec_filings:
                text += f"• {filing}\n"
        else:
            text += "SEC Filings: No data available\n"

        text += "\n"
        annual_reports = regulatory_data.get('annual_reports', [])
        if annual_reports:
            text += "Annual Reports:\n"
            for report in annual_reports:
                text += f"• {report}\n"
        else:
            text += "Annual Reports: No data available\n"

        text += "\n"
        quarterly_reports = regulatory_data.get('quarterly_reports', [])
        if quarterly_reports:
            text += "Quarterly Reports:\n"
            for report in quarterly_reports:
                text += f"• {report}\n"
        else:
            text += "Quarterly Reports: No data available\n"

        self.safe_set_widget_text(getattr(self, 'regulatory_text', None), text)

    def populate_dividends_data(self):
        """Populate dividends data tab"""
        dividend_data = self.detailed_data.get('dividend_data', {})

        if not dividend_data.get('available', False):
            if not self.safe_set_widget_text(getattr(self, 'dividends_status', None),
                                           "❌ Dividend data not available - see detailed explanation below"):
                return
            # Create detailed unavailability explanation
            if hasattr(self, 'dividends_tab') and self.dividends_tab is not None:
                self.create_unavailability_explanation('dividend', self.dividends_tab)
            return

        self.safe_set_widget_text(getattr(self, 'dividends_status', None), "✅ Dividend data loaded successfully")

        # Update summary labels
        dividend_yield = dividend_data.get('dividend_yield', 0)
        dividend_rate = dividend_data.get('dividend_rate', 0)

        self.safe_set_widget_text(getattr(self, 'dividend_yield_label', None),
                                 f"Dividend Yield: {dividend_yield:.2%}" if dividend_yield else "Dividend Yield: N/A")
        self.safe_set_widget_text(getattr(self, 'dividend_rate_label', None),
                                 f"Dividend Rate: ₹{dividend_rate:.2f}" if dividend_rate else "Dividend Rate: N/A")

        # Populate dividend history table
        dividends = dividend_data.get('dividends', [])

        # Safely set table row count
        if not self.safe_set_table_row_count(getattr(self, 'dividends_table', None), len(dividends)):
            return

        for i, dividend in enumerate(dividends):
            # Safely set dividend date
            if not self.safe_set_table_item(getattr(self, 'dividends_table', None), i, 0, QTableWidgetItem(dividend.get('date', ''))):
                return
            # Safely set dividend amount
            if not self.safe_set_table_item(getattr(self, 'dividends_table', None), i, 1, QTableWidgetItem(f"₹{dividend.get('amount', 0):.2f}")):
                return

    def populate_fees_data(self):
        """Populate fees data tab"""
        fees_data = self.detailed_data.get('fees_data', {})

        if not fees_data.get('available', False):
            if not self.safe_set_widget_text(getattr(self, 'fees_status', None),
                                           "❌ Fees data not available - see detailed explanation below"):
                return
            # Create detailed unavailability explanation
            if hasattr(self, 'fees_tab') and self.fees_tab is not None:
                self.create_unavailability_explanation('fees', self.fees_tab)
            return

        self.safe_set_widget_text(getattr(self, 'fees_status', None), "✅ Fees data loaded successfully")

        # Populate table
        fees = [
            ('Expense Ratio', fees_data.get('expense_ratio')),
            ('Management Fee', fees_data.get('management_fee')),
            ('Front End Load', fees_data.get('front_end_load')),
            ('Back End Load', fees_data.get('back_end_load')),
            ('Annual Holdings Turnover', fees_data.get('annual_holdings_turnover')),
            ('Fund Family', fees_data.get('fund_family')),
            ('Category', fees_data.get('category'))
        ]

        # Safely set table row count
        if not self.safe_set_table_row_count(getattr(self, 'fees_table', None), len(fees)):
            return

        for i, (fee_type, value) in enumerate(fees):
            # Safely set fee type
            if not self.safe_set_table_item(getattr(self, 'fees_table', None), i, 0, QTableWidgetItem(fee_type)):
                return

            if value is not None:
                if isinstance(value, (int, float)) and fee_type in ['Expense Ratio', 'Management Fee', 'Front End Load', 'Back End Load', 'Annual Holdings Turnover']:
                    formatted_value = f"{value:.2%}" if value < 1 else f"{value:.2f}%"
                else:
                    formatted_value = str(value)
            else:
                formatted_value = "N/A"

            # Safely set formatted value
            if not self.safe_set_table_item(getattr(self, 'fees_table', None), i, 1, QTableWidgetItem(formatted_value)):
                return

    def show_error(self, message):
        """Show error message"""
        # Hide loading screen
        self.hide_loading_screen()

        # Show error in all status labels using safe method
        error_text = f"❌ {message}"
        self.safe_set_widget_text(getattr(self, 'real_time_status', None), error_text)
        self.safe_set_widget_text(getattr(self, 'historical_status', None), error_text)
        self.safe_set_widget_text(getattr(self, 'performance_status', None), error_text)
        self.safe_set_widget_text(getattr(self, 'financials_status', None), error_text)
        self.safe_set_widget_text(getattr(self, 'portfolio_status', None), error_text)
        self.safe_set_widget_text(getattr(self, 'regulatory_status', None), error_text)
        self.safe_set_widget_text(getattr(self, 'dividends_status', None), error_text)
        self.safe_set_widget_text(getattr(self, 'fees_status', None), error_text)

        # Show error dialog
        QMessageBox.warning(self, "Data Loading Error", f"Failed to load investment data:\n\n{message}")

    def populate_data_sources_info(self):
        """Populate data sources information tab"""
        try:
            self.safe_set_widget_text(getattr(self, 'data_sources_status', None), "✅ Data sources information loaded")

            # Populate symbol information
            if hasattr(self.fetcher, 'symbol_info') and self.fetcher.symbol_info:
                symbol_info = self.fetcher.symbol_info

                symbol_data = [
                    ('Original Symbol', symbol_info.original_symbol),
                    ('Normalized Symbol', symbol_info.normalized_symbol),
                    ('Symbol Type', symbol_info.symbol_type.value.replace('_', ' ').title()),
                    ('Primary Source', symbol_info.primary_source.value.replace('_', ' ').title()),
                    ('Fallback Sources', ', '.join([s.value.replace('_', ' ').title() for s in symbol_info.fallback_sources])),
                    ('Exchange', symbol_info.exchange or 'N/A'),
                    ('Country', symbol_info.country),
                    ('Recognition Confidence', f"{symbol_info.confidence:.1%}")
                ]

                # Safely set table row count
                if not self.safe_set_table_row_count(getattr(self, 'symbol_info_table', None), len(symbol_data)):
                    return

                for i, (prop, value) in enumerate(symbol_data):
                    # Safely set property name
                    if not self.safe_set_table_item(getattr(self, 'symbol_info_table', None), i, 0, QTableWidgetItem(prop)):
                        return
                    # Safely set property value
                    if not self.safe_set_table_item(getattr(self, 'symbol_info_table', None), i, 1, QTableWidgetItem(str(value))):
                        return

            # Populate data sources used
            if hasattr(self.fetcher, 'successful_sources'):
                sources_data = []
                categories = ['real_time', 'historical', 'performance', 'financial', 'portfolio', 'dividend', 'fees']

                for category in categories:
                    source = self.fetcher.successful_sources.get(category, 'Not fetched')
                    attempted = self.fetcher.data_sources_attempted.get(category, [])

                    # Get last updated info from stored data
                    category_data = self.detailed_data.get(f'{category}_data', {})
                    last_updated = category_data.get('last_updated', 'N/A')
                    if last_updated != 'N/A':
                        try:
                            dt = datetime.fromisoformat(last_updated)
                            last_updated = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            pass

                    status = "✅ Success" if source != 'Not fetched' else "❌ Failed"
                    if attempted and source == 'Not fetched':
                        status = f"❌ Failed ({', '.join(attempted)})"

                    sources_data.append((
                        category.replace('_', ' ').title(),
                        source.replace('_', ' ').title() if source != 'Not fetched' else 'N/A',
                        status,
                        last_updated
                    ))

                # Safely set table row count
                if not self.safe_set_table_row_count(getattr(self, 'data_sources_table', None), len(sources_data)):
                    return

                for i, (category, source, status, updated) in enumerate(sources_data):
                    # Safely set each column
                    if not self.safe_set_table_item(getattr(self, 'data_sources_table', None), i, 0, QTableWidgetItem(category)):
                        return
                    if not self.safe_set_table_item(getattr(self, 'data_sources_table', None), i, 1, QTableWidgetItem(source)):
                        return
                    if not self.safe_set_table_item(getattr(self, 'data_sources_table', None), i, 2, QTableWidgetItem(status)):
                        return
                    if not self.safe_set_table_item(getattr(self, 'data_sources_table', None), i, 3, QTableWidgetItem(updated)):
                        return

            # Populate source reliability information
            try:
                stats = investment_data_storage.get_data_source_statistics(self.fund.symbol)
                reliability_data = []

                for source, count in stats.get('by_source', {}).items():
                    reliability_info = investment_data_storage.get_source_reliability_score(source)
                    reliability_data.append((
                        source,
                        f"{reliability_info.get('reliability_score', 0):.1f}%",
                        str(reliability_info.get('total_records', 0)),
                        f"{reliability_info.get('coverage_percentage', 0):.1f}%"
                    ))

                if reliability_data:
                    # Safely set table row count
                    if not self.safe_set_table_row_count(getattr(self, 'reliability_table', None), len(reliability_data)):
                        return

                    for i, (source, reliability, records, coverage) in enumerate(reliability_data):
                        # Safely set each column
                        if not self.safe_set_table_item(getattr(self, 'reliability_table', None), i, 0, QTableWidgetItem(source)):
                            return
                        if not self.safe_set_table_item(getattr(self, 'reliability_table', None), i, 1, QTableWidgetItem(reliability)):
                            return
                        if not self.safe_set_table_item(getattr(self, 'reliability_table', None), i, 2, QTableWidgetItem(records)):
                            return
                        if not self.safe_set_table_item(getattr(self, 'reliability_table', None), i, 3, QTableWidgetItem(coverage)):
                            return
                else:
                    # Safely set table row count for no data case
                    if not self.safe_set_table_row_count(getattr(self, 'reliability_table', None), 1):
                        return
                    # Safely set no data message
                    if not self.safe_set_table_item(getattr(self, 'reliability_table', None), 0, 0, QTableWidgetItem("No reliability data available")):
                        return
                    if not self.safe_set_table_item(getattr(self, 'reliability_table', None), 0, 1, QTableWidgetItem("N/A")):
                        return
                    if not self.safe_set_table_item(getattr(self, 'reliability_table', None), 0, 2, QTableWidgetItem("N/A")):
                        return
                    if not self.safe_set_table_item(getattr(self, 'reliability_table', None), 0, 3, QTableWidgetItem("N/A")):
                        return

            except Exception as e:
                self.logger.error(f"Error loading reliability data: {e}")
                # Safely set table row count for error case
                if not self.safe_set_table_row_count(getattr(self, 'reliability_table', None), 1):
                    return
                # Safely set error message
                if not self.safe_set_table_item(getattr(self, 'reliability_table', None), 0, 0, QTableWidgetItem("Error loading reliability data")):
                    return
                if not self.safe_set_table_item(getattr(self, 'reliability_table', None), 0, 1, QTableWidgetItem("N/A")):
                    return
                if not self.safe_set_table_item(getattr(self, 'reliability_table', None), 0, 2, QTableWidgetItem("N/A")):
                    return
                if not self.safe_set_table_item(getattr(self, 'reliability_table', None), 0, 3, QTableWidgetItem("N/A")):
                    return

        except Exception as e:
            self.logger.error(f"Error populating data sources info: {e}")
            self.safe_set_widget_text(getattr(self, 'data_sources_status', None),
                                     f"❌ Error loading data sources information: {e}")

    def create_unavailability_explanation(self, category: str, tab_widget: QWidget) -> None:
        """Create and display unavailability explanation for a data category"""
        try:
            # Check if tab widget still exists
            if tab_widget is None:
                self.logger.warning(f"Tab widget for {category} is None, skipping unavailability explanation")
                return

            # Check if widget is still valid (not deleted)
            try:
                # Try to access a basic property to check if widget is still valid
                tab_widget.isVisible()
            except RuntimeError:
                self.logger.warning(f"Tab widget for {category} was deleted, skipping unavailability explanation")
                return
            # Get symbol information
            symbol_info = getattr(self.fetcher, 'symbol_info', None)
            if not symbol_info:
                # Fallback: recognize symbol again
                from .symbol_recognition import symbol_recognizer
                symbol_info = symbol_recognizer.recognize_symbol(self.fund.symbol)

            # Get data sources attempted and last error
            data_sources_attempted = getattr(self.fetcher, 'data_sources_attempted', {}).get(category, [])
            successful_sources = getattr(self.fetcher, 'successful_sources', {})

            # Check if this was marked as "Not applicable"
            if successful_sources.get(category) == 'Not applicable':
                # This is expected - category not supported for this symbol type
                pass

            # Get last error from detailed data
            last_error = None
            if hasattr(self, 'detailed_data'):
                category_data = self.detailed_data.get(f'{category}_data', {})
                if not category_data.get('available', False):
                    last_error = category_data.get('error', 'Unknown error')

            # Get last successful fetch timestamp
            last_successful_fetch = None
            try:
                if category == 'real_time':
                    stored_data = investment_data_storage.load_real_time_data(self.fund.symbol)
                elif category == 'performance':
                    stored_data = investment_data_storage.load_performance_data(self.fund.symbol)
                else:
                    stored_data = None

                if stored_data and stored_data.get('available'):
                    last_updated = stored_data.get('last_updated')
                    if last_updated:
                        try:
                            dt = datetime.fromisoformat(last_updated)
                            last_successful_fetch = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            last_successful_fetch = str(last_updated)
            except Exception as e:
                self.logger.debug(f"Could not get last successful fetch for {category}: {e}")

            # Check network availability
            network_available = getattr(self.fetcher, 'network_available', True)

            # Analyze unavailability
            unavailability_info = data_availability_analyzer.analyze_unavailability(
                symbol=self.fund.symbol,
                symbol_type=symbol_info.symbol_type,
                category=category,
                data_sources_attempted=data_sources_attempted,
                last_error=last_error,
                last_successful_fetch=last_successful_fetch,
                network_available=network_available
            )

            # Clear existing tab content
            layout = tab_widget.layout()
            if layout:
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            else:
                layout = QVBoxLayout(tab_widget)

            # Create unavailability container
            try:
                unavailability_container = UnavailabilityContainer()
                unavailability_container.show_unavailability_info(unavailability_info)

                # Connect signals
                unavailability_container.retry_requested.connect(lambda: self.refresh_data())
                unavailability_container.symbol_suggestion_clicked.connect(self.handle_symbol_suggestion)

                layout.addWidget(unavailability_container)
            except Exception as container_error:
                self.logger.error(f"Error creating unavailability container for {category}: {container_error}")
                # Fallback: create simple error message
                error_label = QLabel(f"❌ {category.replace('_', ' ').title()} data not available")
                error_label.setWordWrap(True)
                error_label.setStyleSheet("color: red; padding: 10px; background-color: #ffe6e6; border: 1px solid #ff9999; border-radius: 5px;")
                layout.addWidget(error_label)

        except Exception as e:
            self.logger.error(f"Error creating unavailability explanation for {category}: {e}")
            # Fallback to simple error message
            self.show_simple_unavailability_message(tab_widget, category, str(e))

    def show_simple_unavailability_message(self, tab_widget: QWidget, category: str, error_msg: str = None):
        """Show a simple unavailability message as fallback"""
        layout = tab_widget.layout()
        if not layout:
            layout = QVBoxLayout(tab_widget)

        # Clear existing content
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create simple message
        message_label = QLabel(f"❌ {category.replace('_', ' ').title()} data is not available")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setFont(QFont("Arial", 12, QFont.Bold))
        message_label.setStyleSheet("color: #666; margin: 20px;")

        if error_msg:
            error_label = QLabel(f"Error: {error_msg}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setFont(QFont("Arial", 10))
            error_label.setStyleSheet("color: #999; margin: 10px;")
            error_label.setWordWrap(True)

        layout.addStretch()
        layout.addWidget(message_label)
        if error_msg:
            layout.addWidget(error_label)
        layout.addStretch()

    def handle_symbol_suggestion(self, suggested_symbol: str):
        """Handle when user clicks on a symbol suggestion"""
        try:
            reply = QMessageBox.question(
                self,
                "Try Suggested Symbol",
                f"Would you like to try fetching data for the suggested symbol '{suggested_symbol}'?\n\n"
                f"This will close the current dialog and you can search for the new symbol.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                # Close current dialog
                self.accept()

                # You could emit a signal here to notify parent to search for new symbol
                # For now, just show a message
                QMessageBox.information(
                    self.parent(),
                    "Symbol Suggestion",
                    f"Please search for '{suggested_symbol}' in the investment list to get data for this symbol."
                )

        except Exception as e:
            self.logger.error(f"Error handling symbol suggestion: {e}")
            QMessageBox.warning(self, "Error", f"Could not process symbol suggestion: {e}")

    def debug_network_connectivity(self):
        """Debug network connectivity issues"""
        try:
            # Force a fresh network check
            network_status = self.fetcher.force_network_check()
            status_details = self.fetcher.get_network_status_details()

            # Get detailed information
            debug_info = f"""🔍 Network Connectivity Debug Information

Symbol: {self.fund.symbol}
Network Available: {'✅ Yes' if network_status else '❌ No'}
Last Check: {status_details.get('last_check', 'Never')}
Cache Age: {status_details.get('cache_age_seconds', 0):.1f} seconds

Data Freshness Information:
"""

            # Add freshness info for each category
            freshness_info = self.fetcher.get_data_freshness_info(self.fund.symbol)
            for category, info in freshness_info.items():
                last_updated = info.get('last_updated', 'Never')
                is_stale = info.get('is_stale', True)
                max_age = info.get('max_age_hours', 0)

                debug_info += f"\n{category.title()}: "
                debug_info += f"{'🔴 Stale' if is_stale else '🟢 Fresh'} "
                debug_info += f"(Last: {last_updated}, Max Age: {max_age}h)"

            # Add network test results
            debug_info += f"\n\nNetwork Test Details:"
            debug_info += f"\nWill perform network check: {'Yes' if status_details.get('will_check_network') else 'No (cached)'}"

            # Show debug dialog
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Network Connectivity Debug")
            msg_box.setText(debug_info)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Retry)
            msg_box.setDefaultButton(QMessageBox.Ok)

            # Add custom buttons
            force_online_btn = msg_box.addButton("Force Online Mode", QMessageBox.ActionRole)
            clear_cache_btn = msg_box.addButton("Clear Cache & Retry", QMessageBox.ActionRole)

            result = msg_box.exec()

            # Handle button clicks
            if msg_box.clickedButton() == force_online_btn:
                # Temporarily override network check
                self.fetcher.network_available = True
                self.fetcher.last_network_check = datetime.now()
                QMessageBox.information(self, "Force Online", "Network status forced to online. Try refreshing data now.")

            elif msg_box.clickedButton() == clear_cache_btn:
                # Clear cache and retry
                self.refresh_data()

            elif result == QMessageBox.Retry:
                # Retry network check
                self.debug_network_connectivity()

        except Exception as e:
            QMessageBox.critical(self, "Debug Error", f"Error during network debug:\n\n{str(e)}")


class PurchaseTransactionDialog(QDialog):
    """Dialog for adding/editing purchase transactions"""

    def __init__(self, transaction=None, mutual_funds=None, parent=None):
        super().__init__(parent)
        self.transaction = transaction if transaction else MutualFundPurchaseHistory()
        self.mutual_funds = mutual_funds if mutual_funds else []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Add Purchase Transaction" if not self.transaction.id else "Edit Purchase Transaction")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Fund selection
        fund_layout = QHBoxLayout()
        fund_layout.addWidget(QLabel("Fund/Stock:"))
        self.fund_combo = QComboBox()
        self.fund_combo.setEditable(False)

        # Populate fund combo
        for fund in self.mutual_funds:
            self.fund_combo.addItem(f"{fund.name} ({fund.symbol})", fund.id)

        fund_layout.addWidget(self.fund_combo)
        layout.addLayout(fund_layout)

        # Transaction type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Transaction Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Buy", "Sell", "Dividend", "Bonus"])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Transaction date
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Transaction Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)

        # Units
        units_layout = QHBoxLayout()
        units_layout.addWidget(QLabel("Units:"))
        self.units_spin = QDoubleSpinBox()
        self.units_spin.setDecimals(3)
        self.units_spin.setMaximum(999999.999)
        self.units_spin.valueChanged.connect(self.calculate_total)
        units_layout.addWidget(self.units_spin)
        layout.addLayout(units_layout)

        # Unit price
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Unit Price (₹):"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setDecimals(2)
        self.price_spin.setMaximum(999999.99)
        self.price_spin.valueChanged.connect(self.calculate_total)
        price_layout.addWidget(self.price_spin)
        layout.addLayout(price_layout)

        # Total amount (calculated)
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Total Amount (₹):"))
        self.total_spin = QDoubleSpinBox()
        self.total_spin.setDecimals(2)
        self.total_spin.setMaximum(9999999.99)
        self.total_spin.setReadOnly(True)
        total_layout.addWidget(self.total_spin)
        layout.addLayout(total_layout)

        # Fees
        fees_layout = QHBoxLayout()
        fees_layout.addWidget(QLabel("Fees (₹):"))
        self.fees_spin = QDoubleSpinBox()
        self.fees_spin.setDecimals(2)
        self.fees_spin.setMaximum(99999.99)
        self.fees_spin.valueChanged.connect(self.calculate_net)
        fees_layout.addWidget(self.fees_spin)
        layout.addLayout(fees_layout)

        # Net amount (calculated)
        net_layout = QHBoxLayout()
        net_layout.addWidget(QLabel("Net Amount (₹):"))
        self.net_spin = QDoubleSpinBox()
        self.net_spin.setDecimals(2)
        self.net_spin.setMaximum(9999999.99)
        self.net_spin.setReadOnly(True)
        net_layout.addWidget(self.net_spin)
        layout.addLayout(net_layout)

        # Notes
        notes_layout = QVBoxLayout()
        notes_layout.addWidget(QLabel("Notes:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)
        layout.addLayout(notes_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def calculate_total(self):
        """Calculate total amount from units and price"""
        units = self.units_spin.value()
        price = self.price_spin.value()
        total = units * price
        self.total_spin.setValue(total)
        self.calculate_net()

    def calculate_net(self):
        """Calculate net amount from total and fees"""
        total = self.total_spin.value()
        fees = self.fees_spin.value()
        transaction_type = self.type_combo.currentText()

        if transaction_type.lower() == "buy":
            net = total + fees
        else:  # sell
            net = total - fees

        self.net_spin.setValue(net)

    def load_data(self):
        """Load transaction data into form"""
        if self.transaction.id:
            # Find and select the fund
            for i in range(self.fund_combo.count()):
                if self.fund_combo.itemData(i) == self.transaction.fund_id:
                    self.fund_combo.setCurrentIndex(i)
                    break

            self.type_combo.setCurrentText(self.transaction.transaction_type)

            if self.transaction.transaction_date:
                if isinstance(self.transaction.transaction_date, date):
                    self.date_edit.setDate(QDate(self.transaction.transaction_date))
                else:
                    self.date_edit.setDate(QDate.currentDate())

            self.units_spin.setValue(self.transaction.units)
            self.price_spin.setValue(self.transaction.unit_price)
            self.total_spin.setValue(self.transaction.total_amount)
            self.fees_spin.setValue(self.transaction.fees)
            self.net_spin.setValue(self.transaction.net_amount)
            self.notes_edit.setPlainText(self.transaction.notes)

    def get_transaction(self):
        """Get transaction data from form"""
        self.transaction.fund_id = self.fund_combo.currentData()
        self.transaction.transaction_type = self.type_combo.currentText()
        self.transaction.transaction_date = self.date_edit.date().toPython()
        self.transaction.units = self.units_spin.value()
        self.transaction.unit_price = self.price_spin.value()
        self.transaction.total_amount = self.total_spin.value()
        self.transaction.fees = self.fees_spin.value()
        self.transaction.net_amount = self.net_spin.value()
        self.transaction.notes = self.notes_edit.toPlainText()
        self.transaction.last_updated = datetime.now()

        return self.transaction
