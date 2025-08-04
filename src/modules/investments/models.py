"""
Investment Portfolio Data Models
Handles investment tracking data structure and calculations
"""

import logging
import pandas as pd
import csv
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict, fields
from enum import Enum


class InvestmentType(Enum):
    """Investment types"""
    STOCKS = "Stocks"
    BONDS = "Bonds"
    MUTUAL_FUNDS = "Mutual Funds"
    ETF = "ETF"
    CRYPTO = "Cryptocurrency"
    REAL_ESTATE = "Real Estate"
    COMMODITIES = "Commodities"
    FIXED_DEPOSIT = "Fixed Deposit"
    SAVINGS = "Savings Account"
    OTHER = "Other"


class TransactionType(Enum):
    """Transaction types"""
    BUY = "Buy"
    SELL = "Sell"
    DIVIDEND = "Dividend"
    INTEREST = "Interest"
    SPLIT = "Stock Split"
    BONUS = "Bonus Shares"


@dataclass
class Investment:
    """Data class for individual investments"""
    id: Optional[int] = None
    symbol: str = ""  # Stock symbol or investment identifier
    name: str = ""  # Full name of investment
    investment_type: str = InvestmentType.STOCKS.value
    quantity: float = 0.0
    purchase_price: float = 0.0
    current_price: float = 0.0
    purchase_date: Optional[Union[str, datetime, date]] = None
    last_updated: Optional[datetime] = None
    notes: str = ""
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.last_updated is None:
            self.last_updated = datetime.now()
        
        # Handle purchase_date conversion
        if self.purchase_date and isinstance(self.purchase_date, str):
            try:
                self.purchase_date = datetime.strptime(self.purchase_date, '%Y-%m-%d').date()
            except ValueError:
                self.purchase_date = date.today()
        elif isinstance(self.purchase_date, datetime):
            self.purchase_date = self.purchase_date.date()
        elif self.purchase_date is None:
            self.purchase_date = date.today()
    
    def get_total_investment(self) -> float:
        """Get total investment amount"""
        return self.quantity * self.purchase_price
    
    def get_current_value(self) -> float:
        """Get current market value"""
        return self.quantity * self.current_price
    
    def get_profit_loss(self) -> float:
        """Get profit/loss amount"""
        return self.get_current_value() - self.get_total_investment()
    
    def get_profit_loss_percentage(self) -> float:
        """Get profit/loss percentage"""
        if self.get_total_investment() == 0:
            return 0.0
        return (self.get_profit_loss() / self.get_total_investment()) * 100
    
    def get_days_held(self) -> int:
        """Get number of days held"""
        if not self.purchase_date:
            return 0
        return (date.today() - self.purchase_date).days
    
    def get_annualized_return(self) -> float:
        """Get annualized return percentage"""
        days_held = self.get_days_held()
        if days_held == 0:
            return 0.0
        
        years_held = days_held / 365.25
        if years_held == 0:
            return 0.0
        
        total_return = self.get_profit_loss_percentage() / 100
        return ((1 + total_return) ** (1 / years_held) - 1) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        data = asdict(self)
        
        # Convert date objects to strings
        if isinstance(data['purchase_date'], date):
            data['purchase_date'] = data['purchase_date'].strftime('%Y-%m-%d')
        if isinstance(data['last_updated'], datetime):
            data['last_updated'] = data['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Add calculated fields
        data['total_investment'] = self.get_total_investment()
        data['current_value'] = self.get_current_value()
        data['profit_loss'] = self.get_profit_loss()
        data['profit_loss_percentage'] = self.get_profit_loss_percentage()
        data['days_held'] = self.get_days_held()
        data['annualized_return'] = self.get_annualized_return()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Investment':
        """Create from dictionary"""
        # Remove calculated fields
        calc_fields = ['total_investment', 'current_value', 'profit_loss', 
                      'profit_loss_percentage', 'days_held', 'annualized_return']
        for field in calc_fields:
            data.pop(field, None)
        
        # Handle datetime strings
        if 'last_updated' in data and isinstance(data['last_updated'], str) and data['last_updated']:
            try:
                data['last_updated'] = datetime.strptime(data['last_updated'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['last_updated'] = None
        
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate the investment"""
        errors = []
        
        if not self.symbol.strip():
            errors.append("Symbol is required")
        
        if not self.name.strip():
            errors.append("Name is required")
        
        if self.investment_type not in [t.value for t in InvestmentType]:
            errors.append(f"Invalid investment type: {self.investment_type}")
        
        if self.quantity < 0:
            errors.append("Quantity cannot be negative")
        
        if self.purchase_price < 0:
            errors.append("Purchase price cannot be negative")
        
        if self.current_price < 0:
            errors.append("Current price cannot be negative")
        
        return errors


class InvestmentDataModel:
    """Data model for investment portfolio management"""
    
    def __init__(self, data_manager):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("="*40)
        self.logger.info("INITIALIZING INVESTMENT DATA MODEL")
        self.logger.info("="*40)
        
        try:
            self.data_manager = data_manager
            self.module_name = "investments"
            self.filename = "investments.csv"
            
            # Default columns for CSV
            self.columns = [
                'id', 'symbol', 'name', 'investment_type', 'quantity',
                'purchase_price', 'current_price', 'purchase_date',
                'last_updated', 'notes', 'total_investment', 'current_value',
                'profit_loss', 'profit_loss_percentage', 'days_held', 'annualized_return'
            ]
            
            self.logger.info("✅ InvestmentDataModel initialization SUCCESSFUL")
            
        except Exception as e:
            self.logger.error(f"❌ CRITICAL ERROR in InvestmentDataModel.__init__: {e}")
            raise
    
    def get_all_investments(self) -> pd.DataFrame:
        """Get all investments"""
        try:
            df = self.data_manager.read_csv(self.module_name, self.filename, self.columns)
            return df
        except Exception as e:
            self.logger.error(f"Error getting investments: {e}")
            return pd.DataFrame(columns=self.columns)
    
    def add_investment(self, investment: Investment) -> bool:
        """Add a new investment"""
        errors = investment.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False
        
        return self.data_manager.append_row(
            self.module_name,
            self.filename,
            investment.to_dict(),
            self.columns
        )
    
    def update_investment(self, investment_id: int, investment: Investment) -> bool:
        """Update an existing investment"""
        errors = investment.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False
        
        return self.data_manager.update_row(
            self.module_name,
            self.filename,
            investment_id,
            investment.to_dict()
        )
    
    def delete_investment(self, investment_id: int) -> bool:
        """Delete an investment"""
        return self.data_manager.delete_row(self.module_name, self.filename, investment_id)
    
    def get_investments_by_type(self, investment_type: str) -> pd.DataFrame:
        """Get investments filtered by type"""
        df = self.get_all_investments()
        if df.empty:
            return df
        return df[df['investment_type'] == investment_type]
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary statistics"""
        df = self.get_all_investments()
        
        if df.empty:
            return {
                'total_investments': 0,
                'total_investment_amount': 0.0,
                'total_current_value': 0.0,
                'total_profit_loss': 0.0,
                'total_profit_loss_percentage': 0.0,
                'best_performer': None,
                'worst_performer': None,
                'by_type': {},
                'average_return': 0.0
            }
        
        total_investment_amount = df['total_investment'].sum()
        total_current_value = df['current_value'].sum()
        total_profit_loss = df['profit_loss'].sum()
        
        total_profit_loss_percentage = 0.0
        if total_investment_amount > 0:
            total_profit_loss_percentage = (total_profit_loss / total_investment_amount) * 100
        
        # Best and worst performers
        best_performer = None
        worst_performer = None
        
        if not df.empty:
            best_idx = df['profit_loss_percentage'].idxmax()
            worst_idx = df['profit_loss_percentage'].idxmin()
            
            best_performer = {
                'symbol': df.loc[best_idx, 'symbol'],
                'name': df.loc[best_idx, 'name'],
                'return': df.loc[best_idx, 'profit_loss_percentage']
            }
            
            worst_performer = {
                'symbol': df.loc[worst_idx, 'symbol'],
                'name': df.loc[worst_idx, 'name'],
                'return': df.loc[worst_idx, 'profit_loss_percentage']
            }
        
        # Group by investment type
        by_type = {}
        for inv_type in df['investment_type'].unique():
            type_df = df[df['investment_type'] == inv_type]
            by_type[inv_type] = {
                'count': len(type_df),
                'total_investment': type_df['total_investment'].sum(),
                'current_value': type_df['current_value'].sum(),
                'profit_loss': type_df['profit_loss'].sum()
            }
        
        # Average return (weighted by investment amount)
        if total_investment_amount > 0:
            weighted_returns = (df['profit_loss_percentage'] * df['total_investment']).sum()
            average_return = weighted_returns / total_investment_amount
        else:
            average_return = 0.0
        
        return {
            'total_investments': len(df),
            'total_investment_amount': total_investment_amount,
            'total_current_value': total_current_value,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_percentage': total_profit_loss_percentage,
            'best_performer': best_performer,
            'worst_performer': worst_performer,
            'by_type': by_type,
            'average_return': average_return
        }
    
    def update_current_prices(self, price_updates: Dict[str, float]) -> int:
        """Update current prices for multiple investments"""
        df = self.get_all_investments()
        if df.empty:
            return 0
        
        updated_count = 0
        for symbol, new_price in price_updates.items():
            matching_rows = df[df['symbol'] == symbol]
            for idx, row in matching_rows.iterrows():
                investment = Investment.from_dict(row.to_dict())
                investment.current_price = new_price
                investment.last_updated = datetime.now()
                
                if self.update_investment(row['id'], investment):
                    updated_count += 1
        
        return updated_count


# New data models for additional investment tabs

@dataclass
class CurrentResource:
    """Data class for current resource tracking"""
    id: Optional[int] = None
    category: str = ""
    amount_lakhs: float = 0.0
    allocation_percent: float = 0.0
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class AssetLiability:
    """Data class for asset/liability tracking - matches GUI table structure"""
    id: Optional[int] = None
    name: str = ""  # Changed from item_name to match GUI
    type: str = "Asset"  # Changed from item_type to match GUI (Asset or Liability)
    category: str = ""
    sub_category: str = ""  # New field to match GUI
    geographic_classification: str = ""  # New field to match GUI
    amount: float = 0.0  # New field to match GUI
    percentage: float = 0.0
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'category': self.category,
            'sub_category': self.sub_category,
            'geographic_classification': self.geographic_classification,
            'amount': self.amount,
            'percentage': self.percentage,
            'created_date': self.created_date.isoformat() if self.created_date else '',
            'last_updated': self.last_updated.isoformat() if self.last_updated else ''
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AssetLiability':
        """Create instance from dictionary"""
        # Handle date parsing
        created_date = None
        if data.get('created_date'):
            try:
                created_date = datetime.fromisoformat(data['created_date'])
            except ValueError:
                created_date = datetime.now()

        last_updated = None
        if data.get('last_updated'):
            try:
                last_updated = datetime.fromisoformat(data['last_updated'])
            except ValueError:
                last_updated = datetime.now()

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            name=data.get('name', ''),
            type=data.get('type', 'Asset'),
            category=data.get('category', ''),
            sub_category=data.get('sub_category', ''),
            geographic_classification=data.get('geographic_classification', ''),
            amount=float(data.get('amount', 0.0)),
            percentage=float(data.get('percentage', 0.0)),
            created_date=created_date,
            last_updated=last_updated
        )


@dataclass
class FinancialGoal:
    """Data class for financial goal planning"""
    id: Optional[int] = None
    goal_name: str = ""
    current_cost: float = 0.0
    years_until_goal: int = 0
    future_value: float = 0.0
    monthly_sip_required: float = 0.0
    time_horizon: str = "Medium Term"  # Short Term, Medium Term, Long Term
    action_plan: str = ""
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class InsurancePolicy:
    """Data class for insurance policy tracking"""
    id: Optional[int] = None
    policy_name: str = ""
    policy_type: str = ""  # Vehicle, Health, Life, Property
    policy_number: str = ""
    insurance_provider: str = ""  # Insurance company name
    coverage_type: str = ""  # Specific coverage details
    coverage_amount: float = 0.0  # Coverage amount
    premium_amount: float = 0.0
    payment_frequency: str = "Annual"  # Monthly, Quarterly, Annual
    policy_start_date: Optional[Union[str, datetime, date]] = None
    valid_till: Optional[Union[str, datetime, date]] = None
    premium_due_date: Optional[Union[str, datetime, date]] = None
    beneficiaries: str = ""  # Comma-separated list of beneficiaries
    deductible_amount: float = 0.0
    current_status: str = "Active"  # Active, Expired, Pending Renewal
    amount_insured: float = 0.0  # Legacy field, kept for backward compatibility
    nominee: str = ""  # Legacy field, kept for backward compatibility
    remarks: str = ""
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

        # Handle date conversions
        for date_field in ['valid_till', 'premium_due_date', 'policy_start_date']:
            if hasattr(self, date_field):
                date_value = getattr(self, date_field)
                if date_value and isinstance(date_value, str):
                    try:
                        setattr(self, date_field, datetime.strptime(date_value, '%Y-%m-%d').date())
                    except ValueError:
                        setattr(self, date_field, None)
                elif isinstance(date_value, datetime):
                    setattr(self, date_field, date_value.date())

        # Ensure backward compatibility - sync amount_insured with coverage_amount
        if hasattr(self, 'coverage_amount') and hasattr(self, 'amount_insured'):
            if self.coverage_amount > 0 and self.amount_insured == 0:
                self.amount_insured = self.coverage_amount
            elif self.amount_insured > 0 and self.coverage_amount == 0:
                self.coverage_amount = self.amount_insured

        # Ensure backward compatibility - sync nominee with beneficiaries
        if hasattr(self, 'nominee') and hasattr(self, 'beneficiaries'):
            if self.nominee and not self.beneficiaries:
                self.beneficiaries = self.nominee
            elif self.beneficiaries and not self.nominee:
                # Take first beneficiary as nominee for backward compatibility
                self.nominee = self.beneficiaries.split(',')[0].strip()


@dataclass
class LICPolicy:
    """Data class for LIC (Life Insurance Corporation) policy tracking"""
    id: Optional[int] = None
    policy_holder_name: str = ""  # Family member name
    policy_number: str = ""
    policy_type: str = ""  # Endowment, Term, ULIP, Pension, etc.
    plan_name: str = ""  # Specific LIC plan name
    premium_amount: float = 0.0
    premium_frequency: str = "Annual"  # Monthly, Quarterly, Half-Yearly, Annual
    premium_due_date: Optional[Union[str, datetime, date]] = None
    policy_start_date: Optional[Union[str, datetime, date]] = None
    maturity_date: Optional[Union[str, datetime, date]] = None
    sum_assured: float = 0.0  # Basic sum assured
    bonus_amount: float = 0.0  # Accumulated bonus
    surrender_value: float = 0.0  # Current surrender value
    loan_amount: float = 0.0  # Outstanding loan against policy
    nominee_name: str = ""
    nominee_relationship: str = ""
    current_status: str = "Active"  # Active, Paid-up, Lapsed, Matured, Surrendered
    agent_name: str = ""
    agent_code: str = ""
    branch_office: str = ""
    last_premium_paid_date: Optional[Union[str, datetime, date]] = None
    next_premium_due_date: Optional[Union[str, datetime, date]] = None
    policy_document_number: str = ""  # Physical document reference
    remarks: str = ""
    # Sum Assured Breakdown fields
    base_sum_assured: float = 0.0  # Base coverage amount
    additional_coverage: float = 0.0  # Additional coverage purchased
    rider_coverage: float = 0.0  # Rider benefits coverage
    loyalty_addition: float = 0.0  # Loyalty additions
    terminal_bonus: float = 0.0  # Terminal bonus amount
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

        # Handle date conversions for LIC-specific fields
        for date_field in ['premium_due_date', 'policy_start_date', 'maturity_date',
                          'last_premium_paid_date', 'next_premium_due_date']:
            if hasattr(self, date_field):
                date_value = getattr(self, date_field)
                if date_value and isinstance(date_value, str):
                    try:
                        setattr(self, date_field, datetime.strptime(date_value, '%Y-%m-%d').date())
                    except ValueError:
                        setattr(self, date_field, None)
                elif isinstance(date_value, datetime):
                    setattr(self, date_field, date_value.date())

    def get_sum_assured_breakdown(self):
        """Get sum assured breakdown with default logic if specific components are not available"""
        # Ensure all breakdown components have default values (handle None values)
        self.base_sum_assured = self.base_sum_assured or 0.0
        self.additional_coverage = self.additional_coverage or 0.0
        self.rider_coverage = self.rider_coverage or 0.0
        self.loyalty_addition = self.loyalty_addition or 0.0
        self.terminal_bonus = self.terminal_bonus or 0.0
        self.sum_assured = self.sum_assured or 0.0

        # If breakdown components are not set, create default breakdown
        total_breakdown = (self.base_sum_assured + self.additional_coverage +
                          self.rider_coverage + self.loyalty_addition + self.terminal_bonus)

        if total_breakdown == 0 and self.sum_assured > 0:
            # Create default breakdown based on policy type and sum assured
            if self.policy_type.lower() in ['endowment', 'money back']:
                # Endowment policies typically have base + bonus structure
                self.base_sum_assured = self.sum_assured * 0.75  # 75% base
                self.loyalty_addition = self.sum_assured * 0.15  # 15% loyalty
                self.terminal_bonus = self.sum_assured * 0.10   # 10% terminal bonus
            elif self.policy_type.lower() == 'term':
                # Term policies are usually pure coverage
                self.base_sum_assured = self.sum_assured * 0.95  # 95% base
                self.additional_coverage = self.sum_assured * 0.05  # 5% additional
            elif self.policy_type.lower() == 'ulip':
                # ULIP policies have base + fund value
                self.base_sum_assured = self.sum_assured * 0.60  # 60% base
                self.additional_coverage = self.sum_assured * 0.30  # 30% fund value
                self.rider_coverage = self.sum_assured * 0.10   # 10% riders
            else:
                # Default breakdown for other policy types
                self.base_sum_assured = self.sum_assured * 0.80  # 80% base
                self.additional_coverage = self.sum_assured * 0.15  # 15% additional
                self.loyalty_addition = self.sum_assured * 0.05  # 5% loyalty

        # Return breakdown as list of tuples (component_type, amount, description)
        breakdown = []

        if self.base_sum_assured > 0:
            breakdown.append(("Base Sum Assured", self.base_sum_assured,
                            "Core coverage amount guaranteed by the policy"))

        if self.additional_coverage > 0:
            breakdown.append(("Additional Coverage", self.additional_coverage,
                            "Extra coverage purchased or added to the policy"))

        if self.rider_coverage > 0:
            breakdown.append(("Rider Benefits", self.rider_coverage,
                            "Coverage from attached riders (accident, disability, etc.)"))

        if self.loyalty_addition > 0:
            breakdown.append(("Loyalty Addition", self.loyalty_addition,
                            "Additional benefits for long-term policyholders"))

        if self.terminal_bonus > 0:
            breakdown.append(("Terminal Bonus", self.terminal_bonus,
                            "One-time bonus payable at maturity"))

        # If still no breakdown, use the total sum assured as base
        if not breakdown and self.sum_assured > 0:
            breakdown.append(("Total Sum Assured", self.sum_assured,
                            "Complete coverage amount (breakdown not available)"))

        return breakdown


@dataclass
class LoanDetails:
    """Data class for loan tracking"""
    id: Optional[int] = None
    loan_name: str = ""
    outstanding_amount: float = 0.0
    interest_rate: float = 0.0
    remaining_period_months: int = 0
    emi_amount: float = 0.0
    emi_start_date: Optional[datetime] = None
    emi_end_date: Optional[datetime] = None
    last_paid_date: Optional[datetime] = None
    net_tenure: int = 0
    loan_holder: str = ""
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def calculate_emi(self, principal=None, rate=None, tenure_months=None):
        """Calculate EMI using the standard loan formula: EMI = P × r × (1+r)^n / ((1+r)^n - 1)

        Uses net_tenure by default for complete loan lifecycle calculations.
        """
        # Use provided values or instance values
        P = principal if principal is not None else self.outstanding_amount
        r = (rate if rate is not None else self.interest_rate) / 100 / 12  # Monthly interest rate
        # Use net_tenure for complete loan lifecycle, not remaining_period_months
        n = tenure_months if tenure_months is not None else self.net_tenure

        # Handle edge cases
        if P <= 0 or n <= 0:
            return 0.0

        if r == 0:  # Zero interest rate
            return P / n

        # Standard EMI formula
        emi = P * r * (1 + r) ** n / ((1 + r) ** n - 1)
        return round(emi, 2)

    def generate_amortization_schedule(self):
        """Generate complete amortization schedule for the loan lifecycle using net_tenure

        This generates the full amortization schedule from loan start to finish,
        showing the complete loan repayment journey based on net_tenure.
        """
        if self.outstanding_amount <= 0 or self.net_tenure <= 0:
            return []

        # Calculate EMI if not provided
        emi = self.emi_amount if self.emi_amount > 0 else self.calculate_emi()

        if emi <= 0:
            return []

        schedule = []
        # Use Decimal for high precision calculations to avoid floating-point errors
        from decimal import Decimal, ROUND_HALF_UP

        # Convert to Decimal for precise calculations
        remaining_balance = Decimal(str(self.outstanding_amount))
        emi_decimal = Decimal(str(emi))
        monthly_rate_decimal = Decimal(str(self.interest_rate)) / Decimal('100') / Decimal('12') if self.interest_rate > 0 else Decimal('0')

        # Track cumulative principal for final validation
        cumulative_principal = Decimal('0')
        original_loan_amount = Decimal(str(self.outstanding_amount))

        # Start date for payments
        start_date = self.emi_start_date if self.emi_start_date else datetime.now().date()
        if isinstance(start_date, datetime):
            start_date = start_date.date()

        # Generate ALL payment periods for the complete loan duration using net_tenure
        for payment_num in range(1, self.net_tenure + 1):
            # Calculate payment date
            payment_date = self.add_months_to_date(start_date, payment_num - 1)

            # Calculate interest for this month
            interest_amount = remaining_balance * monthly_rate_decimal

            # For the final payment, ensure we pay exactly the remaining balance
            if payment_num == self.net_tenure:
                # Final payment: pay all remaining balance plus interest
                principal_amount = remaining_balance
                total_payment = principal_amount + interest_amount
                remaining_balance = Decimal('0')
            else:
                # Regular payment
                principal_amount = emi_decimal - interest_amount

                # Ensure principal is not negative (can happen with very high interest rates)
                if principal_amount < 0:
                    principal_amount = Decimal('0')
                    interest_amount = emi_decimal

                # Ensure we don't pay more principal than remaining balance
                if principal_amount > remaining_balance:
                    principal_amount = remaining_balance
                    total_payment = principal_amount + interest_amount
                    remaining_balance = Decimal('0')
                else:
                    total_payment = emi_decimal
                    remaining_balance -= principal_amount

            # Track cumulative principal
            cumulative_principal += principal_amount

            # Convert back to float and round for display
            schedule.append({
                'payment_number': payment_num,
                'payment_date': payment_date,
                'principal_amount': float(principal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'interest_amount': float(interest_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'total_payment': float(total_payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'remaining_balance': float(remaining_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            })

            # Stop if balance is fully paid
            if remaining_balance <= 0:
                break

        # Final validation and adjustment if needed
        if schedule:
            # Ensure final balance is exactly zero
            schedule[-1]['remaining_balance'] = 0.00

            # Check if cumulative principal matches original loan amount
            total_principal_paid = sum(Decimal(str(payment['principal_amount'])) for payment in schedule)
            principal_difference = original_loan_amount - total_principal_paid

            # If there's a small difference due to rounding, adjust the final payment
            if abs(principal_difference) > Decimal('0'):
                final_payment = schedule[-1]
                adjustment = float(principal_difference.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                final_payment['principal_amount'] = round(final_payment['principal_amount'] + adjustment, 2)
                final_payment['total_payment'] = round(final_payment['total_payment'] + adjustment, 2)

        return schedule

    def validate_amortization_schedule(self, schedule):
        """Validate the accuracy of the amortization schedule"""
        if not schedule:
            return {'valid': False, 'errors': ['Empty schedule']}

        errors = []

        # Check if final balance is exactly zero
        final_balance = schedule[-1]['remaining_balance']
        if final_balance != 0.00:
            errors.append(f"Final balance is not zero: ₹{final_balance:.2f}")

        # Check if sum of principal payments equals original loan amount
        total_principal = sum(payment['principal_amount'] for payment in schedule)
        expected_principal = self.outstanding_amount
        principal_diff = abs(total_principal - expected_principal)

        # Allow for reasonable rounding differences (up to ₹0.10 for floating-point precision)
        if principal_diff > 0.10:
            errors.append(f"Principal sum mismatch: Expected ₹{expected_principal:.2f}, Got ₹{total_principal:.2f}")

        # Check if all payment periods are covered using net_tenure
        expected_payments = self.net_tenure
        actual_payments = len(schedule)

        if actual_payments != expected_payments:
            errors.append(f"Payment count mismatch: Expected {expected_payments}, Got {actual_payments}")

        # Check for negative values
        for i, payment in enumerate(schedule):
            if payment['principal_amount'] < 0:
                errors.append(f"Negative principal in payment {i+1}: ₹{payment['principal_amount']:.2f}")
            if payment['interest_amount'] < 0:
                errors.append(f"Negative interest in payment {i+1}: ₹{payment['interest_amount']:.2f}")
            if payment['remaining_balance'] < 0:
                errors.append(f"Negative balance in payment {i+1}: ₹{payment['remaining_balance']:.2f}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'total_principal': total_principal,
            'total_interest': sum(payment['interest_amount'] for payment in schedule),
            'total_payments': len(schedule)
        }

    def add_months_to_date(self, start_date, months):
        """Add months to a date, handling month overflow"""
        try:
            from dateutil.relativedelta import relativedelta
            return start_date + relativedelta(months=months)
        except ImportError:
            # Fallback method if dateutil is not available
            year = start_date.year
            month = start_date.month + months
            day = start_date.day

            # Handle month overflow
            while month > 12:
                year += 1
                month -= 12
            while month < 1:
                year -= 1
                month += 12

            # Handle day overflow (e.g., Jan 31 + 1 month = Feb 28/29)
            import calendar
            max_day = calendar.monthrange(year, month)[1]
            if day > max_day:
                day = max_day

            return date(year, month, day)

    def get_loan_summary_stats(self):
        """Get summary statistics for the loan"""
        schedule = self.generate_amortization_schedule()

        if not schedule:
            return {
                'total_payments': 0,
                'total_interest': 0.0,
                'total_principal': 0.0,
                'total_amount_payable': 0.0,
                'average_monthly_interest': 0.0,
                'interest_percentage': 0.0
            }

        total_interest = sum(payment['interest_amount'] for payment in schedule)
        total_principal = sum(payment['principal_amount'] for payment in schedule)
        total_amount_payable = total_interest + total_principal

        return {
            'total_payments': len(schedule),
            'total_interest': round(total_interest, 2),
            'total_principal': round(total_principal, 2),
            'total_amount_payable': round(total_amount_payable, 2),
            'average_monthly_interest': round(total_interest / len(schedule), 2) if schedule else 0.0,
            'interest_percentage': round((total_interest / total_amount_payable * 100), 2) if total_amount_payable > 0 else 0.0
        }

    def get_chart_data(self):
        """Generate data for various chart visualizations"""
        schedule = self.generate_amortization_schedule()
        stats = self.get_loan_summary_stats()

        if not schedule:
            return {
                'pie_chart_data': [],
                'line_chart_data': [],
                'balance_chart_data': [],
                'bar_chart_data': []
            }

        # Pie chart data (Principal vs Interest)
        pie_data = [
            ('Principal', stats['total_principal']),
            ('Interest', stats['total_interest'])
        ]

        # Line chart data (Payment amounts over time)
        line_data = [(payment['payment_date'], payment['total_payment']) for payment in schedule]

        # Balance reduction chart data
        balance_data = [(payment['payment_date'], payment['remaining_balance']) for payment in schedule]

        # Bar chart data (Monthly Principal vs Interest)
        bar_data = []
        for payment in schedule[:min(24, len(schedule))]:  # Show first 24 months
            bar_data.append({
                'month': payment['payment_date'].strftime('%b %Y'),
                'principal': payment['principal_amount'],
                'interest': payment['interest_amount']
            })

        return {
            'pie_chart_data': pie_data,
            'line_chart_data': line_data,
            'balance_chart_data': balance_data,
            'bar_chart_data': bar_data
        }


@dataclass
class LoanPayment:
    """Data class for loan payment history tracking"""
    id: Optional[int] = None
    loan_id: int = 0  # Reference to the parent loan
    payment_date: Optional[Union[str, datetime, date]] = None
    principal_amount: float = 0.0  # Amount paid towards principal
    interest_amount: float = 0.0  # Amount paid towards interest
    total_payment: float = 0.0  # Total payment amount (principal + interest)
    remaining_balance: float = 0.0  # Remaining loan balance after this payment
    payment_method: str = "Cash"  # Payment method (Cash, Check, Bank Transfer, etc.)
    notes: str = ""  # Optional notes/comments
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

        # Handle payment_date conversion
        if self.payment_date and isinstance(self.payment_date, str):
            try:
                self.payment_date = datetime.strptime(self.payment_date, '%Y-%m-%d').date()
            except ValueError:
                try:
                    self.payment_date = datetime.strptime(self.payment_date, '%Y-%m-%d %H:%M:%S').date()
                except ValueError:
                    self.payment_date = date.today()
        elif isinstance(self.payment_date, datetime):
            self.payment_date = self.payment_date.date()
        elif self.payment_date is None:
            self.payment_date = date.today()

    def validate(self) -> List[str]:
        """Validate loan payment data"""
        errors = []

        if not self.loan_id or self.loan_id <= 0:
            errors.append("Valid loan ID is required")

        if not self.payment_date:
            errors.append("Payment date is required")

        if self.total_payment <= 0:
            errors.append("Total payment amount must be greater than 0")

        if self.principal_amount < 0:
            errors.append("Principal amount cannot be negative")

        if self.interest_amount < 0:
            errors.append("Interest amount cannot be negative")

        if abs(self.total_payment - (self.principal_amount + self.interest_amount)) > 0.01:
            errors.append("Total payment must equal principal + interest amounts")

        if self.remaining_balance < 0:
            errors.append("Remaining balance cannot be negative")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'loan_id': self.loan_id,
            'payment_date': self.payment_date.strftime('%Y-%m-%d') if self.payment_date else '',
            'principal_amount': self.principal_amount,
            'interest_amount': self.interest_amount,
            'total_payment': self.total_payment,
            'remaining_balance': self.remaining_balance,
            'payment_method': self.payment_method,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else '',
            'last_updated': self.last_updated.isoformat() if self.last_updated else ''
        }


@dataclass
class MutualFundPurchaseHistory:
    """Data class for mutual fund purchase history tracking"""
    id: Optional[int] = None
    fund_id: int = 0  # Reference to the parent mutual fund/stock
    transaction_type: str = "Buy"  # Buy, Sell, Dividend, etc.
    transaction_date: Optional[Union[str, datetime, date]] = None
    units: float = 0.0  # Number of units bought/sold
    unit_price: float = 0.0  # Price per unit at transaction
    total_amount: float = 0.0  # Total transaction amount
    fees: float = 0.0  # Transaction fees/charges
    net_amount: float = 0.0  # Net amount (total_amount + fees for buy, total_amount - fees for sell)
    notes: str = ""  # Optional notes/comments
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

        # Handle transaction_date conversion
        if self.transaction_date and isinstance(self.transaction_date, str):
            try:
                self.transaction_date = datetime.strptime(self.transaction_date, '%Y-%m-%d').date()
            except ValueError:
                self.transaction_date = date.today()
        elif isinstance(self.transaction_date, datetime):
            self.transaction_date = self.transaction_date.date()
        elif self.transaction_date is None:
            self.transaction_date = date.today()

        # Calculate net amount if not provided
        if self.net_amount == 0.0 and self.total_amount > 0:
            if self.transaction_type.lower() == "buy":
                self.net_amount = self.total_amount + self.fees
            else:  # sell
                self.net_amount = self.total_amount - self.fees

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'fund_id': self.fund_id,
            'transaction_type': self.transaction_type,
            'transaction_date': self.transaction_date.strftime('%Y-%m-%d') if self.transaction_date else '',
            'units': self.units,
            'unit_price': self.unit_price,
            'total_amount': self.total_amount,
            'fees': self.fees,
            'net_amount': self.net_amount,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else '',
            'last_updated': self.last_updated.isoformat() if self.last_updated else ''
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MutualFundPurchaseHistory':
        """Create instance from dictionary"""
        # Handle date parsing
        transaction_date = None
        if data.get('transaction_date'):
            try:
                transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
            except ValueError:
                transaction_date = date.today()

        created_date = None
        if data.get('created_date'):
            try:
                created_date = datetime.fromisoformat(data['created_date'])
            except ValueError:
                created_date = datetime.now()

        last_updated = None
        if data.get('last_updated'):
            try:
                last_updated = datetime.fromisoformat(data['last_updated'])
            except ValueError:
                last_updated = datetime.now()

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            fund_id=int(data.get('fund_id', 0)),
            transaction_type=data.get('transaction_type', 'Buy'),
            transaction_date=transaction_date,
            units=float(data.get('units', 0.0)),
            unit_price=float(data.get('unit_price', 0.0)),
            total_amount=float(data.get('total_amount', 0.0)),
            fees=float(data.get('fees', 0.0)),
            net_amount=float(data.get('net_amount', 0.0)),
            notes=data.get('notes', ''),
            created_date=created_date,
            last_updated=last_updated
        )


@dataclass
class AllocationSettings:
    """Data class for storing custom allocation percentages"""
    id: Optional[int] = None
    category: str = ""  # Equity, Debt, Gold, Loan, etc.
    sub_category: str = ""  # Large Cap, ELSS, Corporate, etc.
    geographic_classification: str = ""  # Indian, International
    allocation_percent: float = 0.0  # Custom allocation percentage
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class MonthlySavingsTarget:
    """Data class for storing monthly savings target amount"""
    id: Optional[int] = None
    target_amount: float = 3000.0  # Default to ₹3,000
    currency: str = "₹"
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    notes: str = ""

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'target_amount': self.target_amount,
            'currency': self.currency,
            'created_date': self.created_date.isoformat() if self.created_date else '',
            'last_updated': self.last_updated.isoformat() if self.last_updated else '',
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonthlySavingsTarget':
        """Create from dictionary (CSV data)"""
        # Parse dates
        created_date = None
        if data.get('created_date'):
            try:
                created_date = datetime.fromisoformat(data['created_date'])
            except:
                created_date = datetime.now()

        last_updated = None
        if data.get('last_updated'):
            try:
                last_updated = datetime.fromisoformat(data['last_updated'])
            except:
                last_updated = datetime.now()

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            target_amount=float(data.get('target_amount', 3000.0)),
            currency=data.get('currency', '₹'),
            created_date=created_date,
            last_updated=last_updated,
            notes=data.get('notes', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'category': self.category,
            'sub_category': self.sub_category,
            'geographic_classification': self.geographic_classification,
            'allocation_percent': self.allocation_percent,
            'created_date': self.created_date.isoformat() if self.created_date else '',
            'last_updated': self.last_updated.isoformat() if self.last_updated else ''
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AllocationSettings':
        """Create instance from dictionary"""
        # Handle date parsing
        created_date = None
        if data.get('created_date'):
            try:
                created_date = datetime.fromisoformat(data['created_date'])
            except ValueError:
                created_date = datetime.now()

        last_updated = None
        if data.get('last_updated'):
            try:
                last_updated = datetime.fromisoformat(data['last_updated'])
            except ValueError:
                last_updated = datetime.now()

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            category=data.get('category', ''),
            sub_category=data.get('sub_category', ''),
            geographic_classification=data.get('geographic_classification', ''),
            allocation_percent=float(data.get('allocation_percent', 0.0)),
            created_date=created_date,
            last_updated=last_updated
        )


@dataclass
class OwnedAsset:
    """Data class for storing owned physical assets"""
    id: Optional[int] = None
    name: str = ""  # Asset name (e.g., "Primary Residence", "Honda City", "Gold Jewelry")
    category: str = ""  # Real Estate, Vehicle, Gold, Cash, Bank Account, etc.
    sub_category: str = ""  # House, Apartment, Car, Bike, Jewelry, Savings, Current, etc.
    description: str = ""  # Additional details about the asset
    purchase_date: Optional[datetime] = None  # When the asset was acquired
    purchase_value: float = 0.0  # Original purchase price
    current_value: float = 0.0  # Current market value
    location: str = ""  # Where the asset is located
    notes: str = ""  # Additional notes
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'sub_category': self.sub_category,
            'description': self.description,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else '',
            'purchase_value': self.purchase_value,
            'current_value': self.current_value,
            'location': self.location,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else '',
            'last_updated': self.last_updated.isoformat() if self.last_updated else ''
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OwnedAsset':
        """Create instance from dictionary"""
        # Parse dates
        purchase_date = None
        if data.get('purchase_date'):
            try:
                purchase_date = datetime.fromisoformat(data['purchase_date'])
            except (ValueError, TypeError):
                purchase_date = None

        created_date = None
        if data.get('created_date'):
            try:
                created_date = datetime.fromisoformat(data['created_date'])
            except (ValueError, TypeError):
                created_date = datetime.now()

        last_updated = None
        if data.get('last_updated'):
            try:
                last_updated = datetime.fromisoformat(data['last_updated'])
            except (ValueError, TypeError):
                last_updated = datetime.now()

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            name=data.get('name', ''),
            category=data.get('category', ''),
            sub_category=data.get('sub_category', ''),
            description=data.get('description', ''),
            purchase_date=purchase_date,
            purchase_value=float(data.get('purchase_value', 0.0)),
            current_value=float(data.get('current_value', 0.0)),
            location=data.get('location', ''),
            notes=data.get('notes', ''),
            created_date=created_date,
            last_updated=last_updated
        )


@dataclass
class MutualFundStock:
    """Data class for mutual fund and stock tracking"""
    id: Optional[int] = None
    name: str = ""
    symbol: str = ""
    category: str = ""
    sub_category: str = ""
    geographic_classification: str = "Indian"  # Indian or International
    unit_price: float = 0.0  # Purchase/historical price
    current_price: float = 0.0  # Current market price
    units: float = 0.0
    amount: float = 0.0  # Original investment amount
    current_amount: float = 0.0  # Current market value
    allocation_percent: float = 0.0
    remarks: str = ""
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    price_last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

        # Auto-calculate amount if not provided
        if self.amount == 0.0 and self.unit_price > 0 and self.units > 0:
            self.amount = self.unit_price * self.units

        # Auto-calculate current amount if current price is available
        if self.current_price is not None and self.current_price > 0 and self.units > 0:
            self.current_amount = self.current_price * self.units

    def update_current_price(self, new_price: float):
        """Update current price and recalculate current amount"""
        self.current_price = new_price
        self.price_last_updated = datetime.now()
        if self.units > 0:
            self.current_amount = self.current_price * self.units

    def get_profit_loss(self) -> float:
        """Calculate profit/loss amount"""
        if (self.current_amount is not None and self.current_amount > 0 and
            self.amount is not None and self.amount > 0):
            return self.current_amount - self.amount
        return 0.0

    def get_profit_loss_percentage(self) -> float:
        """Calculate profit/loss percentage"""
        if self.amount > 0:
            return (self.get_profit_loss() / self.amount) * 100
        return 0.0

    def is_price_stale(self, max_age_hours: int = 24) -> bool:
        """Check if current price is stale (older than max_age_hours)"""
        if not self.price_last_updated:
            return True
        age = datetime.now() - self.price_last_updated
        return age.total_seconds() > (max_age_hours * 3600)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'name': self.name,
            'symbol': self.symbol,
            'category': self.category,
            'sub_category': self.sub_category,
            'geographic_classification': self.geographic_classification,
            'unit_price': self.unit_price,
            'current_price': self.current_price,
            'units': self.units,
            'amount': self.amount,
            'current_amount': self.current_amount,
            'allocation_percent': self.allocation_percent,
            'remarks': self.remarks,
            'created_date': self.created_date.isoformat() if self.created_date else '',
            'last_updated': self.last_updated.isoformat() if self.last_updated else '',
            'price_last_updated': self.price_last_updated.isoformat() if self.price_last_updated else ''
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MutualFundStock':
        """Create instance from dictionary"""
        # Handle date parsing
        created_date = None
        if data.get('created_date'):
            try:
                created_date = datetime.fromisoformat(data['created_date'])
            except ValueError:
                created_date = datetime.now()

        last_updated = None
        if data.get('last_updated'):
            try:
                last_updated = datetime.fromisoformat(data['last_updated'])
            except ValueError:
                last_updated = datetime.now()

        price_last_updated = None
        if data.get('price_last_updated'):
            try:
                price_last_updated = datetime.fromisoformat(data['price_last_updated'])
            except ValueError:
                price_last_updated = None

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            name=data.get('name', ''),
            symbol=data.get('symbol', ''),
            category=data.get('category', ''),
            sub_category=data.get('sub_category', ''),
            geographic_classification=data.get('geographic_classification', 'Indian'),
            unit_price=float(data.get('unit_price', 0.0)),
            current_price=float(data.get('current_price', 0.0)),
            units=float(data.get('units', 0.0)),
            amount=float(data.get('amount', 0.0)),
            current_amount=float(data.get('current_amount', 0.0)),
            allocation_percent=float(data.get('allocation_percent', 0.0)),
            remarks=data.get('remarks', ''),
            created_date=created_date,
            last_updated=last_updated,
            price_last_updated=price_last_updated
        )


@dataclass
class PortfolioSnapshot:
    """Data class for portfolio snapshots"""
    id: Optional[int] = None
    category: str = ""
    item: str = ""
    amount: float = 0.0
    snapshot_date: Optional[Union[str, datetime, date]] = None
    created_date: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.created_date is None:
            self.created_date = datetime.now()

        # Handle snapshot_date conversion
        if self.snapshot_date and isinstance(self.snapshot_date, str):
            try:
                self.snapshot_date = datetime.strptime(self.snapshot_date, '%Y-%m-%d').date()
            except ValueError:
                self.snapshot_date = date.today()
        elif isinstance(self.snapshot_date, datetime):
            self.snapshot_date = self.snapshot_date.date()
        elif self.snapshot_date is None:
            self.snapshot_date = date.today()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'category': self.category,
            'item': self.item,
            'amount': self.amount,
            'snapshot_date': self.snapshot_date.strftime('%Y-%m-%d') if self.snapshot_date else '',
            'created_date': self.created_date.isoformat() if self.created_date else ''
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioSnapshot':
        """Create instance from dictionary"""
        # Handle date parsing
        created_date = None
        if data.get('created_date'):
            try:
                created_date = datetime.fromisoformat(data['created_date'])
            except ValueError:
                created_date = datetime.now()

        snapshot_date = None
        if data.get('snapshot_date'):
            try:
                snapshot_date = datetime.strptime(data['snapshot_date'], '%Y-%m-%d').date()
            except ValueError:
                snapshot_date = date.today()

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            category=data.get('category', ''),
            item=data.get('item', ''),
            amount=float(data.get('amount', 0.0)),
            snapshot_date=snapshot_date,
            created_date=created_date
        )


@dataclass
class TransactionHistory:
    """Data class for tracking portfolio transaction history"""
    id: Optional[int] = None
    asset_name: str = ""
    symbol: str = ""
    transaction_date: Optional[datetime] = None
    units_purchased: float = 0.0
    price_per_unit: float = 0.0
    total_amount: float = 0.0
    transaction_type: str = "BUY"  # BUY, SELL, UPDATE
    previous_units: float = 0.0
    new_units: float = 0.0
    notes: str = ""
    created_date: Optional[datetime] = None
    # Additional fields to match CSV structure
    fees: float = 0.0
    net_amount: float = 0.0
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.transaction_date is None:
            self.transaction_date = datetime.now()
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

        # Calculate total amount if not provided
        if self.total_amount == 0.0 and self.units_purchased > 0 and self.price_per_unit > 0:
            self.total_amount = self.units_purchased * self.price_per_unit

        # Calculate net amount if not provided (total_amount + fees for buy, total_amount - fees for sell)
        if self.net_amount == 0.0 and self.total_amount > 0:
            if self.transaction_type.upper() == "BUY":
                self.net_amount = self.total_amount + self.fees
            else:
                self.net_amount = self.total_amount - self.fees

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'asset_name': self.asset_name,
            'asset_symbol': self.symbol,  # Map symbol to asset_symbol for CSV consistency
            'transaction_type': self.transaction_type,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else '',
            'units_purchased': self.units_purchased,
            'price_per_unit': self.price_per_unit,
            'total_amount': self.total_amount,
            'fees': self.fees,
            'net_amount': self.net_amount,
            'previous_units': self.previous_units,
            'new_units': self.new_units,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else '',
            'last_updated': self.last_updated.isoformat() if self.last_updated else ''
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransactionHistory':
        """Create instance from dictionary"""
        # Handle date parsing
        transaction_date = None
        if data.get('transaction_date'):
            try:
                transaction_date = datetime.fromisoformat(data['transaction_date'])
            except ValueError:
                transaction_date = datetime.now()

        created_date = None
        if data.get('created_date'):
            try:
                created_date = datetime.fromisoformat(data['created_date'])
            except ValueError:
                created_date = datetime.now()

        # Handle last_updated date parsing
        last_updated = None
        if data.get('last_updated'):
            try:
                last_updated = datetime.fromisoformat(data['last_updated'])
            except ValueError:
                last_updated = datetime.now()

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            asset_name=data.get('asset_name', ''),
            symbol=data.get('symbol', ''),
            transaction_date=transaction_date,
            units_purchased=float(data.get('units_purchased', 0.0)),
            price_per_unit=float(data.get('price_per_unit', 0.0)),
            total_amount=float(data.get('total_amount', 0.0)),
            transaction_type=data.get('transaction_type', 'BUY'),
            previous_units=float(data.get('previous_units', 0.0)),
            new_units=float(data.get('new_units', 0.0)),
            notes=data.get('notes', ''),
            created_date=created_date,
            fees=float(data.get('fees', 0.0)),
            net_amount=float(data.get('net_amount', 0.0)),
            last_updated=last_updated
        )


@dataclass
class PortfolioGrowthSnapshot:
    """Data class for tracking portfolio growth over time"""
    id: Optional[int] = None
    snapshot_date: Optional[datetime] = None
    total_portfolio_value: float = 0.0
    total_invested: float = 0.0
    total_gains: float = 0.0
    gains_percentage: float = 0.0
    asset_count: int = 0
    notes: str = ""
    created_date: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.snapshot_date is None:
            self.snapshot_date = datetime.now()
        if self.created_date is None:
            self.created_date = datetime.now()


@dataclass
class IndividualInvestmentGrowth:
    """Data class for tracking individual investment growth over time"""
    id: Optional[int] = None
    snapshot_date: Optional[datetime] = None
    investment_name: str = ""
    investment_symbol: str = ""
    units: float = 0.0
    unit_price: float = 0.0
    current_value: float = 0.0
    invested_amount: float = 0.0
    notes: str = ""
    created_date: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.id is None:
            self.id = int(datetime.now().timestamp() * 1000000)  # Unique ID based on timestamp
        if self.snapshot_date is None:
            self.snapshot_date = datetime.now()
        if self.created_date is None:
            self.created_date = datetime.now()

    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary"""
        # Handle date parsing
        snapshot_date = None
        if data.get('snapshot_date'):
            if isinstance(data['snapshot_date'], str):
                try:
                    snapshot_date = datetime.fromisoformat(data['snapshot_date'].replace('Z', '+00:00'))
                except ValueError:
                    try:
                        snapshot_date = datetime.strptime(data['snapshot_date'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        snapshot_date = datetime.now()
            elif isinstance(data['snapshot_date'], datetime):
                snapshot_date = data['snapshot_date']

        created_date = None
        if data.get('created_date'):
            if isinstance(data['created_date'], str):
                try:
                    created_date = datetime.fromisoformat(data['created_date'].replace('Z', '+00:00'))
                except ValueError:
                    try:
                        created_date = datetime.strptime(data['created_date'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        created_date = datetime.now()
            elif isinstance(data['created_date'], datetime):
                created_date = data['created_date']

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            snapshot_date=snapshot_date,
            investment_name=data.get('investment_name', ''),
            investment_symbol=data.get('investment_symbol', ''),
            units=float(data.get('units', 0.0)),
            unit_price=float(data.get('unit_price', 0.0)),
            current_value=float(data.get('current_value', 0.0)),
            invested_amount=float(data.get('invested_amount', 0.0)),
            notes=data.get('notes', ''),
            created_date=created_date
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else '',
            'investment_name': self.investment_name,
            'investment_symbol': self.investment_symbol,
            'units': self.units,
            'unit_price': self.unit_price,
            'current_value': self.current_value,
            'invested_amount': self.invested_amount,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else ''
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndividualInvestmentGrowth':
        """Create IndividualInvestmentGrowth from dictionary"""
        # Parse dates
        snapshot_date = None
        if data.get('snapshot_date'):
            try:
                snapshot_date = datetime.fromisoformat(data['snapshot_date'])
            except (ValueError, TypeError):
                snapshot_date = datetime.now()

        created_date = None
        if data.get('created_date'):
            try:
                created_date = datetime.fromisoformat(data['created_date'])
            except (ValueError, TypeError):
                created_date = datetime.now()

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            snapshot_date=snapshot_date,
            investment_name=data.get('investment_name', ''),
            investment_symbol=data.get('investment_symbol', ''),
            units=float(data.get('units', 0.0)),
            unit_price=float(data.get('unit_price', 0.0)),
            current_value=float(data.get('current_value', 0.0)),
            invested_amount=float(data.get('invested_amount', 0.0)),
            notes=data.get('notes', ''),
            created_date=created_date
        )

        # Calculate gains and percentage if not provided
        if self.total_gains == 0.0 and self.total_portfolio_value > 0 and self.total_invested > 0:
            self.total_gains = self.total_portfolio_value - self.total_invested

        if self.gains_percentage == 0.0 and self.total_invested > 0:
            self.gains_percentage = (self.total_gains / self.total_invested) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        return {
            'id': self.id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else '',
            'total_portfolio_value': self.total_portfolio_value,
            'total_invested': self.total_invested,
            'total_gains': self.total_gains,
            'gains_percentage': self.gains_percentage,
            'asset_count': self.asset_count,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else ''
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioGrowthSnapshot':
        """Create instance from dictionary"""
        # Handle date parsing
        snapshot_date = None
        if data.get('snapshot_date'):
            try:
                snapshot_date = datetime.fromisoformat(data['snapshot_date'])
            except ValueError:
                snapshot_date = datetime.now()

        created_date = None
        if data.get('created_date'):
            try:
                created_date = datetime.fromisoformat(data['created_date'])
            except ValueError:
                created_date = datetime.now()

        return cls(
            id=int(data.get('id', 0)) if data.get('id') else None,
            snapshot_date=snapshot_date,
            total_portfolio_value=float(data.get('total_portfolio_value', 0.0)),
            total_invested=float(data.get('total_invested', 0.0)),
            total_gains=float(data.get('total_gains', 0.0)),
            gains_percentage=float(data.get('gains_percentage', 0.0)),
            asset_count=int(data.get('asset_count', 0)),
            notes=data.get('notes', ''),
            created_date=created_date
        )


class InvestmentCSVManager:
    """CSV data manager for all Investment module data"""

    def __init__(self, data_directory: str):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.data_directory = Path(data_directory)

        # If data_directory already ends with 'investments', use it directly
        # Otherwise, append 'investments' to create the investments subdirectory
        if self.data_directory.name == "investments":
            self.investments_dir = self.data_directory
        else:
            self.investments_dir = self.data_directory / "investments"

        # Create investments directory if it doesn't exist
        self.investments_dir.mkdir(parents=True, exist_ok=True)

        # Define CSV file paths
        self.csv_files = {
            'portfolio_tracker': self.investments_dir / 'portfolio_tracker.csv',
            'current_resources': self.investments_dir / 'current_resources.csv',
            'asset_liability': self.investments_dir / 'asset_liability.csv',
            'financial_goals': self.investments_dir / 'financial_goals.csv',
            'insurance_policies': self.investments_dir / 'insurance_policies.csv',
            'lic_policies': self.investments_dir / 'lic_policies.csv',
            'loan_details': self.investments_dir / 'loan_details.csv',
            'loan_payment_history': self.investments_dir / 'loan_payment_history.csv',
            'mutual_funds_stocks': self.investments_dir / 'mutual_funds_stocks.csv',
            'mutual_fund_purchase_history': self.investments_dir / 'mutual_fund_purchase_history.csv',
            'monthly_savings_target': self.investments_dir / 'monthly_savings_target.csv',
            'transaction_history': self.investments_dir / 'transaction_history.csv',
            'portfolio_growth_snapshots': self.investments_dir / 'portfolio_growth_snapshots.csv',
            'individual_investment_growth': self.investments_dir / 'individual_investment_growth.csv',
            'fund_categories': self.investments_dir / 'fund_categories.csv',
            'portfolio_analysis': self.investments_dir / 'portfolio_analysis.csv',
            'portfolio_snapshots': self.investments_dir / 'portfolio_snapshots.csv',
            'allocation_settings': self.investments_dir / 'allocation_settings.csv',
            'owned_assets': self.investments_dir / 'owned_assets.csv'
        }

        self.logger.info(f"InvestmentCSVManager initialized with directory: {self.investments_dir}")

    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """Convert dataclass to dictionary with proper type handling"""
        if not hasattr(obj, '__dataclass_fields__'):
            return obj

        result = {}
        for field in fields(obj):
            try:
                value = getattr(obj, field.name)

                # Handle different data types for CSV storage
                if isinstance(value, datetime):
                    result[field.name] = value.isoformat()
                elif isinstance(value, date):
                    result[field.name] = value.isoformat()
                elif value is None:
                    result[field.name] = ''
                elif isinstance(value, float):
                    # Handle floating point precision issues
                    if abs(value) > 1e15:  # Very large numbers
                        result[field.name] = f"{value:.2e}"  # Scientific notation
                    else:
                        result[field.name] = round(value, 6)  # Limit precision to 6 decimal places
                elif isinstance(value, str):
                    # Handle special characters that might cause CSV issues
                    cleaned_value = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                    # Remove any null bytes that could cause issues
                    cleaned_value = cleaned_value.replace('\x00', '')
                    result[field.name] = cleaned_value
                else:
                    result[field.name] = value

            except Exception as e:
                self.logger.warning(f"Error processing field {field.name}: {e}")
                result[field.name] = ''  # Use empty string as fallback

        return result

    def _dict_to_dataclass(self, data_dict: Dict[str, Any], dataclass_type):
        """Convert dictionary to dataclass with proper type handling"""
        try:
            # Handle column mapping for TransactionHistory
            if dataclass_type.__name__ == 'TransactionHistory':
                # Map CSV column names to dataclass field names
                if 'asset_symbol' in data_dict and 'symbol' not in data_dict:
                    data_dict['symbol'] = data_dict['asset_symbol']

            # Handle type conversions
            converted_data = {}
            for field in fields(dataclass_type):
                field_name = field.name
                field_type = field.type
                value = data_dict.get(field_name, '')

                # Handle None/empty values
                if value == '' or value is None:
                    if field.default != dataclass_type.__dataclass_fields__[field_name].default:
                        converted_data[field_name] = field.default
                    else:
                        converted_data[field_name] = None
                    continue

                # Type-specific conversions
                if field_type == int or field_type == Optional[int]:
                    converted_data[field_name] = int(float(value)) if value else 0
                elif field_type == float or field_type == Optional[float]:
                    converted_data[field_name] = float(value) if value else 0.0
                elif field_type == datetime or field_type == Optional[datetime]:
                    if isinstance(value, str) and value:
                        converted_data[field_name] = datetime.fromisoformat(value)
                    else:
                        converted_data[field_name] = datetime.now()
                elif field_type == date or field_type == Optional[date] or field_type == Optional[Union[str, datetime, date]]:
                    if isinstance(value, str) and value:
                        try:
                            converted_data[field_name] = datetime.fromisoformat(value).date()
                        except:
                            converted_data[field_name] = date.today()
                    else:
                        converted_data[field_name] = date.today()
                else:
                    converted_data[field_name] = str(value) if value else ''

            return dataclass_type(**converted_data)

        except Exception as e:
            self.logger.error(f"Error converting dict to {dataclass_type.__name__}: {e}")
            return dataclass_type()

    def save_data(self, data_type: str, data_list: List[Any]) -> bool:
        """Save data list to CSV file"""
        try:
            if data_type not in self.csv_files:
                self.logger.error(f"Unknown data type: {data_type}")
                return False

            csv_file = self.csv_files[data_type]

            if not data_list:
                # Create empty file with headers if no data
                if data_type == 'current_resources':
                    headers = ['id', 'category', 'amount_lakhs', 'allocation_percent', 'created_date', 'last_updated']
                elif data_type == 'asset_liability':
                    headers = ['id', 'item_name', 'item_type', 'category', 'percentage', 'created_date', 'last_updated']
                elif data_type == 'financial_goals':
                    headers = ['id', 'goal_name', 'current_cost', 'years_until_goal', 'future_value',
                              'monthly_sip_required', 'time_horizon', 'action_plan', 'created_date', 'last_updated']
                elif data_type == 'insurance_policies':
                    headers = ['id', 'policy_name', 'policy_type', 'policy_number', 'valid_till',
                              'premium_amount', 'premium_due_date', 'amount_insured', 'nominee', 'remarks',
                              'created_date', 'last_updated']
                elif data_type == 'lic_policies':
                    headers = ['id', 'policy_holder_name', 'policy_number', 'policy_type', 'plan_name',
                              'premium_amount', 'premium_frequency', 'premium_due_date', 'policy_start_date',
                              'maturity_date', 'sum_assured', 'bonus_amount', 'surrender_value', 'loan_amount',
                              'nominee_name', 'nominee_relationship', 'current_status', 'agent_name', 'agent_code',
                              'branch_office', 'last_premium_paid_date', 'next_premium_due_date',
                              'policy_document_number', 'remarks', 'base_sum_assured', 'additional_coverage',
                              'rider_coverage', 'loyalty_addition', 'terminal_bonus', 'created_date', 'last_updated']
                elif data_type == 'loan_details':
                    headers = ['id', 'loan_name', 'outstanding_amount', 'interest_rate',
                              'remaining_period_months', 'created_date', 'last_updated']
                elif data_type == 'mutual_funds_stocks':
                    headers = ['id', 'name', 'symbol', 'category', 'sub_category', 'unit_price', 'current_price',
                              'units', 'amount', 'current_amount', 'allocation_percent', 'remarks',
                              'created_date', 'last_updated', 'price_last_updated']
                elif data_type == 'portfolio_snapshots':
                    headers = ['id', 'category', 'item', 'amount', 'snapshot_date', 'created_date']
                elif data_type == 'portfolio_growth_snapshots':
                    headers = ['id', 'snapshot_date', 'total_portfolio_value', 'total_invested', 'total_gains',
                              'gains_percentage', 'asset_count', 'notes', 'created_date']
                elif data_type == 'individual_investment_growth':
                    headers = ['id', 'snapshot_date', 'investment_name', 'investment_symbol', 'units',
                              'unit_price', 'current_value', 'invested_amount', 'notes', 'created_date']
                else:
                    headers = ['id']

                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                return True

            # Convert dataclass objects to dictionaries with error handling
            dict_data = []
            for i, item in enumerate(data_list):
                try:
                    converted_item = self._dataclass_to_dict(item)
                    dict_data.append(converted_item)
                except Exception as e:
                    self.logger.error(f"Error converting item {i} to dict: {e}")
                    # Skip problematic items rather than crashing
                    continue

            if not dict_data:
                self.logger.warning(f"No valid data to save for {data_type}")
                return False

            # Create backup of existing file if it exists
            backup_file = None
            if csv_file.exists():
                backup_file = csv_file.with_suffix('.backup')
                try:
                    import shutil
                    shutil.copy2(csv_file, backup_file)
                    self.logger.debug(f"Created backup: {backup_file}")
                except Exception as e:
                    self.logger.warning(f"Could not create backup: {e}")

            # Write to temporary file first, then rename for atomic operation
            temp_file = csv_file.with_suffix('.tmp')
            try:
                with open(temp_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = dict_data[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(dict_data)

                # Verify the temporary file was written correctly
                if temp_file.exists() and temp_file.stat().st_size > 0:
                    # Replace original file with temporary file
                    if csv_file.exists():
                        csv_file.unlink()
                    temp_file.rename(csv_file)

                    # Clean up backup if save was successful
                    if backup_file and backup_file.exists():
                        backup_file.unlink()

                    self.logger.info(f"Successfully saved {len(dict_data)} records to {csv_file}")
                    return True
                else:
                    raise Exception("Temporary file was not created properly")

            except Exception as write_error:
                self.logger.error(f"Error writing to temporary file: {write_error}")

                # Clean up temporary file
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except:
                        pass

                # Restore backup if available
                if backup_file and backup_file.exists():
                    try:
                        backup_file.rename(csv_file)
                        self.logger.info("Restored backup file after write failure")
                    except Exception as restore_error:
                        self.logger.error(f"Could not restore backup: {restore_error}")

                raise write_error

        except Exception as e:
            self.logger.error(f"Error saving {data_type} data: {e}")
            return False

    def load_data(self, data_type: str, dataclass_type) -> List[Any]:
        """Load data from CSV file and convert to dataclass objects"""
        try:
            if data_type not in self.csv_files:
                self.logger.error(f"Unknown data type: {data_type}")
                return []

            csv_file = self.csv_files[data_type]

            if not csv_file.exists():
                self.logger.info(f"CSV file {csv_file} does not exist, returning empty list")
                return []

            data_list = []
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Assign unique ID if not present
                        if 'id' not in row or not row['id']:
                            row['id'] = row_num

                        obj = self._dict_to_dataclass(row, dataclass_type)
                        data_list.append(obj)
                    except Exception as e:
                        self.logger.error(f"Error processing row {row_num} in {csv_file}: {e}")
                        continue

            self.logger.info(f"Loaded {len(data_list)} records from {csv_file}")
            return data_list

        except Exception as e:
            self.logger.error(f"Error loading {data_type} data: {e}")
            return []

    def backup_data(self) -> bool:
        """Create backup of all CSV files"""
        try:
            backup_dir = self.investments_dir / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for data_type, csv_file in self.csv_files.items():
                if csv_file.exists():
                    backup_file = backup_dir / f"{data_type}_{timestamp}.csv"
                    backup_file.write_bytes(csv_file.read_bytes())

            self.logger.info(f"Backup created with timestamp: {timestamp}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False
