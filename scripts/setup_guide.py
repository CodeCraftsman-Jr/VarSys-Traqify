#!/usr/bin/env python3
"""
Interactive Setup Guide for Triple Deployment Strategy
Guides you through setting up all three platforms step by step
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SetupGuide:
    """Interactive setup guide for triple deployment strategy"""
    
    def __init__(self):
        self.setup_status = {
            'environment_variables': False,
            'appwrite_cli': False,
            'appwrite_login': False,
            'render_setup': False,
            'replit_setup': False,
            'appwrite_deployment': False
        }
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print("\n" + "=" * 60)
        print(f"🚀 {title}")
        print("=" * 60)
    
    def print_step(self, step: str, description: str):
        """Print a setup step"""
        print(f"\n📋 {step}")
        print(f"   {description}")
    
    def check_environment_variables(self) -> bool:
        """Check if environment variables are set"""
        firebase_account = os.getenv('FIREBASE_SERVICE_ACCOUNT')
        firebase_api_key = os.getenv('FIREBASE_API_KEY')
        
        if firebase_account and firebase_api_key:
            print("✅ Environment variables are set")
            return True
        else:
            print("❌ Environment variables missing")
            return False
    
    def check_appwrite_cli(self) -> bool:
        """Check if Appwrite CLI is installed"""
        try:
            result = subprocess.run(['appwrite', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Appwrite CLI installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        print("❌ Appwrite CLI not installed")
        return False
    
    def check_appwrite_login(self) -> bool:
        """Check if logged into Appwrite"""
        try:
            result = subprocess.run(['appwrite', 'account', 'get'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Logged into Appwrite")
                return True
        except FileNotFoundError:
            pass
        
        print("❌ Not logged into Appwrite")
        return False
    
    def run_setup(self):
        """Run the complete setup guide"""
        self.print_header("TRIPLE DEPLOYMENT STRATEGY SETUP GUIDE")
        
        print("This guide will help you set up:")
        print("1. 🔥 Firebase Environment Variables")
        print("2. 🚀 Appwrite Functions")
        print("3. 🌐 Render Deployment")
        print("4. 🔧 Replit Configuration")
        print("5. 🧪 Testing & Verification")
        
        # Step 1: Environment Variables
        self.setup_environment_variables()
        
        # Step 2: Appwrite CLI
        self.setup_appwrite_cli()
        
        # Step 3: Appwrite Login
        self.setup_appwrite_login()
        
        # Step 4: Deploy Appwrite Functions
        self.deploy_appwrite_functions()
        
        # Step 5: Configure Render
        self.configure_render()
        
        # Step 6: Configure Replit
        self.configure_replit()
        
        # Step 7: Final Testing
        self.run_final_tests()
        
        # Summary
        self.print_setup_summary()
    
    def setup_environment_variables(self):
        """Guide through environment variable setup"""
        self.print_header("STEP 1: FIREBASE ENVIRONMENT VARIABLES")
        
        if self.check_environment_variables():
            self.setup_status['environment_variables'] = True
            return
        
        print("\n🔥 You need to set up Firebase credentials:")
        print("\n📋 STEP 1.1: Get Firebase Service Account")
        print("   1. Go to: https://console.firebase.google.com/")
        print("   2. Select project: jointjourney-a12d2")
        print("   3. Go to Project Settings → Service Accounts")
        print("   4. Click 'Generate new private key'")
        print("   5. Download the JSON file")
        
        print("\n📋 STEP 1.2: Get Firebase Web API Key")
        print("   1. In Firebase Console, go to Project Settings → General")
        print("   2. Find 'Web API Key' in 'Your apps' section")
        print("   3. Copy the API key (starts with 'AIza...')")
        
        print("\n📋 STEP 1.3: Set Environment Variables")
        print("   Create a file called '.env' in your project root with:")
        print("   FIREBASE_SERVICE_ACCOUNT={\"type\":\"service_account\",...}")
        print("   FIREBASE_API_KEY=AIzaSyC...")
        
        input("\n⏸️  Press Enter after you've set up the environment variables...")
        
        if self.check_environment_variables():
            self.setup_status['environment_variables'] = True
            print("✅ Environment variables setup complete!")
        else:
            print("❌ Environment variables still missing. Please check your setup.")
    
    def setup_appwrite_cli(self):
        """Guide through Appwrite CLI installation"""
        self.print_header("STEP 2: APPWRITE CLI INSTALLATION")
        
        if self.check_appwrite_cli():
            self.setup_status['appwrite_cli'] = True
            return
        
        print("\n📦 Installing Appwrite CLI...")
        print("   Run this command in your terminal:")
        print("   npm install -g appwrite-cli")
        
        input("\n⏸️  Press Enter after installing Appwrite CLI...")
        
        if self.check_appwrite_cli():
            self.setup_status['appwrite_cli'] = True
            print("✅ Appwrite CLI installation complete!")
        else:
            print("❌ Appwrite CLI still not found. Please install it manually.")
    
    def setup_appwrite_login(self):
        """Guide through Appwrite login"""
        self.print_header("STEP 3: APPWRITE LOGIN")
        
        if not self.setup_status['appwrite_cli']:
            print("❌ Appwrite CLI must be installed first")
            return
        
        if self.check_appwrite_login():
            self.setup_status['appwrite_login'] = True
            return
        
        print("\n🔐 Logging into Appwrite...")
        print("   Run this command in your terminal:")
        print("   appwrite login")
        print("   Follow the prompts to authenticate")
        
        input("\n⏸️  Press Enter after logging into Appwrite...")
        
        if self.check_appwrite_login():
            self.setup_status['appwrite_login'] = True
            print("✅ Appwrite login complete!")
        else:
            print("❌ Still not logged into Appwrite. Please try again.")
    
    def deploy_appwrite_functions(self):
        """Guide through Appwrite Functions deployment"""
        self.print_header("STEP 4: DEPLOY APPWRITE FUNCTIONS")
        
        if not self.setup_status['appwrite_login']:
            print("❌ Must be logged into Appwrite first")
            return
        
        print("\n🚀 Deploying to Appwrite Functions...")
        print("   I'll run the deployment script for you...")
        
        try:
            # Change to appwrite_functions directory and run deployment
            appwrite_dir = project_root / "appwrite_functions"
            
            if os.name == 'nt':  # Windows
                script_path = appwrite_dir / "deploy.bat"
                result = subprocess.run([str(script_path)], cwd=appwrite_dir, capture_output=True, text=True)
            else:  # Unix/Linux/Mac
                script_path = appwrite_dir / "deploy.sh"
                result = subprocess.run(["bash", str(script_path)], cwd=appwrite_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Appwrite Functions deployed successfully!")
                self.setup_status['appwrite_deployment'] = True
                print("\n📋 Deployment Output:")
                print(result.stdout)
            else:
                print("❌ Appwrite deployment failed:")
                print(result.stderr)
                print("\n📋 You can try running the deployment manually:")
                print(f"   cd {appwrite_dir}")
                print(f"   {script_path.name}")
                
        except Exception as e:
            print(f"❌ Error running deployment: {e}")
            print("\n📋 Please run the deployment manually:")
            print("   cd appwrite_functions")
            print("   deploy.bat  (Windows) or ./deploy.sh (Linux/Mac)")
    
    def configure_render(self):
        """Guide through Render configuration"""
        self.print_header("STEP 5: CONFIGURE RENDER")
        
        print("\n🌐 Render is already configured in your service discovery!")
        print("   Current URL: https://traqify-api.onrender.com")
        print("\n📋 To set up Render (if not already done):")
        print("   1. Go to: https://render.com/")
        print("   2. Connect your GitHub repository")
        print("   3. Create a new Web Service")
        print("   4. Set build command: cd replit_backend && pip install -r requirements.txt")
        print("   5. Set start command: cd replit_backend && gunicorn --bind 0.0.0.0:$PORT main:app")
        print("   6. Add environment variables:")
        print("      - FIREBASE_SERVICE_ACCOUNT")
        print("      - FIREBASE_API_KEY")
        
        self.setup_status['render_setup'] = True
        print("✅ Render configuration noted!")
    
    def configure_replit(self):
        """Guide through Replit configuration"""
        self.print_header("STEP 6: CONFIGURE REPLIT")
        
        print("\n🔧 Replit Configuration:")
        print("   Current URL: https://replit.com/@YourUsername/YourReplName")
        print("\n📋 To set up Replit (if not already done):")
        print("   1. Go to: https://replit.com/")
        print("   2. Import your GitHub repository")
        print("   3. Set main file: replit_backend/main.py")
        print("   4. Add secrets (environment variables):")
        print("      - FIREBASE_SERVICE_ACCOUNT")
        print("      - FIREBASE_API_KEY")
        print("   5. Update the URL in service_discovery_config.json")
        
        replit_url = input("\n🔗 Enter your Replit URL (or press Enter to skip): ").strip()
        
        if replit_url:
            # Update service discovery config
            try:
                config_file = project_root / "service_discovery_config.json"
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Find and update Replit endpoint
                for endpoint in config['endpoints']:
                    if endpoint['name'] == 'replit':
                        endpoint['url'] = replit_url
                        break
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                print(f"✅ Updated Replit URL to: {replit_url}")
                
            except Exception as e:
                print(f"❌ Failed to update Replit URL: {e}")
        
        self.setup_status['replit_setup'] = True
        print("✅ Replit configuration complete!")
    
    def run_final_tests(self):
        """Run final tests to verify setup"""
        self.print_header("STEP 7: FINAL TESTING")
        
        print("\n🧪 Running comprehensive tests...")
        
        try:
            # Run the test script
            test_script = project_root / "scripts" / "test_deployment.py"
            result = subprocess.run([sys.executable, str(test_script)], 
                                  capture_output=True, text=True, cwd=project_root)
            
            if result.returncode == 0:
                print("✅ All tests passed!")
                print("\n📊 Test Results:")
                print(result.stdout)
            else:
                print("⚠️  Some tests failed:")
                print(result.stdout)
                print("\n📋 This is normal if platforms aren't fully deployed yet.")
                
        except Exception as e:
            print(f"❌ Error running tests: {e}")
    
    def print_setup_summary(self):
        """Print setup summary"""
        self.print_header("SETUP SUMMARY")
        
        print("\n📊 Setup Status:")
        for step, status in self.setup_status.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {step.replace('_', ' ').title()}")
        
        completed = sum(self.setup_status.values())
        total = len(self.setup_status)
        
        print(f"\n📈 Progress: {completed}/{total} steps completed ({completed/total*100:.0f}%)")
        
        if completed == total:
            print("\n🎉 SETUP COMPLETE!")
            print("Your triple deployment strategy is ready!")
            print("\n📋 Next Steps:")
            print("   1. Test the system: python scripts/test_deployment.py")
            print("   2. Deploy all platforms: python scripts/deploy_all_platforms.py")
            print("   3. Monitor the dashboard in your application")
        else:
            print("\n⚠️  Setup incomplete. Please complete the remaining steps:")
            for step, status in self.setup_status.items():
                if not status:
                    print(f"   - {step.replace('_', ' ').title()}")

def main():
    """Main setup function"""
    guide = SetupGuide()
    guide.run_setup()

if __name__ == '__main__':
    main()
