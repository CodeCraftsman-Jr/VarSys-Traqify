"""
Enhanced Style Manager
Modular, token-based theme management system
"""

import logging
from typing import Dict, Optional, List
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from .base.tokens import get_tokens, tokens_to_dict, DesignTokens


class StyleManager:
    """Enhanced style manager with modular architecture and design tokens"""
    
    def __init__(self, app: Optional[QApplication] = None):
        self.app = app
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.current_theme = "dark"
        self.custom_themes: Dict[str, DesignTokens] = {}
        
        # Component style cache
        self._style_cache: Dict[str, str] = {}
        self._component_styles: Dict[str, str] = {}
        
        # Initialize component loaders
        self._load_component_styles()
    
    def _load_component_styles(self):
        """Load component-specific styles"""
        try:
            from .components import (
                get_button_styles,
                get_input_styles,
                get_table_styles,
                get_navigation_styles,
                get_global_styles
            )
            
            self._component_loaders = {
                'global': get_global_styles,
                'buttons': get_button_styles,
                'inputs': get_input_styles,
                'tables': get_table_styles,
                'navigation': get_navigation_styles,
            }
            
        except ImportError as e:
            self.logger.warning(f"Component styles not available: {e}")
            self._component_loaders = {}
    
    def get_stylesheet(self, theme: str = None, components: List[str] = None) -> str:
        """
        Get complete stylesheet for specified theme and components
        
        Args:
            theme: Theme name ('dark', 'light', or custom theme name)
            components: List of component names to include (None = all)
        
        Returns:
            Complete QSS stylesheet string
        """
        if theme is None:
            theme = self.current_theme
        
        # Check cache first
        cache_key = f"{theme}:{','.join(components or ['all'])}"
        if cache_key in self._style_cache:
            return self._style_cache[cache_key]
        
        # Get design tokens
        tokens = self._get_theme_tokens(theme)
        if not tokens:
            self.logger.error(f"Theme '{theme}' not found, falling back to dark")
            tokens = get_tokens("dark")
        
        # Convert tokens to template variables
        template_vars = tokens_to_dict(tokens)
        
        # Build stylesheet from components
        stylesheet_parts = []
        
        # Determine which components to include
        if components is None:
            components = list(self._component_loaders.keys())
        
        # Generate styles for each component
        for component_name in components:
            if component_name in self._component_loaders:
                try:
                    component_style = self._component_loaders[component_name](template_vars)
                    if component_style:
                        stylesheet_parts.append(f"/* {component_name.upper()} STYLES */")
                        stylesheet_parts.append(component_style)
                        stylesheet_parts.append("")  # Empty line for readability
                except Exception as e:
                    self.logger.error(f"Error loading {component_name} styles: {e}")
        
        # Combine all parts
        complete_stylesheet = "\n".join(stylesheet_parts)
        
        # Cache the result
        self._style_cache[cache_key] = complete_stylesheet
        
        return complete_stylesheet
    
    def apply_theme(self, theme: str = None, force_refresh: bool = False):
        """
        Apply theme to the application
        
        Args:
            theme: Theme name to apply
            force_refresh: Force refresh even if theme hasn't changed
        """
        if theme is None:
            theme = self.current_theme
        
        if not force_refresh and theme == self.current_theme:
            return
        
        if not self.app:
            self.logger.warning("No QApplication instance available")
            return
        
        try:
            # Clear cache if theme changed
            if theme != self.current_theme:
                self._style_cache.clear()
                self.current_theme = theme
            
            # Get complete stylesheet
            stylesheet = self.get_stylesheet(theme)
            
            # Apply stylesheet to application
            self.app.setStyleSheet(stylesheet)
            
            # Apply palette for widgets without stylesheets
            palette = self._create_palette(theme)
            self.app.setPalette(palette)
            
            self.logger.info(f"Applied theme: {theme}")
            
        except Exception as e:
            self.logger.error(f"Error applying theme '{theme}': {e}")
            # Fallback to default theme
            if theme != "dark":
                self.apply_theme("dark", force_refresh=True)
    
    def register_custom_theme(self, name: str, tokens: DesignTokens):
        """Register a custom theme"""
        self.custom_themes[name] = tokens
        self.logger.info(f"Registered custom theme: {name}")
    
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names"""
        base_themes = ["dark", "light", "colorwave"]
        custom_themes = list(self.custom_themes.keys())
        return base_themes + custom_themes
    
    def get_theme_tokens(self, theme: str = None) -> Optional[DesignTokens]:
        """Get design tokens for specified theme"""
        if theme is None:
            theme = self.current_theme
        return self._get_theme_tokens(theme)
    
    def _get_theme_tokens(self, theme: str) -> Optional[DesignTokens]:
        """Internal method to get theme tokens"""
        if theme in self.custom_themes:
            return self.custom_themes[theme]
        elif theme in ["dark", "light", "colorwave"]:
            return get_tokens(theme)
        else:
            return None
    
    def _create_palette(self, theme: str) -> QPalette:
        """Create QPalette for theme"""
        palette = QPalette()
        tokens = self._get_theme_tokens(theme)
        
        if not tokens:
            return palette
        
        colors = tokens.colors
        
        # Set palette colors
        palette.setColor(QPalette.ColorRole.Window, QColor(colors.primary_background))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.text_primary))
        palette.setColor(QPalette.ColorRole.Base, QColor(colors.primary_surface))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.primary_surface_variant))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors.primary_surface_variant))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors.text_primary))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors.text_primary))
        palette.setColor(QPalette.ColorRole.Button, QColor(colors.primary_surface_variant))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.text_primary))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(colors.error))
        palette.setColor(QPalette.ColorRole.Link, QColor(colors.accent_primary))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.selection_background))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.selection_text))
        
        return palette
    
    def reload_styles(self):
        """Reload all styles (useful for development)"""
        self._style_cache.clear()
        self._load_component_styles()
        self.apply_theme(force_refresh=True)
    
    def export_theme(self, theme: str, file_path: str):
        """Export theme as QSS file"""
        try:
            stylesheet = self.get_stylesheet(theme)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(stylesheet)
            self.logger.info(f"Exported theme '{theme}' to {file_path}")
        except Exception as e:
            self.logger.error(f"Error exporting theme: {e}")
    
    def get_component_style(self, component: str, theme: str = None) -> str:
        """Get stylesheet for specific component"""
        if theme is None:
            theme = self.current_theme
        
        return self.get_stylesheet(theme, [component])


# Backward compatibility with existing StyleManager
class LegacyStyleManager(StyleManager):
    """Legacy compatibility wrapper"""
    
    def __init__(self, app=None):
        super().__init__(app)
        self.themes = {
            "dark": lambda: self.get_stylesheet("dark"),
            "light": lambda: self.get_stylesheet("light")
        }
    
    def _get_dark_theme(self) -> str:
        """Legacy method for backward compatibility"""
        return self.get_stylesheet("dark")
    
    def _get_light_theme(self) -> str:
        """Legacy method for backward compatibility"""
        return self.get_stylesheet("light")
