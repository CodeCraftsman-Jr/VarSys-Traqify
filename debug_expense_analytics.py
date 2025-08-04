#!/usr/bin/env python3
"""
Debug script for expense analytics dashboard issues
"""

import sys
import os
import pandas as pd
from datetime import date, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_expense_data():
    """Debug expense data loading and filtering"""
    print("=== Debugging Expense Analytics Data ===")

    try:
        from core.data_manager import DataManager
        from modules.expenses.models import ExpenseDataModel

        # Initialize data manager
        data_manager = DataManager()

        # Initialize expense model
        expense_model = ExpenseDataModel(data_manager)

        # Get all expenses
        all_expenses = expense_model.get_all_expenses()
        print(f"Total records loaded: {len(all_expenses)}")

        if not all_expenses.empty:
            print(f"Columns: {list(all_expenses.columns)}")

            # Check record types
            if 'type' in all_expenses.columns:
                type_counts = all_expenses['type'].value_counts()
                print(f"Record types: {type_counts.to_dict()}")

                # Filter for expenses only
                expense_records = all_expenses[all_expenses['type'] == 'Expense']
                print(f"Expense records only: {len(expense_records)}")

                if not expense_records.empty:
                    print(f"Expense categories: {expense_records['category'].nunique()} unique categories")
                    print(f"Top 5 categories: {list(expense_records['category'].value_counts().head().index)}")

                    # Test date range filtering
                    today = date.today()
                    last_30_days = today - timedelta(days=30)

                    print(f"\nTesting date range filter: {last_30_days} to {today}")
                    recent_expenses = expense_model.get_expenses_by_date_range(last_30_days, today)
                    print(f"Recent expenses (last 30 days): {len(recent_expenses)}")

                    if recent_expenses.empty:
                        # Try last year
                        last_year = today - timedelta(days=365)
                        recent_year = expense_model.get_expenses_by_date_range(last_year, today)
                        print(f"Last year: {len(recent_year)} records")

                        if not recent_year.empty:
                            print("✓ Data available for last year")
                            # Test category grouping
                            category_totals = recent_year.groupby('category')['amount'].sum().sort_values(ascending=False)
                            print(f"Top 3 categories in last year:")
                            for cat, amount in category_totals.head(3).items():
                                print(f"  {cat}: ₹{amount:,.0f}")
                    else:
                        print("✓ Recent data available")
                        category_totals = recent_expenses.groupby('category')['amount'].sum().sort_values(ascending=False)
                        print(f"Top 3 categories in last 30 days:")
                        for cat, amount in category_totals.head(3).items():
                            print(f"  {cat}: ₹{amount:,.0f}")
            else:
                print("No 'type' column found in data")
        else:
            print("No data loaded - checking file existence...")
            file_path = data_manager.get_file_path('expenses', 'expenses.csv')
            print(f"File path: {file_path}")
            print(f"File exists: {file_path.exists()}")
            if file_path.exists():
                print(f"File size: {file_path.stat().st_size} bytes")

    except Exception as e:
        print(f"Error in debug_expense_data: {e}")
        import traceback
        traceback.print_exc()

def test_chart_dependencies():
    """Test if chart dependencies are available"""
    print("\n=== Testing Chart Dependencies ===")

    try:
        import plotly.graph_objects as go
        print("✓ Plotly available")
    except ImportError as e:
        print(f"✗ Plotly not available: {e}")

    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        print("✓ QWebEngineView available")
    except ImportError as e:
        print(f"✗ QWebEngineView not available: {e}")

    try:
        from modules.expenses.interactive_charts import (
            InteractivePieChartWidget,
            InteractiveTimeSeriesWidget,
            InteractiveBarChartWidget,
            InteractiveScatterPlotWidget,
            InteractiveHeatmapWidget
        )
        print("✓ Interactive chart widgets available")
    except ImportError as e:
        print(f"✗ Interactive chart widgets not available: {e}")
        import traceback
        traceback.print_exc()

def test_dashboard_creation():
    """Test dashboard creation"""
    print("\n=== Testing Dashboard Creation ===")

    try:
        from PySide6.QtWidgets import QApplication
        from core.data_manager import DataManager
        from modules.expenses.models import ExpenseDataModel
        from modules.expenses.analytics_dashboard import ExpenseAnalyticsDashboard
        from core.config import Config

        # Create minimal Qt application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # Initialize components
        data_manager = DataManager()
        expense_model = ExpenseDataModel(data_manager)
        config = Config()

        print("Creating ExpenseAnalyticsDashboard...")
        dashboard = ExpenseAnalyticsDashboard(expense_model, config)
        print("✓ Dashboard created successfully")

        # Test data refresh
        print("Testing data refresh...")
        dashboard.refresh_data()
        print("✓ Data refresh completed")

        return True

    except Exception as e:
        print(f"✗ Dashboard creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_expense_data()
    test_chart_dependencies()
    test_dashboard_creation()
