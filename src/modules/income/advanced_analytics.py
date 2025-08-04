"""
Advanced Income Analytics Module
Enhanced analytics for income vs expense flow, diversification analysis, and earning potential forecasting
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGroupBox, QProgressBar, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ...ui.themes.base.tokens import get_tokens, tokens_to_dict


@dataclass
class IncomeFlowAnalysis:
    """Data class for income vs expense flow analysis"""
    period: str
    total_income: float
    total_expenses: float
    net_flow: float
    flow_ratio: float
    trend: str
    recommendation: str


@dataclass
class DiversificationMetrics:
    """Data class for income diversification analysis"""
    source_name: str
    contribution_percent: float
    consistency_score: float
    growth_rate: float
    risk_level: str
    recommendation: str


@dataclass
class EarningForecast:
    """Data class for earning potential forecasting"""
    period: str
    predicted_amount: float
    confidence_interval: Tuple[float, float]
    growth_rate: float
    factors: List[str]
    recommendation: str


class AdvancedIncomeAnalytics:
    """Advanced analytics for income data"""
    
    def __init__(self):
        self.income_sources = [
            'zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings',
            'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work'
        ]
    
    def analyze_income_expense_flow(self, income_data: pd.DataFrame, expense_data: pd.DataFrame) -> List[IncomeFlowAnalysis]:
        """Analyze income vs expense flow patterns"""
        flows = []
        
        if income_data.empty or expense_data.empty:
            return flows
        
        try:
            # Ensure date columns are datetime
            income_data = income_data.copy()
            expense_data = expense_data.copy()
            income_data['date'] = pd.to_datetime(income_data['date'])
            expense_data['date'] = pd.to_datetime(expense_data['date'])
            
            # Monthly flow analysis
            monthly_flows = self._analyze_monthly_flows(income_data, expense_data)
            flows.extend(monthly_flows)
            
            # Weekly flow analysis
            weekly_flows = self._analyze_weekly_flows(income_data, expense_data)
            flows.extend(weekly_flows[:4])  # Last 4 weeks
            
            # Overall trend analysis
            overall_flow = self._analyze_overall_trend(income_data, expense_data)
            if overall_flow:
                flows.append(overall_flow)
                
        except Exception as e:
            print(f"Error analyzing income expense flow: {e}")
        
        return flows
    
    def _analyze_monthly_flows(self, income_data: pd.DataFrame, expense_data: pd.DataFrame) -> List[IncomeFlowAnalysis]:
        """Analyze monthly income vs expense flows"""
        flows = []
        
        try:
            # Group by month
            income_monthly = income_data.groupby(income_data['date'].dt.to_period('M'))['earned'].sum()
            expense_monthly = expense_data.groupby(expense_data['date'].dt.to_period('M'))['amount'].sum()
            
            # Get common months
            common_months = income_monthly.index.intersection(expense_monthly.index)
            
            for month in common_months[-6:]:  # Last 6 months
                income_amount = income_monthly.get(month, 0)
                expense_amount = expense_monthly.get(month, 0)
                net_flow = income_amount - expense_amount
                flow_ratio = (income_amount / expense_amount) if expense_amount > 0 else float('inf')
                
                # Determine trend
                if flow_ratio > 1.2:
                    trend = "Positive"
                elif flow_ratio > 0.8:
                    trend = "Balanced"
                else:
                    trend = "Negative"
                
                # Generate recommendation
                if flow_ratio < 0.8:
                    recommendation = "Consider reducing expenses or increasing income sources"
                elif flow_ratio > 1.5:
                    recommendation = "Excellent surplus! Consider investing or saving more"
                else:
                    recommendation = "Maintain current balance and monitor trends"
                
                flow = IncomeFlowAnalysis(
                    period=f"Month {month}",
                    total_income=income_amount,
                    total_expenses=expense_amount,
                    net_flow=net_flow,
                    flow_ratio=flow_ratio,
                    trend=trend,
                    recommendation=recommendation
                )
                flows.append(flow)
        
        except Exception as e:
            print(f"Error in monthly flow analysis: {e}")
        
        return flows
    
    def _analyze_weekly_flows(self, income_data: pd.DataFrame, expense_data: pd.DataFrame) -> List[IncomeFlowAnalysis]:
        """Analyze weekly income vs expense flows"""
        flows = []
        
        try:
            # Group by week
            income_weekly = income_data.groupby(income_data['date'].dt.to_period('W'))['earned'].sum()
            expense_weekly = expense_data.groupby(expense_data['date'].dt.to_period('W'))['amount'].sum()
            
            # Get common weeks
            common_weeks = income_weekly.index.intersection(expense_weekly.index)
            
            for week in common_weeks[-4:]:  # Last 4 weeks
                income_amount = income_weekly.get(week, 0)
                expense_amount = expense_weekly.get(week, 0)
                net_flow = income_amount - expense_amount
                flow_ratio = (income_amount / expense_amount) if expense_amount > 0 else float('inf')
                
                # Determine trend
                if flow_ratio > 1.1:
                    trend = "Positive"
                elif flow_ratio > 0.9:
                    trend = "Balanced"
                else:
                    trend = "Negative"
                
                recommendation = "Weekly monitoring helps maintain financial discipline"
                
                flow = IncomeFlowAnalysis(
                    period=f"Week {week}",
                    total_income=income_amount,
                    total_expenses=expense_amount,
                    net_flow=net_flow,
                    flow_ratio=flow_ratio,
                    trend=trend,
                    recommendation=recommendation
                )
                flows.append(flow)
        
        except Exception as e:
            print(f"Error in weekly flow analysis: {e}")
        
        return flows
    
    def _analyze_overall_trend(self, income_data: pd.DataFrame, expense_data: pd.DataFrame) -> Optional[IncomeFlowAnalysis]:
        """Analyze overall income vs expense trend"""
        try:
            total_income = income_data['earned'].sum()
            total_expenses = expense_data['amount'].sum()
            net_flow = total_income - total_expenses
            flow_ratio = (total_income / total_expenses) if total_expenses > 0 else float('inf')
            
            # Determine overall trend
            if flow_ratio > 1.2:
                trend = "Strong Positive"
                recommendation = "Excellent financial health! Consider long-term investments"
            elif flow_ratio > 1.0:
                trend = "Positive"
                recommendation = "Good financial balance. Build emergency fund"
            elif flow_ratio > 0.8:
                trend = "Cautionary"
                recommendation = "Monitor expenses closely and look for income opportunities"
            else:
                trend = "Critical"
                recommendation = "Immediate action needed: reduce expenses and increase income"
            
            return IncomeFlowAnalysis(
                period="Overall",
                total_income=total_income,
                total_expenses=total_expenses,
                net_flow=net_flow,
                flow_ratio=flow_ratio,
                trend=trend,
                recommendation=recommendation
            )
        
        except Exception as e:
            print(f"Error in overall trend analysis: {e}")
            return None
    
    def analyze_income_diversification(self, data: pd.DataFrame) -> List[DiversificationMetrics]:
        """Analyze income source diversification"""
        metrics = []
        
        if data.empty:
            return metrics
        
        try:
            # Calculate total income
            total_income = data['earned'].sum()
            
            for source in self.income_sources:
                if source in data.columns:
                    source_total = data[source].sum()
                    contribution_percent = (source_total / total_income * 100) if total_income > 0 else 0
                    
                    # Calculate consistency score (based on frequency of non-zero values)
                    non_zero_days = len(data[data[source] > 0])
                    total_days = len(data)
                    consistency_score = (non_zero_days / total_days * 100) if total_days > 0 else 0
                    
                    # Calculate growth rate (simple trend)
                    if len(data) > 1:
                        first_half = data[:len(data)//2][source].mean()
                        second_half = data[len(data)//2:][source].mean()
                        growth_rate = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
                    else:
                        growth_rate = 0
                    
                    # Determine risk level
                    if contribution_percent > 50:
                        risk_level = "High"
                        recommendation = f"Over-dependence on {source}. Diversify income sources"
                    elif contribution_percent > 30:
                        risk_level = "Medium"
                        recommendation = f"{source} is a major contributor. Monitor performance closely"
                    elif contribution_percent > 10:
                        risk_level = "Low"
                        recommendation = f"{source} provides good supplementary income"
                    else:
                        risk_level = "Minimal"
                        recommendation = f"Consider increasing {source} contribution or focus on other sources"
                    
                    metric = DiversificationMetrics(
                        source_name=source.replace('_', ' ').title(),
                        contribution_percent=contribution_percent,
                        consistency_score=consistency_score,
                        growth_rate=growth_rate,
                        risk_level=risk_level,
                        recommendation=recommendation
                    )
                    metrics.append(metric)
            
            # Sort by contribution percentage
            metrics.sort(key=lambda x: x.contribution_percent, reverse=True)
        
        except Exception as e:
            print(f"Error analyzing income diversification: {e}")
        
        return metrics
    
    def forecast_earning_potential(self, data: pd.DataFrame, forecast_days: int = 30) -> List[EarningForecast]:
        """Forecast earning potential based on historical data"""
        forecasts = []
        
        if data.empty or len(data) < 7:  # Need at least a week of data
            return forecasts
        
        try:
            # Ensure date column is datetime
            data = data.copy()
            data['date'] = pd.to_datetime(data['date'])
            data = data.sort_values('date')
            
            # Overall earning forecast
            overall_forecast = self._forecast_overall_earnings(data, forecast_days)
            if overall_forecast:
                forecasts.append(overall_forecast)
            
            # Source-specific forecasts for major contributors
            source_forecasts = self._forecast_source_earnings(data, forecast_days)
            forecasts.extend(source_forecasts)
            
        except Exception as e:
            print(f"Error forecasting earning potential: {e}")
        
        return forecasts
    
    def _forecast_overall_earnings(self, data: pd.DataFrame, forecast_days: int) -> Optional[EarningForecast]:
        """Forecast overall earnings"""
        try:
            # Calculate daily averages and trends
            daily_earnings = data.groupby('date')['earned'].sum()
            
            # Simple moving average
            window = min(7, len(daily_earnings))
            moving_avg = daily_earnings.rolling(window=window).mean().iloc[-1]
            
            # Linear trend
            x = np.arange(len(daily_earnings))
            y = daily_earnings.values
            if len(x) > 1:
                slope, intercept = np.polyfit(x, y, 1)
                trend_factor = slope * forecast_days
            else:
                trend_factor = 0
            
            # Forecast
            base_prediction = moving_avg * forecast_days
            trend_adjusted = base_prediction + trend_factor
            
            # Confidence interval (simple approach)
            std_dev = daily_earnings.std()
            confidence_lower = trend_adjusted - (std_dev * forecast_days * 0.5)
            confidence_upper = trend_adjusted + (std_dev * forecast_days * 0.5)
            
            # Growth rate
            if len(daily_earnings) > 1:
                growth_rate = ((daily_earnings.iloc[-1] - daily_earnings.iloc[0]) / daily_earnings.iloc[0] * 100)
            else:
                growth_rate = 0
            
            # Factors affecting forecast
            factors = [
                "Historical performance trends",
                "Seasonal variations",
                "Income source consistency"
            ]
            
            # Recommendation
            if growth_rate > 10:
                recommendation = "Strong growth trend. Consider scaling successful income sources"
            elif growth_rate > 0:
                recommendation = "Positive trend. Maintain current strategies"
            else:
                recommendation = "Declining trend. Review and optimize income sources"
            
            return EarningForecast(
                period=f"Next {forecast_days} days",
                predicted_amount=trend_adjusted,
                confidence_interval=(confidence_lower, confidence_upper),
                growth_rate=growth_rate,
                factors=factors,
                recommendation=recommendation
            )
        
        except Exception as e:
            print(f"Error in overall earnings forecast: {e}")
            return None
    
    def _forecast_source_earnings(self, data: pd.DataFrame, forecast_days: int) -> List[EarningForecast]:
        """Forecast earnings for individual sources"""
        forecasts = []
        
        try:
            # Calculate total income to identify major sources
            total_income = data['earned'].sum()
            
            for source in self.income_sources:
                if source in data.columns:
                    source_total = data[source].sum()
                    contribution = (source_total / total_income * 100) if total_income > 0 else 0
                    
                    # Only forecast for sources contributing > 10%
                    if contribution > 10:
                        source_data = data[data[source] > 0][source]
                        
                        if len(source_data) > 3:  # Need some data points
                            avg_earning = source_data.mean()
                            frequency = len(source_data) / len(data)  # How often this source earns
                            
                            # Simple forecast
                            predicted_days = forecast_days * frequency
                            predicted_amount = avg_earning * predicted_days
                            
                            # Confidence interval
                            std_dev = source_data.std()
                            confidence_lower = predicted_amount - (std_dev * predicted_days * 0.3)
                            confidence_upper = predicted_amount + (std_dev * predicted_days * 0.3)
                            
                            # Growth rate
                            if len(source_data) > 1:
                                growth_rate = ((source_data.iloc[-1] - source_data.iloc[0]) / source_data.iloc[0] * 100)
                            else:
                                growth_rate = 0
                            
                            forecast = EarningForecast(
                                period=f"{source.replace('_', ' ').title()} - Next {forecast_days} days",
                                predicted_amount=predicted_amount,
                                confidence_interval=(confidence_lower, confidence_upper),
                                growth_rate=growth_rate,
                                factors=[f"Historical {source} performance", "Frequency patterns"],
                                recommendation=f"Focus on optimizing {source.replace('_', ' ')} earnings"
                            )
                            forecasts.append(forecast)
        
        except Exception as e:
            print(f"Error in source earnings forecast: {e}")
        
        return forecasts
    
    def get_comprehensive_analysis(self, income_data: pd.DataFrame, expense_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Get comprehensive income analysis"""
        analysis = {
            'income_expense_flows': [],
            'diversification_metrics': [],
            'earning_forecasts': [],
            'summary': {}
        }
        
        try:
            # Income vs expense flow analysis
            if expense_data is not None and not expense_data.empty:
                flows = self.analyze_income_expense_flow(income_data, expense_data)
                analysis['income_expense_flows'] = flows
            
            # Diversification analysis
            diversification = self.analyze_income_diversification(income_data)
            analysis['diversification_metrics'] = diversification
            
            # Earning forecasts
            forecasts = self.forecast_earning_potential(income_data)
            analysis['earning_forecasts'] = forecasts
            
            # Summary statistics
            total_income = income_data['earned'].sum() if not income_data.empty else 0
            avg_daily = income_data['earned'].mean() if not income_data.empty else 0
            
            analysis['summary'] = {
                'total_income': total_income,
                'average_daily': avg_daily,
                'diversification_score': len([m for m in diversification if m.contribution_percent > 5]),
                'growth_potential': 'High' if any(f.growth_rate > 10 for f in forecasts) else 'Moderate',
                'analysis_date': datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"Error in comprehensive income analysis: {e}")
        
        return analysis


class AdvancedIncomeAnalyticsWidget(QWidget):
    """Widget for displaying advanced income analytics"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.analytics_engine = AdvancedIncomeAnalytics()
        self.current_theme = "light"  # Default to light theme
        self.setup_ui()

    def get_theme_colors(self):
        """Get current theme colors"""
        tokens = get_tokens(self.current_theme)
        return tokens_to_dict(tokens)

    def set_theme(self, theme: str):
        """Set the theme for this widget - FIXED: Proper theme application"""
        self.current_theme = theme
        # CRITICAL FIX: Actually apply the theme styles when theme changes
        self.apply_theme_styles()

    def apply_theme_styles(self):
        """Apply theme-aware styles to the widget - FIXED: Proper theme implementation"""
        # CRITICAL FIX: Use correct design tokens structure
        theme_data = self.get_theme_colors()
        colors = theme_data['colors']  # Access the colors sub-dictionary

        # Apply theme to QGroupBox widgets (these were causing black backgrounds!)
        group_box_style = f"""
            QGroupBox {{
                border: 2px solid {colors['primary_border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """

        # Apply to all group box widgets
        if hasattr(self, 'flow_widget'):
            self.flow_widget.setStyleSheet(group_box_style)
        if hasattr(self, 'diversification_widget'):
            self.diversification_widget.setStyleSheet(group_box_style)
        if hasattr(self, 'forecast_widget'):
            self.forecast_widget.setStyleSheet(group_box_style)

    def setup_ui(self):
        """Setup the advanced income analytics UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Income vs Expense Flow Section
        self.flow_widget = self.create_flow_widget()
        content_layout.addWidget(self.flow_widget)

        # Diversification Analysis Section
        self.diversification_widget = self.create_diversification_widget()
        content_layout.addWidget(self.diversification_widget)

        # Earning Forecasts Section
        self.forecast_widget = self.create_forecast_widget()
        content_layout.addWidget(self.forecast_widget)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def create_flow_widget(self):
        """Create income vs expense flow widget"""
        group_box = QGroupBox("Income vs Expense Flow Analysis")
        layout = QVBoxLayout(group_box)

        self.flow_container = QVBoxLayout()
        layout.addLayout(self.flow_container)

        return group_box

    def create_diversification_widget(self):
        """Create income diversification widget"""
        group_box = QGroupBox("Income Source Diversification")
        layout = QVBoxLayout(group_box)

        self.diversification_container = QVBoxLayout()
        layout.addLayout(self.diversification_container)

        return group_box

    def create_forecast_widget(self):
        """Create earning forecasts widget"""
        group_box = QGroupBox("Earning Potential Forecasts")
        layout = QVBoxLayout(group_box)

        self.forecast_container = QVBoxLayout()
        layout.addLayout(self.forecast_container)

        return group_box

    def update_analysis(self, income_data: pd.DataFrame, expense_data: pd.DataFrame = None):
        """Update the analysis display with new data"""
        try:
            # Get comprehensive analysis
            analysis = self.analytics_engine.get_comprehensive_analysis(income_data, expense_data)

            # Update flow analysis
            self.update_flow_display(analysis['income_expense_flows'])

            # Update diversification analysis
            self.update_diversification_display(analysis['diversification_metrics'])

            # Update forecasts
            self.update_forecast_display(analysis['earning_forecasts'])

        except Exception as e:
            print(f"Error updating advanced income analytics: {e}")

    def update_flow_display(self, flows: List[IncomeFlowAnalysis]):
        """Update income vs expense flow display"""
        # Clear existing flows
        self.clear_layout(self.flow_container)

        if not flows:
            # Get theme colors
            theme_data = self.get_theme_colors()
            colors = theme_data['colors']

            no_data_label = QLabel("No expense data available for flow analysis.")
            no_data_label.setStyleSheet(f"color: {colors['text_secondary']}; font-style: italic;")
            self.flow_container.addWidget(no_data_label)
            return

        # Get theme colors
        theme_data = self.get_theme_colors()
        colors = theme_data['colors']

        for flow in flows[:6]:  # Show top 6 flows
            flow_frame = QFrame()
            flow_frame.setObjectName("flowFrame")
            # CRITICAL FIX: Remove hardcoded background-color to let global theme handle it
            flow_frame.setStyleSheet(f"""
                QFrame#flowFrame {{
                    border: 1px solid {colors['primary_border']};
                    border-radius: 5px;
                    padding: 10px;
                    margin: 5px;
                }}
            """)

            flow_layout = QVBoxLayout(flow_frame)

            # Flow header
            header_layout = QHBoxLayout()

            period_label = QLabel(flow.period)
            period_label.setStyleSheet(f"font-weight: bold; color: {colors['info']};")
            header_layout.addWidget(period_label)

            header_layout.addStretch()

            # Map trend to theme colors
            trend_color_map = {
                "Positive": colors['success'],
                "Balanced": colors['warning'],
                "Negative": colors['error'],
                "Strong Positive": colors['success'],
                "Cautionary": colors['warning'],
                "Critical": colors['error']
            }
            trend_label = QLabel(flow.trend)
            trend_label.setStyleSheet(f"color: {trend_color_map.get(flow.trend, colors['text_secondary'])}; font-weight: bold;")
            header_layout.addWidget(trend_label)

            flow_layout.addLayout(header_layout)

            # Flow metrics
            metrics_layout = QGridLayout()

            income_label = QLabel(f"Income: ₹{flow.total_income:,.0f}")
            income_label.setStyleSheet(f"color: {colors['success']};")
            metrics_layout.addWidget(income_label, 0, 0)

            expense_label = QLabel(f"Expenses: ₹{flow.total_expenses:,.0f}")
            expense_label.setStyleSheet(f"color: {colors['error']};")
            metrics_layout.addWidget(expense_label, 0, 1)

            net_color = colors['success'] if flow.net_flow >= 0 else colors['error']
            net_label = QLabel(f"Net Flow: ₹{flow.net_flow:,.0f}")
            net_label.setStyleSheet(f"color: {net_color}; font-weight: bold;")
            metrics_layout.addWidget(net_label, 1, 0)

            ratio_label = QLabel(f"I/E Ratio: {flow.flow_ratio:.2f}")
            ratio_label.setStyleSheet(f"color: {colors['info']};")
            metrics_layout.addWidget(ratio_label, 1, 1)

            flow_layout.addLayout(metrics_layout)

            # Recommendation
            rec_label = QLabel(f"💡 {flow.recommendation}")
            rec_label.setWordWrap(True)
            rec_label.setStyleSheet(f"color: {colors['text_secondary']}; font-style: italic; margin-top: 5px;")
            flow_layout.addWidget(rec_label)

            self.flow_container.addWidget(flow_frame)

    def update_diversification_display(self, metrics: List[DiversificationMetrics]):
        """Update diversification analysis display"""
        # Clear existing metrics
        self.clear_layout(self.diversification_container)

        if not metrics:
            # Get theme colors
            theme_data = self.get_theme_colors()
            colors = theme_data['colors']

            no_data_label = QLabel("No income source data available for diversification analysis.")
            no_data_label.setStyleSheet(f"color: {colors['text_secondary']}; font-style: italic;")
            self.diversification_container.addWidget(no_data_label)
            return

        # Get theme colors
        theme_data = self.get_theme_colors()
        colors = theme_data['colors']

        for metric in metrics[:8]:  # Show top 8 sources
            if metric.contribution_percent < 1:  # Skip very small contributors
                continue

            metric_frame = QFrame()
            metric_frame.setObjectName("metricFrame")
            # CRITICAL FIX: Remove hardcoded background-color to let global theme handle it
            metric_frame.setStyleSheet(f"""
                QFrame#metricFrame {{
                    border: 1px solid {colors['primary_border']};
                    border-radius: 5px;
                    padding: 10px;
                    margin: 5px;
                }}
            """)

            metric_layout = QVBoxLayout(metric_frame)

            # Source header
            header_layout = QHBoxLayout()

            source_label = QLabel(metric.source_name)
            source_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {colors['text_primary']};")
            header_layout.addWidget(source_label)

            header_layout.addStretch()

            # Map risk levels to theme colors
            risk_color_map = {
                "High": colors['error'],
                "Medium": colors['warning'],
                "Low": colors['success'],
                "Minimal": colors['info']
            }
            risk_label = QLabel(f"Risk: {metric.risk_level}")
            risk_label.setStyleSheet(f"color: {risk_color_map.get(metric.risk_level, colors['text_secondary'])}; font-weight: bold;")
            header_layout.addWidget(risk_label)

            metric_layout.addLayout(header_layout)

            # Metrics grid
            metrics_grid = QGridLayout()

            contribution_label = QLabel(f"Contribution: {metric.contribution_percent:.1f}%")
            metrics_grid.addWidget(contribution_label, 0, 0)

            consistency_label = QLabel(f"Consistency: {metric.consistency_score:.1f}%")
            metrics_grid.addWidget(consistency_label, 0, 1)

            growth_color = colors['success'] if metric.growth_rate > 0 else colors['error']
            growth_label = QLabel(f"Growth: {metric.growth_rate:.1f}%")
            growth_label.setStyleSheet(f"color: {growth_color};")
            metrics_grid.addWidget(growth_label, 1, 0)

            metric_layout.addLayout(metrics_grid)

            # Progress bar for contribution
            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setValue(int(metric.contribution_percent))
            progress_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {colors['info']}; }}")
            metric_layout.addWidget(progress_bar)

            # Recommendation
            rec_label = QLabel(f"💡 {metric.recommendation}")
            rec_label.setWordWrap(True)
            rec_label.setStyleSheet(f"color: {colors['text_secondary']}; font-style: italic; margin-top: 5px;")
            metric_layout.addWidget(rec_label)

            self.diversification_container.addWidget(metric_frame)

    def update_forecast_display(self, forecasts: List[EarningForecast]):
        """Update earning forecasts display"""
        # Clear existing forecasts
        self.clear_layout(self.forecast_container)

        if not forecasts:
            # Get theme colors
            theme_data = self.get_theme_colors()
            colors = theme_data['colors']

            no_data_label = QLabel("Insufficient data for earning forecasts.")
            no_data_label.setStyleSheet(f"color: {colors['text_secondary']}; font-style: italic;")
            self.forecast_container.addWidget(no_data_label)
            return

        # Get theme colors
        theme_data = self.get_theme_colors()
        colors = theme_data['colors']

        for forecast in forecasts[:5]:  # Show top 5 forecasts
            forecast_frame = QFrame()
            forecast_frame.setObjectName("forecastFrame")
            # CRITICAL FIX: Remove hardcoded background-color to let global theme handle it
            forecast_frame.setStyleSheet(f"""
                QFrame#forecastFrame {{
                    border: 1px solid {colors['primary_border']};
                    border-radius: 5px;
                    padding: 10px;
                    margin: 5px;
                }}
            """)

            forecast_layout = QVBoxLayout(forecast_frame)

            # Forecast header
            header_layout = QHBoxLayout()

            period_label = QLabel(forecast.period)
            period_label.setStyleSheet(f"font-weight: bold; color: {colors['warning']};")
            header_layout.addWidget(period_label)

            header_layout.addStretch()

            growth_color = colors['success'] if forecast.growth_rate > 0 else colors['error']
            growth_label = QLabel(f"Growth: {forecast.growth_rate:.1f}%")
            growth_label.setStyleSheet(f"color: {growth_color}; font-weight: bold;")
            header_layout.addWidget(growth_label)

            forecast_layout.addLayout(header_layout)

            # Prediction
            prediction_label = QLabel(f"Predicted Earnings: ₹{forecast.predicted_amount:,.0f}")
            prediction_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {colors['info']};")
            forecast_layout.addWidget(prediction_label)

            # Confidence interval
            confidence_label = QLabel(f"Range: ₹{forecast.confidence_interval[0]:,.0f} - ₹{forecast.confidence_interval[1]:,.0f}")
            confidence_label.setStyleSheet(f"color: {colors['text_secondary']};")
            forecast_layout.addWidget(confidence_label)

            # Factors
            if forecast.factors:
                factors_label = QLabel("Key Factors:")
                factors_label.setStyleSheet(f"font-weight: bold; margin-top: 10px; color: {colors['text_primary']};")
                forecast_layout.addWidget(factors_label)

                for factor in forecast.factors:
                    factor_label = QLabel(f"• {factor}")
                    factor_label.setStyleSheet(f"margin-left: 15px; color: {colors['text_secondary']};")
                    forecast_layout.addWidget(factor_label)

            # Recommendation
            rec_label = QLabel(f"💡 {forecast.recommendation}")
            rec_label.setWordWrap(True)
            rec_label.setStyleSheet(f"color: {colors['success']}; font-style: italic; margin-top: 10px;")
            forecast_layout.addWidget(rec_label)

            self.forecast_container.addWidget(forecast_frame)

    def clear_layout(self, layout):
        """Clear all widgets from a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
