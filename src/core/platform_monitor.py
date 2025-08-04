"""
Platform Monitoring and Health Check System
Provides comprehensive monitoring for the triple deployment strategy
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer

# Service discovery removed - Firebase only architecture

logger = logging.getLogger(__name__)

@dataclass
class HealthMetric:
    """Health metric data point"""
    timestamp: datetime
    platform: str
    response_time: float
    status_code: int
    is_healthy: bool
    error_message: Optional[str] = None
    platform_info: Optional[Dict[str, Any]] = None

@dataclass
class FailoverEvent:
    """Failover event record"""
    timestamp: datetime
    from_platform: Optional[str]
    to_platform: str
    reason: str
    duration: float  # seconds since last failover
    success: bool

@dataclass
class PlatformStats:
    """Platform statistics"""
    platform: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    uptime_percentage: float
    last_seen: Optional[datetime]
    failover_count: int

class PlatformMonitor(QObject):
    """
    Comprehensive platform monitoring system
    Tracks health, performance, and failover events across all platforms
    """
    
    # Signals
    health_updated = Signal(dict)  # Health status update
    failover_detected = Signal(dict)  # Failover event
    platform_down = Signal(str)  # Platform went down
    platform_up = Signal(str)  # Platform came back up
    all_platforms_down = Signal()  # Critical: all platforms down
    
    def __init__(self, config_file: Optional[Path] = None):
        super().__init__()
        
        self.config_file = config_file or Path("platform_monitor_config.json")
        self.metrics_file = Path("platform_metrics.json")
        
        # Configuration
        self.monitoring_interval = 30  # seconds
        self.metrics_retention_days = 7
        self.alert_threshold = 3  # consecutive failures before alert
        
        # Data storage
        self.health_metrics: List[HealthMetric] = []
        self.failover_events: List[FailoverEvent] = []
        self.platform_stats: Dict[str, PlatformStats] = {}
        self.alert_callbacks: List[Callable] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.last_platform = None
        self.consecutive_failures = {}
        
        # Load configuration and historical data
        self.load_configuration()
        self.load_metrics()
        
        # Service discovery callbacks removed - Firebase only architecture
        
        # Start monitoring
        self.start_monitoring()
        
        logger.info("Platform monitor initialized")
    
    def load_configuration(self):
        """Load monitoring configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.monitoring_interval = config.get('monitoring_interval', 30)
                self.metrics_retention_days = config.get('metrics_retention_days', 7)
                self.alert_threshold = config.get('alert_threshold', 3)
                
                logger.info("Loaded monitoring configuration")
            else:
                self.save_configuration()
                
        except Exception as e:
            logger.error(f"Failed to load monitoring configuration: {e}")
    
    def save_configuration(self):
        """Save monitoring configuration"""
        try:
            config = {
                'monitoring_interval': self.monitoring_interval,
                'metrics_retention_days': self.metrics_retention_days,
                'alert_threshold': self.alert_threshold,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save monitoring configuration: {e}")
    
    def load_metrics(self):
        """Load historical metrics"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load health metrics
                for metric_data in data.get('health_metrics', []):
                    metric = HealthMetric(
                        timestamp=datetime.fromisoformat(metric_data['timestamp']),
                        platform=metric_data['platform'],
                        response_time=metric_data['response_time'],
                        status_code=metric_data['status_code'],
                        is_healthy=metric_data['is_healthy'],
                        error_message=metric_data.get('error_message'),
                        platform_info=metric_data.get('platform_info')
                    )
                    self.health_metrics.append(metric)
                
                # Load failover events
                for event_data in data.get('failover_events', []):
                    event = FailoverEvent(
                        timestamp=datetime.fromisoformat(event_data['timestamp']),
                        from_platform=event_data.get('from_platform'),
                        to_platform=event_data['to_platform'],
                        reason=event_data['reason'],
                        duration=event_data['duration'],
                        success=event_data['success']
                    )
                    self.failover_events.append(event)
                
                # Load platform stats
                for platform, stats_data in data.get('platform_stats', {}).items():
                    stats = PlatformStats(
                        platform=platform,
                        total_requests=stats_data['total_requests'],
                        successful_requests=stats_data['successful_requests'],
                        failed_requests=stats_data['failed_requests'],
                        average_response_time=stats_data['average_response_time'],
                        uptime_percentage=stats_data['uptime_percentage'],
                        last_seen=datetime.fromisoformat(stats_data['last_seen']) if stats_data.get('last_seen') else None,
                        failover_count=stats_data['failover_count']
                    )
                    self.platform_stats[platform] = stats
                
                logger.info(f"Loaded {len(self.health_metrics)} health metrics and {len(self.failover_events)} failover events")
                
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
    
    def save_metrics(self):
        """Save metrics to file"""
        try:
            # Clean old metrics
            self.cleanup_old_metrics()
            
            data = {
                'health_metrics': [asdict(metric) for metric in self.health_metrics[-1000:]],  # Keep last 1000
                'failover_events': [asdict(event) for event in self.failover_events[-100:]],  # Keep last 100
                'platform_stats': {platform: asdict(stats) for platform, stats in self.platform_stats.items()},
                'last_updated': datetime.now().isoformat()
            }
            
            # Convert datetime objects to strings
            for metric in data['health_metrics']:
                metric['timestamp'] = metric['timestamp'].isoformat() if isinstance(metric['timestamp'], datetime) else metric['timestamp']
            
            for event in data['failover_events']:
                event['timestamp'] = event['timestamp'].isoformat() if isinstance(event['timestamp'], datetime) else event['timestamp']
            
            for stats in data['platform_stats'].values():
                if stats['last_seen']:
                    stats['last_seen'] = stats['last_seen'].isoformat() if isinstance(stats['last_seen'], datetime) else stats['last_seen']
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def record_request(self, platform: str, success: bool, response_time: float):
        """Record a request and its outcome for monitoring"""
        try:
            # Update platform stats
            if platform not in self.platform_stats:
                self.platform_stats[platform] = PlatformStats(platform=platform)

            stats = self.platform_stats[platform]
            stats.total_requests += 1

            if success:
                stats.successful_requests += 1
                stats.last_success = datetime.now()
                # Reset consecutive failures on success
                if platform in self.consecutive_failures:
                    self.consecutive_failures[platform] = 0
            else:
                stats.failed_requests += 1
                stats.last_failure = datetime.now()
                # Increment consecutive failures
                self.consecutive_failures[platform] = self.consecutive_failures.get(platform, 0) + 1

            # Update response time metrics
            stats.total_response_time += response_time
            if stats.total_requests > 0:
                stats.average_response_time = stats.total_response_time / stats.total_requests

            # Update uptime percentage
            if stats.total_requests > 0:
                stats.uptime_percentage = (stats.successful_requests / stats.total_requests) * 100

            # Create health metric entry
            metric = HealthMetric(
                timestamp=datetime.now(),
                platform=platform,
                is_healthy=success,
                response_time=response_time,
                error_message=None if success else "Request failed"
            )

            self.health_metrics.append(metric)

            # Emit health update signal
            self.health_updated.emit({
                'platform': platform,
                'success': success,
                'response_time': response_time,
                'consecutive_failures': self.consecutive_failures.get(platform, 0)
            })

            # Check for alerts
            self._check_platform_alerts(platform, stats)

            logger.debug(f"Recorded request for {platform}: success={success}, time={response_time:.2f}s")

        except Exception as e:
            logger.error(f"Failed to record request for {platform}: {e}")

    def record_failover(self, from_platform: Optional[str], to_platform: str, reason: str):
        """Record a failover event"""
        try:
            event = FailoverEvent(
                timestamp=datetime.now(),
                from_platform=from_platform,
                to_platform=to_platform,
                reason=reason,
                duration=None,
                success=True
            )

            self.failover_events.append(event)

            # Emit failover signal
            self.failover_detected.emit({
                'from_platform': from_platform,
                'to_platform': to_platform,
                'reason': reason,
                'timestamp': event.timestamp.isoformat()
            })

            # Create alert for failover
            self.create_alert(
                platform=to_platform,
                alert_type='failover',
                message=f"Failover from {from_platform or 'unknown'} to {to_platform}: {reason}",
                severity='medium'
            )

            logger.info(f"Recorded failover: {from_platform} -> {to_platform} ({reason})")

        except Exception as e:
            logger.error(f"Failed to record failover: {e}")

    def _check_platform_alerts(self, platform: str, stats: PlatformStats):
        """Check if platform metrics trigger any alerts"""
        try:
            # High error rate alert
            if stats.total_requests >= 10:  # Only check after sufficient requests
                error_rate = stats.failed_requests / stats.total_requests
                if error_rate > 0.1:  # 10% error rate threshold
                    self.create_alert(
                        platform=platform,
                        alert_type='high_error_rate',
                        message=f"High error rate: {error_rate:.1%}",
                        severity='high'
                    )

            # Consecutive failures alert
            consecutive = self.consecutive_failures.get(platform, 0)
            if consecutive >= self.alert_threshold:
                self.create_alert(
                    platform=platform,
                    alert_type='platform_down',
                    message=f"Platform appears down: {consecutive} consecutive failures",
                    severity='critical'
                )

                # Emit platform down signal
                self.platform_down.emit(platform)

            # Slow response time alert
            if stats.average_response_time > 10.0:  # 10 second threshold
                self.create_alert(
                    platform=platform,
                    alert_type='slow_response',
                    message=f"Slow response time: {stats.average_response_time:.2f}s",
                    severity='medium'
                )

        except Exception as e:
            logger.error(f"Failed to check alerts for {platform}: {e}")

    def get_platform_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary for all platforms"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'platforms': {},
            'overall': {
                'total_platforms': 0,
                'healthy_platforms': 0,
                'total_requests': 0,
                'total_failures': 0,
                'average_response_time': 0.0,
                'overall_uptime': 0.0
            }
        }

        total_requests = 0
        total_response_time = 0.0
        total_uptime = 0.0

        for platform, stats in self.platform_stats.items():
            is_healthy = self.is_platform_healthy(platform)

            summary['platforms'][platform] = {
                'healthy': is_healthy,
                'total_requests': stats.total_requests,
                'successful_requests': stats.successful_requests,
                'failed_requests': stats.failed_requests,
                'error_rate': (stats.failed_requests / max(stats.total_requests, 1)) * 100,
                'average_response_time': stats.average_response_time,
                'uptime_percentage': stats.uptime_percentage,
                'last_check': self.get_last_check_time(platform),
                'consecutive_failures': self.consecutive_failures.get(platform, 0)
            }

            summary['overall']['total_platforms'] += 1
            if is_healthy:
                summary['overall']['healthy_platforms'] += 1

            total_requests += stats.total_requests
            total_response_time += stats.average_response_time * stats.total_requests
            total_uptime += stats.uptime_percentage

        # Calculate overall metrics
        if total_requests > 0:
            summary['overall']['total_requests'] = total_requests
            summary['overall']['average_response_time'] = total_response_time / total_requests

        if summary['overall']['total_platforms'] > 0:
            summary['overall']['overall_uptime'] = total_uptime / summary['overall']['total_platforms']

        return summary

    def is_platform_healthy(self, platform: str) -> bool:
        """Check if a platform is currently healthy"""
        # Check consecutive failures
        if self.consecutive_failures.get(platform, 0) >= self.alert_threshold:
            return False

        # Check recent metrics
        recent_metrics = [
            m for m in self.health_metrics
            if m.platform == platform and
            (datetime.now() - m.timestamp).total_seconds() < 300  # Last 5 minutes
        ]

        if not recent_metrics:
            return False  # No recent data

        # Check if majority of recent checks were successful
        healthy_checks = sum(1 for m in recent_metrics if m.is_healthy)
        return healthy_checks >= len(recent_metrics) * 0.7  # 70% success rate

    def get_last_check_time(self, platform: str) -> Optional[str]:
        """Get the timestamp of the last health check for a platform"""
        platform_metrics = [m for m in self.health_metrics if m.platform == platform]
        if platform_metrics:
            latest = max(platform_metrics, key=lambda x: x.timestamp)
            return latest.timestamp.isoformat()
        return None

    def get_failover_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get failover history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_failovers = [
            event for event in self.failover_events
            if event.timestamp >= cutoff_time
        ]

        return [
            {
                'timestamp': event.timestamp.isoformat(),
                'from_platform': event.from_platform,
                'to_platform': event.to_platform,
                'reason': event.reason,
                'duration': event.duration,
                'success': event.success
            }
            for event in recent_failovers
        ]

    def get_performance_trends(self, platform: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends for a specific platform"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        platform_metrics = [
            m for m in self.health_metrics
            if m.platform == platform and m.timestamp >= cutoff_time
        ]

        if not platform_metrics:
            return {'error': 'No data available for the specified time period'}

        # Calculate trends
        response_times = [m.response_time for m in platform_metrics]
        success_rate = sum(1 for m in platform_metrics if m.is_healthy) / len(platform_metrics)

        return {
            'platform': platform,
            'time_period_hours': hours,
            'total_checks': len(platform_metrics),
            'success_rate': success_rate * 100,
            'average_response_time': sum(response_times) / len(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'response_time_trend': self.calculate_trend(response_times),
            'availability_trend': self.calculate_availability_trend(platform_metrics)
        }

    def calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a list of values"""
        if len(values) < 2:
            return 'stable'

        # Simple trend calculation using first and last quartile
        quarter = len(values) // 4
        if quarter == 0:
            quarter = 1

        first_quarter_avg = sum(values[:quarter]) / quarter
        last_quarter_avg = sum(values[-quarter:]) / quarter

        change_percent = ((last_quarter_avg - first_quarter_avg) / first_quarter_avg) * 100

        if change_percent > 10:
            return 'increasing'
        elif change_percent < -10:
            return 'decreasing'
        else:
            return 'stable'

    def calculate_availability_trend(self, metrics: List[HealthMetric]) -> str:
        """Calculate availability trend"""
        if len(metrics) < 10:
            return 'stable'

        # Split into two halves and compare success rates
        mid = len(metrics) // 2
        first_half = metrics[:mid]
        second_half = metrics[mid:]

        first_success_rate = sum(1 for m in first_half if m.is_healthy) / len(first_half)
        second_success_rate = sum(1 for m in second_half if m.is_healthy) / len(second_half)

        change = second_success_rate - first_success_rate

        if change > 0.1:
            return 'improving'
        elif change < -0.1:
            return 'degrading'
        else:
            return 'stable'

    def create_alert(self, platform: str, alert_type: str, message: str, severity: str = 'medium'):
        """Create and emit an alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'type': alert_type,
            'message': message,
            'severity': severity
        }

        # Emit appropriate signal based on alert type
        if alert_type == 'platform_down':
            self.platform_down.emit(platform)
        elif alert_type == 'platform_up':
            self.platform_up.emit(platform)
        elif alert_type == 'all_platforms_down':
            self.all_platforms_down.emit()

        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

        logger.warning(f"Alert: {platform} - {alert_type} - {message}")

    def add_alert_callback(self, callback: Callable):
        """Add a callback for alert notifications"""
        self.alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable):
        """Remove an alert callback"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)

    def get_performance_trends(self, platform: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends for a specific platform"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            platform_metrics = [
                m for m in self.health_metrics
                if m.platform == platform and m.timestamp >= cutoff_time
            ]

            if not platform_metrics:
                return {'error': 'No data available for the specified time period'}

            # Calculate trends
            response_times = [m.response_time for m in platform_metrics]
            success_rate = sum(1 for m in platform_metrics if m.is_healthy) / len(platform_metrics)

            return {
                'platform': platform,
                'time_period_hours': hours,
                'total_checks': len(platform_metrics),
                'success_rate': success_rate * 100,
                'average_response_time': sum(response_times) / len(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'response_time_trend': 'stable',  # Simplified for now
                'availability_trend': 'stable'   # Simplified for now
            }

        except Exception as e:
            logger.error(f"Failed to get performance trends for {platform}: {e}")
            return {'error': f'Failed to get trends: {str(e)}'}

    def _on_failover(self, old_endpoint, new_endpoint):
        """Handle failover events from service discovery"""
        try:
            from_platform = old_endpoint.name if old_endpoint else None
            to_platform = new_endpoint.name if new_endpoint else None

            if to_platform:
                self.record_failover(from_platform, to_platform, "Automatic failover")

        except Exception as e:
            logger.error(f"Failed to handle failover event: {e}")

    def start_monitoring(self):
        """Start platform monitoring"""
        try:
            logger.info("Platform monitoring started")
            # For now, monitoring is event-driven through service discovery
            # Additional background monitoring can be added here if needed
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")

    def stop_monitoring(self):
        """Stop platform monitoring"""
        try:
            logger.info("Platform monitoring stopped")
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")

# Global monitor instance
platform_monitor = PlatformMonitor()
