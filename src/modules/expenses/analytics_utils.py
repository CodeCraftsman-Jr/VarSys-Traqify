"""
Expense Analytics Utilities
Provides utility functions for expense data analysis and insights generation
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple


def calculate_expense_statistics(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive expense statistics"""
    if data.empty:
        return {
            'total_expenses': 0,
            'average_expense': 0,
            'median_expense': 0,
            'transaction_count': 0,
            'unique_categories': 0,
            'date_range_days': 0,
            'daily_average': 0,
            'largest_expense': 0,
            'smallest_expense': 0,
            'spending_variance': 0,
            'top_category': 'N/A',
            'most_frequent_mode': 'N/A'
        }
    
    # Ensure date column is datetime
    if 'date' in data.columns:
        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])
    
    # Basic statistics
    total_expenses = data['amount'].sum()
    average_expense = data['amount'].mean()
    median_expense = data['amount'].median()
    transaction_count = len(data)
    unique_categories = data['category'].nunique() if 'category' in data.columns else 0
    
    # Date range analysis
    if 'date' in data.columns and len(data) > 0:
        date_range_days = (data['date'].max() - data['date'].min()).days + 1
        daily_average = total_expenses / max(date_range_days, 1)
    else:
        date_range_days = 1
        daily_average = total_expenses
    
    # Amount statistics
    largest_expense = data['amount'].max()
    smallest_expense = data['amount'].min()
    spending_variance = data['amount'].var()
    
    # Category analysis
    if 'category' in data.columns and not data['category'].isna().all():
        top_category = data.groupby('category')['amount'].sum().idxmax()
    else:
        top_category = 'N/A'
    
    # Transaction mode analysis
    if 'transaction_mode' in data.columns and not data['transaction_mode'].isna().all():
        most_frequent_mode = data['transaction_mode'].mode().iloc[0] if not data['transaction_mode'].mode().empty else 'N/A'
    else:
        most_frequent_mode = 'N/A'
    
    return {
        'total_expenses': total_expenses,
        'average_expense': average_expense,
        'median_expense': median_expense,
        'transaction_count': transaction_count,
        'unique_categories': unique_categories,
        'date_range_days': date_range_days,
        'daily_average': daily_average,
        'largest_expense': largest_expense,
        'smallest_expense': smallest_expense,
        'spending_variance': spending_variance,
        'top_category': top_category,
        'most_frequent_mode': most_frequent_mode
    }


def get_expense_insights(data: pd.DataFrame, stats: Dict[str, Any] = None) -> List[str]:
    """Generate insights from expense data"""
    if data.empty:
        return ["No expense data available for analysis."]
    
    if stats is None:
        stats = calculate_expense_statistics(data)
    
    insights = []
    
    # Spending insights
    if stats['total_expenses'] > 0:
        insights.append(f"💰 Total spending: ₹{stats['total_expenses']:,.0f} across {stats['transaction_count']} transactions")
        insights.append(f"📊 Average transaction: ₹{stats['average_expense']:,.0f}")
        insights.append(f"📈 Daily average: ₹{stats['daily_average']:,.0f}")
    
    # Category insights
    if stats['top_category'] != 'N/A':
        insights.append(f"🏷️ Top spending category: {stats['top_category']}")
    
    # Transaction patterns
    if 'date' in data.columns:
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['day_of_week'] = data_copy['date'].dt.day_name()
        
        # Find busiest day
        daily_spending = data_copy.groupby('day_of_week')['amount'].sum()
        if not daily_spending.empty:
            busiest_day = daily_spending.idxmax()
            insights.append(f"📅 Highest spending day: {busiest_day}")
        
        # Find spending trends
        data_copy['month'] = data_copy['date'].dt.to_period('M')
        monthly_spending = data_copy.groupby('month')['amount'].sum()
        if len(monthly_spending) > 1:
            recent_trend = monthly_spending.tail(2)
            if len(recent_trend) == 2:
                change = ((recent_trend.iloc[-1] - recent_trend.iloc[-2]) / recent_trend.iloc[-2]) * 100
                trend_direction = "increased" if change > 0 else "decreased"
                insights.append(f"📈 Monthly spending {trend_direction} by {abs(change):.1f}%")
    
    # Amount insights
    if stats['largest_expense'] > 0:
        insights.append(f"💸 Largest transaction: ₹{stats['largest_expense']:,.0f}")
    
    # Payment method insights
    if stats['most_frequent_mode'] != 'N/A':
        insights.append(f"💳 Most used payment method: {stats['most_frequent_mode']}")
    
    # Spending consistency
    if stats['spending_variance'] > 0 and stats['average_expense'] > 0:
        cv = np.sqrt(stats['spending_variance']) / stats['average_expense']
        if cv < 0.5:
            insights.append("📊 Your spending is quite consistent")
        elif cv > 1.5:
            insights.append("📊 Your spending varies significantly")
    
    return insights


def analyze_spending_patterns(data: pd.DataFrame) -> Dict[str, Any]:
    """Analyze spending patterns and trends"""
    if data.empty:
        return {}
    
    patterns = {}
    
    # Ensure date column is datetime
    if 'date' in data.columns:
        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])
        
        # Weekly patterns
        data['day_of_week'] = data['date'].dt.day_name()
        weekly_pattern = data.groupby('day_of_week')['amount'].agg(['sum', 'count', 'mean']).round(2)
        patterns['weekly'] = weekly_pattern.to_dict('index')
        
        # Monthly patterns
        data['month'] = data['date'].dt.month_name()
        monthly_pattern = data.groupby('month')['amount'].agg(['sum', 'count', 'mean']).round(2)
        patterns['monthly'] = monthly_pattern.to_dict('index')
        
        # Time of month patterns (beginning, middle, end)
        data['day_of_month'] = data['date'].dt.day
        data['month_period'] = pd.cut(data['day_of_month'], 
                                    bins=[0, 10, 20, 31], 
                                    labels=['Beginning', 'Middle', 'End'])
        period_pattern = data.groupby('month_period')['amount'].agg(['sum', 'count', 'mean']).round(2)
        patterns['month_periods'] = period_pattern.to_dict('index')
    
    # Category patterns
    if 'category' in data.columns:
        category_pattern = data.groupby('category')['amount'].agg(['sum', 'count', 'mean']).round(2)
        patterns['categories'] = category_pattern.to_dict('index')
    
    # Transaction mode patterns
    if 'transaction_mode' in data.columns:
        mode_pattern = data.groupby('transaction_mode')['amount'].agg(['sum', 'count', 'mean']).round(2)
        patterns['transaction_modes'] = mode_pattern.to_dict('index')
    
    return patterns


def get_spending_trends(data: pd.DataFrame, periods: int = 6) -> Dict[str, Any]:
    """Get spending trends over time"""
    if data.empty or 'date' not in data.columns:
        return {}
    
    data = data.copy()
    data['date'] = pd.to_datetime(data['date'])
    
    # Monthly trends
    data['month'] = data['date'].dt.to_period('M')
    monthly_spending = data.groupby('month')['amount'].sum().tail(periods)
    
    trends = {
        'monthly_spending': monthly_spending.to_dict(),
        'trend_direction': 'stable',
        'trend_percentage': 0
    }
    
    if len(monthly_spending) > 1:
        # Calculate trend
        recent_months = monthly_spending.tail(2)
        if len(recent_months) == 2:
            change = ((recent_months.iloc[-1] - recent_months.iloc[-2]) / recent_months.iloc[-2]) * 100
            trends['trend_percentage'] = round(change, 1)
            
            if change > 5:
                trends['trend_direction'] = 'increasing'
            elif change < -5:
                trends['trend_direction'] = 'decreasing'
            else:
                trends['trend_direction'] = 'stable'
    
    return trends


def calculate_category_distribution(data: pd.DataFrame) -> Dict[str, float]:
    """Calculate category-wise expense distribution"""
    if data.empty or 'category' not in data.columns:
        return {}
    
    category_totals = data.groupby('category')['amount'].sum()
    total_expenses = category_totals.sum()
    
    if total_expenses == 0:
        return {}
    
    # Calculate percentages
    distribution = {}
    for category, amount in category_totals.items():
        percentage = (amount / total_expenses) * 100
        distribution[category] = {
            'amount': amount,
            'percentage': round(percentage, 1)
        }
    
    return distribution


def find_unusual_transactions(data: pd.DataFrame, threshold_multiplier: float = 3.0) -> pd.DataFrame:
    """Find transactions that are unusually large compared to typical spending"""
    if data.empty:
        return pd.DataFrame()
    
    # Calculate statistics
    mean_amount = data['amount'].mean()
    std_amount = data['amount'].std()
    
    if std_amount == 0:
        return pd.DataFrame()
    
    # Find outliers
    threshold = mean_amount + (threshold_multiplier * std_amount)
    unusual_transactions = data[data['amount'] > threshold].copy()
    
    if not unusual_transactions.empty:
        unusual_transactions['deviation_factor'] = (
            unusual_transactions['amount'] - mean_amount
        ) / std_amount
        unusual_transactions = unusual_transactions.sort_values('amount', ascending=False)
    
    return unusual_transactions


def calculate_budget_variance(data: pd.DataFrame, budget: Dict[str, float]) -> Dict[str, Any]:
    """Calculate variance between actual spending and budget"""
    if data.empty or not budget:
        return {}
    
    # Calculate actual spending by category
    if 'category' in data.columns:
        actual_spending = data.groupby('category')['amount'].sum().to_dict()
    else:
        return {}
    
    variance_analysis = {}
    
    for category, budgeted_amount in budget.items():
        actual_amount = actual_spending.get(category, 0)
        variance = actual_amount - budgeted_amount
        variance_percentage = (variance / budgeted_amount) * 100 if budgeted_amount > 0 else 0
        
        variance_analysis[category] = {
            'budgeted': budgeted_amount,
            'actual': actual_amount,
            'variance': variance,
            'variance_percentage': round(variance_percentage, 1),
            'status': 'over' if variance > 0 else 'under' if variance < 0 else 'on_track'
        }
    
    return variance_analysis


def get_expense_forecasts(data: pd.DataFrame, forecast_months: int = 3) -> Dict[str, Any]:
    """Generate simple expense forecasts based on historical data"""
    if data.empty or 'date' not in data.columns:
        return {}
    
    data = data.copy()
    data['date'] = pd.to_datetime(data['date'])
    data['month'] = data['date'].dt.to_period('M')
    
    # Calculate monthly spending
    monthly_spending = data.groupby('month')['amount'].sum()
    
    if len(monthly_spending) < 2:
        return {}
    
    # Simple trend-based forecast
    recent_average = monthly_spending.tail(3).mean()
    overall_average = monthly_spending.mean()
    
    # Calculate trend
    if len(monthly_spending) >= 3:
        recent_trend = monthly_spending.tail(3)
        trend_slope = (recent_trend.iloc[-1] - recent_trend.iloc[0]) / len(recent_trend)
    else:
        trend_slope = 0
    
    forecasts = {}
    base_forecast = recent_average
    
    for i in range(1, forecast_months + 1):
        forecast_amount = base_forecast + (trend_slope * i)
        forecast_amount = max(forecast_amount, 0)  # Ensure non-negative
        
        forecasts[f"month_{i}"] = {
            'amount': round(forecast_amount, 2),
            'confidence': 'medium' if len(monthly_spending) >= 6 else 'low'
        }
    
    return {
        'forecasts': forecasts,
        'historical_average': round(overall_average, 2),
        'recent_average': round(recent_average, 2),
        'trend': 'increasing' if trend_slope > 0 else 'decreasing' if trend_slope < 0 else 'stable'
    }
