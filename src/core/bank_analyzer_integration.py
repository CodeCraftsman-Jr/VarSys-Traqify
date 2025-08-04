"""
Bank Statement Analyzer Integration Module
Handles launching and integrating with the V2 bank statement analyzer
"""

import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, List
from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import QProcess, QObject, Signal


class BankAnalyzerLauncher(QObject):
    """
    Handles launching the bank statement analyzer as a separate process
    while maintaining proper integration with the main application
    """
    
    # Signals
    analyzer_started = Signal()
    analyzer_finished = Signal(int)  # exit code
    analyzer_error = Signal(str)  # error message
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.parent_widget = parent
        self.process = None
        
        # Determine paths - handle both packaged and script execution
        if getattr(sys, 'frozen', False):
            # Running as packaged executable
            self.main_app_dir = Path(sys.executable).parent
        else:
            # Running as script
            self.main_app_dir = Path(__file__).parent.parent.parent
        self.bank_analyzer_dir = self.main_app_dir / "bank_statement_analyzer"
        self.bank_analyzer_script = self.bank_analyzer_dir / "bank_statement_analyzer.py"
        self.launch_script = self.bank_analyzer_dir / "launch_bank_analyzer.py"

        self.logger.debug(f"Main app dir: {self.main_app_dir}")
        self.logger.debug(f"Bank analyzer dir: {self.bank_analyzer_dir}")
        self.logger.debug(f"Bank analyzer script: {self.bank_analyzer_script}")
    
    def check_analyzer_availability(self) -> Tuple[bool, str]:
        """
        Check if the bank statement analyzer is available and can be launched
        
        Returns:
            Tuple[bool, str]: (is_available, message)
        """
        try:
            # Check if bank analyzer directory exists
            if not self.bank_analyzer_dir.exists():
                return False, f"Bank analyzer directory not found at: {self.bank_analyzer_dir}"
            
            # Check if bank analyzer script exists
            if not self.bank_analyzer_script.exists():
                return False, f"Bank analyzer script not found at: {self.bank_analyzer_script}"
            
            # Check if Python is available
            try:
                result = subprocess.run([sys.executable, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    return False, "Python interpreter not available"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False, "Python interpreter not accessible"
            
            # Check basic imports (quick test)
            test_script = '''
import sys
sys.path.insert(0, r"{}")
try:
    from bank_analyzer.ui.main_window import BankAnalyzerMainWindow
    print("OK")
except Exception as e:
    print(f"ERROR: {{e}}")
'''.format(str(self.bank_analyzer_dir))
            
            try:
                result = subprocess.run([sys.executable, "-c", test_script],
                                      capture_output=True, text=True, timeout=10,
                                      cwd=str(self.bank_analyzer_dir))
                
                if result.returncode == 0 and "OK" in result.stdout:
                    return True, "Bank Statement Analyzer is ready to launch"
                else:
                    error_msg = result.stderr or result.stdout or "Unknown import error"
                    return False, f"Bank analyzer dependencies not available: {error_msg}"
                    
            except subprocess.TimeoutExpired:
                return False, "Timeout checking bank analyzer dependencies"
            except Exception as e:
                return False, f"Error checking dependencies: {str(e)}"
                
        except Exception as e:
            self.logger.error(f"Error checking analyzer availability: {e}")
            return False, f"Error checking availability: {str(e)}"
    
    def launch_analyzer(self, use_launcher: bool = True) -> bool:
        """
        Launch the bank statement analyzer

        Args:
            use_launcher: If True, use the launch script; if False, launch directly

        Returns:
            bool: True if launch was initiated successfully
        """
        try:
            # Check availability first
            is_available, message = self.check_analyzer_availability()
            if not is_available:
                self.show_error("Bank Analyzer Not Available", message)
                return False

            # Determine which script to use
            script_to_run = self.launch_script if use_launcher and self.launch_script.exists() else self.bank_analyzer_script

            self.logger.info(f"Launching bank analyzer: {script_to_run}")

            # Check if already running
            if self.process is not None and self.process.state() != QProcess.NotRunning:
                self.show_info("Bank Analyzer Already Running",
                             "The Bank Statement Analyzer is already running. Please check your taskbar or close the existing instance first.")
                return False

            # Try using subprocess.Popen for better window visibility
            try:
                import subprocess

                # Launch with subprocess for better window handling
                self.subprocess_process = subprocess.Popen(
                    [sys.executable, str(script_to_run)],
                    cwd=str(self.bank_analyzer_dir),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                )

                self.logger.info(f"Bank analyzer launched with PID: {self.subprocess_process.pid}")
                self.analyzer_started.emit()
                return True

            except Exception as subprocess_error:
                self.logger.warning(f"Subprocess launch failed: {subprocess_error}, trying QProcess...")

                # Fallback to QProcess
                self.process = QProcess(self)
                self.process.finished.connect(self.on_process_finished)
                self.process.errorOccurred.connect(self.on_process_error)
                self.process.started.connect(self.on_process_started)

                # Set working directory to bank analyzer folder
                self.process.setWorkingDirectory(str(self.bank_analyzer_dir))

                # Launch the process with detached mode for better window visibility
                success = self.process.startDetached(sys.executable, [str(script_to_run)], str(self.bank_analyzer_dir))

                if success:
                    self.logger.info("Bank analyzer launched in detached mode")
                    self.analyzer_started.emit()
                    return True
                else:
                    # Try regular start as last resort
                    self.process.start(sys.executable, [str(script_to_run)])

                    # Wait a moment to see if it starts successfully
                    if not self.process.waitForStarted(5000):  # 5 second timeout
                        error_msg = self.process.errorString()
                        self.show_error("Launch Failed", f"Failed to start Bank Statement Analyzer: {error_msg}")
                        return False

                    return True

        except Exception as e:
            self.logger.error(f"Error launching bank analyzer: {e}")
            self.show_error("Launch Error", f"An error occurred while launching the Bank Statement Analyzer: {str(e)}")
            return False
    
    def on_process_started(self):
        """Handle process started"""
        self.logger.info("Bank analyzer process started successfully")
        self.analyzer_started.emit()
    
    def on_process_finished(self, exit_code: int):
        """Handle process finished"""
        self.logger.info(f"Bank analyzer process finished with exit code: {exit_code}")
        self.analyzer_finished.emit(exit_code)
        
        if exit_code != 0:
            self.logger.warning(f"Bank analyzer exited with non-zero code: {exit_code}")
    
    def on_process_error(self, error):
        """Handle process error"""
        error_msg = f"Bank analyzer process error: {error}"
        self.logger.error(error_msg)
        self.analyzer_error.emit(error_msg)
    
    def is_running(self) -> bool:
        """Check if the bank analyzer is currently running"""
        return self.process is not None and self.process.state() == QProcess.Running
    
    def terminate_analyzer(self):
        """Terminate the bank analyzer process if running"""
        if self.is_running():
            self.logger.info("Terminating bank analyzer process")
            self.process.terminate()
            if not self.process.waitForFinished(5000):
                self.process.kill()
    
    def show_error(self, title: str, message: str):
        """Show error message to user"""
        if self.parent_widget:
            QMessageBox.critical(self.parent_widget, title, message)
        else:
            self.logger.error(f"{title}: {message}")
    
    def show_info(self, title: str, message: str):
        """Show info message to user"""
        if self.parent_widget:
            QMessageBox.information(self.parent_widget, title, message)
        else:
            self.logger.info(f"{title}: {message}")
    
    def show_warning(self, title: str, message: str):
        """Show warning message to user"""
        if self.parent_widget:
            QMessageBox.warning(self.parent_widget, title, message)
        else:
            self.logger.warning(f"{title}: {message}")


def create_launcher(parent: Optional[QWidget] = None) -> BankAnalyzerLauncher:
    """
    Factory function to create a bank analyzer launcher
    
    Args:
        parent: Parent widget for dialogs
        
    Returns:
        BankAnalyzerLauncher: Configured launcher instance
    """
    return BankAnalyzerLauncher(parent)


def quick_launch_analyzer(parent: Optional[QWidget] = None) -> bool:
    """
    Quick function to launch the bank analyzer with minimal setup

    Args:
        parent: Parent widget for dialogs

    Returns:
        bool: True if launch was successful
    """
    launcher = create_launcher(parent)
    return launcher.launch_analyzer()


class WorkflowHelper:
    """Helper class for managing the complete bank analyzer workflow"""

    def __init__(self, parent: Optional[QWidget] = None):
        self.parent = parent
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Determine paths - handle both packaged and script execution
        if getattr(sys, 'frozen', False):
            # Running as packaged executable
            self.main_app_dir = Path(sys.executable).parent
        else:
            # Running as script
            self.main_app_dir = Path(__file__).parent.parent.parent
        self.bank_analyzer_dir = self.main_app_dir / "bank_statement_analyzer"
        self.exports_dir = self.bank_analyzer_dir / "data" / "exports"

    def check_for_new_exports(self) -> List[Path]:
        """
        Check for new export files from the bank analyzer

        Returns:
            List of new export file paths
        """
        try:
            if not self.exports_dir.exists():
                return []

            # Look for main app format exports
            export_files = list(self.exports_dir.glob("*_main_app_format.csv"))

            # Filter for recent files (last 24 hours)
            from datetime import datetime, timedelta
            recent_files = []
            cutoff_time = datetime.now() - timedelta(hours=24)

            for file_path in export_files:
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time > cutoff_time:
                        recent_files.append(file_path)
                except:
                    continue

            return recent_files

        except Exception as e:
            self.logger.error(f"Error checking for exports: {e}")
            return []

    def suggest_import(self, expense_tracker_widget) -> bool:
        """
        Check for new exports and suggest import to the user

        Args:
            expense_tracker_widget: The expense tracker widget to import into

        Returns:
            bool: True if import was suggested and accepted
        """
        try:
            new_exports = self.check_for_new_exports()

            if not new_exports:
                return False

            # Show suggestion dialog
            from PySide6.QtWidgets import QMessageBox

            if len(new_exports) == 1:
                message = f"A new export from the Bank Statement Analyzer was found:\n\n{new_exports[0].name}\n\nWould you like to import these transactions?"
            else:
                message = f"{len(new_exports)} new exports from the Bank Statement Analyzer were found.\n\nWould you like to import the most recent one?"

            reply = QMessageBox.question(
                self.parent,
                "Import Bank Analyzer Data",
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                # Import the most recent file
                most_recent = max(new_exports, key=lambda p: p.stat().st_mtime)
                return self.auto_import_file(most_recent, expense_tracker_widget)

            return False

        except Exception as e:
            self.logger.error(f"Error suggesting import: {e}")
            return False

    def auto_import_file(self, file_path: Path, expense_tracker_widget) -> bool:
        """
        Automatically import a file into the expense tracker

        Args:
            file_path: Path to the export file
            expense_tracker_widget: The expense tracker widget

        Returns:
            bool: True if import was successful
        """
        try:
            import pandas as pd

            # Read the file
            df = pd.read_csv(file_path)

            # Validate format
            required_columns = ['date', 'type', 'category', 'sub_category', 'transaction_mode', 'amount', 'notes']
            if not all(col in df.columns for col in required_columns):
                self.logger.error(f"Invalid file format: {file_path}")
                return False

            # Import transactions with proper timestamp handling
            from datetime import datetime
            import_timestamp = datetime.now()
            success_count = 0

            for _, row in df.iterrows():
                try:
                    from ..modules.expenses.models import ExpenseRecord

                    expense = ExpenseRecord(
                        date=row['date'],  # Bank statement date
                        type=row['type'],  # Expense/Income based on Debit/Credit
                        category=row['category'],  # From bank analyzer categorization
                        sub_category=row['sub_category'],  # From bank analyzer categorization
                        transaction_mode=row['transaction_mode'],  # Inferred from bank description
                        amount=float(row['amount']),  # Transaction amount
                        notes=row['notes'],  # Original bank statement description
                        created_at=import_timestamp,  # Import date (when first added)
                        updated_at=import_timestamp   # Import date initially, will change on manual edits
                    )

                    if expense_tracker_widget.expense_model.add_expense(expense):
                        success_count += 1

                except Exception as e:
                    self.logger.error(f"Error importing row: {e}")
                    continue

            if success_count > 0:
                expense_tracker_widget.refresh_data()
                expense_tracker_widget.show_status_message(f"📥 Auto-imported {success_count} transactions from Bank Analyzer")

                # Show success message
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.parent,
                    "Import Successful",
                    f"Successfully imported {success_count} transactions from the Bank Statement Analyzer."
                )
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error auto-importing file: {e}")
            return False


def create_workflow_helper(parent: Optional[QWidget] = None) -> WorkflowHelper:
    """
    Factory function to create a workflow helper

    Args:
        parent: Parent widget for dialogs

    Returns:
        WorkflowHelper: Configured workflow helper instance
    """
    return WorkflowHelper(parent)
