"""
Intelligent Symbol Recognition System
Automatically detects symbol types and routes them to appropriate data sources
"""

import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


class SymbolType(Enum):
    """Types of investment symbols"""
    INDIAN_STOCK = "indian_stock"
    INDIAN_MUTUAL_FUND = "indian_mutual_fund"
    INDIAN_ETF = "indian_etf"
    INTERNATIONAL_STOCK = "international_stock"
    INTERNATIONAL_ETF = "international_etf"
    INTERNATIONAL_MUTUAL_FUND = "international_mutual_fund"
    UNKNOWN = "unknown"


class DataSource(Enum):
    """Available data sources"""
    YAHOO_FINANCE = "yahoo_finance"
    AMFI_DIRECT = "amfi_direct"
    MFTOOL = "mftool"
    UNKNOWN = "unknown"


@dataclass
class SymbolInfo:
    """Information about a recognized symbol"""
    original_symbol: str
    normalized_symbol: str
    symbol_type: SymbolType
    primary_source: DataSource
    fallback_sources: List[DataSource]
    exchange: Optional[str] = None
    country: str = "IN"  # Default to India
    confidence: float = 1.0  # Confidence in recognition (0.0 to 1.0)
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SymbolRecognizer:
    """Intelligent symbol recognition and routing system"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Indian stock exchange patterns
        self.indian_stock_patterns = [
            r'^[A-Z0-9&]+\.(NS|NSE)$',  # NSE stocks: RELIANCE.NS
            r'^[A-Z0-9&]+\.(BO|BSE)$',  # BSE stocks: RELIANCE.BO
            r'^[A-Z0-9&]+$',            # Plain symbols that might be Indian stocks
        ]
        
        # Indian ETF patterns
        self.indian_etf_patterns = [
            r'^[A-Z]*BEES\.(NS|BO)$',   # NIFTYBEES.NS, GOLDBEES.NS
            r'^[A-Z]*ETF\.(NS|BO)$',    # Various ETFs
            r'^LIQUID[A-Z]*\.(NS|BO)$', # Liquid ETFs
        ]
        
        # International stock patterns
        self.international_stock_patterns = [
            r'^[A-Z]{1,5}$',            # US stocks: AAPL, GOOGL, MSFT
            r'^[A-Z]+\.[A-Z]{1,3}$',    # International with exchange: ASML.AS
        ]
        
        # Mutual fund patterns (Indian)
        self.indian_mf_patterns = [
            r'^[0-9]{6}$',              # AMFI scheme codes: 120503
            r'^0P[0-9A-Z]{8}\.(BO|NS)$', # Yahoo Finance MF identifiers: 0P0000XVU8.BO
            r'^[A-Z0-9_\-\s]+FUND',     # Contains "FUND"
            r'^[A-Z0-9_\-\s]+MF',       # Contains "MF"
            r'^HDFC[A-Z0-9_\-\s]*',     # HDFC mutual funds
            r'^ICICI[A-Z0-9_\-\s]*',    # ICICI mutual funds
            r'^SBI[A-Z0-9_\-\s]*',      # SBI mutual funds
            r'^AXIS[A-Z0-9_\-\s]*',     # Axis mutual funds
            r'^KOTAK[A-Z0-9_\-\s]*',    # Kotak mutual funds
        ]
        
        # Known AMC (Asset Management Company) prefixes
        self.amc_prefixes = {
            'HDFC', 'ICICI', 'SBI', 'AXIS', 'KOTAK', 'RELIANCE', 'BIRLA', 'FRANKLIN',
            'DSP', 'INVESCO', 'NIPPON', 'UTI', 'TATA', 'MIRAE', 'CANARA', 'UNION',
            'MAHINDRA', 'PRINCIPAL', 'QUANTUM', 'SUNDARAM', 'EDELWEISS', 'BARODA'
        }
        
        # Known international exchanges
        self.international_exchanges = {
            'NASDAQ', 'NYSE', 'LSE', 'TSE', 'ASX', 'HKEX', 'SSE', 'SZSE',
            'AS', 'PA', 'DE', 'L', 'T', 'AX', 'HK', 'SS', 'SZ'
        }

    def recognize_symbol(self, symbol: str) -> SymbolInfo:
        """Recognize symbol type and determine appropriate data sources"""
        try:
            original_symbol = symbol.strip()
            normalized_symbol = self._normalize_symbol(original_symbol)

            # Try different recognition strategies in priority order
            # Check mutual funds first to catch Yahoo Finance MF identifiers
            symbol_info = (
                self._recognize_indian_mutual_fund(original_symbol, normalized_symbol) or
                self._recognize_indian_stock(original_symbol, normalized_symbol) or
                self._recognize_indian_etf(original_symbol, normalized_symbol) or
                self._recognize_international_stock(original_symbol, normalized_symbol) or
                self._recognize_international_etf(original_symbol, normalized_symbol) or
                self._create_unknown_symbol_info(original_symbol, normalized_symbol)
            )
            
            self.logger.debug(f"🔍 Recognized '{original_symbol}' as {symbol_info.symbol_type.value} "
                            f"(confidence: {symbol_info.confidence:.2f})")
            
            return symbol_info
            
        except Exception as e:
            self.logger.error(f"❌ Error recognizing symbol '{symbol}': {e}")
            return self._create_unknown_symbol_info(symbol, symbol)

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for processing"""
        # Remove extra whitespace and convert to uppercase
        normalized = symbol.strip().upper()
        
        # Handle common variations
        normalized = normalized.replace(' ', '_')
        normalized = re.sub(r'[^\w\.\-]', '', normalized)
        
        return normalized

    def _recognize_indian_stock(self, original: str, normalized: str) -> Optional[SymbolInfo]:
        """Recognize Indian stock symbols"""
        for pattern in self.indian_stock_patterns:
            if re.match(pattern, normalized):
                exchange = None
                if '.NS' in normalized or '.NSE' in normalized:
                    exchange = 'NSE'
                elif '.BO' in normalized or '.BSE' in normalized:
                    exchange = 'BSE'
                
                # Ensure proper Yahoo Finance format
                yahoo_symbol = normalized
                if not yahoo_symbol.endswith(('.NS', '.BO')):
                    yahoo_symbol += '.NS'  # Default to NSE
                
                return SymbolInfo(
                    original_symbol=original,
                    normalized_symbol=yahoo_symbol,
                    symbol_type=SymbolType.INDIAN_STOCK,
                    primary_source=DataSource.YAHOO_FINANCE,
                    fallback_sources=[],
                    exchange=exchange,
                    country="IN",
                    confidence=0.9 if exchange else 0.7,
                    metadata={'yahoo_symbol': yahoo_symbol}
                )
        
        return None

    def _recognize_indian_etf(self, original: str, normalized: str) -> Optional[SymbolInfo]:
        """Recognize Indian ETF symbols"""
        for pattern in self.indian_etf_patterns:
            if re.match(pattern, normalized):
                # Ensure proper Yahoo Finance format
                yahoo_symbol = normalized
                if not yahoo_symbol.endswith(('.NS', '.BO')):
                    yahoo_symbol += '.NS'  # Default to NSE for ETFs
                
                return SymbolInfo(
                    original_symbol=original,
                    normalized_symbol=yahoo_symbol,
                    symbol_type=SymbolType.INDIAN_ETF,
                    primary_source=DataSource.YAHOO_FINANCE,
                    fallback_sources=[],
                    exchange='NSE',
                    country="IN",
                    confidence=0.95,
                    metadata={'yahoo_symbol': yahoo_symbol}
                )
        
        return None

    def _recognize_indian_mutual_fund(self, original: str, normalized: str) -> Optional[SymbolInfo]:
        """Recognize Indian mutual fund symbols"""
        confidence = 0.5
        primary_source = DataSource.AMFI_DIRECT
        fallback_sources = [DataSource.MFTOOL, DataSource.YAHOO_FINANCE]

        # Check for Yahoo Finance mutual fund identifier (0P format)
        if re.match(r'^0P[0-9A-Z]{8}\.(BO|NS)$', normalized):
            confidence = 0.95
            primary_source = DataSource.YAHOO_FINANCE  # Yahoo Finance is primary for these
            fallback_sources = [DataSource.AMFI_DIRECT, DataSource.MFTOOL]

        # Check for AMFI scheme code (6 digits)
        elif re.match(r'^[0-9]{6}$', normalized):
            confidence = 0.95

        # Check for mutual fund patterns
        elif any(re.search(pattern, normalized) for pattern in self.indian_mf_patterns):
            confidence = 0.8

        # Check for AMC prefixes
        elif any(normalized.startswith(prefix) for prefix in self.amc_prefixes):
            confidence = 0.7

        # Check for fund-related keywords
        elif any(keyword in normalized for keyword in ['FUND', 'MF', 'MUTUAL', 'SCHEME']):
            confidence = 0.6

        else:
            return None

        return SymbolInfo(
            original_symbol=original,
            normalized_symbol=normalized,
            symbol_type=SymbolType.INDIAN_MUTUAL_FUND,
            primary_source=primary_source,
            fallback_sources=fallback_sources,
            country="IN",
            confidence=confidence,
            metadata={
                'is_amfi_code': re.match(r'^[0-9]{6}$', normalized) is not None,
                'is_yahoo_mf_id': re.match(r'^0P[0-9A-Z]{8}\.(BO|NS)$', normalized) is not None,
                'yahoo_symbol': normalized if re.match(r'^0P[0-9A-Z]{8}\.(BO|NS)$', normalized) else None
            }
        )

    def _recognize_international_stock(self, original: str, normalized: str) -> Optional[SymbolInfo]:
        """Recognize international stock symbols"""
        # US stocks (1-5 letters, no dots)
        if re.match(r'^[A-Z]{1,5}$', normalized):
            return SymbolInfo(
                original_symbol=original,
                normalized_symbol=normalized,
                symbol_type=SymbolType.INTERNATIONAL_STOCK,
                primary_source=DataSource.YAHOO_FINANCE,
                fallback_sources=[],
                country="US",
                confidence=0.8,
                metadata={'market': 'US'}
            )
        
        # International stocks with exchange suffix
        if re.match(r'^[A-Z]+\.[A-Z]{1,3}$', normalized):
            parts = normalized.split('.')
            exchange_suffix = parts[1]
            
            if exchange_suffix in self.international_exchanges:
                country = self._get_country_from_exchange(exchange_suffix)
                return SymbolInfo(
                    original_symbol=original,
                    normalized_symbol=normalized,
                    symbol_type=SymbolType.INTERNATIONAL_STOCK,
                    primary_source=DataSource.YAHOO_FINANCE,
                    fallback_sources=[],
                    exchange=exchange_suffix,
                    country=country,
                    confidence=0.9,
                    metadata={'market': country}
                )
        
        return None

    def _recognize_international_etf(self, original: str, normalized: str) -> Optional[SymbolInfo]:
        """Recognize international ETF symbols"""
        # Common ETF patterns
        etf_indicators = ['ETF', 'SPDR', 'ISHARES', 'VANGUARD', 'QQQ', 'SPY', 'IVV', 'VTI']
        
        if any(indicator in normalized for indicator in etf_indicators):
            return SymbolInfo(
                original_symbol=original,
                normalized_symbol=normalized,
                symbol_type=SymbolType.INTERNATIONAL_ETF,
                primary_source=DataSource.YAHOO_FINANCE,
                fallback_sources=[],
                country="US",  # Most ETFs are US-based
                confidence=0.8,
                metadata={'market': 'US'}
            )
        
        return None

    def _create_unknown_symbol_info(self, original: str, normalized: str) -> SymbolInfo:
        """Create symbol info for unknown symbols"""
        return SymbolInfo(
            original_symbol=original,
            normalized_symbol=normalized,
            symbol_type=SymbolType.UNKNOWN,
            primary_source=DataSource.YAHOO_FINANCE,  # Default fallback
            fallback_sources=[DataSource.AMFI_DIRECT, DataSource.MFTOOL],
            confidence=0.1,
            metadata={'needs_manual_classification': True}
        )

    def _get_country_from_exchange(self, exchange_suffix: str) -> str:
        """Get country code from exchange suffix"""
        exchange_country_map = {
            'AS': 'NL',  # Amsterdam
            'PA': 'FR',  # Paris
            'DE': 'DE',  # Germany
            'L': 'GB',   # London
            'T': 'JP',   # Tokyo
            'AX': 'AU',  # Australia
            'HK': 'HK',  # Hong Kong
            'SS': 'CN',  # Shanghai
            'SZ': 'CN',  # Shenzhen
        }
        return exchange_country_map.get(exchange_suffix, 'US')

    def get_data_source_priority(self, symbol_info: SymbolInfo) -> List[DataSource]:
        """Get prioritized list of data sources for a symbol"""
        sources = [symbol_info.primary_source] + symbol_info.fallback_sources
        return list(dict.fromkeys(sources))  # Remove duplicates while preserving order

    def suggest_symbol_corrections(self, symbol: str) -> List[str]:
        """Suggest possible corrections for invalid symbols"""
        suggestions = []
        normalized = self._normalize_symbol(symbol)
        
        # Common corrections for Indian stocks
        if not normalized.endswith(('.NS', '.BO')):
            suggestions.extend([f"{normalized}.NS", f"{normalized}.BO"])
        
        # Remove common suffixes that might be incorrectly added
        for suffix in ['.NSE', '.BSE', '.IN']:
            if normalized.endswith(suffix):
                base = normalized[:-len(suffix)]
                suggestions.extend([f"{base}.NS", f"{base}.BO"])
        
        return suggestions[:5]  # Limit to 5 suggestions

    def get_symbol_statistics(self) -> Dict[str, Any]:
        """Get statistics about symbol recognition patterns"""
        return {
            'supported_symbol_types': [t.value for t in SymbolType],
            'supported_data_sources': [s.value for s in DataSource],
            'indian_stock_patterns': len(self.indian_stock_patterns),
            'indian_etf_patterns': len(self.indian_etf_patterns),
            'indian_mf_patterns': len(self.indian_mf_patterns),
            'international_patterns': len(self.international_stock_patterns),
            'known_amc_prefixes': len(self.amc_prefixes),
            'supported_exchanges': len(self.international_exchanges)
        }


# Global instance
symbol_recognizer = SymbolRecognizer()
