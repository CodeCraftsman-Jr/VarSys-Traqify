"""
Trading Widgets
UI components for trading functionality
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QGridLayout,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QGroupBox,
    QProgressBar, QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QCheckBox, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QColor, QPalette

from ...core.config import AppConfig
from ...core.data_manager import DataManager
from .api_client import ZerodhaAPIClient
from .models import TradingConfig, Position, Order, Holding
from .startup_auth_dialog import ZerodhaStartupDialog
from .auth_education import ZerodhaEducationDialog, TokenStatusWidget
from .token_manager import TokenManager


class AuthenticationDialog(QDialog):
    """Dialog for Zerodha API authentication"""
    
    def __init__(self, login_url: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zerodha Authentication")
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "1. Click 'Open Login Page' to authenticate with Zerodha\n"
            "2. After successful login, copy the request token from the URL\n"
            "3. Paste the request token below and click 'Authenticate'"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Login URL button
        self.login_button = QPushButton("Open Login Page")
        self.login_button.clicked.connect(lambda: self.open_login_url(login_url))
        layout.addWidget(self.login_button)
        
        # Request token input
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Request Token:"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Paste request token here...")
        token_layout.addWidget(self.token_input)
        layout.addLayout(token_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.login_url = login_url
    
    def open_login_url(self, url: str):
        """Open login URL in browser"""
        import webbrowser
        webbrowser.open(url)
    
    def get_request_token(self) -> str:
        """Get the entered request token"""
        return self.token_input.text().strip()


class ModifyOrderDialog(QDialog):
    """Dialog for modifying existing orders"""

    def __init__(self, order, parent=None):
        super().__init__(parent)
        self.order = order
        self.setWindowTitle(f"Modify Order - {order.tradingsymbol}")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # Order info
        info_group = QGroupBox("Order Information")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("Order ID:", QLabel(order.order_id))
        info_layout.addRow("Symbol:", QLabel(order.tradingsymbol))
        info_layout.addRow("Current Status:", QLabel(order.status))
        layout.addWidget(info_group)

        # Modification form
        modify_group = QGroupBox("Modify Order")
        form_layout = QFormLayout(modify_group)

        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(999999)
        self.quantity_input.setValue(order.quantity)
        form_layout.addRow("Quantity:", self.quantity_input)

        # Order type
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["MARKET", "LIMIT", "SL", "SL-M"])
        self.order_type_combo.setCurrentText(order.order_type)
        self.order_type_combo.currentTextChanged.connect(self.on_order_type_changed)
        form_layout.addRow("Order Type:", self.order_type_combo)

        # Price
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.01)
        self.price_input.setMaximum(999999.99)
        self.price_input.setDecimals(2)
        self.price_input.setValue(order.price or 0.0)
        form_layout.addRow("Price:", self.price_input)

        # Trigger price
        self.trigger_price_input = QDoubleSpinBox()
        self.trigger_price_input.setMinimum(0.01)
        self.trigger_price_input.setMaximum(999999.99)
        self.trigger_price_input.setDecimals(2)
        self.trigger_price_input.setValue(order.trigger_price or 0.0)
        form_layout.addRow("Trigger Price:", self.trigger_price_input)

        layout.addWidget(modify_group)

        # Update field states based on current order type
        self.on_order_type_changed(order.order_type)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_order_type_changed(self, order_type: str):
        """Handle order type change"""
        if order_type == "MARKET":
            self.price_input.setEnabled(False)
            self.trigger_price_input.setEnabled(False)
        elif order_type == "LIMIT":
            self.price_input.setEnabled(True)
            self.trigger_price_input.setEnabled(False)
        elif order_type in ["SL", "SL-M"]:
            self.price_input.setEnabled(order_type == "SL")
            self.trigger_price_input.setEnabled(True)

    def get_modifications(self) -> dict:
        """Get the modifications to apply"""
        modifications = {}

        # Check what has changed
        if self.quantity_input.value() != self.order.quantity:
            modifications["quantity"] = self.quantity_input.value()

        if self.order_type_combo.currentText() != self.order.order_type:
            modifications["order_type"] = self.order_type_combo.currentText()

        current_price = self.price_input.value()
        if current_price != (self.order.price or 0.0):
            modifications["price"] = current_price if current_price > 0 else None

        current_trigger = self.trigger_price_input.value()
        if current_trigger != (self.order.trigger_price or 0.0):
            modifications["trigger_price"] = current_trigger if current_trigger > 0 else None

        return modifications


class TradingWidget(QWidget):
    """Main trading widget with tabs for different trading functions"""
    
    def __init__(self, data_manager: DataManager, config: AppConfig, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.data_manager = data_manager
        self.config = config

        # Authentication state
        self.authentication_skipped = False
        self.startup_auth_completed = False

        # Token manager
        self.token_manager = None

        # Initialize trading configuration from file
        try:
            self.trading_config = ZerodhaAPIClient.load_config_from_file()
            self.logger.info(f"Loaded trading configuration with API key: {self.trading_config.api_key[:8]}...{self.trading_config.api_key[-4:]}")
        except Exception as e:
            self.logger.error(f"Failed to load trading configuration: {e}")
            # Fallback to empty configuration
            self.trading_config = TradingConfig(
                api_key="",  # Will be set from settings
                api_secret="",  # Will be set from settings
                sandbox_mode=True
            )
            self.logger.warning("Using fallback empty configuration")
        
        # Initialize API client
        self.api_client = None
        
        # Enhanced refresh system
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.intelligent_refresh_data)

        # Individual component refresh timers
        self.portfolio_refresh_timer = QTimer()
        self.portfolio_refresh_timer.timeout.connect(self.refresh_portfolio_data)

        self.market_refresh_timer = QTimer()
        self.market_refresh_timer.timeout.connect(self.refresh_market_data)

        self.orders_refresh_timer = QTimer()
        self.orders_refresh_timer.timeout.connect(self.refresh_orders_data)

        # Connection monitoring timer
        self.connection_monitor_timer = QTimer()
        self.connection_monitor_timer.timeout.connect(self.monitor_connection)

        # Connection retry timer
        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self.retry_connection)
        self.retry_attempts = 0
        self.max_retry_attempts = 3

        # Refresh state tracking
        self.last_refresh_time = {}
        self.refresh_intervals = {
            'portfolio': 30,  # seconds
            'market': 15,     # seconds
            'orders': 10,     # seconds
            'analytics': 60   # seconds
        }
        self.is_refreshing = False
        self.refresh_queue = []

        self.setup_ui()
        self.load_settings()

        # Don't show startup dialog during initialization
        # It will be triggered after the main window is fully loaded
        self.startup_dialog_pending = True

    def trigger_startup_dialog_if_pending(self):
        """Trigger the startup dialog if it's pending (called after main window is loaded)"""
        if hasattr(self, 'startup_dialog_pending') and self.startup_dialog_pending:
            self.startup_dialog_pending = False
            # Small delay to ensure main window is fully visible
            QTimer.singleShot(1000, self.show_startup_auth_dialog)
    
    def setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        self.create_header(layout)
        
        # Connection status
        self.create_connection_status(layout)
        
        # Main content tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tradingTabWidget")
        
        # Dashboard tab
        self.dashboard_tab = self.create_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Portfolio tab
        self.portfolio_tab = self.create_portfolio_tab()
        self.tab_widget.addTab(self.portfolio_tab, "Portfolio")

        # Market Data tab
        self.market_data_tab = self.create_market_data_tab()
        self.tab_widget.addTab(self.market_data_tab, "Market Data")

        # Orders tab
        self.orders_tab = self.create_orders_tab()
        self.tab_widget.addTab(self.orders_tab, "Orders")
        
        # Trading tab
        self.trading_tab = self.create_trading_tab()
        self.tab_widget.addTab(self.trading_tab, "Place Order")

        # Analytics tab
        self.analytics_tab = self.create_analytics_tab()
        self.tab_widget.addTab(self.analytics_tab, "Analytics")

        # Settings tab
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        layout.addWidget(self.tab_widget)
    
    def create_header(self, layout):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("Zerodha Trading")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_button)
        
        # Auto-refresh checkbox
        self.auto_refresh_checkbox = QCheckBox("Auto Refresh (30s)")
        self.auto_refresh_checkbox.toggled.connect(self.toggle_auto_refresh)
        header_layout.addWidget(self.auto_refresh_checkbox)
        
        layout.addWidget(header_frame)
    
    def create_connection_status(self, layout):
        """Create enhanced connection status section"""
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_frame.setStyleSheet("""
            QFrame#statusFrame {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)

        # Main status row
        main_status_layout = QHBoxLayout()

        self.status_label = QLabel("🔴 Trading: Not Connected")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        main_status_layout.addWidget(self.status_label)

        # User profile display
        self.profile_label = QLabel("No user profile")
        self.profile_label.setStyleSheet("color: gray; font-size: 10px;")
        main_status_layout.addWidget(self.profile_label)

        main_status_layout.addStretch()

        # Buttons
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_zerodha)
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056B3;
            }
        """)
        main_status_layout.addWidget(self.connect_button)

        self.force_reconnect_button = QPushButton("Force Reconnect")
        self.force_reconnect_button.clicked.connect(self.force_reconnect)
        self.force_reconnect_button.setToolTip("Clear expired tokens and force re-authentication")
        self.force_reconnect_button.setVisible(False)  # Initially hidden
        self.force_reconnect_button.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                color: #212529;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E0A800;
            }
        """)
        main_status_layout.addWidget(self.force_reconnect_button)

        # Help button
        self.help_button = QPushButton("ℹ️ Help")
        self.help_button.clicked.connect(self.show_auth_help)
        self.help_button.setToolTip("Learn about Zerodha authentication")
        self.help_button.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #545B62;
            }
        """)
        main_status_layout.addWidget(self.help_button)

        status_layout.addLayout(main_status_layout)

        # Token status widget
        self.token_status_widget = TokenStatusWidget()
        status_layout.addWidget(self.token_status_widget)

        layout.addWidget(status_frame)
    
    def create_dashboard_tab(self):
        """Create dashboard tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Account summary
        summary_group = QGroupBox("Account Summary")
        summary_layout = QGridLayout(summary_group)

        self.equity_label = QLabel("₹0.00")
        self.commodity_label = QLabel("₹0.00")
        self.total_label = QLabel("₹0.00")
        self.pnl_label = QLabel("₹0.00")

        # Additional portfolio metrics
        self.unrealised_pnl_label = QLabel("₹0.00")
        self.realised_pnl_label = QLabel("₹0.00")
        self.portfolio_value_label = QLabel("₹0.00")
        self.day_change_percentage_label = QLabel("0.00%")

        summary_layout.addWidget(QLabel("Equity:"), 0, 0)
        summary_layout.addWidget(self.equity_label, 0, 1)
        summary_layout.addWidget(QLabel("Commodity:"), 0, 2)
        summary_layout.addWidget(self.commodity_label, 0, 3)
        summary_layout.addWidget(QLabel("Total Available:"), 1, 0)
        summary_layout.addWidget(self.total_label, 1, 1)
        summary_layout.addWidget(QLabel("Day P&L:"), 1, 2)
        summary_layout.addWidget(self.pnl_label, 1, 3)
        summary_layout.addWidget(QLabel("Portfolio Value:"), 2, 0)
        summary_layout.addWidget(self.portfolio_value_label, 2, 1)
        summary_layout.addWidget(QLabel("Day Change %:"), 2, 2)
        summary_layout.addWidget(self.day_change_percentage_label, 2, 3)
        summary_layout.addWidget(QLabel("Unrealised P&L:"), 3, 0)
        summary_layout.addWidget(self.unrealised_pnl_label, 3, 1)
        summary_layout.addWidget(QLabel("Realised P&L:"), 3, 2)
        summary_layout.addWidget(self.realised_pnl_label, 3, 3)
        
        layout.addWidget(summary_group)
        
        # Quick stats
        stats_group = QGroupBox("Quick Stats")
        stats_layout = QGridLayout(stats_group)
        
        self.positions_count_label = QLabel("0")
        self.holdings_count_label = QLabel("0")
        self.orders_count_label = QLabel("0")
        
        stats_layout.addWidget(QLabel("Active Positions:"), 0, 0)
        stats_layout.addWidget(self.positions_count_label, 0, 1)
        stats_layout.addWidget(QLabel("Holdings:"), 0, 2)
        stats_layout.addWidget(self.holdings_count_label, 0, 3)
        stats_layout.addWidget(QLabel("Today's Orders:"), 1, 0)
        stats_layout.addWidget(self.orders_count_label, 1, 1)
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        # User profile section
        profile_group = QGroupBox("User Profile")
        profile_layout = QVBoxLayout(profile_group)

        self.user_profile_display = QLabel("Connect to view user profile")
        self.user_profile_display.setStyleSheet("color: gray; padding: 10px;")
        profile_layout.addWidget(self.user_profile_display)

        layout.addWidget(profile_group)

        return tab
    
    def create_portfolio_tab(self):
        """Create portfolio tab with enhanced analytics"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Portfolio summary section
        portfolio_summary_group = QGroupBox("Portfolio Analytics")
        summary_layout = QGridLayout(portfolio_summary_group)

        # Portfolio metrics
        self.total_portfolio_value_label = QLabel("₹0.00")
        self.total_invested_label = QLabel("₹0.00")
        self.total_pnl_label = QLabel("₹0.00")
        self.total_pnl_percentage_label = QLabel("0.00%")
        self.best_performer_label = QLabel("--")
        self.worst_performer_label = QLabel("--")

        summary_layout.addWidget(QLabel("Total Portfolio Value:"), 0, 0)
        summary_layout.addWidget(self.total_portfolio_value_label, 0, 1)
        summary_layout.addWidget(QLabel("Total Invested:"), 0, 2)
        summary_layout.addWidget(self.total_invested_label, 0, 3)
        summary_layout.addWidget(QLabel("Total P&L:"), 1, 0)
        summary_layout.addWidget(self.total_pnl_label, 1, 1)
        summary_layout.addWidget(QLabel("Total P&L %:"), 1, 2)
        summary_layout.addWidget(self.total_pnl_percentage_label, 1, 3)
        summary_layout.addWidget(QLabel("Best Performer:"), 2, 0)
        summary_layout.addWidget(self.best_performer_label, 2, 1)
        summary_layout.addWidget(QLabel("Worst Performer:"), 2, 2)
        summary_layout.addWidget(self.worst_performer_label, 2, 3)

        layout.addWidget(portfolio_summary_group)

        # Sub-tabs for positions and holdings
        portfolio_tabs = QTabWidget()

        # Positions tab
        positions_widget = QWidget()
        positions_layout = QVBoxLayout(positions_widget)

        # Positions summary
        positions_summary_group = QGroupBox("Positions Summary")
        pos_summary_layout = QHBoxLayout(positions_summary_group)
        self.positions_total_pnl_label = QLabel("Total P&L: ₹0.00")
        self.positions_day_pnl_label = QLabel("Day P&L: ₹0.00")
        self.positions_count_summary_label = QLabel("Open Positions: 0")
        pos_summary_layout.addWidget(self.positions_total_pnl_label)
        pos_summary_layout.addWidget(self.positions_day_pnl_label)
        pos_summary_layout.addWidget(self.positions_count_summary_label)
        pos_summary_layout.addStretch()
        positions_layout.addWidget(positions_summary_group)

        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(16)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Quantity", "Overnight Qty", "Multiplier", "Avg Price", "LTP", "Close Price",
            "P&L", "P&L %", "M2M", "Buy Qty", "Buy Price", "Sell Qty", "Sell Price", "Product", "Exchange"
        ])
        self.positions_table.horizontalHeader().setStretchLastSection(True)
        positions_layout.addWidget(self.positions_table)

        portfolio_tabs.addTab(positions_widget, "Positions")

        # Holdings tab
        holdings_widget = QWidget()
        holdings_layout = QVBoxLayout(holdings_widget)

        # Holdings summary
        holdings_summary_group = QGroupBox("Holdings Summary")
        hold_summary_layout = QHBoxLayout(holdings_summary_group)
        self.holdings_total_value_label = QLabel("Total Value: ₹0.00")
        self.holdings_total_pnl_label = QLabel("Total P&L: ₹0.00")
        self.holdings_count_summary_label = QLabel("Holdings: 0")
        hold_summary_layout.addWidget(self.holdings_total_value_label)
        hold_summary_layout.addWidget(self.holdings_total_pnl_label)
        hold_summary_layout.addWidget(self.holdings_count_summary_label)
        hold_summary_layout.addStretch()
        holdings_layout.addWidget(holdings_summary_group)

        self.holdings_table = QTableWidget()
        self.holdings_table.setColumnCount(15)
        self.holdings_table.setHorizontalHeaderLabels([
            "Symbol", "ISIN", "Quantity", "T1 Qty", "Realised Qty", "Avg Price", "LTP", "Close Price",
            "P&L", "P&L %", "Day Change", "Day Change %", "Value", "Collateral", "MTF"
        ])
        self.holdings_table.horizontalHeader().setStretchLastSection(True)
        holdings_layout.addWidget(self.holdings_table)

        portfolio_tabs.addTab(holdings_widget, "Holdings")

        # Asset Allocation tab
        allocation_widget = QWidget()
        allocation_layout = QVBoxLayout(allocation_widget)

        # Asset allocation summary
        allocation_summary_group = QGroupBox("Asset Allocation")
        alloc_summary_layout = QGridLayout(allocation_summary_group)

        self.equity_allocation_label = QLabel("Equity: 0%")
        self.debt_allocation_label = QLabel("Debt: 0%")
        self.commodity_allocation_label = QLabel("Commodity: 0%")
        self.cash_allocation_label = QLabel("Cash: 0%")

        alloc_summary_layout.addWidget(QLabel("Asset Distribution:"), 0, 0)
        alloc_summary_layout.addWidget(self.equity_allocation_label, 0, 1)
        alloc_summary_layout.addWidget(self.debt_allocation_label, 0, 2)
        alloc_summary_layout.addWidget(self.commodity_allocation_label, 1, 0)
        alloc_summary_layout.addWidget(self.cash_allocation_label, 1, 1)

        allocation_layout.addWidget(allocation_summary_group)

        # Sector allocation table
        sector_group = QGroupBox("Sector Allocation")
        sector_layout = QVBoxLayout(sector_group)

        self.sector_table = QTableWidget()
        self.sector_table.setColumnCount(4)
        self.sector_table.setHorizontalHeaderLabels(["Sector", "Value", "Allocation %", "P&L"])
        self.sector_table.horizontalHeader().setStretchLastSection(True)
        sector_layout.addWidget(self.sector_table)

        allocation_layout.addWidget(sector_group)
        portfolio_tabs.addTab(allocation_widget, "Asset Allocation")

        # Risk Analysis tab
        risk_widget = QWidget()
        risk_layout = QVBoxLayout(risk_widget)

        # Risk metrics
        risk_metrics_group = QGroupBox("Risk Metrics")
        risk_layout_grid = QGridLayout(risk_metrics_group)

        self.portfolio_beta_label = QLabel("Beta: --")
        self.portfolio_volatility_label = QLabel("Volatility: --")
        self.sharpe_ratio_label = QLabel("Sharpe Ratio: --")
        self.max_drawdown_label = QLabel("Max Drawdown: --")
        self.var_label = QLabel("VaR (95%): --")
        self.concentration_risk_label = QLabel("Concentration Risk: --")

        risk_layout_grid.addWidget(QLabel("Portfolio Beta:"), 0, 0)
        risk_layout_grid.addWidget(self.portfolio_beta_label, 0, 1)
        risk_layout_grid.addWidget(QLabel("Volatility:"), 0, 2)
        risk_layout_grid.addWidget(self.portfolio_volatility_label, 0, 3)
        risk_layout_grid.addWidget(QLabel("Sharpe Ratio:"), 1, 0)
        risk_layout_grid.addWidget(self.sharpe_ratio_label, 1, 1)
        risk_layout_grid.addWidget(QLabel("Max Drawdown:"), 1, 2)
        risk_layout_grid.addWidget(self.max_drawdown_label, 1, 3)
        risk_layout_grid.addWidget(QLabel("Value at Risk:"), 2, 0)
        risk_layout_grid.addWidget(self.var_label, 2, 1)
        risk_layout_grid.addWidget(QLabel("Concentration Risk:"), 2, 2)
        risk_layout_grid.addWidget(self.concentration_risk_label, 2, 3)

        risk_layout.addWidget(risk_metrics_group)

        # Top holdings concentration
        concentration_group = QGroupBox("Top Holdings Concentration")
        concentration_layout = QVBoxLayout(concentration_group)

        self.concentration_table = QTableWidget()
        self.concentration_table.setColumnCount(3)
        self.concentration_table.setHorizontalHeaderLabels(["Symbol", "Value", "% of Portfolio"])
        self.concentration_table.horizontalHeader().setStretchLastSection(True)
        concentration_layout.addWidget(self.concentration_table)

        risk_layout.addWidget(concentration_group)
        portfolio_tabs.addTab(risk_widget, "Risk Analysis")

        # Performance Analysis tab
        performance_widget = QWidget()
        performance_layout = QVBoxLayout(performance_widget)

        # Performance metrics
        performance_metrics_group = QGroupBox("Performance Metrics")
        perf_layout_grid = QGridLayout(performance_metrics_group)

        self.total_return_label = QLabel("Total Return: --")
        self.annualized_return_label = QLabel("Annualized Return: --")
        self.ytd_return_label = QLabel("YTD Return: --")
        self.monthly_return_label = QLabel("Monthly Return: --")
        self.weekly_return_label = QLabel("Weekly Return: --")
        self.daily_return_label = QLabel("Daily Return: --")

        perf_layout_grid.addWidget(QLabel("Total Return:"), 0, 0)
        perf_layout_grid.addWidget(self.total_return_label, 0, 1)
        perf_layout_grid.addWidget(QLabel("Annualized Return:"), 0, 2)
        perf_layout_grid.addWidget(self.annualized_return_label, 0, 3)
        perf_layout_grid.addWidget(QLabel("YTD Return:"), 1, 0)
        perf_layout_grid.addWidget(self.ytd_return_label, 1, 1)
        perf_layout_grid.addWidget(QLabel("Monthly Return:"), 1, 2)
        perf_layout_grid.addWidget(self.monthly_return_label, 1, 3)
        perf_layout_grid.addWidget(QLabel("Weekly Return:"), 2, 0)
        perf_layout_grid.addWidget(self.weekly_return_label, 2, 1)
        perf_layout_grid.addWidget(QLabel("Daily Return:"), 2, 2)
        perf_layout_grid.addWidget(self.daily_return_label, 2, 3)

        performance_layout.addWidget(performance_metrics_group)

        # Top gainers and losers
        gainers_losers_group = QGroupBox("Top Gainers & Losers")
        gl_layout = QHBoxLayout(gainers_losers_group)

        # Top gainers
        gainers_group = QGroupBox("Top Gainers")
        gainers_layout = QVBoxLayout(gainers_group)
        self.gainers_table = QTableWidget()
        self.gainers_table.setColumnCount(3)
        self.gainers_table.setHorizontalHeaderLabels(["Symbol", "P&L", "P&L %"])
        self.gainers_table.horizontalHeader().setStretchLastSection(True)
        gainers_layout.addWidget(self.gainers_table)
        gl_layout.addWidget(gainers_group)

        # Top losers
        losers_group = QGroupBox("Top Losers")
        losers_layout = QVBoxLayout(losers_group)
        self.losers_table = QTableWidget()
        self.losers_table.setColumnCount(3)
        self.losers_table.setHorizontalHeaderLabels(["Symbol", "P&L", "P&L %"])
        self.losers_table.horizontalHeader().setStretchLastSection(True)
        losers_layout.addWidget(self.losers_table)
        gl_layout.addWidget(losers_group)

        performance_layout.addWidget(gainers_losers_group)
        portfolio_tabs.addTab(performance_widget, "Performance")

        layout.addWidget(portfolio_tabs)
        return tab

    def create_market_data_tab(self):
        """Create market data and charts tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Market data controls
        controls_group = QGroupBox("Market Data Controls")
        controls_layout = QHBoxLayout(controls_group)

        # Symbol search
        controls_layout.addWidget(QLabel("Symbol:"))
        self.market_symbol_input = QLineEdit()
        self.market_symbol_input.setPlaceholderText("Enter symbol (e.g., RELIANCE)")
        controls_layout.addWidget(self.market_symbol_input)

        # Exchange selection
        controls_layout.addWidget(QLabel("Exchange:"))
        self.market_exchange_combo = QComboBox()
        self.market_exchange_combo.addItems(["NSE", "BSE", "NFO", "MCX"])
        controls_layout.addWidget(self.market_exchange_combo)

        # Get quote button
        self.get_market_quote_button = QPushButton("Get Quote")
        self.get_market_quote_button.clicked.connect(self.get_market_quote)
        controls_layout.addWidget(self.get_market_quote_button)

        # Historical data button
        self.get_historical_button = QPushButton("Get Historical Data")
        self.get_historical_button.clicked.connect(self.get_historical_data)
        controls_layout.addWidget(self.get_historical_button)

        controls_layout.addStretch()
        layout.addWidget(controls_group)

        # Market data display
        market_tabs = QTabWidget()

        # Quote tab
        quote_widget = QWidget()
        quote_layout = QVBoxLayout(quote_widget)

        # Current quote display
        quote_info_group = QGroupBox("Current Quote")
        quote_info_layout = QGridLayout(quote_info_group)

        self.quote_symbol_label = QLabel("--")
        self.quote_ltp_label = QLabel("₹0.00")
        self.quote_change_label = QLabel("₹0.00 (0.00%)")
        self.quote_volume_label = QLabel("0")
        self.quote_high_label = QLabel("₹0.00")
        self.quote_low_label = QLabel("₹0.00")
        self.quote_open_label = QLabel("₹0.00")
        self.quote_close_label = QLabel("₹0.00")

        # Additional comprehensive quote data
        self.quote_avg_price_label = QLabel("₹0.00")
        self.quote_buy_qty_label = QLabel("0")
        self.quote_sell_qty_label = QLabel("0")
        self.quote_oi_label = QLabel("0")
        self.quote_oi_high_label = QLabel("0")
        self.quote_oi_low_label = QLabel("0")
        self.quote_upper_circuit_label = QLabel("₹0.00")
        self.quote_lower_circuit_label = QLabel("₹0.00")
        self.quote_last_trade_time_label = QLabel("--")

        quote_info_layout.addWidget(QLabel("Symbol:"), 0, 0)
        quote_info_layout.addWidget(self.quote_symbol_label, 0, 1)
        quote_info_layout.addWidget(QLabel("LTP:"), 0, 2)
        quote_info_layout.addWidget(self.quote_ltp_label, 0, 3)
        quote_info_layout.addWidget(QLabel("Change:"), 1, 0)
        quote_info_layout.addWidget(self.quote_change_label, 1, 1)
        quote_info_layout.addWidget(QLabel("Volume:"), 1, 2)
        quote_info_layout.addWidget(self.quote_volume_label, 1, 3)
        quote_info_layout.addWidget(QLabel("High:"), 2, 0)
        quote_info_layout.addWidget(self.quote_high_label, 2, 1)
        quote_info_layout.addWidget(QLabel("Low:"), 2, 2)
        quote_info_layout.addWidget(self.quote_low_label, 2, 3)
        quote_info_layout.addWidget(QLabel("Open:"), 3, 0)
        quote_info_layout.addWidget(self.quote_open_label, 3, 1)
        quote_info_layout.addWidget(QLabel("Close:"), 3, 2)
        quote_info_layout.addWidget(self.quote_close_label, 3, 3)
        quote_info_layout.addWidget(QLabel("Avg Price:"), 4, 0)
        quote_info_layout.addWidget(self.quote_avg_price_label, 4, 1)
        quote_info_layout.addWidget(QLabel("Last Trade:"), 4, 2)
        quote_info_layout.addWidget(self.quote_last_trade_time_label, 4, 3)
        quote_info_layout.addWidget(QLabel("Buy Qty:"), 5, 0)
        quote_info_layout.addWidget(self.quote_buy_qty_label, 5, 1)
        quote_info_layout.addWidget(QLabel("Sell Qty:"), 5, 2)
        quote_info_layout.addWidget(self.quote_sell_qty_label, 5, 3)
        quote_info_layout.addWidget(QLabel("Open Interest:"), 6, 0)
        quote_info_layout.addWidget(self.quote_oi_label, 6, 1)
        quote_info_layout.addWidget(QLabel("OI High:"), 6, 2)
        quote_info_layout.addWidget(self.quote_oi_high_label, 6, 3)
        quote_info_layout.addWidget(QLabel("OI Low:"), 7, 0)
        quote_info_layout.addWidget(self.quote_oi_low_label, 7, 1)
        quote_info_layout.addWidget(QLabel("Upper Circuit:"), 7, 2)
        quote_info_layout.addWidget(self.quote_upper_circuit_label, 7, 3)
        quote_info_layout.addWidget(QLabel("Lower Circuit:"), 8, 0)
        quote_info_layout.addWidget(self.quote_lower_circuit_label, 8, 1)

        quote_layout.addWidget(quote_info_group)

        # Market depth
        depth_group = QGroupBox("Market Depth")
        depth_layout = QHBoxLayout(depth_group)

        # Buy depth
        buy_depth_group = QGroupBox("Buy Depth")
        buy_depth_layout = QVBoxLayout(buy_depth_group)
        self.buy_depth_table = QTableWidget()
        self.buy_depth_table.setColumnCount(3)
        self.buy_depth_table.setHorizontalHeaderLabels(["Price", "Quantity", "Orders"])
        self.buy_depth_table.setMaximumHeight(150)
        buy_depth_layout.addWidget(self.buy_depth_table)
        depth_layout.addWidget(buy_depth_group)

        # Sell depth
        sell_depth_group = QGroupBox("Sell Depth")
        sell_depth_layout = QVBoxLayout(sell_depth_group)
        self.sell_depth_table = QTableWidget()
        self.sell_depth_table.setColumnCount(3)
        self.sell_depth_table.setHorizontalHeaderLabels(["Price", "Quantity", "Orders"])
        self.sell_depth_table.setMaximumHeight(150)
        sell_depth_layout.addWidget(self.sell_depth_table)
        depth_layout.addWidget(sell_depth_group)

        quote_layout.addWidget(depth_group)
        market_tabs.addTab(quote_widget, "Live Quote")

        # Historical data tab
        historical_widget = QWidget()
        historical_layout = QVBoxLayout(historical_widget)

        # Historical data controls
        hist_controls_group = QGroupBox("Historical Data Settings")
        hist_controls_layout = QHBoxLayout(hist_controls_group)

        hist_controls_layout.addWidget(QLabel("Interval:"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["minute", "3minute", "5minute", "15minute", "30minute", "60minute", "day"])
        self.interval_combo.setCurrentText("day")
        hist_controls_layout.addWidget(self.interval_combo)

        hist_controls_layout.addWidget(QLabel("Days:"))
        self.days_spinbox = QSpinBox()
        self.days_spinbox.setMinimum(1)
        self.days_spinbox.setMaximum(365)
        self.days_spinbox.setValue(30)
        hist_controls_layout.addWidget(self.days_spinbox)

        hist_controls_layout.addStretch()
        historical_layout.addWidget(hist_controls_group)

        # Historical data table
        self.historical_table = QTableWidget()
        self.historical_table.setColumnCount(6)
        self.historical_table.setHorizontalHeaderLabels(["Date", "Open", "High", "Low", "Close", "Volume"])
        historical_layout.addWidget(self.historical_table)

        market_tabs.addTab(historical_widget, "Historical Data")

        # Watchlist tab
        watchlist_widget = QWidget()
        watchlist_layout = QVBoxLayout(watchlist_widget)

        # Watchlist controls
        watchlist_controls_group = QGroupBox("Watchlist Management")
        watchlist_controls_layout = QHBoxLayout(watchlist_controls_group)

        watchlist_controls_layout.addWidget(QLabel("Add Symbol:"))
        self.watchlist_symbol_input = QLineEdit()
        self.watchlist_symbol_input.setPlaceholderText("Enter symbol to add to watchlist")
        watchlist_controls_layout.addWidget(self.watchlist_symbol_input)

        self.add_to_watchlist_button = QPushButton("Add to Watchlist")
        self.add_to_watchlist_button.clicked.connect(self.add_to_watchlist)
        watchlist_controls_layout.addWidget(self.add_to_watchlist_button)

        self.remove_from_watchlist_button = QPushButton("Remove Selected")
        self.remove_from_watchlist_button.clicked.connect(self.remove_from_watchlist)
        watchlist_controls_layout.addWidget(self.remove_from_watchlist_button)

        self.refresh_watchlist_button = QPushButton("Refresh All")
        self.refresh_watchlist_button.clicked.connect(self.refresh_watchlist)
        watchlist_controls_layout.addWidget(self.refresh_watchlist_button)

        watchlist_controls_layout.addStretch()
        watchlist_layout.addWidget(watchlist_controls_group)

        # Watchlist table
        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(8)
        self.watchlist_table.setHorizontalHeaderLabels([
            "Symbol", "LTP", "Change", "Change %", "Volume", "High", "Low", "Last Updated"
        ])
        self.watchlist_table.horizontalHeader().setStretchLastSection(True)
        self.watchlist_table.setSelectionBehavior(QTableWidget.SelectRows)
        watchlist_layout.addWidget(self.watchlist_table)

        market_tabs.addTab(watchlist_widget, "Watchlist")

        # Market Overview tab
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)

        # Market indices
        indices_group = QGroupBox("Market Indices")
        indices_layout = QVBoxLayout(indices_group)

        self.indices_table = QTableWidget()
        self.indices_table.setColumnCount(4)
        self.indices_table.setHorizontalHeaderLabels(["Index", "Value", "Change", "Change %"])
        self.indices_table.horizontalHeader().setStretchLastSection(True)
        indices_layout.addWidget(self.indices_table)

        overview_layout.addWidget(indices_group)

        # Top gainers and losers
        gainers_losers_group = QGroupBox("Market Movers")
        gl_layout = QHBoxLayout(gainers_losers_group)

        # Top gainers
        market_gainers_group = QGroupBox("Top Gainers")
        market_gainers_layout = QVBoxLayout(market_gainers_group)
        self.market_gainers_table = QTableWidget()
        self.market_gainers_table.setColumnCount(3)
        self.market_gainers_table.setHorizontalHeaderLabels(["Symbol", "LTP", "Change %"])
        self.market_gainers_table.horizontalHeader().setStretchLastSection(True)
        market_gainers_layout.addWidget(self.market_gainers_table)
        gl_layout.addWidget(market_gainers_group)

        # Top losers
        market_losers_group = QGroupBox("Top Losers")
        market_losers_layout = QVBoxLayout(market_losers_group)
        self.market_losers_table = QTableWidget()
        self.market_losers_table.setColumnCount(3)
        self.market_losers_table.setHorizontalHeaderLabels(["Symbol", "LTP", "Change %"])
        self.market_losers_table.horizontalHeader().setStretchLastSection(True)
        market_losers_layout.addWidget(self.market_losers_table)
        gl_layout.addWidget(market_losers_group)

        overview_layout.addWidget(gainers_losers_group)

        # Most active stocks
        active_group = QGroupBox("Most Active (by Volume)")
        active_layout = QVBoxLayout(active_group)
        self.most_active_table = QTableWidget()
        self.most_active_table.setColumnCount(4)
        self.most_active_table.setHorizontalHeaderLabels(["Symbol", "LTP", "Volume", "Turnover"])
        self.most_active_table.horizontalHeader().setStretchLastSection(True)
        active_layout.addWidget(self.most_active_table)
        overview_layout.addWidget(active_group)

        market_tabs.addTab(overview_widget, "Market Overview")

        layout.addWidget(market_tabs)
        return tab

    def create_analytics_tab(self):
        """Create comprehensive trading analytics and history tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Analytics control panel
        control_panel = QGroupBox("Analytics Control Panel")
        control_layout = QHBoxLayout(control_panel)

        self.refresh_analytics_button = QPushButton("Refresh Analytics")
        self.refresh_analytics_button.clicked.connect(self.refresh_analytics_data)
        control_layout.addWidget(self.refresh_analytics_button)

        control_layout.addWidget(QLabel("Period:"))
        self.analytics_period_combo = QComboBox()
        self.analytics_period_combo.addItems(["Last 7 Days", "Last 30 Days", "Last 90 Days", "Last 1 Year", "All Time"])
        self.analytics_period_combo.setCurrentText("Last 30 Days")
        self.analytics_period_combo.currentTextChanged.connect(self.on_analytics_period_changed)
        control_layout.addWidget(self.analytics_period_combo)

        self.export_analytics_button = QPushButton("Export Report")
        self.export_analytics_button.clicked.connect(self.export_analytics_report)
        control_layout.addWidget(self.export_analytics_button)

        control_layout.addStretch()
        layout.addWidget(control_panel)

        # Analytics summary dashboard
        dashboard_group = QGroupBox("Trading Performance Dashboard")
        dashboard_layout = QGridLayout(dashboard_group)

        # Key performance metrics
        self.total_trades_label = QLabel("0")
        self.winning_trades_label = QLabel("0")
        self.losing_trades_label = QLabel("0")
        self.win_rate_label = QLabel("0.00%")
        self.total_pnl_analytics_label = QLabel("₹0.00")
        self.avg_profit_label = QLabel("₹0.00")
        self.avg_loss_label = QLabel("₹0.00")
        self.largest_win_label = QLabel("₹0.00")
        self.largest_loss_label = QLabel("₹0.00")
        self.profit_factor_label = QLabel("0.00")
        self.sharpe_ratio_label = QLabel("0.00")
        self.max_drawdown_label = QLabel("₹0.00")

        # Row 1
        dashboard_layout.addWidget(QLabel("Total Trades:"), 0, 0)
        dashboard_layout.addWidget(self.total_trades_label, 0, 1)
        dashboard_layout.addWidget(QLabel("Winning Trades:"), 0, 2)
        dashboard_layout.addWidget(self.winning_trades_label, 0, 3)
        dashboard_layout.addWidget(QLabel("Losing Trades:"), 0, 4)
        dashboard_layout.addWidget(self.losing_trades_label, 0, 5)

        # Row 2
        dashboard_layout.addWidget(QLabel("Win Rate:"), 1, 0)
        dashboard_layout.addWidget(self.win_rate_label, 1, 1)
        dashboard_layout.addWidget(QLabel("Total P&L:"), 1, 2)
        dashboard_layout.addWidget(self.total_pnl_analytics_label, 1, 3)
        dashboard_layout.addWidget(QLabel("Profit Factor:"), 1, 4)
        dashboard_layout.addWidget(self.profit_factor_label, 1, 5)

        # Row 3
        dashboard_layout.addWidget(QLabel("Avg Profit:"), 2, 0)
        dashboard_layout.addWidget(self.avg_profit_label, 2, 1)
        dashboard_layout.addWidget(QLabel("Avg Loss:"), 2, 2)
        dashboard_layout.addWidget(self.avg_loss_label, 2, 3)
        dashboard_layout.addWidget(QLabel("Sharpe Ratio:"), 2, 4)
        dashboard_layout.addWidget(self.sharpe_ratio_label, 2, 5)

        # Row 4
        dashboard_layout.addWidget(QLabel("Largest Win:"), 3, 0)
        dashboard_layout.addWidget(self.largest_win_label, 3, 1)
        dashboard_layout.addWidget(QLabel("Largest Loss:"), 3, 2)
        dashboard_layout.addWidget(self.largest_loss_label, 3, 3)
        dashboard_layout.addWidget(QLabel("Max Drawdown:"), 3, 4)
        dashboard_layout.addWidget(self.max_drawdown_label, 3, 5)

        layout.addWidget(dashboard_group)

        # Analytics tabs
        analytics_tabs = QTabWidget()

        # P&L Analysis tab
        pnl_widget = QWidget()
        pnl_layout = QVBoxLayout(pnl_widget)

        # Daily P&L chart area (placeholder)
        daily_pnl_group = QGroupBox("Daily P&L Trend")
        daily_pnl_layout = QVBoxLayout(daily_pnl_group)

        self.daily_pnl_table = QTableWidget()
        self.daily_pnl_table.setColumnCount(6)
        self.daily_pnl_table.setHorizontalHeaderLabels([
            "Date", "Trades", "Gross P&L", "Charges", "Net P&L", "Cumulative P&L"
        ])
        self.daily_pnl_table.horizontalHeader().setStretchLastSection(True)
        self.daily_pnl_table.setMaximumHeight(300)
        daily_pnl_layout.addWidget(self.daily_pnl_table)
        pnl_layout.addWidget(daily_pnl_group)

        # P&L breakdown
        pnl_breakdown_group = QGroupBox("P&L Breakdown")
        pnl_breakdown_layout = QHBoxLayout(pnl_breakdown_group)

        # By product type
        product_pnl_group = QGroupBox("By Product Type")
        product_pnl_layout = QVBoxLayout(product_pnl_group)
        self.product_pnl_table = QTableWidget()
        self.product_pnl_table.setColumnCount(4)
        self.product_pnl_table.setHorizontalHeaderLabels(["Product", "Trades", "P&L", "Percentage"])
        product_pnl_layout.addWidget(self.product_pnl_table)
        pnl_breakdown_layout.addWidget(product_pnl_group)

        # By exchange
        exchange_pnl_group = QGroupBox("By Exchange")
        exchange_pnl_layout = QVBoxLayout(exchange_pnl_group)
        self.exchange_pnl_table = QTableWidget()
        self.exchange_pnl_table.setColumnCount(4)
        self.exchange_pnl_table.setHorizontalHeaderLabels(["Exchange", "Trades", "P&L", "Percentage"])
        exchange_pnl_layout.addWidget(self.exchange_pnl_table)
        pnl_breakdown_layout.addWidget(exchange_pnl_group)

        pnl_layout.addWidget(pnl_breakdown_group)
        analytics_tabs.addTab(pnl_widget, "P&L Analysis")

        # Trade History tab
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)

        # Enhanced history filters
        history_filters_group = QGroupBox("Advanced Filters")
        filters_layout = QGridLayout(history_filters_group)

        filters_layout.addWidget(QLabel("Status:"), 0, 0)
        self.analytics_status_combo = QComboBox()
        self.analytics_status_combo.addItems(["All", "COMPLETE", "CANCELLED", "REJECTED"])
        filters_layout.addWidget(self.analytics_status_combo, 0, 1)

        filters_layout.addWidget(QLabel("Symbol:"), 0, 2)
        self.analytics_symbol_input = QLineEdit()
        self.analytics_symbol_input.setPlaceholderText("Filter by symbol...")
        filters_layout.addWidget(self.analytics_symbol_input, 0, 3)

        filters_layout.addWidget(QLabel("Product:"), 1, 0)
        self.analytics_product_combo = QComboBox()
        self.analytics_product_combo.addItems(["All", "CNC", "MIS", "NRML"])
        filters_layout.addWidget(self.analytics_product_combo, 1, 1)

        filters_layout.addWidget(QLabel("Exchange:"), 1, 2)
        self.analytics_exchange_combo = QComboBox()
        self.analytics_exchange_combo.addItems(["All", "NSE", "BSE", "NFO", "BFO", "CDS", "MCX"])
        filters_layout.addWidget(self.analytics_exchange_combo, 1, 3)

        filters_layout.addWidget(QLabel("Min P&L:"), 2, 0)
        self.min_pnl_input = QDoubleSpinBox()
        self.min_pnl_input.setMinimum(-999999)
        self.min_pnl_input.setMaximum(999999)
        filters_layout.addWidget(self.min_pnl_input, 2, 1)

        filters_layout.addWidget(QLabel("Max P&L:"), 2, 2)
        self.max_pnl_input = QDoubleSpinBox()
        self.max_pnl_input.setMinimum(-999999)
        self.max_pnl_input.setMaximum(999999)
        self.max_pnl_input.setValue(999999)
        filters_layout.addWidget(self.max_pnl_input, 2, 3)

        self.apply_analytics_filters_button = QPushButton("Apply Filters")
        self.apply_analytics_filters_button.clicked.connect(self.apply_analytics_filters)
        filters_layout.addWidget(self.apply_analytics_filters_button, 3, 0)

        self.clear_analytics_filters_button = QPushButton("Clear Filters")
        self.clear_analytics_filters_button.clicked.connect(self.clear_analytics_filters)
        filters_layout.addWidget(self.clear_analytics_filters_button, 3, 1)

        history_layout.addWidget(history_filters_group)

        # Enhanced trade history table
        self.trade_history_table = QTableWidget()
        self.trade_history_table.setColumnCount(14)
        self.trade_history_table.setHorizontalHeaderLabels([
            "Date", "Time", "Symbol", "Exchange", "Type", "Side", "Quantity",
            "Price", "Amount", "Product", "Status", "P&L", "Charges", "Net P&L"
        ])
        self.trade_history_table.horizontalHeader().setStretchLastSection(True)
        self.trade_history_table.setSelectionBehavior(QTableWidget.SelectRows)
        history_layout.addWidget(self.trade_history_table)

        analytics_tabs.addTab(history_widget, "Trade History")

        # Performance Analysis tab
        performance_widget = QWidget()
        performance_layout = QVBoxLayout(performance_widget)

        # Performance metrics tabs
        performance_tabs = QTabWidget()

        # Monthly performance
        monthly_widget = QWidget()
        monthly_layout = QVBoxLayout(monthly_widget)

        self.monthly_performance_table = QTableWidget()
        self.monthly_performance_table.setColumnCount(8)
        self.monthly_performance_table.setHorizontalHeaderLabels([
            "Month", "Trades", "Win Rate", "Gross P&L", "Charges", "Net P&L", "Best Day", "Worst Day"
        ])
        self.monthly_performance_table.horizontalHeader().setStretchLastSection(True)
        monthly_layout.addWidget(self.monthly_performance_table)
        performance_tabs.addTab(monthly_widget, "Monthly")

        # Symbol performance
        symbol_widget = QWidget()
        symbol_layout = QVBoxLayout(symbol_widget)

        self.symbol_performance_table = QTableWidget()
        self.symbol_performance_table.setColumnCount(9)
        self.symbol_performance_table.setHorizontalHeaderLabels([
            "Symbol", "Trades", "Win Rate", "Total P&L", "Avg P&L", "Best Trade", "Worst Trade", "Volume", "Turnover"
        ])
        self.symbol_performance_table.horizontalHeader().setStretchLastSection(True)
        symbol_layout.addWidget(self.symbol_performance_table)
        performance_tabs.addTab(symbol_widget, "By Symbol")

        # Strategy performance (if applicable)
        strategy_widget = QWidget()
        strategy_layout = QVBoxLayout(strategy_widget)

        self.strategy_performance_table = QTableWidget()
        self.strategy_performance_table.setColumnCount(7)
        self.strategy_performance_table.setHorizontalHeaderLabels([
            "Strategy", "Trades", "Win Rate", "Total P&L", "Avg P&L", "Max Drawdown", "Sharpe Ratio"
        ])
        self.strategy_performance_table.horizontalHeader().setStretchLastSection(True)
        strategy_layout.addWidget(self.strategy_performance_table)
        performance_tabs.addTab(strategy_widget, "By Strategy")

        performance_layout.addWidget(performance_tabs)
        analytics_tabs.addTab(performance_widget, "Performance Analysis")

        # Risk Analysis tab
        risk_widget = QWidget()
        risk_layout = QVBoxLayout(risk_widget)

        # Risk metrics
        risk_metrics_group = QGroupBox("Risk Metrics")
        risk_metrics_layout = QGridLayout(risk_metrics_group)

        self.var_label = QLabel("₹0.00")
        self.volatility_label = QLabel("0.00%")
        self.beta_label = QLabel("0.00")
        self.correlation_label = QLabel("0.00")

        risk_metrics_layout.addWidget(QLabel("Value at Risk (95%):"), 0, 0)
        risk_metrics_layout.addWidget(self.var_label, 0, 1)
        risk_metrics_layout.addWidget(QLabel("Portfolio Volatility:"), 0, 2)
        risk_metrics_layout.addWidget(self.volatility_label, 0, 3)
        risk_metrics_layout.addWidget(QLabel("Portfolio Beta:"), 1, 0)
        risk_metrics_layout.addWidget(self.beta_label, 1, 1)
        risk_metrics_layout.addWidget(QLabel("Market Correlation:"), 1, 2)
        risk_metrics_layout.addWidget(self.correlation_label, 1, 3)

        risk_layout.addWidget(risk_metrics_group)

        # Risk breakdown table
        risk_breakdown_group = QGroupBox("Risk Breakdown by Position")
        risk_breakdown_layout = QVBoxLayout(risk_breakdown_group)

        self.risk_breakdown_table = QTableWidget()
        self.risk_breakdown_table.setColumnCount(6)
        self.risk_breakdown_table.setHorizontalHeaderLabels([
            "Symbol", "Position Value", "Risk Contribution", "Beta", "Volatility", "VaR"
        ])
        self.risk_breakdown_table.horizontalHeader().setStretchLastSection(True)
        risk_breakdown_layout.addWidget(self.risk_breakdown_table)
        risk_layout.addWidget(risk_breakdown_group)

        analytics_tabs.addTab(risk_widget, "Risk Analysis")

        layout.addWidget(analytics_tabs)
        return tab

    def create_orders_tab(self):
        """Create comprehensive orders tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Orders management tabs
        orders_tabs = QTabWidget()

        # Active Orders tab
        active_orders_widget = QWidget()
        active_orders_layout = QVBoxLayout(active_orders_widget)

        # Active orders controls
        active_controls_group = QGroupBox("Active Orders Management")
        active_controls_layout = QHBoxLayout(active_controls_group)

        self.refresh_orders_button = QPushButton("Refresh Orders")
        self.refresh_orders_button.clicked.connect(self.refresh_orders_data)
        active_controls_layout.addWidget(self.refresh_orders_button)

        self.cancel_all_button = QPushButton("Cancel All Pending")
        self.cancel_all_button.clicked.connect(self.cancel_all_pending_orders)
        self.cancel_all_button.setStyleSheet("background-color: #ff6b6b; color: white;")
        active_controls_layout.addWidget(self.cancel_all_button)

        active_controls_layout.addStretch()
        active_orders_layout.addWidget(active_controls_group)

        # Active orders table
        self.active_orders_table = QTableWidget()
        self.active_orders_table.setColumnCount(11)
        self.active_orders_table.setHorizontalHeaderLabels([
            "Order ID", "Symbol", "Type", "Transaction", "Quantity", "Price",
            "Trigger Price", "Status", "Product", "Time", "Actions"
        ])
        self.active_orders_table.horizontalHeader().setStretchLastSection(True)
        self.active_orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        active_orders_layout.addWidget(self.active_orders_table)

        orders_tabs.addTab(active_orders_widget, "Active Orders")

        # Order History tab
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)

        # History filters
        history_filters_group = QGroupBox("Order History Filters")
        history_filters_layout = QHBoxLayout(history_filters_group)

        history_filters_layout.addWidget(QLabel("Status:"))
        self.history_status_combo = QComboBox()
        self.history_status_combo.addItems(["All", "COMPLETE", "CANCELLED", "REJECTED"])
        history_filters_layout.addWidget(self.history_status_combo)

        history_filters_layout.addWidget(QLabel("Symbol:"))
        self.history_symbol_input = QLineEdit()
        self.history_symbol_input.setPlaceholderText("Filter by symbol")
        history_filters_layout.addWidget(self.history_symbol_input)

        history_filters_layout.addWidget(QLabel("Days:"))
        self.history_days_spinbox = QSpinBox()
        self.history_days_spinbox.setMinimum(1)
        self.history_days_spinbox.setMaximum(365)
        self.history_days_spinbox.setValue(30)
        history_filters_layout.addWidget(self.history_days_spinbox)

        self.apply_history_filters_button = QPushButton("Apply Filters")
        self.apply_history_filters_button.clicked.connect(self.apply_history_filters)
        history_filters_layout.addWidget(self.apply_history_filters_button)

        self.export_history_button = QPushButton("Export to CSV")
        self.export_history_button.clicked.connect(self.export_order_history)
        history_filters_layout.addWidget(self.export_history_button)

        history_filters_layout.addStretch()
        history_layout.addWidget(history_filters_group)

        # Order history table
        self.order_history_table = QTableWidget()
        self.order_history_table.setColumnCount(18)
        self.order_history_table.setHorizontalHeaderLabels([
            "Order ID", "Parent ID", "Exchange Order ID", "Symbol", "Type", "Transaction",
            "Quantity", "Filled Qty", "Pending Qty", "Cancelled Qty", "Price", "Trigger Price",
            "Average Price", "Status", "Status Message", "Product", "Variety", "Order Time"
        ])
        self.order_history_table.horizontalHeader().setStretchLastSection(True)
        self.order_history_table.setSelectionBehavior(QTableWidget.SelectRows)
        history_layout.addWidget(self.order_history_table)

        orders_tabs.addTab(history_widget, "Order History")

        # Order Analytics tab
        analytics_widget = QWidget()
        analytics_layout = QVBoxLayout(analytics_widget)

        # Order statistics
        stats_group = QGroupBox("Order Statistics")
        stats_layout = QGridLayout(stats_group)

        self.total_orders_label = QLabel("0")
        self.completed_orders_label = QLabel("0")
        self.cancelled_orders_label = QLabel("0")
        self.rejected_orders_label = QLabel("0")
        self.pending_orders_label = QLabel("0")
        self.success_rate_label = QLabel("0%")

        stats_layout.addWidget(QLabel("Total Orders:"), 0, 0)
        stats_layout.addWidget(self.total_orders_label, 0, 1)
        stats_layout.addWidget(QLabel("Completed:"), 0, 2)
        stats_layout.addWidget(self.completed_orders_label, 0, 3)
        stats_layout.addWidget(QLabel("Cancelled:"), 1, 0)
        stats_layout.addWidget(self.cancelled_orders_label, 1, 1)
        stats_layout.addWidget(QLabel("Rejected:"), 1, 2)
        stats_layout.addWidget(self.rejected_orders_label, 1, 3)
        stats_layout.addWidget(QLabel("Pending:"), 2, 0)
        stats_layout.addWidget(self.pending_orders_label, 2, 1)
        stats_layout.addWidget(QLabel("Success Rate:"), 2, 2)
        stats_layout.addWidget(self.success_rate_label, 2, 3)

        analytics_layout.addWidget(stats_group)

        # Order breakdown by type
        breakdown_group = QGroupBox("Order Breakdown")
        breakdown_layout = QVBoxLayout(breakdown_group)

        self.order_breakdown_table = QTableWidget()
        self.order_breakdown_table.setColumnCount(4)
        self.order_breakdown_table.setHorizontalHeaderLabels(["Order Type", "Count", "Success Rate", "Avg Fill Time"])
        self.order_breakdown_table.horizontalHeader().setStretchLastSection(True)
        breakdown_layout.addWidget(self.order_breakdown_table)

        analytics_layout.addWidget(breakdown_group)

        # Recent order activity
        recent_group = QGroupBox("Recent Order Activity")
        recent_layout = QVBoxLayout(recent_group)

        self.recent_orders_table = QTableWidget()
        self.recent_orders_table.setColumnCount(6)
        self.recent_orders_table.setHorizontalHeaderLabels([
            "Time", "Symbol", "Transaction", "Quantity", "Price", "Status"
        ])
        self.recent_orders_table.horizontalHeader().setStretchLastSection(True)
        self.recent_orders_table.setMaximumHeight(200)
        recent_layout.addWidget(self.recent_orders_table)

        analytics_layout.addWidget(recent_group)

        orders_tabs.addTab(analytics_widget, "Order Analytics")

        layout.addWidget(orders_tabs)
        return tab
    
    def create_trading_tab(self):
        """Create comprehensive trading/order placement tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Trading tabs
        trading_tabs = QTabWidget()

        # Place Order tab
        place_order_widget = QWidget()
        place_order_layout = QHBoxLayout(place_order_widget)

        # Left side - Order form
        form_group = QGroupBox("Place Order")
        form_layout = QFormLayout(form_group)

        # Symbol search with autocomplete
        symbol_layout = QHBoxLayout()
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("e.g., RELIANCE, TCS, INFY")
        self.symbol_input.textChanged.connect(self.on_symbol_search)
        symbol_layout.addWidget(self.symbol_input)

        self.search_symbol_button = QPushButton("Search")
        self.search_symbol_button.clicked.connect(self.search_instruments)
        symbol_layout.addWidget(self.search_symbol_button)
        form_layout.addRow("Symbol:", symbol_layout)

        # Symbol suggestions
        self.symbol_suggestions = QComboBox()
        self.symbol_suggestions.setVisible(False)
        self.symbol_suggestions.currentTextChanged.connect(self.on_symbol_selected)
        form_layout.addRow("", self.symbol_suggestions)

        self.exchange_combo = QComboBox()
        self.exchange_combo.addItems(["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"])
        form_layout.addRow("Exchange:", self.exchange_combo)

        self.transaction_combo = QComboBox()
        self.transaction_combo.addItems(["BUY", "SELL"])
        self.transaction_combo.currentTextChanged.connect(self.update_order_preview)
        form_layout.addRow("Transaction:", self.transaction_combo)

        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(999999)
        self.quantity_input.valueChanged.connect(self.update_order_preview)
        form_layout.addRow("Quantity:", self.quantity_input)

        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["MARKET", "LIMIT", "SL", "SL-M"])
        self.order_type_combo.currentTextChanged.connect(self.on_order_type_changed)
        form_layout.addRow("Order Type:", self.order_type_combo)

        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.01)
        self.price_input.setMaximum(999999.99)
        self.price_input.setDecimals(2)
        self.price_input.valueChanged.connect(self.update_order_preview)
        form_layout.addRow("Price:", self.price_input)

        # Trigger price for stop loss orders
        self.trigger_price_input = QDoubleSpinBox()
        self.trigger_price_input.setMinimum(0.01)
        self.trigger_price_input.setMaximum(999999.99)
        self.trigger_price_input.setDecimals(2)
        self.trigger_price_input.setEnabled(False)
        self.trigger_price_input.valueChanged.connect(self.update_order_preview)
        form_layout.addRow("Trigger Price:", self.trigger_price_input)

        self.product_combo = QComboBox()
        self.product_combo.addItems(["CNC", "MIS", "NRML"])
        self.product_combo.currentTextChanged.connect(self.update_order_preview)
        form_layout.addRow("Product:", self.product_combo)

        # Validity combo
        self.validity_combo = QComboBox()
        self.validity_combo.addItems(["DAY", "IOC", "TTL"])
        self.validity_combo.currentTextChanged.connect(self.on_validity_changed)
        form_layout.addRow("Validity:", self.validity_combo)

        # TTL validity duration (only shown when TTL is selected)
        self.validity_ttl_input = QSpinBox()
        self.validity_ttl_input.setMinimum(1)
        self.validity_ttl_input.setMaximum(1440)  # Max 24 hours
        self.validity_ttl_input.setValue(60)  # Default 1 hour
        self.validity_ttl_input.setSuffix(" minutes")
        self.validity_ttl_input.setVisible(False)
        form_layout.addRow("TTL Duration:", self.validity_ttl_input)

        # Disclosed quantity
        self.disclosed_qty_input = QSpinBox()
        self.disclosed_qty_input.setMinimum(0)
        self.disclosed_qty_input.setMaximum(999999)
        form_layout.addRow("Disclosed Qty:", self.disclosed_qty_input)

        # Get quote button
        self.get_quote_button = QPushButton("Get Quote")
        self.get_quote_button.clicked.connect(self.get_symbol_quote)
        form_layout.addRow("", self.get_quote_button)

        # Current price display
        self.current_price_label = QLabel("Current Price: --")
        self.current_price_label.setStyleSheet("font-weight: bold; color: blue;")
        form_layout.addRow("", self.current_price_label)

        # Place order button
        self.place_order_button = QPushButton("Place Order")
        self.place_order_button.clicked.connect(self.place_order)
        self.place_order_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        form_layout.addRow("", self.place_order_button)

        place_order_layout.addWidget(form_group)

        # Right side - Order preview and risk analysis
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Order preview
        preview_group = QGroupBox("Order Preview")
        preview_layout = QGridLayout(preview_group)

        self.preview_symbol_label = QLabel("--")
        self.preview_transaction_label = QLabel("--")
        self.preview_quantity_label = QLabel("--")
        self.preview_price_label = QLabel("--")
        self.preview_value_label = QLabel("--")
        self.preview_charges_label = QLabel("--")
        self.preview_total_label = QLabel("--")

        preview_layout.addWidget(QLabel("Symbol:"), 0, 0)
        preview_layout.addWidget(self.preview_symbol_label, 0, 1)
        preview_layout.addWidget(QLabel("Transaction:"), 1, 0)
        preview_layout.addWidget(self.preview_transaction_label, 1, 1)
        preview_layout.addWidget(QLabel("Quantity:"), 2, 0)
        preview_layout.addWidget(self.preview_quantity_label, 2, 1)
        preview_layout.addWidget(QLabel("Price:"), 3, 0)
        preview_layout.addWidget(self.preview_price_label, 3, 1)
        preview_layout.addWidget(QLabel("Order Value:"), 4, 0)
        preview_layout.addWidget(self.preview_value_label, 4, 1)
        preview_layout.addWidget(QLabel("Est. Charges:"), 5, 0)
        preview_layout.addWidget(self.preview_charges_label, 5, 1)
        preview_layout.addWidget(QLabel("Total Required:"), 6, 0)
        preview_layout.addWidget(self.preview_total_label, 6, 1)

        right_layout.addWidget(preview_group)

        # Risk analysis
        risk_group = QGroupBox("Risk Analysis")
        risk_layout = QGridLayout(risk_group)

        self.available_margin_label = QLabel("--")
        self.required_margin_label = QLabel("--")
        self.margin_utilization_label = QLabel("--")
        self.risk_level_label = QLabel("--")

        risk_layout.addWidget(QLabel("Available Margin:"), 0, 0)
        risk_layout.addWidget(self.available_margin_label, 0, 1)
        risk_layout.addWidget(QLabel("Required Margin:"), 1, 0)
        risk_layout.addWidget(self.required_margin_label, 1, 1)
        risk_layout.addWidget(QLabel("Margin Utilization:"), 2, 0)
        risk_layout.addWidget(self.margin_utilization_label, 2, 1)
        risk_layout.addWidget(QLabel("Risk Level:"), 3, 0)
        risk_layout.addWidget(self.risk_level_label, 3, 1)

        right_layout.addWidget(risk_group)

        # Quick order buttons
        quick_order_group = QGroupBox("Quick Orders")
        quick_order_layout = QGridLayout(quick_order_group)

        self.quick_buy_button = QPushButton("Quick Buy")
        self.quick_buy_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.quick_buy_button.clicked.connect(lambda: self.quick_order("BUY"))
        quick_order_layout.addWidget(self.quick_buy_button, 0, 0)

        self.quick_sell_button = QPushButton("Quick Sell")
        self.quick_sell_button.setStyleSheet("background-color: #f44336; color: white;")
        self.quick_sell_button.clicked.connect(lambda: self.quick_order("SELL"))
        quick_order_layout.addWidget(self.quick_sell_button, 0, 1)

        self.square_off_button = QPushButton("Square Off All")
        self.square_off_button.setStyleSheet("background-color: #ff9800; color: white;")
        self.square_off_button.clicked.connect(self.square_off_all_positions)
        quick_order_layout.addWidget(self.square_off_button, 1, 0, 1, 2)

        right_layout.addWidget(quick_order_group)
        right_layout.addStretch()

        place_order_layout.addWidget(right_panel)
        trading_tabs.addTab(place_order_widget, "Place Order")

        layout.addWidget(trading_tabs)
        return tab
    
    def create_settings_tab(self):
        """Create comprehensive settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Settings tabs
        settings_tabs = QTabWidget()

        # API Configuration tab
        api_widget = QWidget()
        api_layout = QVBoxLayout(api_widget)

        # API settings
        api_group = QGroupBox("Zerodha API Configuration")
        api_form_layout = QFormLayout(api_group)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your Zerodha API key")
        api_form_layout.addRow("API Key:", self.api_key_input)

        self.api_secret_input = QLineEdit()
        self.api_secret_input.setEchoMode(QLineEdit.Password)
        self.api_secret_input.setPlaceholderText("Enter your Zerodha API secret")
        api_form_layout.addRow("API Secret:", self.api_secret_input)

        # Show/Hide API secret button
        show_secret_layout = QHBoxLayout()
        self.show_secret_checkbox = QCheckBox("Show API Secret")
        self.show_secret_checkbox.toggled.connect(self.toggle_api_secret_visibility)
        show_secret_layout.addWidget(self.show_secret_checkbox)
        show_secret_layout.addStretch()
        api_form_layout.addRow("", show_secret_layout)

        self.sandbox_checkbox = QCheckBox("Sandbox Mode (for testing)")
        self.sandbox_checkbox.setChecked(True)
        api_form_layout.addRow("", self.sandbox_checkbox)

        self.auto_connect_checkbox = QCheckBox("Auto-connect on startup")
        self.auto_connect_checkbox.setChecked(False)
        api_form_layout.addRow("", self.auto_connect_checkbox)

        # Connection timeout
        self.connection_timeout_spinbox = QSpinBox()
        self.connection_timeout_spinbox.setMinimum(5)
        self.connection_timeout_spinbox.setMaximum(60)
        self.connection_timeout_spinbox.setValue(30)
        self.connection_timeout_spinbox.setSuffix(" seconds")
        api_form_layout.addRow("Connection Timeout:", self.connection_timeout_spinbox)

        # Max retry attempts
        self.max_retry_spinbox = QSpinBox()
        self.max_retry_spinbox.setMinimum(1)
        self.max_retry_spinbox.setMaximum(10)
        self.max_retry_spinbox.setValue(3)
        api_form_layout.addRow("Max Retry Attempts:", self.max_retry_spinbox)

        api_layout.addWidget(api_group)

        # API status and testing
        status_group = QGroupBox("API Status & Testing")
        status_layout = QGridLayout(status_group)

        self.api_status_label = QLabel("Not Connected")
        self.api_status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(QLabel("Status:"), 0, 0)
        status_layout.addWidget(self.api_status_label, 0, 1)

        # Additional API status information
        self.api_session_label = QLabel("--")
        status_layout.addWidget(QLabel("Session:"), 0, 2)
        status_layout.addWidget(self.api_session_label, 0, 3)

        self.api_last_request_label = QLabel("--")
        status_layout.addWidget(QLabel("Last Request:"), 1, 0)
        status_layout.addWidget(self.api_last_request_label, 1, 1)

        self.api_rate_limit_label = QLabel("--")
        status_layout.addWidget(QLabel("Rate Limit:"), 1, 2)
        status_layout.addWidget(self.api_rate_limit_label, 1, 3)

        self.api_uptime_label = QLabel("--")
        status_layout.addWidget(QLabel("Connection Uptime:"), 2, 0)
        status_layout.addWidget(self.api_uptime_label, 2, 1)

        self.api_requests_count_label = QLabel("0")
        status_layout.addWidget(QLabel("Requests Made:"), 2, 2)
        status_layout.addWidget(self.api_requests_count_label, 2, 3)

        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.test_api_connection)
        status_layout.addWidget(self.test_connection_button, 3, 0)

        self.clear_credentials_button = QPushButton("Clear Credentials")
        self.clear_credentials_button.clicked.connect(self.clear_api_credentials)
        self.clear_credentials_button.setStyleSheet("background-color: #ff6b6b; color: white;")
        status_layout.addWidget(self.clear_credentials_button, 3, 1)

        self.refresh_api_status_button = QPushButton("Refresh API Status")
        self.refresh_api_status_button.clicked.connect(self.refresh_api_status)
        status_layout.addWidget(self.refresh_api_status_button, 3, 2)

        api_layout.addWidget(status_group)

        # Save API settings button
        save_api_button = QPushButton("Save API Settings")
        save_api_button.clicked.connect(self.save_settings)
        save_api_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        api_layout.addWidget(save_api_button)

        api_layout.addStretch()
        settings_tabs.addTab(api_widget, "API Configuration")

        # Application Settings tab
        app_widget = QWidget()
        app_layout = QVBoxLayout(app_widget)

        # Data refresh settings
        refresh_group = QGroupBox("Data Refresh Settings")
        refresh_layout = QFormLayout(refresh_group)

        self.auto_refresh_checkbox = QCheckBox("Enable automatic data refresh")
        self.auto_refresh_checkbox.setChecked(True)
        refresh_layout.addRow("", self.auto_refresh_checkbox)

        self.refresh_interval_spinbox = QSpinBox()
        self.refresh_interval_spinbox.setMinimum(5)
        self.refresh_interval_spinbox.setMaximum(300)
        self.refresh_interval_spinbox.setValue(30)
        self.refresh_interval_spinbox.setSuffix(" seconds")
        refresh_layout.addRow("Refresh Interval:", self.refresh_interval_spinbox)

        self.refresh_on_focus_checkbox = QCheckBox("Refresh data when window gains focus")
        self.refresh_on_focus_checkbox.setChecked(True)
        refresh_layout.addRow("", self.refresh_on_focus_checkbox)

        app_layout.addWidget(refresh_group)

        # Display settings
        display_group = QGroupBox("Display Settings")
        display_layout = QFormLayout(display_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        self.theme_combo.setCurrentText("System")
        display_layout.addRow("Theme:", self.theme_combo)

        self.decimal_places_spinbox = QSpinBox()
        self.decimal_places_spinbox.setMinimum(0)
        self.decimal_places_spinbox.setMaximum(6)
        self.decimal_places_spinbox.setValue(2)
        display_layout.addRow("Decimal Places:", self.decimal_places_spinbox)

        self.show_zero_positions_checkbox = QCheckBox("Show zero quantity positions")
        self.show_zero_positions_checkbox.setChecked(False)
        display_layout.addRow("", self.show_zero_positions_checkbox)

        self.compact_view_checkbox = QCheckBox("Use compact table view")
        self.compact_view_checkbox.setChecked(False)
        display_layout.addRow("", self.compact_view_checkbox)

        app_layout.addWidget(display_group)

        # Notification settings
        notification_group = QGroupBox("Notification Settings")
        notification_layout = QFormLayout(notification_group)

        self.enable_notifications_checkbox = QCheckBox("Enable notifications")
        self.enable_notifications_checkbox.setChecked(True)
        notification_layout.addRow("", self.enable_notifications_checkbox)

        self.notify_order_updates_checkbox = QCheckBox("Notify on order updates")
        self.notify_order_updates_checkbox.setChecked(True)
        notification_layout.addRow("", self.notify_order_updates_checkbox)

        self.notify_position_changes_checkbox = QCheckBox("Notify on position changes")
        self.notify_position_changes_checkbox.setChecked(False)
        notification_layout.addRow("", self.notify_position_changes_checkbox)

        self.notify_connection_status_checkbox = QCheckBox("Notify on connection status changes")
        self.notify_connection_status_checkbox.setChecked(True)
        notification_layout.addRow("", self.notify_connection_status_checkbox)

        app_layout.addWidget(notification_group)

        # Save app settings button
        save_app_button = QPushButton("Save Application Settings")
        save_app_button.clicked.connect(self.save_app_settings)
        save_app_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        app_layout.addWidget(save_app_button)

        app_layout.addStretch()
        settings_tabs.addTab(app_widget, "Application Settings")

        # Account Management tab
        account_widget = QWidget()
        account_layout = QVBoxLayout(account_widget)

        # Account information
        account_info_group = QGroupBox("Account Information")
        account_info_layout = QGridLayout(account_info_group)

        self.account_id_label = QLabel("--")
        self.account_name_label = QLabel("--")
        self.account_type_label = QLabel("--")
        self.account_status_label = QLabel("--")
        self.account_email_label = QLabel("--")
        self.account_broker_label = QLabel("--")
        self.account_shortname_label = QLabel("--")
        self.account_exchanges_label = QLabel("--")
        self.account_products_label = QLabel("--")
        self.account_order_types_label = QLabel("--")

        account_info_layout.addWidget(QLabel("Account ID:"), 0, 0)
        account_info_layout.addWidget(self.account_id_label, 0, 1)
        account_info_layout.addWidget(QLabel("Account Name:"), 0, 2)
        account_info_layout.addWidget(self.account_name_label, 0, 3)
        account_info_layout.addWidget(QLabel("Short Name:"), 1, 0)
        account_info_layout.addWidget(self.account_shortname_label, 1, 1)
        account_info_layout.addWidget(QLabel("Account Type:"), 1, 2)
        account_info_layout.addWidget(self.account_type_label, 1, 3)
        account_info_layout.addWidget(QLabel("Email:"), 2, 0)
        account_info_layout.addWidget(self.account_email_label, 2, 1)
        account_info_layout.addWidget(QLabel("Broker:"), 2, 2)
        account_info_layout.addWidget(self.account_broker_label, 2, 3)
        account_info_layout.addWidget(QLabel("Status:"), 3, 0)
        account_info_layout.addWidget(self.account_status_label, 3, 1)
        account_info_layout.addWidget(QLabel("Exchanges:"), 4, 0)
        account_info_layout.addWidget(self.account_exchanges_label, 4, 1, 1, 3)
        account_info_layout.addWidget(QLabel("Products:"), 5, 0)
        account_info_layout.addWidget(self.account_products_label, 5, 1, 1, 3)
        account_info_layout.addWidget(QLabel("Order Types:"), 6, 0)
        account_info_layout.addWidget(self.account_order_types_label, 6, 1, 1, 3)

        self.refresh_account_button = QPushButton("Refresh Account Info")
        self.refresh_account_button.clicked.connect(self.refresh_account_info)
        account_info_layout.addWidget(self.refresh_account_button, 7, 0, 1, 2)

        account_layout.addWidget(account_info_group)

        # Trading limits and permissions
        limits_group = QGroupBox("Trading Limits & Permissions")
        limits_layout = QGridLayout(limits_group)

        self.equity_limit_label = QLabel("--")
        self.commodity_limit_label = QLabel("--")
        self.intraday_limit_label = QLabel("--")
        self.margin_available_label = QLabel("--")
        self.margin_used_label = QLabel("--")
        self.cash_balance_label = QLabel("--")

        limits_layout.addWidget(QLabel("Equity Limit:"), 0, 0)
        limits_layout.addWidget(self.equity_limit_label, 0, 1)
        limits_layout.addWidget(QLabel("Commodity Limit:"), 0, 2)
        limits_layout.addWidget(self.commodity_limit_label, 0, 3)
        limits_layout.addWidget(QLabel("Intraday Limit:"), 1, 0)
        limits_layout.addWidget(self.intraday_limit_label, 1, 1)
        limits_layout.addWidget(QLabel("Available Margin:"), 1, 2)
        limits_layout.addWidget(self.margin_available_label, 1, 3)
        limits_layout.addWidget(QLabel("Used Margin:"), 2, 0)
        limits_layout.addWidget(self.margin_used_label, 2, 1)
        limits_layout.addWidget(QLabel("Cash Balance:"), 2, 2)
        limits_layout.addWidget(self.cash_balance_label, 2, 3)

        self.refresh_limits_button = QPushButton("Refresh Limits")
        self.refresh_limits_button.clicked.connect(self.refresh_trading_limits)
        limits_layout.addWidget(self.refresh_limits_button, 3, 0, 1, 2)

        account_layout.addWidget(limits_group)

        # Data management
        data_group = QGroupBox("Data Management")
        data_layout = QGridLayout(data_group)

        self.clear_cache_button = QPushButton("Clear Cache")
        self.clear_cache_button.clicked.connect(self.clear_application_cache)
        data_layout.addWidget(self.clear_cache_button, 0, 0)

        self.export_data_button = QPushButton("Export Data")
        self.export_data_button.clicked.connect(self.export_application_data)
        data_layout.addWidget(self.export_data_button, 0, 1)

        self.backup_settings_button = QPushButton("Backup Settings")
        self.backup_settings_button.clicked.connect(self.backup_application_settings)
        data_layout.addWidget(self.backup_settings_button, 1, 0)

        self.restore_settings_button = QPushButton("Restore Settings")
        self.restore_settings_button.clicked.connect(self.restore_application_settings)
        data_layout.addWidget(self.restore_settings_button, 1, 1)

        account_layout.addWidget(data_group)

        # Reset and logout
        reset_group = QGroupBox("Reset & Logout")
        reset_layout = QVBoxLayout(reset_group)

        self.reset_settings_button = QPushButton("Reset All Settings")
        self.reset_settings_button.clicked.connect(self.reset_all_settings)
        self.reset_settings_button.setStyleSheet("background-color: #ff9800; color: white;")
        reset_layout.addWidget(self.reset_settings_button)

        self.logout_button = QPushButton("Logout & Clear Session")
        self.logout_button.clicked.connect(self.logout_and_clear_session)
        self.logout_button.setStyleSheet("background-color: #f44336; color: white;")
        reset_layout.addWidget(self.logout_button)

        account_layout.addWidget(reset_group)
        account_layout.addStretch()
        settings_tabs.addTab(account_widget, "Account Management")

        layout.addWidget(settings_tabs)
        return tab

    def load_settings(self):
        """Load trading settings"""
        try:
            settings_file = self.data_manager.data_dir / "trading_settings.json"
            if settings_file.exists():
                import json
                with open(settings_file, 'r') as f:
                    settings = json.load(f)

                self.trading_config.api_key = settings.get('api_key', '')
                self.trading_config.api_secret = settings.get('api_secret', '')
                self.trading_config.sandbox_mode = settings.get('sandbox_mode', True)
                self.trading_config.auto_login = settings.get('auto_login', False)

                # Update UI
                self.api_key_input.setText(self.trading_config.api_key)
                self.api_secret_input.setText(self.trading_config.api_secret)
                self.sandbox_checkbox.setChecked(self.trading_config.sandbox_mode)
                self.auto_connect_checkbox.setChecked(self.trading_config.auto_login)

        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save trading settings"""
        try:
            self.trading_config.api_key = self.api_key_input.text().strip()
            self.trading_config.api_secret = self.api_secret_input.text().strip()
            self.trading_config.sandbox_mode = self.sandbox_checkbox.isChecked()
            self.trading_config.auto_login = self.auto_connect_checkbox.isChecked()

            settings = {
                'api_key': self.trading_config.api_key,
                'api_secret': self.trading_config.api_secret,
                'sandbox_mode': self.trading_config.sandbox_mode,
                'auto_login': self.trading_config.auto_login
            }

            settings_file = self.data_manager.data_dir / "trading_settings.json"
            import json
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            QMessageBox.information(self, "Settings", "Settings saved successfully!")

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def connect_to_zerodha(self):
        """Connect to Zerodha API"""
        try:
            if not self.trading_config.api_key or not self.trading_config.api_secret:
                QMessageBox.warning(self, "Settings Required",
                                  "Please configure API key and secret in Settings tab first.")
                self.tab_widget.setCurrentIndex(4)  # Switch to settings tab
                return

            # Initialize API client
            self.api_client = ZerodhaAPIClient(self.trading_config, self.data_manager.data_dir)

            if not self.api_client.kite:
                QMessageBox.critical(self, "Error", "Failed to initialize Zerodha API client.")
                return

            # Check if already authenticated
            if self.api_client.is_authenticated():
                self.update_connection_status(True)
                self.refresh_data()
                return

            # Get login URL and show authentication dialog
            login_url = self.api_client.get_login_url()
            auth_dialog = AuthenticationDialog(login_url, self)

            if auth_dialog.exec() == QDialog.Accepted:
                request_token = auth_dialog.get_request_token()
                if request_token:
                    if self.api_client.authenticate(request_token):
                        self.update_connection_status(True)
                        self.initialize_token_manager()
                        self.refresh_data()
                        QMessageBox.information(self, "Success", "Connected to Zerodha successfully!")
                    else:
                        QMessageBox.critical(self, "Error", "Authentication failed. Please try again.")
                else:
                    QMessageBox.warning(self, "Warning", "Please enter the request token.")

        except Exception as e:
            self.logger.error(f"Failed to connect to Zerodha: {e}")
            QMessageBox.critical(self, "Error", f"Failed to connect: {e}")

    def force_reconnect(self):
        """Force reconnection by clearing tokens and re-authenticating"""
        try:
            if self.api_client:
                # Clear expired tokens
                self.api_client._clear_expired_tokens()
                self.api_client.is_connected = False

            # Update UI
            self.update_connection_status(False)

            # Initiate new connection
            self.connect_to_zerodha()

        except Exception as e:
            self.logger.error(f"Failed to force reconnect: {e}")
            QMessageBox.critical(self, "Error", f"Failed to force reconnect: {e}")

    def show_startup_auth_dialog(self):
        """Show startup authentication dialog"""
        try:
            # Check if user has already made a choice today
            if self.should_skip_startup_dialog():
                self.logger.info("Skipping startup dialog based on user preference")
                self.check_auto_connect()
                return

            # Create and show startup dialog
            startup_dialog = ZerodhaStartupDialog(self)

            # Check current token status
            has_token = False
            token_info = {}
            if self.api_client and self.api_client.is_authenticated():
                profile = self.api_client.get_profile()
                if profile:
                    has_token = True
                    token_info = profile

            startup_dialog.update_token_status(has_token, token_info)

            # Connect signals
            startup_dialog.connect_now_requested.connect(self.on_startup_connect_now)
            startup_dialog.connect_later_requested.connect(self.on_startup_connect_later)

            # Show dialog
            result = startup_dialog.exec()

            # Save user preference if requested
            if startup_dialog.should_remember_choice():
                self.save_startup_choice(startup_dialog.get_user_choice())

            self.startup_auth_completed = True

        except Exception as e:
            self.logger.error(f"Error showing startup auth dialog: {e}")
            # Fallback to auto-connect behavior
            self.check_auto_connect()

    def on_startup_connect_now(self):
        """Handle startup 'Connect Now' choice"""
        self.logger.info("User chose to connect now")
        self.authentication_skipped = False
        self.connect_to_zerodha()

    def on_startup_connect_later(self):
        """Handle startup 'Connect Later' choice"""
        self.logger.info("User chose to connect later")
        self.authentication_skipped = True
        self.update_connection_status(False)
        self.show_connect_later_info()

    def show_connect_later_info(self):
        """Show information about connecting later"""
        try:
            info_msg = (
                "Trading connection skipped.\n\n"
                "✅ All other app features are fully available:\n"
                "• Expense tracking and analysis\n"
                "• Bank statement import\n"
                "• Financial reports\n\n"
                "🔗 To connect to Zerodha later:\n"
                "• Click the 'Connect' button in this tab\n"
                "• Or use 'Force Reconnect' if needed"
            )

            QMessageBox.information(self, "Trading Connection Skipped", info_msg)

        except Exception as e:
            self.logger.error(f"Error showing connect later info: {e}")

    def show_auth_help(self):
        """Show authentication help dialog"""
        try:
            help_dialog = ZerodhaEducationDialog(self)
            help_dialog.exec()
        except Exception as e:
            self.logger.error(f"Error showing auth help: {e}")

    def initialize_token_manager(self):
        """Initialize token manager for automated validation"""
        try:
            if self.api_client and not self.token_manager:
                self.token_manager = TokenManager(self.api_client, self.data_manager.data_dir, self)

                # Connect signals
                self.token_manager.token_expired.connect(self.on_token_expired)
                self.token_manager.authentication_required.connect(self.on_authentication_required)
                self.token_manager.connection_status_changed.connect(self.on_connection_status_changed)

                # Start monitoring if connected
                if self.api_client.is_authenticated():
                    self.token_manager.start_monitoring()

                self.logger.info("Token manager initialized")

        except Exception as e:
            self.logger.error(f"Error initializing token manager: {e}")

    def on_token_expired(self):
        """Handle token expiry signal"""
        self.logger.warning("Token expired - updating UI")
        self.update_connection_status(False)

    def on_authentication_required(self):
        """Handle authentication required signal"""
        self.logger.info("Authentication required - showing notification")
        # This will be handled by the connection loss handler

    def on_connection_status_changed(self, connected: bool):
        """Handle connection status change from token manager"""
        self.logger.info(f"Connection status changed: {connected}")
        self.update_connection_status(connected)

        # Update token status widget
        if hasattr(self, 'token_status_widget'):
            token_info = {}
            if connected and self.token_manager:
                token_status = self.token_manager.get_token_status()
                token_info = token_status.get('token_info', {})
            self.token_status_widget.update_status(connected, token_info)

    def show_no_connection_message(self):
        """Show helpful message when trading features are unavailable"""
        try:
            # Clear existing data displays
            self.clear_data_displays()

            # Show informative message in the main content area
            if hasattr(self, 'tab_widget'):
                # Create a message widget for each tab
                self.show_connection_required_message()

        except Exception as e:
            self.logger.error(f"Error showing no connection message: {e}")

    def show_connection_required_message(self):
        """Show connection required message in trading tabs"""
        try:
            # Create a central message widget
            message_widget = QWidget()
            message_layout = QVBoxLayout(message_widget)
            message_layout.setAlignment(Qt.AlignCenter)

            # Icon and title
            title_label = QLabel("🔗 Trading Connection Required")
            title_font = QFont()
            title_font.setPointSize(18)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("color: #2E86AB; margin-bottom: 20px;")
            message_layout.addWidget(title_label)

            # Information text
            info_text = QLabel("""
<div style="text-align: center; font-size: 12px; line-height: 1.6;">
<b>Trading features are currently unavailable.</b><br><br>

<b>To access trading functionality:</b><br>
• Click the <b>"Connect"</b> button above<br>
• Or use <b>"Force Reconnect"</b> if you had a previous connection<br><br>

<b>✅ Other app features remain fully functional:</b><br>
• Expense tracking and analysis<br>
• Bank statement import and categorization<br>
• Financial reports and charts<br>
• Investment tracking<br>
• Budget planning<br><br>

<i>💡 You can use the application normally and connect to trading when ready!</i>
</div>
            """)
            info_text.setWordWrap(True)
            info_text.setAlignment(Qt.AlignCenter)
            info_text.setStyleSheet("""
                QLabel {
                    background-color: #F8F9FA;
                    border: 1px solid #DEE2E6;
                    border-radius: 8px;
                    padding: 20px;
                    max-width: 500px;
                }
            """)
            message_layout.addWidget(info_text)

            # Replace tab content with message
            if hasattr(self, 'dashboard_tab'):
                # Clear and replace dashboard content
                dashboard_layout = self.dashboard_tab.layout()
                if dashboard_layout:
                    # Clear existing widgets
                    while dashboard_layout.count():
                        child = dashboard_layout.takeAt(0)
                        if child.widget():
                            child.widget().hide()

                    # Add message
                    dashboard_layout.addWidget(message_widget)

        except Exception as e:
            self.logger.error(f"Error showing connection required message: {e}")

    def check_auto_connect(self):
        """Check if auto-connect should be performed"""
        try:
            if (self.trading_config.auto_login and
                self.trading_config.api_key and
                self.trading_config.api_secret):
                self.logger.info("Auto-connect enabled, attempting to connect...")
                self.auto_connect()
        except Exception as e:
            self.logger.error(f"Error in check_auto_connect: {e}")

    def should_skip_startup_dialog(self) -> bool:
        """Check if startup dialog should be skipped based on user preference"""
        try:
            from datetime import datetime, date

            # Check if user has made a choice for today
            settings_file = self.data_manager.data_dir / "startup_auth_choice.json"
            if settings_file.exists():
                import json
                with open(settings_file, 'r') as f:
                    choice_data = json.load(f)

                choice_date = datetime.fromisoformat(choice_data.get('date', ''))
                if choice_date.date() == date.today():
                    choice = choice_data.get('choice')
                    if choice == 'connect_later':
                        self.authentication_skipped = True
                        return True
                    elif choice == 'connect_now':
                        # Auto-connect if user chose connect now
                        self.check_auto_connect()
                        return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking startup dialog skip: {e}")
            return False

    def save_startup_choice(self, choice: str):
        """Save user's startup authentication choice"""
        try:
            from datetime import datetime
            import json

            choice_data = {
                'choice': choice,
                'date': datetime.now().isoformat(),
                'timestamp': datetime.now().timestamp()
            }

            settings_file = self.data_manager.data_dir / "startup_auth_choice.json"
            with open(settings_file, 'w') as f:
                json.dump(choice_data, f, indent=2)

            self.logger.info(f"Saved startup choice: {choice}")

        except Exception as e:
            self.logger.error(f"Error saving startup choice: {e}")

    def auto_connect(self):
        """Automatically connect to Zerodha using saved credentials"""
        try:
            if not self.trading_config.api_key or not self.trading_config.api_secret:
                self.logger.warning("Auto-connect failed: Missing API credentials")
                return

            # Initialize API client
            self.api_client = ZerodhaAPIClient(self.trading_config, self.data_manager.data_dir)

            if not self.api_client.kite:
                self.logger.error("Auto-connect failed: Could not initialize API client")
                return

            # Check if already authenticated with saved tokens
            if self.api_client.is_authenticated():
                self.logger.info("Auto-connect successful: Using saved tokens")
                self.update_connection_status(True)
                self.refresh_data()
                self.start_auto_refresh()
            else:
                self.logger.info("Auto-connect: No valid saved tokens, manual authentication required")
                self.status_label.setText("Auto-connect: Manual authentication required")
                self.status_label.setStyleSheet("color: orange; font-weight: bold;")

        except Exception as e:
            self.logger.error(f"Auto-connect failed: {e}")
            self.status_label.setText("Auto-connect failed")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def retry_connection(self):
        """Retry connection with exponential backoff"""
        try:
            if self.retry_attempts >= self.max_retry_attempts:
                self.logger.error("Max retry attempts reached, stopping retries")
                self.retry_timer.stop()
                self.status_label.setText("Connection failed - Max retries reached")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                return

            self.retry_attempts += 1
            self.logger.info(f"Retry attempt {self.retry_attempts}/{self.max_retry_attempts}")

            self.status_label.setText(f"Retrying connection... ({self.retry_attempts}/{self.max_retry_attempts})")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")

            # Try to reconnect
            self.auto_connect()

            # If still not connected, schedule next retry with exponential backoff
            if not (self.api_client and self.api_client.is_authenticated()):
                retry_delay = min(5000 * (2 ** (self.retry_attempts - 1)), 30000)  # Max 30 seconds
                self.retry_timer.start(retry_delay)
            else:
                # Connection successful, reset retry counter
                self.retry_attempts = 0
                self.retry_timer.stop()

        except Exception as e:
            self.logger.error(f"Error in retry_connection: {e}")

    def start_auto_refresh(self):
        """Start automatic data refresh with intelligent system"""
        if self.api_client and self.api_client.is_authenticated():
            self.start_intelligent_refresh_system()
            self.logger.info("Intelligent auto-refresh system started")

    def disconnect_from_zerodha(self):
        """Disconnect from Zerodha API"""
        try:
            self.logger.info("Disconnecting from Zerodha...")

            # Stop all refresh timers
            self.stop_refresh_system()
            self.retry_timer.stop()

            # Reset connection state
            if self.api_client:
                self.api_client.is_connected = False
                self.api_client = None

            # Reset retry counter
            self.retry_attempts = 0

            # Update UI
            self.update_connection_status(False)

            # Clear data displays
            self.clear_all_data_displays()

            self.logger.info("Successfully disconnected from Zerodha")

        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")

    def clear_all_data_displays(self):
        """Clear all data displays when disconnected"""
        try:
            # Clear tables
            self.positions_table.setRowCount(0)
            self.holdings_table.setRowCount(0)
            self.orders_table.setRowCount(0)

            # Reset labels
            self.equity_label.setText("₹0.00")
            self.commodity_label.setText("₹0.00")
            self.total_label.setText("₹0.00")
            self.positions_count_label.setText("0")
            self.holdings_count_label.setText("0")
            self.orders_count_label.setText("0")

            self.logger.debug("All data displays cleared")

        except Exception as e:
            self.logger.error(f"Error clearing data displays: {e}")

    def update_connection_status(self, connected: bool):
        """Update connection status UI"""
        if connected:
            self.status_label.setText("Connected to Zerodha")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")

            # Update user profile display
            if self.api_client and self.api_client.is_authenticated():
                # Try to get fresh profile data
                profile = self.api_client.get_profile()
                if profile:
                    user_name = profile.get('user_name', 'Unknown User')
                    user_id = profile.get('user_id', 'Unknown ID')
                    broker = profile.get('broker', 'Unknown Broker')
                    self.profile_label.setText(f"{user_name} ({user_id}) - {broker}")
                    self.profile_label.setStyleSheet("color: green; font-size: 10px;")
                    self.logger.debug(f"🔗 Connection status profile updated for: {user_name}")
                else:
                    self.profile_label.setText("Profile loading...")
                    self.profile_label.setStyleSheet("color: orange; font-size: 10px;")
            else:
                self.profile_label.setText("Profile loading...")
                self.profile_label.setStyleSheet("color: orange; font-size: 10px;")

            self.connect_button.setText("Disconnect")
            self.connect_button.clicked.disconnect()
            self.connect_button.clicked.connect(self.disconnect_from_zerodha)
            self.force_reconnect_button.setVisible(False)  # Hide when connected
        else:
            self.status_label.setText("Not Connected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.profile_label.setText("No user profile")
            self.profile_label.setStyleSheet("color: gray; font-size: 10px;")
            self.connect_button.setText("Connect")
            self.connect_button.clicked.disconnect()
            self.connect_button.clicked.connect(self.connect_to_zerodha)
            self.force_reconnect_button.setVisible(True)  # Show when disconnected

    def update_user_profile_display(self):
        """Update user profile display in dashboard"""
        try:
            if self.api_client and self.api_client.is_authenticated():
                # Fetch fresh profile data
                profile = self.api_client.get_profile()
                if profile:
                    # Format user profile information based on API documentation structure
                    profile_text = f"""
<b>User Information:</b><br>
• Name: {profile.get('user_name', 'N/A')}<br>
• User ID: {profile.get('user_id', 'N/A')}<br>
• Email: {profile.get('email', 'N/A')}<br>
• Broker: {profile.get('broker', 'N/A')}<br>
• User Type: {profile.get('user_type', 'N/A')}<br>
• Login Time: {profile.get('login_time', 'N/A')}<br>

<b>Enabled Exchanges:</b><br>
{', '.join(profile.get('exchanges', []))}<br>

<b>Available Products:</b><br>
{', '.join(profile.get('products', []))}<br>

<b>Order Types:</b><br>
{', '.join(profile.get('order_types', []))}
                    """.strip()

                    if hasattr(self, 'user_profile_display'):
                        self.user_profile_display.setText(profile_text)
                        self.user_profile_display.setStyleSheet("color: black; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
                        self.logger.debug(f"✅ User profile display updated successfully")
                    else:
                        self.logger.warning(f"⚠️ user_profile_display widget not found")

                    self.logger.debug(f"👤 User profile updated for: {profile.get('user_name', 'N/A')}")
                else:
                    self.logger.warning(f"⚠️ Profile data is None")
                    if hasattr(self, 'user_profile_display'):
                        self.user_profile_display.setText("Profile loading...")
                        self.user_profile_display.setStyleSheet("color: orange; padding: 10px;")
            else:
                if hasattr(self, 'user_profile_display'):
                    self.user_profile_display.setText("Connect to view user profile")
                    self.user_profile_display.setStyleSheet("color: gray; padding: 10px;")
        except Exception as e:
            self.logger.error(f"❌ Failed to update user profile display: {e}")
            if hasattr(self, 'user_profile_display'):
                self.user_profile_display.setText("Error loading profile")
                self.user_profile_display.setStyleSheet("color: red; padding: 10px;")


        self.refresh_timer.stop()
        self.auto_refresh_checkbox.setChecked(False)

    def toggle_auto_refresh(self, enabled: bool):
        """Toggle auto refresh with intelligent system"""
        if enabled and self.api_client and self.api_client.is_authenticated():
            self.start_intelligent_refresh_system()
        else:
            self.stop_refresh_system()

    def refresh_data(self):
        """Refresh all trading data with graceful degradation"""
        if not self.api_client or not self.api_client.is_authenticated():
            if not self.authentication_skipped:
                self.logger.warning("Cannot refresh data - API client not authenticated")
            else:
                self.logger.info("Skipping data refresh - authentication was skipped by user")
            self.show_no_connection_message()
            return

        try:
            self.logger.info("🔄 Starting data refresh...")

            # Update user profile display
            self.update_user_profile_display()

            # Get margins for account summary
            self.logger.debug("📊 Fetching margins...")
            margins = self.api_client.get_margins()
            self.logger.info(f"📊 Margins data: {margins is not None}")
            if margins:
                self.logger.debug(f"📊 Equity available: {margins.get('equity', {}).get('available', {}).get('cash', 0)}")
                self.update_account_summary(margins)

            # Get positions
            self.logger.debug("📈 Fetching positions...")
            positions = self.api_client.get_positions()
            self.logger.info(f"📈 Retrieved {len(positions)} positions")
            if positions:
                for i, pos in enumerate(positions[:3]):  # Log first 3 positions
                    self.logger.debug(f"📈 Position {i+1}: {pos.tradingsymbol} - Qty: {pos.quantity}, P&L: ₹{pos.pnl}")
            self.update_positions_table(positions)

            # Get all holdings (regular + mutual funds)
            self.logger.debug("💼 Fetching all holdings...")
            all_holdings_data = self.api_client.get_all_holdings()

            regular_holdings = all_holdings_data['regular_holdings']
            mf_holdings = all_holdings_data['mutual_fund_holdings']
            summary = all_holdings_data['summary']

            self.logger.info(f"💼 Retrieved {summary['regular_count']} regular holdings, {summary['mutual_fund_count']} mutual fund holdings")
            self.logger.info(f"💰 Total P&L: Regular ₹{summary['regular_pnl']:.2f}, MF ₹{summary['mutual_fund_pnl']:.2f}, Combined ₹{summary['total_pnl']:.2f}")

            # Log sample holdings
            if regular_holdings:
                for i, holding in enumerate(regular_holdings[:3]):
                    self.logger.debug(f"📈 Regular Holding {i+1}: {holding.tradingsymbol} - Qty: {holding.quantity}, P&L: ₹{holding.pnl}")
            if mf_holdings:
                for i, holding in enumerate(mf_holdings[:3]):
                    self.logger.debug(f"🏦 MF Holding {i+1}: {holding.fund[:30]}... - Qty: {holding.quantity}, P&L: ₹{holding.pnl}")

            # Update holdings display with all data
            self.update_comprehensive_holdings_display(all_holdings_data)

            # Calculate and update portfolio analytics
            self.calculate_portfolio_analytics(positions, regular_holdings)

            # Get orders
            self.logger.debug("📋 Fetching orders...")
            orders = self.api_client.get_orders()
            self.logger.info(f"📋 Retrieved {len(orders)} orders")
            if orders:
                for i, order in enumerate(orders[:3]):  # Log first 3 orders
                    self.logger.debug(f"📋 Order {i+1}: {order.tradingsymbol} - {order.transaction_type} {order.quantity} @ ₹{order.price}")
            self.update_orders_table(orders)

            # Update quick stats
            self.positions_count_label.setText(str(len(positions)))
            self.holdings_count_label.setText(str(summary['total_count']))
            today_orders = [o for o in orders if o.order_timestamp.date() == datetime.now().date()]
            self.orders_count_label.setText(str(len(today_orders)))
            self.logger.debug(f"📋 Today's orders: {len(today_orders)}")

            # Update trading analytics (apply current filters)
            self.apply_history_filters()

            # Refresh watchlist and market overview
            self.refresh_watchlist()
            self.update_market_overview()

            self.logger.info("✅ Data refresh completed successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to refresh data: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def update_account_summary(self, margins: Dict[str, Any]):
        """Update account summary display with enhanced metrics"""
        try:
            equity = margins.get('equity', {})
            commodity = margins.get('commodity', {})

            self.equity_label.setText(f"₹{equity.get('net', 0):,.2f}")
            self.commodity_label.setText(f"₹{commodity.get('net', 0):,.2f}")

            total = equity.get('net', 0) + commodity.get('net', 0)
            self.total_label.setText(f"₹{total:,.2f}")

            # Store margins for portfolio calculations
            self.current_margins = margins

        except Exception as e:
            self.logger.error(f"Failed to update account summary: {e}")

    def calculate_portfolio_analytics(self, positions: List[Position], holdings: List[Holding]):
        """Calculate comprehensive portfolio analytics"""
        try:
            # Calculate positions analytics
            total_positions_pnl = sum(pos.pnl for pos in positions)
            total_day_pnl = sum(pos.m2m for pos in positions)

            # Calculate holdings analytics
            total_holdings_value = sum(holding.quantity * holding.last_price for holding in holdings)
            total_holdings_invested = sum(holding.quantity * holding.average_price for holding in holdings)
            total_holdings_pnl = sum(holding.pnl for holding in holdings)

            # Overall portfolio metrics
            total_portfolio_value = total_holdings_value
            total_invested = total_holdings_invested
            total_pnl = total_holdings_pnl + total_positions_pnl
            total_pnl_percentage = (total_pnl / total_invested * 100) if total_invested > 0 else 0

            # Find best and worst performers
            best_performer = "--"
            worst_performer = "--"
            best_pnl_pct = float('-inf')
            worst_pnl_pct = float('inf')

            for holding in holdings:
                if holding.quantity * holding.average_price > 0:
                    pnl_pct = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                    if pnl_pct > best_pnl_pct:
                        best_pnl_pct = pnl_pct
                        best_performer = f"{holding.tradingsymbol} (+{pnl_pct:.1f}%)"
                    if pnl_pct < worst_pnl_pct:
                        worst_pnl_pct = pnl_pct
                        worst_performer = f"{holding.tradingsymbol} ({pnl_pct:.1f}%)"

            # Update portfolio analytics display
            self.total_portfolio_value_label.setText(f"₹{total_portfolio_value:,.2f}")
            self.total_invested_label.setText(f"₹{total_invested:,.2f}")

            # Color code total P&L
            pnl_color = "green" if total_pnl >= 0 else "red"
            self.total_pnl_label.setText(f"₹{total_pnl:,.2f}")
            self.total_pnl_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")

            pnl_pct_color = "green" if total_pnl_percentage >= 0 else "red"
            self.total_pnl_percentage_label.setText(f"{total_pnl_percentage:+.2f}%")
            self.total_pnl_percentage_label.setStyleSheet(f"color: {pnl_pct_color}; font-weight: bold;")

            self.best_performer_label.setText(best_performer)
            self.worst_performer_label.setText(worst_performer)

            # Update main dashboard P&L
            day_pnl_color = "green" if total_day_pnl >= 0 else "red"
            self.pnl_label.setText(f"₹{total_day_pnl:,.2f}")
            self.pnl_label.setStyleSheet(f"color: {day_pnl_color}; font-weight: bold;")

            # Calculate day change percentage
            if total_portfolio_value > 0:
                day_change_pct = (total_day_pnl / (total_portfolio_value - total_day_pnl)) * 100
                day_pct_color = "green" if day_change_pct >= 0 else "red"
                self.day_change_percentage_label.setText(f"{day_change_pct:+.2f}%")
                self.day_change_percentage_label.setStyleSheet(f"color: {day_pct_color}; font-weight: bold;")

            # Update additional metrics
            self.portfolio_value_label.setText(f"₹{total_portfolio_value:,.2f}")
            self.unrealised_pnl_label.setText(f"₹{total_holdings_pnl:,.2f}")
            self.realised_pnl_label.setText(f"₹{total_positions_pnl:,.2f}")

            # Calculate and update enhanced analytics
            self.update_asset_allocation(holdings, positions)
            self.update_sector_allocation(holdings)
            self.update_risk_metrics(holdings, positions)
            self.update_performance_metrics(holdings, positions)
            self.update_concentration_analysis(holdings)
            self.update_gainers_losers(holdings)

            return {
                'total_portfolio_value': total_portfolio_value,
                'total_invested': total_invested,
                'total_pnl': total_pnl,
                'total_pnl_percentage': total_pnl_percentage,
                'positions_pnl': total_positions_pnl,
                'day_pnl': total_day_pnl,
                'holdings_pnl': total_holdings_pnl
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate portfolio analytics: {e}")
            return None

    def update_asset_allocation(self, holdings: List[Holding], positions: List[Position]):
        """Update asset allocation display"""
        try:
            total_value = sum(holding.quantity * holding.last_price for holding in holdings)
            if total_value == 0:
                return

            # Categorize holdings by asset type (simplified categorization)
            equity_value = 0
            debt_value = 0
            commodity_value = 0

            for holding in holdings:
                value = holding.quantity * holding.last_price
                # Simple categorization based on symbol patterns
                symbol = holding.tradingsymbol.upper()
                if any(x in symbol for x in ['GOLD', 'SILVER', 'CRUDE', 'COPPER']):
                    commodity_value += value
                elif any(x in symbol for x in ['BOND', 'GILT', 'LIQUID', 'DEBT']):
                    debt_value += value
                else:
                    equity_value += value

            # Calculate percentages
            equity_pct = (equity_value / total_value) * 100
            debt_pct = (debt_value / total_value) * 100
            commodity_pct = (commodity_value / total_value) * 100
            cash_pct = max(0, 100 - equity_pct - debt_pct - commodity_pct)

            # Update labels
            self.equity_allocation_label.setText(f"Equity: {equity_pct:.1f}%")
            self.debt_allocation_label.setText(f"Debt: {debt_pct:.1f}%")
            self.commodity_allocation_label.setText(f"Commodity: {commodity_pct:.1f}%")
            self.cash_allocation_label.setText(f"Cash: {cash_pct:.1f}%")

        except Exception as e:
            self.logger.error(f"Failed to update asset allocation: {e}")

    def update_sector_allocation(self, holdings: List[Holding]):
        """Update sector allocation table"""
        try:
            # Group holdings by sector (simplified mapping)
            sector_map = {
                'RELIANCE': 'Energy', 'ONGC': 'Energy', 'BPCL': 'Energy', 'IOC': 'Energy',
                'TCS': 'IT', 'INFY': 'IT', 'WIPRO': 'IT', 'HCLTECH': 'IT', 'TECHM': 'IT',
                'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'SBIN': 'Banking', 'AXISBANK': 'Banking',
                'ITC': 'FMCG', 'HINDUNILVR': 'FMCG', 'NESTLEIND': 'FMCG', 'BRITANNIA': 'FMCG',
                'BAJFINANCE': 'Financial Services', 'HDFCLIFE': 'Financial Services',
                'MARUTI': 'Auto', 'TATAMOTORS': 'Auto', 'M&M': 'Auto', 'BAJAJ-AUTO': 'Auto',
                'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma', 'DIVISLAB': 'Pharma'
            }

            sectors = {}
            for holding in holdings:
                symbol = holding.tradingsymbol.upper()
                sector = 'Others'
                for key, val in sector_map.items():
                    if key in symbol:
                        sector = val
                        break

                value = holding.quantity * holding.last_price
                pnl = holding.pnl

                if sector not in sectors:
                    sectors[sector] = {'value': 0, 'pnl': 0}
                sectors[sector]['value'] += value
                sectors[sector]['pnl'] += pnl

            # Update sector table
            total_value = sum(data['value'] for data in sectors.values())
            self.sector_table.setRowCount(len(sectors))

            for row, (sector, data) in enumerate(sorted(sectors.items(), key=lambda x: x[1]['value'], reverse=True)):
                allocation_pct = (data['value'] / total_value * 100) if total_value > 0 else 0

                self.sector_table.setItem(row, 0, QTableWidgetItem(sector))
                self.sector_table.setItem(row, 1, QTableWidgetItem(f"₹{data['value']:,.0f}"))
                self.sector_table.setItem(row, 2, QTableWidgetItem(f"{allocation_pct:.1f}%"))

                pnl_item = QTableWidgetItem(f"₹{data['pnl']:,.0f}")
                pnl_item.setForeground(QColor("green" if data['pnl'] >= 0 else "red"))
                self.sector_table.setItem(row, 3, pnl_item)

        except Exception as e:
            self.logger.error(f"Failed to update sector allocation: {e}")

    def update_risk_metrics(self, holdings: List[Holding], positions: List[Position]):
        """Update risk metrics display"""
        try:
            total_value = sum(holding.quantity * holding.last_price for holding in holdings)
            if total_value == 0:
                return

            # Calculate concentration risk (top 5 holdings percentage)
            holding_values = [(holding.tradingsymbol, holding.quantity * holding.last_price)
                            for holding in holdings]
            holding_values.sort(key=lambda x: x[1], reverse=True)

            top_5_value = sum(value for _, value in holding_values[:5])
            concentration_risk = (top_5_value / total_value * 100) if total_value > 0 else 0

            # Simple risk categorization
            if concentration_risk > 60:
                risk_level = "High"
                risk_color = "red"
            elif concentration_risk > 40:
                risk_level = "Medium"
                risk_color = "orange"
            else:
                risk_level = "Low"
                risk_color = "green"

            self.concentration_risk_label.setText(f"{concentration_risk:.1f}% ({risk_level})")
            self.concentration_risk_label.setStyleSheet(f"color: {risk_color}; font-weight: bold;")

            # Calculate portfolio volatility (simplified)
            pnl_values = [holding.pnl for holding in holdings if holding.pnl != 0]
            if len(pnl_values) > 1:
                import statistics
                volatility = statistics.stdev(pnl_values) / total_value * 100
                self.portfolio_volatility_label.setText(f"{volatility:.2f}%")
            else:
                self.portfolio_volatility_label.setText("--")

            # Placeholder values for other metrics (would need historical data)
            self.portfolio_beta_label.setText("--")
            self.sharpe_ratio_label.setText("--")
            self.max_drawdown_label.setText("--")
            self.var_label.setText("--")

        except Exception as e:
            self.logger.error(f"Failed to update risk metrics: {e}")

    def update_performance_metrics(self, holdings: List[Holding], positions: List[Position]):
        """Update performance metrics display"""
        try:
            total_invested = sum(holding.quantity * holding.average_price for holding in holdings)
            total_current_value = sum(holding.quantity * holding.last_price for holding in holdings)
            total_pnl = sum(holding.pnl for holding in holdings)

            if total_invested > 0:
                total_return_pct = (total_pnl / total_invested) * 100
                self.total_return_label.setText(f"{total_return_pct:+.2f}%")

                # Color code the return
                color = "green" if total_return_pct >= 0 else "red"
                self.total_return_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            else:
                self.total_return_label.setText("--")

            # Calculate day return
            day_pnl = sum(pos.m2m for pos in positions)
            if total_current_value > 0:
                day_return_pct = (day_pnl / (total_current_value - day_pnl)) * 100
                self.daily_return_label.setText(f"{day_return_pct:+.2f}%")

                color = "green" if day_return_pct >= 0 else "red"
                self.daily_return_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            else:
                self.daily_return_label.setText("--")

            # Placeholder values for other time periods (would need historical data)
            self.annualized_return_label.setText("--")
            self.ytd_return_label.setText("--")
            self.monthly_return_label.setText("--")
            self.weekly_return_label.setText("--")

        except Exception as e:
            self.logger.error(f"Failed to update performance metrics: {e}")

    def update_concentration_analysis(self, holdings: List[Holding]):
        """Update concentration analysis table"""
        try:
            # Sort holdings by value
            holding_data = []
            total_value = 0

            for holding in holdings:
                value = holding.quantity * holding.last_price
                holding_data.append((holding.tradingsymbol, value))
                total_value += value

            holding_data.sort(key=lambda x: x[1], reverse=True)

            # Show top 10 holdings
            top_holdings = holding_data[:10]
            self.concentration_table.setRowCount(len(top_holdings))

            for row, (symbol, value) in enumerate(top_holdings):
                percentage = (value / total_value * 100) if total_value > 0 else 0

                self.concentration_table.setItem(row, 0, QTableWidgetItem(symbol))
                self.concentration_table.setItem(row, 1, QTableWidgetItem(f"₹{value:,.0f}"))
                self.concentration_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))

        except Exception as e:
            self.logger.error(f"Failed to update concentration analysis: {e}")

    def update_gainers_losers(self, holdings: List[Holding]):
        """Update top gainers and losers tables"""
        try:
            # Calculate P&L percentage for each holding
            holding_performance = []

            for holding in holdings:
                invested = holding.quantity * holding.average_price
                if invested > 0:
                    pnl_pct = (holding.pnl / invested) * 100
                    holding_performance.append((holding.tradingsymbol, holding.pnl, pnl_pct))

            # Sort by P&L percentage
            holding_performance.sort(key=lambda x: x[2], reverse=True)

            # Top gainers (top 5)
            gainers = holding_performance[:5]
            self.gainers_table.setRowCount(len(gainers))

            for row, (symbol, pnl, pnl_pct) in enumerate(gainers):
                self.gainers_table.setItem(row, 0, QTableWidgetItem(symbol))

                pnl_item = QTableWidgetItem(f"₹{pnl:,.0f}")
                pnl_item.setForeground(QColor("green"))
                self.gainers_table.setItem(row, 1, pnl_item)

                pct_item = QTableWidgetItem(f"{pnl_pct:+.1f}%")
                pct_item.setForeground(QColor("green"))
                self.gainers_table.setItem(row, 2, pct_item)

            # Top losers (bottom 5)
            losers = holding_performance[-5:] if len(holding_performance) >= 5 else []
            losers.reverse()  # Show worst first
            self.losers_table.setRowCount(len(losers))

            for row, (symbol, pnl, pnl_pct) in enumerate(losers):
                self.losers_table.setItem(row, 0, QTableWidgetItem(symbol))

                pnl_item = QTableWidgetItem(f"₹{pnl:,.0f}")
                pnl_item.setForeground(QColor("red"))
                self.losers_table.setItem(row, 1, pnl_item)

                pct_item = QTableWidgetItem(f"{pnl_pct:+.1f}%")
                pct_item.setForeground(QColor("red"))
                self.losers_table.setItem(row, 2, pct_item)

        except Exception as e:
            self.logger.error(f"Failed to update gainers/losers: {e}")

    def update_positions_table(self, positions: List[Position]):
        """Update positions table with enhanced analytics"""
        try:
            self.positions_table.setRowCount(len(positions))

            total_pnl = 0
            total_day_pnl = 0
            open_positions = 0

            for row, position in enumerate(positions):
                # Calculate position value and P&L percentage
                position_value = position.quantity * position.last_price
                pnl_percentage = 0
                if position.average_price > 0 and position.quantity != 0:
                    invested_value = abs(position.quantity) * position.average_price
                    pnl_percentage = (position.pnl / invested_value) * 100 if invested_value > 0 else 0

                # Update table columns with comprehensive position data
                self.positions_table.setItem(row, 0, QTableWidgetItem(position.tradingsymbol))
                self.positions_table.setItem(row, 1, QTableWidgetItem(str(position.quantity)))
                self.positions_table.setItem(row, 2, QTableWidgetItem(str(position.overnight_quantity)))
                self.positions_table.setItem(row, 3, QTableWidgetItem(str(position.multiplier)))
                self.positions_table.setItem(row, 4, QTableWidgetItem(f"₹{position.average_price:.2f}"))
                self.positions_table.setItem(row, 5, QTableWidgetItem(f"₹{position.last_price:.2f}"))
                self.positions_table.setItem(row, 6, QTableWidgetItem(f"₹{position.close_price:.2f}"))
                self.positions_table.setItem(row, 7, QTableWidgetItem(f"₹{position.pnl:.2f}"))
                self.positions_table.setItem(row, 8, QTableWidgetItem(f"{pnl_percentage:+.2f}%"))
                self.positions_table.setItem(row, 9, QTableWidgetItem(f"₹{position.m2m:.2f}"))
                self.positions_table.setItem(row, 10, QTableWidgetItem(str(position.buy_quantity)))
                self.positions_table.setItem(row, 11, QTableWidgetItem(f"₹{position.buy_price:.2f}"))
                self.positions_table.setItem(row, 12, QTableWidgetItem(str(position.sell_quantity)))
                self.positions_table.setItem(row, 13, QTableWidgetItem(f"₹{position.sell_price:.2f}"))
                self.positions_table.setItem(row, 14, QTableWidgetItem(position.product))
                self.positions_table.setItem(row, 15, QTableWidgetItem(position.exchange))

                # Color code P&L columns (updated column indices)
                pnl_item = self.positions_table.item(row, 7)  # P&L column
                pnl_pct_item = self.positions_table.item(row, 8)  # P&L % column
                m2m_item = self.positions_table.item(row, 9)  # M2M column

                if position.pnl > 0:
                    pnl_item.setForeground(QColor("green"))
                    pnl_pct_item.setForeground(QColor("green"))
                elif position.pnl < 0:
                    pnl_item.setForeground(QColor("red"))
                    pnl_pct_item.setForeground(QColor("red"))

                if position.m2m > 0:
                    m2m_item.setForeground(QColor("green"))
                elif position.m2m < 0:
                    m2m_item.setForeground(QColor("red"))

                # Accumulate totals
                total_pnl += position.pnl
                total_day_pnl += position.m2m
                if position.quantity != 0:
                    open_positions += 1

            # Update positions summary
            pnl_color = "green" if total_pnl >= 0 else "red"
            day_pnl_color = "green" if total_day_pnl >= 0 else "red"

            self.positions_total_pnl_label.setText(f"Total P&L: ₹{total_pnl:,.2f}")
            self.positions_total_pnl_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")

            self.positions_day_pnl_label.setText(f"Day P&L: ₹{total_day_pnl:,.2f}")
            self.positions_day_pnl_label.setStyleSheet(f"color: {day_pnl_color}; font-weight: bold;")

            self.positions_count_summary_label.setText(f"Open Positions: {open_positions}")

        except Exception as e:
            self.logger.error(f"Failed to update positions table: {e}")

    def update_holdings_table(self, holdings: List[Holding]):
        """Update holdings table with enhanced analytics"""
        try:
            self.logger.debug(f"🔄 Updating holdings table with {len(holdings)} holdings")
            self.holdings_table.setRowCount(len(holdings))

            total_value = 0
            total_pnl = 0
            holdings_count = len(holdings)

            for row, holding in enumerate(holdings):
                self.logger.debug(f"📊 Processing holding {row+1}: {holding.tradingsymbol}")

                # Calculate metrics
                value = holding.quantity * holding.last_price
                invested_value = holding.quantity * holding.average_price
                pnl_percentage = (holding.pnl / invested_value * 100) if invested_value > 0 else 0
                day_change_percentage = (holding.day_change / (holding.last_price - holding.day_change) * 100) if (holding.last_price - holding.day_change) > 0 else 0

                # Update table columns with comprehensive data
                self.holdings_table.setItem(row, 0, QTableWidgetItem(holding.tradingsymbol))
                self.holdings_table.setItem(row, 1, QTableWidgetItem(holding.isin))
                self.holdings_table.setItem(row, 2, QTableWidgetItem(str(holding.quantity)))
                self.holdings_table.setItem(row, 3, QTableWidgetItem(str(holding.t1_quantity)))
                self.holdings_table.setItem(row, 4, QTableWidgetItem(str(holding.realised_quantity)))
                self.holdings_table.setItem(row, 5, QTableWidgetItem(f"₹{holding.average_price:.2f}"))
                self.holdings_table.setItem(row, 6, QTableWidgetItem(f"₹{holding.last_price:.2f}"))
                self.holdings_table.setItem(row, 7, QTableWidgetItem(f"₹{holding.close_price:.2f}"))
                self.holdings_table.setItem(row, 8, QTableWidgetItem(f"₹{holding.pnl:.2f}"))
                self.holdings_table.setItem(row, 9, QTableWidgetItem(f"{pnl_percentage:+.2f}%"))
                self.holdings_table.setItem(row, 10, QTableWidgetItem(f"₹{holding.day_change:.2f}"))
                self.holdings_table.setItem(row, 11, QTableWidgetItem(f"{day_change_percentage:+.2f}%"))
                self.holdings_table.setItem(row, 12, QTableWidgetItem(f"₹{value:.2f}"))

                # Collateral information
                collateral_info = f"{holding.collateral_quantity} ({holding.collateral_type})" if holding.collateral_quantity > 0 else "--"
                self.holdings_table.setItem(row, 13, QTableWidgetItem(collateral_info))

                # MTF information
                mtf_info = "--"
                if holding.mtf and holding.mtf.get('quantity', 0) > 0:
                    mtf_qty = holding.mtf.get('quantity', 0)
                    mtf_value = holding.mtf.get('value', 0)
                    mtf_info = f"Qty: {mtf_qty}, Value: ₹{mtf_value:,.0f}"
                self.holdings_table.setItem(row, 14, QTableWidgetItem(mtf_info))

                self.logger.debug(f"📊 Added row {row}: {holding.tradingsymbol} - Qty: {holding.quantity}, P&L: ₹{holding.pnl:.2f}")

                # Color code P&L columns (updated column indices)
                pnl_item = self.holdings_table.item(row, 8)  # P&L column
                pnl_pct_item = self.holdings_table.item(row, 9)  # P&L % column
                day_change_item = self.holdings_table.item(row, 10)  # Day Change column
                day_change_pct_item = self.holdings_table.item(row, 11)  # Day Change % column

                if holding.pnl > 0:
                    pnl_item.setForeground(QColor("green"))
                    pnl_pct_item.setForeground(QColor("green"))
                elif holding.pnl < 0:
                    pnl_item.setForeground(QColor("red"))
                    pnl_pct_item.setForeground(QColor("red"))

                if holding.day_change > 0:
                    day_change_item.setForeground(QColor("green"))
                    day_change_pct_item.setForeground(QColor("green"))
                elif holding.day_change < 0:
                    day_change_item.setForeground(QColor("red"))
                    day_change_pct_item.setForeground(QColor("red"))

                # Accumulate totals
                total_value += value
                total_pnl += holding.pnl

            # Update holdings summary
            pnl_color = "green" if total_pnl >= 0 else "red"

            self.holdings_total_value_label.setText(f"Total Value: ₹{total_value:,.2f}")
            self.holdings_total_pnl_label.setText(f"Total P&L: ₹{total_pnl:,.2f}")
            self.holdings_total_pnl_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")
            self.holdings_count_summary_label.setText(f"Holdings: {holdings_count}")

            # Force table refresh
            self.holdings_table.viewport().update()
            self.holdings_table.repaint()

            self.logger.debug(f"✅ Holdings table updated successfully - {holdings_count} holdings, Total P&L: ₹{total_pnl:.2f}")
            self.logger.debug(f"📊 Table row count: {self.holdings_table.rowCount()}, Column count: {self.holdings_table.columnCount()}")

        except Exception as e:
            self.logger.error(f"❌ Failed to update holdings table: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def update_comprehensive_holdings_display(self, all_holdings_data: Dict):
        """Update holdings display with both regular and mutual fund holdings"""
        try:
            regular_holdings = all_holdings_data['regular_holdings']
            mf_holdings = all_holdings_data['mutual_fund_holdings']
            summary = all_holdings_data['summary']

            self.logger.debug(f"🔄 Updating comprehensive holdings display")
            self.logger.debug(f"📊 Regular: {summary['regular_count']}, MF: {summary['mutual_fund_count']}, Total: {summary['total_count']}")

            # Create combined holdings list for the table
            combined_holdings = []

            # Add regular holdings
            for holding in regular_holdings:
                combined_holdings.append({
                    'type': 'Stock/ETF',
                    'symbol': holding.tradingsymbol,
                    'name': holding.tradingsymbol,  # For stocks, symbol is the name
                    'quantity': holding.quantity,
                    'avg_price': holding.average_price,
                    'ltp': holding.last_price,
                    'pnl': holding.pnl,
                    'exchange': holding.exchange,
                    'day_change': holding.day_change,
                    'day_change_pct': holding.day_change_percentage
                })

            # Add mutual fund holdings
            for mf_holding in mf_holdings:
                # Calculate day change (MF data might not have this)
                day_change = 0.0
                day_change_pct = 0.0

                combined_holdings.append({
                    'type': 'Mutual Fund',
                    'symbol': mf_holding.tradingsymbol,
                    'name': mf_holding.fund,
                    'quantity': mf_holding.quantity,
                    'avg_price': mf_holding.average_price,
                    'ltp': mf_holding.last_price,
                    'pnl': mf_holding.pnl,
                    'exchange': 'MF',
                    'day_change': day_change,
                    'day_change_pct': day_change_pct,
                    'folio': mf_holding.folio
                })

            # Update the holdings table with combined data
            self.update_combined_holdings_table(combined_holdings, summary)

        except Exception as e:
            self.logger.error(f"❌ Failed to update comprehensive holdings display: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def update_combined_holdings_table(self, combined_holdings: List[Dict], summary: Dict):
        """Update holdings table with combined regular and mutual fund holdings"""
        try:
            self.logger.debug(f"🔄 Updating combined holdings table with {len(combined_holdings)} total holdings")

            # Update table structure to accommodate more columns
            self.holdings_table.setRowCount(len(combined_holdings))
            self.holdings_table.setColumnCount(10)  # Added Type and Name columns
            self.holdings_table.setHorizontalHeaderLabels([
                "Type", "Symbol", "Name", "Quantity", "Avg Price", "LTP", "P&L", "P&L %", "Day Change", "Value"
            ])

            total_value = 0
            total_pnl = summary['total_pnl']

            for row, holding in enumerate(combined_holdings):
                # Calculate metrics
                value = holding['quantity'] * holding['ltp']
                invested_value = holding['quantity'] * holding['avg_price']
                pnl_percentage = (holding['pnl'] / invested_value * 100) if invested_value > 0 else 0

                # Update table columns
                self.holdings_table.setItem(row, 0, QTableWidgetItem(holding['type']))  # Type
                self.holdings_table.setItem(row, 1, QTableWidgetItem(holding['symbol']))  # Symbol

                # Name column - truncate long mutual fund names
                name = holding['name']
                if len(name) > 40:
                    name = name[:37] + "..."
                self.holdings_table.setItem(row, 2, QTableWidgetItem(name))  # Name

                self.holdings_table.setItem(row, 3, QTableWidgetItem(f"{holding['quantity']:.3f}"))  # Quantity
                self.holdings_table.setItem(row, 4, QTableWidgetItem(f"₹{holding['avg_price']:.2f}"))  # Avg Price
                self.holdings_table.setItem(row, 5, QTableWidgetItem(f"₹{holding['ltp']:.2f}"))  # LTP
                self.holdings_table.setItem(row, 6, QTableWidgetItem(f"₹{holding['pnl']:.2f}"))  # P&L
                self.holdings_table.setItem(row, 7, QTableWidgetItem(f"{pnl_percentage:+.2f}%"))  # P&L %
                self.holdings_table.setItem(row, 8, QTableWidgetItem(f"₹{holding['day_change']:.2f}"))  # Day Change
                self.holdings_table.setItem(row, 9, QTableWidgetItem(f"₹{value:.2f}"))  # Value

                # Color coding for P&L
                pnl_item = self.holdings_table.item(row, 6)
                pnl_pct_item = self.holdings_table.item(row, 7)

                if holding['pnl'] > 0:
                    pnl_item.setForeground(QColor("green"))
                    pnl_pct_item.setForeground(QColor("green"))
                elif holding['pnl'] < 0:
                    pnl_item.setForeground(QColor("red"))
                    pnl_pct_item.setForeground(QColor("red"))

                # Color coding for type
                type_item = self.holdings_table.item(row, 0)
                if holding['type'] == 'Mutual Fund':
                    type_item.setForeground(QColor("blue"))
                else:
                    type_item.setForeground(QColor("darkgreen"))

                total_value += value

                self.logger.debug(f"📊 Added row {row}: {holding['type']} - {holding['symbol']} - P&L: ₹{holding['pnl']:.2f}")

            # Update summary labels
            pnl_color = "green" if total_pnl >= 0 else "red"
            self.holdings_total_pnl_label.setText(f"Total P&L: ₹{total_pnl:,.2f}")
            self.holdings_total_pnl_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")
            self.holdings_count_summary_label.setText(f"Holdings: {summary['total_count']} (Stocks: {summary['regular_count']}, MF: {summary['mutual_fund_count']})")

            # Force table refresh
            self.holdings_table.viewport().update()
            self.holdings_table.repaint()

            self.logger.debug(f"✅ Combined holdings table updated successfully")
            self.logger.debug(f"📊 Total: {summary['total_count']} holdings, Regular P&L: ₹{summary['regular_pnl']:.2f}, MF P&L: ₹{summary['mutual_fund_pnl']:.2f}")

        except Exception as e:
            self.logger.error(f"❌ Failed to update combined holdings table: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def update_orders_table(self, orders: List[Order]):
        """Update comprehensive orders tables"""
        try:
            # Update active orders (pending orders)
            active_orders = [o for o in orders if o.status in ["OPEN", "TRIGGER PENDING"]]
            self.update_active_orders_table(active_orders)

            # Update order history (all orders)
            self.update_order_history_table(orders)

            # Update order analytics
            self.update_order_analytics(orders)

        except Exception as e:
            self.logger.error(f"Failed to update orders table: {e}")

    def update_active_orders_table(self, orders: List[Order]):
        """Update active orders table"""
        try:
            self.active_orders_table.setRowCount(len(orders))

            for row, order in enumerate(orders):
                self.active_orders_table.setItem(row, 0, QTableWidgetItem(order.order_id))
                self.active_orders_table.setItem(row, 1, QTableWidgetItem(order.tradingsymbol))
                self.active_orders_table.setItem(row, 2, QTableWidgetItem(order.order_type))
                self.active_orders_table.setItem(row, 3, QTableWidgetItem(order.transaction_type))
                self.active_orders_table.setItem(row, 4, QTableWidgetItem(str(order.quantity)))
                self.active_orders_table.setItem(row, 5, QTableWidgetItem(f"₹{order.price:.2f}"))

                trigger_price = getattr(order, 'trigger_price', 0) or 0
                self.active_orders_table.setItem(row, 6, QTableWidgetItem(f"₹{trigger_price:.2f}" if trigger_price > 0 else "--"))

                # Color code status
                status_item = QTableWidgetItem(order.status)
                if order.status == "OPEN":
                    status_item.setForeground(QColor("blue"))
                elif order.status == "TRIGGER PENDING":
                    status_item.setForeground(QColor("orange"))
                self.active_orders_table.setItem(row, 7, status_item)

                self.active_orders_table.setItem(row, 8, QTableWidgetItem(order.product))
                self.active_orders_table.setItem(row, 9, QTableWidgetItem(order.order_timestamp.strftime("%H:%M:%S")))

                # Add action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(2, 2, 2, 2)

                # Modify button
                modify_btn = QPushButton("Modify")
                modify_btn.setMaximumWidth(60)
                modify_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
                modify_btn.clicked.connect(lambda _, order_obj=order: self.modify_order(order_obj))
                action_layout.addWidget(modify_btn)

                # Cancel button
                cancel_btn = QPushButton("Cancel")
                cancel_btn.setMaximumWidth(60)
                cancel_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
                cancel_btn.clicked.connect(lambda _, oid=order.order_id: self.cancel_order(oid))
                action_layout.addWidget(cancel_btn)

                self.active_orders_table.setCellWidget(row, 10, action_widget)

        except Exception as e:
            self.logger.error(f"Failed to update active orders table: {e}")

    def update_order_history_table(self, orders: List[Order]):
        """Update order history table"""
        try:
            # Apply current filters
            filtered_orders = self.apply_order_filters(orders)

            self.order_history_table.setRowCount(len(filtered_orders))

            for row, order in enumerate(filtered_orders):
                # Comprehensive order data display
                self.order_history_table.setItem(row, 0, QTableWidgetItem(order.order_id))
                self.order_history_table.setItem(row, 1, QTableWidgetItem(order.parent_order_id or "--"))
                self.order_history_table.setItem(row, 2, QTableWidgetItem(order.exchange_order_id or "--"))
                self.order_history_table.setItem(row, 3, QTableWidgetItem(order.tradingsymbol))
                self.order_history_table.setItem(row, 4, QTableWidgetItem(order.order_type))
                self.order_history_table.setItem(row, 5, QTableWidgetItem(order.transaction_type))
                self.order_history_table.setItem(row, 6, QTableWidgetItem(str(order.quantity)))

                filled_qty = getattr(order, 'filled_quantity', 0) or 0
                self.order_history_table.setItem(row, 7, QTableWidgetItem(str(filled_qty)))

                pending_qty = getattr(order, 'pending_quantity', 0) or 0
                self.order_history_table.setItem(row, 8, QTableWidgetItem(str(pending_qty)))

                cancelled_qty = getattr(order, 'cancelled_quantity', 0) or 0
                self.order_history_table.setItem(row, 9, QTableWidgetItem(str(cancelled_qty)))

                self.order_history_table.setItem(row, 10, QTableWidgetItem(f"₹{order.price:.2f}"))

                trigger_price = getattr(order, 'trigger_price', 0) or 0
                self.order_history_table.setItem(row, 11, QTableWidgetItem(f"₹{trigger_price:.2f}" if trigger_price > 0 else "--"))

                avg_price = getattr(order, 'average_price', 0) or 0
                self.order_history_table.setItem(row, 12, QTableWidgetItem(f"₹{avg_price:.2f}" if avg_price > 0 else "--"))

                # Color code status
                status_item = QTableWidgetItem(order.status)
                if order.status == "COMPLETE":
                    status_item.setForeground(QColor("green"))
                elif order.status == "CANCELLED":
                    status_item.setForeground(QColor("orange"))
                elif order.status == "REJECTED":
                    status_item.setForeground(QColor("red"))
                self.order_history_table.setItem(row, 13, status_item)

                # Status message
                status_message = getattr(order, 'status_message', '') or ''
                self.order_history_table.setItem(row, 14, QTableWidgetItem(status_message[:50] + "..." if len(status_message) > 50 else status_message))

                self.order_history_table.setItem(row, 15, QTableWidgetItem(order.product))
                self.order_history_table.setItem(row, 16, QTableWidgetItem(order.variety))
                self.order_history_table.setItem(row, 17, QTableWidgetItem(order.order_timestamp.strftime("%d-%m-%Y %H:%M:%S")))

        except Exception as e:
            self.logger.error(f"Failed to update order history table: {e}")

    def apply_order_filters(self, orders: List[Order]) -> List[Order]:
        """Apply filters to order list"""
        try:
            filtered_orders = orders.copy()

            # Filter by status
            status_filter = self.history_status_combo.currentText()
            if status_filter != "All":
                filtered_orders = [o for o in filtered_orders if o.status == status_filter]

            # Filter by symbol
            symbol_filter = self.history_symbol_input.text().strip().upper()
            if symbol_filter:
                filtered_orders = [o for o in filtered_orders if symbol_filter in o.tradingsymbol.upper()]

            # Filter by date (last N days)
            days_filter = self.history_days_spinbox.value()
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days_filter)
            filtered_orders = [o for o in filtered_orders if o.order_timestamp >= cutoff_date]

            return filtered_orders

        except Exception as e:
            self.logger.error(f"Failed to apply order filters: {e}")
            return orders

    def update_order_analytics(self, orders: List[Order]):
        """Update order analytics display"""
        try:
            total_orders = len(orders)
            completed_orders = len([o for o in orders if o.status == "COMPLETE"])
            cancelled_orders = len([o for o in orders if o.status == "CANCELLED"])
            rejected_orders = len([o for o in orders if o.status == "REJECTED"])
            pending_orders = len([o for o in orders if o.status in ["OPEN", "TRIGGER PENDING"]])

            success_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

            # Update statistics labels
            self.total_orders_label.setText(str(total_orders))
            self.completed_orders_label.setText(str(completed_orders))
            self.cancelled_orders_label.setText(str(cancelled_orders))
            self.rejected_orders_label.setText(str(rejected_orders))
            self.pending_orders_label.setText(str(pending_orders))
            self.success_rate_label.setText(f"{success_rate:.1f}%")

            # Color code success rate
            if success_rate >= 80:
                self.success_rate_label.setStyleSheet("color: green; font-weight: bold;")
            elif success_rate >= 60:
                self.success_rate_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.success_rate_label.setStyleSheet("color: red; font-weight: bold;")

            # Update order breakdown by type
            order_types = {}
            for order in orders:
                order_type = order.order_type
                if order_type not in order_types:
                    order_types[order_type] = {'total': 0, 'completed': 0}
                order_types[order_type]['total'] += 1
                if order.status == "COMPLETE":
                    order_types[order_type]['completed'] += 1

            self.order_breakdown_table.setRowCount(len(order_types))
            for row, (order_type, data) in enumerate(order_types.items()):
                success_rate_type = (data['completed'] / data['total'] * 100) if data['total'] > 0 else 0

                self.order_breakdown_table.setItem(row, 0, QTableWidgetItem(order_type))
                self.order_breakdown_table.setItem(row, 1, QTableWidgetItem(str(data['total'])))
                self.order_breakdown_table.setItem(row, 2, QTableWidgetItem(f"{success_rate_type:.1f}%"))
                self.order_breakdown_table.setItem(row, 3, QTableWidgetItem("--"))  # Avg fill time would need more data

            # Update recent orders (last 10)
            recent_orders = sorted(orders, key=lambda x: x.order_timestamp, reverse=True)[:10]
            self.recent_orders_table.setRowCount(len(recent_orders))

            for row, order in enumerate(recent_orders):
                self.recent_orders_table.setItem(row, 0, QTableWidgetItem(order.order_timestamp.strftime("%H:%M:%S")))
                self.recent_orders_table.setItem(row, 1, QTableWidgetItem(order.tradingsymbol))
                self.recent_orders_table.setItem(row, 2, QTableWidgetItem(order.transaction_type))
                self.recent_orders_table.setItem(row, 3, QTableWidgetItem(str(order.quantity)))
                self.recent_orders_table.setItem(row, 4, QTableWidgetItem(f"₹{order.price:.2f}"))

                status_item = QTableWidgetItem(order.status)
                if order.status == "COMPLETE":
                    status_item.setForeground(QColor("green"))
                elif order.status == "CANCELLED":
                    status_item.setForeground(QColor("orange"))
                elif order.status == "REJECTED":
                    status_item.setForeground(QColor("red"))
                self.recent_orders_table.setItem(row, 5, status_item)

        except Exception as e:
            self.logger.error(f"Failed to update order analytics: {e}")

    def refresh_orders_data(self):
        """Refresh orders data"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            orders = self.api_client.get_orders()
            self.update_orders_table(orders)
            QMessageBox.information(self, "Success", "Orders data refreshed successfully.")

        except Exception as e:
            self.logger.error(f"Failed to refresh orders data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to refresh orders data: {e}")

    def cancel_all_pending_orders(self):
        """Cancel all pending orders"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            reply = QMessageBox.question(self, "Confirm Cancellation",
                                       "Are you sure you want to cancel ALL pending orders?",
                                       QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                orders = self.api_client.get_orders()
                pending_orders = [o for o in orders if o.status in ["OPEN", "TRIGGER PENDING"]]

                if not pending_orders:
                    QMessageBox.information(self, "No Pending Orders", "No pending orders to cancel.")
                    return

                cancelled_count = 0
                failed_count = 0

                for order in pending_orders:
                    try:
                        self.api_client.cancel_order(order.order_id)
                        cancelled_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to cancel order {order.order_id}: {e}")
                        failed_count += 1

                message = f"Cancelled {cancelled_count} orders."
                if failed_count > 0:
                    message += f" Failed to cancel {failed_count} orders."

                QMessageBox.information(self, "Cancellation Complete", message)

                # Refresh orders data
                self.refresh_orders_data()

        except Exception as e:
            self.logger.error(f"Failed to cancel all pending orders: {e}")
            QMessageBox.critical(self, "Error", f"Failed to cancel all pending orders: {e}")

    def export_order_history(self):
        """Export order history to CSV"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            from PySide6.QtWidgets import QFileDialog
            import csv

            # Get file path
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Order History", "order_history.csv", "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # Get orders and apply filters
            orders = self.api_client.get_orders()
            filtered_orders = self.apply_order_filters(orders)

            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow([
                    "Order ID", "Symbol", "Type", "Transaction", "Quantity", "Filled Qty",
                    "Price", "Average Price", "Status", "Product", "Order Time", "Update Time"
                ])

                # Write data
                for order in filtered_orders:
                    filled_qty = getattr(order, 'filled_quantity', 0) or 0
                    avg_price = getattr(order, 'average_price', 0) or 0
                    update_time = getattr(order, 'exchange_update_timestamp', order.order_timestamp)

                    writer.writerow([
                        order.order_id, order.tradingsymbol, order.order_type, order.transaction_type,
                        order.quantity, filled_qty, order.price, avg_price, order.status, order.product,
                        order.order_timestamp.strftime("%d-%m-%Y %H:%M:%S"),
                        update_time.strftime("%d-%m-%Y %H:%M:%S")
                    ])

            QMessageBox.information(self, "Export Complete", f"Order history exported to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to export order history: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export order history: {e}")

    def on_order_type_changed(self, order_type: str):
        """Handle order type change"""
        # Enable/disable price and trigger price inputs based on order type
        if order_type == "MARKET":
            self.price_input.setEnabled(False)
            self.trigger_price_input.setEnabled(False)
        elif order_type == "LIMIT":
            self.price_input.setEnabled(True)
            self.trigger_price_input.setEnabled(False)
        elif order_type in ["SL", "SL-M"]:
            self.price_input.setEnabled(order_type == "SL")
            self.trigger_price_input.setEnabled(True)

        self.update_order_preview()

    def on_validity_changed(self, validity: str):
        """Handle validity type change"""
        if validity == "TTL":
            self.validity_ttl_input.setVisible(True)
        else:
            self.validity_ttl_input.setVisible(False)

        self.update_order_preview()

    def get_symbol_quote(self):
        """Get current quote for the symbol"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            symbol = self.symbol_input.text().strip().upper()
            exchange = self.exchange_combo.currentText()

            if not symbol:
                QMessageBox.warning(self, "Invalid Input", "Please enter a symbol.")
                return

            # Format instrument for quote
            instrument = f"{exchange}:{symbol}"
            quote_data = self.api_client.get_quote([instrument])

            if quote_data and instrument in quote_data:
                quote = quote_data[instrument]
                last_price = quote.get('last_price', 0)
                self.current_price_label.setText(f"Current Price: ₹{last_price:.2f}")

                # Auto-fill price for limit orders
                if self.order_type_combo.currentText() == "LIMIT":
                    self.price_input.setValue(last_price)

            else:
                self.current_price_label.setText("Current Price: Not Available")
                QMessageBox.warning(self, "Quote Error", f"Could not get quote for {symbol}")

        except Exception as e:
            self.logger.error(f"Failed to get quote: {e}")
            QMessageBox.critical(self, "Error", f"Failed to get quote: {e}")

    def validate_order_inputs(self) -> tuple[bool, str]:
        """Validate order inputs and return (is_valid, error_message)"""
        symbol = self.symbol_input.text().strip().upper()
        quantity = self.quantity_input.value()
        order_type = self.order_type_combo.currentText()
        price = self.price_input.value()
        trigger_price = self.trigger_price_input.value()

        if not symbol:
            return False, "Please enter a symbol."

        if len(symbol) < 2:
            return False, "Symbol must be at least 2 characters long."

        if quantity <= 0:
            return False, "Quantity must be greater than 0."

        if order_type == "LIMIT" and price <= 0:
            return False, "Price must be greater than 0 for LIMIT orders."

        if order_type in ["SL", "SL-M"] and trigger_price <= 0:
            return False, "Trigger price must be greater than 0 for Stop Loss orders."

        if order_type == "SL" and price <= 0:
            return False, "Price must be greater than 0 for SL orders."

        return True, ""

    def place_order(self):
        """Place a new order with enhanced validation"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            # Validate inputs
            is_valid, error_message = self.validate_order_inputs()
            if not is_valid:
                QMessageBox.warning(self, "Invalid Input", error_message)
                return

            # Get order parameters
            symbol = self.symbol_input.text().strip().upper()
            exchange = self.exchange_combo.currentText()
            transaction_type = self.transaction_combo.currentText()
            quantity = self.quantity_input.value()
            order_type = self.order_type_combo.currentText()
            price = self.price_input.value() if order_type in ["LIMIT", "SL"] else None
            trigger_price = self.trigger_price_input.value() if order_type in ["SL", "SL-M"] else None
            product = self.product_combo.currentText()
            validity = self.validity_combo.currentText()

            # Calculate estimated order value
            estimated_value = 0
            if order_type == "MARKET":
                # Try to get current price for estimation
                try:
                    instrument = f"{exchange}:{symbol}"
                    quote_data = self.api_client.get_quote([instrument])
                    if quote_data and instrument in quote_data:
                        current_price = quote_data[instrument].get('last_price', 0)
                        estimated_value = current_price * quantity
                except:
                    estimated_value = 0
            else:
                estimated_value = (price or trigger_price or 0) * quantity

            # Enhanced order confirmation dialog
            order_details = f"""
Symbol: {symbol}
Exchange: {exchange}
Transaction: {transaction_type}
Quantity: {quantity:,}
Order Type: {order_type}
Price: {f'₹{price:.2f}' if price else 'Market'}
{f'Trigger Price: ₹{trigger_price:.2f}' if trigger_price else ''}
Product: {product}
Validity: {validity}
{f'Estimated Value: ₹{estimated_value:,.2f}' if estimated_value > 0 else ''}
"""

            reply = QMessageBox.question(self, "Confirm Order",
                                       f"Are you sure you want to place this order?\n{order_details.strip()}",
                                       QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                # Prepare order parameters
                order_params = {
                    "variety": "regular",
                    "exchange": exchange,
                    "tradingsymbol": symbol,
                    "transaction_type": transaction_type,
                    "quantity": quantity,
                    "product": product,
                    "order_type": order_type,
                    "validity": validity
                }

                if price is not None:
                    order_params["price"] = price
                if trigger_price is not None:
                    order_params["trigger_price"] = trigger_price

                order_id = self.api_client.place_order(**order_params)

                if order_id:
                    QMessageBox.information(self, "Success",
                                          f"Order placed successfully!\n\nOrder ID: {order_id}\nSymbol: {symbol}\nQuantity: {quantity}")
                    self.refresh_data()
                    self.clear_order_form()
                else:
                    QMessageBox.critical(self, "Error", "Failed to place order. Please check your inputs and try again.")

        except Exception as e:
            self.logger.error(f"Failed to place order: {e}")
            QMessageBox.critical(self, "Error", f"Failed to place order:\n{str(e)}")

    def clear_order_form(self):
        """Clear the order form"""
        self.symbol_input.clear()
        self.quantity_input.setValue(1)
        self.price_input.setValue(0.0)
        self.trigger_price_input.setValue(0.0)
        self.current_price_label.setText("Current Price: --")
        self.order_type_combo.setCurrentText("MARKET")
        self.transaction_combo.setCurrentText("BUY")
        self.product_combo.setCurrentText("CNC")

    def cancel_order(self, order_id: str):
        """Cancel an order"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                return

            reply = QMessageBox.question(self, "Confirm Cancellation",
                                       f"Are you sure you want to cancel order {order_id}?",
                                       QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                if self.api_client.cancel_order("regular", order_id):
                    QMessageBox.information(self, "Success", "Order cancelled successfully!")
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, "Error", "Failed to cancel order.")

        except Exception as e:
            self.logger.error(f"Failed to cancel order: {e}")
            QMessageBox.critical(self, "Error", f"Failed to cancel order: {e}")

    def modify_order(self, order):
        """Modify an existing order"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                return

            # Create modify order dialog
            dialog = ModifyOrderDialog(order, self)
            if dialog.exec() == QDialog.Accepted:
                modifications = dialog.get_modifications()

                if modifications:
                    success = self.api_client.modify_order("regular", order.order_id, **modifications)
                    if success:
                        QMessageBox.information(self, "Success", f"Order {order.order_id} modified successfully!")
                        self.refresh_data()
                    else:
                        QMessageBox.critical(self, "Error", "Failed to modify order.")

        except Exception as e:
            self.logger.error(f"Failed to modify order: {e}")
            QMessageBox.critical(self, "Error", f"Failed to modify order: {e}")

    def get_market_quote(self):
        """Get market quote for the selected symbol"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            symbol = self.market_symbol_input.text().strip().upper()
            exchange = self.market_exchange_combo.currentText()

            if not symbol:
                QMessageBox.warning(self, "Invalid Input", "Please enter a symbol.")
                return

            # Format instrument for quote
            instrument = f"{exchange}:{symbol}"
            quote_data = self.api_client.get_quote([instrument])

            if quote_data and instrument in quote_data:
                quote = quote_data[instrument]
                self.update_quote_display(quote, symbol)
                self.update_market_depth(quote.get('depth', {}))
            else:
                QMessageBox.warning(self, "Quote Error", f"Could not get quote for {symbol}")
                self.clear_quote_display()

        except Exception as e:
            self.logger.error(f"Failed to get market quote: {e}")
            QMessageBox.critical(self, "Error", f"Failed to get market quote: {e}")

    def update_quote_display(self, quote: Dict[str, Any], symbol: str):
        """Update the quote display with comprehensive market data"""
        try:
            # Basic quote info
            self.quote_symbol_label.setText(symbol)

            last_price = quote.get('last_price', 0)
            self.quote_ltp_label.setText(f"₹{last_price:.2f}")

            # OHLC data
            ohlc = quote.get('ohlc', {})
            self.quote_open_label.setText(f"₹{ohlc.get('open', 0):.2f}")
            self.quote_high_label.setText(f"₹{ohlc.get('high', 0):.2f}")
            self.quote_low_label.setText(f"₹{ohlc.get('low', 0):.2f}")
            self.quote_close_label.setText(f"₹{ohlc.get('close', 0):.2f}")

            # Volume and additional data
            volume = quote.get('volume', 0)
            self.quote_volume_label.setText(f"{volume:,}")

            # Average price
            avg_price = quote.get('average_price', 0)
            self.quote_avg_price_label.setText(f"₹{avg_price:.2f}")

            # Buy/Sell quantities
            buy_qty = quote.get('buy_quantity', 0)
            sell_qty = quote.get('sell_quantity', 0)
            self.quote_buy_qty_label.setText(f"{buy_qty:,}")
            self.quote_sell_qty_label.setText(f"{sell_qty:,}")

            # Open Interest data
            oi = quote.get('oi', 0)
            oi_high = quote.get('oi_day_high', 0)
            oi_low = quote.get('oi_day_low', 0)
            self.quote_oi_label.setText(f"{oi:,}")
            self.quote_oi_high_label.setText(f"{oi_high:,}")
            self.quote_oi_low_label.setText(f"{oi_low:,}")

            # Circuit limits
            upper_circuit = quote.get('upper_circuit_limit', 0)
            lower_circuit = quote.get('lower_circuit_limit', 0)
            self.quote_upper_circuit_label.setText(f"₹{upper_circuit:.2f}")
            self.quote_lower_circuit_label.setText(f"₹{lower_circuit:.2f}")

            # Last trade time
            last_trade_time = quote.get('last_trade_time', '')
            self.quote_last_trade_time_label.setText(last_trade_time or '--')

            # Calculate change
            net_change = quote.get('net_change', 0)
            if ohlc.get('close', 0) > 0:
                change_percentage = (net_change / ohlc.get('close', 1)) * 100
            else:
                change_percentage = 0

            # Color code the change
            change_color = "green" if net_change >= 0 else "red"
            change_sign = "+" if net_change >= 0 else ""

            self.quote_change_label.setText(f"{change_sign}₹{net_change:.2f} ({change_sign}{change_percentage:.2f}%)")
            self.quote_change_label.setStyleSheet(f"color: {change_color}; font-weight: bold;")

        except Exception as e:
            self.logger.error(f"Failed to update quote display: {e}")

    def update_market_depth(self, depth: Dict[str, Any]):
        """Update market depth tables"""
        try:
            # Update buy depth
            buy_depth = depth.get('buy', [])
            self.buy_depth_table.setRowCount(len(buy_depth))

            for row, level in enumerate(buy_depth):
                self.buy_depth_table.setItem(row, 0, QTableWidgetItem(f"₹{level.get('price', 0):.2f}"))
                self.buy_depth_table.setItem(row, 1, QTableWidgetItem(str(level.get('quantity', 0))))
                self.buy_depth_table.setItem(row, 2, QTableWidgetItem(str(level.get('orders', 0))))

            # Update sell depth
            sell_depth = depth.get('sell', [])
            self.sell_depth_table.setRowCount(len(sell_depth))

            for row, level in enumerate(sell_depth):
                self.sell_depth_table.setItem(row, 0, QTableWidgetItem(f"₹{level.get('price', 0):.2f}"))
                self.sell_depth_table.setItem(row, 1, QTableWidgetItem(str(level.get('quantity', 0))))
                self.sell_depth_table.setItem(row, 2, QTableWidgetItem(str(level.get('orders', 0))))

        except Exception as e:
            self.logger.error(f"Failed to update market depth: {e}")

    def clear_quote_display(self):
        """Clear the quote display"""
        self.quote_symbol_label.setText("--")
        self.quote_ltp_label.setText("₹0.00")
        self.quote_change_label.setText("₹0.00 (0.00%)")
        self.quote_volume_label.setText("0")
        self.quote_high_label.setText("₹0.00")
        self.quote_low_label.setText("₹0.00")
        self.quote_open_label.setText("₹0.00")
        self.quote_close_label.setText("₹0.00")
        self.buy_depth_table.setRowCount(0)
        self.sell_depth_table.setRowCount(0)

    def get_historical_data(self):
        """Get historical data for the selected symbol"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            symbol = self.market_symbol_input.text().strip().upper()
            exchange = self.market_exchange_combo.currentText()

            if not symbol:
                QMessageBox.warning(self, "Invalid Input", "Please enter a symbol.")
                return

            # Get instrument token (simplified - in real implementation, you'd need to search instruments)
            # For now, we'll show a message that this requires instrument token
            QMessageBox.information(self, "Historical Data",
                                  "Historical data requires instrument token lookup. "
                                  "This feature will be enhanced in the next update.")

            # TODO: Implement instrument search and historical data display
            # This would involve:
            # 1. Search instruments to get instrument_token
            # 2. Call get_historical_data with proper parameters
            # 3. Display data in the historical_table

        except Exception as e:
            self.logger.error(f"Failed to get historical data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to get historical data: {e}")

    def apply_history_filters(self):
        """Apply filters to trade history"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            # Get filtered orders
            orders = self.api_client.get_orders()

            # Apply filters
            status_filter = self.history_status_combo.currentText()
            symbol_filter = self.history_symbol_input.text().strip().upper()
            days_filter = self.history_days_spinbox.value()

            # Filter by status
            if status_filter != "All":
                orders = [order for order in orders if order.status == status_filter]

            # Filter by symbol
            if symbol_filter:
                orders = [order for order in orders if symbol_filter in order.tradingsymbol.upper()]

            # Filter by date (last N days)
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days_filter)
            orders = [order for order in orders if order.order_timestamp >= cutoff_date]

            # Update trade history table
            self.update_trade_history_table(orders)

            # Update analytics
            self.update_trading_analytics(orders)

        except Exception as e:
            self.logger.error(f"Failed to apply history filters: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply history filters: {e}")

    def update_trade_history_table(self, orders: List):
        """Update the trade history table"""
        try:
            self.trade_history_table.setRowCount(len(orders))

            for row, order in enumerate(orders):
                # Date and time
                order_date = order.order_timestamp.strftime("%Y-%m-%d") if order.order_timestamp else ""
                order_time = order.order_timestamp.strftime("%H:%M:%S") if order.order_timestamp else ""

                self.trade_history_table.setItem(row, 0, QTableWidgetItem(order_date))
                self.trade_history_table.setItem(row, 1, QTableWidgetItem(order_time))
                self.trade_history_table.setItem(row, 2, QTableWidgetItem(order.tradingsymbol))
                self.trade_history_table.setItem(row, 3, QTableWidgetItem(order.order_type))
                self.trade_history_table.setItem(row, 4, QTableWidgetItem(order.transaction_type))
                self.trade_history_table.setItem(row, 5, QTableWidgetItem(str(order.quantity)))
                self.trade_history_table.setItem(row, 6, QTableWidgetItem(f"₹{order.price:.2f}"))

                # Calculate amount
                amount = order.quantity * order.price
                self.trade_history_table.setItem(row, 7, QTableWidgetItem(f"₹{amount:.2f}"))

                # Status with color coding
                status_item = QTableWidgetItem(order.status)
                if order.status == "COMPLETE":
                    status_item.setBackground(QColor(200, 255, 200))  # Light green
                elif order.status == "CANCELLED":
                    status_item.setBackground(QColor(255, 200, 200))  # Light red
                elif order.status == "REJECTED":
                    status_item.setBackground(QColor(255, 220, 200))  # Light orange
                self.trade_history_table.setItem(row, 8, status_item)

                # P&L calculation (simplified)
                if order.status == "COMPLETE" and order.filled_quantity > 0:
                    pnl = (order.average_price - order.price) * order.filled_quantity
                    if order.transaction_type == "SELL":
                        pnl = -pnl
                else:
                    pnl = 0

                pnl_item = QTableWidgetItem(f"₹{pnl:.2f}")
                if pnl > 0:
                    pnl_item.setForeground(QColor(0, 128, 0))  # Green
                elif pnl < 0:
                    pnl_item.setForeground(QColor(255, 0, 0))  # Red
                self.trade_history_table.setItem(row, 9, pnl_item)

                # Charges (estimated)
                charges = amount * 0.001  # Simplified calculation
                self.trade_history_table.setItem(row, 10, QTableWidgetItem(f"₹{charges:.2f}"))

                # Net P&L
                net_pnl = pnl - charges
                net_pnl_item = QTableWidgetItem(f"₹{net_pnl:.2f}")
                if net_pnl > 0:
                    net_pnl_item.setForeground(QColor(0, 128, 0))  # Green
                elif net_pnl < 0:
                    net_pnl_item.setForeground(QColor(255, 0, 0))  # Red
                self.trade_history_table.setItem(row, 11, net_pnl_item)

        except Exception as e:
            self.logger.error(f"Failed to update trade history table: {e}")

    def update_trading_analytics(self, orders: List):
        """Update trading analytics summary"""
        try:
            # Filter completed orders only
            completed_orders = [order for order in orders if order.status == "COMPLETE" and order.filled_quantity > 0]

            if not completed_orders:
                # Reset analytics if no completed orders
                self.total_trades_label.setText("0")
                self.winning_trades_label.setText("0")
                self.losing_trades_label.setText("0")
                self.win_rate_label.setText("0.00%")
                self.total_pnl_analytics_label.setText("₹0.00")
                self.avg_profit_label.setText("₹0.00")
                self.avg_loss_label.setText("₹0.00")
                self.largest_win_label.setText("₹0.00")
                self.largest_loss_label.setText("₹0.00")
                self.profit_factor_label.setText("0.00")
                return

            # Calculate P&L for each trade
            trade_pnls = []
            for order in completed_orders:
                pnl = (order.average_price - order.price) * order.filled_quantity
                if order.transaction_type == "SELL":
                    pnl = -pnl
                # Subtract estimated charges
                charges = (order.quantity * order.price) * 0.001
                net_pnl = pnl - charges
                trade_pnls.append(net_pnl)

            # Calculate metrics
            total_trades = len(trade_pnls)
            winning_trades = len([pnl for pnl in trade_pnls if pnl > 0])
            losing_trades = len([pnl for pnl in trade_pnls if pnl < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            total_pnl = sum(trade_pnls)
            profits = [pnl for pnl in trade_pnls if pnl > 0]
            losses = [pnl for pnl in trade_pnls if pnl < 0]

            avg_profit = sum(profits) / len(profits) if profits else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            largest_win = max(trade_pnls) if trade_pnls else 0
            largest_loss = min(trade_pnls) if trade_pnls else 0

            # Profit factor
            total_profits = sum(profits) if profits else 0
            total_losses = abs(sum(losses)) if losses else 0
            profit_factor = total_profits / total_losses if total_losses > 0 else 0

            # Update labels
            self.total_trades_label.setText(str(total_trades))
            self.winning_trades_label.setText(str(winning_trades))
            self.losing_trades_label.setText(str(losing_trades))
            self.win_rate_label.setText(f"{win_rate:.2f}%")

            # Color code total P&L
            self.total_pnl_analytics_label.setText(f"₹{total_pnl:.2f}")
            if total_pnl > 0:
                self.total_pnl_analytics_label.setStyleSheet("color: green; font-weight: bold;")
            elif total_pnl < 0:
                self.total_pnl_analytics_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.total_pnl_analytics_label.setStyleSheet("color: black;")

            self.avg_profit_label.setText(f"₹{avg_profit:.2f}")
            self.avg_loss_label.setText(f"₹{avg_loss:.2f}")
            self.largest_win_label.setText(f"₹{largest_win:.2f}")
            self.largest_loss_label.setText(f"₹{largest_loss:.2f}")
            self.profit_factor_label.setText(f"{profit_factor:.2f}")

        except Exception as e:
            self.logger.error(f"Failed to update trading analytics: {e}")

    def add_to_watchlist(self):
        """Add symbol to watchlist"""
        try:
            symbol = self.watchlist_symbol_input.text().strip().upper()
            if not symbol:
                QMessageBox.warning(self, "Invalid Input", "Please enter a symbol.")
                return

            # Load existing watchlist
            watchlist = self.load_watchlist()

            if symbol not in watchlist:
                watchlist.append(symbol)
                self.save_watchlist(watchlist)
                self.refresh_watchlist()
                self.watchlist_symbol_input.clear()
                QMessageBox.information(self, "Success", f"{symbol} added to watchlist.")
            else:
                QMessageBox.warning(self, "Duplicate", f"{symbol} is already in watchlist.")

        except Exception as e:
            self.logger.error(f"Failed to add to watchlist: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add to watchlist: {e}")

    def remove_from_watchlist(self):
        """Remove selected symbol from watchlist"""
        try:
            current_row = self.watchlist_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "No Selection", "Please select a symbol to remove.")
                return

            symbol_item = self.watchlist_table.item(current_row, 0)
            if symbol_item:
                symbol = symbol_item.text()

                reply = QMessageBox.question(self, "Confirm Removal",
                                           f"Remove {symbol} from watchlist?",
                                           QMessageBox.Yes | QMessageBox.No)

                if reply == QMessageBox.Yes:
                    watchlist = self.load_watchlist()
                    if symbol in watchlist:
                        watchlist.remove(symbol)
                        self.save_watchlist(watchlist)
                        self.refresh_watchlist()
                        QMessageBox.information(self, "Success", f"{symbol} removed from watchlist.")

        except Exception as e:
            self.logger.error(f"Failed to remove from watchlist: {e}")
            QMessageBox.critical(self, "Error", f"Failed to remove from watchlist: {e}")

    def refresh_watchlist(self):
        """Refresh watchlist with current market data"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            watchlist = self.load_watchlist()
            if not watchlist:
                self.watchlist_table.setRowCount(0)
                return

            # Prepare instruments for quote
            instruments = [f"NSE:{symbol}" for symbol in watchlist]

            # Get quotes for all watchlist symbols
            quotes_data = self.api_client.get_quote(instruments)

            self.watchlist_table.setRowCount(len(watchlist))

            for row, symbol in enumerate(watchlist):
                instrument = f"NSE:{symbol}"

                if instrument in quotes_data:
                    quote = quotes_data[instrument]

                    # Extract quote data
                    ltp = quote.get('last_price', 0)
                    ohlc = quote.get('ohlc', {})
                    prev_close = ohlc.get('close', ltp)
                    change = ltp - prev_close
                    change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                    volume = quote.get('volume', 0)
                    high = ohlc.get('high', 0)
                    low = ohlc.get('low', 0)

                    # Update table
                    self.watchlist_table.setItem(row, 0, QTableWidgetItem(symbol))
                    self.watchlist_table.setItem(row, 1, QTableWidgetItem(f"₹{ltp:.2f}"))

                    change_item = QTableWidgetItem(f"₹{change:+.2f}")
                    change_item.setForeground(QColor("green" if change >= 0 else "red"))
                    self.watchlist_table.setItem(row, 2, change_item)

                    change_pct_item = QTableWidgetItem(f"{change_pct:+.2f}%")
                    change_pct_item.setForeground(QColor("green" if change_pct >= 0 else "red"))
                    self.watchlist_table.setItem(row, 3, change_pct_item)

                    self.watchlist_table.setItem(row, 4, QTableWidgetItem(f"{volume:,}"))
                    self.watchlist_table.setItem(row, 5, QTableWidgetItem(f"₹{high:.2f}"))
                    self.watchlist_table.setItem(row, 6, QTableWidgetItem(f"₹{low:.2f}"))
                    self.watchlist_table.setItem(row, 7, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
                else:
                    # No data available
                    self.watchlist_table.setItem(row, 0, QTableWidgetItem(symbol))
                    for col in range(1, 8):
                        self.watchlist_table.setItem(row, col, QTableWidgetItem("--"))

        except Exception as e:
            self.logger.error(f"Failed to refresh watchlist: {e}")
            QMessageBox.critical(self, "Error", f"Failed to refresh watchlist: {e}")

    def load_watchlist(self) -> List[str]:
        """Load watchlist from file"""
        try:
            watchlist_file = self.data_manager.data_dir / "watchlist.json"
            if watchlist_file.exists():
                import json
                with open(watchlist_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.error(f"Failed to load watchlist: {e}")
            return []

    def save_watchlist(self, watchlist: List[str]):
        """Save watchlist to file"""
        try:
            watchlist_file = self.data_manager.data_dir / "watchlist.json"
            import json
            with open(watchlist_file, 'w') as f:
                json.dump(watchlist, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save watchlist: {e}")

    def update_market_overview(self):
        """Update market overview with indices and market movers"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                return

            # Update market indices (major indices)
            indices = ["NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:NIFTY IT", "BSE:SENSEX"]
            indices_data = self.api_client.get_quote(indices)

            self.indices_table.setRowCount(len(indices))

            for row, instrument in enumerate(indices):
                index_name = instrument.split(':')[1]

                if instrument in indices_data:
                    quote = indices_data[instrument]
                    ltp = quote.get('last_price', 0)
                    ohlc = quote.get('ohlc', {})
                    prev_close = ohlc.get('close', ltp)
                    change = ltp - prev_close
                    change_pct = (change / prev_close * 100) if prev_close > 0 else 0

                    self.indices_table.setItem(row, 0, QTableWidgetItem(index_name))
                    self.indices_table.setItem(row, 1, QTableWidgetItem(f"{ltp:.2f}"))

                    change_item = QTableWidgetItem(f"{change:+.2f}")
                    change_item.setForeground(QColor("green" if change >= 0 else "red"))
                    self.indices_table.setItem(row, 2, change_item)

                    change_pct_item = QTableWidgetItem(f"{change_pct:+.2f}%")
                    change_pct_item.setForeground(QColor("green" if change_pct >= 0 else "red"))
                    self.indices_table.setItem(row, 3, change_pct_item)

            # Note: Top gainers/losers and most active would require additional API calls
            # or market data feeds that may not be available in basic Kite Connect
            self.logger.info("Market overview updated successfully")

        except Exception as e:
            self.logger.error(f"Failed to update market overview: {e}")

    def on_symbol_search(self, text: str):
        """Handle symbol search input"""
        try:
            if len(text) >= 2:  # Start searching after 2 characters
                self.search_instruments_async(text)
        except Exception as e:
            self.logger.error(f"Failed to handle symbol search: {e}")

    def search_instruments_async(self, search_text: str):
        """Search instruments asynchronously"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                return

            # This would require implementing instrument search in the API client
            # For now, we'll show a basic implementation
            instruments = self.api_client.get_instruments()
            if instruments:
                matching_instruments = [
                    inst for inst in instruments
                    if search_text.upper() in inst.get('tradingsymbol', '').upper()
                ][:10]  # Limit to 10 results

                if matching_instruments:
                    self.symbol_suggestions.clear()
                    for inst in matching_instruments:
                        symbol = inst.get('tradingsymbol', '')
                        exchange = inst.get('exchange', '')
                        self.symbol_suggestions.addItem(f"{symbol} ({exchange})")
                    self.symbol_suggestions.setVisible(True)
                else:
                    self.symbol_suggestions.setVisible(False)

        except Exception as e:
            self.logger.error(f"Failed to search instruments: {e}")

    def search_instruments(self):
        """Manual instrument search"""
        try:
            search_text = self.symbol_input.text().strip()
            if search_text:
                self.search_instruments_async(search_text)
        except Exception as e:
            self.logger.error(f"Failed to search instruments: {e}")

    def on_symbol_selected(self, selected_text: str):
        """Handle symbol selection from suggestions"""
        try:
            if selected_text and "(" in selected_text:
                symbol = selected_text.split(" (")[0]
                exchange = selected_text.split("(")[1].replace(")", "")

                self.symbol_input.setText(symbol)
                self.exchange_combo.setCurrentText(exchange)
                self.symbol_suggestions.setVisible(False)

                # Auto-get quote for selected symbol
                self.get_symbol_quote()

        except Exception as e:
            self.logger.error(f"Failed to handle symbol selection: {e}")

    def update_order_preview(self):
        """Update order preview and risk analysis"""
        try:
            symbol = self.symbol_input.text().strip().upper()
            transaction = self.transaction_combo.currentText()
            quantity = self.quantity_input.value()
            order_type = self.order_type_combo.currentText()
            price = self.price_input.value() if order_type in ["LIMIT", "SL"] else 0
            product = self.product_combo.currentText()

            # Update preview labels
            self.preview_symbol_label.setText(symbol or "--")
            self.preview_transaction_label.setText(transaction)
            self.preview_quantity_label.setText(f"{quantity:,}")

            if order_type == "MARKET":
                self.preview_price_label.setText("Market Price")
            else:
                self.preview_price_label.setText(f"₹{price:.2f}")

            # Calculate order value
            order_value = 0
            if order_type == "MARKET":
                # Try to use current price if available
                current_price_text = self.current_price_label.text()
                if "₹" in current_price_text:
                    try:
                        current_price = float(current_price_text.split("₹")[1])
                        order_value = current_price * quantity
                    except:
                        order_value = 0
            else:
                order_value = price * quantity

            self.preview_value_label.setText(f"₹{order_value:,.2f}")

            # Estimate charges (basic calculation)
            brokerage = min(20, order_value * 0.0003)  # Max ₹20 or 0.03%
            stt = order_value * 0.001 if transaction == "SELL" else order_value * 0.0001
            exchange_charges = order_value * 0.0000345
            gst = (brokerage + exchange_charges) * 0.18
            total_charges = brokerage + stt + exchange_charges + gst

            self.preview_charges_label.setText(f"₹{total_charges:.2f}")

            total_required = order_value + (total_charges if transaction == "BUY" else -total_charges)
            self.preview_total_label.setText(f"₹{total_required:,.2f}")

            # Update risk analysis
            self.update_risk_analysis(total_required, product)

        except Exception as e:
            self.logger.error(f"Failed to update order preview: {e}")

    def update_risk_analysis(self, required_amount: float, product: str):
        """Update risk analysis display"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                return

            # Get margin data
            margins = self.api_client.get_margins()
            if margins:
                available_margin = margins.get('equity', {}).get('available', {}).get('cash', 0)

                self.available_margin_label.setText(f"₹{available_margin:,.2f}")
                self.required_margin_label.setText(f"₹{required_amount:,.2f}")

                if available_margin > 0:
                    utilization = (required_amount / available_margin) * 100
                    self.margin_utilization_label.setText(f"{utilization:.1f}%")

                    # Risk level assessment
                    if utilization <= 50:
                        risk_level = "Low"
                        risk_color = "green"
                    elif utilization <= 80:
                        risk_level = "Medium"
                        risk_color = "orange"
                    else:
                        risk_level = "High"
                        risk_color = "red"

                    self.risk_level_label.setText(risk_level)
                    self.risk_level_label.setStyleSheet(f"color: {risk_color}; font-weight: bold;")
                else:
                    self.margin_utilization_label.setText("--")
                    self.risk_level_label.setText("--")

        except Exception as e:
            self.logger.error(f"Failed to update risk analysis: {e}")

    def quick_order(self, transaction_type: str):
        """Place a quick market order"""
        try:
            symbol = self.symbol_input.text().strip()
            if not symbol:
                QMessageBox.warning(self, "Missing Symbol", "Please enter a symbol first.")
                return

            # Set quick order parameters
            self.transaction_combo.setCurrentText(transaction_type)
            self.order_type_combo.setCurrentText("MARKET")

            # Place the order
            self.place_order()

        except Exception as e:
            self.logger.error(f"Failed to place quick order: {e}")

    def square_off_all_positions(self):
        """Square off all open positions"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            reply = QMessageBox.question(self, "Confirm Square Off",
                                       "Are you sure you want to square off ALL open positions?",
                                       QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                positions = self.api_client.get_positions()
                if positions:
                    net_positions = positions.get('net', [])
                    open_positions = [p for p in net_positions if p.get('quantity', 0) != 0]

                    if not open_positions:
                        QMessageBox.information(self, "No Positions", "No open positions to square off.")
                        return

                    squared_off = 0
                    failed = 0

                    for position in open_positions:
                        try:
                            quantity = abs(int(position.get('quantity', 0)))
                            if quantity > 0:
                                transaction_type = "SELL" if int(position.get('quantity', 0)) > 0 else "BUY"

                                order_params = {
                                    "variety": "regular",
                                    "exchange": position.get('exchange'),
                                    "tradingsymbol": position.get('tradingsymbol'),
                                    "transaction_type": transaction_type,
                                    "quantity": quantity,
                                    "product": position.get('product'),
                                    "order_type": "MARKET",
                                    "validity": "DAY"
                                }

                                order_id = self.api_client.place_order(**order_params)
                                if order_id:
                                    squared_off += 1
                                else:
                                    failed += 1
                        except Exception as e:
                            self.logger.error(f"Failed to square off position {position.get('tradingsymbol')}: {e}")
                            failed += 1

                    message = f"Square off complete!\nSquared off: {squared_off} positions"
                    if failed > 0:
                        message += f"\nFailed: {failed} positions"

                    QMessageBox.information(self, "Square Off Complete", message)
                    self.refresh_data()

        except Exception as e:
            self.logger.error(f"Failed to square off positions: {e}")
            QMessageBox.critical(self, "Error", f"Failed to square off positions: {e}")

    def apply_history_filters(self):
        """Apply filters to order history with graceful degradation"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                if not self.authentication_skipped:
                    QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                else:
                    self.logger.info("Cannot apply filters - authentication was skipped")
                return

            orders = self.api_client.get_orders()
            self.update_order_history_table(orders)

        except Exception as e:
            self.logger.error(f"Failed to apply history filters: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply filters: {e}")

    def refresh_analytics_data(self):
        """Refresh all analytics data with graceful degradation"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                if not self.authentication_skipped:
                    QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                else:
                    self.logger.info("Cannot refresh analytics - authentication was skipped")
                return

            # Get all required data
            orders = self.api_client.get_orders()
            trades = self.api_client.get_trades()  # Get detailed trades data
            positions = self.api_client.get_positions()
            holdings = self.api_client.get_holdings()

            # Update all analytics with comprehensive data
            self.update_analytics_dashboard(orders, trades)
            self.update_pnl_analysis(orders, trades)
            self.update_trade_history_analytics(orders, trades)
            self.update_performance_analysis(orders, trades)
            self.update_risk_analysis(positions, holdings)

            QMessageBox.information(self, "Success", "Analytics data refreshed successfully.")

        except Exception as e:
            self.logger.error(f"Failed to refresh analytics data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to refresh analytics data: {e}")

    def on_analytics_period_changed(self, period: str):
        """Handle analytics period change"""
        try:
            # Refresh analytics with new period
            self.refresh_analytics_data()
        except Exception as e:
            self.logger.error(f"Failed to change analytics period: {e}")

    def update_analytics_dashboard(self, orders: List[Order], trades: List[Dict[str, Any]]):
        """Update analytics dashboard with comprehensive key metrics"""
        try:
            # Filter orders and trades based on selected period
            filtered_orders = self.filter_orders_by_period(orders)
            filtered_trades = self.filter_trades_by_period(trades)
            completed_orders = [o for o in filtered_orders if o.status == "COMPLETE"]

            total_trades = len(filtered_trades)  # Use actual trades count

            if total_trades == 0:
                # Reset all labels to zero
                self.total_trades_label.setText("0")
                self.winning_trades_label.setText("0")
                self.losing_trades_label.setText("0")
                self.win_rate_label.setText("0.00%")
                self.total_pnl_analytics_label.setText("₹0.00")
                self.avg_profit_label.setText("₹0.00")
                self.avg_loss_label.setText("₹0.00")
                self.largest_win_label.setText("₹0.00")
                self.largest_loss_label.setText("₹0.00")
                self.profit_factor_label.setText("0.00")
                self.sharpe_ratio_label.setText("0.00")
                self.max_drawdown_label.setText("₹0.00")
                return

            # Calculate P&L for each trade (simplified calculation)
            trade_pnls = []
            total_pnl = 0

            for order in completed_orders:
                # This is a simplified P&L calculation
                # In reality, you'd need to match buy/sell orders
                avg_price = getattr(order, 'average_price', order.price) or order.price
                quantity = getattr(order, 'filled_quantity', order.quantity) or order.quantity

                if order.transaction_type == "SELL":
                    pnl = (avg_price * quantity) * 0.01  # Simplified 1% profit assumption
                else:
                    pnl = -(avg_price * quantity) * 0.005  # Simplified 0.5% cost assumption

                trade_pnls.append(pnl)
                total_pnl += pnl

            # Calculate metrics
            winning_trades = len([pnl for pnl in trade_pnls if pnl > 0])
            losing_trades = len([pnl for pnl in trade_pnls if pnl < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            profits = [pnl for pnl in trade_pnls if pnl > 0]
            losses = [pnl for pnl in trade_pnls if pnl < 0]

            avg_profit = sum(profits) / len(profits) if profits else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            largest_win = max(trade_pnls) if trade_pnls else 0
            largest_loss = min(trade_pnls) if trade_pnls else 0

            profit_factor = abs(sum(profits) / sum(losses)) if losses and sum(losses) != 0 else 0

            # Update labels
            self.total_trades_label.setText(str(total_trades))
            self.winning_trades_label.setText(str(winning_trades))
            self.losing_trades_label.setText(str(losing_trades))
            self.win_rate_label.setText(f"{win_rate:.1f}%")

            # Color code total P&L
            pnl_color = "green" if total_pnl >= 0 else "red"
            self.total_pnl_analytics_label.setText(f"₹{total_pnl:,.2f}")
            self.total_pnl_analytics_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")

            self.avg_profit_label.setText(f"₹{avg_profit:,.2f}")
            self.avg_profit_label.setStyleSheet("color: green;")

            self.avg_loss_label.setText(f"₹{avg_loss:,.2f}")
            self.avg_loss_label.setStyleSheet("color: red;")

            self.largest_win_label.setText(f"₹{largest_win:,.2f}")
            self.largest_win_label.setStyleSheet("color: green; font-weight: bold;")

            self.largest_loss_label.setText(f"₹{largest_loss:,.2f}")
            self.largest_loss_label.setStyleSheet("color: red; font-weight: bold;")

            self.profit_factor_label.setText(f"{profit_factor:.2f}")

            # Calculate Sharpe ratio (simplified)
            if trade_pnls:
                import statistics
                returns_std = statistics.stdev(trade_pnls) if len(trade_pnls) > 1 else 0
                avg_return = statistics.mean(trade_pnls)
                sharpe_ratio = (avg_return / returns_std) if returns_std != 0 else 0
                self.sharpe_ratio_label.setText(f"{sharpe_ratio:.2f}")

            # Calculate max drawdown (simplified)
            cumulative_pnl = 0
            peak = 0
            max_drawdown = 0

            for pnl in trade_pnls:
                cumulative_pnl += pnl
                if cumulative_pnl > peak:
                    peak = cumulative_pnl
                drawdown = peak - cumulative_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            self.max_drawdown_label.setText(f"₹{max_drawdown:,.2f}")
            self.max_drawdown_label.setStyleSheet("color: red;")

        except Exception as e:
            self.logger.error(f"Failed to update analytics dashboard: {e}")

    def filter_orders_by_period(self, orders: List[Order]) -> List[Order]:
        """Filter orders based on selected period"""
        try:
            period = self.analytics_period_combo.currentText()
            from datetime import datetime, timedelta

            now = datetime.now()
            if period == "Last 7 Days":
                cutoff = now - timedelta(days=7)
            elif period == "Last 30 Days":
                cutoff = now - timedelta(days=30)
            elif period == "Last 90 Days":
                cutoff = now - timedelta(days=90)
            elif period == "Last 1 Year":
                cutoff = now - timedelta(days=365)
            else:  # All Time
                return orders

            return [o for o in orders if o.order_timestamp >= cutoff]

        except Exception as e:
            self.logger.error(f"Failed to filter orders by period: {e}")
            return orders

    def filter_trades_by_period(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter trades based on selected analytics period"""
        try:
            period = self.analytics_period_combo.currentText()
            from datetime import datetime, timedelta

            now = datetime.now()
            if period == "Last 7 Days":
                cutoff = now - timedelta(days=7)
            elif period == "Last 30 Days":
                cutoff = now - timedelta(days=30)
            elif period == "Last 90 Days":
                cutoff = now - timedelta(days=90)
            elif period == "Last 1 Year":
                cutoff = now - timedelta(days=365)
            else:  # All Time
                return trades

            filtered_trades = []
            for trade in trades:
                try:
                    # Parse trade timestamp
                    trade_time_str = trade.get('fill_timestamp', '')
                    if trade_time_str:
                        # Handle different timestamp formats
                        if 'T' in trade_time_str:
                            trade_time = datetime.fromisoformat(trade_time_str.replace('Z', '+00:00'))
                        else:
                            trade_time = datetime.strptime(trade_time_str, "%Y-%m-%d %H:%M:%S")

                        if trade_time >= cutoff:
                            filtered_trades.append(trade)
                    else:
                        # If no timestamp, include the trade
                        filtered_trades.append(trade)
                except:
                    # If timestamp parsing fails, include the trade
                    filtered_trades.append(trade)

            return filtered_trades

        except Exception as e:
            self.logger.error(f"Failed to filter trades by period: {e}")
            return trades

    def update_pnl_analysis(self, orders: List[Order], trades: List[Dict[str, Any]] = None):
        """Update P&L analysis tables"""
        try:
            filtered_orders = self.filter_orders_by_period(orders)
            completed_orders = [o for o in filtered_orders if o.status == "COMPLETE"]

            # Daily P&L analysis
            daily_pnl = {}
            for order in completed_orders:
                date_str = order.order_timestamp.strftime("%Y-%m-%d")
                if date_str not in daily_pnl:
                    daily_pnl[date_str] = {
                        'trades': 0, 'gross_pnl': 0, 'charges': 0, 'net_pnl': 0
                    }

                daily_pnl[date_str]['trades'] += 1
                # Simplified P&L calculation
                avg_price = getattr(order, 'average_price', order.price) or order.price
                quantity = getattr(order, 'filled_quantity', order.quantity) or order.quantity
                trade_value = avg_price * quantity

                if order.transaction_type == "SELL":
                    gross_pnl = trade_value * 0.01  # Simplified 1% profit
                else:
                    gross_pnl = -trade_value * 0.005  # Simplified 0.5% cost

                charges = trade_value * 0.001  # Simplified 0.1% charges
                net_pnl = gross_pnl - charges

                daily_pnl[date_str]['gross_pnl'] += gross_pnl
                daily_pnl[date_str]['charges'] += charges
                daily_pnl[date_str]['net_pnl'] += net_pnl

            # Update daily P&L table
            sorted_dates = sorted(daily_pnl.keys(), reverse=True)
            self.daily_pnl_table.setRowCount(len(sorted_dates))

            cumulative_pnl = 0
            for row, date_str in enumerate(sorted_dates):
                data = daily_pnl[date_str]
                cumulative_pnl += data['net_pnl']

                self.daily_pnl_table.setItem(row, 0, QTableWidgetItem(date_str))
                self.daily_pnl_table.setItem(row, 1, QTableWidgetItem(str(data['trades'])))

                gross_item = QTableWidgetItem(f"₹{data['gross_pnl']:,.2f}")
                gross_item.setForeground(QColor("green" if data['gross_pnl'] >= 0 else "red"))
                self.daily_pnl_table.setItem(row, 2, gross_item)

                self.daily_pnl_table.setItem(row, 3, QTableWidgetItem(f"₹{data['charges']:,.2f}"))

                net_item = QTableWidgetItem(f"₹{data['net_pnl']:,.2f}")
                net_item.setForeground(QColor("green" if data['net_pnl'] >= 0 else "red"))
                self.daily_pnl_table.setItem(row, 4, net_item)

                cum_item = QTableWidgetItem(f"₹{cumulative_pnl:,.2f}")
                cum_item.setForeground(QColor("green" if cumulative_pnl >= 0 else "red"))
                self.daily_pnl_table.setItem(row, 5, cum_item)

            # Product P&L breakdown
            product_pnl = {}
            total_pnl = 0

            for order in completed_orders:
                product = order.product
                if product not in product_pnl:
                    product_pnl[product] = {'trades': 0, 'pnl': 0}

                product_pnl[product]['trades'] += 1
                # Simplified P&L calculation
                avg_price = getattr(order, 'average_price', order.price) or order.price
                quantity = getattr(order, 'filled_quantity', order.quantity) or order.quantity
                trade_value = avg_price * quantity

                if order.transaction_type == "SELL":
                    pnl = trade_value * 0.01
                else:
                    pnl = -trade_value * 0.005

                product_pnl[product]['pnl'] += pnl
                total_pnl += pnl

            self.product_pnl_table.setRowCount(len(product_pnl))
            for row, (product, data) in enumerate(product_pnl.items()):
                percentage = (data['pnl'] / total_pnl * 100) if total_pnl != 0 else 0

                self.product_pnl_table.setItem(row, 0, QTableWidgetItem(product))
                self.product_pnl_table.setItem(row, 1, QTableWidgetItem(str(data['trades'])))

                pnl_item = QTableWidgetItem(f"₹{data['pnl']:,.2f}")
                pnl_item.setForeground(QColor("green" if data['pnl'] >= 0 else "red"))
                self.product_pnl_table.setItem(row, 2, pnl_item)

                self.product_pnl_table.setItem(row, 3, QTableWidgetItem(f"{percentage:.1f}%"))

            # Exchange P&L breakdown
            exchange_pnl = {}

            for order in completed_orders:
                exchange = order.exchange
                if exchange not in exchange_pnl:
                    exchange_pnl[exchange] = {'trades': 0, 'pnl': 0}

                exchange_pnl[exchange]['trades'] += 1
                # Simplified P&L calculation
                avg_price = getattr(order, 'average_price', order.price) or order.price
                quantity = getattr(order, 'filled_quantity', order.quantity) or order.quantity
                trade_value = avg_price * quantity

                if order.transaction_type == "SELL":
                    pnl = trade_value * 0.01
                else:
                    pnl = -trade_value * 0.005

                exchange_pnl[exchange]['pnl'] += pnl

            self.exchange_pnl_table.setRowCount(len(exchange_pnl))
            for row, (exchange, data) in enumerate(exchange_pnl.items()):
                percentage = (data['pnl'] / total_pnl * 100) if total_pnl != 0 else 0

                self.exchange_pnl_table.setItem(row, 0, QTableWidgetItem(exchange))
                self.exchange_pnl_table.setItem(row, 1, QTableWidgetItem(str(data['trades'])))

                pnl_item = QTableWidgetItem(f"₹{data['pnl']:,.2f}")
                pnl_item.setForeground(QColor("green" if data['pnl'] >= 0 else "red"))
                self.exchange_pnl_table.setItem(row, 2, pnl_item)

                self.exchange_pnl_table.setItem(row, 3, QTableWidgetItem(f"{percentage:.1f}%"))

        except Exception as e:
            self.logger.error(f"Failed to update P&L analysis: {e}")

    def update_trade_history_analytics(self, orders: List[Order], trades: List = None):
        """Update trade history table with analytics filters"""
        try:
            filtered_orders = self.apply_analytics_filters_to_orders(orders)

            self.trade_history_table.setRowCount(len(filtered_orders))

            for row, order in enumerate(filtered_orders):
                self.trade_history_table.setItem(row, 0, QTableWidgetItem(order.order_timestamp.strftime("%d-%m-%Y")))
                self.trade_history_table.setItem(row, 1, QTableWidgetItem(order.order_timestamp.strftime("%H:%M:%S")))
                self.trade_history_table.setItem(row, 2, QTableWidgetItem(order.tradingsymbol))
                self.trade_history_table.setItem(row, 3, QTableWidgetItem(order.exchange))
                self.trade_history_table.setItem(row, 4, QTableWidgetItem(order.order_type))
                self.trade_history_table.setItem(row, 5, QTableWidgetItem(order.transaction_type))

                quantity = getattr(order, 'filled_quantity', order.quantity) or order.quantity
                self.trade_history_table.setItem(row, 6, QTableWidgetItem(str(quantity)))

                avg_price = getattr(order, 'average_price', order.price) or order.price
                self.trade_history_table.setItem(row, 7, QTableWidgetItem(f"₹{avg_price:.2f}"))

                amount = avg_price * quantity
                self.trade_history_table.setItem(row, 8, QTableWidgetItem(f"₹{amount:,.2f}"))

                self.trade_history_table.setItem(row, 9, QTableWidgetItem(order.product))

                status_item = QTableWidgetItem(order.status)
                if order.status == "COMPLETE":
                    status_item.setForeground(QColor("green"))
                elif order.status == "CANCELLED":
                    status_item.setForeground(QColor("orange"))
                elif order.status == "REJECTED":
                    status_item.setForeground(QColor("red"))
                self.trade_history_table.setItem(row, 10, status_item)

                # Simplified P&L calculation
                if order.transaction_type == "SELL":
                    pnl = amount * 0.01
                else:
                    pnl = -amount * 0.005

                charges = amount * 0.001
                net_pnl = pnl - charges

                pnl_item = QTableWidgetItem(f"₹{pnl:,.2f}")
                pnl_item.setForeground(QColor("green" if pnl >= 0 else "red"))
                self.trade_history_table.setItem(row, 11, pnl_item)

                self.trade_history_table.setItem(row, 12, QTableWidgetItem(f"₹{charges:.2f}"))

                net_pnl_item = QTableWidgetItem(f"₹{net_pnl:,.2f}")
                net_pnl_item.setForeground(QColor("green" if net_pnl >= 0 else "red"))
                self.trade_history_table.setItem(row, 13, net_pnl_item)

        except Exception as e:
            self.logger.error(f"Failed to update trade history analytics: {e}")

    def toggle_api_secret_visibility(self, show: bool):
        """Toggle API secret visibility"""
        if show:
            self.api_secret_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_secret_input.setEchoMode(QLineEdit.Password)

    def test_api_connection(self):
        """Test API connection"""
        try:
            api_key = self.api_key_input.text().strip()
            api_secret = self.api_secret_input.text().strip()

            if not api_key or not api_secret:
                QMessageBox.warning(self, "Missing Credentials", "Please enter both API key and secret.")
                return

            # Create temporary config for testing
            from ..models import TradingConfig
            test_config = TradingConfig(
                api_key=api_key,
                api_secret=api_secret,
                sandbox_mode=self.sandbox_checkbox.isChecked()
            )

            # Test connection
            test_client = ZerodhaAPIClient(test_config, self.data_manager.data_dir)

            if test_client.kite:
                self.api_status_label.setText("Connection Test Successful")
                self.api_status_label.setStyleSheet("color: green; font-weight: bold;")
                QMessageBox.information(self, "Success", "API connection test successful!")
            else:
                self.api_status_label.setText("Connection Test Failed")
                self.api_status_label.setStyleSheet("color: red; font-weight: bold;")
                QMessageBox.warning(self, "Failed", "API connection test failed.")

        except Exception as e:
            self.logger.error(f"API connection test failed: {e}")
            self.api_status_label.setText("Connection Test Failed")
            self.api_status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.critical(self, "Error", f"Connection test failed: {e}")

    def clear_api_credentials(self):
        """Clear API credentials"""
        reply = QMessageBox.question(
            self, "Clear Credentials",
            "Are you sure you want to clear all API credentials?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.api_key_input.clear()
            self.api_secret_input.clear()
            self.api_status_label.setText("Not Connected")
            self.api_status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.information(self, "Cleared", "API credentials cleared.")

    def refresh_api_status(self):
        """Refresh comprehensive API status information"""
        try:
            if not self.api_client:
                self.api_status_label.setText("Not Initialized")
                self.api_status_label.setStyleSheet("color: red; font-weight: bold;")
                self.api_session_label.setText("--")
                self.api_last_request_label.setText("--")
                self.api_rate_limit_label.setText("--")
                self.api_uptime_label.setText("--")
                self.api_requests_count_label.setText("0")
                return

            if self.api_client.is_authenticated():
                self.api_status_label.setText("Connected & Authenticated")
                self.api_status_label.setStyleSheet("color: green; font-weight: bold;")

                # Get session information
                profile = self.api_client.get_profile()
                if profile:
                    session_info = f"{profile.get('user_id', 'Unknown')} ({profile.get('user_type', 'N/A')})"
                    self.api_session_label.setText(session_info)
                else:
                    self.api_session_label.setText("Session Active")

                # Calculate uptime
                if hasattr(self.api_client, 'connection_time'):
                    from datetime import datetime
                    uptime = datetime.now() - self.api_client.connection_time
                    uptime_str = f"{uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"
                    self.api_uptime_label.setText(uptime_str)
                else:
                    self.api_uptime_label.setText("Connected")

                # Request count (if tracked)
                if hasattr(self.api_client, 'request_count'):
                    self.api_requests_count_label.setText(str(self.api_client.request_count))
                else:
                    self.api_requests_count_label.setText("N/A")

                # Rate limit info (Zerodha has rate limits)
                self.api_rate_limit_label.setText("3 req/sec")

                # Last request time
                self.api_last_request_label.setText("Just now")

            elif self.api_client.is_connected:
                self.api_status_label.setText("Connected (Not Authenticated)")
                self.api_status_label.setStyleSheet("color: orange; font-weight: bold;")
                self.api_session_label.setText("Awaiting Authentication")
            else:
                self.api_status_label.setText("Disconnected")
                self.api_status_label.setStyleSheet("color: red; font-weight: bold;")
                self.api_session_label.setText("--")
                self.api_last_request_label.setText("--")
                self.api_uptime_label.setText("--")

        except Exception as e:
            self.logger.error(f"Failed to refresh API status: {e}")
            self.api_status_label.setText("Error")
            self.api_status_label.setStyleSheet("color: red; font-weight: bold;")

    def save_app_settings(self):
        """Save application settings"""
        try:
            app_settings = {
                'auto_refresh': self.auto_refresh_checkbox.isChecked(),
                'refresh_interval': self.refresh_interval_spinbox.value(),
                'refresh_on_focus': self.refresh_on_focus_checkbox.isChecked(),
                'theme': self.theme_combo.currentText(),
                'decimal_places': self.decimal_places_spinbox.value(),
                'show_zero_positions': self.show_zero_positions_checkbox.isChecked(),
                'compact_view': self.compact_view_checkbox.isChecked(),
                'enable_notifications': self.enable_notifications_checkbox.isChecked(),
                'notify_order_updates': self.notify_order_updates_checkbox.isChecked(),
                'notify_position_changes': self.notify_position_changes_checkbox.isChecked(),
                'notify_connection_status': self.notify_connection_status_checkbox.isChecked(),
                'connection_timeout': self.connection_timeout_spinbox.value(),
                'max_retry_attempts': self.max_retry_spinbox.value()
            }

            settings_file = self.data_manager.data_dir / "app_settings.json"
            import json
            with open(settings_file, 'w') as f:
                json.dump(app_settings, f, indent=2)

            # Apply settings immediately
            self.apply_app_settings(app_settings)

            QMessageBox.information(self, "Settings", "Application settings saved successfully!")

        except Exception as e:
            self.logger.error(f"Failed to save app settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save application settings: {e}")

    def load_app_settings(self):
        """Load application settings"""
        try:
            settings_file = self.data_manager.data_dir / "app_settings.json"
            if settings_file.exists():
                import json
                with open(settings_file, 'r') as f:
                    settings = json.load(f)

                # Update UI controls
                self.auto_refresh_checkbox.setChecked(settings.get('auto_refresh', True))
                self.refresh_interval_spinbox.setValue(settings.get('refresh_interval', 30))
                self.refresh_on_focus_checkbox.setChecked(settings.get('refresh_on_focus', True))
                self.theme_combo.setCurrentText(settings.get('theme', 'System'))
                self.decimal_places_spinbox.setValue(settings.get('decimal_places', 2))
                self.show_zero_positions_checkbox.setChecked(settings.get('show_zero_positions', False))
                self.compact_view_checkbox.setChecked(settings.get('compact_view', False))
                self.enable_notifications_checkbox.setChecked(settings.get('enable_notifications', True))
                self.notify_order_updates_checkbox.setChecked(settings.get('notify_order_updates', True))
                self.notify_position_changes_checkbox.setChecked(settings.get('notify_position_changes', False))
                self.notify_connection_status_checkbox.setChecked(settings.get('notify_connection_status', True))
                self.connection_timeout_spinbox.setValue(settings.get('connection_timeout', 30))
                self.max_retry_spinbox.setValue(settings.get('max_retry_attempts', 3))

                # Apply settings
                self.apply_app_settings(settings)

        except Exception as e:
            self.logger.error(f"Failed to load app settings: {e}")

    def apply_app_settings(self, settings: dict):
        """Apply application settings"""
        try:
            # Update refresh timer if needed
            if hasattr(self, 'refresh_timer'):
                if settings.get('auto_refresh', True):
                    interval = settings.get('refresh_interval', 30) * 1000  # Convert to milliseconds
                    self.refresh_timer.setInterval(interval)
                    if not self.refresh_timer.isActive():
                        self.refresh_timer.start()
                else:
                    self.refresh_timer.stop()

            # Apply theme (placeholder - would need actual theme implementation)
            theme = settings.get('theme', 'System')
            if theme == 'Dark':
                # Apply dark theme
                pass
            elif theme == 'Light':
                # Apply light theme
                pass
            # System theme is default

        except Exception as e:
            self.logger.error(f"Failed to apply app settings: {e}")

    def refresh_account_info(self):
        """Refresh account information"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            # Get user profile
            profile = self.api_client.get_profile()
            if profile:
                # Basic account information
                self.account_id_label.setText(profile.get('user_id', '--'))
                self.account_name_label.setText(profile.get('user_name', '--'))
                self.account_shortname_label.setText(profile.get('user_shortname', '--'))
                self.account_type_label.setText(profile.get('user_type', '--'))
                self.account_email_label.setText(profile.get('email', '--'))
                self.account_broker_label.setText(profile.get('broker', '--'))

                # Check if account is active
                if profile.get('enabled', False):
                    self.account_status_label.setText("Active")
                    self.account_status_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.account_status_label.setText("Inactive")
                    self.account_status_label.setStyleSheet("color: red; font-weight: bold;")

                # Trading permissions and capabilities
                exchanges = profile.get('exchanges', [])
                if exchanges:
                    exchanges_text = ", ".join(exchanges)
                    self.account_exchanges_label.setText(exchanges_text)
                else:
                    self.account_exchanges_label.setText("--")

                products = profile.get('products', [])
                if products:
                    products_text = ", ".join(products)
                    self.account_products_label.setText(products_text)
                else:
                    self.account_products_label.setText("--")

                order_types = profile.get('order_types', [])
                if order_types:
                    order_types_text = ", ".join(order_types)
                    self.account_order_types_label.setText(order_types_text)
                else:
                    self.account_order_types_label.setText("--")

                QMessageBox.information(self, "Success", "Account information refreshed successfully.")
            else:
                QMessageBox.warning(self, "Failed", "Failed to retrieve account information.")

        except Exception as e:
            self.logger.error(f"Failed to refresh account info: {e}")
            QMessageBox.critical(self, "Error", f"Failed to refresh account information: {e}")

    def refresh_trading_limits(self):
        """Refresh trading limits and margin information"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            # Get margins information
            margins = self.api_client.get_margins()
            if margins:
                # Equity segment
                equity = margins.get('equity', {})
                if equity:
                    available = equity.get('available', {}).get('cash', 0)
                    used = equity.get('utilised', {}).get('debits', 0)
                    self.equity_limit_label.setText(f"₹{available + used:,.2f}")
                    self.margin_available_label.setText(f"₹{available:,.2f}")
                    self.margin_used_label.setText(f"₹{used:,.2f}")
                    self.cash_balance_label.setText(f"₹{equity.get('net', 0):,.2f}")

                # Commodity segment
                commodity = margins.get('commodity', {})
                if commodity:
                    commodity_available = commodity.get('available', {}).get('cash', 0)
                    self.commodity_limit_label.setText(f"₹{commodity_available:,.2f}")

                # Intraday limits (usually same as equity for most brokers)
                self.intraday_limit_label.setText(f"₹{available:,.2f}")

                QMessageBox.information(self, "Success", "Trading limits refreshed successfully.")
            else:
                QMessageBox.warning(self, "Failed", "Failed to retrieve trading limits.")

        except Exception as e:
            self.logger.error(f"Failed to refresh trading limits: {e}")
            QMessageBox.critical(self, "Error", f"Failed to refresh trading limits: {e}")

    def clear_application_cache(self):
        """Clear application cache"""
        try:
            reply = QMessageBox.question(
                self, "Clear Cache",
                "Are you sure you want to clear all cached data? This will remove temporary files and cached market data.",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Clear cache files
                cache_dir = self.data_manager.data_dir / "cache"
                if cache_dir.exists():
                    import shutil
                    shutil.rmtree(cache_dir)
                    cache_dir.mkdir(exist_ok=True)

                QMessageBox.information(self, "Success", "Application cache cleared successfully.")

        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            QMessageBox.critical(self, "Error", f"Failed to clear cache: {e}")

    def export_application_data(self):
        """Export application data"""
        try:
            from PySide6.QtWidgets import QFileDialog

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Data", "trading_data_export.json", "JSON Files (*.json)"
            )

            if file_path:
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'watchlist': self.get_watchlist_data(),
                    'settings': self.get_all_settings(),
                    'version': '1.0'
                }

                import json
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)

                QMessageBox.information(self, "Success", f"Data exported successfully to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export data: {e}")

    def backup_application_settings(self):
        """Backup application settings"""
        try:
            from PySide6.QtWidgets import QFileDialog

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Backup Settings", "trading_settings_backup.json", "JSON Files (*.json)"
            )

            if file_path:
                settings_data = self.get_all_settings()
                settings_data['backup_timestamp'] = datetime.now().isoformat()

                import json
                with open(file_path, 'w') as f:
                    json.dump(settings_data, f, indent=2)

                QMessageBox.information(self, "Success", f"Settings backed up successfully to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to backup settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to backup settings: {e}")

    def restore_application_settings(self):
        """Restore application settings"""
        try:
            from PySide6.QtWidgets import QFileDialog

            file_path, _ = QFileDialog.getOpenFileName(
                self, "Restore Settings", "", "JSON Files (*.json)"
            )

            if file_path:
                reply = QMessageBox.question(
                    self, "Restore Settings",
                    "Are you sure you want to restore settings? This will overwrite current settings.",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    import json
                    with open(file_path, 'r') as f:
                        settings_data = json.load(f)

                    # Restore settings files
                    if 'trading_settings' in settings_data:
                        settings_file = self.data_manager.data_dir / "trading_settings.json"
                        with open(settings_file, 'w') as f:
                            json.dump(settings_data['trading_settings'], f, indent=2)

                    if 'app_settings' in settings_data:
                        settings_file = self.data_manager.data_dir / "app_settings.json"
                        with open(settings_file, 'w') as f:
                            json.dump(settings_data['app_settings'], f, indent=2)

                    # Reload settings
                    self.load_settings()
                    self.load_app_settings()

                    QMessageBox.information(self, "Success", "Settings restored successfully. Please restart the application.")

        except Exception as e:
            self.logger.error(f"Failed to restore settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to restore settings: {e}")

    def reset_all_settings(self):
        """Reset all settings to default"""
        try:
            reply = QMessageBox.question(
                self, "Reset Settings",
                "Are you sure you want to reset ALL settings to default? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Remove settings files
                settings_files = [
                    "trading_settings.json",
                    "app_settings.json",
                    "watchlist.json"
                ]

                for filename in settings_files:
                    settings_file = self.data_manager.data_dir / filename
                    if settings_file.exists():
                        settings_file.unlink()

                # Reset UI to defaults
                self.api_key_input.clear()
                self.api_secret_input.clear()
                self.sandbox_checkbox.setChecked(True)
                self.auto_connect_checkbox.setChecked(False)

                QMessageBox.information(self, "Success", "All settings reset to default. Please restart the application.")

        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to reset settings: {e}")

    def logout_and_clear_session(self):
        """Logout and clear session"""
        try:
            reply = QMessageBox.question(
                self, "Logout",
                "Are you sure you want to logout and clear the current session?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Disconnect from API
                if self.api_client:
                    self.api_client = None

                # Clear session files
                session_files = ["access_token.txt", "request_token.txt"]
                for filename in session_files:
                    session_file = self.data_manager.data_dir / filename
                    if session_file.exists():
                        session_file.unlink()

                # Update UI
                self.update_connection_status(False)
                self.clear_all_data()

                QMessageBox.information(self, "Success", "Logged out successfully.")

        except Exception as e:
            self.logger.error(f"Failed to logout: {e}")
            QMessageBox.critical(self, "Error", f"Failed to logout: {e}")

    def get_all_settings(self) -> dict:
        """Get all current settings"""
        try:
            settings = {}

            # Trading settings
            trading_file = self.data_manager.data_dir / "trading_settings.json"
            if trading_file.exists():
                import json
                with open(trading_file, 'r') as f:
                    settings['trading_settings'] = json.load(f)

            # App settings
            app_file = self.data_manager.data_dir / "app_settings.json"
            if app_file.exists():
                import json
                with open(app_file, 'r') as f:
                    settings['app_settings'] = json.load(f)

            return settings

        except Exception as e:
            self.logger.error(f"Failed to get all settings: {e}")
            return {}

    def get_watchlist_data(self) -> list:
        """Get current watchlist data"""
        try:
            watchlist_file = self.data_manager.data_dir / "watchlist.json"
            if watchlist_file.exists():
                import json
                with open(watchlist_file, 'r') as f:
                    return json.load(f)
            return []

        except Exception as e:
            self.logger.error(f"Failed to get watchlist data: {e}")
            return []

    def intelligent_refresh_data(self):
        """Intelligent data refresh with priority-based updates"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                self.logger.warning("Cannot refresh data - API client not authenticated")
                return

            if self.is_refreshing:
                self.logger.debug("Refresh already in progress, skipping...")
                return

            self.is_refreshing = True
            current_time = datetime.now()

            # Determine what needs refreshing based on intervals and priority
            refresh_tasks = []

            # High priority: Orders (most time-sensitive)
            if self.should_refresh('orders', current_time):
                refresh_tasks.append(('orders', self.refresh_orders_data))

            # Medium priority: Market data (for active trading)
            if self.should_refresh('market', current_time):
                refresh_tasks.append(('market', self.refresh_market_data))

            # Lower priority: Portfolio data (less frequent changes)
            if self.should_refresh('portfolio', current_time):
                refresh_tasks.append(('portfolio', self.refresh_portfolio_data))

            # Lowest priority: Analytics (least time-sensitive)
            if self.should_refresh('analytics', current_time):
                refresh_tasks.append(('analytics', self.refresh_analytics_data))

            # Execute refresh tasks
            for task_name, task_func in refresh_tasks:
                try:
                    self.logger.debug(f"Refreshing {task_name} data...")
                    task_func()
                    self.last_refresh_time[task_name] = current_time
                except Exception as e:
                    self.logger.error(f"Failed to refresh {task_name} data: {e}")

            # Update connection status
            self.update_connection_status(True)

            self.is_refreshing = False

        except Exception as e:
            self.logger.error(f"Error in intelligent refresh: {e}")
            self.is_refreshing = False

    def should_refresh(self, component: str, current_time: datetime) -> bool:
        """Determine if a component should be refreshed"""
        try:
            if component not in self.last_refresh_time:
                return True

            last_refresh = self.last_refresh_time[component]
            interval = self.refresh_intervals.get(component, 30)

            time_since_refresh = (current_time - last_refresh).total_seconds()
            return time_since_refresh >= interval

        except Exception as e:
            self.logger.error(f"Error checking refresh status for {component}: {e}")
            return True

    def refresh_portfolio_data(self):
        """Refresh portfolio-specific data"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                return

            # Get portfolio data
            holdings = self.api_client.get_holdings()
            positions = self.api_client.get_positions()

            # Update portfolio displays
            if holdings:
                self.update_holdings_table(holdings)

            if positions:
                self.update_positions_table(positions)

            # Update portfolio analytics if both data available
            if holdings and positions:
                self.update_portfolio_analytics(holdings, positions)

            self.logger.debug("Portfolio data refreshed successfully")

        except Exception as e:
            self.logger.error(f"Failed to refresh portfolio data: {e}")

    def refresh_market_data(self):
        """Refresh market-specific data"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                return

            # Refresh watchlist quotes
            self.refresh_watchlist_quotes()

            # Update market overview
            self.update_market_overview()

            self.logger.debug("Market data refreshed successfully")

        except Exception as e:
            self.logger.error(f"Failed to refresh market data: {e}")

    def refresh_orders_data(self):
        """Refresh orders-specific data"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                return

            # Get latest orders
            orders = self.api_client.get_orders()

            if orders:
                # Update all order-related displays
                self.update_active_orders_table(orders)
                self.update_order_history_table(orders)
                self.update_order_analytics(orders)

            self.logger.debug("Orders data refreshed successfully")

        except Exception as e:
            self.logger.error(f"Failed to refresh orders data: {e}")

    def start_intelligent_refresh_system(self):
        """Start the intelligent refresh system"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                return

            # Start main refresh timer (every 5 seconds for intelligent checking)
            self.refresh_timer.start(5000)

            # Start connection monitoring (every 30 seconds)
            self.connection_monitor_timer.start(30000)

            self.logger.info("Intelligent refresh system started")

        except Exception as e:
            self.logger.error(f"Failed to start intelligent refresh system: {e}")

    def stop_refresh_system(self):
        """Stop all refresh timers"""
        try:
            self.refresh_timer.stop()
            self.portfolio_refresh_timer.stop()
            self.market_refresh_timer.stop()
            self.orders_refresh_timer.stop()
            self.connection_monitor_timer.stop()

            self.is_refreshing = False
            self.refresh_queue.clear()

            self.logger.info("Refresh system stopped")

        except Exception as e:
            self.logger.error(f"Failed to stop refresh system: {e}")

    def monitor_connection(self):
        """Monitor API connection status"""
        try:
            if not self.api_client:
                return

            # Check if connection is still valid
            if self.api_client.is_authenticated():
                # Try a lightweight API call to verify connection
                try:
                    profile = self.api_client.get_profile()
                    if profile:
                        self.update_connection_status(True)
                    else:
                        self.handle_connection_loss()
                except Exception:
                    self.handle_connection_loss()
            else:
                self.handle_connection_loss()

        except Exception as e:
            self.logger.error(f"Error monitoring connection: {e}")
            self.handle_connection_loss()

    def handle_connection_loss(self):
        """Handle connection loss"""
        try:
            self.logger.warning("Connection lost, attempting to reconnect...")
            self.update_connection_status(False)

            # Stop refresh system temporarily
            self.stop_refresh_system()

            # Check if it's a token expiry issue
            if self.api_client and not self.api_client.is_authenticated():
                self.logger.info("Token expired - manual re-authentication required")
                self.status_label.setText("Token Expired - Please reconnect")
                self.status_label.setStyleSheet("color: orange; font-weight: bold;")

                # Show reconnection dialog
                from PySide6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "Token Expired",
                    "Your Zerodha access token has expired. Would you like to reconnect now?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    self.connect_to_zerodha()
                return

            # Attempt auto-reconnect if enabled
            if self.trading_config and self.trading_config.auto_login:
                self.start_retry_mechanism()

        except Exception as e:
            self.logger.error(f"Error handling connection loss: {e}")

    def start_retry_mechanism(self):
        """Start connection retry mechanism"""
        try:
            if self.retry_attempts < self.max_retry_attempts:
                self.retry_attempts += 1
                retry_delay = min(5000 * (2 ** (self.retry_attempts - 1)), 30000)  # Exponential backoff

                self.logger.info(f"Retry attempt {self.retry_attempts}/{self.max_retry_attempts} in {retry_delay/1000} seconds")
                self.retry_timer.start(retry_delay)
            else:
                self.logger.error("Max retry attempts reached, manual reconnection required")
                self.status_label.setText("Connection lost - Manual reconnection required")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")

        except Exception as e:
            self.logger.error(f"Error starting retry mechanism: {e}")

    def set_refresh_intervals(self, intervals: dict):
        """Set custom refresh intervals for different components"""
        try:
            self.refresh_intervals.update(intervals)
            self.logger.info(f"Refresh intervals updated: {self.refresh_intervals}")

        except Exception as e:
            self.logger.error(f"Failed to set refresh intervals: {e}")

    def force_refresh_component(self, component: str):
        """Force refresh a specific component"""
        try:
            if component == 'portfolio':
                self.refresh_portfolio_data()
            elif component == 'market':
                self.refresh_market_data()
            elif component == 'orders':
                self.refresh_orders_data()
            elif component == 'analytics':
                self.refresh_analytics_data()
            elif component == 'all':
                self.refresh_data()

            # Update last refresh time
            self.last_refresh_time[component] = datetime.now()

        except Exception as e:
            self.logger.error(f"Failed to force refresh {component}: {e}")

    def get_refresh_status(self) -> dict:
        """Get current refresh status"""
        try:
            current_time = datetime.now()
            status = {}

            for component in self.refresh_intervals.keys():
                last_refresh = self.last_refresh_time.get(component)
                if last_refresh:
                    seconds_since = (current_time - last_refresh).total_seconds()
                    status[component] = {
                        'last_refresh': last_refresh.strftime("%H:%M:%S"),
                        'seconds_since': int(seconds_since),
                        'next_refresh_in': max(0, self.refresh_intervals[component] - int(seconds_since))
                    }
                else:
                    status[component] = {
                        'last_refresh': 'Never',
                        'seconds_since': 0,
                        'next_refresh_in': 0
                    }

            return status

        except Exception as e:
            self.logger.error(f"Failed to get refresh status: {e}")
            return {}

    def export_analytics_report(self):
        """Export analytics report to file"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            # Get current orders for analytics
            orders = self.api_client.get_orders()
            if not orders:
                QMessageBox.information(self, "No Data", "No order data available for export.")
                return

            # Create analytics report data
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'total_orders': len(orders),
                'order_breakdown': {},
                'pnl_summary': {},
                'performance_metrics': {}
            }

            # Calculate order breakdown
            for order in orders:
                status = order.status
                if status not in report_data['order_breakdown']:
                    report_data['order_breakdown'][status] = 0
                report_data['order_breakdown'][status] += 1

            # Calculate P&L summary
            total_pnl = sum(getattr(order, 'pnl', 0) for order in orders)
            report_data['pnl_summary'] = {
                'total_pnl': total_pnl,
                'profitable_orders': len([o for o in orders if getattr(o, 'pnl', 0) > 0]),
                'loss_orders': len([o for o in orders if getattr(o, 'pnl', 0) < 0])
            }

            # Save to file
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Analytics Report",
                f"trading_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json)"
            )

            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(report_data, f, indent=2)

                QMessageBox.information(self, "Export Successful", f"Analytics report exported to:\n{file_path}")
                self.logger.info(f"Analytics report exported to: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to export analytics report: {e}")
            QMessageBox.critical(self, "Export Failed", f"Failed to export analytics report:\n{str(e)}")

    def apply_analytics_filters(self):
        """Apply analytics filters to data"""
        try:
            if not self.api_client or not self.api_client.is_authenticated():
                QMessageBox.warning(self, "Not Connected", "Please connect to Zerodha first.")
                return

            # Get orders and apply filters
            orders = self.api_client.get_orders()
            if orders:
                self.update_trade_history_analytics(orders)
                QMessageBox.information(self, "Success", "Analytics filters applied successfully.")
            else:
                QMessageBox.information(self, "No Data", "No order data available to filter.")

        except Exception as e:
            self.logger.error(f"Failed to apply analytics filters: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply analytics filters:\n{str(e)}")

    def apply_analytics_filters_to_orders(self, orders: List[Order]) -> List[Order]:
        """Apply current analytics filters to order list"""
        try:
            filtered_orders = orders.copy()

            # Filter by status
            status_filter = self.analytics_status_combo.currentText()
            if status_filter != "All":
                filtered_orders = [o for o in filtered_orders if o.status == status_filter]

            # Filter by symbol
            symbol_filter = self.analytics_symbol_input.text().strip().upper()
            if symbol_filter:
                filtered_orders = [o for o in filtered_orders if symbol_filter in o.tradingsymbol.upper()]

            # Filter by product
            product_filter = self.analytics_product_combo.currentText()
            if product_filter != "All":
                filtered_orders = [o for o in filtered_orders if o.product == product_filter]

            # Filter by exchange
            exchange_filter = self.analytics_exchange_combo.currentText()
            if exchange_filter != "All":
                filtered_orders = [o for o in filtered_orders if o.exchange == exchange_filter]

            # Filter by P&L range
            min_pnl = self.min_pnl_input.value()
            max_pnl = self.max_pnl_input.value()

            if min_pnl != -999999 or max_pnl != 999999:
                filtered_orders = [
                    o for o in filtered_orders
                    if min_pnl <= getattr(o, 'pnl', 0) <= max_pnl
                ]

            # Filter by period (from analytics period combo)
            filtered_orders = self.filter_orders_by_period(filtered_orders)

            return filtered_orders

        except Exception as e:
            self.logger.error(f"Failed to apply analytics filters to orders: {e}")
            return orders

    def clear_analytics_filters(self):
        """Clear all analytics filters"""
        try:
            # Reset all filter controls to default values
            self.analytics_status_combo.setCurrentText("All")
            self.analytics_symbol_input.clear()
            self.analytics_product_combo.setCurrentText("All")
            self.analytics_exchange_combo.setCurrentText("All")
            self.min_pnl_input.setValue(-999999)
            self.max_pnl_input.setValue(999999)

            # Refresh analytics with cleared filters
            self.apply_analytics_filters()

        except Exception as e:
            self.logger.error(f"Failed to clear analytics filters: {e}")

    def update_performance_analysis(self, orders: List[Order]):
        """Update performance analysis tables"""
        try:
            filtered_orders = self.filter_orders_by_period(orders)
            completed_orders = [o for o in filtered_orders if o.status == "COMPLETE"]

            if not completed_orders:
                return

            # Monthly performance analysis
            monthly_data = {}
            for order in completed_orders:
                month_key = order.order_timestamp.strftime("%Y-%m")
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'trades': 0, 'wins': 0, 'gross_pnl': 0, 'charges': 0,
                        'best_day': 0, 'worst_day': 0
                    }

                monthly_data[month_key]['trades'] += 1

                # Simplified P&L calculation
                avg_price = getattr(order, 'average_price', order.price) or order.price
                quantity = getattr(order, 'filled_quantity', order.quantity) or order.quantity
                trade_value = avg_price * quantity

                if order.transaction_type == "SELL":
                    pnl = trade_value * 0.01
                else:
                    pnl = -trade_value * 0.005

                if pnl > 0:
                    monthly_data[month_key]['wins'] += 1

                charges = trade_value * 0.001
                monthly_data[month_key]['gross_pnl'] += pnl
                monthly_data[month_key]['charges'] += charges

                # Track best/worst day (simplified)
                if pnl > monthly_data[month_key]['best_day']:
                    monthly_data[month_key]['best_day'] = pnl
                if pnl < monthly_data[month_key]['worst_day']:
                    monthly_data[month_key]['worst_day'] = pnl

            # Update monthly performance table
            sorted_months = sorted(monthly_data.keys(), reverse=True)
            self.monthly_performance_table.setRowCount(len(sorted_months))

            for row, month in enumerate(sorted_months):
                data = monthly_data[month]
                win_rate = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0
                net_pnl = data['gross_pnl'] - data['charges']

                self.monthly_performance_table.setItem(row, 0, QTableWidgetItem(month))
                self.monthly_performance_table.setItem(row, 1, QTableWidgetItem(str(data['trades'])))
                self.monthly_performance_table.setItem(row, 2, QTableWidgetItem(f"{win_rate:.1f}%"))

                gross_item = QTableWidgetItem(f"₹{data['gross_pnl']:,.2f}")
                gross_item.setForeground(QColor("green" if data['gross_pnl'] >= 0 else "red"))
                self.monthly_performance_table.setItem(row, 3, gross_item)

                self.monthly_performance_table.setItem(row, 4, QTableWidgetItem(f"₹{data['charges']:,.2f}"))

                net_item = QTableWidgetItem(f"₹{net_pnl:,.2f}")
                net_item.setForeground(QColor("green" if net_pnl >= 0 else "red"))
                self.monthly_performance_table.setItem(row, 5, net_item)

                self.monthly_performance_table.setItem(row, 6, QTableWidgetItem(f"₹{data['best_day']:,.2f}"))
                self.monthly_performance_table.setItem(row, 7, QTableWidgetItem(f"₹{data['worst_day']:,.2f}"))

            # Symbol performance analysis
            symbol_data = {}
            for order in completed_orders:
                symbol = order.tradingsymbol
                if symbol not in symbol_data:
                    symbol_data[symbol] = {
                        'trades': 0, 'wins': 0, 'total_pnl': 0, 'best_trade': 0, 'worst_trade': 0,
                        'volume': 0, 'turnover': 0
                    }

                symbol_data[symbol]['trades'] += 1

                # Simplified P&L calculation
                avg_price = getattr(order, 'average_price', order.price) or order.price
                quantity = getattr(order, 'filled_quantity', order.quantity) or order.quantity
                trade_value = avg_price * quantity

                if order.transaction_type == "SELL":
                    pnl = trade_value * 0.01
                else:
                    pnl = -trade_value * 0.005

                if pnl > 0:
                    symbol_data[symbol]['wins'] += 1

                symbol_data[symbol]['total_pnl'] += pnl
                symbol_data[symbol]['volume'] += quantity
                symbol_data[symbol]['turnover'] += trade_value

                if pnl > symbol_data[symbol]['best_trade']:
                    symbol_data[symbol]['best_trade'] = pnl
                if pnl < symbol_data[symbol]['worst_trade']:
                    symbol_data[symbol]['worst_trade'] = pnl

            # Update symbol performance table
            sorted_symbols = sorted(symbol_data.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
            self.symbol_performance_table.setRowCount(len(sorted_symbols))

            for row, (symbol, data) in enumerate(sorted_symbols):
                win_rate = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0
                avg_pnl = data['total_pnl'] / data['trades'] if data['trades'] > 0 else 0

                self.symbol_performance_table.setItem(row, 0, QTableWidgetItem(symbol))
                self.symbol_performance_table.setItem(row, 1, QTableWidgetItem(str(data['trades'])))
                self.symbol_performance_table.setItem(row, 2, QTableWidgetItem(f"{win_rate:.1f}%"))

                total_pnl_item = QTableWidgetItem(f"₹{data['total_pnl']:,.2f}")
                total_pnl_item.setForeground(QColor("green" if data['total_pnl'] >= 0 else "red"))
                self.symbol_performance_table.setItem(row, 3, total_pnl_item)

                avg_pnl_item = QTableWidgetItem(f"₹{avg_pnl:,.2f}")
                avg_pnl_item.setForeground(QColor("green" if avg_pnl >= 0 else "red"))
                self.symbol_performance_table.setItem(row, 4, avg_pnl_item)

                self.symbol_performance_table.setItem(row, 5, QTableWidgetItem(f"₹{data['best_trade']:,.2f}"))
                self.symbol_performance_table.setItem(row, 6, QTableWidgetItem(f"₹{data['worst_trade']:,.2f}"))
                self.symbol_performance_table.setItem(row, 7, QTableWidgetItem(f"{data['volume']:,}"))
                self.symbol_performance_table.setItem(row, 8, QTableWidgetItem(f"₹{data['turnover']:,.0f}"))

        except Exception as e:
            self.logger.error(f"Failed to update performance analysis: {e}")

    def update_risk_analysis(self, positions: List[Position], holdings: List[Holding]):
        """Update risk analysis display"""
        try:
            # Calculate portfolio-level risk metrics
            total_portfolio_value = 0
            position_values = []

            # Calculate from holdings
            for holding in holdings:
                value = holding.quantity * holding.last_price
                total_portfolio_value += value
                position_values.append(value)

            if total_portfolio_value == 0:
                return

            # Calculate basic risk metrics
            import statistics

            # Portfolio volatility (simplified using P&L variance)
            pnl_values = [holding.pnl for holding in holdings if holding.pnl != 0]
            if len(pnl_values) > 1:
                volatility = statistics.stdev(pnl_values) / total_portfolio_value * 100
                self.volatility_label.setText(f"{volatility:.2f}%")

            # Value at Risk (simplified 95% confidence)
            if pnl_values:
                sorted_pnl = sorted(pnl_values)
                var_index = int(len(sorted_pnl) * 0.05)  # 5th percentile
                var_value = abs(sorted_pnl[var_index]) if var_index < len(sorted_pnl) else 0
                self.var_label.setText(f"₹{var_value:,.2f}")

            # Update risk breakdown table
            self.risk_breakdown_table.setRowCount(len(holdings))

            for row, holding in enumerate(holdings):
                position_value = holding.quantity * holding.last_price
                risk_contribution = (position_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0

                # Simplified risk metrics per position
                position_volatility = abs(holding.pnl / position_value * 100) if position_value > 0 else 0
                position_var = abs(holding.pnl) * 0.05  # Simplified VaR

                self.risk_breakdown_table.setItem(row, 0, QTableWidgetItem(holding.tradingsymbol))
                self.risk_breakdown_table.setItem(row, 1, QTableWidgetItem(f"₹{position_value:,.0f}"))
                self.risk_breakdown_table.setItem(row, 2, QTableWidgetItem(f"{risk_contribution:.1f}%"))
                self.risk_breakdown_table.setItem(row, 3, QTableWidgetItem("--"))  # Beta would need market data
                self.risk_breakdown_table.setItem(row, 4, QTableWidgetItem(f"{position_volatility:.2f}%"))
                self.risk_breakdown_table.setItem(row, 5, QTableWidgetItem(f"₹{position_var:,.0f}"))

        except Exception as e:
            self.logger.error(f"Failed to update risk analysis: {e}")

    def refresh_watchlist_quotes(self):
        """Refresh watchlist quotes only"""
        try:
            watchlist = self.load_watchlist()
            if not watchlist:
                return

            # Get quotes for watchlist symbols
            instruments = [f"NSE:{symbol}" for symbol in watchlist]
            quotes_data = self.api_client.get_quote(instruments)

            # Update watchlist table with new quotes
            for row in range(self.watchlist_table.rowCount()):
                symbol_item = self.watchlist_table.item(row, 0)
                if symbol_item:
                    symbol = symbol_item.text()
                    instrument = f"NSE:{symbol}"

                    if instrument in quotes_data:
                        quote = quotes_data[instrument]
                        ltp = quote.get('last_price', 0)
                        ohlc = quote.get('ohlc', {})
                        prev_close = ohlc.get('close', ltp)
                        change = ltp - prev_close
                        change_pct = (change / prev_close * 100) if prev_close > 0 else 0

                        # Update only price-related columns
                        self.watchlist_table.setItem(row, 1, QTableWidgetItem(f"₹{ltp:.2f}"))

                        change_item = QTableWidgetItem(f"₹{change:+.2f}")
                        change_item.setForeground(QColor("green" if change >= 0 else "red"))
                        self.watchlist_table.setItem(row, 2, change_item)

                        change_pct_item = QTableWidgetItem(f"{change_pct:+.2f}%")
                        change_pct_item.setForeground(QColor("green" if change_pct >= 0 else "red"))
                        self.watchlist_table.setItem(row, 3, change_pct_item)

                        self.watchlist_table.setItem(row, 7, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))

        except Exception as e:
            self.logger.error(f"Failed to refresh watchlist quotes: {e}")
