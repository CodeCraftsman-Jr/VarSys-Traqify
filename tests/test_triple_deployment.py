"""
Comprehensive Test Suite for Triple Deployment Strategy
Tests service discovery, failover, monitoring, and deployment management
"""

import unittest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests
import tempfile
import os
from pathlib import Path

# Import the modules to test
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.core.service_discovery import ServiceDiscovery, ServiceEndpoint
from src.core.platform_monitor import PlatformMonitor
from src.core.deployment_manager import DeploymentManager
from src.core.failover_firebase_client import FailoverFirebaseClient

class TestServiceDiscovery(unittest.TestCase):
    """Test service discovery and failover functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_service_discovery.json"
        
        # Create test configuration
        test_config = {
            "endpoints": [
                {
                    "name": "render",
                    "url": "https://test-render.com",
                    "priority": 1,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "platform_type": "container",
                    "health_check_path": "/",
                    "ping_path": "/ping"
                },
                {
                    "name": "appwrite",
                    "url": "https://test-appwrite.com/executions",
                    "priority": 2,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "platform_type": "serverless",
                    "health_check_path": "/",
                    "ping_path": "/ping"
                },
                {
                    "name": "replit",
                    "url": "https://test-replit.com",
                    "priority": 3,
                    "timeout": 45,
                    "retry_attempts": 2,
                    "platform_type": "container",
                    "health_check_path": "/",
                    "ping_path": "/ping"
                }
            ],
            "health_check_interval": 60,
            "platform_specific": {
                "appwrite": {
                    "project_id": "test-project-id"
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        self.service_discovery = ServiceDiscovery(self.config_file)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_configuration(self):
        """Test configuration loading"""
        self.assertEqual(len(self.service_discovery.endpoints), 3)
        self.assertEqual(self.service_discovery.endpoints[0].name, "render")
        self.assertEqual(self.service_discovery.endpoints[0].priority, 1)
        self.assertEqual(self.service_discovery.endpoints[1].platform_type, "serverless")
    
    def test_endpoint_selection(self):
        """Test endpoint selection logic"""
        # All endpoints healthy - should select highest priority
        for endpoint in self.service_discovery.endpoints:
            endpoint.is_healthy = True
        
        selected = self.service_discovery.select_endpoint()
        self.assertEqual(selected.name, "render")
        
        # Primary unhealthy - should select backup
        self.service_discovery.endpoints[0].is_healthy = False
        selected = self.service_discovery.select_endpoint()
        self.assertEqual(selected.name, "appwrite")
        
        # Primary and backup unhealthy - should select fallback
        self.service_discovery.endpoints[1].is_healthy = False
        selected = self.service_discovery.select_endpoint()
        self.assertEqual(selected.name, "replit")
    
    @patch('requests.get')
    def test_health_check_standard(self, mock_get):
        """Test health check for standard platforms (Render, Replit)"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'healthy',
            'firebase_initialized': True,
            'environment': {'platform': 'render'}
        }
        mock_get.return_value = mock_response
        
        endpoint = self.service_discovery.endpoints[0]  # Render
        result = self.service_discovery.check_endpoint_health(endpoint)
        
        self.assertTrue(result)
        self.assertTrue(endpoint.is_healthy)
        self.assertIsNotNone(endpoint.last_check)
    
    @patch('requests.post')
    def test_health_check_appwrite(self, mock_post):
        """Test health check for Appwrite Functions"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'healthy',
            'firebase_initialized': True,
            'platform': 'appwrite'
        }
        mock_post.return_value = mock_response
        
        endpoint = self.service_discovery.endpoints[1]  # Appwrite
        result = self.service_discovery.check_endpoint_health(endpoint)
        
        self.assertTrue(result)
        self.assertTrue(endpoint.is_healthy)
        
        # Verify Appwrite-specific request format
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('json', call_args.kwargs)
        self.assertEqual(call_args.kwargs['json']['path'], '/')
        self.assertEqual(call_args.kwargs['json']['method'], 'GET')
    
    @patch('requests.request')
    def test_make_request_standard(self, mock_request):
        """Test making requests to standard platforms"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        # Set render as current endpoint
        self.service_discovery.current_endpoint = self.service_discovery.endpoints[0]
        
        response = self.service_discovery.make_request('GET', '/test')
        
        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once()
        
        # Verify standard request format
        call_args = mock_request.call_args
        self.assertEqual(call_args.args[0], 'GET')
        self.assertEqual(call_args.args[1], 'https://test-render.com/test')
    
    @patch('requests.post')
    def test_make_request_appwrite(self, mock_post):
        """Test making requests to Appwrite Functions"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Set appwrite as current endpoint
        self.service_discovery.current_endpoint = self.service_discovery.endpoints[1]
        
        response = self.service_discovery.make_request('POST', '/auth/signin', json={'email': 'test@test.com'})
        
        self.assertEqual(response.status_code, 200)
        mock_post.assert_called_once()
        
        # Verify Appwrite request format
        call_args = mock_post.call_args
        self.assertEqual(call_args.args[0], 'https://test-appwrite.com/executions')
        self.assertIn('json', call_args.kwargs)
        
        request_body = call_args.kwargs['json']
        self.assertEqual(request_body['path'], '/auth/signin')
        self.assertEqual(request_body['method'], 'POST')
        self.assertIn('body', request_body)
    
    def test_failover_callback(self):
        """Test failover callback mechanism"""
        callback_called = False
        old_endpoint = None
        new_endpoint = None
        
        def test_callback(old, new):
            nonlocal callback_called, old_endpoint, new_endpoint
            callback_called = True
            old_endpoint = old
            new_endpoint = new
        
        self.service_discovery.add_failover_callback(test_callback)
        
        # Trigger failover
        self.service_discovery.current_endpoint = self.service_discovery.endpoints[0]
        self.service_discovery.endpoints[0].is_healthy = False
        self.service_discovery.select_endpoint()
        
        self.assertTrue(callback_called)
        self.assertEqual(old_endpoint.name, "render")
        self.assertEqual(new_endpoint.name, "appwrite")

class TestPlatformMonitor(unittest.TestCase):
    """Test platform monitoring and alerting"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_monitor_config.json"
        self.metrics_file = Path(self.temp_dir) / "test_metrics.json"
        
        self.monitor = PlatformMonitor(self.config_file)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_record_request_success(self):
        """Test recording successful requests"""
        self.monitor.record_request('render', True, 0.5)
        
        metrics = self.monitor.platform_metrics['render']
        self.assertEqual(metrics.total_requests, 1)
        self.assertEqual(metrics.successful_requests, 1)
        self.assertEqual(metrics.failed_requests, 0)
        self.assertEqual(metrics.consecutive_failures, 0)
        self.assertAlmostEqual(metrics.avg_response_time, 0.5)
    
    def test_record_request_failure(self):
        """Test recording failed requests"""
        self.monitor.record_request('render', False, 2.0)
        
        metrics = self.monitor.platform_metrics['render']
        self.assertEqual(metrics.total_requests, 1)
        self.assertEqual(metrics.successful_requests, 0)
        self.assertEqual(metrics.failed_requests, 1)
        self.assertEqual(metrics.consecutive_failures, 1)
        self.assertEqual(metrics.error_rate, 1.0)
    
    def test_alert_creation(self):
        """Test alert creation and callbacks"""
        alert_received = None
        
        def alert_callback(alert):
            nonlocal alert_received
            alert_received = alert
        
        self.monitor.add_alert_callback(alert_callback)
        
        # Trigger high error rate alert
        for _ in range(10):
            self.monitor.record_request('render', False, 1.0)
        
        self.assertIsNotNone(alert_received)
        self.assertEqual(alert_received['platform'], 'render')
        self.assertEqual(alert_received['type'], 'high_error_rate')
    
    def test_failover_recording(self):
        """Test failover event recording"""
        self.monitor.record_failover('render', 'appwrite', 'Health check failed')
        
        self.assertEqual(len(self.monitor.failover_events), 1)
        event = self.monitor.failover_events[0]
        self.assertEqual(event.from_platform, 'render')
        self.assertEqual(event.to_platform, 'appwrite')
        self.assertEqual(event.reason, 'Health check failed')
    
    def test_platform_health_summary(self):
        """Test platform health summary generation"""
        # Add some test data
        self.monitor.record_request('render', True, 0.5)
        self.monitor.record_request('appwrite', False, 2.0)
        
        summary = self.monitor.get_platform_health_summary()
        
        self.assertIn('timestamp', summary)
        self.assertIn('platforms', summary)
        self.assertIn('overall', summary)
        
        self.assertIn('render', summary['platforms'])
        self.assertIn('appwrite', summary['platforms'])
        
        render_data = summary['platforms']['render']
        self.assertTrue(render_data['healthy'])
        self.assertEqual(render_data['total_requests'], 1)

class TestDeploymentManager(unittest.TestCase):
    """Test deployment management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_deployment_config.json"
        
        self.deployment_manager = DeploymentManager(self.config_file)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_configuration_loading(self):
        """Test deployment configuration loading"""
        self.assertIn('render', self.deployment_manager.deployment_configs)
        self.assertIn('appwrite', self.deployment_manager.deployment_configs)
        self.assertIn('replit', self.deployment_manager.deployment_configs)
        
        render_config = self.deployment_manager.deployment_configs['render']
        self.assertEqual(render_config.platform, 'render')
        self.assertTrue(render_config.enabled)
    
    def test_platform_status(self):
        """Test platform status retrieval"""
        status = self.deployment_manager.get_platform_status()
        
        self.assertIn('render', status)
        self.assertIn('appwrite', status)
        self.assertIn('replit', status)
        
        for platform, config in status.items():
            self.assertIn('enabled', config)
            self.assertIn('auto_deploy', config)
            self.assertIn('url', config)

class TestFailoverFirebaseClient(unittest.TestCase):
    """Test failover Firebase client functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock service discovery
        self.mock_service_discovery = Mock()
        self.mock_endpoint = Mock()
        self.mock_endpoint.name = 'render'
        self.mock_endpoint.url = 'https://test-render.com'
        self.mock_service_discovery.current_endpoint = self.mock_endpoint
        
        with patch('src.core.failover_firebase_client.service_discovery', self.mock_service_discovery):
            self.client = FailoverFirebaseClient()
    
    @patch('src.core.failover_firebase_client.service_discovery')
    def test_make_request_success(self, mock_service_discovery):
        """Test successful request through failover client"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'user': {'uid': 'test-uid', 'email': 'test@test.com'}
        }
        
        mock_service_discovery.make_request.return_value = mock_response
        mock_service_discovery.current_endpoint = self.mock_endpoint
        
        success, result = self.client._make_request('/auth/signin', 'POST', {'email': 'test@test.com'})
        
        self.assertTrue(success)
        self.assertIn('_platform', result)
        self.assertEqual(result['_platform'], 'render')
    
    @patch('src.core.failover_firebase_client.service_discovery')
    def test_make_request_failure(self, mock_service_discovery):
        """Test failed request handling"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'error': 'Internal server error'}
        
        mock_service_discovery.make_request.return_value = mock_response
        mock_service_discovery.current_endpoint = self.mock_endpoint
        
        success, result = self.client._make_request('/auth/signin', 'POST', {'email': 'test@test.com'})
        
        self.assertFalse(success)
        self.assertIn('error', result)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete triple deployment system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test configurations
        self.service_config_file = Path(self.temp_dir) / "service_discovery.json"
        self.monitor_config_file = Path(self.temp_dir) / "monitor.json"
        self.deployment_config_file = Path(self.temp_dir) / "deployment.json"
        
        # Initialize components
        self.service_discovery = ServiceDiscovery(self.service_config_file)
        self.monitor = PlatformMonitor(self.monitor_config_file)
        self.deployment_manager = DeploymentManager(self.deployment_config_file)
    
    def tearDown(self):
        """Clean up integration test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_failover(self):
        """Test complete end-to-end failover scenario"""
        # Set up initial state - all platforms healthy
        for endpoint in self.service_discovery.endpoints:
            endpoint.is_healthy = True
        
        # Primary should be selected
        selected = self.service_discovery.select_endpoint()
        self.assertEqual(selected.priority, 1)
        
        # Simulate primary failure
        primary = self.service_discovery.endpoints[0]
        primary.is_healthy = False
        
        # Should failover to backup
        selected = self.service_discovery.select_endpoint()
        self.assertEqual(selected.priority, 2)
        
        # Verify monitoring recorded the event
        # (In real implementation, this would be triggered by the failover callback)
        self.monitor.record_failover(primary.name, selected.name, "Primary platform failed")
        
        self.assertEqual(len(self.monitor.failover_events), 1)
        event = self.monitor.failover_events[0]
        self.assertEqual(event.from_platform, primary.name)
        self.assertEqual(event.to_platform, selected.name)
    
    def test_monitoring_integration(self):
        """Test monitoring integration with service discovery"""
        # Record some requests
        platforms = ['render', 'appwrite', 'replit']
        
        for platform in platforms:
            # Simulate successful requests
            for _ in range(5):
                self.monitor.record_request(platform, True, 0.5)
            
            # Simulate some failures
            for _ in range(2):
                self.monitor.record_request(platform, False, 2.0)
        
        # Get health summary
        summary = self.monitor.get_platform_health_summary()
        
        self.assertEqual(summary['overall']['total_platforms'], 3)
        self.assertEqual(summary['overall']['total_requests'], 21)  # 7 requests per platform
        
        # Verify platform-specific data
        for platform in platforms:
            platform_data = summary['platforms'][platform]
            self.assertEqual(platform_data['total_requests'], 7)
            self.assertEqual(platform_data['successful_requests'], 5)
            self.assertEqual(platform_data['failed_requests'], 2)

def run_comprehensive_tests():
    """Run all tests and generate a comprehensive report"""
    print("🧪 Running Triple Deployment Strategy Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestServiceDiscovery,
        TestPlatformMonitor,
        TestDeploymentManager,
        TestFailoverFirebaseClient,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY REPORT")
    print("=" * 60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED! Triple deployment strategy is ready for production.")
    else:
        print("\n⚠️  Some tests failed. Please review and fix issues before deployment.")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
