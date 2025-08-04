#!/usr/bin/env python3
"""
Personal Finance Dashboard - Desktop Application
A comprehensive PySide6-based personal finance management application
"""

import sys
import os
import traceback
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from PySide6.QtGui import QIcon, QFont

# Fix Google Cloud authentication issues in standalone executable
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''
os.environ['GCLOUD_PROJECT'] = ''

def get_app_directory():
    """Get the application directory, handling both packaged and script execution"""
    if getattr(sys, 'frozen', False):
        # Running as packaged executable
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent

# Set up comprehensive logging
app_dir = get_app_directory()
logs_dir = app_dir / "logs"
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'app_debug.log', mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific logger levels
logging.getLogger('PySide6').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.ERROR)
logging.getLogger('google.auth').setLevel(logging.ERROR)
logging.getLogger('google.cloud').setLevel(logging.ERROR)
logging.getLogger('firebase_admin').setLevel(logging.ERROR)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('modules.attendance.simple_widgets').setLevel(logging.INFO)  # Change from DEBUG to INFO
logging.getLogger('modules.expenses').setLevel(logging.WARNING)  # Reduce expense tracker debug output
logging.getLogger('src.ui.loading_screen').setLevel(logging.INFO)  # Reduce loading screen debug output

logger = logging.getLogger(__name__)
logger.info("="*80)
logger.info("PERSONAL FINANCE DASHBOARD - DETAILED LOGGING SESSION")
logger.info("="*80)

# Add the src directory to the Python path
app_dir = get_app_directory()
src_path = app_dir / 'src'
if src_path.exists():
    sys.path.insert(0, str(src_path))

from src.ui.main_window import MainWindow
from src.core.config import AppConfig
from src.core.data_manager import DataManager
from src.ui.loading_screen import LoadingScreen


def setup_application():
    """Setup the QApplication with proper configuration"""
    app = QApplication(sys.argv)

    # CRITICAL FIX: Force Qt to use a style that respects application stylesheets
    # On Windows, the default "windowsvista" style overrides application stylesheets
    # We need to use a style that properly inherits from application-level styling
    from PySide6.QtWidgets import QStyleFactory

    logger.info(f"Available Qt styles: {QStyleFactory.keys()}")
    logger.info(f"Current Qt style: {app.style().objectName()}")

    # Try to set a style that respects application stylesheets
    # Fusion style is known to work well with custom stylesheets
    available_styles = QStyleFactory.keys()
    preferred_styles = ["Fusion", "Windows", "windowsvista"]

    for style_name in preferred_styles:
        if style_name in available_styles:
            try:
                style = QStyleFactory.create(style_name)
                if style:
                    app.setStyle(style)
                    logger.info(f"Successfully set Qt style to: {style_name}")
                    break
            except Exception as e:
                logger.warning(f"Failed to set style {style_name}: {e}")

    logger.info(f"Final Qt style: {app.style().objectName()}")

    # Set application properties
    app.setApplicationName("Personal Finance Dashboard")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Personal Finance")
    app.setOrganizationDomain("personalfinance.local")

    # Set application icon
    app_dir = get_app_directory()
    icon_path = app_dir / "assets" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Set default font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # Enable high DPI scaling (Qt 6 handles this automatically)
    # These attributes are deprecated in Qt 6
    # app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    # app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    return app


def initialize_config():
    """Initialize application configuration"""
    logger.info("Initializing configuration...")
    config = AppConfig.load_from_file()

    # Auto-detect correct data directory by checking where actual data exists
    current_dir = os.getcwd()
    logger.info(f"Current working directory: {current_dir}")

    # List of possible data directory locations to check
    possible_data_dirs = [
        "EXE/data",           # From repository root
        "data",               # From EXE directory or repository root
        "../data",            # From subdirectory
        "EXE\\data",          # Windows path from repository root
        config.data_directory # Original config value
    ]

    # Find the data directory that actually contains attendance data
    data_dir = None
    for candidate_dir in possible_data_dirs:
        test_file = os.path.join(candidate_dir, "attendance", "attendance_records.csv")
        if os.path.exists(test_file):
            # Check if this file has substantial data (more than just headers)
            try:
                with open(test_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 10:  # More than just headers + a few records
                        data_dir = candidate_dir
                        logger.info(f"Found data directory with {len(lines)-1} attendance records: {data_dir}")
                        break
                    else:
                        logger.debug(f"Data directory {candidate_dir} has only {len(lines)-1} records, continuing search...")
            except Exception as e:
                logger.debug(f"Error checking {test_file}: {e}")
                continue

    # If no substantial data found, use the first existing directory
    if data_dir is None:
        for candidate_dir in possible_data_dirs:
            if os.path.exists(candidate_dir):
                data_dir = candidate_dir
                logger.warning(f"Using first available data directory (no substantial data found): {data_dir}")
                break

    # Final fallback
    if data_dir is None:
        data_dir = config.data_directory
        logger.warning(f"No data directories found, using config default: {data_dir}")

    # Override the data directory
    config.data_directory = data_dir
    logger.info(f"Config loaded: data_directory={config.data_directory}")
    return config


def initialize_data_manager(config):
    """Initialize data manager"""
    logger.info("Initializing data manager...")
    data_manager = DataManager(config.data_directory)
    logger.info("Data manager initialized successfully")
    return data_manager


def create_main_window(data_manager, config, progress_callback=None):
    """Create main window with detailed progress tracking"""
    logger.info("Creating main window...")

    def update_progress(progress, message, detail="", step_detail=""):
        """Internal progress update function"""
        if progress_callback:
            progress_callback(progress, message, detail, step_detail)
        logger.debug(f"Main window creation progress: {progress}% - {message}")

    # Start main window creation process
    update_progress(42, "Creating main window...", "Initializing user interface framework")

    # Create main window (this is the heavy operation)
    # Hide the main window initially to prevent it from stealing focus
    update_progress(45, "Building main window...", "Setting up application window and core systems")
    main_window = MainWindow(data_manager, config, progress_callback=update_progress)
    main_window.hide()  # Keep it hidden until loading is complete

    update_progress(90, "User interface created", "All application modules and interface components loaded")
    logger.info("Main window created successfully")
    return main_window


def require_secure_authentication(loading_screen=None):
    """Require authentication before starting the application"""
    logger.info("Checking authentication requirement...")

    try:
        # Temporarily hide loading screen during authentication to prevent z-index issues
        if loading_screen and loading_screen.isVisible():
            logger.info("Temporarily hiding loading screen for authentication dialog")
            loading_screen.hide()

        # Check if direct Firebase is configured
        from src.core.secure_config import get_secure_config
        config = get_secure_config()

        if config.backend_type == "direct_firebase":
            result = require_direct_firebase_authentication()
        else:
            result = require_backend_authentication()

        # Restore loading screen after authentication
        if loading_screen:
            logger.info("Restoring loading screen after authentication")
            loading_screen.show()
            loading_screen.raise_()
            loading_screen.activateWindow()

        return result

    except Exception as e:
        logger.error(f"Error during authentication: {e}")

        # Restore loading screen even on error
        if loading_screen:
            loading_screen.show()

        QMessageBox.critical(
            None, "Authentication Error",
            f"An error occurred during authentication:\n\n{e}"
        )
        return False


def require_direct_firebase_authentication():
    """Require direct Firebase authentication"""
    logger.info("Using direct Firebase authentication...")

    try:
        from src.core.direct_firebase_client import get_direct_firebase_client
        from src.ui.direct_firebase_auth_dialog import show_direct_firebase_auth_dialog

        # Get direct Firebase client
        firebase_client = get_direct_firebase_client()

        # Check if already authenticated
        if firebase_client.is_authenticated():
            logger.info("User already authenticated with direct Firebase, proceeding...")
            return True

        # Show direct Firebase authentication dialog
        logger.info("Showing direct Firebase authentication dialog...")
        success = show_direct_firebase_auth_dialog()

        if success:
            logger.info("Direct Firebase authentication successful")
            return True
        else:
            logger.info("Direct Firebase authentication cancelled or failed")
            return False

    except ImportError as e:
        logger.error(f"Direct Firebase authentication not available: {e}")
        QMessageBox.critical(
            None, "Authentication Required",
            "Direct Firebase authentication is required but not available.\n"
            "Please ensure the Firebase modules are installed."
        )
        return False


def require_backend_authentication():
    """Require backend authentication (original method)"""
    logger.info("Using backend authentication...")

    try:
        from src.ui.startup_login import StartupLoginDialog
        from src.core.direct_firebase_client import get_direct_firebase_client

        # Get direct Firebase client (this will auto-load session if available)
        firebase_client = get_direct_firebase_client()
        logger.info("Checking authentication status...")

        # Check if user is authenticated (session should be loaded during client initialization)
        if firebase_client.is_authenticated():
            user_email = firebase_client.current_user.get('email', 'Unknown') if firebase_client.current_user else 'Unknown'
            logger.info(f"✅ User already authenticated: {user_email}")
            return True
        else:
            logger.info("No valid session found, requiring authentication")

        # Show Firebase authentication dialog
        logger.info("Showing Firebase authentication dialog...")
        login_dialog = StartupLoginDialog()

        # Show dialog and wait for authentication
        result = login_dialog.exec()

        if result == QDialog.Accepted and firebase_client.is_authenticated():
            logger.info(f"Authentication successful")
            return True
        elif result == QDialog.Rejected:
            logger.info("Authentication cancelled by user - exiting application")
            # User explicitly chose to exit
            return False
        else:
            logger.info("Authentication failed")
            return False

    except ImportError as e:
        logger.error(f"Firebase authentication not available: {e}")
        QMessageBox.critical(
            None, "Authentication Required",
            "Secure authentication is required but not available.\n"
            "Please ensure the secure authentication modules are installed."
        )
        return False


def main():
    """Main application entry point with authentication-first flow"""
    app = None
    loading_screen = None

    try:
        logger.info("Starting Personal Finance Dashboard...")

        # Create application first
        logger.info("Setting up QApplication...")
        app = setup_application()

        # STEP 1: Handle authentication FIRST, before showing loading screen
        logger.info("Performing authentication check...")

        # Always use direct Firebase authentication
        from src.core.direct_firebase_client import get_direct_firebase_client
        firebase_client = get_direct_firebase_client()

        user_authenticated = firebase_client.is_authenticated()

        if user_authenticated:
            # User already authenticated via saved session
            user_email = firebase_client.current_user.get('email', 'Unknown') if firebase_client.current_user else 'Unknown'
            logger.info(f"✅ User already authenticated via saved session: {user_email}")
        else:
            # No saved session, require authentication before showing loading screen
            logger.info("No saved session found, requiring authentication...")

            # Perform authentication WITHOUT loading screen interference
            auth_success = require_secure_authentication()

            if not auth_success:
                logger.info("Authentication failed or cancelled, exiting...")
                return 0

            logger.info("✅ Authentication successful, proceeding with application initialization")

            # Verify session was saved after successful authentication
            if firebase_client.remember_session:
                if firebase_client.session_file.exists():
                    logger.info("✅ Session file verified after authentication")
                else:
                    logger.warning("⚠️ Session file missing after authentication, attempting to save...")
                    try:
                        firebase_client._save_session()
                        if firebase_client.session_file.exists():
                            logger.info("✅ Session file created successfully on retry")
                        else:
                            logger.error("❌ Failed to create session file on retry")
                    except Exception as e:
                        logger.error(f"❌ Error saving session on retry: {e}")

        # STEP 2: NOW show loading screen after authentication is complete
        logger.info("Creating loading screen after authentication...")
        loading_screen = LoadingScreen()
        loading_screen.set_version(app.applicationVersion())
        loading_screen.set_title(app.applicationName())

        # Show loading screen with initial progress
        loading_screen.show_loading()

        # Force immediate display with multiple UI updates
        QApplication.processEvents()
        loading_screen.update_progress(15, "Authentication complete", "Starting application initialization", "Authentication completed successfully")
        QApplication.processEvents()

        # Small delay to ensure the loading screen is visible
        import time
        time.sleep(0.1)
        QApplication.processEvents()

        # Get user info for display
        if user_authenticated or firebase_client.is_authenticated():
            user_email = firebase_client.current_user.get('email', 'Unknown') if firebase_client.current_user else 'Unknown'
            loading_screen.update_progress(18, "Welcome back!", f"Signed in as {user_email}", f"User authenticated: {user_email}")

        # STEP 3: Continue with application initialization
        logger.info("Starting application initialization...")
        loading_screen.update_progress(22, "Skipping update check", "Proceeding with initialization", "Skipping update check for faster startup")

        # Note: Update checking disabled to prevent hanging on placeholder URLs
        # To re-enable, configure a valid functions_base_url in secure_config.py

        # Continue with main initialization phase
        logger.info("Starting main initialization phase...")
        loading_screen.update_progress(25, "Starting initialization", "Preparing core components", "Initializing core application components")

        # Initialize components with coordinated progress tracking
        config = None
        data_manager = None
        main_window = None

        try:
            # Step 1: Initialize configuration
            logger.info("Initializing configuration...")
            loading_screen.update_progress(28, "Loading configuration...", "Reading application settings and user preferences", "Loading application configuration")
            config = initialize_config()

            # CRITICAL FIX: Set theme on QApplication instance for chart widgets to access
            if hasattr(config, 'theme'):
                app.current_theme = config.theme
                logger.info(f"Set application theme to: {config.theme}")

                # Apply theme to loading screen
                loading_screen.apply_theme(config.theme)
                logger.info(f"Applied theme {config.theme} to loading screen")

            loading_screen.update_progress(32, "Configuration loaded", "Application settings and preferences ready", "Configuration loaded successfully")

            # Step 2: Initialize data manager
            logger.info("Initializing data manager...")
            loading_screen.update_progress(35, "Initializing data storage...", "Setting up database connections and data management", "Setting up data storage system")
            data_manager = initialize_data_manager(config)
            loading_screen.update_progress(40, "Data storage ready", "Database and data management system initialized", "Data storage system ready")

            # Step 3: Create main window (this is the heavy operation)
            logger.info("Creating main window...")

            try:
                # Create progress callback to update loading screen
                def progress_callback(progress, message, detail="", step_detail=""):
                    # Use step_detail if provided, otherwise use detail for loading steps display
                    actual_step_detail = step_detail if step_detail else detail
                    loading_screen.update_progress(progress, message, detail, actual_step_detail)

                main_window = create_main_window(data_manager, config, progress_callback)

            except Exception as e:
                logger.error(f"Failed to create main window: {e}")
                loading_screen.update_progress(0, "Error", f"Failed to create main window: {e}", f"Error: {e}")
                raise

            # Finalize loading
            logger.info("Finalizing loading process...")
            loading_screen.update_progress(92, "Finalizing startup...", "Preparing application interface for display", "Finalizing application startup")
            loading_screen.update_progress(95, "Completing initialization...", "Finalizing all systems and components", "Completing system initialization")
            loading_screen.update_progress(98, "Application ready...", "All modules loaded and ready for use", "Application ready for use")
            loading_screen.update_progress(100, "Welcome to Traqify!", "Application startup complete - enjoy tracking!", "Welcome! Application startup complete")

            # Close loading screen and show main window
            import time
            time.sleep(1.5)  # Brief pause to show completion message
            loading_screen.close_loading()

            # Show main window
            main_window.show()
            main_window.raise_()
            main_window.activateWindow()

            # Trigger post-loading dialogs
            if hasattr(main_window, 'trigger_post_loading_dialogs'):
                main_window.trigger_post_loading_dialogs()

        except Exception as e:
            # Handle initialization errors
            error_msg = f"Initialization failed: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")

            if loading_screen:
                loading_screen.update_progress(0, "Error", error_msg)
            raise

        # Set up cleanup on application exit
        def cleanup_on_exit():
            try:
                logger.info("Application exiting, performing cleanup...")
                # Note: Updater cleanup skipped (updater disabled)
                # Cleanup main window if it exists
                if 'main_window' in locals() and main_window:
                    try:
                        main_window.close()
                    except:
                        pass
                logger.info("Cleanup completed")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

        app.aboutToQuit.connect(cleanup_on_exit)

        # Start event loop
        exit_code = app.exec()

        # Final cleanup before exit
        cleanup_on_exit()
        return exit_code  # Use return instead of sys.exit

    except Exception as e:
        error_msg = f"Error starting application: {e}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Note: Updater cleanup skipped (updater disabled)

        # Hide loading screen if it exists
        try:
            if 'loading_screen' in locals() and loading_screen:
                loading_screen.hide()
        except Exception as screen_error:
            logger.error(f"Error hiding loading screen: {screen_error}")

        # Show error dialog if possible
        try:
            if 'app' not in locals() or app is None:
                app = QApplication(sys.argv)

            QMessageBox.critical(None, "Application Error",
                               f"Failed to start application:\n\n{e}\n\nCheck app_debug.log for details.")
        except Exception as dialog_error:
            logger.error(f"Error showing error dialog: {dialog_error}")

        print(error_msg)
        print(traceback.format_exc())
        return 1  # Use return instead of sys.exit


def handle_initialization_error(error_msg, loading_screen):
    """Handle initialization errors safely"""
    logger.error(f"Initialization failed: {error_msg}")

    try:
        if loading_screen:
            loading_screen.hide()
    except Exception as e:
        logger.error(f"Error hiding loading screen: {e}")

    try:
        QMessageBox.critical(None, "Initialization Error",
                           f"Failed to initialize application:\n\n{error_msg}\n\nCheck app_debug.log for details.")
    except Exception as e:
        logger.error(f"Error showing error dialog: {e}")

    return 1  # Use return instead of sys.exit


def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    try:
        from src.ui.main_window import MainWindow
        from src.core.config import AppConfig
        from src.core.data_manager import DataManager
        from src.ui.loading_screen import LoadingScreen
        print("✅ All core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting Traqify application...")
    print("🔍 Debug: Python executable:", sys.executable)
    print("🔍 Debug: Working directory:", os.getcwd())

    # Check if running as packaged executable
    if getattr(sys, 'frozen', False):
        # Running as packaged executable
        print("🔍 Debug: Running as packaged executable")
        print("🔍 Debug: Executable location:", sys.executable)
        try:
            print("🔍 Debug: Executable size:", os.path.getsize(sys.executable), "bytes")
        except Exception as e:
            print(f"🔍 Debug: Could not get executable size: {e}")
    else:
        # Running as script
        print("🔍 Debug: Running as Python script")
        print("🔍 Debug: File location:", __file__)
        try:
            print("🔍 Debug: File size:", os.path.getsize(__file__), "bytes")
            # Test if this file is actually readable
            with open(__file__, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"🔍 Debug: File has {len(lines)} lines")
                print(f"🔍 Debug: First line: {lines[0].strip()}")
                print(f"🔍 Debug: Last line: {lines[-1].strip()}")
        except Exception as e:
            print(f"❌ Error reading file: {e}")

    # Test imports before running main application
    if not test_imports():
        print("❌ Import test failed - check dependencies")
        sys.exit(1)

    # Add command line argument for testing mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("✅ Test mode completed successfully - all imports work")
        sys.exit(0)

    try:
        exit_code = main()
        if exit_code == 0:
            print("✅ Traqify application completed successfully")
        else:
            print(f"❌ Traqify application exited with code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        sys.exit(1)



