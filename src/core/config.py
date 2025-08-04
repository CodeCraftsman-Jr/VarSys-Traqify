"""
Application Configuration Module
Handles all configuration settings for the Personal Finance Dashboard
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from PySide6.QtCore import QSettings


@dataclass
class AppConfig:
    """Application configuration class"""
    
    # Application settings
    app_name: str = "Personal Finance Dashboard"
    app_version: str = "1.0.0"
    
    # Data settings
    data_directory: str = "data"
    backup_directory: str = "backups"
    auto_save_interval: int = 300  # seconds
    max_backup_files: int = 10
    
    # UI settings
    theme: str = "dark"  # "light" or "dark"
    sidebar_width: int = 250
    sidebar_collapsed_width: int = 60
    window_width: int = 1400
    window_height: int = 900
    remember_window_state: bool = True
    
    # Module settings
    default_currency: str = "₹"
    date_format: str = "dd/MM/yyyy"
    decimal_places: int = 2
    
    # Expense tracker settings
    expense_categories: list = None
    expense_subcategories: dict = None
    transaction_modes: list = None
    
    # Goal income settings
    default_daily_goal: float = 1000.0
    goal_currency: str = "₹"
    
    # Habit tracker settings
    predefined_habits: list = None
    
    # Attendance settings
    total_periods: int = 8
    attendance_threshold: float = 75.0
    college_joining_year: int = 2024  # Year when college started
    
    def __post_init__(self):
        """Initialize default values after object creation"""
        if self.expense_categories is None:
            self.expense_categories = [
                "Food & Dining", "Transportation", "Shopping", "Entertainment",
                "Bills & Utilities", "Healthcare", "Education", "Travel",
                "Personal Care", "Gifts & Donations", "Business", "Other"
            ]
        
        if self.expense_subcategories is None:
            self.expense_subcategories = {
                "Food & Dining": ["Restaurants", "Groceries", "Fast Food", "Coffee", "Delivery"],
                "Transportation": ["Fuel", "Public Transport", "Taxi/Uber", "Parking", "Maintenance"],
                "Shopping": ["Clothing", "Electronics", "Books", "Home & Garden", "Groceries"],
                "Entertainment": ["Movies", "Games", "Sports", "Hobbies", "Subscriptions"],
                "Bills & Utilities": ["Electricity", "Water", "Internet", "Phone", "Insurance"],
                "Healthcare": ["Doctor", "Pharmacy", "Dental", "Vision", "Fitness"],
                "Education": ["Courses", "Books", "Supplies", "Tuition", "Certification"],
                "Travel": ["Flights", "Hotels", "Car Rental", "Activities", "Food"],
                "Personal Care": ["Haircut", "Cosmetics", "Spa", "Clothing", "Accessories"],
                "Gifts & Donations": ["Gifts", "Charity", "Tips", "Religious", "Social"],
                "Business": ["Office Supplies", "Software", "Equipment", "Travel", "Meals"],
                "Other": ["Miscellaneous", "Unexpected", "Emergency", "Investment", "Savings"]
            }
        
        if self.transaction_modes is None:
            self.transaction_modes = [
                "Cash", "Credit Card", "Debit Card", "UPI", "Net Banking",
                "Wallet", "Cheque", "Bank Transfer", "Other"
            ]
        
        if self.predefined_habits is None:
            self.predefined_habits = [
                "Face wash (Morning)", "Face wash (Night)", "Serum Application",
                "Sunscreen Application", "Study Session", "Project Work",
                "Aptitude Practice", "Handwriting Practice", "Record Updates",
                "Exercise", "Reading", "Meditation"
            ]
    
    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> 'AppConfig':
        """Load configuration from JSON file with enhanced validation"""
        if config_path is None:
            config_path = Path("config.json")

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # Validate and clean config data
                config_data = cls._validate_config_data(config_data)
                return cls(**config_data)

            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                # Create backup of corrupted config
                cls._backup_corrupted_config(config_path)

        return cls()

    @staticmethod
    def _validate_config_data(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean configuration data"""
        # Create a new AppConfig instance to get defaults
        defaults = AppConfig()
        validated = {}

        # Validate each field
        for field_name, default_value in asdict(defaults).items():
            if field_name in config_data:
                value = config_data[field_name]

                # Type validation
                if isinstance(default_value, bool):
                    validated[field_name] = bool(value) if isinstance(value, (bool, int)) else default_value
                elif isinstance(default_value, int):
                    try:
                        validated[field_name] = int(value) if value is not None else default_value
                        # Validate ranges for specific fields
                        if field_name in ['window_width', 'window_height'] and validated[field_name] < 400:
                            validated[field_name] = default_value
                        elif field_name == 'max_backup_files' and validated[field_name] < 1:
                            validated[field_name] = default_value
                    except (ValueError, TypeError):
                        validated[field_name] = default_value
                elif isinstance(default_value, float):
                    try:
                        validated[field_name] = float(value) if value is not None else default_value
                        # Validate ranges
                        if field_name == 'attendance_threshold' and not (0 <= validated[field_name] <= 100):
                            validated[field_name] = default_value
                    except (ValueError, TypeError):
                        validated[field_name] = default_value
                elif isinstance(default_value, str):
                    validated[field_name] = str(value) if value is not None else default_value
                    # Validate specific string fields
                    if field_name == 'theme' and validated[field_name] not in ['light', 'dark']:
                        validated[field_name] = default_value
                elif isinstance(default_value, (list, dict)):
                    validated[field_name] = value if isinstance(value, type(default_value)) else default_value
                else:
                    validated[field_name] = value
            else:
                validated[field_name] = default_value

        return validated

    @staticmethod
    def _backup_corrupted_config(config_path: Path):
        """Create backup of corrupted config file"""
        try:
            backup_path = config_path.with_suffix('.corrupted.bak')
            if config_path.exists():
                config_path.rename(backup_path)
                print(f"Corrupted config backed up to: {backup_path}")
        except Exception as e:
            print(f"Failed to backup corrupted config: {e}")
    
    def save_to_file(self, config_path: Optional[Path] = None):
        """Save configuration to JSON file"""
        if config_path is None:
            config_path = Path("config.json")
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_data_path(self) -> Path:
        """Get the data directory path"""
        return Path(self.data_directory)
    
    def get_backup_path(self) -> Path:
        """Get the backup directory path"""
        return Path(self.backup_directory)
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        self.get_data_path().mkdir(parents=True, exist_ok=True)
        self.get_backup_path().mkdir(parents=True, exist_ok=True)
        
        # Create module-specific data directories
        modules = [
            "expenses", "income", "habits", "attendance",
            "todos", "investments", "budget"
        ]
        
        for module in modules:
            (self.get_data_path() / module).mkdir(parents=True, exist_ok=True)


class SettingsManager:
    """Manages application settings using QSettings"""
    
    def __init__(self):
        self.settings = QSettings()
    
    def save_window_geometry(self, geometry: bytes):
        """Save window geometry"""
        self.settings.setValue("window/geometry", geometry)
    
    def load_window_geometry(self) -> Optional[bytes]:
        """Load window geometry"""
        return self.settings.value("window/geometry")
    
    def save_window_state(self, state: bytes):
        """Save window state"""
        self.settings.setValue("window/state", state)
    
    def load_window_state(self) -> Optional[bytes]:
        """Load window state"""
        return self.settings.value("window/state")
    
    def save_setting(self, key: str, value: Any):
        """Save a setting"""
        self.settings.setValue(key, value)
    
    def load_setting(self, key: str, default: Any = None) -> Any:
        """Load a setting"""
        return self.settings.value(key, default)
    
    def clear_all(self):
        """Clear all settings"""
        self.settings.clear()
