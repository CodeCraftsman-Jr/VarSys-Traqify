"""
Simple Optimized Style Manager Module
High-performance theming with caching (simplified version)
"""

import logging
from typing import Dict, Optional, Callable
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import QTimer


class SimpleStylesheetCache:
    """Simple stylesheet cache for performance optimization"""
    
    def __init__(self):
        self.cache: Dict[str, str] = {}
        self.palette_cache: Dict[str, QPalette] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def get_stylesheet(self, theme: str) -> Optional[str]:
        """Get cached stylesheet for theme"""
        return self.cache.get(theme)
            
    def set_stylesheet(self, theme: str, stylesheet: str):
        """Cache stylesheet for theme"""
        self.cache[theme] = stylesheet
        self.logger.debug(f"Cached stylesheet for theme: {theme}")
            
    def get_palette(self, theme: str) -> Optional[QPalette]:
        """Get cached palette for theme"""
        return self.palette_cache.get(theme)
            
    def set_palette(self, theme: str, palette: QPalette):
        """Cache palette for theme"""
        self.palette_cache[theme] = palette
        self.logger.debug(f"Cached palette for theme: {theme}")
            
    def clear(self):
        """Clear all cached data"""
        self.cache.clear()
        self.palette_cache.clear()
        self.logger.debug("Stylesheet cache cleared")
            
    def preload_themes(self, themes: list, stylesheet_generator: Callable):
        """Preload themes into cache"""
        for theme in themes:
            if theme not in self.cache:
                try:
                    stylesheet = stylesheet_generator(theme)
                    self.set_stylesheet(theme, stylesheet)
                except Exception as e:
                    self.logger.error(f"Error preloading theme {theme}: {e}")


class OptimizedStyleManager:
    """
    High-performance style manager with caching (simplified version)
    """
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Performance optimizations
        self.cache = SimpleStylesheetCache()
        self.current_theme = "dark"
        self.is_applying = False
        
        # Batch update timer for reducing repaints
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._apply_pending_updates)
        self.pending_updates = []
        
        # Initialize cache with themes
        self._preload_themes()
        
    def _preload_themes(self):
        """Preload themes into cache for instant switching"""
        try:
            themes = ["dark", "light", "colorwave"]
            for theme in themes:
                if not self.cache.get_stylesheet(theme):
                    if theme == "dark":
                        stylesheet = self._get_dark_theme()
                    elif theme == "light":
                        stylesheet = self._get_light_theme()
                    else:  # colorwave
                        stylesheet = self._get_colorwave_theme()

                    self.cache.set_stylesheet(theme, stylesheet)

                    # Also cache palette
                    palette = self._generate_palette(theme)
                    self.cache.set_palette(theme, palette)

            self.logger.info("Themes preloaded into cache")

        except Exception as e:
            self.logger.error(f"Error preloading themes: {e}")
    
    def get_stylesheet(self, theme: str = "dark") -> str:
        """Get stylesheet for specified theme (cached)"""
        # Try cache first
        cached_stylesheet = self.cache.get_stylesheet(theme)
        if cached_stylesheet:
            return cached_stylesheet
            
        # Generate if not cached
        if theme == "dark":
            stylesheet = self._get_dark_theme()
        elif theme == "light":
            stylesheet = self._get_light_theme()
        elif theme == "colorwave":
            stylesheet = self._get_colorwave_theme()
        else:
            self.logger.warning(f"Unknown theme {theme}, falling back to dark")
            stylesheet = self._get_dark_theme()
            
        # Cache for next time
        self.cache.set_stylesheet(theme, stylesheet)
        return stylesheet
    
    def apply_theme(self, theme: str = "dark", callback: Optional[Callable] = None, force_refresh: bool = False):
        """Apply theme with optimizations"""
        if self.is_applying:
            self.logger.warning("Theme application already in progress")
            return

        if theme == self.current_theme and not force_refresh:
            self.logger.debug(f"Theme {theme} already applied")
            if callback:
                callback()
            return

        self.is_applying = True

        try:
            # Clear cache if force refresh is requested
            if force_refresh:
                self.logger.info("Force refresh requested - clearing stylesheet cache")
                self.cache.clear()

            # Get cached data
            stylesheet = self.cache.get_stylesheet(theme)
            palette = self.cache.get_palette(theme)
            
            if not stylesheet or not palette:
                # Generate missing data
                if not stylesheet:
                    stylesheet = self.get_stylesheet(theme)
                if not palette:
                    palette = self._generate_palette(theme)
                    self.cache.set_palette(theme, palette)
            
            # Apply optimizations
            self._apply_theme_optimized(theme, stylesheet, palette)
            
            self.current_theme = theme
            self.logger.info(f"Theme applied: {theme}")
            
            if callback:
                callback()
                
        except Exception as e:
            self.logger.error(f"Error applying theme {theme}: {e}")
        finally:
            self.is_applying = False
    
    def _apply_theme_optimized(self, theme: str, stylesheet: str, palette: QPalette):
        """Apply theme with performance optimizations"""
        if not self.app:
            return

        try:
            # Apply stylesheet first
            self.app.setStyleSheet(stylesheet)

            # Apply palette
            self.app.setPalette(palette)

            # Force immediate style refresh for critical widgets
            self._refresh_critical_widgets()

            # Process events to ensure updates are applied
            self.app.processEvents()

        except Exception as e:
            self.logger.error(f"Error in optimized theme application: {e}")
    
    def _refresh_critical_widgets(self):
        """Refresh critical widgets that need immediate style updates"""
        try:
            # Get all top-level widgets
            for widget in self.app.topLevelWidgets():
                if widget.isVisible():
                    # Force style refresh
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)
                    
        except Exception as e:
            self.logger.error(f"Error refreshing critical widgets: {e}")
    
    def _apply_pending_updates(self):
        """Apply batched updates"""
        if not self.pending_updates:
            return
            
        # Process all pending updates
        for update_func in self.pending_updates:
            try:
                update_func()
            except Exception as e:
                self.logger.error(f"Error applying pending update: {e}")
                
        self.pending_updates.clear()
    
    def _generate_palette(self, theme: str) -> QPalette:
        """Generate palette for theme (optimized)"""
        palette = QPalette()
        
        if theme == "dark":
            # Dark theme palette (optimized color creation)
            colors = {
                QPalette.ColorRole.Window: "#1e1e1e",
                QPalette.ColorRole.WindowText: "#ffffff",
                QPalette.ColorRole.Base: "#252526",
                QPalette.ColorRole.AlternateBase: "#2d2d30",
                QPalette.ColorRole.ToolTipBase: "#3e3e42",
                QPalette.ColorRole.ToolTipText: "#ffffff",
                QPalette.ColorRole.Text: "#ffffff",
                QPalette.ColorRole.Button: "#3e3e42",
                QPalette.ColorRole.ButtonText: "#ffffff",
                QPalette.ColorRole.BrightText: "#ff0000",
                QPalette.ColorRole.Link: "#0e639c",
                QPalette.ColorRole.Highlight: "#0e639c",
                QPalette.ColorRole.HighlightedText: "#ffffff",
            }
            
            # Apply colors efficiently
            for role, color_str in colors.items():
                palette.setColor(role, QColor(color_str))
                
            # Disabled colors
            disabled_color = QColor("#999999")
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_color)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)
            
        elif theme == "light":
            colors = {
                QPalette.ColorRole.Window: "#ffffff",
                QPalette.ColorRole.WindowText: "#000000",
                QPalette.ColorRole.Base: "#ffffff",
                QPalette.ColorRole.AlternateBase: "#f9f9f9",
                QPalette.ColorRole.ToolTipBase: "#ffffcc",
                QPalette.ColorRole.ToolTipText: "#000000",
                QPalette.ColorRole.Text: "#000000",
                QPalette.ColorRole.Button: "#f0f0f0",
                QPalette.ColorRole.ButtonText: "#000000",
                QPalette.ColorRole.BrightText: "#ff0000",
                QPalette.ColorRole.Link: "#0078d4",
                QPalette.ColorRole.Highlight: "#0078d4",
                QPalette.ColorRole.HighlightedText: "#ffffff",
            }

            for role, color_str in colors.items():
                palette.setColor(role, QColor(color_str))

            # Disabled colors
            disabled_color = QColor("#666666")
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_color)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)

        else:  # colorwave theme
            colors = {
                QPalette.ColorRole.Window: "#0a0a1a",
                QPalette.ColorRole.WindowText: "#ffffff",
                QPalette.ColorRole.Base: "#1a1a2e",
                QPalette.ColorRole.AlternateBase: "#2d1b3d",
                QPalette.ColorRole.ToolTipBase: "#2d1b3d",
                QPalette.ColorRole.ToolTipText: "#ffffff",
                QPalette.ColorRole.Text: "#ffffff",
                QPalette.ColorRole.Button: "#2d1b3d",
                QPalette.ColorRole.ButtonText: "#ffffff",
                QPalette.ColorRole.BrightText: "#f44336",
                QPalette.ColorRole.Link: "#c2185b",
                QPalette.ColorRole.Highlight: "#c2185b",
                QPalette.ColorRole.HighlightedText: "#ffffff",
            }

            for role, color_str in colors.items():
                palette.setColor(role, QColor(color_str))

            # Disabled colors
            disabled_color = QColor("#888888")
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_color)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)
        
        return palette
    
    def clear_cache(self):
        """Clear stylesheet cache"""
        self.cache.clear()
        
    def get_cache_info(self) -> dict:
        """Get cache statistics"""
        return {
            "cached_themes": len(self.cache.cache),
            "cached_palettes": len(self.cache.palette_cache),
            "current_theme": self.current_theme
        }
    
    # Import existing theme methods for compatibility
    def _get_dark_theme(self) -> str:
        """Get dark theme stylesheet (imported from original)"""
        # Import the massive stylesheet from the original StyleManager
        from .styles import StyleManager as OriginalStyleManager
        original = OriginalStyleManager()
        return original._get_dark_theme()
    
    def _get_light_theme(self) -> str:
        """Get light theme stylesheet (imported from original)"""
        from .styles import StyleManager as OriginalStyleManager
        original = OriginalStyleManager()
        return original._get_light_theme()

    def _get_colorwave_theme(self) -> str:
        """Get colorwave theme stylesheet (imported from original)"""
        from .styles import StyleManager as OriginalStyleManager
        original = OriginalStyleManager()
        return original._get_colorwave_theme()
    
    def cleanup(self):
        """Cleanup resources"""
        self.cache.clear()
        if self.update_timer:
            self.update_timer.stop()
