"""
Progressive Investment Data Fetcher
Implements a robust data fetching system that loads from local storage first,
then updates in background with progress tracking
"""

import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from PySide6.QtCore import QObject, Signal, QTimer

from .data_storage import investment_data_storage
from .price_fetcher import price_fetcher
from .amfi_fetcher import amfi_fetcher
from .symbol_recognition import symbol_recognizer, SymbolType, DataSource


class ProgressiveDataFetcher(QObject):
    """Progressive data fetcher with local storage and background updates"""
    
    # Signals for progress tracking
    progress_updated = Signal(int, str)  # progress_percent, status_message
    data_category_completed = Signal(str, bool)  # category, success
    all_data_loaded = Signal(dict)  # complete_data
    error_occurred = Signal(str)  # error_message
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.storage = investment_data_storage
        self.fetcher = price_fetcher
        
        # Data categories and their fetch priorities
        self.data_categories = {
            'real_time': {'priority': 1, 'max_age_hours': 0.5, 'weight': 20},
            'historical': {'priority': 2, 'max_age_hours': 24, 'weight': 25},
            'performance': {'priority': 3, 'max_age_hours': 24, 'weight': 15},
            'financial': {'priority': 4, 'max_age_hours': 168, 'weight': 15},  # 1 week
            'portfolio': {'priority': 5, 'max_age_hours': 720, 'weight': 10},  # 1 month
            'dividend': {'priority': 6, 'max_age_hours': 168, 'weight': 10},
            'fees': {'priority': 7, 'max_age_hours': 720, 'weight': 5}
        }
        
        # Progress tracking
        self.total_weight = sum(cat['weight'] for cat in self.data_categories.values())
        self.completed_weight = 0
        self.current_symbol = None
        self.is_fetching = False
        self.cancel_requested = False
        
        # Results storage
        self.fetched_data = {}

        # Network status
        self.network_available = True
        self.last_network_check = None

        # Multi-source data fetching
        self.symbol_info = None
        self.data_sources_attempted = {}
        self.successful_sources = {}
        self.symbol_recognizer = symbol_recognizer

    def fetch_investment_data(self, symbol: str, force_refresh: bool = False) -> None:
        """
        Fetch investment data progressively with multi-source support
        1. Recognize symbol type and determine data sources
        2. Load from local storage immediately
        3. Check data freshness
        4. Fetch updates from appropriate sources in background
        """
        if self.is_fetching:
            self.logger.warning(f"Already fetching data, ignoring request for {symbol}")
            return

        self.current_symbol = symbol
        self.is_fetching = True
        self.cancel_requested = False
        self.completed_weight = 0
        self.fetched_data = {'symbol': symbol}

        # Recognize symbol type and determine data sources
        self.symbol_info = symbol_recognizer.recognize_symbol(symbol)
        self.data_sources_attempted = {}
        self.successful_sources = {}

        self.logger.info(f"🚀 Starting progressive data fetch for {symbol}")
        self.logger.info(f"🔍 Recognized as {self.symbol_info.symbol_type.value} "
                        f"(confidence: {self.symbol_info.confidence:.2f})")
        self.logger.info(f"📊 Primary source: {self.symbol_info.primary_source.value}, "
                        f"Fallbacks: {[s.value for s in self.symbol_info.fallback_sources]}")

        # Start the progressive loading process
        self.progress_updated.emit(0, f"Loading data for {symbol} ({self.symbol_info.symbol_type.value})...")

        # Load from local storage first (immediate)
        self._load_from_storage()

        # Check what needs updating and fetch in background
        self._start_background_updates(force_refresh)

    def _load_from_storage(self) -> None:
        """Load all available data from local storage immediately"""
        try:
            symbol = self.current_symbol
            
            # Load each category from storage
            storage_methods = {
                'real_time': self.storage.load_real_time_data,
                'historical': self.storage.load_historical_data,
                'performance': self.storage.load_performance_data,
                'financial': self.storage.load_financial_data,
                'portfolio': self.storage.load_portfolio_data,
                'dividend': self.storage.load_dividend_data,
                'fees': self.storage.load_fees_data
            }
            
            loaded_categories = 0
            for category, load_method in storage_methods.items():
                try:
                    data = load_method(symbol)
                    if data and data.get('available'):
                        self.fetched_data[f'{category}_data'] = data
                        loaded_categories += 1
                        self.logger.debug(f"✅ Loaded {category} data from storage for {symbol}")
                    else:
                        # Create placeholder for missing data
                        self.fetched_data[f'{category}_data'] = {'available': False, 'error': 'No local data available'}
                        
                except Exception as e:
                    self.logger.error(f"❌ Error loading {category} from storage: {e}")
                    self.fetched_data[f'{category}_data'] = {'available': False, 'error': str(e)}
            
            # Emit initial data (from storage)
            progress = min(50, (loaded_categories / len(storage_methods)) * 100)
            self.progress_updated.emit(int(progress), f"Loaded {loaded_categories} categories from local storage")
            
            # Emit the data we have so far
            self.all_data_loaded.emit(self.fetched_data.copy())
            
        except Exception as e:
            self.logger.error(f"❌ Error loading from storage: {e}")
            self.error_occurred.emit(f"Error loading local data: {e}")

    def _start_background_updates(self, force_refresh: bool = False) -> None:
        """Start background thread to fetch updates"""
        def background_fetch():
            try:
                self._fetch_updates_background(force_refresh)
            except Exception as e:
                self.logger.error(f"❌ Background fetch error: {e}")
                self.error_occurred.emit(f"Background update failed: {e}")
            finally:
                self.is_fetching = False
        
        thread = threading.Thread(target=background_fetch, daemon=True)
        thread.start()

    def _fetch_updates_background(self, force_refresh: bool = False) -> None:
        """Fetch updates in background thread"""
        symbol = self.current_symbol
        categories_to_update = []
        
        # Determine which categories need updating
        for category, config in self.data_categories.items():
            if self.cancel_requested:
                break
                
            needs_update = (force_refresh or 
                          self.storage.is_data_stale(symbol, category, config['max_age_hours']))
            
            if needs_update:
                categories_to_update.append(category)
        
        if not categories_to_update and not force_refresh:
            self.progress_updated.emit(100, "All data is up to date")
            return
        
        # Sort by priority
        categories_to_update.sort(key=lambda x: self.data_categories[x]['priority'])
        
        self.logger.info(f"📡 Fetching updates for {len(categories_to_update)} categories: {categories_to_update}")
        
        # Fetch each category
        for i, category in enumerate(categories_to_update):
            if self.cancel_requested:
                break
                
            try:
                # Update progress
                base_progress = 50  # We already loaded from storage
                category_progress = (i / len(categories_to_update)) * 50
                total_progress = int(base_progress + category_progress)
                
                self.progress_updated.emit(total_progress, f"Fetching {category} data...")
                
                # Fetch the data
                success = self._fetch_category_data(symbol, category)
                
                # Update completed weight
                if success:
                    self.completed_weight += self.data_categories[category]['weight']
                
                # Emit category completion
                self.data_category_completed.emit(category, success)
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"❌ Error fetching {category} data: {e}")
                self.data_category_completed.emit(category, False)
        
        # Final progress update
        if not self.cancel_requested:
            self.progress_updated.emit(100, "Data fetch completed")
            
            # Reload all data from storage and emit final result
            self._load_from_storage()

    def _fetch_category_data(self, symbol: str, category: str) -> bool:
        """Fetch data for a specific category with multi-source support"""
        try:
            # Check if category is supported for this symbol type FIRST
            if not self._is_category_supported_for_symbol_type(category, self.symbol_info.symbol_type):
                self.logger.info(f"ℹ️ Category {category} is not supported for {self.symbol_info.symbol_type.value}")
                # Mark as successful but with no data (expected behavior)
                self.successful_sources[category] = 'Not applicable'
                self.data_sources_attempted[category] = ['Not applicable']
                return True

            # Check network connectivity
            if not self.check_network_connectivity():
                self.logger.warning(f"⚠️ No network connectivity, using cached data for {category}")
                return self.handle_network_failure(category, symbol)

            # Get prioritized data sources for this symbol
            data_sources = symbol_recognizer.get_data_source_priority(self.symbol_info)

            # Track attempts for this category
            self.data_sources_attempted[category] = []

            # Try each data source in priority order
            for source in data_sources:
                if self.cancel_requested:
                    break

                try:
                    self.logger.debug(f"🔄 Trying {source.value} for {category} data")
                    self.data_sources_attempted[category].append(source.value)

                    success = self._fetch_from_source(symbol, category, source)

                    if success:
                        self.successful_sources[category] = source.value
                        self.logger.info(f"✅ Successfully fetched {category} data from {source.value}")
                        return True
                    else:
                        self.logger.debug(f"⚠️ {source.value} failed for {category}, trying next source")

                except Exception as source_error:
                    self.logger.warning(f"⚠️ Error with {source.value} for {category}: {source_error}")
                    continue

            # If all sources failed, try cached data
            self.logger.warning(f"⚠️ All data sources failed for {category}, using cached data")
            self.logger.info(f"📊 Attempted sources for {category}: {self.data_sources_attempted.get(category, [])}")

            return self.handle_network_failure(category, symbol)

        except Exception as e:
            self.logger.error(f"❌ Error in _fetch_category_data for {category}: {e}")
            return self.handle_network_failure(category, symbol)

    def _fetch_from_source(self, symbol: str, category: str, source: DataSource) -> bool:
        """Fetch data from a specific source"""
        try:
            if source == DataSource.YAHOO_FINANCE:
                return self._fetch_from_yahoo_finance(symbol, category)
            elif source == DataSource.AMFI_DIRECT:
                return self._fetch_from_amfi(symbol, category)
            elif source == DataSource.MFTOOL:
                return self._fetch_from_mftool(symbol, category)
            else:
                self.logger.warning(f"⚠️ Unknown data source: {source}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error fetching from {source.value}: {e}")
            return False

    def _fetch_from_yahoo_finance(self, symbol: str, category: str) -> bool:
        """Fetch data from Yahoo Finance"""
        try:
            # Use the normalized symbol for Yahoo Finance
            yahoo_symbol = self.symbol_info.metadata.get('yahoo_symbol', self.symbol_info.normalized_symbol)

            # Check if this category is supported for this symbol type
            if not self._is_category_supported_for_symbol_type(category, self.symbol_info.symbol_type):
                self.logger.debug(f"⚠️ Category {category} not supported for {self.symbol_info.symbol_type.value}")
                return False

            fetch_functions = {
                'real_time': lambda: self.fetcher._get_real_time_data(yahoo_symbol),
                'historical': lambda: self.fetcher._get_historical_data(yahoo_symbol, "1y"),
                'performance': lambda: self.fetcher._get_performance_data(yahoo_symbol),
                'financial': lambda: self.fetcher._get_financial_data(yahoo_symbol),
                'portfolio': lambda: self.fetcher._get_portfolio_data(yahoo_symbol),
                'dividend': lambda: self.fetcher._get_dividend_data(yahoo_symbol),
                'fees': lambda: self.fetcher._get_fees_data(yahoo_symbol)
            }

            storage_functions = {
                'real_time': lambda data: self.storage.store_real_time_data(symbol, self._add_source_info(data, 'Yahoo Finance')),
                'historical': lambda data: self.storage.store_historical_data(symbol, data.get('data', []), "1y"),
                'performance': lambda data: self.storage.store_performance_data(symbol, self._add_source_info(data, 'Yahoo Finance')),
                'financial': lambda data: self.storage.store_financial_data(symbol, self._add_source_info(data, 'Yahoo Finance')),
                'portfolio': lambda data: self.storage.store_portfolio_data(symbol, self._add_source_info(data, 'Yahoo Finance')),
                'dividend': lambda data: self.storage.store_dividend_data(symbol, self._add_source_info(data, 'Yahoo Finance')),
                'fees': lambda data: self.storage.store_fees_data(symbol, self._add_source_info(data, 'Yahoo Finance'))
            }

            if category not in fetch_functions:
                return False

            def fetch_and_store():
                data = fetch_functions[category]()
                if data and data.get('available'):
                    return storage_functions[category](data)
                return False

            return self.retry_with_backoff(fetch_and_store, max_attempts=2)

        except Exception as e:
            self.logger.error(f"❌ Yahoo Finance fetch error for {category}: {e}")
            return False

    def _is_category_supported_for_symbol_type(self, category: str, symbol_type: SymbolType) -> bool:
        """Check if a data category is supported for a given symbol type"""
        # Define which categories are supported for each symbol type
        category_support = {
            SymbolType.INDIAN_STOCK: ['real_time', 'historical', 'performance', 'financial', 'portfolio', 'dividend'],
            SymbolType.INDIAN_ETF: ['real_time', 'historical', 'performance', 'fees'],
            SymbolType.INDIAN_MUTUAL_FUND: ['real_time', 'historical', 'performance', 'fees'],  # Limited for MFs
            SymbolType.INTERNATIONAL_STOCK: ['real_time', 'historical', 'performance', 'financial', 'portfolio', 'dividend'],
            SymbolType.INTERNATIONAL_ETF: ['real_time', 'historical', 'performance', 'fees'],
            SymbolType.INTERNATIONAL_MUTUAL_FUND: ['real_time', 'historical', 'performance', 'fees'],
            SymbolType.UNKNOWN: ['real_time', 'historical']  # Conservative approach for unknown symbols
        }

        supported_categories = category_support.get(symbol_type, [])
        return category in supported_categories

    def _fetch_from_amfi(self, symbol: str, category: str) -> bool:
        """Fetch data from AMFI Direct API"""
        try:
            # AMFI primarily provides real-time NAV data
            if category == 'real_time':
                data = amfi_fetcher.get_nav_data(symbol)
                if data and data.get('available'):
                    # Add additional source information
                    data = self._add_source_info(data, 'AMFI Direct')
                    return self.storage.store_real_time_data(symbol, data)

            # AMFI doesn't provide other categories, return False to try next source
            return False

        except Exception as e:
            self.logger.error(f"❌ AMFI fetch error for {category}: {e}")
            return False

    def _fetch_from_mftool(self, symbol: str, category: str) -> bool:
        """Fetch data from mftool library"""
        try:
            # mftool primarily provides mutual fund data
            if category == 'real_time' and self.symbol_info.symbol_type == SymbolType.INDIAN_MUTUAL_FUND:
                # Try to use existing mftool integration from price_fetcher
                # This would need to be implemented in price_fetcher.py
                return False  # Placeholder for now

            return False

        except Exception as e:
            self.logger.error(f"❌ mftool fetch error for {category}: {e}")
            return False

    def _add_source_info(self, data: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        """Add data source information to fetched data"""
        if isinstance(data, dict):
            data = data.copy()
            data['data_source'] = source_name
            data['source_timestamp'] = datetime.now().isoformat()
        return data

    def cancel_fetch(self) -> None:
        """Cancel the current fetch operation"""
        self.cancel_requested = True
        self.is_fetching = False
        self.progress_updated.emit(0, "Fetch cancelled")
        self.logger.info("🛑 Data fetch cancelled by user")

    def get_data_freshness_info(self, symbol: str) -> Dict[str, Any]:
        """Get information about data freshness for all categories"""
        freshness_info = {}
        
        for category in self.data_categories.keys():
            freshness = self.storage.get_data_freshness(symbol, category)
            is_stale = self.storage.is_data_stale(symbol, category, 
                                                self.data_categories[category]['max_age_hours'])
            
            freshness_info[category] = {
                'last_updated': freshness.isoformat() if freshness else None,
                'is_stale': is_stale,
                'max_age_hours': self.data_categories[category]['max_age_hours']
            }
        
        return freshness_info

    def clear_cache(self, symbol: str) -> None:
        """Clear cached data for a symbol"""
        self.storage.clear_symbol_data(symbol)
        self.logger.info(f"🗑️ Cleared cached data for {symbol}")

    def check_network_connectivity(self) -> bool:
        """Check if network is available for data fetching with multiple fallback endpoints"""
        # Only check every 10 seconds to avoid excessive requests (reduced from 30s)
        if (self.last_network_check and
            datetime.now() - self.last_network_check < timedelta(seconds=10)):
            return self.network_available

        # Multiple endpoints to try (in order of preference)
        test_endpoints = [
            'https://query1.finance.yahoo.com/v8/finance/chart/AAPL',  # Primary - Yahoo Finance API
            'https://finance.yahoo.com',  # Secondary - Yahoo Finance main site
            'https://www.google.com',     # Fallback 1 - Google (very reliable)
            'https://httpbin.org/status/200',  # Fallback 2 - Original endpoint
        ]

        self.network_available = False
        last_error = None

        for i, endpoint in enumerate(test_endpoints):
            try:
                self.logger.debug(f"🔍 Testing network connectivity to {endpoint}")

                # Increased timeout and added headers to look more like a real browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }

                response = requests.get(
                    endpoint,
                    timeout=10,  # Increased from 5 to 10 seconds
                    headers=headers,
                    allow_redirects=True
                )

                # Accept various status codes that indicate network connectivity
                if response.status_code in [200, 301, 302, 403, 429]:  # Include 429 (rate limited)
                    self.network_available = True
                    self.last_network_check = datetime.now()

                    if response.status_code == 429:
                        self.logger.info(f"✅ Network connectivity confirmed via {endpoint} (rate limited - status: {response.status_code})")
                    else:
                        self.logger.info(f"✅ Network connectivity confirmed via {endpoint} (status: {response.status_code})")
                    break
                else:
                    self.logger.debug(f"⚠️ Endpoint {endpoint} returned status {response.status_code}")

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout connecting to {endpoint}: {e}"
                self.logger.debug(f"⏱️ Timeout connecting to {endpoint}")

            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error to {endpoint}: {e}"
                self.logger.debug(f"🔌 Connection error to {endpoint}")

            except requests.exceptions.RequestException as e:
                last_error = f"Request error to {endpoint}: {e}"
                self.logger.debug(f"📡 Request error to {endpoint}: {e}")

            except Exception as e:
                last_error = f"Unexpected error testing {endpoint}: {e}"
                self.logger.debug(f"❌ Unexpected error testing {endpoint}: {e}")

        # Update timestamp even if all failed
        self.last_network_check = datetime.now()

        if not self.network_available:
            self.logger.warning(f"⚠️ All network connectivity tests failed. Last error: {last_error}")
            self.logger.info("🔄 Will attempt to use cached data as fallback")

        return self.network_available

    def force_network_check(self) -> bool:
        """Force a fresh network connectivity check (bypass cache)"""
        self.last_network_check = None  # Reset cache
        return self.check_network_connectivity()

    def get_network_status_details(self) -> dict:
        """Get detailed network status information for debugging"""
        return {
            'network_available': self.network_available,
            'last_check': self.last_network_check.isoformat() if self.last_network_check else None,
            'cache_age_seconds': (datetime.now() - self.last_network_check).total_seconds() if self.last_network_check else None,
            'will_check_network': not self.last_network_check or datetime.now() - self.last_network_check >= timedelta(seconds=10)
        }

    def handle_network_failure(self, category: str, symbol: str) -> bool:
        """Handle network failure gracefully by using cached data"""
        try:
            self.logger.info(f"🔄 Network failure, attempting to use cached data for {category}")

            # Try to load from local storage as fallback
            storage_methods = {
                'real_time': self.storage.load_real_time_data,
                'historical': self.storage.load_historical_data,
                'performance': self.storage.load_performance_data,
                'financial': self.storage.load_financial_data,
                'portfolio': self.storage.load_portfolio_data,
                'dividend': self.storage.load_dividend_data,
                'fees': self.storage.load_fees_data
            }

            if category in storage_methods:
                cached_data = storage_methods[category](symbol)
                if cached_data and cached_data.get('available'):
                    self.fetched_data[f'{category}_data'] = cached_data

                    # Add staleness warning
                    freshness = self.storage.get_data_freshness(symbol, category)
                    if freshness:
                        age = datetime.now() - freshness
                        cached_data['staleness_warning'] = f"Data is {age.days} days old (offline mode)"

                    self.logger.info(f"✅ Using cached {category} data for {symbol}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"❌ Failed to handle network failure for {category}: {e}")
            return False

    def get_retry_delay(self, attempt: int, is_rate_limited: bool = False) -> float:
        """Get exponential backoff delay for retries"""
        if is_rate_limited:
            # Longer delays for rate limiting
            base_delay = 5.0  # 5 second base delay for rate limits
            max_delay = 60.0  # Maximum 60 seconds for rate limits
        else:
            base_delay = 1.0  # 1 second base delay for other errors
            max_delay = 30.0  # Maximum 30 seconds for other errors

        delay = min(base_delay * (2 ** attempt), max_delay)
        return delay

    def retry_with_backoff(self, func, max_attempts: int = 3, *args, **kwargs):
        """Retry a function with exponential backoff and rate limit handling"""
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_attempts - 1:  # Last attempt
                    raise e

                # Check if this is a rate limiting error
                is_rate_limited = (
                    "429" in str(e) or
                    "rate limit" in str(e).lower() or
                    "too many requests" in str(e).lower()
                )

                delay = self.get_retry_delay(attempt, is_rate_limited)

                if is_rate_limited:
                    self.logger.warning(f"🚦 Rate limited on attempt {attempt + 1}, waiting {delay:.1f}s before retry: {e}")
                else:
                    self.logger.warning(f"⚠️ Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {e}")

                time.sleep(delay)

        return None


# Global instance
progressive_fetcher = ProgressiveDataFetcher()
