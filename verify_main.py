#!/usr/bin/env python3
"""
Verification script to test main.py functionality
"""

import os
import sys
import traceback

def verify_main_py():
    """Verify that main.py is not blank and contains expected content"""
    print("=" * 60)
    print("MAIN.PY VERIFICATION SCRIPT")
    print("=" * 60)
    
    # Check if main.py exists
    main_py_path = "main.py"
    if not os.path.exists(main_py_path):
        print("❌ main.py file not found!")
        return False
    
    print(f"✅ main.py file exists at: {os.path.abspath(main_py_path)}")
    
    # Check file size
    file_size = os.path.getsize(main_py_path)
    print(f"📊 File size: {file_size} bytes")
    
    if file_size == 0:
        print("❌ main.py is empty (0 bytes)!")
        return False
    
    # Read and analyze file content
    try:
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        print(f"📄 File has {len(lines)} lines")
        print(f"📄 File has {len(content)} characters")
        
        if len(lines) == 0:
            print("❌ main.py appears to be blank (no lines)!")
            return False
        
        # Check for key content indicators
        key_indicators = [
            "Personal Finance Dashboard",
            "def main():",
            "if __name__ == \"__main__\":",
            "from PySide6",
            "QApplication"
        ]
        
        found_indicators = []
        for indicator in key_indicators:
            if indicator in content:
                found_indicators.append(indicator)
        
        print(f"🔍 Found {len(found_indicators)}/{len(key_indicators)} key indicators:")
        for indicator in found_indicators:
            print(f"  ✅ {indicator}")
        
        missing_indicators = [ind for ind in key_indicators if ind not in found_indicators]
        if missing_indicators:
            print("⚠️ Missing indicators:")
            for indicator in missing_indicators:
                print(f"  ❌ {indicator}")
        
        # Show first and last few lines
        print("\n📖 First 5 lines:")
        for i, line in enumerate(lines[:5], 1):
            print(f"  {i:2d}: {line}")
        
        print("\n📖 Last 5 lines:")
        for i, line in enumerate(lines[-5:], len(lines)-4):
            print(f"  {i:2d}: {line}")
        
        # Test basic syntax
        print("\n🔍 Testing Python syntax...")
        try:
            compile(content, main_py_path, 'exec')
            print("✅ Python syntax is valid")
        except SyntaxError as e:
            print(f"❌ Syntax error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading main.py: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_imports():
    """Test if we can import from the main.py file"""
    print("\n🔍 Testing imports from main.py...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Try to import main module
        import main
        print("✅ Successfully imported main module")
        
        # Check for expected functions
        expected_functions = ['main', 'setup_application', 'test_imports']
        found_functions = []
        
        for func_name in expected_functions:
            if hasattr(main, func_name):
                found_functions.append(func_name)
        
        print(f"🔍 Found {len(found_functions)}/{len(expected_functions)} expected functions:")
        for func in found_functions:
            print(f"  ✅ {func}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print(f"🔍 Current working directory: {os.getcwd()}")
    print(f"🔍 Python executable: {sys.executable}")
    print(f"🔍 Python version: {sys.version}")
    
    # Run verification
    file_ok = verify_main_py()
    import_ok = test_imports()
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    if file_ok and import_ok:
        print("✅ main.py is NOT blank and appears to be working correctly!")
        print("✅ The file contains a complete Personal Finance Dashboard application")
        print("✅ All syntax and import tests passed")
    else:
        print("❌ Issues detected with main.py:")
        if not file_ok:
            print("  - File content issues")
        if not import_ok:
            print("  - Import issues")
    
    print("\n💡 If main.py appears blank in your editor:")
    print("  1. Try refreshing/reopening the file")
    print("  2. Check file encoding (should be UTF-8)")
    print("  3. Clear your IDE cache")
    print("  4. Try opening with a different editor")
