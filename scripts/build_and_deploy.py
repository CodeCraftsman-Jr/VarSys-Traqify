#!/usr/bin/env python3
"""
Build and Deploy Script

This script integrates with py-auto-to-exe to build the application
and then deploy it as an update to Firebase Hosting.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


class BuildAndDeploy:
    """Handles building and deploying the application"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.build_script = project_root / "build_scripts" / "py_auto_to_exe_build.py"
        self.deploy_script = project_root / "scripts" / "deploy_update.py"
        
    def build_application(self) -> bool:
        """Build the application using py-auto-to-exe"""
        try:
            print("🔨 Building application with py-auto-to-exe...")
            
            if not self.build_script.exists():
                print(f"❌ Build script not found: {self.build_script}")
                return False
            
            # Run the build script
            result = subprocess.run([
                sys.executable, str(self.build_script)
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Build completed successfully!")
                print(result.stdout)
                return True
            else:
                print("❌ Build failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error building application: {e}")
            return False
    
    def get_version_from_config(self) -> str:
        """Get version from config file"""
        try:
            config_file = self.project_root / "config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('app_version', '1.0.0')
        except Exception:
            pass
        
        return '1.0.0'
    
    def create_release_changelog(self, version: str) -> dict:
        """Create a release changelog"""
        return {
            "version": version,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "changes": [
                {
                    "type": "feature",
                    "description": f"Release version {version}"
                }
            ]
        }
    
    def deploy_update(self, version: str, channel: str = "dev", 
                     required: bool = False, deploy_to_firebase: bool = False) -> bool:
        """Deploy the built application as an update"""
        try:
            print(f"🚀 Deploying update {version} to {channel} channel...")
            
            # Prepare deployment command
            cmd = [
                sys.executable, str(self.deploy_script),
                "--version", version,
                "--channel", channel
            ]
            
            if required:
                cmd.append("--required")
            
            if deploy_to_firebase:
                cmd.append("--deploy")
            
            # Run deployment
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Deployment completed successfully!")
                print(result.stdout)
                return True
            else:
                print("❌ Deployment failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error deploying update: {e}")
            return False
    
    def full_build_and_deploy(self, version: str = None, channel: str = "dev",
                             required: bool = False, deploy_to_firebase: bool = False) -> bool:
        """Perform full build and deploy process"""
        try:
            # Get version
            if version is None:
                version = self.get_version_from_config()
            
            print(f"🎯 Starting full build and deploy process for version {version}")
            print(f"📦 Target channel: {channel}")
            print(f"🔥 Deploy to Firebase: {'Yes' if deploy_to_firebase else 'No'}")
            print("=" * 50)
            
            # Step 1: Build application
            if not self.build_application():
                return False
            
            print("\n" + "=" * 50)
            
            # Step 2: Deploy update
            if not self.deploy_update(version, channel, required, deploy_to_firebase):
                return False
            
            print("\n" + "=" * 50)
            print("🎉 Full build and deploy process completed successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in build and deploy process: {e}")
            return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Build and deploy application")
    parser.add_argument("--version", help="Version number (auto-detected if not specified)")
    parser.add_argument("--channel", choices=["stable", "beta", "dev"], 
                       default="dev", help="Release channel")
    parser.add_argument("--required", action="store_true", 
                       help="Mark this update as required")
    parser.add_argument("--deploy", action="store_true", 
                       help="Deploy to Firebase Hosting")
    parser.add_argument("--build-only", action="store_true",
                       help="Only build, don't deploy")
    parser.add_argument("--deploy-only", action="store_true",
                       help="Only deploy, don't build")
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    builder = BuildAndDeploy(project_root)
    
    # Get version
    version = args.version or builder.get_version_from_config()
    
    success = True
    
    if args.build_only:
        success = builder.build_application()
    elif args.deploy_only:
        success = builder.deploy_update(version, args.channel, args.required, args.deploy)
    else:
        success = builder.full_build_and_deploy(version, args.channel, args.required, args.deploy)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
