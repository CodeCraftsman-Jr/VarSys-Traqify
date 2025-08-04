#!/usr/bin/env python3
"""
Create Deployment Package for Appwrite Function

This script creates a proper tar.gz archive for the Appwrite function deployment.
"""

import tarfile
import os
from pathlib import Path

def create_deployment_package():
    """Create a tar.gz package with the function code"""
    
    # Set the working directory to the function directory
    function_dir = Path("appwrite_functions/functions/traquify-backend-api")
    
    if not function_dir.exists():
        print(f"❌ Function directory not found: {function_dir}")
        return False
    
    # Change to function directory
    original_dir = os.getcwd()
    os.chdir(function_dir)
    
    try:
        print("📦 Creating deployment package...")
        
        # Create tar.gz file
        with tarfile.open('deployment.tar.gz', 'w:gz') as tar:
            # Add src directory
            if Path('src').exists():
                tar.add('src', arcname='src')
                print("✅ Added src/ directory")
            else:
                print("❌ src/ directory not found")
                return False
            
            # Add requirements.txt
            if Path('requirements.txt').exists():
                tar.add('requirements.txt', arcname='requirements.txt')
                print("✅ Added requirements.txt")
            else:
                print("❌ requirements.txt not found")
                return False
        
        print("✅ Deployment package created: deployment.tar.gz")
        
        # List contents to verify
        print("\n📋 Package contents:")
        with tarfile.open('deployment.tar.gz', 'r:gz') as tar:
            for member in tar.getmembers():
                print(f"  - {member.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating package: {e}")
        return False
        
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    success = create_deployment_package()
    if success:
        print("\n🎉 Deployment package ready!")
    else:
        print("\n❌ Failed to create deployment package")
    exit(0 if success else 1)
