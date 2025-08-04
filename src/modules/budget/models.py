"""
Budget Planning Data Models
Handles budget planning data structure and calculations
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class BudgetType(Enum):
    """Budget types"""
    MONTHLY = "Monthly"
    WEEKLY = "Weekly"
    YEARLY = "Yearly"


class CategoryType(Enum):
    """Budget category types"""
    INCOME = "Income"
    EXPENSE = "Expense"
    SAVINGS = "Savings"
    INVESTMENT = "Investment"


class BudgetCategoryIDManager:
    """
    Manages ID assignment and validation for budget categories.
    Ensures data integrity and prepares for future database migration.
    """

    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        self.module_name = "budget"
        self.categories_filename = "budget_categories.csv"

    def validate_id(self, category_id: Any) -> bool:
        """
        Validate if an ID is valid for database operations.

        Args:
            category_id: The ID to validate

        Returns:
            bool: True if ID is valid, False otherwise
        """
        if category_id is None:
            return False

        if pd.isna(category_id):
            return False

        if isinstance(category_id, str):
            if category_id.strip() == '' or category_id.lower() == 'nan':
                return False
            try:
                int(category_id)
                return True
            except ValueError:
                return False

        if isinstance(category_id, (int, float)):
            if np.isnan(category_id) or np.isinf(category_id):
                return False
            return category_id > 0

        return False

    def get_next_available_id(self) -> int:
        """
        Get the next available ID for a new budget category.
        Ensures sequential numbering and no conflicts.

        Returns:
            int: Next available ID
        """
        try:
            df = self.data_manager.read_csv(self.module_name, self.categories_filename)

            if df.empty:
                return 1

            # Get all valid IDs
            valid_ids = []
            for idx, row in df.iterrows():
                category_id = row.get('id')
                if self.validate_id(category_id):
                    try:
                        valid_ids.append(int(float(category_id)))
                    except (ValueError, TypeError):
                        continue

            if not valid_ids:
                return 1

            # Return the next sequential ID
            return max(valid_ids) + 1

        except Exception as e:
            self.logger.error(f"Error getting next available ID: {e}")
            return 1

    def assign_missing_ids(self) -> Dict[str, Any]:
        """
        Scan all budget categories and assign proper sequential IDs to any
        categories with missing or invalid IDs.

        Returns:
            Dict containing operation results and statistics
        """
        try:
            df = self.data_manager.read_csv(self.module_name, self.categories_filename)

            if df.empty:
                return {
                    'success': True,
                    'categories_processed': 0,
                    'ids_assigned': 0,
                    'message': 'No categories found'
                }

            categories_processed = len(df)
            ids_assigned = 0
            next_id = 1

            # First pass: collect all valid existing IDs
            existing_valid_ids = set()
            for idx, row in df.iterrows():
                category_id = row.get('id')
                if self.validate_id(category_id):
                    try:
                        existing_valid_ids.add(int(float(category_id)))
                    except (ValueError, TypeError):
                        continue

            # Determine starting ID (next available after existing valid IDs)
            if existing_valid_ids:
                next_id = max(existing_valid_ids) + 1

            # Second pass: assign IDs to categories with invalid IDs
            changes_made = False
            for idx, row in df.iterrows():
                category_id = row.get('id')

                if not self.validate_id(category_id):
                    # Assign new sequential ID
                    while next_id in existing_valid_ids:
                        next_id += 1

                    df.at[idx, 'id'] = next_id
                    existing_valid_ids.add(next_id)
                    ids_assigned += 1
                    changes_made = True

                    self.logger.info(f"Assigned ID {next_id} to category '{row.get('name', 'Unknown')}'")
                    next_id += 1

            # Save changes if any were made
            if changes_made:
                self.data_manager.write_csv(self.module_name, self.categories_filename, df)
                self.logger.info(f"Successfully assigned {ids_assigned} missing IDs")

            return {
                'success': True,
                'categories_processed': categories_processed,
                'ids_assigned': ids_assigned,
                'message': f'Processed {categories_processed} categories, assigned {ids_assigned} new IDs'
            }

        except Exception as e:
            self.logger.error(f"Error assigning missing IDs: {e}")
            return {
                'success': False,
                'categories_processed': 0,
                'ids_assigned': 0,
                'message': f'Error: {str(e)}'
            }

    def compact_id_sequence(self) -> Dict[str, Any]:
        """
        Compact the ID sequence to remove gaps and ensure sequential numbering.
        This prepares the data for relational database migration.

        Returns:
            Dict containing operation results
        """
        try:
            df = self.data_manager.read_csv(self.module_name, self.categories_filename)

            if df.empty:
                return {
                    'success': True,
                    'categories_processed': 0,
                    'message': 'No categories found'
                }

            # Sort by current ID to maintain relative order
            df_sorted = df.copy()

            # Create mapping of old IDs to new sequential IDs
            id_mapping = {}
            new_id = 1

            for idx, row in df_sorted.iterrows():
                old_id = row.get('id')
                if self.validate_id(old_id):
                    id_mapping[old_id] = new_id
                    df_sorted.at[idx, 'id'] = new_id
                    new_id += 1
                else:
                    # Assign new ID to invalid ones
                    id_mapping[old_id] = new_id
                    df_sorted.at[idx, 'id'] = new_id
                    new_id += 1

            # Save the compacted data
            self.data_manager.write_csv(self.module_name, self.categories_filename, df_sorted)

            self.logger.info(f"Compacted ID sequence for {len(df_sorted)} categories")

            return {
                'success': True,
                'categories_processed': len(df_sorted),
                'id_mapping': id_mapping,
                'message': f'Successfully compacted {len(df_sorted)} category IDs'
            }

        except Exception as e:
            self.logger.error(f"Error compacting ID sequence: {e}")
            return {
                'success': False,
                'categories_processed': 0,
                'message': f'Error: {str(e)}'
            }

    def ensure_category_has_valid_id(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure a category has a valid ID before saving.
        Assigns a new ID if the current one is invalid.

        Args:
            category_data: Dictionary containing category data

        Returns:
            Dict: Category data with valid ID
        """
        category_id = category_data.get('id')

        if not self.validate_id(category_id):
            # Assign new ID
            new_id = self.get_next_available_id()
            category_data['id'] = new_id
            self.logger.info(f"Assigned new ID {new_id} to category '{category_data.get('name', 'Unknown')}'")

        return category_data

    def validate_category_for_database(self, category_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate that a category is ready for database operations.

        Args:
            category_data: Dictionary containing category data

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check ID validity
        category_id = category_data.get('id')
        if not self.validate_id(category_id):
            return False, f"Invalid ID: {category_id}"

        # Check required fields
        if not category_data.get('name', '').strip():
            return False, "Category name is required"

        # Check for ID conflicts
        try:
            df = self.data_manager.read_csv(self.module_name, self.categories_filename)
            if not df.empty:
                existing_ids = df['id'].tolist()
                if category_id in existing_ids:
                    # Check if it's the same category (update) or a conflict (new category)
                    existing_category = df[df['id'] == category_id]
                    if not existing_category.empty:
                        existing_name = existing_category.iloc[0].get('name', '')
                        if existing_name != category_data.get('name', ''):
                            return False, f"ID {category_id} already exists for category '{existing_name}'"
        except Exception as e:
            self.logger.error(f"Error validating category for database: {e}")
            return False, f"Validation error: {str(e)}"

        return True, "Valid"

    def get_id_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about ID usage and validity.

        Returns:
            Dict containing ID statistics
        """
        try:
            df = self.data_manager.read_csv(self.module_name, self.categories_filename)

            if df.empty:
                return {
                    'total_categories': 0,
                    'valid_ids': 0,
                    'invalid_ids': 0,
                    'max_id': 0,
                    'id_gaps': [],
                    'duplicate_ids': []
                }

            total_categories = len(df)
            valid_ids = []
            invalid_ids = []

            # Analyze IDs
            for idx, row in df.iterrows():
                category_id = row.get('id')
                if self.validate_id(category_id):
                    try:
                        valid_ids.append(int(float(category_id)))
                    except (ValueError, TypeError):
                        invalid_ids.append(category_id)
                else:
                    invalid_ids.append(category_id)

            # Find gaps in sequence
            id_gaps = []
            if valid_ids:
                valid_ids_sorted = sorted(valid_ids)
                for i in range(1, max(valid_ids_sorted) + 1):
                    if i not in valid_ids_sorted:
                        id_gaps.append(i)

            # Find duplicates
            duplicate_ids = []
            if valid_ids:
                seen = set()
                for id_val in valid_ids:
                    if id_val in seen:
                        duplicate_ids.append(id_val)
                    seen.add(id_val)

            return {
                'total_categories': total_categories,
                'valid_ids': len(valid_ids),
                'invalid_ids': len(invalid_ids),
                'max_id': max(valid_ids) if valid_ids else 0,
                'id_gaps': id_gaps,
                'duplicate_ids': duplicate_ids,
                'next_available_id': self.get_next_available_id()
            }

        except Exception as e:
            self.logger.error(f"Error getting ID statistics: {e}")
            return {
                'total_categories': 0,
                'valid_ids': 0,
                'invalid_ids': 0,
                'max_id': 0,
                'id_gaps': [],
                'duplicate_ids': [],
                'error': str(e)
            }


@dataclass
class BudgetCategory:
    """Data class for budget categories"""
    id: Optional[int] = None
    name: str = ""
    category_type: str = CategoryType.EXPENSE.value
    planned_amount: float = 0.0
    actual_amount: float = 0.0
    description: str = ""
    is_essential: bool = True  # Essential vs discretionary spending
    parent_category: Optional[str] = None  # For subcategories
    
    def get_variance(self) -> float:
        """Get variance between planned and actual"""
        return self.actual_amount - self.planned_amount
    
    def get_variance_percentage(self) -> float:
        """Get variance percentage"""
        if self.planned_amount == 0:
            return 0.0
        return (self.get_variance() / self.planned_amount) * 100
    
    def is_over_budget(self) -> bool:
        """Check if over budget"""
        return self.actual_amount > self.planned_amount
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget amount"""
        return self.planned_amount - self.actual_amount
    
    def get_utilization_percentage(self) -> float:
        """Get budget utilization percentage"""
        if self.planned_amount == 0:
            return 0.0
        return (self.actual_amount / self.planned_amount) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        data = asdict(self)
        
        # Add calculated fields
        data['variance'] = self.get_variance()
        data['variance_percentage'] = self.get_variance_percentage()
        data['remaining_budget'] = self.get_remaining_budget()
        data['utilization_percentage'] = self.get_utilization_percentage()
        data['is_over_budget'] = self.is_over_budget()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BudgetCategory':
        """Create from dictionary"""
        # Remove calculated fields
        calc_fields = ['variance', 'variance_percentage', 'remaining_budget', 
                      'utilization_percentage', 'is_over_budget']
        for field in calc_fields:
            data.pop(field, None)
        
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate the budget category"""
        errors = []
        
        if not self.name.strip():
            errors.append("Category name is required")
        
        if self.category_type not in [t.value for t in CategoryType]:
            errors.append(f"Invalid category type: {self.category_type}")
        
        if self.planned_amount < 0:
            errors.append("Planned amount cannot be negative")
        
        if self.actual_amount < 0:
            errors.append("Actual amount cannot be negative")
        
        return errors


@dataclass
class BudgetPlan:
    """Data class for budget plans"""
    id: Optional[int] = None
    name: str = ""
    budget_type: str = BudgetType.MONTHLY.value
    period_start: Optional[Union[str, datetime, date]] = None
    period_end: Optional[Union[str, datetime, date]] = None
    total_income_planned: float = 0.0
    total_income_actual: float = 0.0
    total_expenses_planned: float = 0.0
    total_expenses_actual: float = 0.0
    total_savings_planned: float = 0.0
    total_savings_actual: float = 0.0
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        self.updated_at = datetime.now()
        
        # Handle date conversions
        for field in ['period_start', 'period_end']:
            value = getattr(self, field)
            if value and isinstance(value, str):
                try:
                    setattr(self, field, datetime.strptime(value, '%Y-%m-%d').date())
                except ValueError:
                    setattr(self, field, None)
            elif isinstance(value, datetime):
                setattr(self, field, value.date())
    
    def get_net_income_planned(self) -> float:
        """Get planned net income (income - expenses)"""
        return self.total_income_planned - self.total_expenses_planned
    
    def get_net_income_actual(self) -> float:
        """Get actual net income"""
        return self.total_income_actual - self.total_expenses_actual
    
    def get_savings_rate_planned(self) -> float:
        """Get planned savings rate percentage"""
        if self.total_income_planned == 0:
            return 0.0
        return (self.total_savings_planned / self.total_income_planned) * 100
    
    def get_savings_rate_actual(self) -> float:
        """Get actual savings rate percentage"""
        if self.total_income_actual == 0:
            return 0.0
        return (self.total_savings_actual / self.total_income_actual) * 100
    
    def get_expense_ratio_planned(self) -> float:
        """Get planned expense ratio percentage"""
        if self.total_income_planned == 0:
            return 0.0
        return (self.total_expenses_planned / self.total_income_planned) * 100
    
    def get_expense_ratio_actual(self) -> float:
        """Get actual expense ratio percentage"""
        if self.total_income_actual == 0:
            return 0.0
        return (self.total_expenses_actual / self.total_income_actual) * 100
    
    def is_on_track(self) -> bool:
        """Check if budget is on track"""
        return (self.total_expenses_actual <= self.total_expenses_planned and 
                self.total_savings_actual >= self.total_savings_planned * 0.9)  # 90% of savings goal
    
    def get_budget_health_score(self) -> float:
        """Get budget health score (0-100)"""
        score = 100.0
        
        # Deduct points for overspending
        if self.total_expenses_actual > self.total_expenses_planned:
            overspend_ratio = (self.total_expenses_actual - self.total_expenses_planned) / self.total_expenses_planned
            score -= min(overspend_ratio * 50, 50)  # Max 50 points deduction
        
        # Deduct points for under-saving
        if self.total_savings_actual < self.total_savings_planned:
            undersave_ratio = (self.total_savings_planned - self.total_savings_actual) / self.total_savings_planned
            score -= min(undersave_ratio * 30, 30)  # Max 30 points deduction
        
        # Bonus points for exceeding savings
        if self.total_savings_actual > self.total_savings_planned:
            oversave_ratio = (self.total_savings_actual - self.total_savings_planned) / self.total_savings_planned
            score += min(oversave_ratio * 20, 20)  # Max 20 bonus points
        
        return max(0, min(100, score))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        data = asdict(self)
        
        # Convert date objects to strings
        for field in ['period_start', 'period_end']:
            if isinstance(data[field], date):
                data[field] = data[field].strftime('%Y-%m-%d')
        
        for field in ['created_at', 'updated_at']:
            if isinstance(data[field], datetime):
                data[field] = data[field].strftime('%Y-%m-%d %H:%M:%S')
        
        # Add calculated fields
        data['net_income_planned'] = self.get_net_income_planned()
        data['net_income_actual'] = self.get_net_income_actual()
        data['savings_rate_planned'] = self.get_savings_rate_planned()
        data['savings_rate_actual'] = self.get_savings_rate_actual()
        data['expense_ratio_planned'] = self.get_expense_ratio_planned()
        data['expense_ratio_actual'] = self.get_expense_ratio_actual()
        data['is_on_track'] = self.is_on_track()
        data['budget_health_score'] = self.get_budget_health_score()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BudgetPlan':
        """Create from dictionary"""
        # Remove calculated fields
        calc_fields = ['net_income_planned', 'net_income_actual', 'savings_rate_planned',
                      'savings_rate_actual', 'expense_ratio_planned', 'expense_ratio_actual',
                      'is_on_track', 'budget_health_score']
        for field in calc_fields:
            data.pop(field, None)
        
        # Handle datetime strings
        for field in ['created_at', 'updated_at']:
            if field in data and isinstance(data[field], str) and data[field]:
                try:
                    data[field] = datetime.strptime(data[field], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    data[field] = None
        
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate the budget plan"""
        errors = []
        
        if not self.name.strip():
            errors.append("Budget plan name is required")
        
        if self.budget_type not in [t.value for t in BudgetType]:
            errors.append(f"Invalid budget type: {self.budget_type}")
        
        if self.total_income_planned < 0:
            errors.append("Planned income cannot be negative")
        
        if self.total_expenses_planned < 0:
            errors.append("Planned expenses cannot be negative")
        
        if self.total_savings_planned < 0:
            errors.append("Planned savings cannot be negative")
        
        if self.period_start and self.period_end and self.period_start > self.period_end:
            errors.append("Period start date must be before end date")
        
        return errors


class BudgetDataModel:
    """Data model for budget planning management"""
    
    def __init__(self, data_manager):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("="*40)
        self.logger.info("INITIALIZING BUDGET DATA MODEL")
        self.logger.info("="*40)
        
        try:
            self.data_manager = data_manager
            self.module_name = "budget"
            self.plans_filename = "budget_plans.csv"
            self.categories_filename = "budget_categories.csv"
            
            # Default columns for budget plans CSV
            self.plans_columns = [
                'id', 'name', 'budget_type', 'period_start', 'period_end',
                'total_income_planned', 'total_income_actual', 'total_expenses_planned',
                'total_expenses_actual', 'total_savings_planned', 'total_savings_actual',
                'notes', 'created_at', 'updated_at', 'net_income_planned', 'net_income_actual',
                'savings_rate_planned', 'savings_rate_actual', 'expense_ratio_planned',
                'expense_ratio_actual', 'is_on_track', 'budget_health_score'
            ]
            
            # Default columns for budget categories CSV
            self.categories_columns = [
                'id', 'name', 'category_type', 'planned_amount', 'actual_amount',
                'description', 'is_essential', 'parent_category', 'variance',
                'variance_percentage', 'remaining_budget', 'utilization_percentage',
                'is_over_budget'
            ]

            # Initialize ID manager for comprehensive ID management
            self.id_manager = BudgetCategoryIDManager(data_manager)

            # Perform initial ID cleanup and validation
            self._initialize_id_management()

            # Initialize default categories if none exist
            # TEMPORARILY DISABLED - User wants to add categories manually
            # self.initialize_default_categories()

            self.logger.info("✅ BudgetDataModel initialization SUCCESSFUL")

        except Exception as e:
            self.logger.error(f"❌ CRITICAL ERROR in BudgetDataModel.__init__: {e}")
            raise

    def _initialize_id_management(self):
        """
        Initialize ID management system for budget categories.
        Performs cleanup and validation of existing IDs.
        """
        try:
            self.logger.info("Initializing ID management system...")

            # Get current ID statistics
            stats = self.id_manager.get_id_statistics()
            self.logger.info(f"ID Statistics: {stats}")

            # Assign missing IDs if any exist
            if stats['invalid_ids'] > 0:
                self.logger.warning(f"Found {stats['invalid_ids']} categories with invalid IDs")
                result = self.id_manager.assign_missing_ids()

                if result['success']:
                    self.logger.info(f"Successfully assigned {result['ids_assigned']} missing IDs")
                else:
                    self.logger.error(f"Failed to assign missing IDs: {result['message']}")

            # Check for ID gaps and duplicates
            if stats['id_gaps']:
                self.logger.warning(f"Found ID gaps: {stats['id_gaps']}")

            if stats['duplicate_ids']:
                self.logger.error(f"Found duplicate IDs: {stats['duplicate_ids']}")
                # Compact sequence to resolve duplicates
                compact_result = self.id_manager.compact_id_sequence()
                if compact_result['success']:
                    self.logger.info("Successfully compacted ID sequence to resolve duplicates")
                else:
                    self.logger.error(f"Failed to compact ID sequence: {compact_result['message']}")

            self.logger.info("ID management system initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing ID management: {e}")

    def initialize_default_categories(self):
        """Initialize default budget categories if none exist"""
        try:
            # Check if categories already exist
            existing_categories = self.get_all_budget_categories()
            if not existing_categories.empty:
                return  # Categories already exist

            # Define default categories with ₹15,000 total budget
            default_categories = [
                BudgetCategory(name="EMI", category_type=CategoryType.EXPENSE.value,
                             planned_amount=4000.0, description="Loan EMIs", is_essential=True),
                BudgetCategory(name="Recharge", category_type=CategoryType.EXPENSE.value,
                             planned_amount=500.0, description="Mobile and internet recharge", is_essential=True),
                BudgetCategory(name="Bills", category_type=CategoryType.EXPENSE.value,
                             planned_amount=2000.0, description="Utility bills", is_essential=True),
                BudgetCategory(name="Food", category_type=CategoryType.EXPENSE.value,
                             planned_amount=3000.0, description="Groceries and food", is_essential=True),
                BudgetCategory(name="Snacks", category_type=CategoryType.EXPENSE.value,
                             planned_amount=1000.0, description="Snacks and beverages", is_essential=False),
                BudgetCategory(name="Entertainment", category_type=CategoryType.EXPENSE.value,
                             planned_amount=1500.0, description="Movies, games, subscriptions", is_essential=False),
                BudgetCategory(name="Unexpected", category_type=CategoryType.EXPENSE.value,
                             planned_amount=2000.0, description="Emergency and unexpected expenses", is_essential=True),
                BudgetCategory(name="Family", category_type=CategoryType.EXPENSE.value,
                             planned_amount=1000.0, description="Family expenses", is_essential=True),
                BudgetCategory(name="Other", category_type=CategoryType.EXPENSE.value,
                             planned_amount=0.0, description="Miscellaneous expenses", is_essential=False)
            ]

            # Add each default category
            for category in default_categories:
                self.add_budget_category(category)

            self.logger.info(f"Initialized {len(default_categories)} default budget categories")

        except Exception as e:
            self.logger.error(f"Error initializing default categories: {e}")

    # Budget Plans Methods
    def get_all_budget_plans(self) -> pd.DataFrame:
        """Get all budget plans"""
        try:
            df = self.data_manager.read_csv(self.module_name, self.plans_filename, self.plans_columns)
            return df
        except Exception as e:
            self.logger.error(f"Error getting budget plans: {e}")
            return pd.DataFrame(columns=self.plans_columns)

    def add_budget_plan(self, plan: BudgetPlan) -> bool:
        """Add a new budget plan"""
        errors = plan.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False

        return self.data_manager.append_row(
            self.module_name,
            self.plans_filename,
            plan.to_dict(),
            self.plans_columns
        )

    def update_budget_plan(self, plan_id: int, plan: BudgetPlan) -> bool:
        """Update an existing budget plan"""
        errors = plan.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False

        return self.data_manager.update_row(
            self.module_name,
            self.plans_filename,
            plan_id,
            plan.to_dict()
        )

    def delete_budget_plan(self, plan_id: int) -> bool:
        """Delete a budget plan"""
        return self.data_manager.delete_row(self.module_name, self.plans_filename, plan_id)

    # Budget Categories Methods
    def get_all_budget_categories(self) -> pd.DataFrame:
        """Get all budget categories"""
        try:
            df = self.data_manager.read_csv(self.module_name, self.categories_filename, self.categories_columns)
            return df
        except Exception as e:
            self.logger.error(f"Error getting budget categories: {e}")
            return pd.DataFrame(columns=self.categories_columns)

    def add_budget_category(self, category: BudgetCategory) -> bool:
        """Add a new budget category with proper ID management"""
        try:
            # Validate category data
            errors = category.validate()
            if errors:
                self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
                return False

            # Prepare category data with proper ID assignment
            category_data = category.to_dict()

            # Ensure category has a valid ID
            category_data = self.id_manager.ensure_category_has_valid_id(category_data)

            # Validate category is ready for database operations
            is_valid, error_message = self.id_manager.validate_category_for_database(category_data)
            if not is_valid:
                self.logger.error(f"Category validation failed: {error_message}")
                self.data_manager.error_occurred.emit(f"Category validation failed: {error_message}")
                return False

            # Add to database
            result = self.data_manager.append_row(
                self.module_name,
                self.categories_filename,
                category_data,
                self.categories_columns
            )

            if result:
                self.logger.info(f"Successfully added budget category '{category.name}' with ID {category_data['id']}")
            else:
                self.logger.error(f"Failed to add budget category '{category.name}'")

            return result

        except Exception as e:
            self.logger.error(f"Error adding budget category: {e}")
            self.data_manager.error_occurred.emit(f"Error adding budget category: {str(e)}")
            return False

    def update_budget_category(self, category_id: int, category: BudgetCategory) -> bool:
        """Update an existing budget category with proper ID validation"""
        try:
            # Validate category ID
            if not self.id_manager.validate_id(category_id):
                error_msg = f"Invalid category ID for update: {category_id}"
                self.logger.error(error_msg)
                self.data_manager.error_occurred.emit(error_msg)
                return False

            # Validate category data
            errors = category.validate()
            if errors:
                self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
                return False

            # Prepare category data
            category_data = category.to_dict()
            category_data['id'] = category_id  # Ensure ID is preserved

            # Validate category is ready for database operations
            is_valid, error_message = self.id_manager.validate_category_for_database(category_data)
            if not is_valid:
                self.logger.error(f"Category validation failed: {error_message}")
                self.data_manager.error_occurred.emit(f"Category validation failed: {error_message}")
                return False

            # Update in database
            result = self.data_manager.update_row(
                self.module_name,
                self.categories_filename,
                category_id,
                category_data
            )

            if result:
                self.logger.info(f"Successfully updated budget category '{category.name}' with ID {category_id}")
            else:
                self.logger.error(f"Failed to update budget category '{category.name}' with ID {category_id}")

            return result

        except Exception as e:
            self.logger.error(f"Error updating budget category: {e}")
            self.data_manager.error_occurred.emit(f"Error updating budget category: {str(e)}")
            return False

    def delete_budget_category(self, category_id: int) -> bool:
        """Delete a budget category with proper ID validation"""
        try:
            # Validate category ID
            if not self.id_manager.validate_id(category_id):
                error_msg = f"Invalid category ID for deletion: {category_id}"
                self.logger.error(error_msg)
                self.data_manager.error_occurred.emit(error_msg)
                return False

            # Check if category exists before deletion
            df = self.get_all_budget_categories()
            if df.empty or not (df['id'] == category_id).any():
                error_msg = f"Category with ID {category_id} not found for deletion"
                self.logger.error(error_msg)
                self.data_manager.error_occurred.emit(error_msg)
                return False

            # Get category name for logging
            category_row = df[df['id'] == category_id]
            category_name = category_row.iloc[0].get('name', 'Unknown') if not category_row.empty else 'Unknown'

            # Delete from database
            result = self.data_manager.delete_row(self.module_name, self.categories_filename, category_id)

            if result:
                self.logger.info(f"Successfully deleted budget category '{category_name}' with ID {category_id}")
            else:
                self.logger.error(f"Failed to delete budget category '{category_name}' with ID {category_id}")

            return result

        except Exception as e:
            self.logger.error(f"Error deleting budget category: {e}")
            self.data_manager.error_occurred.emit(f"Error deleting budget category: {str(e)}")
            return False

    # ID Management Methods
    def get_id_statistics(self) -> Dict[str, Any]:
        """Get comprehensive ID statistics for budget categories"""
        return self.id_manager.get_id_statistics()

    def assign_missing_ids(self) -> Dict[str, Any]:
        """Assign missing IDs to budget categories"""
        return self.id_manager.assign_missing_ids()

    def compact_id_sequence(self) -> Dict[str, Any]:
        """Compact ID sequence to remove gaps"""
        return self.id_manager.compact_id_sequence()

    def validate_all_category_ids(self) -> Dict[str, Any]:
        """Validate all category IDs and return detailed report"""
        try:
            df = self.get_all_budget_categories()

            if df.empty:
                return {
                    'success': True,
                    'total_categories': 0,
                    'valid_categories': 0,
                    'invalid_categories': [],
                    'message': 'No categories found'
                }

            valid_categories = []
            invalid_categories = []

            for idx, row in df.iterrows():
                category_id = row.get('id')
                category_name = row.get('name', 'Unknown')

                if self.id_manager.validate_id(category_id):
                    valid_categories.append({
                        'id': category_id,
                        'name': category_name,
                        'status': 'valid'
                    })
                else:
                    invalid_categories.append({
                        'id': category_id,
                        'name': category_name,
                        'status': 'invalid',
                        'reason': 'Invalid ID format or value'
                    })

            return {
                'success': True,
                'total_categories': len(df),
                'valid_categories': len(valid_categories),
                'invalid_categories': invalid_categories,
                'message': f'Validated {len(df)} categories: {len(valid_categories)} valid, {len(invalid_categories)} invalid'
            }

        except Exception as e:
            self.logger.error(f"Error validating category IDs: {e}")
            return {
                'success': False,
                'total_categories': 0,
                'valid_categories': 0,
                'invalid_categories': [],
                'message': f'Error: {str(e)}'
            }

    def get_categories_by_type(self, category_type: str) -> pd.DataFrame:
        """Get categories filtered by type"""
        df = self.get_all_budget_categories()
        if df.empty:
            return df
        return df[df['category_type'] == category_type]

    def get_budget_summary(self) -> Dict[str, Any]:
        """Get budget summary statistics"""
        plans_df = self.get_all_budget_plans()
        categories_df = self.get_all_budget_categories()

        if plans_df.empty:
            return {
                'total_plans': 0,
                'active_plans': 0,
                'total_planned_income': 0.0,
                'total_actual_income': 0.0,
                'total_planned_expenses': 0.0,
                'total_actual_expenses': 0.0,
                'average_health_score': 0.0,
                'plans_on_track': 0,
                'categories_over_budget': 0,
                'total_categories': 0
            }

        # Current date for active plans
        today = date.today()

        # Filter active plans (current period)
        active_plans = plans_df[
            (pd.to_datetime(plans_df['period_start']).dt.date <= today) &
            (pd.to_datetime(plans_df['period_end']).dt.date >= today)
        ]

        total_planned_income = plans_df['total_income_planned'].sum()
        total_actual_income = plans_df['total_income_actual'].sum()
        total_planned_expenses = plans_df['total_expenses_planned'].sum()
        total_actual_expenses = plans_df['total_expenses_actual'].sum()

        average_health_score = plans_df['budget_health_score'].mean() if not plans_df.empty else 0.0
        plans_on_track = len(plans_df[plans_df['is_on_track'] == True])

        categories_over_budget = 0
        if not categories_df.empty:
            categories_over_budget = len(categories_df[categories_df['is_over_budget'] == True])

        return {
            'total_plans': len(plans_df),
            'active_plans': len(active_plans),
            'total_planned_income': total_planned_income,
            'total_actual_income': total_actual_income,
            'total_planned_expenses': total_planned_expenses,
            'total_actual_expenses': total_actual_expenses,
            'average_health_score': average_health_score,
            'plans_on_track': plans_on_track,
            'categories_over_budget': categories_over_budget,
            'total_categories': len(categories_df)
        }
