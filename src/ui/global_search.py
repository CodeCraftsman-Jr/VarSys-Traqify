"""
Global Search Dialog
Provides search functionality across all modules
"""

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QComboBox, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QIcon

import pandas as pd
from typing import Dict, List, Any, Optional


class SearchWorker(QThread):
    """Worker thread for performing search operations"""
    
    search_completed = Signal(list)  # Emits search results
    
    def __init__(self, data_manager, search_term: str, search_modules: List[str]):
        super().__init__()
        self.data_manager = data_manager
        self.search_term = search_term.lower()
        self.search_modules = search_modules
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def run(self):
        """Perform the search operation"""
        try:
            results = []
            
            for module in self.search_modules:
                module_results = self.search_in_module(module)
                results.extend(module_results)
            
            self.search_completed.emit(results)
            
        except Exception as e:
            self.logger.error(f"Error in search worker: {e}")
            self.search_completed.emit([])
    
    def search_in_module(self, module: str) -> List[Dict[str, Any]]:
        """Search within a specific module"""
        results = []
        
        try:
            if module == "expenses":
                df = self.data_manager.read_csv('expenses', 'expenses.csv', 
                                              ['id', 'amount', 'category', 'description', 'date'])
                for _, row in df.iterrows():
                    if (self.search_term in str(row['description']).lower() or 
                        self.search_term in str(row['category']).lower()):
                        results.append({
                            'module': 'Expenses',
                            'type': 'Expense',
                            'title': row['description'],
                            'details': f"₹{row['amount']:.2f} - {row['category']}",
                            'date': row['date'],
                            'id': row['id']
                        })
            
            elif module == "income":
                df = self.data_manager.read_csv('income', 'income_records.csv',
                                              ['id', 'amount', 'source', 'description', 'date'])
                for _, row in df.iterrows():
                    if (self.search_term in str(row['description']).lower() or 
                        self.search_term in str(row['source']).lower()):
                        results.append({
                            'module': 'Income',
                            'type': 'Income',
                            'title': row['description'],
                            'details': f"₹{row['amount']:.2f} - {row['source']}",
                            'date': row['date'],
                            'id': row['id']
                        })
            
            elif module == "todos":
                df = self.data_manager.read_csv('todos', 'todo_items.csv',
                                              ['id', 'title', 'description', 'status', 'priority'])
                for _, row in df.iterrows():
                    if (self.search_term in str(row['title']).lower() or 
                        self.search_term in str(row['description']).lower()):
                        results.append({
                            'module': 'To-Do',
                            'type': 'Task',
                            'title': row['title'],
                            'details': f"{row['status']} - {row['priority']} Priority",
                            'date': '',
                            'id': row['id']
                        })
            
            elif module == "investments":
                df = self.data_manager.read_csv('investments', 'investments.csv',
                                              ['id', 'symbol', 'name', 'current_value', 'profit_loss'])
                for _, row in df.iterrows():
                    if (self.search_term in str(row['symbol']).lower() or 
                        self.search_term in str(row['name']).lower()):
                        results.append({
                            'module': 'Investments',
                            'type': 'Investment',
                            'title': f"{row['symbol']} - {row['name']}",
                            'details': f"₹{row['current_value']:.2f} (P&L: ₹{row['profit_loss']:.2f})",
                            'date': '',
                            'id': row['id']
                        })
            
            elif module == "habits":
                df = self.data_manager.read_csv('habits', 'habit_records.csv',
                                              ['id', 'habit_name', 'is_completed', 'date'])
                for _, row in df.iterrows():
                    if self.search_term in str(row['habit_name']).lower():
                        status = "✅ Completed" if row['is_completed'] else "⏳ Pending"
                        results.append({
                            'module': 'Habits',
                            'type': 'Habit',
                            'title': row['habit_name'],
                            'details': status,
                            'date': row['date'],
                            'id': row['id']
                        })
            
            elif module == "budget":
                df = self.data_manager.read_csv('budget', 'budget_plans.csv',
                                              ['id', 'name', 'budget_type', 'budget_health_score'])
                for _, row in df.iterrows():
                    if self.search_term in str(row['name']).lower():
                        results.append({
                            'module': 'Budget',
                            'type': 'Budget Plan',
                            'title': row['name'],
                            'details': f"{row['budget_type']} - Health: {row['budget_health_score']:.1f}%",
                            'date': '',
                            'id': row['id']
                        })
            
        except Exception as e:
            self.logger.error(f"Error searching in module {module}: {e}")
        
        return results


class GlobalSearchDialog(QDialog):
    """Global search dialog for searching across all modules"""
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.search_worker = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the search dialog UI"""
        self.setWindowTitle("Global Search")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Search header
        header_layout = QHBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search across all modules...")
        self.search_input.setFont(QFont("Arial", 12))
        header_layout.addWidget(self.search_input)
        
        # Module filter
        self.module_filter = QComboBox()
        self.module_filter.addItems([
            "All Modules", "Expenses", "Income", "To-Do", 
            "Investments", "Habits", "Budget"
        ])
        header_layout.addWidget(self.module_filter)
        
        # Search button
        self.search_button = QPushButton("🔍 Search")
        self.search_button.clicked.connect(self.perform_search)
        header_layout.addWidget(self.search_button)
        
        layout.addLayout(header_layout)
        
        # Results info
        self.results_label = QLabel("Enter search term and click Search")
        self.results_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.results_label)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Module", "Type", "Title", "Details", "Date"
        ])
        
        # Table settings
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
        
        # Resize columns
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.results_table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.open_button = QPushButton("Open Module")
        self.open_button.clicked.connect(self.open_selected_module)
        self.open_button.setEnabled(False)
        button_layout.addWidget(self.open_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.search_input.returnPressed.connect(self.perform_search)
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def perform_search(self):
        """Perform the search operation"""
        search_term = self.search_input.text().strip()
        
        if not search_term:
            QMessageBox.warning(self, "Search", "Please enter a search term")
            return
        
        if len(search_term) < 2:
            QMessageBox.warning(self, "Search", "Search term must be at least 2 characters")
            return
        
        # Determine which modules to search
        module_filter = self.module_filter.currentText()
        if module_filter == "All Modules":
            search_modules = ["expenses", "income", "todos", "investments", "habits", "budget"]
        else:
            module_map = {
                "Expenses": "expenses",
                "Income": "income", 
                "To-Do": "todos",
                "Investments": "investments",
                "Habits": "habits",
                "Budget": "budget"
            }
            search_modules = [module_map[module_filter]]
        
        # Update UI
        self.search_button.setEnabled(False)
        self.search_button.setText("🔍 Searching...")
        self.results_label.setText("Searching...")
        
        # Start search worker
        self.search_worker = SearchWorker(self.data_manager, search_term, search_modules)
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.start()
    
    def on_search_completed(self, results: List[Dict[str, Any]]):
        """Handle search completion"""
        # Update UI
        self.search_button.setEnabled(True)
        self.search_button.setText("🔍 Search")
        
        # Update results
        self.update_results_table(results)
        
        # Update results label
        if results:
            self.results_label.setText(f"Found {len(results)} result(s)")
        else:
            self.results_label.setText("No results found")
    
    def update_results_table(self, results: List[Dict[str, Any]]):
        """Update the results table"""
        self.results_table.setRowCount(len(results))
        
        for row_idx, result in enumerate(results):
            # Module
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(result['module']))
            
            # Type
            self.results_table.setItem(row_idx, 1, QTableWidgetItem(result['type']))
            
            # Title
            self.results_table.setItem(row_idx, 2, QTableWidgetItem(result['title']))
            
            # Details
            self.results_table.setItem(row_idx, 3, QTableWidgetItem(result['details']))
            
            # Date
            self.results_table.setItem(row_idx, 4, QTableWidgetItem(result['date']))
            
            # Store full result data
            self.results_table.item(row_idx, 0).setData(Qt.UserRole, result)
    
    def on_selection_changed(self):
        """Handle selection change"""
        self.open_button.setEnabled(self.results_table.currentRow() >= 0)
    
    def open_selected_module(self):
        """Open the module containing the selected result"""
        current_row = self.results_table.currentRow()
        if current_row >= 0:
            item = self.results_table.item(current_row, 0)
            if item:
                result = item.data(Qt.UserRole)
                if result:
                    module_name = result['module'].lower()
                    # Emit signal to parent to switch to module
                    # This would be connected to the main window's module switching
                    QMessageBox.information(
                        self, "Open Module",
                        f"Would open {result['module']} module and highlight item:\n{result['title']}"
                    )
