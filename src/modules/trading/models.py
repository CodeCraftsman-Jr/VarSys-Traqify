"""
Trading Models
Data models for trading functionality
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal


@dataclass
class Position:
    """Represents a trading position"""
    tradingsymbol: str
    exchange: str
    instrument_token: int
    product: str
    quantity: int
    overnight_quantity: int
    multiplier: int
    average_price: float
    close_price: float
    last_price: float
    value: float
    pnl: float
    m2m: float
    unrealised: float
    realised: float
    buy_quantity: int
    buy_price: float
    buy_value: float
    sell_quantity: int
    sell_price: float
    sell_value: float
    day_buy_quantity: int
    day_buy_price: float
    day_buy_value: float
    day_sell_quantity: int
    day_sell_price: float
    day_sell_value: float


@dataclass
class Order:
    """Represents a trading order"""
    order_id: str
    parent_order_id: Optional[str]
    exchange_order_id: Optional[str]
    placed_by: str
    variety: str
    status: str
    tradingsymbol: str
    exchange: str
    instrument_token: int
    transaction_type: str
    order_type: str
    product: str
    quantity: int
    disclosed_quantity: int
    price: float
    trigger_price: float
    average_price: float
    filled_quantity: int
    pending_quantity: int
    cancelled_quantity: int
    market_protection: int
    order_timestamp: datetime
    exchange_timestamp: Optional[datetime]
    status_message: Optional[str]
    status_message_raw: Optional[str]
    guid: str
    tag: Optional[str]
    # Additional fields from API
    exchange_update_timestamp: Optional[datetime] = None
    validity: str = "DAY"
    validity_ttl: int = 0
    auction_number: Optional[str] = None
    modified: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Trade:
    """Represents a trade execution"""
    trade_id: str
    order_id: str
    exchange_order_id: Optional[str]
    tradingsymbol: str
    exchange: str
    instrument_token: int
    product: str
    average_price: float
    quantity: int
    transaction_type: str
    fill_timestamp: datetime
    order_timestamp: datetime
    exchange_timestamp: Optional[datetime] = None


@dataclass
class Holding:
    """Represents a stock holding - includes ALL Zerodha API fields"""
    # All required fields (no defaults)
    tradingsymbol: str
    exchange: str
    instrument_token: int
    isin: str
    product: str
    quantity: int
    used_quantity: int
    t1_quantity: int
    realised_quantity: int
    authorised_quantity: int
    opening_quantity: int
    collateral_quantity: int
    average_price: float
    last_price: float
    close_price: float
    pnl: float
    day_change: float
    day_change_percentage: float
    # All optional fields with defaults (must be at the end)
    price: float = 0.0
    collateral_type: str = ""
    authorised_date: Optional[datetime] = None
    short_quantity: int = 0
    discrepancy: bool = False
    authorisation: Optional[Dict[str, Any]] = None
    mtf: Optional[Dict[str, Any]] = None


@dataclass
class MarketData:
    """Represents market data for an instrument"""
    instrument_token: int
    last_price: float
    last_quantity: int
    average_price: float
    volume: int
    buy_quantity: int
    sell_quantity: int
    ohlc: Dict[str, float]  # open, high, low, close
    net_change: float
    oi: int
    oi_day_high: int
    oi_day_low: int
    timestamp: datetime
    depth: Dict[str, List[Dict[str, Any]]]  # buy/sell depth


@dataclass
class MutualFundHolding:
    """Represents a mutual fund holding"""
    tradingsymbol: str  # ISIN
    fund: str  # Fund name
    quantity: float
    average_price: float
    last_price: float
    pnl: float
    folio: Optional[str] = None
    last_price_date: str = ""
    pledged_quantity: float = 0.0

@dataclass
class Portfolio:
    """Represents portfolio summary"""
    equity: Dict[str, float]
    commodity: Dict[str, float]
    total: float
    day_pnl: float
    day_pnl_percentage: float
    unrealised_pnl: float
    realised_pnl: float
    positions: List[Position] = field(default_factory=list)
    holdings: List[Holding] = field(default_factory=list)
    orders: List[Order] = field(default_factory=list)


@dataclass
class Instrument:
    """Represents a trading instrument"""
    instrument_token: int
    exchange_token: int
    tradingsymbol: str
    name: str
    last_price: float
    expiry: Optional[datetime]
    strike: float
    tick_size: float
    lot_size: int
    instrument_type: str
    segment: str
    exchange: str


@dataclass
class TradingConfig:
    """Trading configuration settings"""
    api_key: str
    api_secret: str
    request_token: Optional[str] = None
    access_token: Optional[str] = None
    public_token: Optional[str] = None
    user_id: Optional[str] = None
    auto_login: bool = False
    sandbox_mode: bool = True
    websocket_enabled: bool = True
    max_positions: int = 50
    risk_management: Dict[str, Any] = field(default_factory=dict)
