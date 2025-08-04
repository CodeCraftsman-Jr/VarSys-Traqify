"""
Data Availability Analysis System
Analyzes and categorizes reasons for data unavailability in investment data fetching
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

from .symbol_recognition import SymbolType, DataSource


class UnavailabilityReason(Enum):
    """Reasons why data might be unavailable"""
    SYMBOL_TYPE_INCOMPATIBLE = "symbol_type_incompatible"
    DATA_SOURCE_LIMITATION = "data_source_limitation"
    NETWORK_ISSUE = "network_issue"
    SYMBOL_RECOGNITION_ISSUE = "symbol_recognition_issue"
    RATE_LIMITING = "rate_limiting"
    REGIONAL_RESTRICTION = "regional_restriction"
    API_ERROR = "api_error"
    TEMPORARY_UNAVAILABLE = "temporary_unavailable"
    NOT_SUPPORTED = "not_supported"
    UNKNOWN = "unknown"


class SeverityLevel(Enum):
    """Severity levels for unavailability issues"""
    INFO = "info"          # Expected limitation (e.g., mutual funds don't have financial data)
    WARNING = "warning"    # Temporary issue (e.g., network problems)
    ERROR = "error"        # Serious issue (e.g., symbol not recognized)


@dataclass
class UnavailabilityInfo:
    """Information about why data is unavailable"""
    reason: UnavailabilityReason
    severity: SeverityLevel
    title: str
    description: str
    icon: str
    actionable_guidance: List[str]
    alternative_sources: List[str]
    retry_suggestion: Optional[str]
    expected_availability: Optional[str]
    last_successful_fetch: Optional[str]
    data_sources_attempted: List[str]
    symbol_suggestions: List[str]


class DataAvailabilityAnalyzer:
    """Analyzes data availability and provides detailed explanations for unavailable data"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Category support matrix
        self.category_support_matrix = {
            SymbolType.INDIAN_STOCK: {
                'real_time': True, 'historical': True, 'performance': True,
                'financial': True, 'portfolio': True, 'regulatory': False,
                'dividend': True, 'fees': False
            },
            SymbolType.INDIAN_MUTUAL_FUND: {
                'real_time': True, 'historical': True, 'performance': True,
                'financial': False, 'portfolio': False, 'regulatory': False,
                'dividend': False, 'fees': True
            },
            SymbolType.INDIAN_ETF: {
                'real_time': True, 'historical': True, 'performance': True,
                'financial': False, 'portfolio': False, 'regulatory': False,
                'dividend': False, 'fees': True
            },
            SymbolType.INTERNATIONAL_STOCK: {
                'real_time': True, 'historical': True, 'performance': True,
                'financial': True, 'portfolio': True, 'regulatory': False,
                'dividend': True, 'fees': False
            },
            SymbolType.INTERNATIONAL_ETF: {
                'real_time': True, 'historical': True, 'performance': True,
                'financial': False, 'portfolio': False, 'regulatory': False,
                'dividend': False, 'fees': True
            },
            SymbolType.INTERNATIONAL_MUTUAL_FUND: {
                'real_time': True, 'historical': True, 'performance': True,
                'financial': False, 'portfolio': False, 'regulatory': False,
                'dividend': False, 'fees': True
            },
            SymbolType.UNKNOWN: {
                'real_time': True, 'historical': False, 'performance': False,
                'financial': False, 'portfolio': False, 'regulatory': False,
                'dividend': False, 'fees': False
            }
        }

    def analyze_unavailability(
        self, 
        symbol: str, 
        symbol_type: SymbolType, 
        category: str,
        data_sources_attempted: List[str] = None,
        last_error: Optional[str] = None,
        last_successful_fetch: Optional[str] = None,
        network_available: bool = True
    ) -> UnavailabilityInfo:
        """Analyze why data is unavailable and provide detailed explanation"""
        
        data_sources_attempted = data_sources_attempted or []
        
        # Check if category is supported for this symbol type
        if not self._is_category_supported(symbol_type, category):
            return self._create_symbol_type_incompatible_info(symbol, symbol_type, category)
        
        # Check for network issues
        if not network_available:
            return self._create_network_issue_info(symbol, category, last_successful_fetch)
        
        # Check for rate limiting
        if self._is_rate_limiting_error(last_error):
            return self._create_rate_limiting_info(symbol, category, data_sources_attempted)
        
        # Check for symbol recognition issues
        if symbol_type == SymbolType.UNKNOWN:
            return self._create_symbol_recognition_issue_info(symbol, category)
        
        # Check for data source limitations
        if data_sources_attempted and not self._has_successful_source(data_sources_attempted):
            return self._create_data_source_limitation_info(symbol, symbol_type, category, data_sources_attempted)
        
        # Check for regional restrictions
        if self._is_regional_restriction(symbol, symbol_type, data_sources_attempted):
            return self._create_regional_restriction_info(symbol, symbol_type, category)
        
        # Default to unknown issue
        return self._create_unknown_issue_info(symbol, category, last_error, data_sources_attempted)

    def _is_category_supported(self, symbol_type: SymbolType, category: str) -> bool:
        """Check if a category is supported for a symbol type"""
        return self.category_support_matrix.get(symbol_type, {}).get(category, False)

    def _is_rate_limiting_error(self, error: Optional[str]) -> bool:
        """Check if error indicates rate limiting"""
        if not error:
            return False
        
        rate_limit_indicators = [
            "429", "too many requests", "rate limit", "quota exceeded",
            "throttled", "rate exceeded", "limit reached"
        ]
        
        return any(indicator in error.lower() for indicator in rate_limit_indicators)

    def _has_successful_source(self, sources_attempted: List[str]) -> bool:
        """Check if any source was successful"""
        return any(source not in ['Failed', 'Error', 'Not available'] for source in sources_attempted)

    def _is_regional_restriction(self, symbol: str, symbol_type: SymbolType, sources_attempted: List[str]) -> bool:
        """Check if this might be a regional restriction issue"""
        # International symbols with Indian data sources might face restrictions
        if symbol_type in [SymbolType.INTERNATIONAL_STOCK, SymbolType.INTERNATIONAL_ETF]:
            indian_sources = ['AMFI Direct', 'mftool']
            return any(source in sources_attempted for source in indian_sources)
        
        return False

    def _create_symbol_type_incompatible_info(self, symbol: str, symbol_type: SymbolType, category: str) -> UnavailabilityInfo:
        """Create info for symbol type incompatibility"""
        symbol_type_name = symbol_type.value.replace('_', ' ').title()
        category_name = category.replace('_', ' ').title()
        
        descriptions = {
            'financial': f"Financial data (revenue, profit, debt ratios) is not applicable for {symbol_type_name.lower()}s - only available for individual stocks",
            'portfolio': f"Portfolio composition data is not applicable for {symbol_type_name.lower()}s - only available for individual stocks",
            'dividend': f"Dividend data is not applicable for {symbol_type_name.lower()}s - mutual funds typically reinvest dividends automatically",
            'regulatory': f"Regulatory filing data is not available for {symbol_type_name.lower()}s in our current data sources",
            'fees': f"Fee and expense ratio data is not applicable for {symbol_type_name.lower()}s - only available for mutual funds and ETFs"
        }
        
        description = descriptions.get(category, f"{category_name} data is not supported for {symbol_type_name.lower()}s")
        
        # Determine what symbol types DO support this category
        supported_types = []
        for stype, categories in self.category_support_matrix.items():
            if categories.get(category, False):
                supported_types.append(stype.value.replace('_', ' ').title())
        
        expected_availability = f"This data type is typically available for: {', '.join(supported_types)}" if supported_types else None
        
        return UnavailabilityInfo(
            reason=UnavailabilityReason.SYMBOL_TYPE_INCOMPATIBLE,
            severity=SeverityLevel.INFO,
            title=f"{category_name} Not Applicable",
            description=description,
            icon="ℹ️",
            actionable_guidance=[
                f"This is expected behavior for {symbol_type_name.lower()}s",
                "Consider looking at other available data categories",
                "For financial analysis, try individual stock symbols instead"
            ],
            alternative_sources=[],
            retry_suggestion=None,
            expected_availability=expected_availability,
            last_successful_fetch=None,
            data_sources_attempted=[],
            symbol_suggestions=[]
        )

    def _create_network_issue_info(self, symbol: str, category: str, last_successful_fetch: Optional[str]) -> UnavailabilityInfo:
        """Create info for network connectivity issues"""
        return UnavailabilityInfo(
            reason=UnavailabilityReason.NETWORK_ISSUE,
            severity=SeverityLevel.WARNING,
            title="Network Connectivity Issue",
            description="Unable to fetch data due to network connectivity issues. The application cannot reach the data sources.",
            icon="⚠️",
            actionable_guidance=[
                "Check your internet connection",
                "Try refreshing the data in a few moments",
                "Check if firewall is blocking the application",
                "Consider using a VPN if corporate firewall is restrictive"
            ],
            alternative_sources=["Cached data (if available)"],
            retry_suggestion="Click 'Refresh Data' to retry fetching when network is restored",
            expected_availability="Data should be available when network connectivity is restored",
            last_successful_fetch=last_successful_fetch,
            data_sources_attempted=[],
            symbol_suggestions=[]
        )

    def _create_rate_limiting_info(self, symbol: str, category: str, sources_attempted: List[str]) -> UnavailabilityInfo:
        """Create info for rate limiting issues"""
        return UnavailabilityInfo(
            reason=UnavailabilityReason.RATE_LIMITING,
            severity=SeverityLevel.WARNING,
            title="Data Source Rate Limited",
            description="Data source temporarily unavailable due to rate limiting. Too many requests have been made in a short period.",
            icon="🚦",
            actionable_guidance=[
                "Wait a few minutes before trying again",
                "Rate limits typically reset within 1-5 minutes",
                "Avoid rapid successive refresh attempts"
            ],
            alternative_sources=["Cached data (if available)"],
            retry_suggestion="Wait 2-3 minutes, then click 'Refresh Data' to retry",
            expected_availability="Data should be available after rate limit period expires",
            last_successful_fetch=None,
            data_sources_attempted=sources_attempted,
            symbol_suggestions=[]
        )

    def _create_symbol_recognition_issue_info(self, symbol: str, category: str) -> UnavailabilityInfo:
        """Create info for symbol recognition issues"""
        # Generate symbol suggestions
        suggestions = self._generate_symbol_suggestions(symbol)
        
        return UnavailabilityInfo(
            reason=UnavailabilityReason.SYMBOL_RECOGNITION_ISSUE,
            severity=SeverityLevel.ERROR,
            title="Symbol Not Recognized",
            description=f"The symbol '{symbol}' format is not recognized by any of our data sources. This might be due to incorrect symbol format or unsupported symbol type.",
            icon="❌",
            actionable_guidance=[
                "Verify the symbol format is correct",
                "Try alternative symbol formats (see suggestions below)",
                "For Indian stocks, ensure .NS or .BO suffix is included",
                "For mutual funds, try using AMFI scheme code instead"
            ],
            alternative_sources=[
                "AMFI Direct (for Indian mutual funds)",
                "Yahoo Finance (for stocks with proper suffixes)",
                "Manual search by fund/company name"
            ],
            retry_suggestion="Try one of the suggested symbol formats below",
            expected_availability="Data should be available with correct symbol format",
            last_successful_fetch=None,
            data_sources_attempted=[],
            symbol_suggestions=suggestions
        )

    def _generate_symbol_suggestions(self, symbol: str) -> List[str]:
        """Generate symbol format suggestions"""
        suggestions = []
        
        # Remove common suffixes for base symbol
        base_symbol = symbol.replace('.NS', '').replace('.BO', '').replace('.BSE', '').replace('.NSE', '').strip()
        
        # Add exchange suffixes if not present
        if not any(suffix in symbol.upper() for suffix in ['.NS', '.BO', '.BSE', '.NSE']):
            suggestions.extend([f"{base_symbol}.NS", f"{base_symbol}.BO"])
        
        # If it looks like it might be a mutual fund name, suggest AMFI code search
        if any(word in symbol.upper() for word in ['FUND', 'MF', 'MUTUAL', 'HDFC', 'ICICI', 'SBI', 'AXIS']):
            suggestions.append("Try searching by AMFI scheme code (6-digit number)")
            suggestions.append("Try searching by partial fund name")
        
        # If it's very short, might need exchange suffix
        if len(base_symbol) <= 5 and base_symbol.isalpha():
            suggestions.extend([f"{base_symbol}.NS", f"{base_symbol}.BO"])
        
        return suggestions[:5]  # Limit to 5 suggestions

    def _create_data_source_limitation_info(self, symbol: str, symbol_type: SymbolType, category: str, sources_attempted: List[str]) -> UnavailabilityInfo:
        """Create info for data source limitations"""
        symbol_type_name = symbol_type.value.replace('_', ' ').title()
        category_name = category.replace('_', ' ').title()

        # Determine primary data source for this symbol type
        primary_source = self._get_primary_source_name(symbol_type)

        description = f"{primary_source} does not provide {category_name.lower()} data for this {symbol_type_name.lower()} symbol. This data category may not be available from our current data sources."

        return UnavailabilityInfo(
            reason=UnavailabilityReason.DATA_SOURCE_LIMITATION,
            severity=SeverityLevel.WARNING,
            title=f"{category_name} Not Available from Data Sources",
            description=description,
            icon="📊",
            actionable_guidance=[
                f"Try alternative data sources if available",
                f"Check if symbol format is correct for {primary_source}",
                "Some data may only be available for premium symbols",
                "Consider checking the company's official website"
            ],
            alternative_sources=self._get_alternative_sources(symbol_type, category),
            retry_suggestion="Try 'Refresh Data' in case of temporary data source issues",
            expected_availability=f"This data type may be limited for {symbol_type_name.lower()}s",
            last_successful_fetch=None,
            data_sources_attempted=sources_attempted,
            symbol_suggestions=[]
        )

    def _create_regional_restriction_info(self, symbol: str, symbol_type: SymbolType, category: str) -> UnavailabilityInfo:
        """Create info for regional restriction issues"""
        symbol_type_name = symbol_type.value.replace('_', ' ').title()

        return UnavailabilityInfo(
            reason=UnavailabilityReason.REGIONAL_RESTRICTION,
            severity=SeverityLevel.WARNING,
            title="Regional Data Restriction",
            description=f"This {symbol_type_name.lower()} symbol may not be supported by Indian data sources due to regional restrictions or limited international coverage.",
            icon="🌍",
            actionable_guidance=[
                "International symbols have limited support in Indian data sources",
                "Try using Yahoo Finance format for international symbols",
                "Consider using international financial platforms",
                "Verify the symbol is actively traded"
            ],
            alternative_sources=[
                "Yahoo Finance (for international symbols)",
                "International financial data providers",
                "Company's official investor relations page"
            ],
            retry_suggestion="Try with proper international symbol format",
            expected_availability="Limited availability for international symbols in Indian data sources",
            last_successful_fetch=None,
            data_sources_attempted=[],
            symbol_suggestions=[]
        )

    def _create_unknown_issue_info(self, symbol: str, category: str, last_error: Optional[str], sources_attempted: List[str]) -> UnavailabilityInfo:
        """Create info for unknown issues"""
        category_name = category.replace('_', ' ').title()

        error_context = f" Error details: {last_error}" if last_error else ""

        return UnavailabilityInfo(
            reason=UnavailabilityReason.UNKNOWN,
            severity=SeverityLevel.ERROR,
            title=f"{category_name} Data Unavailable",
            description=f"Unable to fetch {category_name.lower()} data for this symbol. The specific cause is unclear.{error_context}",
            icon="❓",
            actionable_guidance=[
                "Try refreshing the data",
                "Check if the symbol is correct",
                "Verify the symbol is actively traded",
                "Try again in a few minutes"
            ],
            alternative_sources=[
                "Manual search on financial websites",
                "Company's official website",
                "Alternative financial data platforms"
            ],
            retry_suggestion="Click 'Refresh Data' to retry fetching",
            expected_availability="Data availability depends on symbol and data source support",
            last_successful_fetch=None,
            data_sources_attempted=sources_attempted,
            symbol_suggestions=[]
        )

    def _get_primary_source_name(self, symbol_type: SymbolType) -> str:
        """Get the primary data source name for a symbol type"""
        source_mapping = {
            SymbolType.INDIAN_STOCK: "Yahoo Finance",
            SymbolType.INDIAN_MUTUAL_FUND: "AMFI Direct",
            SymbolType.INDIAN_ETF: "Yahoo Finance",
            SymbolType.INTERNATIONAL_STOCK: "Yahoo Finance",
            SymbolType.INTERNATIONAL_ETF: "Yahoo Finance",
            SymbolType.INTERNATIONAL_MUTUAL_FUND: "Yahoo Finance",
            SymbolType.UNKNOWN: "Multiple sources"
        }
        return source_mapping.get(symbol_type, "Data sources")

    def _get_alternative_sources(self, symbol_type: SymbolType, category: str) -> List[str]:
        """Get alternative data sources for a symbol type and category"""
        alternatives = []

        if symbol_type == SymbolType.INDIAN_MUTUAL_FUND:
            alternatives.extend(["AMFI Direct", "mftool library", "Yahoo Finance"])
        elif symbol_type in [SymbolType.INDIAN_STOCK, SymbolType.INDIAN_ETF]:
            alternatives.extend(["Yahoo Finance", "NSE/BSE official websites"])
        elif symbol_type in [SymbolType.INTERNATIONAL_STOCK, SymbolType.INTERNATIONAL_ETF]:
            alternatives.extend(["Yahoo Finance", "International financial platforms"])

        # Add category-specific alternatives
        if category == 'financial':
            alternatives.extend(["Company annual reports", "SEC filings", "Company investor relations"])
        elif category == 'dividend':
            alternatives.extend(["Company dividend history pages", "Financial news websites"])
        elif category == 'fees':
            alternatives.extend(["Fund fact sheets", "Prospectus documents"])

        return list(set(alternatives))  # Remove duplicates

    def get_category_explanation(self, category: str) -> str:
        """Get explanation of what a data category contains"""
        explanations = {
            'real_time': "Current price, NAV, volume, and basic trading information",
            'historical': "Historical price data, charts, and performance over time",
            'performance': "Key performance metrics like P/E ratio, beta, returns, and ratios",
            'financial': "Financial statements data including revenue, profit, debt, and margins",
            'portfolio': "Portfolio composition, sector allocation, and holdings information",
            'regulatory': "Regulatory filings, compliance reports, and official announcements",
            'dividend': "Dividend history, yield information, and payout schedules",
            'fees': "Expense ratios, management fees, and cost structure information"
        }
        return explanations.get(category, f"{category.replace('_', ' ').title()} data")


# Global instance
data_availability_analyzer = DataAvailabilityAnalyzer()
