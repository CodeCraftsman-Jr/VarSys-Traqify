"""
Zerodha API Client
Handles all interactions with Zerodha Kite Connect API
"""

import logging
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

try:
    from kiteconnect import KiteConnect
    from kiteconnect.exceptions import KiteException
    KITE_AVAILABLE = True
except ImportError:
    KITE_AVAILABLE = False
    KiteConnect = None
    KiteException = Exception

from .models import Position, Order, Holding, MarketData, Portfolio, Instrument, TradingConfig, MutualFundHolding, Trade


class ZerodhaAPIClient:
    """Zerodha API client for trading operations"""

    @staticmethod
    def load_config_from_file(config_file: str = "trading_config.json") -> TradingConfig:
        """Load trading configuration from JSON file"""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_file}")

            with open(config_path, 'r') as f:
                config_data = json.load(f)

            # Validate required fields
            if config_data.get('api_key') == 'REPLACE_WITH_YOUR_API_KEY':
                raise ValueError("Please update your API key in trading_config.json")
            if config_data.get('api_secret') == 'REPLACE_WITH_YOUR_API_SECRET':
                raise ValueError("Please update your API secret in trading_config.json")

            return TradingConfig(
                api_key=config_data['api_key'],
                api_secret=config_data['api_secret'],
                sandbox_mode=config_data.get('sandbox_mode', False),
                auto_login=config_data.get('auto_login', False),
                websocket_enabled=config_data.get('websocket_enabled', True),
                max_positions=config_data.get('max_positions', 50),
                risk_management=config_data.get('risk_management', {})
            )

        except Exception as e:
            logging.error(f"Failed to load trading configuration: {e}")
            raise

    def __init__(self, config: TradingConfig, data_directory: Path):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config
        self.data_directory = data_directory
        self.kite = None
        self.is_connected = False
        self.user_profile = None
        
        # Create trading data directory
        self.trading_data_dir = data_directory / "trading"
        self.trading_data_dir.mkdir(exist_ok=True)
        
        # Token storage file
        self.token_file = self.trading_data_dir / "tokens.json"
        
        if not KITE_AVAILABLE:
            self.logger.error("KiteConnect library not available. Please install kiteconnect package.")
            return
            
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Kite Connect client"""
        try:
            self.kite = KiteConnect(api_key=self.config.api_key)
            self.logger.info("Kite Connect client initialized")
            
            # Try to load existing tokens
            self._load_tokens()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Kite Connect client: {e}")
    
    def _load_tokens(self):
        """Load stored access tokens"""
        try:
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
                
                self.config.access_token = tokens.get('access_token')
                self.config.public_token = tokens.get('public_token')
                self.config.user_id = tokens.get('user_id')
                
                if self.config.access_token:
                    self.kite.set_access_token(self.config.access_token)
                    self.is_connected = True
                    self.logger.info("Loaded existing access token")
                    
        except Exception as e:
            self.logger.error(f"Failed to load tokens: {e}")
    
    def _save_tokens(self):
        """Save access tokens to file"""
        try:
            tokens = {
                'access_token': self.config.access_token,
                'public_token': self.config.public_token,
                'user_id': self.config.user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(tokens, f, indent=2)
                
            self.logger.info("Tokens saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save tokens: {e}")

    def _clear_expired_tokens(self):
        """Clear expired tokens from storage"""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
                self.logger.info("Cleared expired tokens from storage")

            # Reset token-related config
            self.config.access_token = None
            self.config.public_token = None
            self.config.user_id = None

        except Exception as e:
            self.logger.error(f"Failed to clear expired tokens: {e}")

    def get_login_url(self, redirect_params: str = None) -> str:
        """Get the login URL for authentication

        Args:
            redirect_params: Optional URL encoded query params to be sent back to redirect URL
        """
        if not self.kite:
            return ""

        # Use the official Kite Connect login URL format from documentation
        url = f"https://kite.zerodha.com/connect/login?v=3&api_key={self.config.api_key}"
        if redirect_params:
            url += f"&redirect_params={redirect_params}"

        return url
    
    def authenticate(self, request_token: str) -> bool:
        """Authenticate with request token"""
        try:
            if not self.kite:
                return False
                
            data = self.kite.generate_session(request_token, api_secret=self.config.api_secret)
            
            self.config.access_token = data["access_token"]
            self.config.public_token = data["public_token"]
            self.config.user_id = data["user_id"]
            
            self.kite.set_access_token(self.config.access_token)
            self.is_connected = True
            
            # Save tokens for future use
            self._save_tokens()
            
            # Get user profile
            self.user_profile = self.kite.profile()
            
            self.logger.info(f"Authentication successful for user: {self.config.user_id}")
            return True
            
        except KiteException as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {e}")
            return False

    def validate_postback_checksum(self, order_id: str, order_timestamp: str, checksum: str) -> bool:
        """Validate postback checksum as per Kite Connect documentation

        Args:
            order_id: Order ID from postback
            order_timestamp: Order timestamp from postback
            checksum: Checksum from postback payload

        Returns:
            bool: True if checksum is valid, False otherwise
        """
        try:
            import hashlib

            # Calculate expected checksum: SHA-256 of (order_id + order_timestamp + api_secret)
            expected_checksum_string = f"{order_id}{order_timestamp}{self.config.api_secret}"
            expected_checksum = hashlib.sha256(expected_checksum_string.encode()).hexdigest()

            is_valid = expected_checksum == checksum

            if not is_valid:
                self.logger.warning(f"Invalid postback checksum for order {order_id}")

            return is_valid

        except Exception as e:
            self.logger.error(f"Error validating postback checksum: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.is_connected and self.config.access_token is not None

    def _handle_api_error(self, e: Exception, method_name: str):
        """Handle API errors, particularly authentication errors"""
        if isinstance(e, KiteException):
            error_msg = str(e)
            if ("Incorrect `api_key` or `access_token`" in error_msg or
                "403" in error_msg or
                "TokenException" in error_msg):
                self.logger.warning(f"Authentication error in {method_name}, clearing tokens")
                self._clear_expired_tokens()
                self.is_connected = False
                return True  # Indicates auth error was handled
        return False  # Not an auth error
    
    def get_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            if not self.is_authenticated():
                return None
            return self.kite.profile()
        except KiteException as e:
            # Check if it's an authentication error
            if "Incorrect `api_key` or `access_token`" in str(e) or "403" in str(e):
                self.logger.warning("Access token expired, clearing stored tokens")
                self._clear_expired_tokens()
                self.is_connected = False
            self.logger.error(f"Failed to get profile: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get profile: {e}")
            return None
    
    def get_margins(self) -> Optional[Dict[str, Any]]:
        """Get account margins"""
        try:
            if not self.is_authenticated():
                return None
            return self.kite.margins()
        except Exception as e:
            if self._handle_api_error(e, "get_margins"):
                return None  # Auth error handled
            self.logger.error(f"Failed to get margins: {e}")
            return None
    
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            if not self.is_authenticated():
                return []
                
            positions_data = self.kite.positions()
            positions = []
            
            for pos_data in positions_data.get('day', []) + positions_data.get('net', []):
                position = Position(**pos_data)
                positions.append(position)
                
            return positions
            
        except Exception as e:
            if self._handle_api_error(e, "get_positions"):
                return []  # Auth error handled
            self.logger.error(f"Failed to get positions: {e}")
            return []
    
    def get_holdings(self) -> List[Holding]:
        """Get current holdings"""
        try:
            if not self.is_authenticated():
                return []
                
            holdings_data = self.kite.holdings()
            self.logger.debug(f"Raw holdings data: {holdings_data}")
            holdings = []
            
            for holding_data in holdings_data:
                # Convert date strings to datetime objects if present
                if 'authorised_date' in holding_data and holding_data['authorised_date']:
                    try:
                        # Try parsing with time component first
                        holding_data['authorised_date'] = datetime.strptime(
                            holding_data['authorised_date'], '%Y-%m-%d %H:%M:%S'
                        )
                    except ValueError:
                        try:
                            # Fallback to date only
                            holding_data['authorised_date'] = datetime.strptime(
                                holding_data['authorised_date'], '%Y-%m-%d'
                            )
                        except ValueError:
                            # If both fail, set to None
                            self.logger.warning(f"Could not parse authorised_date: {holding_data['authorised_date']}")
                            holding_data['authorised_date'] = None

                # Filter out fields that our Holding model doesn't expect
                expected_fields = {
                    'tradingsymbol', 'exchange', 'instrument_token', 'isin', 'product',
                    'price', 'quantity', 'used_quantity', 't1_quantity', 'realised_quantity',
                    'authorised_quantity', 'authorised_date', 'opening_quantity',
                    'collateral_quantity', 'collateral_type', 'average_price',
                    'last_price', 'close_price', 'pnl', 'day_change', 'day_change_percentage'
                }
                filtered_data = {k: v for k, v in holding_data.items() if k in expected_fields}

                holding = Holding(**filtered_data)
                holdings.append(holding)
                
            return holdings

        except Exception as e:
            self.logger.error(f"Failed to get holdings: {e}")
            return []

    def get_mutual_fund_holdings(self) -> List[MutualFundHolding]:
        """Get mutual fund holdings (separate from regular holdings)"""
        try:
            if not self.is_authenticated():
                return []

            mf_holdings_data = self.kite.mf_holdings()
            self.logger.debug(f"Raw mutual fund holdings data: {mf_holdings_data}")

            mf_holdings = []
            for mf_data in mf_holdings_data:
                # Create MutualFundHolding object with all available fields
                mf_holding = MutualFundHolding(
                    tradingsymbol=mf_data.get('tradingsymbol', ''),
                    fund=mf_data.get('fund', ''),
                    quantity=float(mf_data.get('quantity', 0)),
                    average_price=float(mf_data.get('average_price', 0)),
                    last_price=float(mf_data.get('last_price', 0)),
                    pnl=float(mf_data.get('pnl', 0)),
                    folio=mf_data.get('folio'),
                    last_price_date=mf_data.get('last_price_date', ''),
                    pledged_quantity=float(mf_data.get('pledged_quantity', 0))
                )
                mf_holdings.append(mf_holding)

            return mf_holdings

        except Exception as e:
            self.logger.error(f"Failed to get mutual fund holdings: {e}")
            return []

    def get_all_holdings(self) -> Dict[str, Any]:
        """Get all holdings data - both regular holdings and mutual fund holdings"""
        try:
            # Get regular holdings (stocks, ETFs)
            regular_holdings = self.get_holdings()
            self.logger.info(f"📊 Retrieved {len(regular_holdings)} regular holdings")

            # Get mutual fund holdings
            mf_holdings = self.get_mutual_fund_holdings()
            self.logger.info(f"🏦 Retrieved {len(mf_holdings)} mutual fund holdings")

            # Calculate totals
            regular_total_pnl = sum(h.pnl for h in regular_holdings)
            mf_total_pnl = sum(h.pnl for h in mf_holdings)
            total_pnl = regular_total_pnl + mf_total_pnl

            return {
                'regular_holdings': regular_holdings,
                'mutual_fund_holdings': mf_holdings,
                'summary': {
                    'regular_count': len(regular_holdings),
                    'mutual_fund_count': len(mf_holdings),
                    'total_count': len(regular_holdings) + len(mf_holdings),
                    'regular_pnl': regular_total_pnl,
                    'mutual_fund_pnl': mf_total_pnl,
                    'total_pnl': total_pnl
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get all holdings: {e}")
            return {
                'regular_holdings': [],
                'mutual_fund_holdings': [],
                'summary': {
                    'regular_count': 0,
                    'mutual_fund_count': 0,
                    'total_count': 0,
                    'regular_pnl': 0,
                    'mutual_fund_pnl': 0,
                    'total_pnl': 0
                }
            }
    
    def get_orders(self) -> List[Order]:
        """Get order history"""
        try:
            if not self.is_authenticated():
                return []
                
            orders_data = self.kite.orders()
            orders = []
            
            for order_data in orders_data:
                # Convert timestamp strings to datetime objects
                if 'order_timestamp' in order_data:
                    order_data['order_timestamp'] = datetime.fromisoformat(
                        order_data['order_timestamp'].replace('Z', '+00:00')
                    )
                if 'exchange_timestamp' in order_data and order_data['exchange_timestamp']:
                    order_data['exchange_timestamp'] = datetime.fromisoformat(
                        order_data['exchange_timestamp'].replace('Z', '+00:00')
                    )
                
                order = Order(**order_data)
                orders.append(order)
                
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            return []
    
    def place_order(self, variety: str, exchange: str, tradingsymbol: str, 
                   transaction_type: str, quantity: int, product: str,
                   order_type: str, price: Optional[float] = None,
                   trigger_price: Optional[float] = None, **kwargs) -> Optional[str]:
        """Place a new order"""
        try:
            if not self.is_authenticated():
                return None
                
            order_params = {
                'variety': variety,
                'exchange': exchange,
                'tradingsymbol': tradingsymbol,
                'transaction_type': transaction_type,
                'quantity': quantity,
                'product': product,
                'order_type': order_type
            }
            
            if price is not None:
                order_params['price'] = price
            if trigger_price is not None:
                order_params['trigger_price'] = trigger_price
                
            # Add any additional parameters
            order_params.update(kwargs)
            
            order_id = self.kite.place_order(**order_params)
            self.logger.info(f"Order placed successfully: {order_id}")
            return order_id
            
        except Exception as e:
            self.logger.error(f"Failed to place order: {e}")
            return None
    
    def modify_order(self, variety: str, order_id: str, **kwargs) -> bool:
        """Modify an existing order"""
        try:
            if not self.is_authenticated():
                return False
                
            self.kite.modify_order(variety=variety, order_id=order_id, **kwargs)
            self.logger.info(f"Order modified successfully: {order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to modify order {order_id}: {e}")
            return False
    
    def cancel_order(self, variety: str, order_id: str) -> bool:
        """Cancel an order"""
        try:
            if not self.is_authenticated():
                return False
                
            self.kite.cancel_order(variety=variety, order_id=order_id)
            self.logger.info(f"Order cancelled successfully: {order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def get_quote(self, instruments: List[str]) -> Dict[str, Any]:
        """Get market quotes for instruments"""
        try:
            if not self.is_authenticated():
                return {}
            return self.kite.quote(instruments)
        except Exception as e:
            self.logger.error(f"Failed to get quotes: {e}")
            return {}
    
    def get_historical_data(self, instrument_token: int, from_date: datetime,
                          to_date: datetime, interval: str) -> List[Dict[str, Any]]:
        """Get historical data for an instrument"""
        try:
            if not self.is_authenticated():
                return []
            return self.kite.historical_data(instrument_token, from_date, to_date, interval)
        except Exception as e:
            self.logger.error(f"Failed to get historical data: {e}")
            return []

    def get_instruments(self, exchange: Optional[str] = None) -> List[Instrument]:
        """Get list of instruments"""
        try:
            if not self.is_authenticated():
                return []

            instruments_data = self.kite.instruments(exchange)
            instruments = []

            for inst_data in instruments_data:
                # Convert expiry string to datetime if present
                if 'expiry' in inst_data and inst_data['expiry']:
                    try:
                        inst_data['expiry'] = datetime.strptime(inst_data['expiry'], '%Y-%m-%d')
                    except:
                        inst_data['expiry'] = None
                else:
                    inst_data['expiry'] = None

                instrument = Instrument(**inst_data)
                instruments.append(instrument)

            return instruments

        except Exception as e:
            self.logger.error(f"Failed to get instruments: {e}")
            return []

    def get_trades(self) -> List[Dict[str, Any]]:
        """Get all trades for the day"""
        try:
            if not self.is_authenticated():
                return []
            return self.kite.trades()
        except Exception as e:
            self.logger.error(f"Failed to get trades: {e}")
            return []

    def get_order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Get history of a specific order"""
        try:
            if not self.is_authenticated():
                return []
            return self.kite.order_history(order_id)
        except Exception as e:
            self.logger.error(f"Failed to get order history for {order_id}: {e}")
            return []

    def get_order_trades(self, order_id: str) -> List[Dict[str, Any]]:
        """Get trades generated by a specific order"""
        try:
            if not self.is_authenticated():
                return []
            return self.kite.order_trades(order_id)
        except Exception as e:
            self.logger.error(f"Failed to get order trades for {order_id}: {e}")
            return []

    def get_margin_required(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate margin required for orders"""
        try:
            if not self.is_authenticated():
                return {}
            return self.kite.order_margins(orders)
        except Exception as e:
            self.logger.error(f"Failed to get margin requirements: {e}")
            return {}

    def search_instruments(self, exchange: str, query: str) -> List[Instrument]:
        """Search for instruments by symbol"""
        try:
            if not self.is_authenticated():
                return []

            # Get all instruments for the exchange
            all_instruments = self.get_instruments(exchange)

            # Filter by query
            query_upper = query.upper()
            matching_instruments = []

            for instrument in all_instruments:
                if (query_upper in instrument.tradingsymbol.upper() or
                    query_upper in instrument.name.upper()):
                    matching_instruments.append(instrument)

                # Limit results to avoid overwhelming the UI
                if len(matching_instruments) >= 50:
                    break

            return matching_instruments

        except Exception as e:
            self.logger.error(f"Failed to search instruments: {e}")
            return []

    def get_ltp(self, instruments: List[str]) -> Dict[str, Any]:
        """Get Last Traded Price for instruments"""
        try:
            if not self.is_authenticated():
                return {}
            return self.kite.ltp(instruments)
        except Exception as e:
            self.logger.error(f"Failed to get LTP: {e}")
            return {}

    def get_ohlc(self, instruments: List[str]) -> Dict[str, Any]:
        """Get OHLC data for instruments"""
        try:
            if not self.is_authenticated():
                return {}
            return self.kite.ohlc(instruments)
        except Exception as e:
            self.logger.error(f"Failed to get OHLC: {e}")
            return {}

    def disconnect(self):
        """Disconnect from API"""
        self.is_connected = False
        self.kite = None
        self.logger.info("Disconnected from Zerodha API")
