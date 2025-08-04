"""
Service Discovery Module - DEPRECATED STUB
This module has been deprecated in favor of Firebase direct integration.
This stub exists only to prevent import errors in legacy code.
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ServiceEndpoint:
    """Deprecated service endpoint class - stub only"""
    name: str = "firebase"
    url: str = "https://firebase.google.com"
    priority: int = 1
    timeout: int = 30
    retry_attempts: int = 3
    is_healthy: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'url': self.url,
            'priority': self.priority,
            'timeout': self.timeout,
            'retry_attempts': self.retry_attempts,
            'is_healthy': self.is_healthy
        }

class ServiceDiscovery:
    """
    DEPRECATED: Service Discovery Class - Stub Implementation
    
    This class has been deprecated in favor of Firebase direct integration.
    All methods return default/stub values to prevent import errors.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.warning("ServiceDiscovery is deprecated - using Firebase direct integration")
        
        # Stub properties
        self.endpoints = [ServiceEndpoint()]
        self.current_endpoint = ServiceEndpoint()
        self._failover_callbacks: List[Callable] = []
    
    def select_endpoint(self) -> Optional[ServiceEndpoint]:
        """Return default Firebase endpoint"""
        return ServiceEndpoint()
    
    def make_request(self, method: str, path: str, **kwargs) -> Any:
        """Stub method - returns mock response"""
        class MockResponse:
            status_code = 200
            text = "OK"
            
            def json(self):
                return {"status": "ok", "message": "Firebase direct integration"}
        
        return MockResponse()
    
    def add_failover_callback(self, callback: Callable):
        """Add failover callback - stub implementation"""
        self._failover_callbacks.append(callback)
        self.logger.info("Failover callback registered (stub)")
    
    def load_configuration_data(self) -> Dict[str, Any]:
        """Return stub configuration data"""
        return {
            "backend_type": "firebase",
            "status": "active",
            "message": "Using Firebase direct integration"
        }
    
    def get_healthy_endpoints(self) -> List[ServiceEndpoint]:
        """Return list of healthy endpoints - stub"""
        return [ServiceEndpoint()]
    
    def check_endpoint_health(self, endpoint: ServiceEndpoint) -> bool:
        """Check endpoint health - always returns True for stub"""
        return True

# Global instance for backward compatibility
service_discovery = ServiceDiscovery()

# Export for backward compatibility
__all__ = ['ServiceDiscovery', 'ServiceEndpoint', 'service_discovery']
