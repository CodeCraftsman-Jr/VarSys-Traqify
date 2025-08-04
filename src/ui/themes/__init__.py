"""
Enhanced Theme System for PyQt Application

This module provides a modular, token-based theme management system that replaces
the monolithic stylesheet approach with a maintainable, extensible architecture.

Key Features:
- Design token system for consistent styling
- Modular component-based stylesheets
- Runtime theme switching
- Custom theme support
- Backward compatibility with existing StyleManager

Usage:
    from src.ui.themes import StyleManager
    
    # Initialize with QApplication instance
    style_manager = StyleManager(app)
    
    # Apply theme
    style_manager.apply_theme("dark")
    
    # Switch themes at runtime
    style_manager.apply_theme("light")
    
    # Get specific component styles
    button_styles = style_manager.get_component_style("buttons")
"""

from .manager import StyleManager, LegacyStyleManager
from .base.tokens import get_tokens, tokens_to_dict, DesignTokens, DARK_TOKENS, LIGHT_TOKENS

__all__ = [
    'StyleManager',
    'LegacyStyleManager', 
    'get_tokens',
    'tokens_to_dict',
    'DesignTokens',
    'DARK_TOKENS',
    'LIGHT_TOKENS'
]

__version__ = "2.0.0"
