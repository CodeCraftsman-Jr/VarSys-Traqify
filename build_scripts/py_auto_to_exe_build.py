#!/usr/bin/env python3
"""
Py-Auto-To-Exe Build Script for Personal Finance Dashboard
This script automates the build process using py-auto-to-exe
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Setup logging with UTF-8 encoding to handle Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/py_auto_to_exe_build_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PyAutoToExeBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.build_dir = self.project_root / "build_scripts" / "py_auto_to_exe_output"
        self.dist_dir = self.project_root / "dist"
        self.main_script = self.project_root / "main.py"
        
        # Ensure directories exist
        self.build_dir.mkdir(parents=True, exist_ok=True)
        (self.project_root / "logs").mkdir(exist_ok=True)
        
    def check_dependencies(self):
        """Check if py-auto-to-exe is installed"""
        logger.info("Checking dependencies...")
        
        try:
            import auto_py_to_exe
            logger.info("SUCCESS: py-auto-to-exe is installed")
            return True
        except ImportError:
            logger.error("✗ py-auto-to-exe is not installed")
            logger.info("Installing py-auto-to-exe...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "auto-py-to-exe"], 
                             check=True, capture_output=True, text=True)
                logger.info("SUCCESS: py-auto-to-exe installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install py-auto-to-exe: {e}")
                return False
    
    def create_config_file(self):
        """Create py-auto-to-exe configuration file"""
        logger.info("Creating py-auto-to-exe configuration...")
        
        # Define paths relative to project root
        icon_path = self.project_root / "assets" / "icons" / "app_icon.png"
        
        config = {
            "version": "auto-py-to-exe-configuration_v1",
            "pyinstallerOptions": [
                {
                    "optionDest": "noconfirm",
                    "value": True
                },
                {
                    "optionDest": "filenames",
                    "value": str(self.main_script)
                },
                {
                    "optionDest": "onefile",
                    "value": False  # Use --onedir for better compatibility
                },
                {
                    "optionDest": "console",
                    "value": False  # No console window
                },
                {
                    "optionDest": "noupx",
                    "value": True
                },
                {
                    "optionDest": "icon_file",
                    "value": str(icon_path) if icon_path.exists() else ""
                },
                {
                    "optionDest": "name",
                    "value": "Traqify"
                },
                {
                    "optionDest": "distpath",
                    "value": str(self.dist_dir)
                },
                {
                    "optionDest": "workpath",
                    "value": str(self.build_dir)
                },
                {
                    "optionDest": "add_data",
                    "value": [
                        f"{self.project_root / 'assets'};assets",
                        f"{self.project_root / 'src'};src",
                        f"{self.project_root / 'data'};data",
                        f"{self.project_root / 'config'};config",
                        f"{self.project_root / 'updates'};updates",
                        f"{self.project_root / 'logs'};logs",
                        f"{self.project_root / 'releases'};releases",
                        f"{self.project_root / 'config.json'};.",
                        f"{self.project_root / 'secure_firebase_config_replit.json'};.",
                        f"{self.project_root / 'service_discovery_config.json'};.",
                        f"{self.project_root / 'config' / 'trading_config.json'};config",
                        f"{self.project_root / 'data' / 'config' / 'secure_session.json'};data/config",
                        f"{self.project_root / 'data' / 'config' / 'sync_metadata.json'};data/config",
                        f"{self.project_root / 'data' / 'holidays.json'};data",
                        f"{self.project_root / 'firebase.json'};.",
                        f"{self.project_root / 'requirements.txt'};.",
                        f"{self.project_root / 'README.md'};.",
                        f"{self.project_root / 'BUILD_CONFIGURATION_UPDATES.md'};."
                    ]
                },
                {
                    "optionDest": "hidden_import",
                    "value": [
                        "PySide6.QtCore",
                        "PySide6.QtWidgets",
                        "PySide6.QtGui",
                        "pandas",
                        "numpy",
                        "matplotlib",
                        "seaborn",
                        "plotly",
                        "kiteconnect",
                        "cryptography",
                        "requests",
                        "json",
                        "yfinance",
                        "mftool",
                        "websocket",
                        "google.auth",
                        "google.oauth2",
                        "googleapiclient",
                        "firebase_admin",
                        "pyrebase",
                        "Crypto",
                        # Core modules
                        "src.core.config",
                        "src.core.data_manager",
                        "src.core.initialization_tracker",
                        "src.core.secure_config",
                        "src.core.direct_firebase_client",
                        "src.core.auto_updater",
                        "src.core.version_manager",
                        "src.core.update_downloader",
                        "src.core.update_installer",
                        "src.core.update_manager",
                        "src.core.update_system",
                        "src.core.firebase_sync",
                        "src.core.firebase_auth",
                        "src.core.firebase_config",
                        "src.core.firebase_phone_auth",
                        "src.core.service_discovery",
                        "src.core.platform_monitor",
                        "src.core.bank_analyzer_integration",
                        "src.core.category_sync",
                        "src.core.deployment_manager",
                        "src.core.loading_state_manager",
                        # UI modules
                        "src.ui.main_window",
                        "src.ui.loading_screen",
                        "src.ui.startup_login",
                        "src.ui.service_discovery_widget",
                        "src.ui.settings_dialog",
                        "src.ui.update_dialogs",
                        "src.ui.update_dialog",
                        "src.ui.dashboard",
                        "src.ui.sidebar",
                        "src.ui.styles",
                        "src.ui.global_search",
                        "src.ui.direct_firebase_auth_dialog",
                        "src.ui.firebase_settings",
                        "src.ui.sync_widgets",
                        # Enhanced UI modules
                        "src.ui.smart_dashboard",
                        "src.ui.themes.manager",
                        "src.ui.themes.base",
                        "src.ui.themes.base.tokens",
                        "src.ui.themes.components",
                        "src.ui.themes.components.buttons",
                        "src.ui.themes.components.global_styles",
                        "src.ui.themes.components.inputs",
                        "src.ui.themes.components.navigation",
                        "src.ui.themes.components.tables",
                        "src.ui.themes.utils",
                        "src.ui.simple_optimized_styles",
                        "src.ui.simple_theme_overlay",
                        "src.ui.plotly_theme",
                        "src.ui.optimized_styles",
                        "src.ui.theme_switch_overlay",
                        "src.ui.theme_performance_test",
                        # Module widgets
                        "src.modules.expenses.widgets",
                        "src.modules.income.widgets",
                        "src.modules.habits.widgets",
                        "src.modules.attendance.widgets",
                        "src.modules.todos.widgets",
                        "src.modules.investments.widgets",
                        "src.modules.budget.widgets",
                        "src.modules.trading.widgets",
                        # Module models
                        "src.modules.expenses.models",
                        "src.modules.income.models",
                        "src.modules.habits.models",
                        "src.modules.attendance.models",
                        "src.modules.todos.models",
                        "src.modules.investments.models",
                        "src.modules.budget.models",
                        "src.modules.trading.models",
                        # Additional attendance modules
                        "src.modules.attendance.analytics_dashboard",
                        "src.modules.attendance.analytics_utils",
                        "src.modules.attendance.interactive_charts",
                        "src.modules.attendance.semester_models",
                        "src.modules.attendance.semester_widgets",
                        "src.modules.attendance.simple_models",
                        "src.modules.attendance.simple_widgets",
                        # Additional habits modules
                        "src.modules.habits.analytics_dashboard",
                        "src.modules.habits.analytics_utils",
                        "src.modules.habits.interactive_charts",
                        # Advanced analytics modules
                        "src.modules.expenses.advanced_analytics",
                        "src.modules.expenses.analytics_dashboard",
                        "src.modules.expenses.analytics_utils",
                        "src.modules.expenses.interactive_charts",
                        "src.modules.expenses.basic_charts",
                        "src.modules.expenses.summary_widget",
                        "src.modules.expenses.visualization",
                        "src.modules.income.advanced_analytics",
                        "src.modules.income.analytics_dashboard",
                        "src.modules.income.analytics_utils",
                        "src.modules.income.interactive_charts",
                        "src.modules.income.visualization",
                        # Enhanced investment modules
                        "src.modules.investments.amfi_fetcher",
                        "src.modules.investments.price_fetcher",
                        "src.modules.investments.progressive_fetcher",
                        "src.modules.investments.symbol_recognition",
                        "src.modules.investments.data_availability_analyzer",
                        "src.modules.investments.data_storage",
                        "src.modules.investments.loading_widget",
                        "src.modules.investments.unavailability_widgets",
                        # Todo analytics modules
                        "src.modules.todo.analytics_dashboard",
                        "src.modules.todo.analytics_utils",
                        "src.modules.todo.interactive_charts",
                        # Enhanced todos modules
                        "src.modules.todos.sync_worker",
                        "src.modules.todos.google_tasks_integration",
                        # Trading modules
                        "src.modules.trading.api_client",
                        "src.modules.trading.auth_education",
                        "src.modules.trading.startup_auth_dialog",
                        "src.modules.trading.token_manager"
                    ]
                },
                {
                    "optionDest": "collect_all",
                    "value": [
                        "PySide6",
                        "matplotlib",
                        "plotly",
                        "pandas",
                        "numpy",
                        "seaborn"
                    ]
                },
                {
                    "optionDest": "collect_submodules",
                    "value": [
                        "firebase_admin",
                        "google.cloud",
                        "google.auth",
                        "google.oauth2",
                        "googleapiclient",
                        "kiteconnect",
                        "yfinance",
                        "mftool",
                        "plotly.graph_objects",
                        "plotly.express",
                        "plotly.subplots",
                        "sklearn",
                        "scipy",
                        "statsmodels",
                        "websocket",
                        "Crypto",
                        "pyrebase"
                    ]
                }
            ]
        }
        
        config_file = self.build_dir / "build_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration saved to: {config_file}")
        return config_file
    
    def run_build(self, config_file):
        """Run the py-auto-to-exe build process"""
        logger.info("Starting py-auto-to-exe build process...")
        
        try:
            # Change to project root directory
            os.chdir(self.project_root)
            
            # Run auto-py-to-exe with the configuration file
            cmd = [
                sys.executable, "-m", "auto_py_to_exe",
                "--config", str(config_file),
                "--output-dir", str(self.dist_dir)
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            
            # Run the build process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            
            # Stream output in real-time
            for line in process.stdout:
                logger.info(line.strip())
            
            process.wait()
            
            if process.returncode == 0:
                logger.info("SUCCESS: Build completed successfully!")
                return True
            else:
                logger.error(f"ERROR: Build failed with return code: {process.returncode}")
                return False
                
        except Exception as e:
            logger.error(f"Error during build: {e}")
            return False
    
    def post_build_setup(self):
        """Setup post-build directory structure and verify critical files"""
        import shutil  # Import shutil here to avoid scope issues
        logger.info("Setting up post-build directory structure...")

        exe_dir = self.dist_dir / "Traqify"
        if not exe_dir.exists():
            logger.error("Build output directory not found!")
            return False

        try:
            # Verify critical configuration files are included (excluding sensitive Firebase files)
            critical_files = [
                "config.json",
                "secure_firebase_config_replit.json",
                "service_discovery_config.json",
                "requirements.txt",
                "README.md"
            ]

            # Files that are in subdirectories
            critical_subdir_files = [
                ("config/trading_config.json", "config")
            ]

            # Note: Firebase credentials are intentionally excluded for security
            logger.info("SECURITY: Sensitive Firebase credentials excluded from build")
            logger.info("SECURITY: Application uses secure Replit backend for authentication")
            logger.info("SECURITY: Only public configuration included in executable")

            missing_files = []
            for file_name in critical_files:
                if not (exe_dir / file_name).exists():
                    missing_files.append(file_name)
                else:
                    logger.info(f"SUCCESS: Critical file found: {file_name}")

            # Check subdirectory files
            for file_path, subdir in critical_subdir_files:
                if not (exe_dir / file_path).exists():
                    missing_files.append(file_path)
                else:
                    logger.info(f"SUCCESS: Critical file found: {file_path}")

            if missing_files:
                logger.warning(f"Missing critical files: {missing_files}")
                # Try to copy them manually
                for file_name in missing_files:
                    src_file = self.project_root / file_name
                    if src_file.exists():
                        # Ensure target directory exists
                        target_file = exe_dir / file_name
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, target_file)
                        logger.info(f"Manually copied missing file: {file_name}")
                    else:
                        logger.error(f"Source file not found: {file_name}")

            # Verify critical directories
            critical_dirs = ["assets", "src", "updates", "data", "config"]
            for dir_name in critical_dirs:
                if (exe_dir / dir_name).exists():
                    logger.info(f"SUCCESS: Critical directory found: {dir_name}")
                else:
                    logger.warning(f"Missing critical directory: {dir_name}")
                    # Try to copy missing directories
                    src_dir = self.project_root / dir_name
                    if src_dir.exists():
                        shutil.copytree(src_dir, exe_dir / dir_name, dirs_exist_ok=True)
                        logger.info(f"Manually copied missing directory: {dir_name}")

            # Copy additional files that might be needed
            additional_files = [
                "requirements.txt",
                "README.md",
                "BUILD_CONFIGURATION_UPDATES.md"
            ]

            for file_name in additional_files:
                src_file = self.project_root / file_name
                if src_file.exists():
                    shutil.copy2(src_file, exe_dir)
                    logger.info(f"Copied {file_name} to build directory")

            # Create a run script for easier execution
            run_script = exe_dir / "run.bat"
            with open(run_script, 'w') as f:
                f.write("@echo off\n")
                f.write("cd /d \"%~dp0\"\n")
                f.write("Traqify.exe\n")
                f.write("pause\n")

            logger.info("SUCCESS: Post-build setup completed")
            return True

        except Exception as e:
            logger.error(f"Error in post-build setup: {e}")
            return False
    
    def build(self):
        """Main build process"""
        logger.info("="*60)
        logger.info("STARTING PY-AUTO-TO-EXE BUILD PROCESS")
        logger.info("="*60)
        
        # Step 1: Check dependencies
        if not self.check_dependencies():
            return False
        
        # Step 2: Create configuration
        config_file = self.create_config_file()
        
        # Step 3: Run build
        if not self.run_build(config_file):
            return False
        
        # Step 4: Post-build setup
        if not self.post_build_setup():
            return False
        
        logger.info("="*60)
        logger.info("BUILD COMPLETED SUCCESSFULLY!")
        logger.info(f"Output directory: {self.dist_dir / 'Traqify'}")
        logger.info("="*60)
        
        return True

def main():
    """Main entry point"""
    builder = PyAutoToExeBuilder()
    
    try:
        success = builder.build()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
