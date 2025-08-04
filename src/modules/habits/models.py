"""
Habit Tracker Data Models
Handles habit tracking data structure and validation
"""

import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class HabitFrequency(Enum):
    """Habit frequency enumeration"""
    DAILY = "Daily"
    WEEKLY = "Weekly"
    CUSTOM = "Custom"


class HabitCategory(Enum):
    """Habit category enumeration"""
    HEALTH = "Health & Wellness"
    PRODUCTIVITY = "Productivity"
    LEARNING = "Learning & Development"
    PERSONAL_CARE = "Personal Care"
    FITNESS = "Fitness"
    MINDFULNESS = "Mindfulness"
    OTHER = "Other"


@dataclass
class HabitDefinition:
    """Data class for habit definitions"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    category: str = "Other"
    frequency: str = "Daily"
    target_count: int = 1  # How many times per day/week
    is_active: bool = True
    color: str = "#0e639c"  # Color for UI display
    icon: str = "✓"  # Icon/emoji for display
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        data = asdict(self)
        
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HabitDefinition':
        """Create from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['created_at'] = datetime.now()
        
        return cls(**data)


@dataclass
class HabitRecord:
    """Data class for daily habit completion records"""
    id: Optional[int] = None
    date: Union[str, datetime, date] = None
    habit_id: int = 0
    habit_name: str = ""
    completed_count: int = 0
    target_count: int = 1
    is_completed: bool = False
    completion_time: Optional[datetime] = None
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
        
        # Update completion status
        self.update_completion_status()
    
    def update_completion_status(self):
        """Update completion status based on completed vs target count"""
        self.is_completed = self.completed_count >= self.target_count
        
        if self.is_completed and self.completion_time is None:
            self.completion_time = datetime.now()
    
    def increment_completion(self):
        """Increment completion count"""
        if self.completed_count < self.target_count:
            self.completed_count += 1
            self.update_completion_status()
    
    def decrement_completion(self):
        """Decrement completion count"""
        if self.completed_count > 0:
            self.completed_count -= 1
            self.update_completion_status()
    
    def get_completion_percentage(self) -> float:
        """Get completion percentage"""
        if self.target_count == 0:
            return 0.0
        return min(100.0, (self.completed_count / self.target_count) * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        data = asdict(self)
        
        # Convert date objects to strings
        if isinstance(data['date'], date):
            data['date'] = data['date'].strftime('%Y-%m-%d')
        if data['completion_time'] and isinstance(data['completion_time'], datetime):
            data['completion_time'] = data['completion_time'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HabitRecord':
        """Create from dictionary"""
        # Handle datetime strings
        for field in ['completion_time', 'created_at', 'updated_at']:
            if field in data and isinstance(data[field], str) and data[field]:
                try:
                    data[field] = datetime.strptime(data[field], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    if field in ['created_at', 'updated_at']:
                        data[field] = datetime.now()
                    else:
                        data[field] = None
        
        return cls(**data)


class HabitDataModel:
    """Data model for habit tracking management"""

    def __init__(self, data_manager):
        import logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.data_manager = data_manager
        self.module_name = "habits"
        self.habits_filename = "habit_definitions.csv"
        self.records_filename = "habit_records.csv"
        
        # Default columns for habit definitions CSV
        self.habits_columns = [
            'id', 'name', 'description', 'category', 'frequency',
            'target_count', 'is_active', 'color', 'icon', 'created_at'
        ]
        
        # Default columns for habit records CSV
        self.records_columns = [
            'id', 'date', 'habit_id', 'habit_name', 'completed_count',
            'target_count', 'is_completed', 'completion_time', 'notes',
            'created_at', 'updated_at'
        ]
        
        # Initialize default habits if not exists
        self._initialize_default_habits()

        # Repair any invalid record IDs
        self.repair_invalid_record_ids()
    
    def _initialize_default_habits(self):
        """Initialize default habits if they don't exist"""
        if not self.data_manager.file_exists(self.module_name, self.habits_filename):
            default_habits = [
                HabitDefinition(
                    name="Face wash (Morning)",
                    description="Morning face wash routine",
                    category="Personal Care",
                    icon="🧴",
                    color="#4CAF50"
                ),
                HabitDefinition(
                    name="Face wash (Night)",
                    description="Night face wash routine",
                    category="Personal Care",
                    icon="🌙",
                    color="#2196F3"
                ),
                HabitDefinition(
                    name="Serum Application",
                    description="Apply facial serum",
                    category="Personal Care",
                    icon="💧",
                    color="#FF9800"
                ),
                HabitDefinition(
                    name="Sunscreen Application",
                    description="Apply sunscreen protection",
                    category="Personal Care",
                    icon="☀️",
                    color="#FFC107"
                ),
                HabitDefinition(
                    name="Study Session",
                    description="Dedicated study time",
                    category="Learning & Development",
                    icon="📚",
                    color="#9C27B0"
                ),
                HabitDefinition(
                    name="Project Work",
                    description="Work on personal projects",
                    category="Productivity",
                    icon="💻",
                    color="#607D8B"
                ),
                HabitDefinition(
                    name="Aptitude Practice",
                    description="Practice aptitude questions",
                    category="Learning & Development",
                    icon="🧮",
                    color="#795548"
                ),
                HabitDefinition(
                    name="Handwriting Practice",
                    description="Improve handwriting skills",
                    category="Learning & Development",
                    icon="✍️",
                    color="#E91E63"
                ),
                HabitDefinition(
                    name="Record Updates",
                    description="Update personal records and logs",
                    category="Productivity",
                    icon="📝",
                    color="#3F51B5"
                ),
                HabitDefinition(
                    name="Exercise",
                    description="Physical exercise or workout",
                    category="Fitness",
                    icon="💪",
                    color="#F44336"
                ),
                HabitDefinition(
                    name="Reading",
                    description="Read books or articles",
                    category="Learning & Development",
                    icon="📖",
                    color="#009688"
                ),
                HabitDefinition(
                    name="Meditation",
                    description="Mindfulness and meditation practice",
                    category="Mindfulness",
                    icon="🧘",
                    color="#8BC34A"
                )
            ]
            
            habits_data = [habit.to_dict() for habit in default_habits]
            df = pd.DataFrame(habits_data)
            self.data_manager.write_csv(self.module_name, self.habits_filename, df)
    
    def get_all_habits(self) -> pd.DataFrame:
        """Get all habit definitions"""
        return self.data_manager.read_csv(
            self.module_name,
            self.habits_filename,
            self.habits_columns
        )
    
    def get_active_habits(self) -> pd.DataFrame:
        """Get only active habit definitions"""
        df = self.get_all_habits()
        if df.empty:
            return df
        
        return df[df['is_active'] == True]
    
    def add_habit(self, habit: HabitDefinition) -> bool:
        """Add a new habit definition"""
        return self.data_manager.append_row(
            self.module_name,
            self.habits_filename,
            habit.to_dict(),
            self.habits_columns
        )
    
    def update_habit(self, habit_id: int, habit: HabitDefinition) -> bool:
        """Update an existing habit definition"""
        return self.data_manager.update_row(
            self.module_name,
            self.habits_filename,
            habit_id,
            habit.to_dict()
        )

    def delete_habit(self, habit_id: int) -> bool:
        """Delete a habit definition and all its records"""
        # First delete all records for this habit
        records_df = self.get_all_records()
        if not records_df.empty:
            habit_records = records_df[records_df['habit_id'] == habit_id]
            for _, record in habit_records.iterrows():
                self.data_manager.delete_row(
                    self.module_name,
                    self.records_filename,
                    record['id']
                )

        # Then delete the habit definition
        return self.data_manager.delete_row(
            self.module_name,
            self.habits_filename,
            habit_id
        )
    
    def get_all_records(self) -> pd.DataFrame:
        """Get all habit records"""
        return self.data_manager.read_csv(
            self.module_name,
            self.records_filename,
            self.records_columns
        )
    
    def get_records_by_date(self, target_date: date) -> pd.DataFrame:
        """Get habit records for a specific date"""
        df = self.get_all_records()
        if df.empty:
            return df
        
        # Convert date column to datetime for comparison
        df['date'] = pd.to_datetime(df['date'])
        target_timestamp = pd.Timestamp(target_date)
        
        return df[df['date'] == target_timestamp]
    
    def get_or_create_daily_records(self, target_date: date = None) -> List[HabitRecord]:
        """Get or create habit records for a specific date with enhanced error handling"""
        if target_date is None:
            target_date = date.today()

        try:
            # Get existing records for the date
            existing_records = self.get_records_by_date(target_date)

            # Get active habits
            active_habits = self.get_active_habits()

            records = []

            if active_habits.empty:
                self.logger.info(f"No active habits found for date {target_date}")
                return records

            for _, habit in active_habits.iterrows():
                try:
                    # Skip habits with invalid IDs
                    if pd.isna(habit['id']) or habit['id'] == '' or habit['id'] is None:
                        self.logger.warning(f"Skipping habit with invalid ID: {habit.get('name', 'Unknown')}")
                        continue

                    # Validate and convert habit_id
                    try:
                        habit_id = int(float(habit['id']))  # Handle float conversion first
                    except (ValueError, TypeError, OverflowError):
                        self.logger.warning(f"Skipping habit with non-numeric ID: {habit['id']} for habit {habit.get('name', 'Unknown')}")
                        continue

                    # Validate habit name
                    habit_name = str(habit.get('name', 'Unknown Habit')).strip()
                    if not habit_name or habit_name == 'nan':
                        habit_name = f"Habit {habit_id}"

                    # Validate target count
                    try:
                        target_count = int(float(habit.get('target_count', 1)))
                        if target_count <= 0:
                            target_count = 1
                    except (ValueError, TypeError, OverflowError):
                        target_count = 1

                    # Check if record exists for this habit on this date
                    habit_record = existing_records[existing_records['habit_id'] == habit_id] if not existing_records.empty else pd.DataFrame()

                    if not habit_record.empty:
                        # Use existing record with validation
                        try:
                            record_data = habit_record.iloc[0].to_dict()
                            # Clean up any NaN values
                            for key, value in record_data.items():
                                if pd.isna(value):
                                    if key in ['completed_count', 'target_count']:
                                        record_data[key] = 0 if key == 'completed_count' else 1
                                    elif key in ['habit_name']:
                                        record_data[key] = habit_name
                                    elif key in ['notes']:
                                        record_data[key] = ""
                                    elif key in ['is_completed']:
                                        record_data[key] = False

                            records.append(HabitRecord.from_dict(record_data))
                        except Exception as e:
                            self.logger.error(f"Error processing existing record for habit {habit_name}: {e}")
                            # Create a new record as fallback
                            new_record = HabitRecord(
                                date=target_date,
                                habit_id=habit_id,
                                habit_name=habit_name,
                                target_count=target_count
                            )
                            records.append(new_record)
                    else:
                        # Create new record
                        new_record = HabitRecord(
                            date=target_date,
                            habit_id=habit_id,
                            habit_name=habit_name,
                            target_count=target_count
                        )
                        records.append(new_record)

                except Exception as habit_error:
                    self.logger.error(f"Error processing habit {habit.get('name', 'Unknown')}: {habit_error}")
                    continue

            self.logger.debug(f"Successfully created {len(records)} habit records for date {target_date}")
            return records

        except Exception as e:
            self.logger.error(f"Critical error in get_or_create_daily_records for date {target_date}: {e}")
            # Return empty list to prevent crashes
            return []

    def save_habit_record(self, record: HabitRecord) -> bool:
        """Save or update a habit record with comprehensive error handling"""
        try:
            # Validate the record before saving
            if not record:
                self.logger.error("Cannot save None habit record")
                return False

            if not hasattr(record, 'habit_id') or record.habit_id is None:
                self.logger.error("Cannot save habit record without habit_id")
                return False

            if not hasattr(record, 'date') or record.date is None:
                self.logger.error("Cannot save habit record without date")
                return False

            # Check if record already exists
            try:
                existing_records = self.get_records_by_date(record.date)
            except Exception as e:
                self.logger.error(f"Error checking existing records for date {record.date}: {e}")
                return False

            if not existing_records.empty:
                existing_record = existing_records[existing_records['habit_id'] == record.habit_id]

                if not existing_record.empty:
                    # Update existing record
                    try:
                        record_id = existing_record.iloc[0]['id']

                        # Check for invalid ID (NaN, None, empty string)
                        if pd.isna(record_id) or record_id is None or record_id == '':
                            self.logger.warning(f"Found habit record with invalid ID for habit {record.habit_id}, will create new record instead")
                            # Fall through to create new record
                        else:
                            record_dict = record.to_dict()

                            success = self.data_manager.update_row(
                                self.module_name,
                                self.records_filename,
                                record_id,
                                record_dict
                            )

                            if success:
                                self.logger.debug(f"Successfully updated habit record {record_id} for habit {record.habit_id}")
                                return success
                            else:
                                self.logger.error(f"Failed to update habit record {record_id} for habit {record.habit_id}")
                                return False

                    except Exception as e:
                        self.logger.error(f"Error updating existing habit record: {e}")
                        # Fall through to create new record
                        pass

            # Add new record
            try:
                record_dict = record.to_dict()
                success = self.data_manager.append_row(
                    self.module_name,
                    self.records_filename,
                    record_dict,
                    self.records_columns
                )

                if success:
                    self.logger.debug(f"Successfully added new habit record for habit {record.habit_id}")
                else:
                    self.logger.error(f"Failed to add new habit record for habit {record.habit_id}")

                return success

            except Exception as e:
                self.logger.error(f"Error adding new habit record: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Critical error in save_habit_record: {e}")
            return False

    def repair_invalid_record_ids(self) -> bool:
        """Repair habit records with invalid or missing IDs"""
        try:
            df = self.get_all_records()
            if df.empty:
                return True

            # Find records with invalid IDs
            invalid_mask = df['id'].isna() | (df['id'] == '') | (df['id'].astype(str) == 'nan')
            invalid_records = df[invalid_mask]

            if invalid_records.empty:
                self.logger.debug("No invalid record IDs found")
                return True

            self.logger.info(f"Found {len(invalid_records)} records with invalid IDs, repairing...")

            # Generate new IDs for invalid records
            max_id = df['id'].dropna().max() if not df['id'].dropna().empty else 0
            next_id = int(max_id) + 1 if not pd.isna(max_id) else 1

            for idx in invalid_records.index:
                df.loc[idx, 'id'] = next_id
                next_id += 1

            # Write the repaired data back
            success = self.data_manager.write_csv(self.module_name, self.records_filename, df)

            if success:
                self.logger.info(f"Successfully repaired {len(invalid_records)} invalid record IDs")
            else:
                self.logger.error("Failed to write repaired records back to file")

            return success

        except Exception as e:
            self.logger.error(f"Error repairing invalid record IDs: {e}")
            return False

    def get_habit_streak(self, habit_id: int) -> int:
        """Calculate current streak for a specific habit"""
        df = self.get_all_records()
        if df.empty:
            return 0

        # Filter records for this habit
        habit_records = df[df['habit_id'] == habit_id]
        if habit_records.empty:
            return 0

        # Sort by date descending
        habit_records = habit_records.sort_values('date', ascending=False)
        habit_records['date'] = pd.to_datetime(habit_records['date'])

        streak = 0
        current_date = date.today()

        for _, record in habit_records.iterrows():
            record_date = record['date'].date()

            # Check if this is the expected date in the streak
            if record_date == current_date and record['is_completed']:
                streak += 1
                current_date -= timedelta(days=1)
            elif record_date == current_date:
                # Found the date but not completed, streak breaks
                break
            elif record_date < current_date:
                # Gap in records, streak breaks
                break

        return streak

    def get_habit_completion_rate(self, habit_id: int, days: int = 30) -> float:
        """Get completion rate for a habit over the last N days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)

        df = self.get_all_records()
        if df.empty:
            return 0.0

        # Filter records for this habit and date range
        df['date'] = pd.to_datetime(df['date'])
        habit_records = df[
            (df['habit_id'] == habit_id) &
            (df['date'] >= pd.Timestamp(start_date)) &
            (df['date'] <= pd.Timestamp(end_date))
        ]

        if habit_records.empty:
            return 0.0

        completed_days = len(habit_records[habit_records['is_completed'] == True])
        total_days = len(habit_records)

        return (completed_days / total_days) * 100 if total_days > 0 else 0.0

    def get_weekly_summary(self, start_date: date = None) -> Dict[str, Any]:
        """Get weekly habit completion summary"""
        if start_date is None:
            # Start from Monday of current week
            today = date.today()
            start_date = today - timedelta(days=today.weekday())

        end_date = start_date + timedelta(days=6)

        # Get all records for the week
        df = self.get_all_records()
        if df.empty:
            return self._empty_weekly_summary(start_date, end_date)

        df['date'] = pd.to_datetime(df['date'])
        week_records = df[
            (df['date'] >= pd.Timestamp(start_date)) &
            (df['date'] <= pd.Timestamp(end_date))
        ]

        # Get active habits
        active_habits = self.get_active_habits()

        weekly_data = {
            'start_date': start_date,
            'end_date': end_date,
            'total_habits': len(active_habits),
            'total_possible_completions': len(active_habits) * 7,
            'total_completions': 0,
            'completion_rate': 0.0,
            'daily_breakdown': [],
            'habit_breakdown': []
        }

        # Calculate daily breakdown
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            day_records = week_records[week_records['date'] == pd.Timestamp(current_date)] if not week_records.empty else pd.DataFrame()

            completed_today = len(day_records[day_records['is_completed'] == True]) if not day_records.empty else 0
            total_today = len(active_habits)

            day_info = {
                'date': current_date,
                'day_name': current_date.strftime('%A'),
                'completed': completed_today,
                'total': total_today,
                'completion_rate': (completed_today / total_today * 100) if total_today > 0 else 0
            }

            weekly_data['daily_breakdown'].append(day_info)
            weekly_data['total_completions'] += completed_today

        # Calculate habit breakdown
        for _, habit in active_habits.iterrows():
            habit_week_records = week_records[week_records['habit_id'] == habit['id']] if not week_records.empty else pd.DataFrame()
            completed_days = len(habit_week_records[habit_week_records['is_completed'] == True]) if not habit_week_records.empty else 0

            habit_info = {
                'habit_id': habit['id'],
                'habit_name': habit['name'],
                'completed_days': completed_days,
                'total_days': 7,
                'completion_rate': (completed_days / 7) * 100,
                'streak': self.get_habit_streak(habit['id'])
            }

            weekly_data['habit_breakdown'].append(habit_info)

        # Calculate overall completion rate
        weekly_data['completion_rate'] = (weekly_data['total_completions'] / weekly_data['total_possible_completions'] * 100) if weekly_data['total_possible_completions'] > 0 else 0

        return weekly_data

    def _empty_weekly_summary(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Return empty weekly summary structure"""
        active_habits = self.get_active_habits()

        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_habits': len(active_habits),
            'total_possible_completions': len(active_habits) * 7,
            'total_completions': 0,
            'completion_rate': 0.0,
            'daily_breakdown': [
                {
                    'date': start_date + timedelta(days=i),
                    'day_name': (start_date + timedelta(days=i)).strftime('%A'),
                    'completed': 0,
                    'total': len(active_habits),
                    'completion_rate': 0.0
                }
                for i in range(7)
            ],
            'habit_breakdown': [
                {
                    'habit_id': habit['id'],
                    'habit_name': habit['name'],
                    'completed_days': 0,
                    'total_days': 7,
                    'completion_rate': 0.0,
                    'streak': 0
                }
                for _, habit in active_habits.iterrows()
            ]
        }

    def get_habit_summary(self) -> Dict[str, Any]:
        """Get overall habit tracking summary"""
        active_habits = self.get_active_habits()
        all_records = self.get_all_records()

        if active_habits.empty:
            return {
                'total_habits': 0,
                'total_records': 0,
                'overall_completion_rate': 0.0,
                'best_streak': 0,
                'habits_completed_today': 0,
                'habits_total_today': 0,
                'today_completion_rate': 0.0
            }

        total_habits = len(active_habits)
        total_records = len(all_records) if not all_records.empty else 0

        # Calculate overall completion rate
        if not all_records.empty:
            completed_records = len(all_records[all_records['is_completed'] == True])
            overall_completion_rate = (completed_records / total_records) * 100
        else:
            overall_completion_rate = 0.0

        # Find best streak across all habits
        best_streak = 0
        for _, habit in active_habits.iterrows():
            habit_streak = self.get_habit_streak(habit['id'])
            best_streak = max(best_streak, habit_streak)

        # Today's completion
        today_records = self.get_records_by_date(date.today())
        habits_completed_today = len(today_records[today_records['is_completed'] == True]) if not today_records.empty else 0
        habits_total_today = total_habits
        today_completion_rate = (habits_completed_today / habits_total_today * 100) if habits_total_today > 0 else 0

        return {
            'total_habits': total_habits,
            'total_records': total_records,
            'overall_completion_rate': overall_completion_rate,
            'best_streak': best_streak,
            'habits_completed_today': habits_completed_today,
            'habits_total_today': habits_total_today,
            'today_completion_rate': today_completion_rate
        }
