#!/usr/bin/env python3
"""
Create Release Package Script for VarSys_Traqify_Public
Creates a release ZIP file for Traqify with proper versioning and metadata
Repository: https://github.com/CodeCraftsman-Jr/VarSys_Traqify_Public
"""

import os
import sys
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

def create_release_package():
    """Create a release package with the latest build"""
    
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist" / "PersonalFinanceDashboard"
    releases_dir = project_root / "releases"
    
    # Ensure releases directory exists
    releases_dir.mkdir(exist_ok=True)
    
    # Check if build exists
    if not dist_dir.exists():
        print(f"❌ Build directory not found: {dist_dir}")
        print("Please run the build script first to create the executable")
        return False
    
    print(f"📦 Creating release package from: {dist_dir}")
    
    # Create release ZIP file
    release_zip = releases_dir / "Traqify_v1.0.2_Release.zip"
    
    try:
        with zipfile.ZipFile(release_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the dist directory
            for root, dirs, files in os.walk(dist_dir):
                for file in files:
                    file_path = Path(root) / file
                    # Create archive path relative to the dist directory
                    arcname = file_path.relative_to(dist_dir)
                    zipf.write(file_path, arcname)
                    print(f"  ✓ Added: {arcname}")
        
        # Get file size
        file_size = release_zip.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"✅ Release package created successfully!")
        print(f"📁 Location: {release_zip}")
        print(f"📊 Size: {file_size_mb:.1f} MB ({file_size:,} bytes)")
        
        # Create release metadata
        metadata = {
            "version": "1.0.2",
            "release_date": datetime.now().isoformat(),
            "file_name": release_zip.name,
            "file_size": file_size,
            "file_size_mb": round(file_size_mb, 1),
            "build_type": "Release",
            "platform": "Windows",
            "architecture": "x64",
            "features": [
                "Enhanced serverless secure authentication",
                "Advanced backend selection dialog",
                "Service discovery configuration",
                "Secure Firebase client integration",
                "Auto-update functionality",
                "Personal finance tracking",
                "Investment portfolio management",
                "Data visualization and reports"
            ],
            "requirements": {
                "os": "Windows 10 or later",
                "architecture": "64-bit",
                "memory": "4GB RAM minimum, 8GB recommended",
                "storage": "500MB free disk space",
                "network": "Internet connection required"
            }
        }
        
        # Save metadata
        metadata_file = releases_dir / "Traqify_v1.0.2_Release_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📋 Metadata saved: {metadata_file}")
        
        # Create release notes
        release_notes = releases_dir / "Traqify_v1.0.2_Release_Notes.md"
        with open(release_notes, 'w', encoding='utf-8') as f:
            f.write(f"""# Traqify v1.0.2 Release Notes

## Release Information
- **Version:** 1.0.2
- **Release Date:** {datetime.now().strftime('%B %d, %Y')}
- **File Size:** {file_size_mb:.1f} MB
- **Platform:** Windows 10+ (64-bit)

## What's New in v1.0.2

### 🚀 New Features
- Enhanced serverless secure authentication system
- Advanced backend selection dialog with service discovery
- Improved build system with comprehensive module inclusion
- Innovation script for automated deployment pipeline

### 🔧 Improvements
- Better integration of secure Firebase client
- Enhanced startup login with backend switching
- Improved executable packaging with all dependencies
- Updated version management system

### 🐛 Bug Fixes
- Fixed missing authentication modules in build
- Resolved backend selection persistence issues
- Fixed service discovery configuration loading

### 🔒 Security Enhancements
- Comprehensive credential protection in .gitignore
- Secure serverless authentication flow
- Enhanced Firebase integration security
- Protected API keys and sensitive configuration

## Installation Instructions

1. **Download** the `Traqify_v1.0.2_Release.zip` file
2. **Extract** the ZIP file to your desired location
3. **Run** `Traqify_v1.0.2.exe` to start the application
4. **Follow** the on-screen setup instructions

## System Requirements
- Windows 10 or later (64-bit)
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space
- Internet connection required for authentication and updates

## Support
For support and updates, visit: https://jointjourney-a12d2.web.app

## Previous Versions
- v1.0.1 available at: https://drive.google.com/uc?export=download&id=1px3i_JAVJMHKmsE7SO5TDM4WHIcdFB5T
""")
        
        print(f"📝 Release notes created: {release_notes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating release package: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Traqify Release Package Creator")
    print("=" * 50)
    
    success = create_release_package()
    
    if success:
        print("\n🎉 Release package created successfully!")
        print("Ready for distribution and deployment.")
    else:
        print("\n❌ Failed to create release package.")
        sys.exit(1)
