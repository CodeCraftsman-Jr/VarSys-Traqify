#!/usr/bin/env python3
"""
Launcher script for Traqify that handles path issues in frozen executables
"""

import sys
import os
from pathlib import Path

def setup_frozen_paths():
    """Setup paths for frozen executable"""
    if getattr(sys, 'frozen', False):
        # Running in a frozen executable
        application_path = Path(sys.executable).parent
        
        # Add the application directory to sys.path
        if str(application_path) not in sys.path:
            sys.path.insert(0, str(application_path))
        
        # Set the working directory to the application directory
        os.chdir(application_path)
        
        # Add lib directory to path if it exists
        lib_path = application_path / 'lib'
        if lib_path.exists() and str(lib_path) not in sys.path:
            sys.path.insert(0, str(lib_path))
            
        print(f"Frozen executable detected")
        print(f"Application path: {application_path}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
        
    else:
        # Running in normal Python environment
        print("Running in development mode")

def main():
    """Main entry point"""
    try:
        # Setup paths for frozen executable
        setup_frozen_paths()
        
        # Import and run the main application
        from main import main as app_main
        return app_main()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Trying alternative import...")
        
        try:
            # Try importing from current directory
            import main
            return main.main()
        except Exception as e2:
            print(f"Failed to import main module: {e2}")
            print("Please ensure all required files are present.")
            input("Press Enter to exit...")
            return 1
            
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
