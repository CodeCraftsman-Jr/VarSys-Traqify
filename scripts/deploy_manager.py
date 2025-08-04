#!/usr/bin/env python3
"""
Deployment Manager for Personal Finance Dashboard
Handles deployment to both Replit and Render platforms
"""

import os
import sys
import json
import argparse
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class DeploymentManager:
    """Manages deployments to multiple platforms"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.replit_backend_dir = project_root / "replit_backend"
        self.scripts_dir = project_root / "scripts"
        
    def check_prerequisites(self):
        """Check if all prerequisites are met for deployment"""
        print("🔍 Checking deployment prerequisites...")
        
        issues = []
        
        # Check if backend directory exists
        if not self.replit_backend_dir.exists():
            issues.append("replit_backend directory not found")
        
        # Check if main.py exists
        if not (self.replit_backend_dir / "main.py").exists():
            issues.append("main.py not found in replit_backend directory")
        
        # Check if requirements.txt exists
        if not (self.replit_backend_dir / "requirements.txt").exists():
            issues.append("requirements.txt not found in replit_backend directory")
        
        # Check for configuration files
        config_files = [
            self.project_root / "render.yaml",
            self.project_root / "Dockerfile",
            self.replit_backend_dir / ".replit",
            self.replit_backend_dir / "replit.nix"
        ]
        
        for config_file in config_files:
            if not config_file.exists():
                issues.append(f"Configuration file not found: {config_file.name}")
        
        if issues:
            print("❌ Prerequisites check failed:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ All prerequisites met!")
        return True
    
    def test_backend_locally(self):
        """Test the backend locally before deployment"""
        print("🧪 Testing backend locally...")
        
        try:
            # Change to backend directory
            os.chdir(self.replit_backend_dir)
            
            # Install dependencies
            print("📦 Installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, capture_output=True)
            
            # Test import
            print("🔍 Testing imports...")
            test_script = """
import sys
sys.path.insert(0, '.')
try:
    from main import app
    print("✅ Import successful")
    
    # Test basic app creation
    with app.test_client() as client:
        response = client.get('/')
        if response.status_code == 200:
            print("✅ Health check endpoint working")
        else:
            print(f"⚠️  Health check returned status {response.status_code}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
"""
            
            result = subprocess.run([sys.executable, "-c", test_script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Local testing passed!")
                print(result.stdout)
                return True
            else:
                print("❌ Local testing failed!")
                print(result.stderr)
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Local testing failed: {e}")
            return False
        finally:
            # Change back to project root
            os.chdir(self.project_root)
    
    def prepare_replit_deployment(self):
        """Prepare files for Replit deployment"""
        print("📦 Preparing Replit deployment...")

        # Check if .replit file is properly configured
        replit_file = self.replit_backend_dir / ".replit"
        if replit_file.exists():
            print("✅ .replit file found")
        else:
            print("❌ .replit file not found")
            return False

        # Check if replit.nix file exists
        nix_file = self.replit_backend_dir / "replit.nix"
        if nix_file.exists():
            print("✅ replit.nix file found")
        else:
            print("❌ replit.nix file not found")
            return False

        print("✅ Replit deployment preparation complete!")
        print("\n📋 Next steps for Replit deployment:")
        print("1. Go to https://replit.com")
        print("2. Create a new Repl or import from GitHub")
        print("3. Upload the replit_backend directory contents")
        print("4. Set environment variables in Replit Secrets:")
        print("   - FIREBASE_SERVICE_ACCOUNT")
        print("   - FIREBASE_API_KEY")
        print("5. Run the application")

        return True
    
    def prepare_render_deployment(self):
        """Prepare files for Render deployment"""
        print("📦 Preparing Render deployment...")
        
        # Check if render.yaml exists
        render_file = self.project_root / "render.yaml"
        if render_file.exists():
            print("✅ render.yaml file found")
        else:
            print("❌ render.yaml file not found")
            return False
        
        # Check if Dockerfile exists
        dockerfile = self.project_root / "Dockerfile"
        if dockerfile.exists():
            print("✅ Dockerfile found")
        else:
            print("❌ Dockerfile not found")
            return False
        
        print("✅ Render deployment preparation complete!")
        print("\n📋 Next steps for Render deployment:")
        print("1. Go to https://render.com")
        print("2. Connect your GitHub repository")
        print("3. Create a new Web Service")
        print("4. Use the render.yaml configuration")
        print("5. Set environment variables in Render dashboard:")
        print("   - FIREBASE_SERVICE_ACCOUNT")
        print("   - FIREBASE_API_KEY")
        print("6. Deploy the service")
        
        return True

    def prepare_appwrite_deployment(self):
        """Prepare files for Appwrite Functions deployment"""
        print("📦 Preparing Appwrite Functions deployment...")

        appwrite_dir = self.project_root / "appwrite_functions"

        # Check if Appwrite directory exists
        if not appwrite_dir.exists():
            print("❌ appwrite_functions directory not found")
            return False

        # Check required files
        required_files = [
            appwrite_dir / "appwrite.json",
            appwrite_dir / "main.py",
            appwrite_dir / "flask_app.py",
            appwrite_dir / "requirements.txt"
        ]

        for file_path in required_files:
            if file_path.exists():
                print(f"✅ {file_path.name} found")
            else:
                print(f"❌ {file_path.name} not found")
                return False

        # Check if Appwrite CLI is available
        try:
            import subprocess
            result = subprocess.run(['appwrite', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Appwrite CLI found")
            else:
                print("⚠️  Appwrite CLI not found - manual deployment required")
        except FileNotFoundError:
            print("⚠️  Appwrite CLI not found - manual deployment required")

        print("✅ Appwrite Functions deployment preparation complete!")
        print("\n📋 Next steps for Appwrite Functions deployment:")
        print("1. Install Appwrite CLI: npm install -g appwrite-cli")
        print("2. Login to Appwrite: appwrite login")
        print("3. Run deployment script: cd appwrite_functions && bash deploy.sh")
        print("4. Set environment variables in Appwrite Console:")
        print("   - FIREBASE_SERVICE_ACCOUNT")
        print("   - FIREBASE_API_KEY")
        print("5. Test the function endpoint")

        return True

    def create_deployment_checklist(self):
        """Create a deployment checklist"""
        checklist_file = self.project_root / "DEPLOYMENT_CHECKLIST.md"
        
        checklist_content = f"""# Triple Deployment Strategy Checklist

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Pre-deployment Checks

- [ ] All code changes committed and pushed to repository
- [ ] Backend tested locally
- [ ] Environment variables prepared
- [ ] Firebase service account JSON ready
- [ ] Firebase API key ready
- [ ] Service discovery configuration updated

## Platform 1: Render (Primary Production)

- [ ] GitHub repository connected to Render
- [ ] Web Service created with render.yaml
- [ ] Environment variables set in Render dashboard:
  - [ ] FIREBASE_SERVICE_ACCOUNT
  - [ ] FIREBASE_API_KEY
- [ ] Service deployed successfully
- [ ] Health check endpoint accessible
- [ ] Custom domain configured (if needed)
- [ ] Performance monitoring active

## Platform 2: Appwrite Functions (Backup Production)

- [ ] Appwrite CLI installed and configured
- [ ] Appwrite project created
- [ ] Function deployed using deploy script
- [ ] Environment variables set in Appwrite Console:
  - [ ] FIREBASE_SERVICE_ACCOUNT
  - [ ] FIREBASE_API_KEY
- [ ] Function tested and responding
- [ ] Health check endpoint accessible
- [ ] Function URL documented

## Platform 3: Replit (Development/Emergency Fallback)

- [ ] Replit project created/updated
- [ ] replit_backend directory uploaded
- [ ] Environment variables set in Replit Secrets:
  - [ ] FIREBASE_SERVICE_ACCOUNT
  - [ ] FIREBASE_API_KEY
- [ ] Application started and tested
- [ ] Health check endpoint accessible
- [ ] Auto-sleep behavior documented

## Service Discovery Configuration

- [ ] service_discovery_config.json updated with all platform URLs
- [ ] Platform priorities configured correctly:
  - [ ] Render: Priority 1 (Primary)
  - [ ] Appwrite: Priority 2 (Backup)
  - [ ] Replit: Priority 3 (Fallback)
- [ ] Health check intervals configured
- [ ] Failover thresholds set appropriately

## Client Application Updates

- [ ] Failover Firebase client integrated
- [ ] Service discovery widget added to UI
- [ ] Platform monitoring enabled
- [ ] Failover notifications configured
- [ ] Error handling for all platforms tested

## Post-deployment Verification

- [ ] All three platforms responding correctly
- [ ] Authentication working on all platforms
- [ ] Database connections established
- [ ] Automatic failover tested
- [ ] Manual platform switching tested
- [ ] Error logging functional on all platforms
- [ ] Performance monitoring active

## Monitoring and Alerting

- [ ] Health check monitoring configured
- [ ] Failover alerts set up
- [ ] Performance metrics tracking enabled
- [ ] Platform availability dashboard created
- [ ] Incident response procedures documented

## Rollback Plan

- [ ] Previous version tagged in Git
- [ ] Rollback procedure documented for each platform
- [ ] Database backup created (if applicable)
- [ ] Emergency contact list updated
- [ ] Platform-specific rollback tested
"""
        
        with open(checklist_file, 'w', encoding='utf-8') as f:
            f.write(checklist_content)
        
        print(f"✅ Deployment checklist created: {checklist_file}")
        return checklist_file

def main():
    parser = argparse.ArgumentParser(description="Triple Deployment Manager for Personal Finance Dashboard")
    parser.add_argument("--platform", choices=["replit", "render", "appwrite", "all"], default="all",
                       help="Target deployment platform")
    parser.add_argument("--test", action="store_true", help="Run local tests before deployment")
    parser.add_argument("--checklist", action="store_true", help="Generate deployment checklist")
    parser.add_argument("--check", action="store_true", help="Check prerequisites only")
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    manager = DeploymentManager(project_root)
    
    print("🚀 Personal Finance Dashboard - Deployment Manager")
    print("=" * 60)
    
    # Check prerequisites
    if not manager.check_prerequisites():
        print("\n❌ Prerequisites check failed. Please fix the issues and try again.")
        return 1
    
    if args.check:
        print("\n✅ Prerequisites check passed!")
        return 0
    
    # Run local tests if requested
    if args.test:
        if not manager.test_backend_locally():
            print("\n❌ Local tests failed. Please fix the issues and try again.")
            return 1
    
    # Generate checklist if requested
    if args.checklist:
        manager.create_deployment_checklist()
    
    # Prepare deployments
    success = True

    if args.platform in ["replit", "all"]:
        if not manager.prepare_replit_deployment():
            success = False

    if args.platform in ["render", "all"]:
        if not manager.prepare_render_deployment():
            success = False

    if args.platform in ["appwrite", "all"]:
        if not manager.prepare_appwrite_deployment():
            success = False
    
    if success:
        print("\n🎉 Deployment preparation completed successfully!")
        return 0
    else:
        print("\n❌ Deployment preparation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
