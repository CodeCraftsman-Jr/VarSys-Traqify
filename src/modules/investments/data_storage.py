"""
Investment Data Storage System
Manages local CSV-based storage for investment data with organized file structure
"""

import os
import csv
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import shutil
from decimal import Decimal, InvalidOperation


class InvestmentDataStorage:
    """Manages local CSV storage for investment data"""

    def __init__(self, base_data_dir: str = "data/investments"):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_dir = Path(base_data_dir)
        self.ensure_directory_structure()
        
        # Data categories and their corresponding file structures
        self.data_categories = {
            'real_time': {
                'filename': 'real_time_data.csv',
                'columns': ['symbol', 'current_price', 'nav', 'previous_close', 'open',
                          'day_high', 'day_low', 'volume', 'market_cap', 'currency',
                          'data_source', 'source_timestamp', 'timestamp']
            },
            'historical': {
                'filename': 'historical_data.csv',
                'columns': ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 
                          'change', 'change_percent', 'period', 'timestamp']
            },
            'performance': {
                'filename': 'performance_data.csv',
                'columns': ['symbol', 'beta', 'trailing_pe', 'forward_pe', 'price_to_book',
                          'return_on_equity', 'return_on_assets', 'profit_margins',
                          'operating_margins', 'earnings_growth', 'revenue_growth',
                          'week_52_high', 'week_52_low', 'moving_avg_50', 'moving_avg_200',
                          'data_source', 'source_timestamp', 'timestamp']
            },
            'financial': {
                'filename': 'financial_data.csv',
                'columns': ['symbol', 'total_revenue', 'gross_profits', 'ebitda', 'net_income',
                          'total_cash', 'total_debt', 'book_value', 'shares_outstanding',
                          'enterprise_value', 'price_to_sales', 'enterprise_to_revenue',
                          'enterprise_to_ebitda', 'debt_to_equity', 'current_ratio', 
                          'quick_ratio', 'timestamp']
            },
            'portfolio': {
                'filename': 'portfolio_data.csv',
                'columns': ['symbol', 'sector', 'industry', 'full_time_employees', 'website',
                          'city', 'state', 'country', 'business_summary', 'timestamp']
            },
            'regulatory': {
                'filename': 'regulatory_data.csv',
                'columns': ['symbol', 'sec_filings', 'annual_reports', 'quarterly_reports',
                          'notes', 'timestamp']
            },
            'dividend': {
                'filename': 'dividend_data.csv',
                'columns': ['symbol', 'dividend_date', 'dividend_amount', 'dividend_yield',
                          'dividend_rate', 'payout_ratio', 'ex_dividend_date', 'timestamp']
            },
            'fees': {
                'filename': 'fees_data.csv',
                'columns': ['symbol', 'expense_ratio', 'management_fee', 'front_end_load',
                          'back_end_load', 'annual_holdings_turnover', 'fund_family',
                          'category', 'timestamp']
            }
        }

    def ensure_directory_structure(self):
        """Create necessary directory structure"""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for different data types
            subdirs = ['cache', 'historical_archive', 'metadata']
            for subdir in subdirs:
                (self.base_dir / subdir).mkdir(exist_ok=True)
                
            self.logger.info(f"✅ Investment data directory structure created: {self.base_dir}")
        except Exception as e:
            self.logger.error(f"❌ Failed to create directory structure: {e}")
            raise

    def get_file_path(self, category: str) -> Path:
        """Get file path for a data category"""
        if category not in self.data_categories:
            raise ValueError(f"Unknown data category: {category}")
        return self.base_dir / self.data_categories[category]['filename']

    def get_columns(self, category: str) -> List[str]:
        """Get column names for a data category"""
        if category not in self.data_categories:
            raise ValueError(f"Unknown data category: {category}")
        return self.data_categories[category]['columns']

    def initialize_csv_file(self, category: str) -> bool:
        """Initialize CSV file with headers if it doesn't exist"""
        try:
            file_path = self.get_file_path(category)
            if not file_path.exists():
                columns = self.get_columns(category)
                df = pd.DataFrame(columns=columns)
                df.to_csv(file_path, index=False)
                self.logger.info(f"✅ Initialized CSV file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize CSV file for {category}: {e}")
            return False

    def store_real_time_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Store real-time data for a symbol with validation and backup"""
        try:
            # Validate symbol
            if not self.validate_symbol(symbol):
                self.logger.error(f"❌ Invalid symbol format: {symbol}")
                return False

            # Validate data
            is_valid, errors = self.validate_numeric_data(data)
            if not is_valid:
                self.logger.error(f"❌ Data validation failed for {symbol}: {errors}")
                return False

            self.initialize_csv_file('real_time')
            file_path = self.get_file_path('real_time')

            # Create backup
            self.backup_file('real_time')

            # Read existing data
            df = pd.read_csv(file_path)

            # Remove existing data for this symbol
            df = df[df['symbol'] != symbol]

            # Add new data
            new_row = {
                'symbol': symbol,
                'current_price': data.get('current_price'),
                'nav': data.get('nav'),
                'previous_close': data.get('previous_close'),
                'open': data.get('open'),
                'day_high': data.get('day_high'),
                'day_low': data.get('day_low'),
                'volume': data.get('volume'),
                'market_cap': data.get('market_cap'),
                'currency': data.get('currency', 'INR'),
                'data_source': data.get('data_source', 'Unknown'),
                'source_timestamp': data.get('source_timestamp', datetime.now().isoformat()),
                'timestamp': datetime.now().isoformat()
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(file_path, index=False)

            # Verify integrity after write
            is_valid, issues = self.verify_data_integrity('real_time')
            if not is_valid:
                self.logger.warning(f"⚠️ Data integrity issues after storing {symbol}: {issues}")

            self.logger.debug(f"✅ Stored real-time data for {symbol}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to store real-time data for {symbol}: {e}")
            return False

    def load_real_time_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load real-time data for a symbol"""
        try:
            file_path = self.get_file_path('real_time')
            if not file_path.exists():
                return None
                
            df = pd.read_csv(file_path)
            symbol_data = df[df['symbol'] == symbol]
            
            if symbol_data.empty:
                return None
                
            # Get the most recent record
            latest = symbol_data.iloc[-1]
            
            return {
                'available': True,
                'current_price': latest.get('current_price'),
                'nav': latest.get('nav'),
                'previous_close': latest.get('previous_close'),
                'open': latest.get('open'),
                'day_high': latest.get('day_high'),
                'day_low': latest.get('day_low'),
                'volume': latest.get('volume'),
                'market_cap': latest.get('market_cap'),
                'currency': latest.get('currency', 'INR'),
                'data_source': latest.get('data_source', 'Unknown'),
                'source_timestamp': latest.get('source_timestamp'),
                'last_updated': latest.get('timestamp')
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load real-time data for {symbol}: {e}")
            return None

    def store_historical_data(self, symbol: str, data: List[Dict[str, Any]], period: str = "1y") -> bool:
        """Store historical data for a symbol"""
        try:
            self.initialize_csv_file('historical')
            file_path = self.get_file_path('historical')
            
            # Read existing data
            df = pd.read_csv(file_path)
            
            # Remove existing data for this symbol and period
            df = df[~((df['symbol'] == symbol) & (df['period'] == period))]
            
            # Add new data
            new_rows = []
            timestamp = datetime.now().isoformat()
            
            for record in data:
                new_row = {
                    'symbol': symbol,
                    'date': record.get('date'),
                    'open': record.get('open'),
                    'high': record.get('high'),
                    'low': record.get('low'),
                    'close': record.get('close'),
                    'volume': record.get('volume'),
                    'change': record.get('change'),
                    'change_percent': record.get('change_percent'),
                    'period': period,
                    'timestamp': timestamp
                }
                new_rows.append(new_row)
            
            if new_rows:
                new_df = pd.DataFrame(new_rows)
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_csv(file_path, index=False)
                
                self.logger.debug(f"✅ Stored {len(new_rows)} historical records for {symbol} ({period})")
                return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store historical data for {symbol}: {e}")
            return False

    def load_historical_data(self, symbol: str, period: str = "1y") -> Optional[Dict[str, Any]]:
        """Load historical data for a symbol"""
        try:
            file_path = self.get_file_path('historical')
            if not file_path.exists():
                return None
                
            df = pd.read_csv(file_path)
            symbol_data = df[(df['symbol'] == symbol) & (df['period'] == period)]
            
            if symbol_data.empty:
                return None
            
            # Convert to list of dictionaries
            historical_data = []
            for _, row in symbol_data.iterrows():
                historical_data.append({
                    'date': row.get('date'),
                    'open': row.get('open'),
                    'high': row.get('high'),
                    'low': row.get('low'),
                    'close': row.get('close'),
                    'volume': row.get('volume'),
                    'change': row.get('change'),
                    'change_percent': row.get('change_percent')
                })
            
            return {
                'available': True,
                'data': historical_data,
                'period': period,
                'total_records': len(historical_data),
                'last_updated': symbol_data.iloc[-1].get('timestamp') if not symbol_data.empty else None
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load historical data for {symbol}: {e}")
            return None

    def get_data_freshness(self, symbol: str, category: str) -> Optional[datetime]:
        """Get the timestamp when data was last updated for a symbol and category"""
        try:
            file_path = self.get_file_path(category)
            if not file_path.exists():
                return None
                
            df = pd.read_csv(file_path)
            symbol_data = df[df['symbol'] == symbol]
            
            if symbol_data.empty:
                return None
                
            latest_timestamp = symbol_data['timestamp'].iloc[-1]
            return datetime.fromisoformat(latest_timestamp)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get data freshness for {symbol} ({category}): {e}")
            return None

    def is_data_stale(self, symbol: str, category: str, max_age_hours: int = 24) -> bool:
        """Check if data is stale (older than max_age_hours)"""
        freshness = self.get_data_freshness(symbol, category)
        if not freshness:
            return True  # No data means stale

        age = datetime.now() - freshness
        return age > timedelta(hours=max_age_hours)

    def validate_symbol(self, symbol: str) -> bool:
        """Validate symbol format"""
        if not symbol or not isinstance(symbol, str):
            return False

        # Remove common suffixes and check length
        clean_symbol = symbol.replace('.NS', '').replace('.BO', '').strip()
        return len(clean_symbol) >= 2 and len(clean_symbol) <= 20 and clean_symbol.isalnum()

    def validate_numeric_data(self, data: Dict[str, Any], required_fields: List[str] = None) -> Tuple[bool, List[str]]:
        """Validate numeric data fields"""
        errors = []

        # Define non-numeric fields that should be excluded from numeric validation
        non_numeric_fields = [
            'symbol', 'timestamp', 'currency', 'date', 'scheme_name', 'amc_name',
            'data_source', 'source_timestamp', 'symbol_used', 'last_updated',
            'isin_div_payout', 'isin_div_reinvest', 'nav_date', 'scheme_code',
            'company_name', 'sector', 'industry', 'exchange', 'country'
        ]

        for key, value in data.items():
            if value is not None and key not in non_numeric_fields:
                try:
                    if isinstance(value, str) and value.strip() == '':
                        continue  # Empty strings are OK, will be treated as None

                    # Try to convert to float
                    float_val = float(value)

                    # Check for reasonable ranges
                    if key in ['current_price', 'nav', 'open', 'high', 'low', 'close'] and float_val < 0:
                        errors.append(f"{key} cannot be negative: {value}")
                    elif key in ['volume'] and float_val < 0:
                        errors.append(f"{key} cannot be negative: {value}")
                    elif abs(float_val) > 1e15:  # Unreasonably large number
                        errors.append(f"{key} value too large: {value}")

                except (ValueError, TypeError, InvalidOperation):
                    errors.append(f"Invalid numeric value for {key}: {value}")

        # Check required fields
        if required_fields:
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Required field missing: {field}")

        return len(errors) == 0, errors

    def backup_file(self, category: str) -> bool:
        """Create backup of data file before modification"""
        try:
            file_path = self.get_file_path(category)
            if file_path.exists():
                backup_dir = self.base_dir / 'backups'
                backup_dir.mkdir(exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = backup_dir / f"{category}_backup_{timestamp}.csv"

                shutil.copy2(file_path, backup_path)

                # Keep only last 10 backups
                backups = sorted(backup_dir.glob(f"{category}_backup_*.csv"))
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()

                self.logger.debug(f"✅ Created backup: {backup_path}")
                return True
        except Exception as e:
            self.logger.error(f"❌ Failed to create backup for {category}: {e}")
            return False

    def verify_data_integrity(self, category: str) -> Tuple[bool, List[str]]:
        """Verify data integrity for a category"""
        issues = []

        try:
            file_path = self.get_file_path(category)
            if not file_path.exists():
                return True, []  # No file means no issues

            df = pd.read_csv(file_path)
            expected_columns = self.get_columns(category)

            # Check column structure
            if list(df.columns) != expected_columns:
                issues.append(f"Column mismatch. Expected: {expected_columns}, Found: {list(df.columns)}")

            # Check for duplicate symbols with same timestamp
            if 'symbol' in df.columns and 'timestamp' in df.columns:
                duplicates = df.groupby(['symbol', 'timestamp']).size()
                duplicate_count = (duplicates > 1).sum()
                if duplicate_count > 0:
                    issues.append(f"Found {duplicate_count} duplicate symbol-timestamp combinations")

            # Check for invalid timestamps
            if 'timestamp' in df.columns:
                invalid_timestamps = 0
                for timestamp in df['timestamp'].dropna():
                    try:
                        datetime.fromisoformat(str(timestamp))
                    except (ValueError, TypeError):
                        invalid_timestamps += 1

                if invalid_timestamps > 0:
                    issues.append(f"Found {invalid_timestamps} invalid timestamps")

            # Check for completely empty rows
            empty_rows = df.isnull().all(axis=1).sum()
            if empty_rows > 0:
                issues.append(f"Found {empty_rows} completely empty rows")

            return len(issues) == 0, issues

        except Exception as e:
            issues.append(f"Error reading file: {e}")
            return False, issues

    def store_performance_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Store performance data for a symbol"""
        try:
            self.initialize_csv_file('performance')
            file_path = self.get_file_path('performance')

            df = pd.read_csv(file_path)
            df = df[df['symbol'] != symbol]  # Remove existing data

            new_row = {
                'symbol': symbol,
                'beta': data.get('beta'),
                'trailing_pe': data.get('trailing_pe'),
                'forward_pe': data.get('forward_pe'),
                'price_to_book': data.get('price_to_book'),
                'return_on_equity': data.get('return_on_equity'),
                'return_on_assets': data.get('return_on_assets'),
                'profit_margins': data.get('profit_margins'),
                'operating_margins': data.get('operating_margins'),
                'earnings_growth': data.get('earnings_growth'),
                'revenue_growth': data.get('revenue_growth'),
                'week_52_high': data.get('52_week_high'),
                'week_52_low': data.get('52_week_low'),
                'moving_avg_50': data.get('moving_avg_50'),
                'moving_avg_200': data.get('moving_avg_200'),
                'data_source': data.get('data_source', 'Unknown'),
                'source_timestamp': data.get('source_timestamp', datetime.now().isoformat()),
                'timestamp': datetime.now().isoformat()
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(file_path, index=False)

            self.logger.debug(f"✅ Stored performance data for {symbol}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to store performance data for {symbol}: {e}")
            return False

    def load_performance_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load performance data for a symbol"""
        try:
            file_path = self.get_file_path('performance')
            if not file_path.exists():
                return None

            df = pd.read_csv(file_path)
            symbol_data = df[df['symbol'] == symbol]

            if symbol_data.empty:
                return None

            latest = symbol_data.iloc[-1]

            return {
                'available': True,
                'beta': latest.get('beta'),
                'trailing_pe': latest.get('trailing_pe'),
                'forward_pe': latest.get('forward_pe'),
                'price_to_book': latest.get('price_to_book'),
                'return_on_equity': latest.get('return_on_equity'),
                'return_on_assets': latest.get('return_on_assets'),
                'profit_margins': latest.get('profit_margins'),
                'operating_margins': latest.get('operating_margins'),
                'earnings_growth': latest.get('earnings_growth'),
                'revenue_growth': latest.get('revenue_growth'),
                '52_week_high': latest.get('week_52_high'),
                '52_week_low': latest.get('week_52_low'),
                'moving_avg_50': latest.get('moving_avg_50'),
                'moving_avg_200': latest.get('moving_avg_200'),
                'last_updated': latest.get('timestamp')
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to load performance data for {symbol}: {e}")
            return None

    def store_financial_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Store financial data for a symbol"""
        try:
            self.initialize_csv_file('financial')
            file_path = self.get_file_path('financial')

            df = pd.read_csv(file_path)
            df = df[df['symbol'] != symbol]  # Remove existing data

            new_row = {
                'symbol': symbol,
                'total_revenue': data.get('total_revenue'),
                'gross_profits': data.get('gross_profits'),
                'ebitda': data.get('ebitda'),
                'net_income': data.get('net_income'),
                'total_cash': data.get('total_cash'),
                'total_debt': data.get('total_debt'),
                'book_value': data.get('book_value'),
                'shares_outstanding': data.get('shares_outstanding'),
                'enterprise_value': data.get('enterprise_value'),
                'price_to_sales': data.get('price_to_sales'),
                'enterprise_to_revenue': data.get('enterprise_to_revenue'),
                'enterprise_to_ebitda': data.get('enterprise_to_ebitda'),
                'debt_to_equity': data.get('debt_to_equity'),
                'current_ratio': data.get('current_ratio'),
                'quick_ratio': data.get('quick_ratio'),
                'timestamp': datetime.now().isoformat()
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(file_path, index=False)

            self.logger.debug(f"✅ Stored financial data for {symbol}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to store financial data for {symbol}: {e}")
            return False

    def load_financial_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load financial data for a symbol"""
        try:
            file_path = self.get_file_path('financial')
            if not file_path.exists():
                return None

            df = pd.read_csv(file_path)
            symbol_data = df[df['symbol'] == symbol]

            if symbol_data.empty:
                return None

            latest = symbol_data.iloc[-1]

            return {
                'available': True,
                'total_revenue': latest.get('total_revenue'),
                'gross_profits': latest.get('gross_profits'),
                'ebitda': latest.get('ebitda'),
                'net_income': latest.get('net_income'),
                'total_cash': latest.get('total_cash'),
                'total_debt': latest.get('total_debt'),
                'book_value': latest.get('book_value'),
                'shares_outstanding': latest.get('shares_outstanding'),
                'enterprise_value': latest.get('enterprise_value'),
                'price_to_sales': latest.get('price_to_sales'),
                'enterprise_to_revenue': latest.get('enterprise_to_revenue'),
                'enterprise_to_ebitda': latest.get('enterprise_to_ebitda'),
                'debt_to_equity': latest.get('debt_to_equity'),
                'current_ratio': latest.get('current_ratio'),
                'quick_ratio': latest.get('quick_ratio'),
                'last_updated': latest.get('timestamp')
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to load financial data for {symbol}: {e}")
            return None

    def store_portfolio_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Store portfolio data for a symbol"""
        try:
            self.initialize_csv_file('portfolio')
            file_path = self.get_file_path('portfolio')

            df = pd.read_csv(file_path)
            df = df[df['symbol'] != symbol]  # Remove existing data

            headquarters = data.get('headquarters', {})
            new_row = {
                'symbol': symbol,
                'sector': data.get('sector'),
                'industry': data.get('industry'),
                'full_time_employees': data.get('full_time_employees'),
                'website': data.get('website'),
                'city': headquarters.get('city'),
                'state': headquarters.get('state'),
                'country': headquarters.get('country'),
                'business_summary': data.get('business_summary'),
                'timestamp': datetime.now().isoformat()
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(file_path, index=False)

            self.logger.debug(f"✅ Stored portfolio data for {symbol}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to store portfolio data for {symbol}: {e}")
            return False

    def load_portfolio_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load portfolio data for a symbol"""
        try:
            file_path = self.get_file_path('portfolio')
            if not file_path.exists():
                return None

            df = pd.read_csv(file_path)
            symbol_data = df[df['symbol'] == symbol]

            if symbol_data.empty:
                return None

            latest = symbol_data.iloc[-1]

            return {
                'available': True,
                'sector': latest.get('sector'),
                'industry': latest.get('industry'),
                'full_time_employees': latest.get('full_time_employees'),
                'website': latest.get('website'),
                'headquarters': {
                    'city': latest.get('city'),
                    'state': latest.get('state'),
                    'country': latest.get('country')
                },
                'business_summary': latest.get('business_summary'),
                'last_updated': latest.get('timestamp')
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to load portfolio data for {symbol}: {e}")
            return None

    def store_dividend_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Store dividend data for a symbol"""
        try:
            self.initialize_csv_file('dividend')
            file_path = self.get_file_path('dividend')

            df = pd.read_csv(file_path)
            df = df[df['symbol'] != symbol]  # Remove existing data

            # Store dividend history
            dividends = data.get('dividends', [])
            new_rows = []
            timestamp = datetime.now().isoformat()

            for dividend in dividends:
                new_row = {
                    'symbol': symbol,
                    'dividend_date': dividend.get('date'),
                    'dividend_amount': dividend.get('amount'),
                    'dividend_yield': data.get('dividend_yield'),
                    'dividend_rate': data.get('dividend_rate'),
                    'payout_ratio': data.get('payout_ratio'),
                    'ex_dividend_date': data.get('ex_dividend_date'),
                    'timestamp': timestamp
                }
                new_rows.append(new_row)

            if new_rows:
                new_df = pd.DataFrame(new_rows)
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_csv(file_path, index=False)

                self.logger.debug(f"✅ Stored {len(new_rows)} dividend records for {symbol}")
                return True

        except Exception as e:
            self.logger.error(f"❌ Failed to store dividend data for {symbol}: {e}")
            return False

    def load_dividend_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load dividend data for a symbol"""
        try:
            file_path = self.get_file_path('dividend')
            if not file_path.exists():
                return None

            df = pd.read_csv(file_path)
            symbol_data = df[df['symbol'] == symbol]

            if symbol_data.empty:
                return None

            # Convert to list of dictionaries
            dividends = []
            for _, row in symbol_data.iterrows():
                dividends.append({
                    'date': row.get('dividend_date'),
                    'amount': row.get('dividend_amount')
                })

            # Get summary data from the latest record
            latest = symbol_data.iloc[-1]

            return {
                'available': True,
                'dividends': dividends,
                'dividend_yield': latest.get('dividend_yield'),
                'dividend_rate': latest.get('dividend_rate'),
                'payout_ratio': latest.get('payout_ratio'),
                'ex_dividend_date': latest.get('ex_dividend_date'),
                'total_records': len(dividends),
                'last_updated': latest.get('timestamp')
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to load dividend data for {symbol}: {e}")
            return None

    def store_fees_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Store fees data for a symbol"""
        try:
            self.initialize_csv_file('fees')
            file_path = self.get_file_path('fees')

            df = pd.read_csv(file_path)
            df = df[df['symbol'] != symbol]  # Remove existing data

            new_row = {
                'symbol': symbol,
                'expense_ratio': data.get('expense_ratio'),
                'management_fee': data.get('management_fee'),
                'front_end_load': data.get('front_end_load'),
                'back_end_load': data.get('back_end_load'),
                'annual_holdings_turnover': data.get('annual_holdings_turnover'),
                'fund_family': data.get('fund_family'),
                'category': data.get('category'),
                'timestamp': datetime.now().isoformat()
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(file_path, index=False)

            self.logger.debug(f"✅ Stored fees data for {symbol}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to store fees data for {symbol}: {e}")
            return False

    def load_fees_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load fees data for a symbol"""
        try:
            file_path = self.get_file_path('fees')
            if not file_path.exists():
                return None

            df = pd.read_csv(file_path)
            symbol_data = df[df['symbol'] == symbol]

            if symbol_data.empty:
                return None

            latest = symbol_data.iloc[-1]

            return {
                'available': True,
                'expense_ratio': latest.get('expense_ratio'),
                'management_fee': latest.get('management_fee'),
                'front_end_load': latest.get('front_end_load'),
                'back_end_load': latest.get('back_end_load'),
                'annual_holdings_turnover': latest.get('annual_holdings_turnover'),
                'fund_family': latest.get('fund_family'),
                'category': latest.get('category'),
                'last_updated': latest.get('timestamp')
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to load fees data for {symbol}: {e}")
            return None

    def get_all_stored_symbols(self) -> List[str]:
        """Get all symbols that have any stored data"""
        symbols = set()

        for category in self.data_categories.keys():
            try:
                file_path = self.get_file_path(category)
                if file_path.exists():
                    df = pd.read_csv(file_path)
                    if 'symbol' in df.columns:
                        symbols.update(df['symbol'].unique())
            except Exception as e:
                self.logger.error(f"❌ Error reading symbols from {category}: {e}")

        return list(symbols)

    def clear_symbol_data(self, symbol: str, category: Optional[str] = None) -> bool:
        """Clear data for a symbol (all categories or specific category)"""
        try:
            categories = [category] if category else self.data_categories.keys()

            for cat in categories:
                file_path = self.get_file_path(cat)
                if file_path.exists():
                    df = pd.read_csv(file_path)
                    df = df[df['symbol'] != symbol]
                    df.to_csv(file_path, index=False)

            self.logger.info(f"✅ Cleared data for {symbol} ({category or 'all categories'})")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to clear data for {symbol}: {e}")
            return False

    def get_data_source_statistics(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about data sources used"""
        try:
            stats = {
                'by_category': {},
                'by_source': {},
                'total_records': 0,
                'symbols_analyzed': 0
            }

            for category in self.data_categories.keys():
                try:
                    file_path = self.get_file_path(category)
                    if not file_path.exists():
                        continue

                    df = pd.read_csv(file_path)

                    # Filter by symbol if specified
                    if symbol:
                        df = df[df['symbol'] == symbol]

                    if df.empty:
                        continue

                    # Count by data source
                    if 'data_source' in df.columns:
                        source_counts = df['data_source'].value_counts().to_dict()
                        stats['by_category'][category] = source_counts

                        # Aggregate by source
                        for source, count in source_counts.items():
                            if source not in stats['by_source']:
                                stats['by_source'][source] = 0
                            stats['by_source'][source] += count

                    stats['total_records'] += len(df)
                    if not symbol:
                        stats['symbols_analyzed'] += df['symbol'].nunique()

                except Exception as e:
                    self.logger.error(f"❌ Error analyzing {category}: {e}")
                    continue

            return stats

        except Exception as e:
            self.logger.error(f"❌ Error getting data source statistics: {e}")
            return {}

    def cross_validate_data(self, symbol: str, category: str) -> Dict[str, Any]:
        """Cross-validate data from multiple sources for the same symbol"""
        try:
            file_path = self.get_file_path(category)
            if not file_path.exists():
                return {'available': False, 'error': 'No data file found'}

            df = pd.read_csv(file_path)
            symbol_data = df[df['symbol'] == symbol]

            if symbol_data.empty:
                return {'available': False, 'error': 'No data found for symbol'}

            # Group by data source
            sources = symbol_data['data_source'].unique() if 'data_source' in symbol_data.columns else ['Unknown']

            if len(sources) <= 1:
                return {
                    'available': True,
                    'sources_count': len(sources),
                    'validation_status': 'single_source',
                    'primary_source': sources[0] if sources else 'Unknown'
                }

            # Compare data from different sources
            validation_results = {
                'available': True,
                'sources_count': len(sources),
                'validation_status': 'multi_source',
                'sources': list(sources),
                'discrepancies': [],
                'consensus_data': {}
            }

            # For real-time data, compare key metrics
            if category == 'real_time' and len(symbol_data) > 1:
                price_fields = ['current_price', 'nav']
                for field in price_fields:
                    if field in symbol_data.columns:
                        values = symbol_data[field].dropna()
                        if len(values) > 1:
                            std_dev = values.std()
                            mean_val = values.mean()
                            cv = (std_dev / mean_val) * 100 if mean_val != 0 else 0

                            if cv > 5:  # More than 5% coefficient of variation
                                validation_results['discrepancies'].append({
                                    'field': field,
                                    'coefficient_of_variation': cv,
                                    'values': values.to_dict(),
                                    'concern_level': 'high' if cv > 10 else 'medium'
                                })

                            validation_results['consensus_data'][field] = {
                                'mean': mean_val,
                                'median': values.median(),
                                'std_dev': std_dev,
                                'cv_percent': cv
                            }

            return validation_results

        except Exception as e:
            self.logger.error(f"❌ Error cross-validating data for {symbol}: {e}")
            return {'available': False, 'error': str(e)}

    def get_source_reliability_score(self, source: str) -> Dict[str, Any]:
        """Calculate reliability score for a data source"""
        try:
            total_records = 0
            successful_records = 0
            categories_covered = 0

            for category in self.data_categories.keys():
                try:
                    file_path = self.get_file_path(category)
                    if not file_path.exists():
                        continue

                    df = pd.read_csv(file_path)
                    if 'data_source' not in df.columns:
                        continue

                    source_data = df[df['data_source'] == source]
                    if source_data.empty:
                        continue

                    categories_covered += 1
                    category_records = len(source_data)
                    total_records += category_records

                    # Count successful records (non-null key fields)
                    if category == 'real_time':
                        successful_records += source_data['current_price'].notna().sum()
                    elif category == 'historical':
                        successful_records += source_data['close'].notna().sum()
                    else:
                        successful_records += category_records

                except Exception as e:
                    self.logger.debug(f"⚠️ Error analyzing {category} for {source}: {e}")
                    continue

            reliability_score = (successful_records / total_records) * 100 if total_records > 0 else 0

            return {
                'source': source,
                'reliability_score': reliability_score,
                'total_records': total_records,
                'successful_records': successful_records,
                'categories_covered': categories_covered,
                'coverage_percentage': (categories_covered / len(self.data_categories)) * 100
            }

        except Exception as e:
            self.logger.error(f"❌ Error calculating reliability for {source}: {e}")
            return {'source': source, 'reliability_score': 0, 'error': str(e)}


# Global instance
investment_data_storage = InvestmentDataStorage()
