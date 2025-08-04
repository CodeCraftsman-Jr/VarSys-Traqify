"""
Theme Switching Performance Testing Tool
Measures and compares theme switching performance
"""

import time
import logging
from typing import Dict, List, Callable
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import QTimer, QThread, QObject, Signal
from PySide6.QtGui import QFont

from .styles import StyleManager as OriginalStyleManager
from .optimized_styles import OptimizedStyleManager


class PerformanceMetrics:
    """Container for performance metrics"""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.stylesheet_generation_time = 0.0
        self.stylesheet_application_time = 0.0
        self.palette_application_time = 0.0
        self.total_time = 0.0
        self.widget_count = 0
        self.memory_usage_before = 0
        self.memory_usage_after = 0
        
    def to_dict(self) -> Dict:
        return {
            'stylesheet_generation_ms': round(self.stylesheet_generation_time * 1000, 2),
            'stylesheet_application_ms': round(self.stylesheet_application_time * 1000, 2),
            'palette_application_ms': round(self.palette_application_time * 1000, 2),
            'total_time_ms': round(self.total_time * 1000, 2),
            'widget_count': self.widget_count,
            'memory_delta_kb': round((self.memory_usage_after - self.memory_usage_before) / 1024, 2)
        }


class ThemePerformanceTester(QObject):
    """Performance tester for theme switching"""
    
    # Signals
    test_completed = Signal(str, dict)  # test_name, metrics
    test_failed = Signal(str, str)  # test_name, error
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def measure_theme_switch(self, style_manager, theme: str, test_name: str):
        """Measure theme switching performance"""
        metrics = PerformanceMetrics()
        
        try:
            # Get memory usage before
            import psutil
            process = psutil.Process()
            metrics.memory_usage_before = process.memory_info().rss
            
            # Count widgets
            app = QApplication.instance()
            if app:
                metrics.widget_count = len(app.allWidgets())
            
            # Start total time measurement
            total_start = time.perf_counter()
            
            # Measure stylesheet generation
            gen_start = time.perf_counter()
            stylesheet = style_manager.get_stylesheet(theme)
            metrics.stylesheet_generation_time = time.perf_counter() - gen_start
            
            # Measure stylesheet application
            if hasattr(style_manager, 'app') and style_manager.app:
                app_start = time.perf_counter()
                style_manager.app.setStyleSheet(stylesheet)
                metrics.stylesheet_application_time = time.perf_counter() - app_start
                
                # Measure palette application
                if hasattr(style_manager, '_get_palette'):
                    palette_start = time.perf_counter()
                    palette = style_manager._get_palette(theme)
                    style_manager.app.setPalette(palette)
                    metrics.palette_application_time = time.perf_counter() - palette_start
                elif hasattr(style_manager, '_generate_palette'):
                    palette_start = time.perf_counter()
                    palette = style_manager._generate_palette(theme)
                    style_manager.app.setPalette(palette)
                    metrics.palette_application_time = time.perf_counter() - palette_start
            
            # Total time
            metrics.total_time = time.perf_counter() - total_start
            
            # Memory usage after
            metrics.memory_usage_after = process.memory_info().rss
            
            self.test_completed.emit(test_name, metrics.to_dict())
            
        except Exception as e:
            self.logger.error(f"Performance test failed for {test_name}: {e}")
            self.test_failed.emit(test_name, str(e))


class ThemePerformanceWidget(QWidget):
    """Widget for running theme performance tests"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.tester = ThemePerformanceTester()
        self.results = {}
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the UI"""
        self.setWindowTitle("Theme Performance Tester")
        self.setFixedSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Theme Switching Performance Test")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Test buttons
        self.test_original_btn = QPushButton("Test Original StyleManager")
        self.test_optimized_btn = QPushButton("Test Optimized StyleManager")
        self.compare_btn = QPushButton("Compare Performance")
        self.clear_btn = QPushButton("Clear Results")
        
        layout.addWidget(self.test_original_btn)
        layout.addWidget(self.test_optimized_btn)
        layout.addWidget(self.compare_btn)
        layout.addWidget(self.clear_btn)
        
        # Results display
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.results_text)
        
    def setup_connections(self):
        """Setup signal connections"""
        self.test_original_btn.clicked.connect(self.test_original_manager)
        self.test_optimized_btn.clicked.connect(self.test_optimized_manager)
        self.compare_btn.clicked.connect(self.compare_performance)
        self.clear_btn.clicked.connect(self.clear_results)
        
        self.tester.test_completed.connect(self.on_test_completed)
        self.tester.test_failed.connect(self.on_test_failed)
        
    def test_original_manager(self):
        """Test original StyleManager performance"""
        self.results_text.append("Testing Original StyleManager...")
        
        try:
            original_manager = OriginalStyleManager(QApplication.instance())
            
            # Test dark theme
            self.tester.measure_theme_switch(original_manager, "dark", "Original_Dark")
            
            # Small delay before light theme test
            QTimer.singleShot(100, lambda: self.tester.measure_theme_switch(
                original_manager, "light", "Original_Light"
            ))
            
        except Exception as e:
            self.results_text.append(f"Error testing original manager: {e}")
            
    def test_optimized_manager(self):
        """Test optimized StyleManager performance"""
        self.results_text.append("Testing Optimized StyleManager...")
        
        try:
            optimized_manager = OptimizedStyleManager(QApplication.instance())
            
            # Test dark theme
            self.tester.measure_theme_switch(optimized_manager, "dark", "Optimized_Dark")
            
            # Small delay before light theme test
            QTimer.singleShot(100, lambda: self.tester.measure_theme_switch(
                optimized_manager, "light", "Optimized_Light"
            ))
            
        except Exception as e:
            self.results_text.append(f"Error testing optimized manager: {e}")
            
    def on_test_completed(self, test_name: str, metrics: Dict):
        """Handle test completion"""
        self.results[test_name] = metrics
        
        # Display results
        self.results_text.append(f"\n=== {test_name} Results ===")
        for key, value in metrics.items():
            self.results_text.append(f"{key}: {value}")
        self.results_text.append("")
        
        self.logger.info(f"Test completed: {test_name}")
        
    def on_test_failed(self, test_name: str, error: str):
        """Handle test failure"""
        self.results_text.append(f"\n❌ {test_name} FAILED: {error}\n")
        self.logger.error(f"Test failed: {test_name} - {error}")
        
    def compare_performance(self):
        """Compare performance between managers"""
        if len(self.results) < 2:
            self.results_text.append("Need at least 2 test results to compare")
            return
            
        self.results_text.append("\n" + "="*50)
        self.results_text.append("PERFORMANCE COMPARISON")
        self.results_text.append("="*50)
        
        # Compare original vs optimized for same theme
        themes = ["Dark", "Light"]
        
        for theme in themes:
            original_key = f"Original_{theme}"
            optimized_key = f"Optimized_{theme}"
            
            if original_key in self.results and optimized_key in self.results:
                original = self.results[original_key]
                optimized = self.results[optimized_key]
                
                self.results_text.append(f"\n{theme} Theme Comparison:")
                self.results_text.append("-" * 30)
                
                # Calculate improvements
                metrics_to_compare = [
                    'total_time_ms',
                    'stylesheet_generation_ms',
                    'stylesheet_application_ms',
                    'palette_application_ms'
                ]
                
                for metric in metrics_to_compare:
                    if metric in original and metric in optimized:
                        orig_val = original[metric]
                        opt_val = optimized[metric]
                        
                        if orig_val > 0:
                            improvement = ((orig_val - opt_val) / orig_val) * 100
                            self.results_text.append(
                                f"{metric}: {orig_val:.2f}ms → {opt_val:.2f}ms "
                                f"({improvement:+.1f}%)"
                            )
                        else:
                            self.results_text.append(
                                f"{metric}: {orig_val:.2f}ms → {opt_val:.2f}ms"
                            )
        
        # Overall summary
        if "Original_Dark" in self.results and "Optimized_Dark" in self.results:
            orig_total = self.results["Original_Dark"]["total_time_ms"]
            opt_total = self.results["Optimized_Dark"]["total_time_ms"]
            
            if orig_total > 0:
                overall_improvement = ((orig_total - opt_total) / orig_total) * 100
                self.results_text.append(f"\nOverall Performance Improvement: {overall_improvement:+.1f}%")
                
                if overall_improvement > 0:
                    self.results_text.append("✅ Optimization successful!")
                else:
                    self.results_text.append("⚠️ Optimization may need further work")
        
    def clear_results(self):
        """Clear all results"""
        self.results.clear()
        self.results_text.clear()
        self.results_text.append("Results cleared. Ready for new tests.")


def run_performance_test():
    """Run the performance test widget"""
    import sys
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    test_widget = ThemePerformanceWidget()
    test_widget.show()
    
    return test_widget


if __name__ == "__main__":
    test_widget = run_performance_test()
    import sys
    sys.exit(QApplication.instance().exec())
