"""
AMFI (Association of Mutual Funds in India) Direct API Integration
Provides authoritative source for Indian mutual fund NAV data
"""

import logging
import requests
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import pandas as pd
import re


class AMFIDataFetcher:
    """Fetches and processes data from AMFI's official NAV API"""

    def __init__(self, cache_dir: str = "data/investments/amfi_cache"):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # AMFI API endpoints (semicolon-delimited format)
        self.nav_url = "https://www.amfiindia.com/spages/NAVAll.txt"
        self.backup_nav_url = "https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?tp=1"
        
        # Cache settings
        self.cache_file = self.cache_dir / "amfi_nav_data.csv"
        self.cache_duration = timedelta(hours=6)  # Cache for 6 hours
        
        # Data processing
        self.scheme_data = {}
        self.last_update = None
        
        self.logger.info("✅ AMFI Data Fetcher initialized")

    def fetch_nav_data(self, force_refresh: bool = False) -> bool:
        """Fetch NAV data from AMFI API"""
        try:
            # Check if we need to fetch fresh data
            if not force_refresh and self._is_cache_valid():
                self.logger.debug("📦 Using cached AMFI data")
                return self._load_from_cache()
            
            self.logger.info("🌐 Fetching fresh NAV data from AMFI...")
            
            # Try primary endpoint first
            success = self._fetch_from_endpoint(self.nav_url)
            
            if not success:
                self.logger.warning("⚠️ Primary AMFI endpoint failed, trying backup...")
                success = self._fetch_from_endpoint(self.backup_nav_url)
            
            if success:
                self._save_to_cache()
                self.logger.info(f"✅ Successfully fetched {len(self.scheme_data)} mutual fund schemes from AMFI")
                return True
            else:
                self.logger.error("❌ All AMFI endpoints failed")
                # Try to load from cache as fallback
                return self._load_from_cache()
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching AMFI data: {e}")
            return self._load_from_cache()

    def _fetch_from_endpoint(self, url: str) -> bool:
        """Fetch data from a specific AMFI endpoint"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/plain, text/html, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse the pipe-delimited data
            return self._parse_nav_data(response.text)
            
        except requests.RequestException as e:
            self.logger.error(f"❌ Request failed for {url}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error processing data from {url}: {e}")
            return False

    def _parse_nav_data(self, data_text: str) -> bool:
        """Parse AMFI NAV data from semicolon-delimited format"""
        try:
            self.scheme_data = {}
            lines = data_text.strip().split('\n')
            
            current_amc = ""
            parsed_count = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip header and footer lines
                if line.startswith('Scheme Code') or line.startswith('Total'):
                    continue
                
                # AMC name lines (no semicolon separator)
                if ';' not in line:
                    current_amc = line.strip()
                    continue

                # Parse scheme data (semicolon-delimited)
                parts = line.split(';')
                if len(parts) >= 6:
                    try:
                        scheme_code = parts[0].strip()
                        isin_div_payout = parts[1].strip()
                        isin_div_reinvest = parts[2].strip()
                        scheme_name = parts[3].strip()
                        nav = parts[4].strip()
                        date = parts[5].strip()
                        
                        # Skip if NAV is not available
                        if nav in ['N.A.', 'NA', '', '-']:
                            continue
                        
                        # Convert NAV to float
                        nav_value = float(nav)
                        
                        # Parse date
                        nav_date = datetime.strptime(date, '%d-%b-%Y').date()
                        
                        # Store scheme data
                        self.scheme_data[scheme_code] = {
                            'scheme_code': scheme_code,
                            'scheme_name': scheme_name,
                            'amc_name': current_amc,
                            'nav': nav_value,
                            'nav_date': nav_date.isoformat(),
                            'isin_div_payout': isin_div_payout,
                            'isin_div_reinvest': isin_div_reinvest,
                            'last_updated': datetime.now().isoformat()
                        }
                        
                        parsed_count += 1
                        
                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"⚠️ Skipping invalid line: {line[:50]}... Error: {e}")
                        continue
            
            self.last_update = datetime.now()
            self.logger.info(f"✅ Parsed {parsed_count} mutual fund schemes from AMFI data")
            return parsed_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ Error parsing AMFI data: {e}")
            return False

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.cache_file.exists():
            return False
        
        try:
            cache_age = datetime.now() - datetime.fromtimestamp(self.cache_file.stat().st_mtime)
            return cache_age < self.cache_duration
        except Exception:
            return False

    def _save_to_cache(self) -> bool:
        """Save current scheme data to cache"""
        try:
            if not self.scheme_data:
                return False
            
            # Convert to DataFrame for easy CSV handling
            df = pd.DataFrame.from_dict(self.scheme_data, orient='index')
            df.to_csv(self.cache_file, index=False)
            
            self.logger.debug(f"💾 Saved {len(self.scheme_data)} schemes to cache")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error saving to cache: {e}")
            return False

    def _load_from_cache(self) -> bool:
        """Load scheme data from cache"""
        try:
            if not self.cache_file.exists():
                return False
            
            df = pd.read_csv(self.cache_file)
            self.scheme_data = {}
            
            for _, row in df.iterrows():
                scheme_code = str(row['scheme_code'])
                self.scheme_data[scheme_code] = {
                    'scheme_code': scheme_code,
                    'scheme_name': row['scheme_name'],
                    'amc_name': row['amc_name'],
                    'nav': float(row['nav']),
                    'nav_date': row['nav_date'],
                    'isin_div_payout': row.get('isin_div_payout', ''),
                    'isin_div_reinvest': row.get('isin_div_reinvest', ''),
                    'last_updated': row['last_updated']
                }
            
            self.last_update = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
            self.logger.info(f"📦 Loaded {len(self.scheme_data)} schemes from cache")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error loading from cache: {e}")
            return False

    def search_scheme_by_name(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for mutual fund schemes by name"""
        if not self.scheme_data:
            self.fetch_nav_data()
        
        name_lower = name.lower()
        matches = []
        
        for scheme_code, scheme_info in self.scheme_data.items():
            scheme_name_lower = scheme_info['scheme_name'].lower()
            
            # Exact match gets highest priority
            if name_lower == scheme_name_lower:
                matches.insert(0, scheme_info)
            # Contains match
            elif name_lower in scheme_name_lower:
                matches.append(scheme_info)
            # Word match
            elif any(word in scheme_name_lower for word in name_lower.split()):
                matches.append(scheme_info)
        
        return matches[:limit]

    def get_scheme_by_code(self, scheme_code: str) -> Optional[Dict[str, Any]]:
        """Get scheme data by AMFI scheme code"""
        if not self.scheme_data:
            self.fetch_nav_data()
        
        return self.scheme_data.get(str(scheme_code))

    def get_nav_data(self, symbol: str) -> Dict[str, Any]:
        """Get NAV data for a symbol (try multiple matching strategies)"""
        try:
            if not self.scheme_data:
                if not self.fetch_nav_data():
                    return {'available': False, 'error': 'Failed to fetch AMFI data', 'source': 'AMFI'}
            
            # Strategy 1: Direct scheme code match
            scheme_data = self.get_scheme_by_code(symbol)
            if scheme_data:
                return self._format_nav_response(scheme_data)
            
            # Strategy 2: Search by name
            matches = self.search_scheme_by_name(symbol, limit=1)
            if matches:
                return self._format_nav_response(matches[0])
            
            # Strategy 3: Fuzzy matching for common patterns
            normalized_symbol = self._normalize_symbol(symbol)
            for scheme_code, scheme_info in self.scheme_data.items():
                normalized_scheme = self._normalize_symbol(scheme_info['scheme_name'])
                if normalized_symbol in normalized_scheme or normalized_scheme in normalized_symbol:
                    return self._format_nav_response(scheme_info)
            
            return {
                'available': False, 
                'error': f'No AMFI data found for symbol: {symbol}',
                'source': 'AMFI',
                'searched_schemes': len(self.scheme_data)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting NAV data for {symbol}: {e}")
            return {'available': False, 'error': str(e), 'source': 'AMFI'}

    def _format_nav_response(self, scheme_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format scheme data into standard response format"""
        return {
            'available': True,
            'source': 'AMFI',
            'current_price': scheme_data['nav'],
            'nav': scheme_data['nav'],
            'scheme_name': scheme_data['scheme_name'],
            'scheme_code': scheme_data['scheme_code'],
            'amc_name': scheme_data['amc_name'],
            'nav_date': scheme_data['nav_date'],
            'currency': 'INR',
            'last_updated': scheme_data['last_updated'],
            'data_freshness': self._get_data_age(scheme_data['nav_date'])
        }

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for better matching"""
        # Remove common suffixes and normalize
        normalized = re.sub(r'\.(NS|BO|BSE|NSE)$', '', symbol.upper())
        normalized = re.sub(r'[^A-Z0-9]', '', normalized)
        return normalized

    def _get_data_age(self, nav_date_str: str) -> str:
        """Get human-readable data age"""
        try:
            nav_date = datetime.fromisoformat(nav_date_str).date()
            today = datetime.now().date()
            age_days = (today - nav_date).days
            
            if age_days == 0:
                return "Today"
            elif age_days == 1:
                return "1 day old"
            else:
                return f"{age_days} days old"
        except:
            return "Unknown age"

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about cached AMFI data"""
        if not self.scheme_data:
            self.fetch_nav_data()
        
        amc_count = len(set(scheme['amc_name'] for scheme in self.scheme_data.values()))
        
        return {
            'total_schemes': len(self.scheme_data),
            'total_amcs': amc_count,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'cache_valid': self._is_cache_valid(),
            'data_source': 'AMFI Official API'
        }


# Global instance
amfi_fetcher = AMFIDataFetcher()
