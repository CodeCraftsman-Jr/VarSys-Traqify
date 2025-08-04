"""
Price Fetching Service for Investment Tracking
Handles fetching current prices from Yahoo Finance API with proper error handling
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import threading

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

try:
    from mftool import Mftool
    import requests
    import pandas as pd
    MFTOOL_AVAILABLE = True
except ImportError:
    MFTOOL_AVAILABLE = False
    Mftool = None
    pd = None


class PriceFetcher:
    """Service for fetching current investment prices from Yahoo Finance and alternative sources"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(minutes=5)  # Cache prices for 5 minutes
        self.request_delay = 0.1  # Delay between requests to avoid rate limiting
        self.last_request_time = 0
        self.YFINANCE_AVAILABLE = YFINANCE_AVAILABLE  # Expose the module-level variable
        self.MFTOOL_AVAILABLE = MFTOOL_AVAILABLE

        # Enhanced caching for detailed data
        self.detailed_cache = {}
        self.detailed_cache_expiry = {}
        self.detailed_cache_duration = timedelta(hours=1)  # Cache detailed data for 1 hour

        # Initialize mftool for Indian mutual fund data with error handling
        self.mf = None
        if MFTOOL_AVAILABLE:
            try:
                self.mf = Mftool()
                self.logger.info("✅ Mftool initialized successfully")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to initialize Mftool: {e}")
                self.logger.warning("Continuing without mftool - mutual fund data may be limited")
                self.MFTOOL_AVAILABLE = False

        self._setup_ssl_handling()

        # Symbol mapping for Indian stocks and mutual funds
        self.symbol_mappings = {
            # Common Indian stock symbols
            'HDFCBANK': 'HDFCBANK.NS',
            'HINDUNILVR': 'HINDUNILVR.NS',
            'RELIANCE': 'RELIANCE.NS',
            'TCS': 'TCS.NS',
            'INFY': 'INFY.NS',
            'ICICIBANK': 'ICICIBANK.NS',
            'SBIN': 'SBIN.NS',
            'BHARTIARTL': 'BHARTIARTL.NS',
            'ITC': 'ITC.NS',
            'KOTAKBANK': 'KOTAKBANK.NS',

            # ETFs and Index Funds
            'GOLDBEES': 'GOLDBEES.NS',
            'NIFTYBEES': 'NIFTYBEES.NS',
            'JUNIORBEES': 'JUNIORBEES.NS',

            # Direct stock symbols (add .NS suffix for Indian stocks)
            'GOLDBEES.NS': 'GOLDBEES.NS',
            'HDFCBANK.NS': 'HDFCBANK.NS',
            'HINDUNILVR.NS': 'HINDUNILVR.NS',
            # 'UTI': 'UTI.BO',  # UTI appears to be delisted - commented out
            # Note: UTI stock appears to be delisted from both NSE and BSE
            # User should update this symbol or remove the investment

            # Actual Yahoo Finance Ticker Symbols (No Proxy/Fallback Mappings)
            # Axis Mutual Funds - Only verified working tickers
            'AXIS_ELSS_TAX_SAVER': '0P0000XVU7.BO',   # Axis Long Term Equity (ELSS)
            '0P0000XVU8.BO': '0P0000XVU8.BO',         # Axis Bluechip Fund (direct symbol)

            # Navi Funds - Only actual tickers
            'NAVI_NIFTY_50_INDEX': 'NIFTYBEES.NS',    # Navi Nifty 50 Index ETF

            # UTI Stock - Corrected symbol
            'UTIAMC.NS': 'UTIAMC.NS',  # UTI Asset Management Company (direct symbol)

            # ✅ FIX: Add missing symbol mappings for consistent data fetching
            # These symbols have AMFI data but need Yahoo Finance mappings for detailed data
            # Using proxy symbols that provide similar market data for performance/financial analysis
            'KOTAK_CORP_BOND_FUND': 'KOTAKBANK.NS',      # Use Kotak Bank as proxy for corporate bond analysis
            'KOTAK_FLEX_CAP_FUND': 'KOTAKBANK.NS',       # Use Kotak Bank as proxy for flexicap analysis
            'MOTILAL_NASDAQ_100_FOF': 'NIFTYBEES.NS',    # Use Nifty ETF as proxy for index fund analysis
            'MOTILAL_SP_500_FOF': 'NIFTYBEES.NS',        # Use Nifty ETF as proxy for international fund analysis
            'EDEL_BANK_PSU_BENFIT': 'SBIN.NS',           # Use SBI as proxy for banking/PSU bond analysis
            'NAVI_NIFT_MDCP_150IND': 'JUNIORBEES.NS',    # Use Junior Bees as proxy for midcap analysis

            # Additional Yahoo Finance mappings for mutual funds (where available)
            # Note: Many mutual funds don't have direct Yahoo Finance tickers
            # These will fall back to AMFI/mftool data sources

            # Note: The following symbols have been REMOVED (no valid Yahoo Finance tickers):
            # - AXIS_BLUE_FUND_5L9BJX (Axis Bluechip Fund) - No working ticker found
            # - EDEL_BANK_PSU_BENFIT (Edelweiss Banking and PSU Bond Fund)
            # - KOTAK_CORP_BOND_FUND (Kotak Corporate Bond Fund)
            # - KOTAK_FLEX_CAP_FUND (Kotak Flexicap Fund)
            # - MOTILAL_NASDAQ_100_FOF (Motilal Oswal Nasdaq 100 FOF)
            # - MOTILAL_SP_500_FOF (Motilal Oswal S&P 500 FOF)
            # - NAVI_NIFT_MDCP_150IND (Navi Nifty Midcap 150 Index ETF)
            # - UTI (UTI Stock)
            # These will show "No data found" instead of proxy prices

            # International symbols (already in correct format)
            'AAPL': 'AAPL',
            'GOOGL': 'GOOGL',
            'MSFT': 'MSFT',
            'TSLA': 'TSLA',
        }

        # Mutual Fund Scheme Mappings for AMFI/mftool integration
        # Maps custom symbols to exact AMFI scheme names for NAV fetching
        self.mutual_fund_mappings = {
            # Working AMFI scheme names (verified from AMFI database)
            'EDEL_BANK_PSU_BENFIT': 'Edelweiss Banking and PSU Debt Fund - Direct Plan - Growth Option',
            'KOTAK_CORP_BOND_FUND': 'Kotak Corporate Bond Fund- Direct Plan- Growth Option',

            # Verified AMFI scheme names (found in live AMFI data 21-Jul-2025)
            'KOTAK_FLEX_CAP_FUND': 'Kotak Flexicap Fund - Growth - Direct',  # NAV: 96.406
            'MOTILAL_NASDAQ_100_FOF': 'Motilal Oswal Nasdaq 100 Fund of Fund- Direct Plan Growth',  # NAV: 41.5869
            'MOTILAL_SP_500_FOF': 'Motilal Oswal S&P 500 Index Fund - Direct Plan Growth',  # NAV: 25.0381
            'NAVI_NIFT_MDCP_150IND': 'Navi Nifty Midcap 150 Index Fund Direct Plan- Growth',  # NAV: 20.7916

            # Note: AXIS_BLUE_FUND_5L9BJX and UTI now use Yahoo Finance mappings above
        }

        # Symbol status information with alternative data source support
        self.symbol_status = {
            # Symbols with verified working Yahoo Finance tickers
            'AXIS_ELSS_TAX_SAVER': 'Axis Long Term Equity (ELSS) - Yahoo Finance: 0P0000XVU7.BO',
            'AXIS_BLUE_FUND_5L9BJX': 'Axis Bluechip Fund - Yahoo Finance: 0P0000XVU8.BO',
            'NAVI_NIFTY_50_INDEX': 'Navi Nifty 50 Index ETF - Yahoo Finance: NIFTYBEES.NS',
            'HDFCBANK.NS': 'HDFC Bank - Yahoo Finance: HDFCBANK.NS',
            'GOLDBEES.NS': 'Gold ETF - Yahoo Finance: GOLDBEES.NS',
            'HINDUNILVR.NS': 'Hindustan Unilever - Yahoo Finance: HINDUNILVR.NS',
            'UTI': 'UTI Asset Management Company - Yahoo Finance: UTIAMC.NS',

            # ✅ FIX: Updated symbols with hybrid data sources (AMFI NAV + Yahoo Finance proxy for detailed data)
            'EDEL_BANK_PSU_BENFIT': 'Edelweiss Banking PSU Fund - NAV: AMFI, Analysis: SBIN.NS proxy',
            'KOTAK_CORP_BOND_FUND': 'Kotak Corporate Bond Fund - NAV: AMFI, Analysis: KOTAKBANK.NS proxy',
            'KOTAK_FLEX_CAP_FUND': 'Kotak Flexicap Fund - NAV: AMFI, Analysis: KOTAKBANK.NS proxy',
            'MOTILAL_NASDAQ_100_FOF': 'Motilal Nasdaq 100 FOF - NAV: AMFI, Analysis: NIFTYBEES.NS proxy',
            'MOTILAL_SP_500_FOF': 'Motilal S&P 500 FOF - NAV: AMFI, Analysis: NIFTYBEES.NS proxy',
            'NAVI_NIFT_MDCP_150IND': 'Navi Midcap 150 Index - NAV: AMFI, Analysis: JUNIORBEES.NS proxy',
            'KOTAK_FLEX_CAP_FUND': 'Kotak Flexicap Fund - AMFI NAV data',
            'MOTILAL_NASDAQ_100_FOF': 'Motilal Oswal Nasdaq 100 FOF - AMFI NAV data',
            'MOTILAL_SP_500_FOF': 'Motilal Oswal S&P 500 FOF - AMFI NAV data',
            'NAVI_NIFT_MDCP_150IND': 'Navi Nifty Midcap 150 Index Fund - AMFI NAV data',
        }
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for Yahoo Finance API"""
        if not symbol:
            self.logger.warning("Empty or None symbol passed to _normalize_symbol")
            return ""

        # Remove common prefixes
        symbol = symbol.replace('NSE:', '').replace('BSE:', '').strip()

        # Check if it's in our mapping
        if symbol in self.symbol_mappings:
            return self.symbol_mappings[symbol]

        # If it already has an exchange suffix, use as is
        if '.' in symbol:
            return symbol

        # For Indian symbols, add .NS suffix by default
        # This is a heuristic - may need refinement based on actual data
        if symbol.isupper() and len(symbol) <= 12:
            return f"{symbol}.NS"

        return symbol

    def _get_analysis_symbol(self, symbol: str) -> str:
        """Get the appropriate symbol for detailed analysis (performance, financial, etc.)

        For custom mutual fund symbols, this returns a proxy symbol that provides
        similar market data for analysis purposes, while preserving the original
        symbol for NAV/price data from AMFI sources.
        """
        # For custom symbols with proxy mappings, use the proxy for analysis
        if symbol in self.symbol_mappings:
            proxy_symbol = self.symbol_mappings[symbol]

            # Check if this is a proxy mapping (different from original)
            if proxy_symbol != symbol and symbol in self.mutual_fund_mappings:
                self.logger.debug(f"Using proxy symbol {proxy_symbol} for analysis of {symbol}")
                return proxy_symbol

            return proxy_symbol

        # Fallback to normalization
        return self._normalize_symbol(symbol)
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached price is still valid"""
        if symbol not in self.cache or symbol not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[symbol]
    
    def _rate_limit(self):
        """Implement rate limiting to avoid overwhelming the API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a single symbol with fallback to alternative data sources"""
        if not symbol:
            return None

        # Check cache first
        if self._is_cache_valid(symbol):
            self.logger.debug(f"Using cached price for {symbol}")
            return self.cache[symbol]

        # Phase 1: Try Yahoo Finance first (if available)
        if YFINANCE_AVAILABLE:
            price = self._fetch_price_for_symbol(symbol)
            if price is not None:
                self.logger.debug(f"Successfully fetched price from Yahoo Finance for {symbol}: ₹{price:.2f}")
                return price

        # Phase 2: Try alternative data sources for mutual funds
        if symbol in self.mutual_fund_mappings:
            scheme_name = self.mutual_fund_mappings[symbol]
            self.logger.info(f"Yahoo Finance failed for {symbol}, trying alternative sources...")

            # Try mftool first
            if self.MFTOOL_AVAILABLE:
                price = self.get_mf_nav_from_mftool(scheme_name)
                if price is not None:
                    # Cache the result
                    self.cache[symbol] = price
                    self.cache_expiry[symbol] = datetime.now() + self.cache_duration
                    self.logger.info(f"✅ Successfully fetched NAV from mftool for {symbol}: ₹{price:.2f}")
                    return price

            # Try direct AMFI API as fallback
            price = self.get_mf_nav_from_direct_api(scheme_name)
            if price is not None:
                # Cache the result
                self.cache[symbol] = price
                self.cache_expiry[symbol] = datetime.now() + self.cache_duration
                self.logger.info(f"✅ Successfully fetched NAV from direct AMFI API for {symbol}: ₹{price:.2f}")
                return price

        # Phase 2.5: Try intelligent mutual fund name matching for unmapped symbols
        price = self._try_intelligent_mf_matching(symbol)
        if price is not None:
            return price

        # Phase 3: All sources failed - log detailed error information
        self._log_symbol_failure(symbol)
        return None

    def _log_symbol_failure(self, symbol: str):
        """Log detailed information about why a symbol failed"""
        normalized_symbol = self._normalize_symbol(symbol)

        if symbol in self.symbol_status:
            # Known symbol with status information
            status = self.symbol_status[symbol]
            if "Alternative: AMFI/mftool NAV data" in status:
                # Symbol should have been handled by alternative sources but failed
                self.logger.error(f"❌ All data sources failed for {symbol}")
                self.logger.error(f"   Status: {status}")
                self.logger.error(f"   Tried: Yahoo Finance, mftool, direct AMFI API")
                if symbol in self.mutual_fund_mappings:
                    scheme_name = self.mutual_fund_mappings[symbol]
                    self.logger.error(f"   AMFI scheme name: {scheme_name}")
                self.logger.error(f"   Reason: All available data sources returned no data")
            else:
                # Symbol has Yahoo Finance mapping but failed
                self.logger.error(f"❌ Symbol lookup failed for {symbol}")
                self.logger.error(f"   Original symbol: {symbol}")
                self.logger.error(f"   Mapped to: {normalized_symbol}")
                self.logger.error(f"   Status: {status}")
                self.logger.error(f"   Reason: Yahoo Finance API returned no data for {normalized_symbol}")
        elif symbol in self.symbol_mappings:
            # Has direct mapping but failed
            mapped_to = self.symbol_mappings[symbol]
            self.logger.error(f"❌ Symbol lookup failed for {symbol}")
            self.logger.error(f"   Original symbol: {symbol}")
            self.logger.error(f"   Mapped to: {mapped_to}")
            self.logger.error(f"   Reason: Yahoo Finance API returned no data for {mapped_to}")
        else:
            # No mapping available - show "No data found"
            self.logger.warning(f"⚠️  No data found for {symbol}")
            self.logger.warning(f"   Original symbol: {symbol}")
            self.logger.warning(f"   Normalized to: {normalized_symbol}")
            self.logger.warning(f"   Reason: No symbol mapping found - not available on any data source")

            # Suggest possible solutions
            if symbol.endswith('.NS'):
                self.logger.info(f"   Note: Symbol appears to be Indian stock - verify ticker symbol")
            elif '_' in symbol:
                self.logger.info(f"   Note: Symbol contains underscores - likely a custom identifier")
                self.logger.info(f"   Suggestion: Add to mutual_fund_mappings if it's a mutual fund")
            else:
                self.logger.info(f"   Note: Verify symbol exists on Yahoo Finance or add alternative mapping")

    def _fetch_price_for_symbol(self, symbol: str) -> Optional[float]:
        """Internal method to fetch price for a specific symbol"""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            self.logger.debug(f"Fetching price for {symbol} -> {normalized_symbol}")

            # Rate limiting
            self._rate_limit()

            # Fetch data from Yahoo Finance
            # Handle SSL certificate issues on Windows
            import os
            original_verify = os.environ.get('PYTHONHTTPSVERIFY')

            try:
                # If SSL verification is disabled, ensure it's set for this request
                if os.environ.get('PYTHONHTTPSVERIFY') == '0':
                    # Disable SSL warnings for this request
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

                ticker = yf.Ticker(normalized_symbol)
                info = ticker.info

            except Exception as ssl_error:
                # If we get an SSL error, try with SSL verification disabled
                if "SSL" in str(ssl_error).upper() or "CERTIFICATE" in str(ssl_error).upper():
                    self.logger.warning(f"SSL error encountered, retrying with SSL verification disabled: {ssl_error}")
                    os.environ['PYTHONHTTPSVERIFY'] = '0'

                    # Disable SSL warnings
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

                    # Retry the request
                    ticker = yf.Ticker(normalized_symbol)
                    info = ticker.info
                else:
                    raise  # Re-raise non-SSL errors

            # Try different price fields in order of preference
            price = None
            price_fields = ['regularMarketPrice', 'currentPrice', 'previousClose', 'open']

            for field in price_fields:
                if field in info and info[field] is not None:
                    price = float(info[field])
                    break

            if price is None:
                # Try getting recent data
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])

            if price is not None:
                # Cache the result
                self.cache[symbol] = price
                self.cache_expiry[symbol] = datetime.now() + self.cache_duration
                self.logger.debug(f"Successfully fetched price for {normalized_symbol}: ₹{price:.2f}")
                return price
            else:
                self.logger.warning(f"No price data found for {normalized_symbol}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Get current prices for multiple symbols"""
        if not YFINANCE_AVAILABLE:
            self.logger.warning("yfinance library not available")
            return {symbol: None for symbol in symbols}
        
        results = {}
        
        # Separate cached and non-cached symbols
        cached_symbols = []
        fetch_symbols = []
        
        for symbol in symbols:
            if self._is_cache_valid(symbol):
                results[symbol] = self.cache[symbol]
                cached_symbols.append(symbol)
            else:
                fetch_symbols.append(symbol)
        
        if cached_symbols:
            self.logger.debug(f"Using cached prices for {len(cached_symbols)} symbols")
        
        # Fetch non-cached symbols
        for symbol in fetch_symbols:
            price = self.get_current_price(symbol)
            results[symbol] = price
            
            # Small delay between requests to be respectful to the API
            if len(fetch_symbols) > 1:
                time.sleep(0.1)
        
        return results
    
    def clear_cache(self):
        """Clear the price cache"""
        self.cache.clear()
        self.cache_expiry.clear()
        self.logger.info("Price cache cleared")

    def _setup_ssl_handling(self):
        """Setup SSL handling for Windows certificate issues"""
        try:
            import ssl
            import os

            # Check if SSL verification is disabled via environment variable
            if os.environ.get('PYTHONHTTPSVERIFY') == '0':
                self.logger.info("🔧 SSL verification disabled via environment variable")

                # Disable SSL warnings
                try:
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                except ImportError:
                    pass  # urllib3 not available

        except Exception as e:
            self.logger.debug(f"SSL setup warning: {e}")

    def get_mf_nav_from_mftool(self, scheme_name: str) -> Optional[float]:
        """Get mutual fund NAV using mftool library"""
        if not self.MFTOOL_AVAILABLE or not self.mf:
            self.logger.warning("mftool library not available")
            return None

        try:
            self.logger.debug(f"Fetching NAV from mftool for scheme: {scheme_name}")

            # Rate limiting for AMFI API
            self._rate_limit()

            # Search for the scheme
            schemes = self.mf.get_scheme_codes()
            if not schemes:
                self.logger.warning("Could not fetch scheme codes from mftool")
                return None

            # Find matching scheme (case-insensitive partial match)
            scheme_name_lower = scheme_name.lower()
            matching_schemes = []

            for scheme_code, scheme_details in schemes.items():
                if isinstance(scheme_details, dict) and 'scheme_name' in scheme_details:
                    if scheme_name_lower in scheme_details['scheme_name'].lower():
                        matching_schemes.append((scheme_code, scheme_details['scheme_name']))

            if not matching_schemes:
                self.logger.warning(f"No matching schemes found for: {scheme_name}")
                return None

            # Use the first matching scheme
            scheme_code, found_scheme_name = matching_schemes[0]
            self.logger.debug(f"Found matching scheme: {found_scheme_name} (Code: {scheme_code})")

            # Get NAV data
            nav_data = self.mf.get_scheme_quote(scheme_code)
            if nav_data and 'nav' in nav_data:
                nav_value = float(nav_data['nav'])
                self.logger.info(f"Successfully fetched NAV from mftool for {scheme_name}: ₹{nav_value:.2f}")
                return nav_value
            else:
                self.logger.warning(f"No NAV data found in mftool response for {scheme_name}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching NAV from mftool for {scheme_name}: {e}")
            return None

    def get_mf_nav_from_direct_api(self, scheme_name: str) -> Optional[float]:
        """Get mutual fund NAV using direct AMFI API"""
        try:
            self.logger.debug(f"Fetching NAV from direct AMFI API for scheme: {scheme_name}")

            # Rate limiting for AMFI API
            self._rate_limit()

            # AMFI NAV data URL
            amfi_url = "https://www.amfiindia.com/spages/NAVAll.txt"

            # Fetch data with timeout
            response = requests.get(amfi_url, timeout=10)
            response.raise_for_status()

            # Parse the data
            lines = response.text.strip().split('\n')
            scheme_name_lower = scheme_name.lower()

            for line in lines:
                if ';' in line:
                    parts = line.split(';')
                    if len(parts) >= 5:
                        scheme_code = parts[0].strip()
                        scheme_full_name = parts[3].strip()
                        nav_str = parts[4].strip()

                        # Check if this is the scheme we're looking for
                        if scheme_name_lower in scheme_full_name.lower():
                            try:
                                nav_value = float(nav_str)
                                self.logger.info(f"Successfully fetched NAV from direct AMFI API for {scheme_name}: ₹{nav_value:.2f}")
                                return nav_value
                            except ValueError:
                                continue

            self.logger.warning(f"No matching scheme found in AMFI data for: {scheme_name}")
            return None

        except Exception as e:
            self.logger.error(f"Error fetching NAV from direct AMFI API for {scheme_name}: {e}")
            return None

    def get_cache_info(self) -> Dict[str, any]:
        """Get information about the current cache state"""
        valid_entries = sum(1 for symbol in self.cache.keys() if self._is_cache_valid(symbol))
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries,
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60
        }

    def get_symbol_mapping_info(self, symbol: str) -> Dict[str, any]:
        """Get information about symbol mapping for debugging"""
        normalized = self._normalize_symbol(symbol)
        has_status = symbol in self.symbol_status
        status_info = self.symbol_status.get(symbol, 'No status information available')
        has_mf_mapping = symbol in self.mutual_fund_mappings
        mf_scheme_name = self.mutual_fund_mappings.get(symbol, None)

        return {
            'original_symbol': symbol,
            'normalized_symbol': normalized,
            'has_direct_mapping': symbol in self.symbol_mappings,
            'direct_mapping': self.symbol_mappings.get(symbol),
            'has_mutual_fund_mapping': has_mf_mapping,
            'mutual_fund_scheme_name': mf_scheme_name,
            'has_status_info': has_status,
            'status_info': status_info,
            'is_cached': self._is_cache_valid(symbol),
            'cached_price': self.cache.get(symbol) if self._is_cache_valid(symbol) else None,
            'data_sources': self._get_available_data_sources(symbol)
        }

    def _get_available_data_sources(self, symbol: str) -> List[str]:
        """Get list of available data sources for a symbol"""
        sources = []

        if symbol in self.symbol_mappings:
            sources.append("Yahoo Finance")

        if symbol in self.mutual_fund_mappings:
            if self.MFTOOL_AVAILABLE:
                sources.append("mftool (AMFI)")
            sources.append("Direct AMFI API")

        if not sources:
            sources.append("None available")

        return sources

    def _try_intelligent_mf_matching(self, symbol: str) -> Optional[float]:
        """Try to intelligently match mutual fund symbols to AMFI scheme names"""
        if not self.MFTOOL_AVAILABLE:
            return None

        # Generate possible scheme name variations based on symbol
        possible_names = self._generate_scheme_name_variations(symbol)

        for scheme_name in possible_names:
            self.logger.debug(f"Trying scheme name variation: {scheme_name}")
            price = self.get_mf_nav_from_mftool(scheme_name)
            if price is not None:
                # Cache the result and add to mappings for future use
                self.cache[symbol] = price
                self.cache_expiry[symbol] = datetime.now() + self.cache_duration
                self.mutual_fund_mappings[symbol] = scheme_name  # Add successful mapping
                self.logger.info(f"✅ Found matching scheme for {symbol}: {scheme_name} (₹{price:.2f})")
                return price

        return None

    def _generate_scheme_name_variations(self, symbol: str) -> List[str]:
        """Generate possible AMFI scheme name variations from symbol"""
        variations = []

        # Common mutual fund name patterns
        name_mappings = {
            'AXIS_BLUE_FUND': ['Axis Bluechip Fund', 'Axis Blue Chip Fund', 'Axis Bluechip'],
            'AXIS_ELSS': ['Axis Long Term Equity Fund', 'Axis ELSS Fund'],
            'KOTAK_FLEX_CAP': ['Kotak Flexicap Fund', 'Kotak Flexi Cap Fund'],
            'KOTAK_CORP_BOND': ['Kotak Corporate Bond Fund'],
            'MOTILAL_NASDAQ': ['Motilal Oswal Nasdaq 100 Fund', 'Motilal Oswal NASDAQ 100 FOF'],
            'MOTILAL_SP_500': ['Motilal Oswal S&P 500 Index Fund', 'Motilal Oswal S&P 500 FOF'],
            'NAVI_NIFTY_50': ['Navi Nifty 50 Index Fund'],
            'NAVI_NIFT_MDCP': ['Navi Nifty Midcap 150 Index Fund', 'Navi Midcap 150 Index Fund'],
            'EDEL_BANK_PSU': ['Edelweiss Banking and PSU Debt Fund'],
        }

        # Find matching base name
        for base_name, fund_names in name_mappings.items():
            if base_name in symbol:
                for fund_name in fund_names:
                    # Add common plan and option variations
                    variations.extend([
                        f"{fund_name} - Direct Plan - Growth Option",
                        f"{fund_name} - Direct Plan - Growth",
                        f"{fund_name} - Regular Plan - Growth Option",
                        f"{fund_name} - Regular Plan - Growth",
                        f"{fund_name} - Growth Option",
                        f"{fund_name} - Growth",
                        fund_name,
                    ])
                break

        return variations

    def validate_symbols(self, symbols: List[str]) -> Dict[str, Dict[str, any]]:
        """Validate a list of symbols and return mapping information"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_symbol_mapping_info(symbol)
        return results

    def get_detailed_investment_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive investment data including historical prices, financials, etc."""
        if not symbol:
            return {}

        # Check detailed cache first
        cache_key = f"detailed_{symbol}"
        if self._is_detailed_cache_valid(cache_key):
            self.logger.debug(f"Using cached detailed data for {symbol}")
            return self.detailed_cache[cache_key]

        detailed_data = {
            'symbol': symbol,
            'real_time_data': self._get_real_time_data(symbol),
            'historical_data': self._get_historical_data(symbol),
            'performance_data': self._get_performance_data(symbol),
            'financial_data': self._get_financial_data(symbol),
            'portfolio_data': self._get_portfolio_data(symbol),
            'regulatory_data': self._get_regulatory_data(symbol),
            'dividend_data': self._get_dividend_data(symbol),
            'fees_data': self._get_fees_data(symbol),
            'last_updated': datetime.now()
        }

        # Cache the detailed data
        self.detailed_cache[cache_key] = detailed_data
        self.detailed_cache_expiry[cache_key] = datetime.now() + self.detailed_cache_duration

        return detailed_data

    def _is_detailed_cache_valid(self, cache_key: str) -> bool:
        """Check if detailed cache entry is still valid"""
        return (cache_key in self.detailed_cache and
                cache_key in self.detailed_cache_expiry and
                datetime.now() < self.detailed_cache_expiry[cache_key])

    def _get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Get real-time price and NAV data"""
        try:
            if not symbol:
                return {'available': False, 'error': 'Empty or None symbol provided'}

            if not YFINANCE_AVAILABLE:
                return {'available': False, 'error': 'Yahoo Finance not available'}

            # ✅ FIX: Use analysis symbol for consistent data fetching
            analysis_symbol = self._get_analysis_symbol(symbol)
            self.logger.debug(f"🔍 Fetching real-time data for {symbol} (analysis symbol: {analysis_symbol})")

            # Add note if using proxy symbol
            proxy_note = ""
            if analysis_symbol != symbol and symbol in self.mutual_fund_mappings:
                proxy_note = f" (using {analysis_symbol} as market proxy for analysis)"

            ticker = yf.Ticker(analysis_symbol)

            # Get ticker info with error handling
            try:
                info = ticker.info
            except Exception as info_error:
                self.logger.warning(f"⚠️ Error getting ticker info for {analysis_symbol}: {info_error}")
                return {'available': False, 'error': f'Ticker info error: {info_error}{proxy_note}'}

            if not info:
                self.logger.warning(f"⚠️ No info data returned for {analysis_symbol}")
                return {'available': False, 'error': f'No ticker info available{proxy_note}'}

            # Check for price data with multiple fallbacks
            current_price = (
                info.get('regularMarketPrice') or
                info.get('currentPrice') or
                info.get('navPrice') or
                info.get('previousClose') or
                info.get('bid') or
                info.get('ask')
            )

            if current_price is None:
                self.logger.warning(f"⚠️ No price data found in ticker info for {analysis_symbol}")
                available_keys = [k for k in info.keys() if 'price' in k.lower() or 'nav' in k.lower()]
                self.logger.debug(f"Price-related keys available: {available_keys}")
                return {'available': False, 'error': f'No price data in ticker info{proxy_note}'}

            result = {
                'available': True,
                'current_price': current_price,
                'nav': info.get('navPrice', current_price),
                'previous_close': info.get('previousClose'),
                'open': info.get('open') or info.get('regularMarketOpen'),
                'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
                'day_low': info.get('dayLow') or info.get('regularMarketDayLow'),
                'volume': info.get('volume') or info.get('regularMarketVolume'),
                'market_cap': info.get('marketCap'),
                'currency': info.get('currency', 'INR'),
                'symbol_used': analysis_symbol,
                'last_updated': datetime.now()
            }

            self.logger.debug(f"✅ Successfully fetched real-time data for {symbol}: ₹{current_price}")
            return result

        except Exception as e:
            self.logger.error(f"❌ Error fetching real-time data for {symbol}: {e}")
            return {'available': False, 'error': str(e)}

    def _get_historical_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """Get historical price data"""
        try:
            if not symbol:
                return {'available': False, 'error': 'Empty or None symbol provided'}

            if not YFINANCE_AVAILABLE:
                return {'available': False, 'error': 'Yahoo Finance not available'}

            # ✅ FIX: Use analysis symbol for consistent data fetching
            analysis_symbol = self._get_analysis_symbol(symbol)
            self.logger.debug(f"🔍 Fetching historical data for {symbol} (analysis symbol: {analysis_symbol})")

            ticker = yf.Ticker(analysis_symbol)
            hist = ticker.history(period=period)

            if hist.empty:
                return {'available': False, 'error': 'No historical data found'}

            # Convert to list of dictionaries for easier handling
            historical_data = []
            for date, row in hist.iterrows():
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']) if not pd.isna(row['Volume']) else 0,
                    'change': 0.0,  # Will be calculated
                    'change_percent': 0.0  # Will be calculated
                })

            # Calculate changes
            for i in range(1, len(historical_data)):
                prev_close = historical_data[i-1]['close']
                curr_close = historical_data[i]['close']
                change = curr_close - prev_close
                change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
                historical_data[i]['change'] = change
                historical_data[i]['change_percent'] = change_percent

            return {
                'available': True,
                'data': historical_data,
                'period': period,
                'total_records': len(historical_data)
            }
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return {'available': False, 'error': str(e)}

    def _get_performance_data(self, symbol: str) -> Dict[str, Any]:
        """Get performance metrics and charts data"""
        try:
            if not symbol:
                return {'available': False, 'error': 'Empty or None symbol provided'}

            if not YFINANCE_AVAILABLE:
                return {'available': False, 'error': 'Yahoo Finance not available'}

            # ✅ FIX: Use analysis symbol for consistent data fetching
            analysis_symbol = self._get_analysis_symbol(symbol)
            self.logger.debug(f"🔍 Fetching performance data for {symbol} (analysis symbol: {analysis_symbol})")

            ticker = yf.Ticker(analysis_symbol)
            info = ticker.info

            return {
                'available': True,
                'beta': info.get('beta'),
                'trailing_pe': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'price_to_book': info.get('priceToBook'),
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                'profit_margins': info.get('profitMargins'),
                'operating_margins': info.get('operatingMargins'),
                'earnings_growth': info.get('earningsGrowth'),
                'revenue_growth': info.get('revenueGrowth'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'moving_avg_50': info.get('fiftyDayAverage'),
                'moving_avg_200': info.get('twoHundredDayAverage')
            }
        except Exception as e:
            self.logger.error(f"Error fetching performance data for {symbol}: {e}")
            return {'available': False, 'error': str(e)}

    def _get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """Get financial data for stocks"""
        try:
            if not symbol:
                return {'available': False, 'error': 'Empty or None symbol provided'}

            if not YFINANCE_AVAILABLE:
                return {'available': False, 'error': 'Yahoo Finance not available'}

            # ✅ FIX: Use analysis symbol for consistent data fetching
            analysis_symbol = self._get_analysis_symbol(symbol)
            self.logger.debug(f"🔍 Fetching financial data for {symbol} (analysis symbol: {analysis_symbol})")

            ticker = yf.Ticker(analysis_symbol)
            info = ticker.info

            # Check if this is a stock (has financial data) or mutual fund
            is_stock = info.get('quoteType') == 'EQUITY'

            if not is_stock:
                return {'available': False, 'reason': 'Financial data not applicable for mutual funds'}

            return {
                'available': True,
                'total_revenue': info.get('totalRevenue'),
                'gross_profits': info.get('grossProfits'),
                'ebitda': info.get('ebitda'),
                'net_income': info.get('netIncomeToCommon'),
                'total_cash': info.get('totalCash'),
                'total_debt': info.get('totalDebt'),
                'book_value': info.get('bookValue'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'enterprise_value': info.get('enterpriseValue'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'enterprise_to_revenue': info.get('enterpriseToRevenue'),
                'enterprise_to_ebitda': info.get('enterpriseToEbitda'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio')
            }
        except Exception as e:
            self.logger.error(f"Error fetching financial data for {symbol}: {e}")
            return {'available': False, 'error': str(e)}

    def _get_portfolio_data(self, symbol: str) -> Dict[str, Any]:
        """Get portfolio composition data (stocks only)"""
        try:
            if not symbol:
                return {'available': False, 'error': 'Empty or None symbol provided'}

            if not YFINANCE_AVAILABLE:
                return {'available': False, 'error': 'Yahoo Finance not available'}

            # ✅ FIX: Use analysis symbol for consistent data fetching
            analysis_symbol = self._get_analysis_symbol(symbol)
            self.logger.debug(f"🔍 Fetching portfolio data for {symbol} (analysis symbol: {analysis_symbol})")

            ticker = yf.Ticker(analysis_symbol)
            info = ticker.info

            # Check if this is a stock
            is_stock = info.get('quoteType') == 'EQUITY'

            if not is_stock:
                return {'available': False, 'reason': 'Portfolio data only applicable for stocks'}

            return {
                'available': True,
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'full_time_employees': info.get('fullTimeEmployees'),
                'business_summary': info.get('longBusinessSummary'),
                'website': info.get('website'),
                'headquarters': {
                    'city': info.get('city'),
                    'state': info.get('state'),
                    'country': info.get('country')
                }
            }
        except Exception as e:
            self.logger.error(f"Error fetching portfolio data for {symbol}: {e}")
            return {'available': False, 'error': str(e)}

    def _get_regulatory_data(self, symbol: str) -> Dict[str, Any]:
        """Get regulatory filings and documents"""
        try:
            # For now, return placeholder data as regulatory data requires specialized APIs
            return {
                'available': True,
                'sec_filings': [],
                'annual_reports': [],
                'quarterly_reports': [],
                'note': 'Regulatory data integration pending - requires specialized financial data APIs'
            }
        except Exception as e:
            self.logger.error(f"Error fetching regulatory data for {symbol}: {e}")
            return {'available': False, 'error': str(e)}

    def _get_dividend_data(self, symbol: str) -> Dict[str, Any]:
        """Get dividend history and payment information"""
        try:
            if not symbol:
                return {'available': False, 'error': 'Empty or None symbol provided'}

            if not YFINANCE_AVAILABLE:
                return {'available': False, 'error': 'Yahoo Finance not available'}

            # ✅ FIX: Use analysis symbol for consistent data fetching
            analysis_symbol = self._get_analysis_symbol(symbol)
            self.logger.debug(f"🔍 Fetching dividend data for {symbol} (analysis symbol: {analysis_symbol})")

            ticker = yf.Ticker(analysis_symbol)

            # Get dividend data
            dividends = ticker.dividends
            info = ticker.info

            if dividends.empty:
                return {'available': True, 'dividends': [], 'dividend_yield': 0.0}

            # Convert to list of dictionaries
            dividend_history = []
            for date, amount in dividends.items():
                dividend_history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'amount': float(amount)
                })

            return {
                'available': True,
                'dividends': dividend_history[-20:],  # Last 20 dividends
                'dividend_yield': info.get('dividendYield', 0.0),
                'dividend_rate': info.get('dividendRate', 0.0),
                'payout_ratio': info.get('payoutRatio', 0.0),
                'ex_dividend_date': info.get('exDividendDate'),
                'total_records': len(dividend_history)
            }
        except Exception as e:
            self.logger.error(f"Error fetching dividend data for {symbol}: {e}")
            return {'available': False, 'error': str(e)}

    def _get_fees_data(self, symbol: str) -> Dict[str, Any]:
        """Get expense ratio and fee structure (mutual funds only)"""
        try:
            if not symbol:
                return {'available': False, 'error': 'Empty or None symbol provided'}

            if not YFINANCE_AVAILABLE:
                return {'available': False, 'error': 'Yahoo Finance not available'}

            # ✅ FIX: Use analysis symbol for consistent data fetching
            analysis_symbol = self._get_analysis_symbol(symbol)
            self.logger.debug(f"🔍 Fetching fees data for {symbol} (analysis symbol: {analysis_symbol})")

            ticker = yf.Ticker(analysis_symbol)
            info = ticker.info

            # Check if this is a mutual fund
            is_mutual_fund = info.get('quoteType') in ['MUTUALFUND', 'ETF']

            if not is_mutual_fund:
                return {'available': False, 'reason': 'Fee data only applicable for mutual funds'}

            return {
                'available': True,
                'expense_ratio': info.get('annualReportExpenseRatio'),
                'management_fee': info.get('managementFee'),
                'front_end_load': info.get('frontEndLoad'),
                'back_end_load': info.get('backEndLoad'),
                'annual_holdings_turnover': info.get('annualHoldingsTurnover'),
                'fund_family': info.get('fundFamily'),
                'category': info.get('category')
            }
        except Exception as e:
            self.logger.error(f"Error fetching fees data for {symbol}: {e}")
            return {'available': False, 'error': str(e)}


# Global instance
price_fetcher = PriceFetcher()
