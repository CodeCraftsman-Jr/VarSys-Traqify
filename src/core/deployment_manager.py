"""
Unified Deployment Manager for Triple Deployment Strategy
Manages deployments across Render, Appwrite Functions, and Replit platforms
"""

import os
import json
import logging
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import tempfile
import shutil

from PySide6.QtCore import QObject, Signal, QThread

logger = logging.getLogger(__name__)

@dataclass
class DeploymentConfig:
    """Configuration for a deployment platform"""
    platform: str
    name: str
    url: Optional[str]
    enabled: bool
    auto_deploy: bool
    deployment_script: str
    environment_variables: Dict[str, str]
    health_check_endpoint: str
    deployment_timeout: int = 600  # 10 minutes

@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    platform: str
    success: bool
    message: str
    url: Optional[str] = None
    deployment_id: Optional[str] = None
    duration: float = 0.0
    logs: List[str] = None

class DeploymentWorker(QThread):
    """Worker thread for deployment operations"""
    
    deployment_started = Signal(str)  # platform
    deployment_progress = Signal(str, str)  # platform, message
    deployment_completed = Signal(str, bool, str)  # platform, success, message
    
    def __init__(self, platform: str, config: DeploymentConfig, operation: str = 'deploy'):
        super().__init__()
        self.platform = platform
        self.config = config
        self.operation = operation
        self.logger = logging.getLogger(f"{__name__}.DeploymentWorker")
    
    def run(self):
        """Execute deployment operation"""
        try:
            self.deployment_started.emit(self.platform)
            
            if self.operation == 'deploy':
                success, message = self.deploy()
            elif self.operation == 'test':
                success, message = self.test_deployment()
            else:
                success, message = False, f"Unknown operation: {self.operation}"
            
            self.deployment_completed.emit(self.platform, success, message)
            
        except Exception as e:
            error_msg = f"Deployment error: {str(e)}"
            self.logger.error(error_msg)
            self.deployment_completed.emit(self.platform, False, error_msg)
    
    def deploy(self) -> Tuple[bool, str]:
        """Execute deployment for the platform"""
        try:
            if self.platform == 'render':
                return self.deploy_render()
            elif self.platform == 'appwrite':
                return self.deploy_appwrite()
            elif self.platform == 'replit':
                return self.deploy_replit()
            else:
                return False, f"Unknown platform: {self.platform}"
                
        except Exception as e:
            return False, f"Deployment failed: {str(e)}"
    
    def deploy_render(self) -> Tuple[bool, str]:
        """Deploy to Render platform"""
        self.deployment_progress.emit(self.platform, "Triggering Render deployment...")
        
        # Render deployments are typically triggered by git push
        # We can trigger a manual deployment via webhook if configured
        webhook_url = self.config.environment_variables.get('RENDER_DEPLOY_WEBHOOK')
        
        if webhook_url:
            try:
                response = requests.post(webhook_url, timeout=30)
                if response.status_code == 200:
                    return True, "Render deployment triggered successfully"
                else:
                    return False, f"Render deployment trigger failed: HTTP {response.status_code}"
            except Exception as e:
                return False, f"Failed to trigger Render deployment: {str(e)}"
        else:
            return True, "Render deployment will be triggered by git push (auto-deploy enabled)"
    
    def deploy_appwrite(self) -> Tuple[bool, str]:
        """Deploy to Appwrite Functions"""
        self.deployment_progress.emit(self.platform, "Deploying to Appwrite Functions...")
        
        try:
            # Change to appwrite_functions directory
            appwrite_dir = Path("appwrite_functions")
            if not appwrite_dir.exists():
                return False, "Appwrite functions directory not found"
            
            # Execute deployment script
            if os.name == 'nt':  # Windows
                script_path = appwrite_dir / "deploy.bat"
                cmd = [str(script_path)]
            else:  # Unix/Linux/Mac
                script_path = appwrite_dir / "deploy.sh"
                cmd = ["bash", str(script_path)]
            
            if not script_path.exists():
                return False, f"Deployment script not found: {script_path}"
            
            # Run deployment script
            result = subprocess.run(
                cmd,
                cwd=appwrite_dir,
                capture_output=True,
                text=True,
                timeout=self.config.deployment_timeout
            )
            
            if result.returncode == 0:
                return True, "Appwrite Functions deployment completed successfully"
            else:
                error_msg = result.stderr or result.stdout or "Unknown deployment error"
                return False, f"Appwrite deployment failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Appwrite deployment timed out"
        except Exception as e:
            return False, f"Appwrite deployment error: {str(e)}"
    
    def deploy_replit(self) -> Tuple[bool, str]:
        """Deploy to Replit platform"""
        self.deployment_progress.emit(self.platform, "Deploying to Replit...")
        
        # Replit deployments are typically automatic when files are updated
        # We can trigger a restart via Replit API if credentials are available
        replit_token = self.config.environment_variables.get('REPLIT_TOKEN')
        repl_id = self.config.environment_variables.get('REPL_ID')
        
        if replit_token and repl_id:
            try:
                # Use Replit API to restart the repl
                headers = {
                    'Authorization': f'Bearer {replit_token}',
                    'Content-Type': 'application/json'
                }
                
                restart_url = f"https://replit.com/data/repls/{repl_id}/restart"
                response = requests.post(restart_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    return True, "Replit deployment completed successfully"
                else:
                    return False, f"Replit restart failed: HTTP {response.status_code}"
                    
            except Exception as e:
                return False, f"Failed to restart Replit: {str(e)}"
        else:
            return True, "Replit deployment will be automatic (files updated)"
    
    def test_deployment(self) -> Tuple[bool, str]:
        """Test deployment health"""
        try:
            if not self.config.url:
                return False, "No URL configured for health check"
            
            health_url = f"{self.config.url.rstrip('/')}{self.config.health_check_endpoint}"
            
            # Special handling for Appwrite Functions
            if self.platform == 'appwrite':
                headers = {
                    'Content-Type': 'application/json',
                    'X-Appwrite-Project': '6874905d00119a86f907'
                }
                body = {
                    'path': self.config.health_check_endpoint,
                    'method': 'GET'
                }
                response = requests.post(health_url, json=body, headers=headers, timeout=30)
            else:
                response = requests.get(health_url, timeout=30)
            
            if response.status_code == 200:
                return True, f"Health check passed for {self.platform}"
            else:
                return False, f"Health check failed: HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Health check error: {str(e)}"

class DeploymentManager(QObject):
    """
    Unified deployment manager for all platforms
    Coordinates deployments across Render, Appwrite Functions, and Replit
    """
    
    # Signals
    deployment_started = Signal(str)  # platform
    deployment_progress = Signal(str, str)  # platform, message
    deployment_completed = Signal(str, bool, str)  # platform, success, message
    all_deployments_completed = Signal(dict)  # results summary
    
    def __init__(self, config_file: Optional[Path] = None):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.config_file = config_file or Path("deployment_config.json")
        self.deployment_configs: Dict[str, DeploymentConfig] = {}
        self.active_workers: Dict[str, DeploymentWorker] = {}
        self.deployment_results: Dict[str, DeploymentResult] = {}
        
        # Load configuration
        self.load_configuration()
        
        self.logger.info("DeploymentManager initialized")
    
    def load_configuration(self):
        """Load deployment configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                for platform_name, platform_config in config_data.get('platforms', {}).items():
                    self.deployment_configs[platform_name] = DeploymentConfig(**platform_config)
                
                self.logger.info(f"Loaded configuration for {len(self.deployment_configs)} platforms")
            else:
                self.create_default_configuration()
                
        except Exception as e:
            self.logger.error(f"Failed to load deployment configuration: {e}")
            self.create_default_configuration()
    
    def create_default_configuration(self):
        """Create default deployment configuration"""
        default_config = {
            'platforms': {
                'render': {
                    'platform': 'render',
                    'name': 'Render Production',
                    'url': 'https://traqify-api.onrender.com',
                    'enabled': True,
                    'auto_deploy': True,
                    'deployment_script': 'git push origin main',
                    'environment_variables': {
                        'RENDER_DEPLOY_WEBHOOK': ''
                    },
                    'health_check_endpoint': '/',
                    'deployment_timeout': 600
                },
                'appwrite': {
                    'platform': 'appwrite',
                    'name': 'Appwrite Functions',
                    'url': 'https://fra.cloud.appwrite.io/v1/functions/traqify-api/executions',
                    'enabled': True,
                    'auto_deploy': False,
                    'deployment_script': 'appwrite_functions/deploy.sh',
                    'environment_variables': {
                        'APPWRITE_PROJECT_ID': '6874905d00119a86f907',
                        'APPWRITE_FUNCTION_ID': 'traqify-api'
                    },
                    'health_check_endpoint': '/',
                    'deployment_timeout': 300
                },
                'replit': {
                    'platform': 'replit',
                    'name': 'Replit Development',
                    'url': 'https://replit.com/@YourUsername/YourReplName',
                    'enabled': True,
                    'auto_deploy': True,
                    'deployment_script': 'replit_backend/start.sh',
                    'environment_variables': {
                        'REPLIT_TOKEN': '',
                        'REPL_ID': ''
                    },
                    'health_check_endpoint': '/',
                    'deployment_timeout': 180
                }
            },
            'global_settings': {
                'parallel_deployments': True,
                'deployment_order': ['render', 'appwrite', 'replit'],
                'stop_on_failure': False,
                'health_check_after_deploy': True,
                'rollback_on_failure': False
            }
        }
        
        # Save default configuration
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            # Load the default configuration
            for platform_name, platform_config in default_config['platforms'].items():
                self.deployment_configs[platform_name] = DeploymentConfig(**platform_config)
                
            self.logger.info("Created default deployment configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to save default configuration: {e}")
    
    def deploy_platform(self, platform: str) -> bool:
        """Deploy to a specific platform"""
        if platform not in self.deployment_configs:
            self.logger.error(f"Unknown platform: {platform}")
            return False
        
        config = self.deployment_configs[platform]
        if not config.enabled:
            self.logger.info(f"Platform {platform} is disabled, skipping deployment")
            return False
        
        # Create and start deployment worker
        worker = DeploymentWorker(platform, config, 'deploy')
        worker.deployment_started.connect(self.deployment_started.emit)
        worker.deployment_progress.connect(self.deployment_progress.emit)
        worker.deployment_completed.connect(self._on_deployment_completed)
        
        self.active_workers[platform] = worker
        worker.start()
        
        return True
    
    def deploy_all_platforms(self) -> bool:
        """Deploy to all enabled platforms"""
        enabled_platforms = [
            name for name, config in self.deployment_configs.items()
            if config.enabled
        ]
        
        if not enabled_platforms:
            self.logger.warning("No enabled platforms found")
            return False
        
        self.deployment_results.clear()
        
        for platform in enabled_platforms:
            self.deploy_platform(platform)
        
        return True
    
    def test_platform(self, platform: str) -> bool:
        """Test deployment health for a specific platform"""
        if platform not in self.deployment_configs:
            self.logger.error(f"Unknown platform: {platform}")
            return False
        
        config = self.deployment_configs[platform]
        
        # Create and start test worker
        worker = DeploymentWorker(platform, config, 'test')
        worker.deployment_completed.connect(self._on_test_completed)
        
        worker.start()
        return True
    
    def _on_deployment_completed(self, platform: str, success: bool, message: str):
        """Handle deployment completion"""
        if platform in self.active_workers:
            worker = self.active_workers[platform]
            worker.deleteLater()
            del self.active_workers[platform]
        
        # Store result
        self.deployment_results[platform] = DeploymentResult(
            platform=platform,
            success=success,
            message=message,
            url=self.deployment_configs[platform].url
        )
        
        self.deployment_completed.emit(platform, success, message)
        
        # Check if all deployments are complete
        if not self.active_workers:
            self.all_deployments_completed.emit(self.get_deployment_summary())
    
    def _on_test_completed(self, platform: str, success: bool, message: str):
        """Handle test completion"""
        self.logger.info(f"Test completed for {platform}: {success} - {message}")
    
    def get_deployment_summary(self) -> Dict[str, Any]:
        """Get summary of deployment results"""
        total_platforms = len(self.deployment_results)
        successful_platforms = sum(1 for result in self.deployment_results.values() if result.success)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_platforms': total_platforms,
            'successful_platforms': successful_platforms,
            'failed_platforms': total_platforms - successful_platforms,
            'success_rate': (successful_platforms / max(total_platforms, 1)) * 100,
            'results': {
                platform: {
                    'success': result.success,
                    'message': result.message,
                    'url': result.url
                }
                for platform, result in self.deployment_results.items()
            }
        }
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all configured platforms"""
        return {
            platform: {
                'enabled': config.enabled,
                'auto_deploy': config.auto_deploy,
                'url': config.url,
                'last_deployment': self.deployment_results.get(platform)
            }
            for platform, config in self.deployment_configs.items()
        }

# Global deployment manager instance
deployment_manager = DeploymentManager()
