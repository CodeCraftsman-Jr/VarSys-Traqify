#!/usr/bin/env python3
"""
Triple Deployment Strategy - Deploy All Platforms
Automated deployment script for Render, Appwrite Functions, and Replit
"""

import sys
import os
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class PlatformDeployer:
    """Handles deployment to a specific platform"""
    
    def __init__(self, platform: str, config: Dict[str, Any], verbose: bool = False):
        self.platform = platform
        self.config = config
        self.verbose = verbose
        self.deployment_log: List[str] = []
        
    def log(self, message: str, level: str = 'INFO'):
        """Log deployment message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{self.platform.upper()}] {message}"
        self.deployment_log.append(log_entry)
        
        if self.verbose or level in ['ERROR', 'SUCCESS']:
            prefix = {
                'INFO': '📋',
                'SUCCESS': '✅',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'DEBUG': '🔍'
            }.get(level, '📋')
            print(f"{prefix} {log_entry}")
    
    def deploy(self) -> Tuple[bool, str, List[str]]:
        """Deploy to the platform"""
        try:
            self.log(f"Starting deployment to {self.platform}...", 'INFO')
            
            if self.platform == 'render':
                return self.deploy_render()
            elif self.platform == 'appwrite':
                return self.deploy_appwrite()
            elif self.platform == 'replit':
                return self.deploy_replit()
            else:
                return False, f"Unknown platform: {self.platform}", self.deployment_log
                
        except Exception as e:
            error_msg = f"Deployment failed with exception: {str(e)}"
            self.log(error_msg, 'ERROR')
            return False, error_msg, self.deployment_log
    
    def deploy_render(self) -> Tuple[bool, str, List[str]]:
        """Deploy to Render platform"""
        self.log("Deploying to Render...", 'INFO')
        
        # Check if webhook is configured
        webhook_url = self.config.get('webhook_url')
        
        if webhook_url:
            try:
                self.log("Triggering Render deployment via webhook...", 'INFO')
                response = requests.post(webhook_url, timeout=30)
                
                if response.status_code == 200:
                    self.log("Render deployment triggered successfully", 'SUCCESS')
                    return True, "Render deployment triggered via webhook", self.deployment_log
                else:
                    error_msg = f"Webhook trigger failed: HTTP {response.status_code}"
                    self.log(error_msg, 'ERROR')
                    return False, error_msg, self.deployment_log
                    
            except Exception as e:
                error_msg = f"Failed to trigger Render webhook: {str(e)}"
                self.log(error_msg, 'ERROR')
                return False, error_msg, self.deployment_log
        else:
            # Auto-deploy via git push
            try:
                self.log("Checking git status...", 'INFO')
                
                # Check if there are changes to commit
                result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    cwd=project_root,
                    capture_output=True,
                    text=True
                )
                
                if result.stdout.strip():
                    self.log("Committing changes...", 'INFO')
                    
                    # Add all changes
                    subprocess.run(['git', 'add', '.'], cwd=project_root, check=True)
                    
                    # Commit changes
                    commit_msg = f"Automated deployment - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    subprocess.run(['git', 'commit', '-m', commit_msg], cwd=project_root, check=True)
                
                # Push to trigger Render deployment
                self.log("Pushing to main branch...", 'INFO')
                subprocess.run(['git', 'push', 'origin', 'main'], cwd=project_root, check=True)
                
                self.log("Git push completed - Render auto-deploy will trigger", 'SUCCESS')
                return True, "Render deployment triggered via git push", self.deployment_log
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Git operation failed: {e}"
                self.log(error_msg, 'ERROR')
                return False, error_msg, self.deployment_log
    
    def deploy_appwrite(self) -> Tuple[bool, str, List[str]]:
        """Deploy to Appwrite Functions"""
        self.log("Deploying to Appwrite Functions...", 'INFO')
        
        try:
            # Change to appwrite_functions directory
            appwrite_dir = project_root / "appwrite_functions"
            
            if not appwrite_dir.exists():
                error_msg = "Appwrite functions directory not found"
                self.log(error_msg, 'ERROR')
                return False, error_msg, self.deployment_log
            
            # Check if Appwrite CLI is available
            try:
                subprocess.run(['appwrite', '--version'], capture_output=True, check=True, shell=True)
                self.log("Appwrite CLI found", 'INFO')
            except (subprocess.CalledProcessError, FileNotFoundError):
                error_msg = "Appwrite CLI not found. Please install: npm install -g appwrite-cli"
                self.log(error_msg, 'ERROR')
                return False, error_msg, self.deployment_log
            
            # Check authentication
            try:
                subprocess.run(['appwrite', 'account', 'get'], capture_output=True, check=True, shell=True)
                self.log("Appwrite authentication verified", 'INFO')
            except subprocess.CalledProcessError:
                error_msg = "Not authenticated with Appwrite. Please run: appwrite login"
                self.log(error_msg, 'ERROR')
                return False, error_msg, self.deployment_log
            
            # Execute deployment script
            self.log("Executing Appwrite deployment script...", 'INFO')
            
            if os.name == 'nt':  # Windows
                script_path = appwrite_dir / "deploy.bat"
                cmd = [str(script_path)]
            else:  # Unix/Linux/Mac
                script_path = appwrite_dir / "deploy.sh"
                cmd = ["bash", str(script_path)]
            
            if not script_path.exists():
                error_msg = f"Deployment script not found: {script_path}"
                self.log(error_msg, 'ERROR')
                return False, error_msg, self.deployment_log
            
            # Run deployment script
            result = subprocess.run(
                cmd,
                cwd=appwrite_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                self.log("Appwrite Functions deployment completed successfully", 'SUCCESS')
                return True, "Appwrite Functions deployed successfully", self.deployment_log
            else:
                error_msg = f"Appwrite deployment failed: {result.stderr or result.stdout}"
                self.log(error_msg, 'ERROR')
                return False, error_msg, self.deployment_log
                
        except subprocess.TimeoutExpired:
            error_msg = "Appwrite deployment timed out"
            self.log(error_msg, 'ERROR')
            return False, error_msg, self.deployment_log
        except Exception as e:
            error_msg = f"Appwrite deployment error: {str(e)}"
            self.log(error_msg, 'ERROR')
            return False, error_msg, self.deployment_log
    
    def deploy_replit(self) -> Tuple[bool, str, List[str]]:
        """Deploy to Replit platform"""
        self.log("Deploying to Replit...", 'INFO')
        
        # Check if Replit API credentials are available
        replit_token = os.getenv('REPLIT_TOKEN')
        repl_id = os.getenv('REPL_ID')
        
        if replit_token and repl_id:
            try:
                self.log("Using Replit API to restart repl...", 'INFO')
                
                headers = {
                    'Authorization': f'Bearer {replit_token}',
                    'Content-Type': 'application/json'
                }
                
                # Restart the repl to trigger deployment
                restart_url = f"https://replit.com/data/repls/{repl_id}/restart"
                response = requests.post(restart_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    self.log("Replit restart triggered successfully", 'SUCCESS')
                    return True, "Replit deployment completed via API restart", self.deployment_log
                else:
                    error_msg = f"Replit API restart failed: HTTP {response.status_code}"
                    self.log(error_msg, 'ERROR')
                    return False, error_msg, self.deployment_log
                    
            except Exception as e:
                error_msg = f"Failed to restart Replit via API: {str(e)}"
                self.log(error_msg, 'ERROR')
                return False, error_msg, self.deployment_log
        else:
            # Manual deployment note
            self.log("Replit API credentials not configured", 'WARNING')
            self.log("Replit deployment will be automatic when files are synced", 'INFO')
            return True, "Replit deployment will be automatic (no API credentials)", self.deployment_log
    
    def test_deployment(self) -> Tuple[bool, str]:
        """Test the deployment by checking health endpoint"""
        try:
            url = self.config.get('url')
            if not url:
                return False, "No URL configured for health check"
            
            health_endpoint = f"{url.rstrip('/')}/ping"
            
            self.log(f"Testing deployment at {health_endpoint}...", 'INFO')
            
            # Special handling for Appwrite Functions
            if self.platform == 'appwrite':
                headers = {
                    'Content-Type': 'application/json',
                    'X-Appwrite-Project': '6874905d00119a86f907'
                }
                body = {
                    'path': '/ping',
                    'method': 'GET'
                }
                response = requests.post(url, json=body, headers=headers, timeout=30)
            else:
                response = requests.get(health_endpoint, timeout=30)
            
            if response.status_code == 200:
                self.log(f"Health check passed for {self.platform}", 'SUCCESS')
                return True, "Health check passed"
            else:
                error_msg = f"Health check failed: HTTP {response.status_code}"
                self.log(error_msg, 'WARNING')
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Health check error: {str(e)}"
            self.log(error_msg, 'WARNING')
            return False, error_msg

class TripleDeploymentManager:
    """Manages deployment across all three platforms"""
    
    def __init__(self, verbose: bool = False, parallel: bool = True):
        self.verbose = verbose
        self.parallel = parallel
        self.deployment_config = self.load_deployment_config()
        self.deployment_results: Dict[str, Dict[str, Any]] = {}
        
    def load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        config_file = project_root / "deployment_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Failed to load deployment config: {e}")
        
        # Return default configuration
        return {
            'platforms': {
                'render': {
                    'enabled': True,
                    'url': 'https://traqify-api.onrender.com',
                    'webhook_url': os.getenv('RENDER_DEPLOY_WEBHOOK')
                },
                'appwrite': {
                    'enabled': True,
                    'url': 'https://fra.cloud.appwrite.io/v1/functions/traqify-api/executions'
                },
                'replit': {
                    'enabled': True,
                    'url': 'https://replit.com/@YourUsername/YourReplName'
                }
            },
            'settings': {
                'parallel_deployment': True,
                'test_after_deploy': True,
                'stop_on_failure': False
            }
        }
    
    def deploy_platform(self, platform: str) -> Dict[str, Any]:
        """Deploy to a single platform"""
        config = self.deployment_config['platforms'].get(platform, {})
        
        if not config.get('enabled', True):
            return {
                'platform': platform,
                'success': False,
                'message': 'Platform disabled in configuration',
                'duration': 0,
                'logs': []
            }
        
        deployer = PlatformDeployer(platform, config, self.verbose)
        
        start_time = time.time()
        success, message, logs = deployer.deploy()
        duration = time.time() - start_time
        
        result = {
            'platform': platform,
            'success': success,
            'message': message,
            'duration': duration,
            'logs': logs
        }
        
        # Test deployment if enabled
        if success and self.deployment_config.get('settings', {}).get('test_after_deploy', True):
            test_success, test_message = deployer.test_deployment()
            result['test_success'] = test_success
            result['test_message'] = test_message
        
        return result
    
    def deploy_all_platforms(self) -> Dict[str, Any]:
        """Deploy to all enabled platforms"""
        print("🚀 Starting Triple Deployment Strategy")
        print("=" * 60)
        
        enabled_platforms = [
            platform for platform, config in self.deployment_config['platforms'].items()
            if config.get('enabled', True)
        ]
        
        if not enabled_platforms:
            print("❌ No platforms enabled for deployment")
            return {'success': False, 'message': 'No platforms enabled'}
        
        print(f"📋 Deploying to {len(enabled_platforms)} platforms: {', '.join(enabled_platforms)}")
        
        start_time = time.time()
        
        if self.parallel and len(enabled_platforms) > 1:
            # Parallel deployment
            print("🔄 Running parallel deployments...")
            
            with ThreadPoolExecutor(max_workers=len(enabled_platforms)) as executor:
                future_to_platform = {
                    executor.submit(self.deploy_platform, platform): platform
                    for platform in enabled_platforms
                }
                
                for future in as_completed(future_to_platform):
                    platform = future_to_platform[future]
                    try:
                        result = future.result()
                        self.deployment_results[platform] = result
                        
                        if result['success']:
                            print(f"✅ {platform.upper()} deployment completed ({result['duration']:.1f}s)")
                        else:
                            print(f"❌ {platform.upper()} deployment failed: {result['message']}")
                            
                    except Exception as e:
                        print(f"🚨 {platform.upper()} deployment error: {e}")
                        self.deployment_results[platform] = {
                            'platform': platform,
                            'success': False,
                            'message': f"Deployment error: {str(e)}",
                            'duration': 0,
                            'logs': []
                        }
        else:
            # Sequential deployment
            print("🔄 Running sequential deployments...")
            
            for platform in enabled_platforms:
                print(f"\n📦 Deploying to {platform.upper()}...")
                
                result = self.deploy_platform(platform)
                self.deployment_results[platform] = result
                
                if result['success']:
                    print(f"✅ {platform.upper()} deployment completed ({result['duration']:.1f}s)")
                else:
                    print(f"❌ {platform.upper()} deployment failed: {result['message']}")
                    
                    # Stop on failure if configured
                    if self.deployment_config['settings'].get('stop_on_failure', False):
                        print("🛑 Stopping deployment due to failure")
                        break
        
        total_duration = time.time() - start_time
        
        # Generate summary
        return self.generate_deployment_summary(total_duration)
    
    def generate_deployment_summary(self, total_duration: float) -> Dict[str, Any]:
        """Generate deployment summary"""
        successful_platforms = [
            platform for platform, result in self.deployment_results.items()
            if result['success']
        ]
        
        failed_platforms = [
            platform for platform, result in self.deployment_results.items()
            if not result['success']
        ]
        
        total_platforms = len(self.deployment_results)
        success_rate = (len(successful_platforms) / max(total_platforms, 1)) * 100
        
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT SUMMARY")
        print("=" * 60)
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"Platforms Deployed: {total_platforms}")
        print(f"Successful: {len(successful_platforms)}")
        print(f"Failed: {len(failed_platforms)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if successful_platforms:
            print(f"\n✅ Successful Deployments: {', '.join(successful_platforms)}")
        
        if failed_platforms:
            print(f"\n❌ Failed Deployments: {', '.join(failed_platforms)}")
            for platform in failed_platforms:
                result = self.deployment_results[platform]
                print(f"   {platform}: {result['message']}")
        
        # Health check summary
        healthy_platforms = []
        for platform, result in self.deployment_results.items():
            if result.get('test_success', False):
                healthy_platforms.append(platform)
        
        if healthy_platforms:
            print(f"\n🏥 Healthy Platforms: {', '.join(healthy_platforms)}")
        
        # Overall status
        overall_success = len(failed_platforms) == 0
        
        if overall_success:
            print("\n🎉 All deployments completed successfully!")
            print("Your triple deployment strategy is now active.")
        else:
            print("\n⚠️  Some deployments failed. Please review and fix issues.")
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_duration': total_duration,
            'success_rate': success_rate,
            'overall_success': overall_success,
            'results': self.deployment_results
        }
        
        report_file = project_root / f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Detailed report saved to: {report_file}")
        except Exception as e:
            print(f"⚠️  Failed to save report: {e}")
        
        return report

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='Triple Deployment Strategy - Deploy All Platforms')
    parser.add_argument('--platform', '-p', help='Deploy to specific platform only (render, appwrite, replit)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--sequential', '-s', action='store_true', help='Run deployments sequentially instead of parallel')
    parser.add_argument('--test-only', '-t', action='store_true', help='Only test deployments, do not deploy')
    
    args = parser.parse_args()
    
    # Create deployment manager
    manager = TripleDeploymentManager(
        verbose=args.verbose,
        parallel=not args.sequential
    )
    
    if args.test_only:
        # Run test script instead
        test_script = project_root / "scripts" / "test_deployment.py"
        subprocess.run([sys.executable, str(test_script), '--verbose' if args.verbose else ''])
        return
    
    if args.platform:
        # Deploy to specific platform
        if args.platform not in ['render', 'appwrite', 'replit']:
            print(f"❌ Unknown platform: {args.platform}")
            sys.exit(1)
        
        result = manager.deploy_platform(args.platform)
        
        if result['success']:
            print(f"✅ {args.platform.upper()} deployment completed successfully")
            sys.exit(0)
        else:
            print(f"❌ {args.platform.upper()} deployment failed: {result['message']}")
            sys.exit(1)
    else:
        # Deploy to all platforms
        summary = manager.deploy_all_platforms()
        sys.exit(0 if summary['overall_success'] else 1)

if __name__ == '__main__':
    main()
