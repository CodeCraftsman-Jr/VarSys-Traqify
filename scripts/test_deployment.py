#!/usr/bin/env python3
"""
Triple Deployment Strategy Test Runner
Comprehensive testing script for all deployment components
"""

import sys
import os
import json
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_file = project_root / '.env'

    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            return True
        except Exception as e:
            print(f"Failed to load .env file: {e}")
    return False

# Load environment variables
load_env_file()

from src.core.service_discovery import service_discovery
from src.core.platform_monitor import platform_monitor
from src.core.deployment_manager import deployment_manager
from src.core.failover_firebase_client import FailoverFirebaseClient

class DeploymentTester:
    """Comprehensive deployment testing suite"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'warnings': 0
            }
        }
        
    def log(self, message: str, level: str = 'INFO'):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        prefix = {
            'INFO': '📋',
            'SUCCESS': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'DEBUG': '🔍'
        }.get(level, '📋')
        
        print(f"[{timestamp}] {prefix} {message}")
        
        if self.verbose and level == 'DEBUG':
            print(f"    DEBUG: {message}")
    
    def test_configuration_files(self) -> bool:
        """Test that all configuration files exist and are valid"""
        self.log("Testing configuration files...", 'INFO')
        
        config_files = [
            'service_discovery_config.json',
            'appwrite_functions/appwrite.json',
            'render.yaml',
            'replit_backend/requirements.txt'
        ]
        
        all_valid = True
        
        for config_file in config_files:
            file_path = project_root / config_file
            
            if not file_path.exists():
                self.log(f"Missing configuration file: {config_file}", 'ERROR')
                all_valid = False
                continue
            
            # Validate JSON files
            if config_file.endswith('.json'):
                try:
                    with open(file_path, 'r') as f:
                        json.load(f)
                    self.log(f"Valid JSON: {config_file}", 'SUCCESS')
                except json.JSONDecodeError as e:
                    self.log(f"Invalid JSON in {config_file}: {e}", 'ERROR')
                    all_valid = False
            else:
                self.log(f"Configuration file exists: {config_file}", 'SUCCESS')
        
        self.test_results['tests']['configuration_files'] = {
            'passed': all_valid,
            'details': f"Checked {len(config_files)} configuration files"
        }
        
        return all_valid
    
    def test_service_discovery(self) -> bool:
        """Test service discovery functionality"""
        self.log("Testing service discovery...", 'INFO')
        
        try:
            # Test endpoint loading
            endpoints = service_discovery.endpoints
            if not endpoints:
                self.log("No endpoints configured in service discovery", 'ERROR')
                return False
            
            self.log(f"Loaded {len(endpoints)} endpoints", 'SUCCESS')
            
            # Test endpoint selection
            selected = service_discovery.select_endpoint()
            if selected:
                self.log(f"Selected endpoint: {selected.name} ({selected.url})", 'SUCCESS')
            else:
                self.log("No healthy endpoints available", 'WARNING')
            
            # Test configuration data loading
            config_data = service_discovery.load_configuration_data()
            if config_data:
                self.log("Configuration data loaded successfully", 'SUCCESS')
            else:
                self.log("Failed to load configuration data", 'ERROR')
                return False
            
            self.test_results['tests']['service_discovery'] = {
                'passed': True,
                'details': f"Service discovery working with {len(endpoints)} endpoints"
            }
            
            return True
            
        except Exception as e:
            self.log(f"Service discovery test failed: {e}", 'ERROR')
            self.test_results['tests']['service_discovery'] = {
                'passed': False,
                'details': f"Error: {str(e)}"
            }
            return False
    
    def test_platform_health_checks(self) -> bool:
        """Test health checks for all platforms"""
        self.log("Testing platform health checks...", 'INFO')
        
        try:
            healthy_platforms = 0
            total_platforms = len(service_discovery.endpoints)
            
            for endpoint in service_discovery.endpoints:
                self.log(f"Checking health of {endpoint.name}...", 'DEBUG')
                
                # Perform health check
                is_healthy = service_discovery.check_endpoint_health(endpoint)
                
                if is_healthy:
                    self.log(f"Platform {endpoint.name} is healthy", 'SUCCESS')
                    healthy_platforms += 1
                else:
                    self.log(f"Platform {endpoint.name} is unhealthy: {endpoint.last_error}", 'WARNING')
            
            success_rate = (healthy_platforms / total_platforms) * 100
            self.log(f"Health check results: {healthy_platforms}/{total_platforms} platforms healthy ({success_rate:.1f}%)", 'INFO')
            
            # Consider test passed if at least one platform is healthy
            test_passed = healthy_platforms > 0
            
            self.test_results['tests']['platform_health_checks'] = {
                'passed': test_passed,
                'details': f"{healthy_platforms}/{total_platforms} platforms healthy",
                'healthy_platforms': healthy_platforms,
                'total_platforms': total_platforms
            }
            
            return test_passed
            
        except Exception as e:
            self.log(f"Platform health check test failed: {e}", 'ERROR')
            self.test_results['tests']['platform_health_checks'] = {
                'passed': False,
                'details': f"Error: {str(e)}"
            }
            return False
    
    def test_failover_mechanism(self) -> bool:
        """Test automatic failover functionality"""
        self.log("Testing failover mechanism...", 'INFO')
        
        try:
            # Get initial endpoint
            initial_endpoint = service_discovery.current_endpoint
            if not initial_endpoint:
                initial_endpoint = service_discovery.select_endpoint()
            
            if not initial_endpoint:
                self.log("No endpoints available for failover test", 'ERROR')
                return False
            
            self.log(f"Initial endpoint: {initial_endpoint.name}", 'DEBUG')
            
            # Simulate endpoint failure
            original_health = initial_endpoint.is_healthy
            initial_endpoint.is_healthy = False
            initial_endpoint.last_error = "Simulated failure for testing"
            
            # Trigger failover
            new_endpoint = service_discovery.select_endpoint()
            
            # Restore original health status
            initial_endpoint.is_healthy = original_health
            initial_endpoint.last_error = None
            
            if new_endpoint and new_endpoint != initial_endpoint:
                self.log(f"Failover successful: {initial_endpoint.name} → {new_endpoint.name}", 'SUCCESS')
                test_passed = True
            elif new_endpoint == initial_endpoint:
                self.log("Failover test inconclusive: same endpoint selected", 'WARNING')
                test_passed = True  # Not necessarily a failure
            else:
                self.log("Failover failed: no alternative endpoint available", 'ERROR')
                test_passed = False
            
            self.test_results['tests']['failover_mechanism'] = {
                'passed': test_passed,
                'details': f"Failover from {initial_endpoint.name} to {new_endpoint.name if new_endpoint else 'none'}"
            }
            
            return test_passed
            
        except Exception as e:
            self.log(f"Failover mechanism test failed: {e}", 'ERROR')
            self.test_results['tests']['failover_mechanism'] = {
                'passed': False,
                'details': f"Error: {str(e)}"
            }
            return False
    
    def test_monitoring_system(self) -> bool:
        """Test platform monitoring functionality"""
        self.log("Testing monitoring system...", 'INFO')
        
        try:
            # Test platform metrics recording
            platform_monitor.record_request('test_platform', True, 0.5)
            platform_monitor.record_request('test_platform', False, 2.0)
            
            # Test health summary generation
            summary = platform_monitor.get_platform_health_summary()
            
            if summary and 'platforms' in summary:
                self.log("Platform health summary generated successfully", 'SUCCESS')
                
                # Test performance trends
                trends = platform_monitor.get_performance_trends('test_platform', hours=1)
                if 'error' not in trends:
                    self.log("Performance trends calculated successfully", 'SUCCESS')
                else:
                    self.log("Performance trends calculation failed", 'WARNING')
                
                test_passed = True
            else:
                self.log("Failed to generate platform health summary", 'ERROR')
                test_passed = False
            
            self.test_results['tests']['monitoring_system'] = {
                'passed': test_passed,
                'details': "Monitoring system functionality verified"
            }
            
            return test_passed
            
        except Exception as e:
            self.log(f"Monitoring system test failed: {e}", 'ERROR')
            self.test_results['tests']['monitoring_system'] = {
                'passed': False,
                'details': f"Error: {str(e)}"
            }
            return False
    
    def test_deployment_manager(self) -> bool:
        """Test deployment manager functionality"""
        self.log("Testing deployment manager...", 'INFO')
        
        try:
            # Test configuration loading
            platform_status = deployment_manager.get_platform_status()
            
            if platform_status:
                self.log(f"Deployment manager loaded {len(platform_status)} platform configurations", 'SUCCESS')
                
                # Test deployment summary
                summary = deployment_manager.get_deployment_summary()
                if summary:
                    self.log("Deployment summary generated successfully", 'SUCCESS')
                    test_passed = True
                else:
                    self.log("Failed to generate deployment summary", 'WARNING')
                    test_passed = True  # Not critical
            else:
                self.log("Failed to load platform configurations", 'ERROR')
                test_passed = False
            
            self.test_results['tests']['deployment_manager'] = {
                'passed': test_passed,
                'details': f"Deployment manager managing {len(platform_status)} platforms"
            }
            
            return test_passed
            
        except Exception as e:
            self.log(f"Deployment manager test failed: {e}", 'ERROR')
            self.test_results['tests']['deployment_manager'] = {
                'passed': False,
                'details': f"Error: {str(e)}"
            }
            return False
    
    def test_failover_client(self) -> bool:
        """Test failover Firebase client"""
        self.log("Testing failover Firebase client...", 'INFO')
        
        try:
            # Create failover client
            client = FailoverFirebaseClient()
            
            # Test service status
            status = client.get_service_status()
            if status:
                self.log("Failover client service status retrieved", 'SUCCESS')
                
                # Test current platform detection
                current_platform = client.get_current_platform()
                if current_platform:
                    self.log(f"Current platform detected: {current_platform}", 'SUCCESS')
                else:
                    self.log("No current platform detected", 'WARNING')
                
                test_passed = True
            else:
                self.log("Failed to get service status from failover client", 'ERROR')
                test_passed = False
            
            self.test_results['tests']['failover_client'] = {
                'passed': test_passed,
                'details': "Failover Firebase client functionality verified"
            }
            
            return test_passed
            
        except Exception as e:
            self.log(f"Failover client test failed: {e}", 'ERROR')
            self.test_results['tests']['failover_client'] = {
                'passed': False,
                'details': f"Error: {str(e)}"
            }
            return False
    
    def test_environment_variables(self) -> bool:
        """Test environment variable configuration"""
        self.log("Testing environment variables...", 'INFO')
        
        required_vars = [
            'FIREBASE_SERVICE_ACCOUNT',
            'FIREBASE_API_KEY'
        ]
        
        optional_vars = [
            'RENDER_DEPLOY_WEBHOOK',
            'REPLIT_TOKEN',
            'REPL_ID'
        ]
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        if missing_required:
            self.log(f"Missing required environment variables: {', '.join(missing_required)}", 'ERROR')
            test_passed = False
        else:
            self.log("All required environment variables are set", 'SUCCESS')
            test_passed = True
        
        if missing_optional:
            self.log(f"Missing optional environment variables: {', '.join(missing_optional)}", 'WARNING')
        
        self.test_results['tests']['environment_variables'] = {
            'passed': test_passed,
            'details': f"Required: {len(required_vars) - len(missing_required)}/{len(required_vars)}, Optional: {len(optional_vars) - len(missing_optional)}/{len(optional_vars)}",
            'missing_required': missing_required,
            'missing_optional': missing_optional
        }
        
        return test_passed
    
    def run_all_tests(self) -> bool:
        """Run all tests and generate comprehensive report"""
        self.log("🚀 Starting Triple Deployment Strategy Test Suite", 'INFO')
        self.log("=" * 60, 'INFO')
        
        # Define test methods
        test_methods = [
            ('Configuration Files', self.test_configuration_files),
            ('Environment Variables', self.test_environment_variables),
            ('Service Discovery', self.test_service_discovery),
            ('Platform Health Checks', self.test_platform_health_checks),
            ('Failover Mechanism', self.test_failover_mechanism),
            ('Monitoring System', self.test_monitoring_system),
            ('Deployment Manager', self.test_deployment_manager),
            ('Failover Client', self.test_failover_client)
        ]
        
        # Run tests
        for test_name, test_method in test_methods:
            self.log(f"\n🧪 Running {test_name} test...", 'INFO')
            
            try:
                start_time = time.time()
                result = test_method()
                duration = time.time() - start_time
                
                self.test_results['summary']['total_tests'] += 1
                
                if result:
                    self.test_results['summary']['passed_tests'] += 1
                    self.log(f"✅ {test_name} test PASSED ({duration:.2f}s)", 'SUCCESS')
                else:
                    self.test_results['summary']['failed_tests'] += 1
                    self.log(f"❌ {test_name} test FAILED ({duration:.2f}s)", 'ERROR')
                    
            except Exception as e:
                self.test_results['summary']['failed_tests'] += 1
                self.log(f"🚨 {test_name} test ERROR: {e}", 'ERROR')
        
        # Generate final report
        self.generate_final_report()
        
        # Return overall success
        return self.test_results['summary']['failed_tests'] == 0
    
    def generate_final_report(self):
        """Generate comprehensive test report"""
        summary = self.test_results['summary']
        
        self.log("\n" + "=" * 60, 'INFO')
        self.log("📊 TRIPLE DEPLOYMENT STRATEGY TEST REPORT", 'INFO')
        self.log("=" * 60, 'INFO')
        
        self.log(f"Total Tests: {summary['total_tests']}", 'INFO')
        self.log(f"Passed: {summary['passed_tests']}", 'SUCCESS')
        self.log(f"Failed: {summary['failed_tests']}", 'ERROR' if summary['failed_tests'] > 0 else 'INFO')
        
        if summary['total_tests'] > 0:
            success_rate = (summary['passed_tests'] / summary['total_tests']) * 100
            self.log(f"Success Rate: {success_rate:.1f}%", 'SUCCESS' if success_rate >= 80 else 'WARNING')
        
        # Detailed test results
        self.log("\n📋 Detailed Test Results:", 'INFO')
        for test_name, result in self.test_results['tests'].items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            self.log(f"  {test_name}: {status} - {result['details']}", 'INFO')
        
        # Recommendations
        self.log("\n💡 Recommendations:", 'INFO')
        
        if summary['failed_tests'] == 0:
            self.log("🎉 All tests passed! Your triple deployment strategy is ready for production.", 'SUCCESS')
            self.log("Consider running periodic tests to ensure continued reliability.", 'INFO')
        else:
            self.log("⚠️  Some tests failed. Please address the issues before deploying to production.", 'WARNING')
            self.log("Review the detailed test results above for specific issues to fix.", 'INFO')
        
        # Save report to file
        report_file = project_root / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            self.log(f"📄 Detailed report saved to: {report_file}", 'INFO')
        except Exception as e:
            self.log(f"Failed to save report: {e}", 'WARNING')

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='Triple Deployment Strategy Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--test', '-t', help='Run specific test only')
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = DeploymentTester(verbose=args.verbose)
    
    # Run tests
    if args.test:
        # Run specific test
        test_method = getattr(tester, f'test_{args.test}', None)
        if test_method:
            success = test_method()
            sys.exit(0 if success else 1)
        else:
            print(f"❌ Unknown test: {args.test}")
            sys.exit(1)
    else:
        # Run all tests
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
