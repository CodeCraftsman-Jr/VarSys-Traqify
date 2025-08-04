#!/usr/bin/env python3
"""
Update Deployment Script

This script helps package and deploy updates to Firebase Hosting.
It handles version management, checksum calculation, and deployment.
"""

import os
import sys
import json
import hashlib
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class UpdateDeployer:
    """Handles deployment of updates to Firebase Hosting"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.hosting_dir = project_root / "hosting"
        self.build_dir = project_root / "dist"  # Where py-auto-to-exe outputs
        
        # Ensure directories exist
        self.hosting_dir.mkdir(exist_ok=True)
        for channel in ["stable", "beta", "dev"]:
            (self.hosting_dir / "updates" / channel).mkdir(parents=True, exist_ok=True)
    
    def calculate_checksums(self, file_path: Path) -> Dict[str, str]:
        """Calculate MD5 and SHA256 checksums for a file"""
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
        
        return {
            'md5': md5_hash.hexdigest(),
            'sha256': sha256_hash.hexdigest()
        }
    
    def create_version_info(self, version: str, channel: str, exe_path: Path, 
                           changelog: Dict[str, Any], required: bool = False) -> Dict[str, Any]:
        """Create version information JSON"""
        file_size = exe_path.stat().st_size
        checksums = self.calculate_checksums(exe_path)
        
        # Generate download URL
        filename = f"PersonalFinanceDashboard-{version}.exe"
        download_url = f"https://jointjourney-a12d2.web.app/updates/{channel}/{filename}"
        
        version_info = {
            "version": version,
            "build_number": self.get_build_number(version),
            "release_date": datetime.now(timezone.utc).isoformat(),
            "channel": channel,
            "required": required,
            "download_url": download_url,
            "download_size": file_size,
            "checksum": checksums,
            "changelog": changelog,
            "system_requirements": {
                "os": "Windows 10 or later",
                "architecture": "x64",
                "ram": "4GB minimum, 8GB recommended",
                "disk_space": "500MB"
            },
            "update_notes": f"Version {version} release for {channel} channel.",
            "rollback_supported": True,
            "auto_update_eligible": channel == "stable"
        }
        
        return version_info
    
    def get_build_number(self, version: str) -> int:
        """Generate build number from version"""
        # Simple build number generation - you might want to use a more sophisticated approach
        parts = version.replace('-', '.').split('.')
        try:
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return major * 10000 + minor * 100 + patch
        except ValueError:
            return 1
    
    def deploy_update(self, version: str, channel: str, exe_path: Path, 
                     changelog: Dict[str, Any], required: bool = False) -> bool:
        """Deploy an update to Firebase Hosting"""
        try:
            print(f"🚀 Deploying update {version} to {channel} channel...")
            
            # Validate inputs
            if not exe_path.exists():
                print(f"❌ Executable not found: {exe_path}")
                return False
            
            if channel not in ["stable", "beta", "dev"]:
                print(f"❌ Invalid channel: {channel}")
                return False
            
            # Create version info
            version_info = self.create_version_info(version, channel, exe_path, changelog, required)
            
            # Copy executable to hosting directory
            filename = f"PersonalFinanceDashboard-{version}.exe"
            dest_exe = self.hosting_dir / "updates" / channel / filename
            
            print(f"📦 Copying executable to {dest_exe}")
            shutil.copy2(exe_path, dest_exe)
            
            # Create version.json
            version_json_path = self.hosting_dir / "updates" / channel / "version.json"
            print(f"📝 Creating version info at {version_json_path}")
            
            with open(version_json_path, 'w') as f:
                json.dump(version_info, f, indent=2)
            
            print(f"✅ Update {version} prepared for {channel} channel")
            print(f"📊 File size: {version_info['download_size'] / (1024*1024):.1f} MB")
            print(f"🔐 SHA256: {version_info['checksum']['sha256']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error deploying update: {e}")
            return False
    
    def deploy_to_firebase(self) -> bool:
        """Deploy to Firebase Hosting using Firebase CLI"""
        try:
            print("🔥 Deploying to Firebase Hosting...")
            
            # Check if Firebase CLI is available
            result = subprocess.run(["firebase", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Firebase CLI not found. Please install it first:")
                print("   npm install -g firebase-tools")
                return False
            
            # Deploy to Firebase Hosting
            result = subprocess.run(["firebase", "deploy", "--only", "hosting"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Successfully deployed to Firebase Hosting!")
                print(result.stdout)
                return True
            else:
                print("❌ Firebase deployment failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error deploying to Firebase: {e}")
            return False
    
    def create_changelog_template(self) -> Dict[str, Any]:
        """Create a changelog template"""
        return {
            "version": "1.0.0",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "changes": [
                {
                    "type": "feature",
                    "description": "New feature description"
                },
                {
                    "type": "improvement",
                    "description": "Improvement description"
                },
                {
                    "type": "bugfix",
                    "description": "Bug fix description"
                }
            ]
        }
    
    def list_available_builds(self) -> list:
        """List available builds in the dist directory"""
        if not self.build_dir.exists():
            return []
        
        builds = []
        for exe_file in self.build_dir.glob("*.exe"):
            builds.append({
                'name': exe_file.name,
                'path': exe_file,
                'size': exe_file.stat().st_size,
                'modified': datetime.fromtimestamp(exe_file.stat().st_mtime)
            })
        
        return sorted(builds, key=lambda x: x['modified'], reverse=True)


def main():
    parser = argparse.ArgumentParser(description="Deploy updates to Firebase Hosting")
    parser.add_argument("--version", required=True, help="Version number (e.g., 1.0.1)")
    parser.add_argument("--channel", choices=["stable", "beta", "dev"], 
                       default="dev", help="Release channel")
    parser.add_argument("--exe", help="Path to executable file")
    parser.add_argument("--changelog", help="Path to changelog JSON file")
    parser.add_argument("--required", action="store_true", 
                       help="Mark this update as required")
    parser.add_argument("--deploy", action="store_true", 
                       help="Deploy to Firebase Hosting after packaging")
    parser.add_argument("--list-builds", action="store_true",
                       help="List available builds")
    
    args = parser.parse_args()
    
    # Get project root (assuming script is in scripts/ directory)
    project_root = Path(__file__).parent.parent
    deployer = UpdateDeployer(project_root)
    
    if args.list_builds:
        builds = deployer.list_available_builds()
        if not builds:
            print("No builds found in dist/ directory")
            return
        
        print("Available builds:")
        for i, build in enumerate(builds):
            print(f"{i+1}. {build['name']} ({build['size']/(1024*1024):.1f} MB) - {build['modified']}")
        return
    
    # Determine executable path
    exe_path = None
    if args.exe:
        exe_path = Path(args.exe)
    else:
        # Try to find the latest build
        builds = deployer.list_available_builds()
        if builds:
            exe_path = builds[0]['path']
            print(f"Using latest build: {exe_path}")
        else:
            print("❌ No executable specified and no builds found")
            return
    
    # Load changelog
    changelog = None
    if args.changelog:
        with open(args.changelog, 'r') as f:
            changelog = json.load(f)
    else:
        # Create default changelog
        changelog = deployer.create_changelog_template()
        changelog['version'] = args.version
        print("⚠️  Using default changelog template")
    
    # Deploy update
    success = deployer.deploy_update(
        args.version, 
        args.channel, 
        exe_path, 
        changelog, 
        args.required
    )
    
    if success and args.deploy:
        deployer.deploy_to_firebase()


if __name__ == "__main__":
    main()
