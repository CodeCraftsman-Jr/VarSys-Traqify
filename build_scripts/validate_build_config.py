#!/usr/bin/env python3
"""
Build Configuration Validation Script
This script validates that all necessary modules and dependencies are properly configured for the build process.
"""

import os
import sys
import json
import importlib
from pathlib import Path
from typing import List, Dict, Set

class BuildConfigValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.errors = []
        self.warnings = []
        
    def validate_hidden_imports(self, config_file: Path) -> bool:
        """Validate that all hidden imports in the config actually exist"""
        print(f"Validating hidden imports in {config_file.name}...")
        
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix == '.json':
                    config = json.load(f)
                    hidden_imports = []
                    for option in config.get('pyinstallerOptions', []):
                        if option.get('optionDest') == 'hidden_import':
                            hidden_imports = option.get('value', [])
                            break
                else:
                    # For .py files, we'd need to parse differently
                    return True
                    
            missing_modules = []
            for module_name in hidden_imports:
                if module_name.startswith('src.'):
                    # Convert to file path
                    module_path = self.src_dir / module_name[4:].replace('.', '/')
                    if not (module_path.with_suffix('.py').exists() or 
                           (module_path / '__init__.py').exists()):
                        missing_modules.append(module_name)
                else:
                    # Try to import external modules
                    try:
                        importlib.import_module(module_name)
                    except ImportError:
                        missing_modules.append(module_name)
            
            if missing_modules:
                self.errors.append(f"Missing modules in {config_file.name}: {missing_modules}")
                return False
            else:
                print(f"SUCCESS: All hidden imports validated in {config_file.name}")
                return True
                
        except Exception as e:
            self.errors.append(f"Error validating {config_file.name}: {e}")
            return False
    
    def validate_data_files(self, config_file: Path) -> bool:
        """Validate that all data files in the config actually exist"""
        print(f"Validating data files in {config_file.name}...")
        
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix == '.json':
                    config = json.load(f)
                    data_files = []
                    for option in config.get('pyinstallerOptions', []):
                        if option.get('optionDest') == 'add_data':
                            data_files = option.get('value', [])
                            break
                else:
                    return True
                    
            missing_files = []
            for data_entry in data_files:
                if ';' in data_entry:
                    source_path = data_entry.split(';')[0]
                    full_path = self.project_root / source_path
                    if not full_path.exists():
                        missing_files.append(source_path)
            
            if missing_files:
                self.warnings.append(f"Missing data files in {config_file.name}: {missing_files}")
                return False
            else:
                print(f"SUCCESS: All data files validated in {config_file.name}")
                return True
                
        except Exception as e:
            self.errors.append(f"Error validating data files in {config_file.name}: {e}")
            return False
    
    def validate_requirements(self) -> bool:
        """Validate that requirements.txt includes all necessary dependencies"""
        print("Validating requirements.txt...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            self.errors.append("requirements.txt not found")
            return False
        
        with open(requirements_file, 'r') as f:
            requirements = f.read()
        
        required_packages = [
            'auto-py-to-exe',
            'PySide6',
            'pandas',
            'numpy',
            'matplotlib',
            'plotly',
            'firebase-admin',
            'requests',
            'seaborn',
            'yfinance',
            'mftool',
            'kiteconnect',
            'cryptography'
        ]
        
        missing_packages = []
        for package in required_packages:
            if package not in requirements:
                missing_packages.append(package)
        
        if missing_packages:
            self.errors.append(f"Missing packages in requirements.txt: {missing_packages}")
            return False
        else:
            print("SUCCESS: All required packages found in requirements.txt")
            return True
    
    def validate_version_consistency(self) -> bool:
        """Validate that version numbers are consistent across files"""
        print("Validating version consistency...")
        
        # Check config.json
        config_file = self.project_root / "config.json"
        config_version = None
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                config_version = config.get('app_version')
        
        # Check installer script
        installer_file = self.project_root / "build_scripts" / "traqify_installer.iss"
        installer_version = None
        if installer_file.exists():
            with open(installer_file, 'r') as f:
                for line in f:
                    if line.startswith('AppVersion='):
                        installer_version = line.split('=')[1].strip()
                        break
        
        if config_version and installer_version and config_version != installer_version:
            self.warnings.append(f"Version mismatch: config.json={config_version}, installer={installer_version}")
            return False
        else:
            print(f"SUCCESS: Version consistency validated: {config_version}")
            return True
    
    def run_validation(self) -> bool:
        """Run all validations"""
        print("="*60)
        print("BUILD CONFIGURATION VALIDATION")
        print("="*60)
        
        success = True
        
        # Validate build config files
        config_files = [
            self.project_root / "build_scripts" / "py_auto_to_exe_manual_config.json"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                success &= self.validate_hidden_imports(config_file)
                success &= self.validate_data_files(config_file)
        
        # Validate requirements
        success &= self.validate_requirements()
        
        # Validate version consistency
        success &= self.validate_version_consistency()
        
        # Print results
        print("\n" + "="*60)
        if self.errors:
            print("ERRORS:")
            for error in self.errors:
                print(f"  ERROR: {error}")

        if self.warnings:
            print("WARNINGS:")
            for warning in self.warnings:
                print(f"  WARNING: {warning}")
        
        if success and not self.errors:
            print("SUCCESS: BUILD CONFIGURATION VALIDATION PASSED")
        else:
            print("ERROR: BUILD CONFIGURATION VALIDATION FAILED")
        
        print("="*60)
        return success and not self.errors

def main():
    validator = BuildConfigValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
