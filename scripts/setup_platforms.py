#!/usr/bin/env python3
"""
Platform Setup Helper
Guides you through setting up Render and Appwrite platforms
"""

import os
import sys
import json
import webbrowser
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_step(step_num, title):
    """Print a formatted step"""
    print(f"\n📋 Step {step_num}: {title}")
    print("-" * 40)

def get_user_input(prompt, required=True):
    """Get user input with validation"""
    while True:
        value = input(f"{prompt}: ").strip()
        if value or not required:
            return value
        print("❌ This field is required. Please try again.")

def validate_json(json_str):
    """Validate JSON string"""
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False

def main():
    print_header("Personal Finance Dashboard - Platform Setup Helper")
    print("This script will guide you through setting up Render and Appwrite platforms.")
    print("Make sure you have your Firebase credentials ready!")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Check if Firebase credentials are available
    print_step(1, "Firebase Credentials Check")
    
    firebase_sa = os.getenv('FIREBASE_SERVICE_ACCOUNT')
    firebase_key = os.getenv('FIREBASE_API_KEY')
    
    if not firebase_sa or not firebase_key:
        print("⚠️  Firebase credentials not found in environment variables.")
        print("You'll need to get these from Firebase Console:")
        print("1. Service Account JSON from Project Settings > Service Accounts")
        print("2. Web API Key from Project Settings > General")
        print()
        
        # Get Firebase credentials
        print("Let's collect your Firebase credentials:")
        
        if not firebase_sa:
            print("\n🔑 Firebase Service Account JSON:")
            print("Go to Firebase Console > Project Settings > Service Accounts")
            print("Click 'Generate new private key' and copy the entire JSON content")
            firebase_sa = get_user_input("Paste Firebase Service Account JSON")
            
            if not validate_json(firebase_sa):
                print("❌ Invalid JSON format. Please check and try again.")
                return 1
        
        if not firebase_key:
            print("\n🔑 Firebase API Key:")
            print("Go to Firebase Console > Project Settings > General")
            print("Copy the Web API Key from 'Your apps' section")
            firebase_key = get_user_input("Enter Firebase API Key")
    else:
        print("✅ Firebase credentials found in environment variables")
    
    # Platform selection
    print_step(2, "Platform Selection")
    print("Which platforms would you like to set up?")
    print("1. Render only")
    print("2. Appwrite only") 
    print("3. Both platforms (recommended)")
    
    choice = get_user_input("Enter your choice (1-3)", required=True)
    
    setup_render = choice in ['1', '3']
    setup_appwrite = choice in ['2', '3']
    
    # Render setup
    if setup_render:
        print_step(3, "Render Setup")
        print("Setting up Render (Primary Production Platform)")
        print()
        
        print("📖 Follow these steps:")
        print("1. Go to render.com and create an account")
        print("2. Connect your GitHub repository")
        print("3. Create a new Web Service")
        print("4. Use the configuration from RENDER_SETUP_GUIDE.md")
        print()
        
        open_render = input("Open Render website now? (y/n): ").lower() == 'y'
        if open_render:
            webbrowser.open('https://render.com')
        
        print("\n📋 Render Configuration:")
        print("Build Command: cd replit_backend && pip install -r requirements.txt")
        print("Start Command: cd replit_backend && gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 main:app")
        print()
        print("Environment Variables to set:")
        print(f"FIREBASE_SERVICE_ACCOUNT = {firebase_sa[:50]}...")
        print(f"FIREBASE_API_KEY = {firebase_key}")
        print("PORT = 10000")
        print("PYTHON_VERSION = 3.10.12")
        
        render_url = get_user_input("\nEnter your Render service URL (when ready)", required=False)
        
        if render_url:
            print(f"✅ Render URL saved: {render_url}")
    
    # Appwrite setup
    if setup_appwrite:
        print_step(4, "Appwrite Setup")
        print("Setting up Appwrite Functions (Backup Production Platform)")
        print()
        
        print("📖 Follow these steps:")
        print("1. Go to cloud.appwrite.io and create an account")
        print("2. Create a new project")
        print("3. Install Appwrite CLI: npm install -g appwrite-cli")
        print("4. Follow the detailed steps in APPWRITE_SETUP_GUIDE.md")
        print()
        
        open_appwrite = input("Open Appwrite Console now? (y/n): ").lower() == 'y'
        if open_appwrite:
            webbrowser.open('https://cloud.appwrite.io')
        
        project_id = get_user_input("\nEnter your Appwrite Project ID (when ready)", required=False)
        
        if project_id:
            # Update appwrite.json with project ID
            appwrite_config_file = project_root / "appwrite_functions" / "appwrite.json"
            try:
                with open(appwrite_config_file, 'r') as f:
                    config = json.load(f)
                
                config['projectId'] = project_id
                
                with open(appwrite_config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                print(f"✅ Updated appwrite.json with Project ID: {project_id}")
            except Exception as e:
                print(f"⚠️  Could not update appwrite.json: {e}")
        
        appwrite_url = get_user_input("Enter your Appwrite Function URL (when ready)", required=False)
        
        if appwrite_url:
            print(f"✅ Appwrite URL saved: {appwrite_url}")
    
    # Update service discovery configuration
    print_step(5, "Service Discovery Configuration")
    
    config_file = project_root / "service_discovery_config.json"
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Update URLs if provided
        if setup_render and 'render_url' in locals() and render_url:
            for endpoint in config['endpoints']:
                if endpoint['name'] == 'render':
                    endpoint['url'] = render_url.rstrip('/')
                    break
        
        if setup_appwrite and 'appwrite_url' in locals() and appwrite_url:
            for endpoint in config['endpoints']:
                if endpoint['name'] == 'appwrite':
                    endpoint['url'] = appwrite_url.rstrip('/')
                    break
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Service discovery configuration updated")
        
    except Exception as e:
        print(f"⚠️  Could not update service discovery config: {e}")
    
    # Create environment file for local testing
    print_step(6, "Local Environment Setup")
    
    env_file = project_root / "replit_backend" / ".env"
    
    create_env = input("Create local .env file for testing? (y/n): ").lower() == 'y'
    
    if create_env:
        env_content = f"""# Local Development Environment
# Generated by setup_platforms.py

FIREBASE_SERVICE_ACCOUNT={firebase_sa}
FIREBASE_API_KEY={firebase_key}
DEBUG=true
LOG_LEVEL=DEBUG
PORT=5000
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            print(f"✅ Created local .env file: {env_file}")
        except Exception as e:
            print(f"⚠️  Could not create .env file: {e}")
    
    # Final instructions
    print_step(7, "Next Steps")
    print("🎉 Platform setup helper completed!")
    print()
    print("📋 What to do next:")
    
    if setup_render:
        print("1. Complete Render setup using RENDER_SETUP_GUIDE.md")
        print("2. Test your Render deployment")
    
    if setup_appwrite:
        print("3. Complete Appwrite setup using APPWRITE_SETUP_GUIDE.md")
        print("4. Deploy your function using the deployment scripts")
    
    print("5. Test the complete failover system:")
    print("   python scripts/deploy_manager.py --test")
    print()
    print("6. Run your application and check the Service Discovery widget")
    print("   python main.py")
    print()
    print("📚 Documentation:")
    print("- RENDER_SETUP_GUIDE.md - Detailed Render setup")
    print("- APPWRITE_SETUP_GUIDE.md - Detailed Appwrite setup") 
    print("- TRIPLE_DEPLOYMENT_GUIDE.md - Complete system overview")
    print("- FAILOVER_SYSTEM_README.md - Technical details")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)
