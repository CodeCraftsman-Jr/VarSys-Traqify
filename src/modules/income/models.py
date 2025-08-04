"""
Income Goal Tracker Data Models
Handles income goal data structure and validation
"""

import pandas as pd
import calendar
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class GoalPeriod(Enum):
    """Goal period enumeration"""
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"


class IncomeStatus(Enum):
    """Income status enumeration"""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    EXCEEDED = "Exceeded"
    MISSED = "Missed"


@dataclass
class IncomeRecord:
    """Data class for daily income records"""
    id: Optional[int] = None
    date: Union[str, datetime, date] = None
    zomato: float = 0.0
    swiggy: float = 0.0
    shadow_fax: float = 0.0
    pc_repair: float = 0.0
    settings: float = 0.0
    youtube: float = 0.0
    gp_links: float = 0.0
    id_sales: float = 0.0
    other_sources: float = 0.0
    extra_work: float = 0.0  # Additional work to meet targets
    earned: float = 0.0  # Total earned (calculated)
    status: str = "Pending"
    goal_inc: float = 0.0  # Daily goal
    progress: float = 0.0  # Progress percentage (calculated)
    extra: float = 0.0  # Extra amount above goal (calculated)
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
        
        # Calculate derived fields
        self.calculate_totals()
    
    def calculate_totals(self):
        """Calculate total earned, progress, and extra amount"""
        # Calculate total earned from all sources
        self.earned = (self.zomato + self.swiggy + self.shadow_fax + self.pc_repair +
                      self.settings + self.youtube + self.gp_links + self.id_sales +
                      self.other_sources + self.extra_work)

        # Calculate progress percentage
        if self.goal_inc > 0:
            self.progress = (self.earned / self.goal_inc) * 100
        else:
            self.progress = 0.0

        # Calculate extra amount
        self.extra = max(0, self.earned - self.goal_inc)

        # Update status based on progress
        self.update_status()
    
    def update_status(self):
        """Update status based on current progress"""
        if self.earned == 0:
            self.status = "Pending"
        elif self.earned >= self.goal_inc:
            if self.earned > self.goal_inc:
                self.status = "Exceeded"
            else:
                self.status = "Completed"
        elif self.earned > 0:
            self.status = "In Progress"
        else:
            # Check if date has passed without achieving goal
            if self.date < date.today():
                self.status = "Missed"
            else:
                self.status = "Pending"
    
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
    def from_dict(cls, data: Dict[str, Any]) -> 'IncomeRecord':
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
        """Validate the income record"""
        errors = []
        
        if self.goal_inc < 0:
            errors.append("Goal amount cannot be negative")
        
        if any(amount < 0 for amount in [self.zomato, self.swiggy, self.shadow_fax, self.other_sources]):
            errors.append("Income amounts cannot be negative")
        
        return errors


@dataclass
class WeeklyGoalTarget:
    """Data class for weekly goal targets"""
    id: Optional[int] = None
    week_start: Union[str, datetime, date] = None
    monday_target: float = 500.0
    tuesday_target: float = 500.0
    wednesday_target: float = 500.0
    thursday_target: float = 500.0
    friday_target: float = 500.0
    saturday_target: float = 800.0
    sunday_target: float = 1000.0
    weekly_target: float = 4300.0  # Sum of daily targets
    is_active: bool = True
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.week_start is None:
            # Get Monday of current week
            today = date.today()
            self.week_start = today - timedelta(days=today.weekday())
        elif isinstance(self.week_start, str):
            try:
                self.week_start = datetime.strptime(self.week_start, '%Y-%m-%d').date()
            except ValueError:
                today = date.today()
                self.week_start = today - timedelta(days=today.weekday())
        elif isinstance(self.week_start, datetime):
            self.week_start = self.week_start.date()

        if self.created_at is None:
            self.created_at = datetime.now()

        # Calculate weekly target
        self.weekly_target = (self.monday_target + self.tuesday_target +
                            self.wednesday_target + self.thursday_target +
                            self.friday_target + self.saturday_target +
                            self.sunday_target)

    def get_target_for_date(self, target_date: date) -> float:
        """Get target amount for a specific date"""
        weekday = target_date.weekday()  # 0=Monday, 6=Sunday
        targets = [
            self.monday_target, self.tuesday_target, self.wednesday_target,
            self.thursday_target, self.friday_target, self.saturday_target,
            self.sunday_target
        ]
        return targets[weekday]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if isinstance(data['week_start'], date):
            data['week_start'] = data['week_start'].strftime('%Y-%m-%d')
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeeklyGoalTarget':
        """Create from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['created_at'] = datetime.now()
        return cls(**data)


@dataclass
class MonthlyGoalSummary:
    """Data class for monthly goal summary"""
    id: Optional[int] = None
    month: Union[str, datetime, date] = None
    monthly_target: float = 23300.0  # Total monthly target
    total_earned: float = 0.0
    zomato_earned: float = 0.0
    swiggy_earned: float = 0.0
    shadow_fax_earned: float = 0.0
    pc_repair_earned: float = 0.0
    settings_earned: float = 0.0
    youtube_earned: float = 0.0
    gp_links_earned: float = 0.0
    id_sales_earned: float = 0.0
    other_sources_earned: float = 0.0
    extra_work_earned: float = 0.0
    progress_percentage: float = 0.0
    days_completed: int = 0
    days_in_month: int = 0
    average_daily: float = 0.0
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.month is None:
            self.month = date.today().replace(day=1)
        elif isinstance(self.month, str):
            try:
                self.month = datetime.strptime(self.month, '%Y-%m-%d').date()
            except ValueError:
                self.month = date.today().replace(day=1)
        elif isinstance(self.month, datetime):
            self.month = self.month.date()

        if self.created_at is None:
            self.created_at = datetime.now()

        # Calculate progress
        if self.monthly_target > 0:
            self.progress_percentage = (self.total_earned / self.monthly_target) * 100

        # Calculate average daily
        if self.days_completed > 0:
            self.average_daily = self.total_earned / self.days_completed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if isinstance(data['month'], date):
            data['month'] = data['month'].strftime('%Y-%m-%d')
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonthlyGoalSummary':
        """Create from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['created_at'] = datetime.now()
        return cls(**data)


@dataclass
class GoalSetting:
    """Data class for goal settings"""
    id: Optional[int] = None
    name: str = ""
    period: str = "Daily"  # Daily, Weekly, Monthly
    amount: float = 0.0
    start_date: Union[str, datetime, date] = None
    end_date: Union[str, datetime, date] = None
    is_active: bool = True
    description: str = ""
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.start_date is None:
            self.start_date = date.today()
        elif isinstance(self.start_date, str):
            try:
                self.start_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
            except ValueError:
                self.start_date = date.today()
        elif isinstance(self.start_date, datetime):
            self.start_date = self.start_date.date()
        
        if self.end_date and isinstance(self.end_date, str):
            try:
                self.end_date = datetime.strptime(self.end_date, '%Y-%m-%d').date()
            except ValueError:
                self.end_date = None
        elif isinstance(self.end_date, datetime):
            self.end_date = self.end_date.date()
        
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        data = asdict(self)
        
        # Convert date objects to strings
        if isinstance(data['start_date'], date):
            data['start_date'] = data['start_date'].strftime('%Y-%m-%d')
        if data['end_date'] and isinstance(data['end_date'], date):
            data['end_date'] = data['end_date'].strftime('%Y-%m-%d')
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GoalSetting':
        """Create from dictionary"""
        # Handle datetime strings
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['created_at'] = datetime.now()

        # Ensure description is a string
        if 'description' in data and data['description'] is not None:
            data['description'] = str(data['description'])
        
        return cls(**data)


@dataclass
class SourceWeightageHistory:
    """Data class for tracking income source weightage changes over time"""
    id: Optional[int] = None
    date: Union[str, datetime, date] = None
    source_name: str = ""
    weightage_percentage: float = 0.0
    total_earned: float = 0.0
    period_type: str = "monthly"  # daily, weekly, monthly, yearly
    notes: str = ""
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values after object creation"""
        if self.created_at is None:
            self.created_at = datetime.now()

        # Convert date string to date object if needed
        if isinstance(self.date, str) and self.date:
            try:
                self.date = datetime.strptime(self.date, '%Y-%m-%d').date()
            except ValueError:
                self.date = date.today()
        elif self.date is None:
            self.date = date.today()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d') if isinstance(self.date, date) else str(self.date),
            'source_name': self.source_name,
            'weightage_percentage': self.weightage_percentage,
            'total_earned': self.total_earned,
            'period_type': self.period_type,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SourceWeightageHistory':
        """Create from dictionary"""
        # Handle datetime strings
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['created_at'] = datetime.now()

        return cls(**data)


@dataclass
class BaseIncomeSettings:
    """Data class for base daily income targets"""
    id: Optional[int] = None
    weekday_base: float = 500.0  # Monday to Friday
    saturday_base: float = 700.0  # Saturday
    sunday_base: float = 1000.0  # Sunday
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values after object creation"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'weekday_base': self.weekday_base,
            'saturday_base': self.saturday_base,
            'sunday_base': self.sunday_base,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseIncomeSettings':
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

        # Ensure numeric fields are properly converted to float
        if 'weekday_base' in data:
            data['weekday_base'] = float(data['weekday_base'])
        if 'saturday_base' in data:
            data['saturday_base'] = float(data['saturday_base'])
        if 'sunday_base' in data:
            data['sunday_base'] = float(data['sunday_base'])

        # Ensure boolean field is properly converted
        if 'is_active' in data:
            if isinstance(data['is_active'], str):
                data['is_active'] = data['is_active'].lower() in ('true', '1', 'yes')
            else:
                data['is_active'] = bool(data['is_active'])

        return cls(**data)

    def get_base_for_date(self, target_date: date) -> float:
        """Get base income target for a specific date"""
        weekday = target_date.weekday()  # 0=Monday, 6=Sunday

        if weekday == 5:  # Saturday
            return self.saturday_base
        elif weekday == 6:  # Sunday
            return self.sunday_base
        else:  # Monday to Friday
            return self.weekday_base


class IncomeDataModel:
    """Data model for income goal management"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.module_name = "income"
        self.income_filename = "income_records.csv"
        self.goals_filename = "goal_settings.csv"

        # Cache for reducing redundant file reads and warnings
        self._income_records_cache = None
        self._cache_timestamp = None
        self._cache_duration = 30  # Increased cache duration to 30 seconds for better performance

        # Cache for base income settings to avoid repeated CSV reads
        self._base_income_settings_cache = None
        self._base_settings_cache_timestamp = None
        self._base_settings_cache_duration = 300  # Cache base settings for 5 minutes
        
        # Default columns for income records CSV
        self.income_columns = [
            'id', 'date', 'zomato', 'swiggy', 'shadow_fax', 'pc_repair',
            'settings', 'youtube', 'gp_links', 'id_sales', 'other_sources',
            'extra_work', 'earned', 'status', 'goal_inc', 'progress', 'extra',
            'notes', 'created_at', 'updated_at'
        ]

        # Weekly targets columns
        self.weekly_targets_filename = "weekly_targets.csv"
        self.weekly_targets_columns = [
            'id', 'week_start', 'monday_target', 'tuesday_target', 'wednesday_target',
            'thursday_target', 'friday_target', 'saturday_target', 'sunday_target',
            'weekly_target', 'is_active', 'created_at'
        ]

        # Monthly summary columns
        self.monthly_summary_filename = "monthly_summary.csv"
        self.monthly_summary_columns = [
            'id', 'month', 'monthly_target', 'total_earned', 'zomato_earned',
            'swiggy_earned', 'shadow_fax_earned', 'pc_repair_earned', 'settings_earned',
            'youtube_earned', 'gp_links_earned', 'id_sales_earned', 'other_sources_earned',
            'extra_work_earned', 'progress_percentage', 'days_completed', 'days_in_month',
            'average_daily', 'created_at'
        ]
        
        # Default columns for goal settings CSV
        self.goals_columns = [
            'id', 'name', 'period', 'amount', 'start_date', 'end_date',
            'is_active', 'description', 'created_at'
        ]

        # Source weightage history columns
        self.weightage_history_filename = "source_weightage_history.csv"
        self.weightage_history_columns = [
            'id', 'date', 'source_name', 'weightage_percentage', 'total_earned',
            'period_type', 'notes', 'created_at'
        ]

        # Base income settings columns
        self.base_income_filename = "base_income_settings.csv"
        self.base_income_columns = [
            'id', 'weekday_base', 'saturday_base', 'sunday_base',
            'is_active', 'created_at', 'updated_at'
        ]
        
        # Initialize default goal if not exists
        self._initialize_default_goal()
    
    def _initialize_default_goal(self):
        """Initialize default goal if it doesn't exist"""
        if not self.data_manager.file_exists(self.module_name, self.goals_filename):
            default_goal = GoalSetting(
                name="Default Daily Goal",
                period="Daily",
                amount=1000.0,
                description="Default daily income goal"
            )
            
            df = pd.DataFrame([default_goal.to_dict()])
            self.data_manager.write_csv(self.module_name, self.goals_filename, df)
    
    def get_all_income_records(self) -> pd.DataFrame:
        """Get all income records with caching to reduce file I/O"""
        from datetime import datetime

        # Check if cache is valid
        current_time = datetime.now()
        if (self._income_records_cache is not None and
            self._cache_timestamp is not None and
            (current_time - self._cache_timestamp).total_seconds() < self._cache_duration):
            return self._income_records_cache

        # Cache miss or expired - read from file
        df = self.data_manager.read_csv(
            self.module_name,
            self.income_filename,
            self.income_columns
        )

        # Update cache
        self._income_records_cache = df
        self._cache_timestamp = current_time

        return df

    def _invalidate_cache(self):
        """Invalidate all caches when data changes"""
        self._income_records_cache = None
        self._cache_timestamp = None
        self._base_income_settings_cache = None
        self._base_settings_cache_timestamp = None

    def add_income_record(self, income: IncomeRecord) -> bool:
        """Add a new income record"""
        errors = income.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False
        
        result = self.data_manager.append_row(
            self.module_name,
            self.income_filename,
            income.to_dict(),
            self.income_columns
        )

        # Invalidate cache when data changes
        if result:
            self._invalidate_cache()  # Invalidate cache when data changes

        return result
    
    def update_income_record(self, income_id: int, income: IncomeRecord) -> bool:
        """Update an existing income record"""
        errors = income.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False
        
        result = self.data_manager.update_row(
            self.module_name,
            self.income_filename,
            income_id,
            income.to_dict()
        )

        # Invalidate cache when data changes
        if result:
            self._invalidate_cache()

        return result
    
    def delete_income_record(self, income_id: int) -> bool:
        """Delete an income record"""
        result = self.data_manager.delete_row(
            self.module_name,
            self.income_filename,
            income_id
        )

        # Invalidate cache when data changes
        if result:
            self._invalidate_cache()

        return result

    def get_income_record_by_id(self, record_id: int) -> Optional[IncomeRecord]:
        """Get income record by ID"""
        df = self.get_all_income_records()
        if df.empty:
            return None

        # Filter by ID
        matching_records = df[df['id'] == record_id]

        if matching_records.empty:
            return None

        # Return the first matching record
        record_data = matching_records.iloc[0].to_dict()
        return IncomeRecord.from_dict(record_data)

    def get_income_record_by_date(self, target_date: date) -> Optional[IncomeRecord]:
        """Get income record for a specific date"""
        df = self.get_all_income_records()
        if df.empty:
            return None
        
        # Convert date column to datetime for comparison
        df['date'] = pd.to_datetime(df['date'])
        target_timestamp = pd.Timestamp(target_date)
        
        record_data = df[df['date'] == target_timestamp]
        if record_data.empty:
            return None
        
        return IncomeRecord.from_dict(record_data.iloc[0].to_dict())
    
    def get_or_create_today_record(self) -> IncomeRecord:
        """Get today's income record or create a new one"""
        today = date.today()
        record = self.get_income_record_by_date(today)
        
        if record is None:
            # Create new record with current goal
            current_goal = self.get_current_daily_goal()
            record = IncomeRecord(
                date=today,
                goal_inc=current_goal
            )
            # Don't save yet, let the caller decide
        
        return record

    def get_income_records_by_date_range(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get income records within a date range"""
        df = self.get_all_income_records()
        if df.empty:
            return df

        # Convert date column to datetime for filtering
        df['date'] = pd.to_datetime(df['date'])

        # Filter by date range
        mask = (df['date'] >= pd.Timestamp(start_date)) & (df['date'] <= pd.Timestamp(end_date))
        return df[mask]

    def get_current_monthly_goal(self) -> float:
        """Get current active monthly goal"""
        goals_df = self.get_all_goals()
        if goals_df.empty:
            return 30000.0  # Default monthly goal (₹30,000)

        # Filter for active monthly goals
        active_monthly_goals = goals_df[
            (goals_df['is_active'] == True) &
            (goals_df['period'] == 'Monthly')
        ]

        if active_monthly_goals.empty:
            return 30000.0  # Default monthly goal

        # Return the most recent active monthly goal
        return float(active_monthly_goals.iloc[-1]['amount'])

    def get_current_daily_goal(self) -> float:
        """Get current daily goal (auto-calculated from monthly goal)"""
        monthly_goal = self.get_current_monthly_goal()

        # Get current month's days
        today = date.today()
        days_in_month = calendar.monthrange(today.year, today.month)[1]

        return monthly_goal / days_in_month

    def get_current_yearly_goal(self) -> float:
        """Get current yearly goal (auto-calculated from monthly goal)"""
        monthly_goal = self.get_current_monthly_goal()
        return monthly_goal * 12

    def get_all_goals(self) -> pd.DataFrame:
        """Get all goal settings"""
        return self.data_manager.read_csv(
            self.module_name,
            self.goals_filename,
            self.goals_columns
        )

    def add_goal(self, goal: GoalSetting) -> bool:
        """Add a new goal setting"""
        return self.data_manager.append_row(
            self.module_name,
            self.goals_filename,
            goal.to_dict(),
            self.goals_columns
        )

    def update_goal(self, goal_id: int, goal: GoalSetting) -> bool:
        """Update an existing goal setting"""
        return self.data_manager.update_row(
            self.module_name,
            self.goals_filename,
            goal_id,
            goal.to_dict()
        )

    def delete_goal(self, goal_id: int) -> bool:
        """Delete a goal setting"""
        return self.data_manager.delete_row(
            self.module_name,
            self.goals_filename,
            goal_id
        )

    def get_income_source_analysis(self, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get detailed income source contribution analysis"""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)  # Last 30 days
        if end_date is None:
            end_date = date.today()

        df = self.get_income_records_by_date_range(start_date, end_date)

        if df.empty:
            return self._empty_source_analysis()

        # Income sources to analyze
        sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings',
                  'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']

        source_analysis = {}
        total_earned = float(df['earned'].sum())

        for source in sources:
            if source in df.columns:
                source_total = float(df[source].sum())
                source_avg = float(df[source].mean())
                source_percentage = (source_total / total_earned * 100) if total_earned > 0 else 0

                # Calculate consistency (days with earnings from this source)
                days_with_earnings = len(df[df[source] > 0])
                total_days = len(df)
                consistency = (days_with_earnings / total_days * 100) if total_days > 0 else 0

                # Calculate trend (comparing first half vs second half of period)
                mid_point = len(df) // 2
                if mid_point > 0:
                    first_half_avg = float(df[source].iloc[:mid_point].mean())
                    second_half_avg = float(df[source].iloc[mid_point:].mean())
                    trend = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
                else:
                    trend = 0

                source_analysis[source] = {
                    'total': source_total,
                    'average_daily': source_avg,
                    'percentage': source_percentage,
                    'consistency': consistency,
                    'trend': trend,
                    'days_active': days_with_earnings,
                    'best_day': float(df[source].max()),
                    'worst_day': float(df[source].min())
                }

        # Calculate source rankings
        source_rankings = {
            'by_total': sorted(source_analysis.items(), key=lambda x: x[1]['total'], reverse=True),
            'by_percentage': sorted(source_analysis.items(), key=lambda x: x[1]['percentage'], reverse=True),
            'by_consistency': sorted(source_analysis.items(), key=lambda x: x[1]['consistency'], reverse=True),
            'by_trend': sorted(source_analysis.items(), key=lambda x: x[1]['trend'], reverse=True)
        }

        return {
            'period': {'start': start_date, 'end': end_date},
            'total_earned': total_earned,
            'sources': source_analysis,
            'rankings': source_rankings,
            'top_performer': source_rankings['by_total'][0] if source_rankings['by_total'] else None,
            'most_consistent': source_rankings['by_consistency'][0] if source_rankings['by_consistency'] else None,
            'fastest_growing': source_rankings['by_trend'][0] if source_rankings['by_trend'] else None
        }

    def _empty_source_analysis(self) -> Dict[str, Any]:
        """Return empty source analysis structure"""
        return {
            'period': {'start': date.today(), 'end': date.today()},
            'total_earned': 0.0,
            'sources': {},
            'rankings': {'by_total': [], 'by_percentage': [], 'by_consistency': [], 'by_trend': []},
            'top_performer': None,
            'most_consistent': None,
            'fastest_growing': None
        }

    def calculate_optimal_source_targets(self, total_daily_goal: float, analysis_period_days: int = 30) -> Dict[str, float]:
        """Calculate optimal daily targets for each income source based on historical performance"""
        source_analysis = self.get_income_source_analysis(
            start_date=date.today() - timedelta(days=analysis_period_days),
            end_date=date.today()
        )

        sources = source_analysis['sources']
        if not sources:
            return self._default_source_targets(total_daily_goal)

        # Calculate weightage based on historical performance
        total_historical_avg = sum(source['average_daily'] for source in sources.values())

        if total_historical_avg == 0:
            return self._default_source_targets(total_daily_goal)

        optimal_targets = {}
        for source_name, source_data in sources.items():
            # Base weightage on historical average
            historical_weight = source_data['average_daily'] / total_historical_avg

            # Adjust for consistency (more consistent sources get slightly higher targets)
            consistency_factor = 1 + (source_data['consistency'] / 100 * 0.1)  # Up to 10% bonus

            # Adjust for trend (growing sources get slightly higher targets)
            trend_factor = 1 + (max(-0.2, min(0.2, source_data['trend'] / 100)))  # ±20% max adjustment

            # Calculate final target
            adjusted_weight = historical_weight * consistency_factor * trend_factor
            optimal_targets[source_name] = total_daily_goal * adjusted_weight

        # Normalize to ensure total equals daily goal
        total_allocated = sum(optimal_targets.values())
        if total_allocated > 0:
            normalization_factor = total_daily_goal / total_allocated
            for source in optimal_targets:
                optimal_targets[source] *= normalization_factor

        return optimal_targets

    def _default_source_targets(self, total_daily_goal: float) -> Dict[str, float]:
        """Return default source targets when no historical data is available"""
        # Default allocation based on typical delivery patterns
        default_weights = {
            'zomato': 0.35,      # 35%
            'swiggy': 0.30,      # 30%
            'shadow_fax': 0.15,  # 15%
            'pc_repair': 0.05,   # 5%
            'settings': 0.02,    # 2%
            'youtube': 0.03,     # 3%
            'gp_links': 0.02,    # 2%
            'id_sales': 0.03,    # 3%
            'other_sources': 0.03, # 3%
            'extra_work': 0.02   # 2%
        }

        return {source: total_daily_goal * weight for source, weight in default_weights.items()}

    def get_source_performance_recommendations(self, analysis_period_days: int = 30) -> List[str]:
        """Get recommendations for improving income source performance"""
        source_analysis = self.get_income_source_analysis(
            start_date=date.today() - timedelta(days=analysis_period_days),
            end_date=date.today()
        )

        recommendations = []
        sources = source_analysis['sources']

        if not sources:
            recommendations.append("Start tracking income sources to get personalized recommendations")
            return recommendations

        # Find underperforming sources
        avg_consistency = sum(s['consistency'] for s in sources.values()) / len(sources)
        for source_name, source_data in sources.items():
            if source_data['consistency'] < avg_consistency * 0.7:  # 30% below average
                recommendations.append(f"📈 {source_name.replace('_', ' ').title()}: Low consistency ({source_data['consistency']:.1f}%) - try to earn from this source more regularly")

        # Find declining sources
        for source_name, source_data in sources.items():
            if source_data['trend'] < -10:  # Declining by more than 10%
                recommendations.append(f"📉 {source_name.replace('_', ' ').title()}: Declining trend ({source_data['trend']:.1f}%) - investigate what's causing the decrease")

        # Find growing sources to focus on
        growing_sources = [(name, data) for name, data in sources.items() if data['trend'] > 10]
        if growing_sources:
            best_growing = max(growing_sources, key=lambda x: x[1]['trend'])
            recommendations.append(f"🚀 {best_growing[0].replace('_', ' ').title()}: Strong growth ({best_growing[1]['trend']:.1f}%) - consider focusing more effort here")

        # Check for over-dependence on single source
        top_source = max(sources.items(), key=lambda x: x[1]['percentage'])
        if top_source[1]['percentage'] > 60:
            recommendations.append(f"⚠️ Over-dependence on {top_source[0].replace('_', ' ').title()} ({top_source[1]['percentage']:.1f}%) - diversify income sources for stability")

        # General recommendations
        if len([s for s in sources.values() if s['consistency'] > 80]) < 3:
            recommendations.append("🎯 Focus on building consistency in at least 3 income sources")

        if not recommendations:
            recommendations.append("✅ Great job! Your income sources are well-balanced and performing consistently")

        return recommendations

    def get_income_summary(self) -> Dict[str, Any]:
        """Get income summary statistics"""
        df = self.get_all_income_records()

        if df.empty:
            return {
                'total_records': 0,
                'total_earned': 0.0,
                'average_daily': 0.0,
                'current_goal': self.get_current_daily_goal(),
                'this_month_earned': 0.0,
                'this_week_earned': 0.0,
                'goal_achievement_rate': 0.0,
                'best_day_amount': 0.0,
                'streak_days': 0
            }

        # Convert date column
        df['date'] = pd.to_datetime(df['date'])

        # Calculate summary statistics
        total_records = len(df)
        total_earned = df['earned'].sum()
        average_daily = df['earned'].mean()
        current_goal = self.get_current_daily_goal()

        # This month earnings
        current_month = datetime.now().replace(day=1)
        this_month_df = df[df['date'] >= current_month]
        this_month_earned = this_month_df['earned'].sum()

        # This week earnings
        current_week = datetime.now() - timedelta(days=7)
        this_week_df = df[df['date'] >= current_week]
        this_week_earned = this_week_df['earned'].sum()

        # Goal achievement rate
        completed_goals = len(df[df['status'].isin(['Completed', 'Exceeded'])])
        goal_achievement_rate = (completed_goals / total_records * 100) if total_records > 0 else 0

        # Best day amount
        best_day_amount = df['earned'].max() if not df.empty else 0.0

        # Calculate streak (consecutive days with goals met)
        streak_days = self._calculate_goal_streak(df)

        return {
            'total_records': total_records,
            'total_earned': float(total_earned),
            'average_daily': float(average_daily),
            'current_goal': current_goal,
            'this_month_earned': float(this_month_earned),
            'this_week_earned': float(this_week_earned),
            'goal_achievement_rate': float(goal_achievement_rate),
            'best_day_amount': float(best_day_amount),
            'streak_days': streak_days
        }

    def _calculate_goal_streak(self, df: pd.DataFrame) -> int:
        """Calculate current goal achievement streak"""
        if df.empty:
            return 0

        # Sort by date descending
        df_sorted = df.sort_values('date', ascending=False)

        streak = 0
        for _, record in df_sorted.iterrows():
            if record['status'] in ['Completed', 'Exceeded']:
                streak += 1
            else:
                break

        return streak

    def get_weekly_summary(self, start_date: date = None) -> Dict[str, Any]:
        """Get weekly summary starting from start_date"""
        if start_date is None:
            # Start from Monday of current week
            today = date.today()
            start_date = today - timedelta(days=today.weekday())

        end_date = start_date + timedelta(days=6)

        df = self.get_income_records_by_date_range(start_date, end_date)

        weekly_data = {
            'start_date': start_date,
            'end_date': end_date,
            'total_earned': 0.0,
            'total_goal': 0.0,
            'days_completed': 0,
            'daily_breakdown': []
        }

        current_goal = self.get_current_daily_goal()

        for i in range(7):
            current_date = start_date + timedelta(days=i)
            day_record = df[pd.to_datetime(df['date']).dt.date == current_date] if not df.empty else pd.DataFrame()

            if not day_record.empty:
                day_data = day_record.iloc[0]
                earned = float(day_data['earned'])
                status = day_data['status']
            else:
                earned = 0.0
                status = 'Pending'

            day_info = {
                'date': current_date,
                'day_name': current_date.strftime('%A'),
                'earned': earned,
                'goal': current_goal,
                'status': status,
                'progress': (earned / current_goal * 100) if current_goal > 0 else 0
            }

            weekly_data['daily_breakdown'].append(day_info)
            weekly_data['total_earned'] += earned
            weekly_data['total_goal'] += current_goal

            if status in ['Completed', 'Exceeded']:
                weekly_data['days_completed'] += 1

        weekly_data['week_progress'] = (weekly_data['total_earned'] / weekly_data['total_goal'] * 100) if weekly_data['total_goal'] > 0 else 0

        return weekly_data

    def get_monthly_summary(self, month_date: date = None) -> Dict[str, Any]:
        """Get monthly summary for specified month"""
        if month_date is None:
            month_date = date.today().replace(day=1)

        year = month_date.year
        month = month_date.month

        # Get first and last day of month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        df = self.get_income_records_by_date_range(start_date, end_date)

        # Calculate working days (excluding weekends)
        working_days = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday=0 to Friday=4
                working_days += 1
            current_date += timedelta(days=1)

        monthly_data = {
            'month_date': month_date,
            'year': year,
            'month': month,
            'month_name': start_date.strftime('%B'),
            'start_date': start_date,
            'end_date': end_date,
            'total_earned': 0.0,
            'goal_amount': 0.0,
            'working_days': working_days,
            'days_completed': 0,
            'total_days': (end_date - start_date).days + 1,
            'average_daily': 0.0,
            'weekly_breakdown': []
        }

        if not df.empty:
            monthly_data['total_earned'] = float(df['earned'].sum())
            monthly_data['days_completed'] = len(df[df['status'].isin(['Completed', 'Exceeded'])])
            monthly_data['average_daily'] = float(df['earned'].mean())

        current_goal = self.get_current_daily_goal()
        monthly_data['goal_amount'] = current_goal * working_days
        monthly_data['month_progress'] = (monthly_data['total_earned'] / monthly_data['goal_amount'] * 100) if monthly_data['goal_amount'] > 0 else 0

        # Add weekly breakdown
        week_start = start_date
        week_number = 1
        while week_start <= end_date:
            week_end = min(week_start + timedelta(days=6), end_date)

            week_df = df[(df['date'] >= week_start.strftime('%Y-%m-%d')) &
                        (df['date'] <= week_end.strftime('%Y-%m-%d'))]

            week_earned = float(week_df['earned'].sum()) if not week_df.empty else 0.0
            week_goal = current_goal * 7  # Weekly goal
            week_progress = (week_earned / week_goal * 100) if week_goal > 0 else 0

            week_data = {
                'week_number': week_number,
                'date_range': f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}",
                'earned': week_earned,
                'progress': week_progress,
                'status': 'Good' if week_progress >= 80 else 'Average' if week_progress >= 50 else 'Low'
            }
            monthly_data['weekly_breakdown'].append(week_data)

            week_start = week_end + timedelta(days=1)
            week_number += 1

        return monthly_data

    def get_yearly_summary(self, year: int = None) -> Dict[str, Any]:
        """Get yearly summary for specified year"""
        if year is None:
            year = datetime.now().year

        # Get records for the entire year
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        df = self.get_income_records_by_date_range(start_date, end_date)

        yearly_data = {
            'year': year,
            'total_earned': 0.0,
            'months_with_data': 0,
            'annual_goal': 0.0,
            'best_month_amount': 0.0,
            'monthly_breakdown': []
        }

        if not df.empty:
            yearly_data['total_earned'] = float(df['earned'].sum())

            # Get monthly breakdown
            monthly_totals = []
            for month in range(1, 13):
                month_start = date(year, month, 1)
                if month == 12:
                    month_end = date(year, 12, 31)
                else:
                    month_end = date(year, month + 1, 1) - timedelta(days=1)

                month_df = df[(df['date'] >= month_start.strftime('%Y-%m-%d')) &
                             (df['date'] <= month_end.strftime('%Y-%m-%d'))]

                month_total = float(month_df['earned'].sum()) if not month_df.empty else 0.0
                monthly_totals.append(month_total)

                # Add to monthly breakdown
                month_data = {
                    'month_name': month_start.strftime('%B'),
                    'year': year,
                    'earned': month_total,
                    'progress': 0,  # Will be calculated below
                    'status': 'No Data' if month_df.empty else 'Has Data'
                }
                yearly_data['monthly_breakdown'].append(month_data)

            # Calculate statistics
            yearly_data['months_with_data'] = len([total for total in monthly_totals if total > 0])
            yearly_data['best_month_amount'] = max(monthly_totals) if monthly_totals else 0.0

        # Calculate annual goal (daily goal * 365)
        current_goal = self.get_current_daily_goal()
        yearly_data['annual_goal'] = current_goal * 365

        # Update progress for monthly breakdown
        monthly_goal = yearly_data['annual_goal'] / 12 if yearly_data['annual_goal'] > 0 else 1
        for month_data in yearly_data['monthly_breakdown']:
            month_data['progress'] = (month_data['earned'] / monthly_goal * 100) if monthly_goal > 0 else 0

        return yearly_data

    # Weekly Targets Methods
    def get_weekly_targets(self) -> pd.DataFrame:
        """Get all weekly targets"""
        return self.data_manager.read_csv(
            self.module_name,
            self.weekly_targets_filename,
            self.weekly_targets_columns
        )

    def add_weekly_target(self, target: WeeklyGoalTarget) -> bool:
        """Add a new weekly target"""
        return self.data_manager.append_row(
            self.module_name,
            self.weekly_targets_filename,
            target.to_dict(),
            self.weekly_targets_columns
        )

    def get_current_weekly_target(self) -> WeeklyGoalTarget:
        """Get the current week's target"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        targets_df = self.get_weekly_targets()
        if not targets_df.empty:
            # Look for target for current week
            current_week_targets = targets_df[
                (targets_df['week_start'] == week_start.strftime('%Y-%m-%d')) &
                (targets_df['is_active'] == True)
            ]

            if not current_week_targets.empty:
                return WeeklyGoalTarget.from_dict(current_week_targets.iloc[-1].to_dict())

        # Create default weekly target if none exists
        default_target = WeeklyGoalTarget(week_start=week_start)
        self.add_weekly_target(default_target)
        return default_target

    def get_daily_target_for_date(self, target_date: date) -> float:
        """Get the target amount for a specific date"""
        weekly_target = self.get_current_weekly_target()
        return weekly_target.get_target_for_date(target_date)

    # Monthly Summary Methods
    def get_monthly_summaries(self) -> pd.DataFrame:
        """Get all monthly summaries"""
        return self.data_manager.read_csv(
            self.module_name,
            self.monthly_summary_filename,
            self.monthly_summary_columns
        )

    def calculate_monthly_summary(self, month: date) -> MonthlyGoalSummary:
        """Calculate monthly summary for a given month"""
        # Get all income records for the month
        income_df = self.get_all_income_records()
        if income_df.empty:
            return MonthlyGoalSummary(month=month)

        # Convert date column
        income_df['date'] = pd.to_datetime(income_df['date'])

        # Filter for the specific month
        month_start = month.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_df = income_df[
            (income_df['date'] >= month_start) &
            (income_df['date'] < next_month)
        ]

        if month_df.empty:
            return MonthlyGoalSummary(month=month)

        # Calculate totals
        summary = MonthlyGoalSummary(
            month=month,
            total_earned=float(month_df['earned'].sum()),
            zomato_earned=float(month_df['zomato'].sum()),
            swiggy_earned=float(month_df['swiggy'].sum()),
            shadow_fax_earned=float(month_df['shadow_fax'].sum()),
            pc_repair_earned=float(month_df['pc_repair'].sum()) if 'pc_repair' in month_df.columns else 0.0,
            settings_earned=float(month_df['settings'].sum()) if 'settings' in month_df.columns else 0.0,
            youtube_earned=float(month_df['youtube'].sum()) if 'youtube' in month_df.columns else 0.0,
            gp_links_earned=float(month_df['gp_links'].sum()) if 'gp_links' in month_df.columns else 0.0,
            id_sales_earned=float(month_df['id_sales'].sum()) if 'id_sales' in month_df.columns else 0.0,
            other_sources_earned=float(month_df['other_sources'].sum()),
            extra_work_earned=float(month_df['extra_work'].sum()) if 'extra_work' in month_df.columns else 0.0,
            days_completed=len(month_df),
            days_in_month=(next_month - month_start).days
        )

        return summary

    def save_monthly_summary(self, summary: MonthlyGoalSummary) -> bool:
        """Save monthly summary"""
        return self.data_manager.append_row(
            self.module_name,
            self.monthly_summary_filename,
            summary.to_dict(),
            self.monthly_summary_columns
        )

    def record_source_weightage_snapshot(self, period_type: str = "monthly", notes: str = ""):
        """Record a snapshot of current source weightages for historical tracking"""
        try:
            # Get current period analysis
            if period_type == "monthly":
                start_date = date.today().replace(day=1)
                end_date = date.today()
            elif period_type == "weekly":
                today = date.today()
                start_date = today - timedelta(days=today.weekday())
                end_date = today
            else:  # daily
                start_date = end_date = date.today()

            analysis = self.get_income_source_analysis(start_date, end_date)
            sources = analysis.get('sources', {})

            # Record weightage for each source
            for source_name, source_data in sources.items():
                weightage_record = SourceWeightageHistory(
                    date=end_date,
                    source_name=source_name,
                    weightage_percentage=source_data['percentage'],
                    total_earned=source_data['total'],
                    period_type=period_type,
                    notes=notes
                )

                self.add_weightage_history_record(weightage_record)

            return True

        except Exception as e:
            print(f"Error recording weightage snapshot: {e}")
            return False

    def add_weightage_history_record(self, record: SourceWeightageHistory) -> bool:
        """Add a weightage history record"""
        return self.data_manager.append_row(
            self.module_name,
            self.weightage_history_filename,
            record.to_dict(),
            self.weightage_history_columns
        )

    def get_weightage_history(self, source_name: str = None, period_type: str = None,
                             start_date: date = None, end_date: date = None) -> pd.DataFrame:
        """Get weightage history with optional filtering"""
        df = self.data_manager.read_csv(
            self.module_name,
            self.weightage_history_filename,
            self.weightage_history_columns
        )

        if df.empty:
            return df

        # Apply filters
        if source_name:
            df = df[df['source_name'] == source_name]

        if period_type:
            df = df[df['period_type'] == period_type]

        if start_date:
            df = df[pd.to_datetime(df['date']).dt.date >= start_date]

        if end_date:
            df = df[pd.to_datetime(df['date']).dt.date <= end_date]

        return df.sort_values('date')

    def get_year_over_year_comparison(self, current_year: int = None) -> Dict[str, Any]:
        """Get year-over-year comparison of income source contributions"""
        if current_year is None:
            current_year = date.today().year

        previous_year = current_year - 1

        # Get data for both years
        current_year_start = date(current_year, 1, 1)
        current_year_end = date(current_year, 12, 31)
        previous_year_start = date(previous_year, 1, 1)
        previous_year_end = date(previous_year, 12, 31)

        current_analysis = self.get_income_source_analysis(current_year_start, current_year_end)
        previous_analysis = self.get_income_source_analysis(previous_year_start, previous_year_end)

        comparison = {
            'current_year': current_year,
            'previous_year': previous_year,
            'current_total': current_analysis.get('total_earned', 0),
            'previous_total': previous_analysis.get('total_earned', 0),
            'source_comparisons': {},
            'summary': {}
        }

        # Compare each source
        current_sources = current_analysis.get('sources', {})
        previous_sources = previous_analysis.get('sources', {})

        all_sources = set(current_sources.keys()) | set(previous_sources.keys())

        for source in all_sources:
            current_data = current_sources.get(source, {'total': 0, 'percentage': 0})
            previous_data = previous_sources.get(source, {'total': 0, 'percentage': 0})

            current_total = current_data['total']
            previous_total = previous_data['total']
            current_percentage = current_data['percentage']
            previous_percentage = previous_data['percentage']

            # Calculate changes
            total_change = current_total - previous_total
            total_change_percent = ((current_total - previous_total) / previous_total * 100) if previous_total > 0 else 0
            percentage_point_change = current_percentage - previous_percentage

            comparison['source_comparisons'][source] = {
                'current_total': current_total,
                'previous_total': previous_total,
                'total_change': total_change,
                'total_change_percent': total_change_percent,
                'current_percentage': current_percentage,
                'previous_percentage': previous_percentage,
                'percentage_point_change': percentage_point_change,
                'status': self._get_change_status(total_change_percent, percentage_point_change)
            }

        # Generate summary insights
        comparison['summary'] = self._generate_yoy_summary(comparison)

        return comparison

    def _get_change_status(self, total_change_percent: float, percentage_point_change: float) -> str:
        """Get status description for year-over-year changes"""
        if total_change_percent > 20 and percentage_point_change > 5:
            return "Significantly Growing"
        elif total_change_percent > 10 and percentage_point_change > 2:
            return "Growing"
        elif total_change_percent > -10 and abs(percentage_point_change) < 2:
            return "Stable"
        elif total_change_percent < -10 and percentage_point_change < -2:
            return "Declining"
        elif total_change_percent < -20 and percentage_point_change < -5:
            return "Significantly Declining"
        else:
            return "Mixed"

    def _generate_yoy_summary(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary insights from year-over-year comparison"""
        source_comparisons = comparison['source_comparisons']

        # Find biggest winners and losers
        biggest_gainer = max(source_comparisons.items(),
                           key=lambda x: x[1]['total_change_percent'], default=(None, None))
        biggest_loser = min(source_comparisons.items(),
                          key=lambda x: x[1]['total_change_percent'], default=(None, None))

        # Count status categories
        status_counts = {}
        for source_data in source_comparisons.values():
            status = source_data['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        # Calculate overall growth
        current_total = comparison['current_total']
        previous_total = comparison['previous_total']
        overall_growth = ((current_total - previous_total) / previous_total * 100) if previous_total > 0 else 0

        return {
            'overall_growth_percent': overall_growth,
            'biggest_gainer': biggest_gainer[0] if biggest_gainer[0] else None,
            'biggest_gainer_change': biggest_gainer[1]['total_change_percent'] if biggest_gainer[0] else 0,
            'biggest_loser': biggest_loser[0] if biggest_loser[0] else None,
            'biggest_loser_change': biggest_loser[1]['total_change_percent'] if biggest_loser[0] else 0,
            'status_distribution': status_counts,
            'diversification_trend': self._analyze_diversification_trend(source_comparisons)
        }

    def _analyze_diversification_trend(self, source_comparisons: Dict[str, Any]) -> str:
        """Analyze if income is becoming more or less diversified"""
        # Calculate concentration changes
        current_percentages = [data['current_percentage'] for data in source_comparisons.values()]
        previous_percentages = [data['previous_percentage'] for data in source_comparisons.values()]

        # Simple concentration measure: sum of squares of percentages
        current_concentration = sum(p**2 for p in current_percentages) / 100
        previous_concentration = sum(p**2 for p in previous_percentages) / 100

        if current_concentration < previous_concentration * 0.9:
            return "More Diversified"
        elif current_concentration > previous_concentration * 1.1:
            return "Less Diversified"
        else:
            return "Similar Diversification"

    def get_current_base_income_settings(self) -> BaseIncomeSettings:
        """Get current active base income settings with enhanced caching"""
        from datetime import datetime

        try:
            # Check if cache is valid
            current_time = datetime.now()
            if (self._base_income_settings_cache is not None and
                self._base_settings_cache_timestamp is not None and
                (current_time - self._base_settings_cache_timestamp).total_seconds() < self._base_settings_cache_duration):
                return self._base_income_settings_cache

            # Cache miss or expired - read from file
            df = self.data_manager.read_csv(
                self.module_name,
                self.base_income_filename,
                self.base_income_columns
            )

            if df.empty:
                # Return default settings
                settings = BaseIncomeSettings()
            else:
                # Get the most recent active settings
                active_settings = df[df['is_active'] == True]
                if active_settings.empty:
                    settings = BaseIncomeSettings()
                else:
                    latest_settings = active_settings.iloc[-1]
                    settings_dict = latest_settings.to_dict()
                    settings = BaseIncomeSettings.from_dict(settings_dict)

            # Update cache
            self._base_income_settings_cache = settings
            self._base_settings_cache_timestamp = current_time

            return settings

        except Exception as e:
            print(f"Error getting base income settings: {e}")
            return BaseIncomeSettings()

    def update_base_income_settings(self, settings: BaseIncomeSettings) -> bool:
        """Update base income settings"""
        try:
            # Deactivate existing settings
            df = self.data_manager.read_csv(
                self.module_name,
                self.base_income_filename,
                self.base_income_columns
            )

            if not df.empty:
                # Mark all existing as inactive
                df['is_active'] = False
                self.data_manager.write_csv(
                    self.module_name,
                    self.base_income_filename,
                    df
                )

            # Add new settings
            settings.is_active = True
            settings.updated_at = datetime.now()

            result = self.data_manager.append_row(
                self.module_name,
                self.base_income_filename,
                settings.to_dict(),
                self.base_income_columns
            )

            # Invalidate cache when settings are updated
            if result:
                self.invalidate_base_income_cache()

            return result

        except Exception as e:
            print(f"Error updating base income settings: {e}")
            return False

    def invalidate_base_income_cache(self):
        """Force invalidation of base income settings cache"""
        self._base_income_settings_cache = None
        self._base_settings_cache_timestamp = None
        print("Base income settings cache invalidated")

    def get_base_income_for_date(self, target_date: date) -> float:
        """Get base income target for a specific date"""
        settings = self.get_current_base_income_settings()
        return settings.get_base_for_date(target_date)

    def calculate_bonus_income(self, target_date: date, actual_earned: float) -> Dict[str, float]:
        """Calculate base vs bonus income for a specific date"""
        try:
            # Ensure actual_earned is a float
            actual_earned = float(actual_earned) if actual_earned is not None else 0.0

            base_target = self.get_base_income_for_date(target_date)
            base_target = float(base_target)  # Ensure it's a float

            bonus_amount = max(0.0, actual_earned - base_target)
            base_achieved = min(actual_earned, base_target)

            # Prevent division by zero
            if base_target > 0:
                base_percentage = (base_achieved / base_target) * 100
            else:
                base_percentage = 0.0

            result = {
                'base_target': float(base_target),
                'actual_earned': float(actual_earned),
                'bonus_amount': float(bonus_amount),
                'base_achieved': float(base_achieved),
                'base_percentage': float(base_percentage)
            }

            return result

        except Exception as e:
            print(f"Error calculating bonus income: {e}")
            # Ensure actual_earned is safe to use
            safe_actual = float(actual_earned) if actual_earned is not None else 0.0
            return {
                'base_target': 500.0,  # Default weekday base
                'actual_earned': safe_actual,
                'bonus_amount': max(0.0, safe_actual - 500.0),
                'base_achieved': min(safe_actual, 500.0),
                'base_percentage': (min(safe_actual, 500.0) / 500.0 * 100) if safe_actual > 0 else 0.0
            }

    def calculate_bulk_bonus_income(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate base vs bonus income for multiple records efficiently using vectorized operations"""
        try:
            if df.empty:
                return df

            # Ensure we have a copy to avoid modifying the original
            result_df = df.copy()

            # Convert date column to datetime if it's not already
            if 'date' in result_df.columns:
                result_df['date'] = pd.to_datetime(result_df['date'])

                # Check for weekly targets first, fall back to base income settings
                def get_target_for_date(row_date):
                    try:
                        # Find the Monday of the week containing this date
                        date_obj = row_date.date() if hasattr(row_date, 'date') else row_date
                        week_start = date_obj - timedelta(days=date_obj.weekday())
                        week_start_str = week_start.strftime('%Y-%m-%d')

                        # Check for weekly targets
                        targets_df = self.get_weekly_targets()
                        matching_targets = targets_df[
                            (targets_df['week_start'] == week_start_str) &
                            (targets_df['is_active'] == True)
                        ]

                        if not matching_targets.empty:
                            # Use configured weekly targets
                            target_row = matching_targets.iloc[-1]
                            day_name = date_obj.strftime('%A').lower()
                            day_targets = {
                                'monday': float(target_row['monday_target']),
                                'tuesday': float(target_row['tuesday_target']),
                                'wednesday': float(target_row['wednesday_target']),
                                'thursday': float(target_row['thursday_target']),
                                'friday': float(target_row['friday_target']),
                                'saturday': float(target_row['saturday_target']),
                                'sunday': float(target_row['sunday_target'])
                            }
                            return day_targets.get(day_name, 500.0)
                        else:
                            # Fall back to base income settings
                            settings = self.get_current_base_income_settings()
                            day_of_week = date_obj.weekday()
                            if day_of_week == 5:  # Saturday
                                return settings.saturday_base
                            elif day_of_week == 6:  # Sunday
                                return settings.sunday_base
                            else:  # Weekday
                                return settings.weekday_base
                    except:
                        # Fallback to default weekday target
                        return 500.0

                # Apply target calculation to each row
                result_df['base_target'] = result_df['date'].apply(get_target_for_date)

                # Vectorized bonus calculations
                result_df['earned'] = result_df['earned'].fillna(0.0).astype(float)
                result_df['base_achieved'] = result_df[['earned', 'base_target']].min(axis=1)
                result_df['bonus_amount'] = (result_df['earned'] - result_df['base_target']).clip(lower=0.0)
                result_df['base_percentage'] = (result_df['base_achieved'] / result_df['base_target'] * 100).fillna(0.0)

                # Clean up temporary columns if they exist
                columns_to_drop = [col for col in ['day_of_week'] if col in result_df.columns]
                if columns_to_drop:
                    result_df = result_df.drop(columns_to_drop, axis=1)

            return result_df

        except Exception as e:
            print(f"Error in bulk bonus calculation: {e}")
            return df

    def get_weekly_base_vs_bonus_summary(self, start_date: date = None) -> Dict[str, Any]:
        """Get weekly summary with base vs bonus breakdown - OPTIMIZED VERSION"""
        try:
            if start_date is None:
                today = date.today()
                start_date = today - timedelta(days=today.weekday())

            end_date = start_date + timedelta(days=6)

            try:
                df = self.get_income_records_by_date_range(start_date, end_date)
            except Exception as e:
                print(f"Error getting income records: {e}")
                df = pd.DataFrame()

            weekly_summary = {
                'start_date': start_date,
                'end_date': end_date,
                'total_base_target': 0.0,
                'total_base_achieved': 0.0,
                'total_bonus': 0.0,
                'total_earned': 0.0,
                'daily_breakdown': []
            }

            if not df.empty:
                # Use vectorized calculation for better performance
                df_with_bonus = self.calculate_bulk_bonus_income(df)

                # Check if bonus calculation was successful
                if 'base_target' in df_with_bonus.columns:
                    # Calculate totals using pandas aggregation
                    weekly_summary['total_earned'] = float(df_with_bonus['earned'].sum())
                    weekly_summary['total_base_target'] = float(df_with_bonus['base_target'].sum())
                    weekly_summary['total_base_achieved'] = float(df_with_bonus['base_achieved'].sum())
                    weekly_summary['total_bonus'] = float(df_with_bonus['bonus_amount'].sum())

                    # Create a lookup dictionary for faster daily breakdown
                    df_with_bonus['date'] = pd.to_datetime(df_with_bonus['date']).dt.date
                    daily_lookup = df_with_bonus.set_index('date').to_dict('index')
                else:
                    # Fallback calculation if bulk bonus calculation failed
                    weekly_summary['total_earned'] = float(df_with_bonus['earned'].sum())
                    settings = self.get_current_base_income_settings()
                    daily_lookup = {}

                    # Manual calculation for each record
                    for _, row in df_with_bonus.iterrows():
                        date_obj = pd.to_datetime(row['date']).date()
                        day_of_week = date_obj.weekday()
                        if day_of_week == 5:  # Saturday
                            base_target = settings.saturday_base
                        elif day_of_week == 6:  # Sunday
                            base_target = settings.sunday_base
                        else:  # Weekday
                            base_target = settings.weekday_base

                        earned = float(row['earned'])
                        base_achieved = min(earned, base_target)
                        bonus_amount = max(0.0, earned - base_target)
                        base_percentage = (base_achieved / base_target * 100) if base_target > 0 else 0.0

                        weekly_summary['total_base_target'] += base_target
                        weekly_summary['total_base_achieved'] += base_achieved
                        weekly_summary['total_bonus'] += bonus_amount

                        # Add to daily lookup
                        daily_lookup[date_obj] = {
                            'earned': earned,
                            'base_target': base_target,
                            'base_achieved': base_achieved,
                            'bonus_amount': bonus_amount,
                            'base_percentage': base_percentage
                        }
            else:
                daily_lookup = {}

            # Check for weekly targets first, fall back to base income settings
            try:
                targets_df = self.get_weekly_targets()
                week_start_str = start_date.strftime('%Y-%m-%d')
                matching_targets = targets_df[
                    (targets_df['week_start'] == week_start_str) &
                    (targets_df['is_active'] == True)
                ]

                if not matching_targets.empty:
                    # Use configured weekly targets
                    target_row = matching_targets.iloc[-1]
                    weekly_target_config = {
                        'monday': float(target_row['monday_target']),
                        'tuesday': float(target_row['tuesday_target']),
                        'wednesday': float(target_row['wednesday_target']),
                        'thursday': float(target_row['thursday_target']),
                        'friday': float(target_row['friday_target']),
                        'saturday': float(target_row['saturday_target']),
                        'sunday': float(target_row['sunday_target'])
                    }
                    use_weekly_targets = True
                else:
                    use_weekly_targets = False
                    settings = self.get_current_base_income_settings()
            except:
                use_weekly_targets = False
                settings = self.get_current_base_income_settings()

            # Generate daily breakdown (still need individual days for UI display)
            for i in range(7):
                current_date = start_date + timedelta(days=i)
                day_name = current_date.strftime('%A').lower()

                if current_date in daily_lookup:
                    # Use pre-calculated data
                    day_data = daily_lookup[current_date]
                    day_info = {
                        'date': current_date,
                        'day_name': current_date.strftime('%A'),
                        'base_target': float(day_data['base_target']),
                        'base_achieved': float(day_data['base_achieved']),
                        'bonus_amount': float(day_data['bonus_amount']),
                        'actual_earned': float(day_data['earned']),
                        'base_percentage': float(day_data['base_percentage'])
                    }
                else:
                    # No data for this day - calculate theoretical targets
                    if use_weekly_targets:
                        # Use configured weekly target for this day
                        base_target = weekly_target_config.get(day_name, 500.0)
                    else:
                        # Use base income settings
                        day_of_week = current_date.weekday()
                        if day_of_week == 5:  # Saturday
                            base_target = settings.saturday_base
                        elif day_of_week == 6:  # Sunday
                            base_target = settings.sunday_base
                        else:  # Weekday
                            base_target = settings.weekday_base

                    day_info = {
                        'date': current_date,
                        'day_name': current_date.strftime('%A'),
                        'base_target': base_target,
                        'base_achieved': 0.0,
                        'bonus_amount': 0.0,
                        'actual_earned': 0.0,
                        'base_percentage': 0.0
                    }

                    # Add to totals for days without data
                    weekly_summary['total_base_target'] += base_target

                weekly_summary['daily_breakdown'].append(day_info)

            return weekly_summary

        except Exception as e:
            print(f"Error in get_weekly_base_vs_bonus_summary: {e}")
            # Return safe default data
            if start_date is None:
                today = date.today()
                start_date = today - timedelta(days=today.weekday())

            end_date = start_date + timedelta(days=6)

            # Calculate default weekly base target from current settings
            settings = self.get_current_base_income_settings()
            default_weekly_target = (settings.weekday_base * 5 +
                                   settings.saturday_base +
                                   settings.sunday_base)

            return {
                'start_date': start_date,
                'end_date': end_date,
                'total_base_target': default_weekly_target,
                'total_base_achieved': 0.0,
                'total_bonus': 0.0,
                'total_earned': 0.0,
                'daily_breakdown': []
            }

    def get_smart_goal_recommendations(self, analysis_period_days: int = 30) -> Dict[str, Any]:
        """Get smart recommendations for goal adjustments based on performance analysis"""
        try:
            # Get recent performance data
            start_date = date.today() - timedelta(days=analysis_period_days)
            df = self.get_income_records_by_date_range(start_date, date.today())

            if df.empty:
                return self._empty_goal_recommendations()

            # Current goal
            current_goal = self.get_current_daily_goal()

            # Calculate performance metrics
            avg_daily_earned = float(df['earned'].mean())
            median_daily_earned = float(df['earned'].median())
            std_daily_earned = float(df['earned'].std())
            achievement_rate = len(df[df['earned'] >= current_goal]) / len(df) * 100

            # Calculate trend
            if len(df) >= 7:
                recent_week = df.tail(7)['earned'].mean()
                earlier_week = df.head(7)['earned'].mean()
                trend = ((recent_week - earlier_week) / earlier_week * 100) if earlier_week > 0 else 0
            else:
                trend = 0

            # Generate recommendations
            recommendations = {
                'current_goal': current_goal,
                'performance_metrics': {
                    'average_daily': avg_daily_earned,
                    'median_daily': median_daily_earned,
                    'standard_deviation': std_daily_earned,
                    'achievement_rate': achievement_rate,
                    'trend': trend
                },
                'recommended_adjustments': [],
                'goal_suggestions': {},
                'alerts': [],
                'confidence_score': 0
            }

            # Analyze and generate specific recommendations
            self._analyze_goal_performance(recommendations, df, current_goal)

            return recommendations

        except Exception as e:
            print(f"Error generating goal recommendations: {e}")
            return self._empty_goal_recommendations()

    def _analyze_goal_performance(self, recommendations: Dict[str, Any], df: pd.DataFrame, current_goal: float):
        """Analyze goal performance and generate specific recommendations"""
        metrics = recommendations['performance_metrics']
        avg_daily = metrics['average_daily']
        achievement_rate = metrics['achievement_rate']
        trend = metrics['trend']
        std_dev = metrics['standard_deviation']

        # Goal is too high if achievement rate is very low
        if achievement_rate < 30:
            new_goal = avg_daily * 1.1  # 10% above average
            recommendations['recommended_adjustments'].append({
                'type': 'decrease',
                'reason': f'Low achievement rate ({achievement_rate:.1f}%)',
                'suggested_goal': new_goal,
                'confidence': 'high'
            })
            recommendations['alerts'].append(f"⚠️ Current goal may be too ambitious - only achieved {achievement_rate:.1f}% of the time")

        # Goal is too low if achievement rate is very high
        elif achievement_rate > 80:
            new_goal = avg_daily * 1.2  # 20% above average
            recommendations['recommended_adjustments'].append({
                'type': 'increase',
                'reason': f'High achievement rate ({achievement_rate:.1f}%)',
                'suggested_goal': new_goal,
                'confidence': 'medium'
            })
            recommendations['alerts'].append(f"🎯 You're consistently exceeding your goal - consider raising it to {new_goal:.0f}")

        # Positive trend suggests goal can be increased
        if trend > 15:
            trend_adjusted_goal = current_goal * (1 + trend / 100)
            recommendations['recommended_adjustments'].append({
                'type': 'increase',
                'reason': f'Strong positive trend ({trend:.1f}%)',
                'suggested_goal': trend_adjusted_goal,
                'confidence': 'medium'
            })
            recommendations['alerts'].append(f"📈 Strong upward trend detected - consider increasing goal")

        # Negative trend suggests goal should be decreased
        elif trend < -15:
            trend_adjusted_goal = current_goal * (1 + trend / 100)
            recommendations['recommended_adjustments'].append({
                'type': 'decrease',
                'reason': f'Negative trend ({trend:.1f}%)',
                'suggested_goal': trend_adjusted_goal,
                'confidence': 'medium'
            })
            recommendations['alerts'].append(f"📉 Declining trend detected - consider adjusting goal")

        # High variability suggests goal adjustment
        coefficient_of_variation = (std_dev / avg_daily) if avg_daily > 0 else 0
        if coefficient_of_variation > 0.5:  # High variability
            stable_goal = avg_daily * 0.8  # More conservative goal
            recommendations['recommended_adjustments'].append({
                'type': 'stabilize',
                'reason': f'High income variability (CV: {coefficient_of_variation:.2f})',
                'suggested_goal': stable_goal,
                'confidence': 'low'
            })
            recommendations['alerts'].append(f"⚡ High income variability detected - consider a more stable goal")

        # Generate goal suggestions for different scenarios
        recommendations['goal_suggestions'] = {
            'conservative': avg_daily * 0.9,
            'realistic': avg_daily * 1.1,
            'ambitious': avg_daily * 1.3,
            'stretch': avg_daily * 1.5
        }

        # Calculate confidence score
        confidence_factors = []
        if len(df) >= 14:  # Sufficient data
            confidence_factors.append(0.3)
        if std_dev / avg_daily < 0.3:  # Low variability
            confidence_factors.append(0.3)
        if abs(trend) < 10:  # Stable trend
            confidence_factors.append(0.2)
        if 40 <= achievement_rate <= 70:  # Reasonable achievement rate
            confidence_factors.append(0.2)

        recommendations['confidence_score'] = sum(confidence_factors) * 100

    def _empty_goal_recommendations(self) -> Dict[str, Any]:
        """Return empty goal recommendations structure"""
        return {
            'current_goal': 0,
            'performance_metrics': {
                'average_daily': 0,
                'median_daily': 0,
                'standard_deviation': 0,
                'achievement_rate': 0,
                'trend': 0
            },
            'recommended_adjustments': [],
            'goal_suggestions': {},
            'alerts': ['No sufficient data for recommendations'],
            'confidence_score': 0
        }

    def auto_adjust_goals_based_on_performance(self, apply_changes: bool = False) -> Dict[str, Any]:
        """Automatically suggest or apply goal adjustments based on performance"""
        recommendations = self.get_smart_goal_recommendations()

        if not recommendations['recommended_adjustments']:
            return {
                'status': 'no_changes_needed',
                'message': 'Current goals appear to be well-calibrated',
                'recommendations': recommendations
            }

        # Find the highest confidence recommendation
        best_recommendation = max(
            recommendations['recommended_adjustments'],
            key=lambda x: {'high': 3, 'medium': 2, 'low': 1}.get(x['confidence'], 0)
        )

        if apply_changes and best_recommendation['confidence'] in ['high', 'medium']:
            # Create new goal
            new_goal = GoalSetting(
                name=f"Auto-Adjusted Goal ({date.today().strftime('%Y-%m-%d')})",
                period="Daily",
                amount=best_recommendation['suggested_goal'],
                description=f"Auto-adjusted based on {best_recommendation['reason']}",
                is_active=True
            )

            # Deactivate current goals
            current_goals = self.get_all_goals()
            for _, goal_row in current_goals.iterrows():
                if goal_row['is_active'] and goal_row['period'] == 'Daily':
                    goal = GoalSetting.from_dict(goal_row.to_dict())
                    goal.is_active = False
                    self.update_goal(goal_row['id'], goal)

            # Add new goal
            if self.add_goal(new_goal):
                return {
                    'status': 'adjusted',
                    'message': f"Goal automatically adjusted to ₹{best_recommendation['suggested_goal']:.2f}",
                    'old_goal': recommendations['current_goal'],
                    'new_goal': best_recommendation['suggested_goal'],
                    'reason': best_recommendation['reason'],
                    'recommendations': recommendations
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to apply goal adjustment',
                    'recommendations': recommendations
                }
        else:
            return {
                'status': 'suggestion_only',
                'message': f"Suggested goal adjustment: ₹{best_recommendation['suggested_goal']:.2f}",
                'suggested_goal': best_recommendation['suggested_goal'],
                'reason': best_recommendation['reason'],
                'confidence': best_recommendation['confidence'],
                'recommendations': recommendations
            }
