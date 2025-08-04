#!/usr/bin/env python3
"""
Load environment variables from .env file and test the setup
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_env_file():
    """Load environment variables from .env file"""
    env_file = project_root / '.env'
    
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        
        print("✅ Environment variables loaded from .env file")
        return True
        
    except Exception as e:
        print(f"❌ Failed to load .env file: {e}")
        return False

def test_environment():
    """Test environment variables"""
    print("\n🔍 Testing Environment Variables:")
    
    firebase_account = os.getenv('FIREBASE_SERVICE_ACCOUNT')
    firebase_api_key = os.getenv('FIREBASE_API_KEY')
    
    if firebase_account:
        print("✅ FIREBASE_SERVICE_ACCOUNT: SET")
        # Check if it's valid JSON
        try:
            import json
            account_data = json.loads(firebase_account)
            project_id = account_data.get('project_id', 'unknown')
            print(f"   Project ID: {project_id}")
        except:
            print("⚠️  FIREBASE_SERVICE_ACCOUNT: Invalid JSON format")
    else:
        print("❌ FIREBASE_SERVICE_ACCOUNT: NOT SET")
    
    if firebase_api_key and firebase_api_key != "your_firebase_api_key_here":
        print("✅ FIREBASE_API_KEY: SET")
    else:
        print("❌ FIREBASE_API_KEY: NOT SET or using placeholder")
    
    return bool(firebase_account and firebase_api_key and firebase_api_key != "your_firebase_api_key_here")

def test_firebase_connection():
    """Test Firebase connection"""
    print("\n🔥 Testing Firebase Connection:")
    
    try:
        import firebase_admin
        from firebase_admin import credentials
        import json
        
        firebase_account = os.getenv('FIREBASE_SERVICE_ACCOUNT')
        if not firebase_account:
            print("❌ No Firebase service account found")
            return False
        
        # Parse service account
        service_account_info = json.loads(firebase_account)
        
        # Initialize Firebase Admin (if not already initialized)
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred, {
                'databaseURL': f"https://{service_account_info['project_id']}-default-rtdb.firebaseio.com/"
            })
            print("✅ Firebase Admin SDK initialized successfully")
        else:
            print("✅ Firebase Admin SDK already initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        return False

def run_service_discovery_test():
    """Test service discovery"""
    print("\n🔍 Testing Service Discovery:")
    
    try:
        from src.core.service_discovery import service_discovery
        
        endpoints = service_discovery.endpoints
        print(f"✅ Loaded {len(endpoints)} endpoints")
        
        for endpoint in endpoints:
            print(f"   - {endpoint.name}: {endpoint.url} (Priority: {endpoint.priority})")
        
        return True
        
    except Exception as e:
        print(f"❌ Service discovery test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Triple Deployment Strategy - Environment Test")
    print("=" * 60)
    
    # Load environment variables
    env_loaded = load_env_file()
    
    # Test environment variables
    env_valid = test_environment()
    
    # Test Firebase connection
    firebase_ok = False
    if env_valid:
        firebase_ok = test_firebase_connection()
    
    # Test service discovery
    service_discovery_ok = run_service_discovery_test()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Environment File Loading", env_loaded),
        ("Environment Variables", env_valid),
        ("Firebase Connection", firebase_ok),
        ("Service Discovery", service_discovery_ok)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for deployment!")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        
        if not env_valid:
            print("\n📋 Next Steps:")
            print("1. Get your Firebase Web API Key from Firebase Console")
            print("2. Update the .env file with the correct API key")
            print("3. Run this test again")
        
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
