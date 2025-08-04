"""
Expense Data Models
Handles expense data structure and validation
"""

import pandas as pd
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path


class TransactionType(Enum):
    """Transaction type enumeration"""
    EXPENSE = "Expense"
    INCOME = "Income"
    TRANSFER = "Transfer"


class TransactionMode(Enum):
    """Transaction mode enumeration"""
    CASH = "Cash"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    UPI = "UPI"
    NET_BANKING = "Net Banking"
    WALLET = "Wallet"
    CHEQUE = "Cheque"
    BANK_TRANSFER = "Bank Transfer"
    OTHER = "Other"


@dataclass
class ExpenseRecord:
    """Data class for expense records"""
    id: Optional[int] = None
    date: Union[str, datetime, date] = None
    type: str = "Expense"
    category: str = ""
    sub_category: str = ""
    transaction_mode: str = "Cash"
    amount: float = 0.0
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.date is None:
            self.date = date.today()
        elif isinstance(self.date, str):
            try:
                self.date = datetime.strptime(self.date, '%Y-%m-%d').date()
            except ValueError:
                self.date = date.today()
        elif isinstance(self.date, datetime):
            self.date = self.date.date()
        
        if self.created_at is None:
            self.created_at = datetime.now()
        
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        data = asdict(self)
        
        # Convert date objects to strings
        if isinstance(data['date'], date):
            data['date'] = data['date'].strftime('%Y-%m-%d')
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpenseRecord':
        """Create from dictionary"""
        # Handle datetime strings
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['created_at'] = datetime.now()
        
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            try:
                data['updated_at'] = datetime.strptime(data['updated_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['updated_at'] = datetime.now()
        
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate the expense record"""
        errors = []
        
        if not self.category:
            errors.append("Category is required")
        
        if not self.sub_category:
            errors.append("Sub-category is required")
        
        if self.amount <= 0:
            errors.append("Amount must be greater than 0")
        
        if not self.transaction_mode:
            errors.append("Transaction mode is required")
        
        return errors


class ExpenseDataModel:
    """Data model for expense management"""

    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.module_name = "expenses"
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.filename = "expenses.csv"
        self.categories_filename = "categories.csv"

        # Default columns for expenses CSV
        self.default_columns = [
            'id', 'date', 'type', 'category', 'sub_category',
            'transaction_mode', 'amount', 'notes', 'created_at', 'updated_at'
        ]

        # Default columns for categories CSV - updated to match actual file structure
        self.categories_columns = [
            'category', 'sub_category', 'is_active', 'created_at', 'updated_at',
            'source', 'id', 'category_type', 'color', 'icon', 'ml_parent_id', 'ml_child_id'
        ]

        # Data caching for performance optimization
        self._cached_expenses = None
        self._cache_timestamp = None
        self._cache_valid_duration = 30  # Cache valid for 30 seconds
        self._processed_cache = None  # Cache for processed data with datetime conversion

        # Initialize default categories if not exists
        self._initialize_default_categories()
    
    def _initialize_default_categories(self):
        """Initialize default categories if they don't exist"""
        if not self.data_manager.file_exists(self.module_name, self.categories_filename):
            default_categories = [
                ("Food & Dining", ["Restaurants", "Groceries", "Fast Food", "Coffee", "Delivery"]),
                ("Transportation", ["Fuel", "Public Transport", "Taxi/Uber", "Parking", "Maintenance"]),
                ("Shopping", ["Clothing", "Electronics", "Books", "Home & Garden", "Groceries"]),
                ("Entertainment", ["Movies", "Games", "Sports", "Hobbies", "Subscriptions"]),
                ("Bills & Utilities", ["Electricity", "Water", "Internet", "Phone", "Insurance"]),
                ("Healthcare", ["Doctor", "Pharmacy", "Dental", "Vision", "Fitness"]),
                ("Education", ["Courses", "Books", "Supplies", "Tuition", "Certification"]),
                ("Travel", ["Flights", "Hotels", "Car Rental", "Activities", "Food"]),
                ("Personal Care", ["Haircut", "Cosmetics", "Spa", "Clothing", "Accessories"]),
                ("Gifts & Donations", ["Gifts", "Charity", "Tips", "Religious", "Social"]),
                ("Business", ["Office Supplies", "Software", "Equipment", "Travel", "Meals"]),
                ("Other", ["Miscellaneous", "Unexpected", "Emergency", "Investment", "Savings"])
            ]
            
            categories_data = []
            cat_id = 1
            
            for category, subcategories in default_categories:
                for subcategory in subcategories:
                    categories_data.append({
                        'id': cat_id,
                        'category': category,
                        'sub_category': subcategory,
                        'is_active': True,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    cat_id += 1
            
            df = pd.DataFrame(categories_data)
            self.data_manager.write_csv(self.module_name, self.categories_filename, df)
    
    def get_all_expenses(self) -> pd.DataFrame:
        """Get all expense records with caching for performance and proper validation"""
        import time

        current_time = time.time()

        # Check if cache is valid
        if (self._cached_expenses is not None and
            self._cache_timestamp is not None and
            current_time - self._cache_timestamp < self._cache_valid_duration):
            return self._cached_expenses.copy()

        # Load fresh data with flexible column handling
        df = self.data_manager.read_csv(
            self.module_name,
            self.filename,
            None  # Don't enforce default columns initially
        )

        # Validate and normalize the DataFrame structure
        df = self._validate_and_normalize_dataframe(df)

        # Update cache
        self._cached_expenses = df.copy()
        self._cache_timestamp = current_time
        self._processed_cache = None  # Clear processed cache

        return df

    def _validate_and_normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and normalize DataFrame structure to handle different CSV formats"""
        if df.empty:
            # Return empty DataFrame with proper structure
            return pd.DataFrame(columns=self.default_columns)

        # Required columns for basic functionality
        required_columns = ['id', 'date', 'category', 'amount', 'type']

        # Check if we have the minimum required columns
        missing_required = [col for col in required_columns if col not in df.columns]
        if missing_required:
            self.logger.warning(f"Missing required columns: {missing_required}")
            # Add missing columns with default values
            for col in missing_required:
                if col == 'type':
                    df[col] = 'Expense'  # Default to Expense if type is missing
                elif col == 'id':
                    df[col] = range(1, len(df) + 1)  # Generate sequential IDs
                else:
                    df[col] = ''

        # Ensure all default columns exist
        for col in self.default_columns:
            if col not in df.columns:
                if col in ['created_at', 'updated_at']:
                    df[col] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                elif col == 'sub_category':
                    df[col] = df.get('sub_category', 'General')
                elif col == 'transaction_mode':
                    df[col] = df.get('transaction_mode', 'Unknown')
                elif col == 'notes':
                    df[col] = df.get('notes', '')
                else:
                    df[col] = ''

        # Reorder columns to match expected structure
        df = df.reindex(columns=self.default_columns, fill_value='')

        # Validate transaction types
        valid_types = ['Income', 'Credit', 'Expense', 'Debit']
        if 'type' in df.columns:
            # Replace invalid types with 'Expense' as default
            df.loc[~df['type'].isin(valid_types), 'type'] = 'Expense'

        # Clean and validate data types
        try:
            # Ensure amount is numeric
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

            # Ensure date is datetime
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

            # Remove rows with invalid dates or zero amounts
            df = df.dropna(subset=['date'])
            df = df[df['amount'] > 0]

            # Ensure string columns are strings
            string_columns = ['category', 'sub_category', 'transaction_mode', 'notes', 'type']
            for col in string_columns:
                df[col] = df[col].astype(str).fillna('').replace('nan', '')

        except Exception as e:
            self.logger.error(f"Error normalizing data: {e}")

        return df

    def _has_valid_transaction_data(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame contains valid transaction data (excluding sample/test data)"""
        if df.empty:
            return False

        # Check if we have required columns
        required_columns = ['type', 'amount', 'category']
        if not all(col in df.columns for col in required_columns):
            return False

        # Filter out sample/test data
        real_data = self._filter_out_sample_data(df)
        if real_data.empty:
            return False

        # Check if we have valid transaction types
        valid_types = ['Income', 'Credit', 'Expense', 'Debit']
        if 'type' in real_data.columns:
            valid_type_data = real_data[real_data['type'].isin(valid_types)]
            if valid_type_data.empty:
                return False

        # Check if we have valid amounts (greater than 0)
        if 'amount' in real_data.columns:
            valid_amounts = real_data[real_data['amount'] > 0]
            if valid_amounts.empty:
                return False

        # Check if we have valid categories (not empty)
        if 'category' in real_data.columns:
            valid_categories = real_data[real_data['category'].str.strip() != '']
            if valid_categories.empty:
                return False

        return True

    def _filter_out_sample_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out sample/test data to only include real transactions"""
        if df.empty:
            return df

        # Create a copy to avoid modifying the original
        filtered_df = df.copy()

        # Identify sample data patterns
        sample_patterns = [
            'Sample expense',
            'Sample income',
            'Test expense',
            'Test income',
            'Sample transaction',
            'Test transaction'
        ]

        # Check notes column for sample patterns
        if 'notes' in filtered_df.columns:
            for pattern in sample_patterns:
                filtered_df = filtered_df[~filtered_df['notes'].str.contains(pattern, case=False, na=False)]

        # Check for generic subcategory patterns that indicate sample data
        if 'sub_category' in filtered_df.columns:
            sample_subcategory_patterns = [
                r'.*_sub_\d+$',  # Patterns like "Shopping_sub_3", "Entertainment_sub_1"
                r'^General$',
                r'^Test.*',
                r'^Sample.*'
            ]

            for pattern in sample_subcategory_patterns:
                filtered_df = filtered_df[~filtered_df['sub_category'].str.match(pattern, case=False, na=False)]

        # If we have very few records (less than 10% of original or less than 100),
        # and they all look like sample data, consider it invalid
        if len(filtered_df) < max(10, len(df) * 0.1):
            # Additional check: if all remaining records have very similar amounts or patterns
            if not filtered_df.empty and 'amount' in filtered_df.columns:
                # Check if amounts are suspiciously uniform (common in sample data)
                amount_variance = filtered_df['amount'].var()
                amount_mean = filtered_df['amount'].mean()

                # If variance is very low relative to mean, it might be sample data
                if amount_mean > 0 and (amount_variance / amount_mean) < 0.1:
                    return pd.DataFrame()  # Return empty - likely all sample data

        return filtered_df

    def get_processed_expenses(self) -> pd.DataFrame:
        """Get expenses with datetime conversion and preprocessing for filtering"""
        import time

        current_time = time.time()

        # Check if processed cache is valid
        if (self._processed_cache is not None and
            self._cache_timestamp is not None and
            current_time - self._cache_timestamp < self._cache_valid_duration):
            return self._processed_cache.copy()

        # Get raw data
        df = self.get_all_expenses()
        if df.empty:
            return df

        # Process data for filtering with comprehensive data type handling
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

        # Ensure string columns are properly handled and NaN values are replaced
        string_columns = ['category', 'sub_category', 'type', 'transaction_mode', 'notes']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna('')
                # Replace 'nan' string with empty string
                df[col] = df[col].replace('nan', '')

        # Cache processed data
        self._processed_cache = df.copy()

        return df

    def get_expense_records_only(self) -> pd.DataFrame:
        """Get only expense records (excluding income) - HELPER METHOD"""
        df = self.get_all_expenses()
        if df.empty:
            return df

        # Filter for only Expense records
        if 'type' in df.columns:
            df = df[df['type'] == 'Expense']
            print(f"Filtered to {len(df)} expense records (excluding income)")

        return df

    def invalidate_cache(self):
        """Invalidate the data cache - call when data is modified"""
        self._cached_expenses = None
        self._cache_timestamp = None
        self._processed_cache = None
    
    def add_expense(self, expense: ExpenseRecord) -> bool:
        """Add a new expense record"""
        errors = expense.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False

        result = self.data_manager.append_row(
            self.module_name,
            self.filename,
            expense.to_dict(),
            self.default_columns
        )

        if result:
            self.invalidate_cache()

        return result
    
    def update_expense(self, expense_id: int, expense: ExpenseRecord) -> bool:
        """Update an existing expense record"""
        errors = expense.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False

        result = self.data_manager.update_row(
            self.module_name,
            self.filename,
            expense_id,
            expense.to_dict()
        )

        if result:
            self.invalidate_cache()

        return result
    
    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense record"""
        result = self.data_manager.delete_row(
            self.module_name,
            self.filename,
            expense_id
        )

        if result:
            self.invalidate_cache()

        return result
    
    def get_expense_by_id(self, expense_id: int) -> Optional[ExpenseRecord]:
        """Get a specific expense by ID"""
        df = self.get_all_expenses()
        if df.empty:
            return None
        
        expense_data = df[df['id'] == expense_id]
        if expense_data.empty:
            return None
        
        return ExpenseRecord.from_dict(expense_data.iloc[0].to_dict())
    
    def search_expenses(self, search_term: str) -> pd.DataFrame:
        """Search expenses by term"""
        search_columns = ['category', 'sub_category', 'notes', 'transaction_mode']
        return self.data_manager.search_data(
            self.module_name,
            self.filename,
            search_term,
            search_columns
        )
    
    def get_expenses_by_date_range(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get expenses within a date range - FIXED to filter only Expense records"""
        df = self.get_all_expenses()
        if df.empty:
            return df

        # CRITICAL FIX: Filter for only Expense records (not Income)
        if 'type' in df.columns:
            df = df[df['type'] == 'Expense']
            print(f"Filtered to {len(df)} expense records (excluding income)")

        if df.empty:
            print("No expense records found after filtering by type")
            return df

        # Convert date column to datetime for filtering
        df['date'] = pd.to_datetime(df['date'])

        # Filter by date range
        mask = (df['date'] >= pd.Timestamp(start_date)) & (df['date'] <= pd.Timestamp(end_date))
        filtered_df = df[mask]

        print(f"Date range filter: {start_date} to {end_date}, found {len(filtered_df)} records")
        return filtered_df
    
    def get_expenses_by_category(self, category: str, subcategory: str = None) -> pd.DataFrame:
        """Get expenses by category and optionally subcategory - FIXED to filter only Expense records"""
        df = self.get_all_expenses()
        if df.empty:
            return df

        # CRITICAL FIX: Filter for only Expense records (not Income)
        if 'type' in df.columns:
            df = df[df['type'] == 'Expense']

        if df.empty:
            return df

        # Filter by category
        df = df[df['category'] == category]

        # Filter by subcategory if provided
        if subcategory:
            df = df[df['sub_category'] == subcategory]

        return df

    def get_expenses_by_filters(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Get expenses based on comprehensive filter criteria with optimized processing"""
        # Use processed cache for better performance
        df = self.get_processed_expenses()
        if df.empty:
            return df

        # Apply date filters
        if 'date_filter' in filters and filters['date_filter']:
            df = self._apply_date_filter(df, filters)

        # Apply transaction type filters with proper data type handling
        if 'transaction_types' in filters:
            transaction_types = filters['transaction_types']
            if transaction_types:  # Non-empty list
                # Ensure both sides are strings for comparison
                transaction_types = [str(t) for t in transaction_types]
                df = df[df['type'].astype(str).isin(transaction_types)]
            else:  # Empty list - show no data
                return pd.DataFrame(columns=df.columns)

        # Apply amount range filters
        if 'amount_range' in filters and filters['amount_range']:
            df = self._apply_amount_filter(df, filters['amount_range'])

        # Apply category filters with proper data type handling
        if 'categories' in filters and filters['categories']:
            # Ensure both sides are strings and handle empty/NaN values
            categories = [str(c) for c in filters['categories'] if str(c) != 'nan' and str(c) != '']
            if categories:  # Only filter if we have valid categories
                df = df[df['category'].astype(str).isin(categories)]

        # Apply sub-category filters with proper data type handling
        if 'sub_categories' in filters and filters['sub_categories']:
            # Ensure both sides are strings and handle empty/NaN values
            sub_categories = [str(sc) for sc in filters['sub_categories'] if str(sc) != 'nan' and str(sc) != '']
            if sub_categories:  # Only filter if we have valid sub-categories
                df = df[df['sub_category'].astype(str).isin(sub_categories)]

        return df

    def _apply_date_filter(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply date filtering logic with support for both string and dict formats"""
        date_filter = filters['date_filter']
        today = datetime.now().date()

        # Handle dict format (new format with type and date range)
        if isinstance(date_filter, dict):
            filter_type = date_filter.get('type', 'range')
            if filter_type == 'range':
                start_date = date_filter.get('start_date')
                end_date = date_filter.get('end_date')
                if start_date and end_date:
                    return df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
            return df

        # Handle string format (legacy format)
        if date_filter == 'all':
            return df
        elif date_filter == 'today':
            return df[df['date'].dt.date == today]
        elif date_filter == 'this_week':
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return df[(df['date'].dt.date >= start_of_week) & (df['date'].dt.date <= end_of_week)]
        elif date_filter == 'last_week':
            start_of_last_week = today - timedelta(days=today.weekday() + 7)
            end_of_last_week = start_of_last_week + timedelta(days=6)
            return df[(df['date'].dt.date >= start_of_last_week) & (df['date'].dt.date <= end_of_last_week)]
        elif date_filter == 'this_month':
            start_of_month = today.replace(day=1)
            return df[df['date'].dt.date >= start_of_month]
        elif date_filter == 'last_month':
            # Get first day of last month
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            return df[(df['date'].dt.date >= first_day_last_month) & (df['date'].dt.date <= last_day_last_month)]
        elif date_filter == 'this_year':
            start_of_year = today.replace(month=1, day=1)
            return df[df['date'].dt.date >= start_of_year]
        elif isinstance(date_filter, str) and date_filter.startswith('last_') and date_filter.endswith('_days'):
            # Extract number of days
            n_days = filters.get('last_n_days', 30)
            start_date = today - timedelta(days=n_days)
            return df[df['date'].dt.date >= start_date]
        elif date_filter == 'custom_range':
            start_date = filters.get('start_date')
            end_date = filters.get('end_date')
            if start_date and end_date:
                return df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]

        return df

    def _apply_amount_filter(self, df: pd.DataFrame, amount_range) -> pd.DataFrame:
        """Apply amount filtering logic with proper data type handling"""
        if amount_range is None:
            return df

        min_amount, max_amount = amount_range

        # Ensure amount column is numeric and handle NaN values
        df = df.copy()
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

        # Filter out rows with NaN amounts for filtering
        valid_amounts = df['amount'].notna()

        if min_amount is not None and max_amount is not None:
            return df[valid_amounts & (df['amount'] >= min_amount) & (df['amount'] <= max_amount)]
        elif min_amount is not None:
            return df[valid_amounts & (df['amount'] >= min_amount)]
        elif max_amount is not None:
            return df[valid_amounts & (df['amount'] <= max_amount)]

        return df

    def get_expenses_by_month_year(self, month: int, year: int) -> pd.DataFrame:
        """Get expenses for a specific month and year"""
        df = self.get_all_expenses()
        if df.empty:
            return df

        # Convert date column to datetime for filtering
        df['date'] = pd.to_datetime(df['date'])

        # Filter by month and year
        mask = (df['date'].dt.month == month) & (df['date'].dt.year == year)
        return df[mask]

    def get_expenses_by_year(self, year: int) -> pd.DataFrame:
        """Get expenses for a specific year"""
        df = self.get_all_expenses()
        if df.empty:
            return df

        # Convert date column to datetime for filtering
        df['date'] = pd.to_datetime(df['date'])

        # Filter by year
        return df[df['date'].dt.year == year]

    def get_expenses_last_n_days(self, n_days: int) -> pd.DataFrame:
        """Get expenses from the last N days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=n_days)
        return self.get_expenses_by_date_range(start_date, end_date)

    def get_expenses_by_transaction_types(self, transaction_types: List[str]) -> pd.DataFrame:
        """Get expenses by transaction types"""
        df = self.get_all_expenses()
        if df.empty:
            return df

        return df[df['type'].isin(transaction_types)]

    def get_expenses_by_amount_range(self, min_amount: float = None, max_amount: float = None) -> pd.DataFrame:
        """Get expenses within an amount range"""
        df = self.get_all_expenses()
        if df.empty:
            return df

        if min_amount is not None and max_amount is not None:
            return df[(df['amount'] >= min_amount) & (df['amount'] <= max_amount)]
        elif min_amount is not None:
            return df[df['amount'] >= min_amount]
        elif max_amount is not None:
            return df[df['amount'] <= max_amount]

        return df

    def get_expenses_by_categories_and_subcategories(self, categories: List[str] = None,
                                                   subcategories: List[str] = None) -> pd.DataFrame:
        """Get expenses by multiple categories and subcategories"""
        df = self.get_all_expenses()
        if df.empty:
            return df

        # Filter by categories if provided
        if categories:
            df = df[df['category'].isin(categories)]

        # Filter by subcategories if provided
        if subcategories:
            df = df[df['sub_category'].isin(subcategories)]

        return df

    def get_subcategories_for_categories(self, categories: List[str]) -> List[str]:
        """Get all subcategories for given categories"""
        df = self.get_all_expenses()
        if df.empty:
            return []

        # Filter by categories
        category_df = df[df['category'].isin(categories)]

        # Get unique subcategories
        subcategories = category_df['sub_category'].dropna().unique().tolist()
        return sorted([sub for sub in subcategories if sub and sub.strip()])

    def get_category_subcategory_pairs(self) -> List[Dict[str, str]]:
        """Get all unique category-subcategory pairs"""
        df = self.get_all_expenses()
        if df.empty:
            return []

        # Get unique combinations
        pairs = df[['category', 'sub_category']].drop_duplicates()
        pairs = pairs.dropna()

        result = []
        for _, row in pairs.iterrows():
            if row['category'] and row['sub_category']:
                result.append({
                    'category': row['category'],
                    'sub_category': row['sub_category']
                })

        return sorted(result, key=lambda x: (x['category'], x['sub_category']))

    def get_categories(self, category_type: str = None) -> pd.DataFrame:
        """Get all categories and subcategories, optionally filtered by category_type"""
        df = self.data_manager.read_csv(
            self.module_name,
            self.categories_filename,
            self.categories_columns
        )

        if df.empty:
            return df

        # Filter by category_type if specified
        if category_type:
            df = df[df['category_type'] == category_type]

        return df

    def get_category_list(self, category_type: str = None) -> List[str]:
        """Get list of unique categories, optionally filtered by category_type"""
        df = self.get_categories(category_type)
        if df.empty:
            return []

        return sorted(df[df['is_active'] == True]['category'].unique().tolist())

    def get_subcategory_list(self, category: str = None, category_type: str = None) -> List[str]:
        """Get list of subcategories for a category, or all subcategories if no category specified"""
        df = self.get_categories(category_type)
        if df.empty:
            return []

        if category:
            # Get subcategories for specific category
            filtered_df = df[(df['category'] == category) & (df['is_active'] == True)]
            return sorted(filtered_df['sub_category'].unique().tolist())
        else:
            # Get all subcategories
            return sorted(df[df['is_active'] == True]['sub_category'].unique().tolist())
    
    def add_category(self, category: str, subcategory: str, category_type: str = "expense") -> bool:
        """Add a new category/subcategory combination"""
        # Check if combination already exists
        df = self.get_categories()
        if not df.empty:
            existing = df[(df['category'] == category) & (df['sub_category'] == subcategory) & (df['category_type'] == category_type)]
            if not existing.empty:
                self.data_manager.error_occurred.emit("Category/subcategory combination already exists")
                return False

        category_data = {
            'category': category,
            'sub_category': subcategory,
            'is_active': True,
            'category_type': category_type,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        success = self.data_manager.append_row(
            self.module_name,
            self.categories_filename,
            category_data,
            self.categories_columns
        )

        # Auto-sync with bank analyzer if successful
        if success:
            self._sync_with_bank_analyzer(category, subcategory)

        return success

    def update_category(self, category_id: int, category: str, subcategory: str, category_type: str = None) -> bool:
        """Update an existing category/subcategory combination"""
        # Get current category to preserve category_type if not specified
        df = self.get_categories()
        if df.empty:
            self.data_manager.error_occurred.emit("Category not found")
            return False

        current_category = df[df['id'] == category_id]
        if current_category.empty:
            self.data_manager.error_occurred.emit("Category not found")
            return False

        # Use existing category_type if not specified
        if category_type is None:
            category_type = current_category.iloc[0]['category_type']

        # Check if the new combination already exists (excluding the current record)
        existing = df[(df['category'] == category) & (df['sub_category'] == subcategory) &
                     (df['category_type'] == category_type) & (df['id'] != category_id)]
        if not existing.empty:
            self.data_manager.error_occurred.emit("Category/subcategory combination already exists")
            return False

        category_data = {
            'category': category,
            'sub_category': subcategory,
            'category_type': category_type,
            'is_active': True,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        success = self.data_manager.update_row(
            self.module_name,
            self.categories_filename,
            category_id,
            category_data
        )

        return success

    def delete_category(self, category_id: int) -> bool:
        """Delete a category/subcategory combination"""
        # Check if category is being used in any expenses
        expenses_df = self.get_all_expenses()
        if not expenses_df.empty:
            # Get the category details first
            categories_df = self.get_categories()
            if not categories_df.empty:
                category_row = categories_df[categories_df['id'] == category_id]
                if not category_row.empty:
                    category_name = category_row.iloc[0]['category']
                    subcategory_name = category_row.iloc[0]['sub_category']

                    # Check if this category/subcategory is used in expenses
                    used_in_expenses = expenses_df[
                        (expenses_df['category'] == category_name) &
                        (expenses_df['sub_category'] == subcategory_name)
                    ]

                    if not used_in_expenses.empty:
                        self.data_manager.error_occurred.emit(
                            f"Cannot delete category '{category_name} - {subcategory_name}' as it is being used in {len(used_in_expenses)} expense(s)"
                        )
                        return False

        success = self.data_manager.delete_row(
            self.module_name,
            self.categories_filename,
            category_id
        )

        return success

    def toggle_category_status(self, category_id: int, is_active: bool) -> bool:
        """Toggle the active status of a category"""
        category_data = {
            'is_active': is_active,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        success = self.data_manager.update_row(
            self.module_name,
            self.categories_filename,
            category_id,
            category_data
        )

        return success

    def get_expense_summary(self) -> Dict[str, Any]:
        """Get expense summary statistics with robust error handling and proper data validation"""
        try:
            df = self.get_all_expenses()

            # Check if we have any valid data (excluding sample data)
            if df.empty or not self._has_valid_transaction_data(df):
                return {
                    'total_income': 0.0,
                    'income_count': 0,
                    'total_expense': 0.0,
                    'expense_count': 0,
                    'total_transactions': 0,
                    'total_amount': 0.0,
                    'average_amount': 0.0,
                    'categories_count': 0,
                    'this_month_amount': 0.0,
                    'this_week_amount': 0.0,
                    'category_breakdown': {},
                    'total_expenses': 0
                }

            # Filter out sample data for calculations
            df = self._filter_out_sample_data(df)

            # Ensure amount column is numeric
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

            # Convert date column with error handling
            try:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                # Remove rows with invalid dates
                df = df.dropna(subset=['date'])
            except Exception as e:
                self.logger.warning(f"Date conversion error: {e}")
                # If date conversion fails, use current date for calculations
                df['date'] = pd.to_datetime(datetime.now().date())

            # Debug: Check what type values exist
            if 'type' in df.columns:
                unique_types = df['type'].unique()
                print(f"DEBUG: Unique type values in data: {unique_types}")
                type_counts = df['type'].value_counts()
                print(f"DEBUG: Type value counts: {type_counts}")
            else:
                print("DEBUG: No 'type' column found in data")

            # Separate income and expenses based on transaction type
            # Try multiple possible values for income and expense
            if 'type' in df.columns:
                income_df = df[df['type'].str.lower().isin(['income', 'credit', 'earning'])]
                expense_df = df[df['type'].str.lower().isin(['expense', 'debit', 'spending'])]
            else:
                income_df = pd.DataFrame()
                expense_df = df.copy()  # If no type column, assume all are expenses

            print(f"DEBUG: Income records: {len(income_df)}, Expense records: {len(expense_df)}")

            # Calculate income statistics
            total_income = income_df['amount'].sum() if not income_df.empty else 0.0
            income_count = len(income_df)

            # Calculate expense statistics
            total_expense = expense_df['amount'].sum() if not expense_df.empty else 0.0
            expense_count = len(expense_df)

            print(f"DEBUG: Total income: ₹{total_income}, Total expense: ₹{total_expense}")

            # Overall statistics
            total_transactions = len(df)
            total_amount = df['amount'].sum() if not df['amount'].empty else 0.0
            average_amount = df['amount'].mean() if not df['amount'].empty else 0.0
            categories_count = df['category'].nunique() if 'category' in df.columns else 0

            # Category breakdown
            category_breakdown = {}
            if 'category' in df.columns:
                category_breakdown = df.groupby('category')['amount'].sum().to_dict()

            # This month expenses with error handling
            try:
                current_month = datetime.now().replace(day=1)
                this_month_df = df[df['date'] >= current_month]
                this_month_amount = this_month_df['amount'].sum() if not this_month_df.empty else 0.0
            except Exception as e:
                self.logger.warning(f"This month calculation error: {e}")
                this_month_amount = 0.0

            # This week expenses with error handling
            try:
                current_week = datetime.now() - pd.Timedelta(days=7)
                this_week_df = df[df['date'] >= current_week]
                this_week_amount = this_week_df['amount'].sum() if not this_week_df.empty else 0.0
            except Exception as e:
                self.logger.warning(f"This week calculation error: {e}")
                this_week_amount = 0.0

            return {
                # Income/Credit statistics
                'total_income': float(total_income) if pd.notna(total_income) else 0.0,
                'income_count': int(income_count),

                # Expense/Debit statistics
                'total_expense': float(total_expense) if pd.notna(total_expense) else 0.0,
                'expense_count': int(expense_count),

                # Overall statistics
                'total_transactions': int(total_transactions),
                'total_amount': float(total_amount) if pd.notna(total_amount) else 0.0,
                'average_amount': float(average_amount) if pd.notna(average_amount) else 0.0,
                'categories_count': int(categories_count),
                'this_month_amount': float(this_month_amount) if pd.notna(this_month_amount) else 0.0,
                'this_week_amount': float(this_week_amount) if pd.notna(this_week_amount) else 0.0,

                # Category breakdown
                'category_breakdown': category_breakdown,

                # Legacy fields for backward compatibility
                'total_expenses': int(total_transactions)
            }

        except Exception as e:
            self.logger.error(f"Error in get_expense_summary: {e}")
            # Return safe default values
            return {
                'total_income': 0.0,
                'income_count': 0,
                'total_expense': 0.0,
                'expense_count': 0,
                'total_transactions': 0,
                'total_amount': 0.0,
                'average_amount': 0.0,
                'categories_count': 0,
                'this_month_amount': 0.0,
                'this_week_amount': 0.0,
                'category_breakdown': {},
                'total_expenses': 0
            }

    def _sync_with_bank_analyzer(self, category: str, subcategory: str):
        """Automatically sync new category with bank analyzer"""
        try:
            from ...core.category_sync import create_category_synchronizer

            synchronizer = create_category_synchronizer()
            success, message = synchronizer.add_category_to_both(category, subcategory)

            if success:
                self.logger.info(f"Category '{category}/{subcategory}' synced with bank analyzer")
            else:
                self.logger.warning(f"Failed to sync category with bank analyzer: {message}")

        except Exception as e:
            # Don't fail the main operation if sync fails
            self.logger.warning(f"Could not sync category with bank analyzer: {e}")

    def import_bank_statement_transactions(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Import pre-labeled transaction data from bank statement analyzer CSV with duplicate prevention

        Args:
            csv_file_path: Path to the transactions CSV file

        Returns:
            Dict with import results including success count, errors, etc.
        """
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file_path)

            if df.empty:
                return {
                    'success': False,
                    'message': 'CSV file is empty',
                    'imported_count': 0,
                    'errors': []
                }

            self.logger.info(f"Starting import of {len(df)} transactions from {csv_file_path}")

            # Get existing expenses to avoid duplicates
            existing_df = self.get_all_expenses()
            next_id = 1 if existing_df.empty else existing_df['id'].max() + 1

            # Create a set of existing transaction signatures to prevent duplicates
            existing_signatures = set()
            if not existing_df.empty:
                for _, row in existing_df.iterrows():
                    # Create signature: date + amount + notes (first 50 chars)
                    signature = f"{row['date']}_{row['amount']}_{str(row['notes'])[:50]}"
                    existing_signatures.add(signature)

            imported_count = 0
            skipped_count = 0
            errors = []
            bulk_data = []

            for index, row in df.iterrows():
                try:
                    # Clean and validate date
                    date_str = pd.to_datetime(row['date']).strftime('%Y-%m-%d')  # Clean date format

                    # Map transaction type
                    transaction_type = "Income" if row['transaction_type'] == 'credit' else "Expense"

                    # Clean amount
                    amount = abs(float(row['amount']))

                    # Clean notes (description)
                    notes = str(row['description']).strip()

                    # Create transaction signature to check for duplicates
                    signature = f"{date_str}_{amount}_{notes[:50]}"

                    if signature in existing_signatures:
                        skipped_count += 1
                        continue  # Skip duplicate

                    # Create expense record data
                    expense_data = {
                        'id': next_id,
                        'date': date_str,  # Clean date format without time
                        'type': transaction_type,
                        'category': str(row['category']).strip(),
                        'sub_category': str(row['subcategory']).strip(),
                        'transaction_mode': 'Bank Transfer',  # Default for bank transactions
                        'amount': amount,
                        'notes': notes,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    bulk_data.append(expense_data)
                    existing_signatures.add(signature)  # Add to prevent duplicates within this import
                    imported_count += 1
                    next_id += 1

                except Exception as e:
                    errors.append(f"Error processing row {index + 1}: {str(e)}")
                    continue

            # Bulk import using DataFrame
            if bulk_data:
                try:
                    new_df = pd.DataFrame(bulk_data)

                    # Append to existing data
                    if not existing_df.empty:
                        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    else:
                        combined_df = new_df

                    # Write back to file
                    self.data_manager.write_csv(self.module_name, self.filename, combined_df)
                    self.logger.info(f"Successfully imported {imported_count} transactions, skipped {skipped_count} duplicates")

                except Exception as e:
                    return {
                        'success': False,
                        'message': f'Error during bulk import: {str(e)}',
                        'imported_count': 0,
                        'errors': [str(e)]
                    }

            # Prepare result message
            message = f'Successfully imported {imported_count} transactions'
            if skipped_count > 0:
                message += f' (skipped {skipped_count} duplicates)'

            return {
                'success': imported_count > 0 or skipped_count > 0,
                'message': message,
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'errors': errors
            }

        except Exception as e:
            self.logger.error(f"Error importing transactions: {str(e)}")
            return {
                'success': False,
                'message': f'Error reading CSV file: {str(e)}',
                'imported_count': 0,
                'errors': [str(e)]
            }
