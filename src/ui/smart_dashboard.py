"""
Smart Dashboard with AI Insights Module
Advanced dashboard with unified financial health score, goal progress tracking, and predictive analytics
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QPushButton, QScrollArea, QGroupBox, QProgressBar,
    QTabWidget, QSplitter, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPalette, QPixmap, QPainter, QColor

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

from ..core.config import AppConfig
from ..core.data_manager import DataManager
from ..modules.expenses.visualization import SummaryCardWidget, ExpenseDataProcessor
from ..modules.income.models import IncomeDataModel
from ..modules.habits.models import HabitDataModel
from ..modules.expenses.models import ExpenseDataModel


class FinancialHealthScoreWidget(QFrame):
    """Widget displaying unified financial health score"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("financialHealthScoreWidget")
        self.setMinimumHeight(250)
        self.setMaximumHeight(300)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the financial health score UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Financial Health Score")
        title.setObjectName("healthScoreTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Score display
        self.score_label = QLabel("--")
        self.score_label.setObjectName("healthScoreValue")
        score_font = QFont()
        score_font.setPointSize(48)
        score_font.setBold(True)
        self.score_label.setFont(score_font)
        self.score_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.score_label)
        
        # Score description
        self.description_label = QLabel("Calculating...")
        self.description_label.setObjectName("healthScoreDescription")
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        # Factors breakdown
        factors_frame = QFrame()
        factors_layout = QGridLayout(factors_frame)
        
        self.factor_labels = {}
        factors = ["Income Stability", "Expense Control", "Savings Rate", "Goal Progress"]
        
        for i, factor in enumerate(factors):
            factor_label = QLabel(factor)
            factor_label.setObjectName("factorLabel")
            
            factor_value = QLabel("--")
            factor_value.setObjectName("factorValue")
            
            self.factor_labels[factor] = factor_value
            
            row = i // 2
            col = (i % 2) * 2
            factors_layout.addWidget(factor_label, row, col)
            factors_layout.addWidget(factor_value, row, col + 1)
        
        layout.addWidget(factors_frame)
    
    def update_score(self, score_data: Dict[str, Any]):
        """Update the financial health score display"""
        score = score_data.get('overall_score', 0)
        self.score_label.setText(f"{score:.0f}")
        
        # Update color based on score
        if score >= 80:
            color = "#4CAF50"  # Green
            description = "Excellent financial health!"
        elif score >= 60:
            color = "#FF9800"  # Orange
            description = "Good financial health with room for improvement"
        else:
            color = "#F44336"  # Red
            description = "Financial health needs attention"
        
        self.score_label.setStyleSheet(f"color: {color};")
        self.description_label.setText(description)
        
        # Update factors
        factors = score_data.get('factors', {})
        for factor_name, factor_widget in self.factor_labels.items():
            factor_key = factor_name.lower().replace(' ', '_')
            factor_value = factors.get(factor_key, 0)
            factor_widget.setText(f"{factor_value:.0f}%")


class GoalProgressWidget(QFrame):
    """Widget for tracking goal progress across modules"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("goalProgressWidget")
        self.setMinimumHeight(250)
        self.setMaximumHeight(300)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the goal progress UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Goal Progress Tracking")
        title.setObjectName("goalProgressTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Goals container
        self.goals_container = QVBoxLayout()
        layout.addLayout(self.goals_container)
        
        layout.addStretch()
    
    def add_goal_progress(self, goal_name: str, current: float, target: float, unit: str = ""):
        """Add a goal progress bar"""
        goal_frame = QFrame()
        goal_frame.setObjectName("goalFrame")
        goal_layout = QVBoxLayout(goal_frame)
        goal_layout.setContentsMargins(10, 10, 10, 10)
        
        # Goal header
        header_layout = QHBoxLayout()
        
        goal_label = QLabel(goal_name)
        goal_label.setObjectName("goalLabel")
        header_layout.addWidget(goal_label)
        
        header_layout.addStretch()
        
        progress_text = QLabel(f"{current:.1f}{unit} / {target:.1f}{unit}")
        progress_text.setObjectName("goalProgressText")
        header_layout.addWidget(progress_text)
        
        goal_layout.addLayout(header_layout)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setObjectName("goalProgressBar")
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        
        progress_percentage = min(100, (current / target * 100) if target > 0 else 0)
        progress_bar.setValue(int(progress_percentage))
        
        goal_layout.addWidget(progress_bar)
        
        self.goals_container.addWidget(goal_frame)
    
    def clear_goals(self):
        """Clear all goal progress displays"""
        while self.goals_container.count():
            child = self.goals_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


class PredictiveAnalyticsWidget(QFrame):
    """Widget for displaying predictive analytics and insights"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("predictiveAnalyticsWidget")
        self.setMinimumHeight(200)
        self.setMaximumHeight(250)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the predictive analytics UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("AI Insights & Predictions")
        title.setObjectName("predictiveTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Insights container
        self.insights_container = QVBoxLayout()
        layout.addLayout(self.insights_container)
        
        layout.addStretch()
    
    def add_insight(self, insight_text: str, insight_type: str = "info"):
        """Add an AI insight"""
        insight_frame = QFrame()
        insight_frame.setObjectName(f"insightFrame_{insight_type}")
        insight_layout = QHBoxLayout(insight_frame)
        insight_layout.setContentsMargins(15, 10, 15, 10)
        
        # Icon based on type
        icon_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "success": "✅",
            "prediction": "🔮",
            "recommendation": "💡"
        }
        
        icon_label = QLabel(icon_map.get(insight_type, "ℹ️"))
        icon_label.setObjectName("insightIcon")
        insight_layout.addWidget(icon_label)
        
        # Insight text
        text_label = QLabel(insight_text)
        text_label.setObjectName("insightText")
        text_label.setWordWrap(True)
        insight_layout.addWidget(text_label)
        
        self.insights_container.addWidget(insight_frame)
    
    def clear_insights(self):
        """Clear all insights"""
        while self.insights_container.count():
            child = self.insights_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


class SmartDashboardWidget(QWidget):
    """Smart Dashboard with AI Insights"""
    
    def __init__(self, data_manager: DataManager, config: AppConfig, parent=None):
        super().__init__(parent)
        
        self.data_manager = data_manager
        self.config = config
        
        self.setup_ui()
        self.setup_refresh_timer()

    def update_theme(self, new_theme):
        """Update theme for smart dashboard components"""
        # Update any chart widgets or themed components here
        # For now, just force a widget update
        self.update()
        
    def setup_ui(self):
        """Setup the smart dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(15)

        # Top row: Financial Health Score and Goal Progress
        top_row = QHBoxLayout()
        top_row.setSpacing(15)

        self.health_score_widget = FinancialHealthScoreWidget()
        self.health_score_widget.setMinimumHeight(250)
        self.health_score_widget.setMaximumHeight(300)
        top_row.addWidget(self.health_score_widget)

        self.goal_progress_widget = GoalProgressWidget()
        self.goal_progress_widget.setMinimumHeight(250)
        self.goal_progress_widget.setMaximumHeight(300)
        top_row.addWidget(self.goal_progress_widget)

        content_layout.addLayout(top_row)

        # Bottom row: Predictive Analytics
        self.predictive_widget = PredictiveAnalyticsWidget()
        self.predictive_widget.setMinimumHeight(200)
        self.predictive_widget.setMaximumHeight(250)
        content_layout.addWidget(self.predictive_widget)

        # Remove addStretch() to prevent layout issues
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # Initial data load
        self.refresh_data()
    
    def setup_refresh_timer(self):
        """Setup automatic refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes
    
    def refresh_data(self):
        """Refresh all smart dashboard data"""
        try:
            self.update_financial_health_score()
            self.update_goal_progress()
            self.update_predictive_insights()
        except Exception as e:
            print(f"Error refreshing smart dashboard: {e}")
    
    def update_financial_health_score(self):
        """Calculate and update financial health score"""
        try:
            # Get data from different modules
            expense_model = ExpenseDataModel(self.data_manager)
            income_model = IncomeDataModel(self.data_manager)
            
            # Calculate financial health score
            score_data = self.calculate_financial_health_score(expense_model, income_model)
            self.health_score_widget.update_score(score_data)
            
        except Exception as e:
            print(f"Error updating financial health score: {e}")
    
    def calculate_financial_health_score(self, expense_model, income_model) -> Dict[str, Any]:
        """Calculate comprehensive financial health score"""
        factors = {}
        
        # Income stability (based on consistency)
        try:
            income_summary = income_model.get_income_summary()
            factors['income_stability'] = min(100, income_summary.get('consistency_score', 50))
        except:
            factors['income_stability'] = 50
        
        # Expense control (based on budget adherence and trends)
        try:
            expense_data = expense_model.get_all_expenses()
            if not expense_data.empty:
                # Simple expense control metric based on spending variance
                daily_spending = expense_data.groupby('date')['amount'].sum()
                if len(daily_spending) > 1:
                    cv = daily_spending.std() / daily_spending.mean() if daily_spending.mean() > 0 else 1
                    factors['expense_control'] = max(0, min(100, 100 - (cv * 50)))
                else:
                    factors['expense_control'] = 75
            else:
                factors['expense_control'] = 50
        except:
            factors['expense_control'] = 50
        
        # Savings rate (income vs expenses)
        try:
            today = date.today()
            month_start = today.replace(day=1)

            # Get monthly income and expenses using existing methods
            income_data = income_model.get_all_income_records()
            expense_data = expense_model.get_expenses_by_date_range(month_start, today)

            monthly_income = 0
            monthly_expenses = 0

            if not income_data.empty:
                # Filter income data for current month
                income_data['date'] = pd.to_datetime(income_data['date'])
                current_month_income = income_data[
                    (income_data['date'].dt.date >= month_start) &
                    (income_data['date'].dt.date <= today)
                ]
                monthly_income = current_month_income['earned'].sum() if not current_month_income.empty else 0

            if not expense_data.empty:
                monthly_expenses = expense_data['amount'].sum()

            if monthly_income > 0:
                savings_rate = ((monthly_income - monthly_expenses) / monthly_income) * 100
                factors['savings_rate'] = max(0, min(100, savings_rate))
            else:
                factors['savings_rate'] = 0
        except Exception as e:
            print(f"Error calculating savings rate: {e}")
            factors['savings_rate'] = 25
        
        # Goal progress (average across modules)
        try:
            # This would be expanded to include actual goal tracking
            factors['goal_progress'] = 70  # Placeholder
        except:
            factors['goal_progress'] = 50
        
        # Calculate overall score (weighted average)
        weights = {
            'income_stability': 0.25,
            'expense_control': 0.30,
            'savings_rate': 0.30,
            'goal_progress': 0.15
        }
        
        overall_score = sum(factors[key] * weights[key] for key in factors.keys())
        
        return {
            'overall_score': overall_score,
            'factors': factors
        }
    
    def update_goal_progress(self):
        """Update goal progress tracking"""
        try:
            self.goal_progress_widget.clear_goals()
            
            # Income goals
            income_model = IncomeDataModel(self.data_manager)
            today_record = income_model.get_income_record_by_date(date.today())
            if today_record:
                current_income = today_record.earned
                target_income = income_model.get_base_income_for_date(date.today())
                self.goal_progress_widget.add_goal_progress(
                    "Daily Income Goal", current_income, target_income, "₹"
                )
            
            # Habit goals (placeholder - would need actual habit data)
            self.goal_progress_widget.add_goal_progress(
                "Daily Habits", 3, 5, " completed"
            )
            
            # Monthly savings goal (placeholder)
            self.goal_progress_widget.add_goal_progress(
                "Monthly Savings", 15000, 25000, "₹"
            )
            
        except Exception as e:
            print(f"Error updating goal progress: {e}")
    
    def update_predictive_insights(self):
        """Update AI insights and predictions"""
        try:
            self.predictive_widget.clear_insights()
            
            # Generate insights based on data patterns
            insights = self.generate_ai_insights()
            
            for insight in insights:
                self.predictive_widget.add_insight(
                    insight['text'], 
                    insight.get('type', 'info')
                )
                
        except Exception as e:
            print(f"Error updating predictive insights: {e}")
    
    def generate_ai_insights(self) -> List[Dict[str, str]]:
        """Generate AI-powered insights"""
        insights = []
        
        try:
            # Expense pattern insights
            expense_model = ExpenseDataModel(self.data_manager)
            expense_data = expense_model.get_all_expenses()
            
            if not expense_data.empty:
                # Spending trend analysis
                recent_data = expense_data.tail(30)  # Last 30 transactions
                avg_amount = recent_data['amount'].mean()
                
                if avg_amount > 500:
                    insights.append({
                        'text': f"Your average transaction amount is ₹{avg_amount:.0f}. Consider reviewing large expenses for optimization opportunities.",
                        'type': 'recommendation'
                    })
                
                # Weekend vs weekday spending
                recent_data['date'] = pd.to_datetime(recent_data['date'])
                recent_data['weekday'] = recent_data['date'].dt.weekday
                weekend_spending = recent_data[recent_data['weekday'].isin([5, 6])]['amount'].mean()
                weekday_spending = recent_data[~recent_data['weekday'].isin([5, 6])]['amount'].mean()
                
                if weekend_spending > weekday_spending * 1.5:
                    insights.append({
                        'text': "You tend to spend more on weekends. Consider setting a weekend budget to maintain financial discipline.",
                        'type': 'warning'
                    })
            
            # Income insights
            income_model = IncomeDataModel(self.data_manager)
            income_summary = income_model.get_income_summary()
            
            if income_summary:
                monthly_avg = income_summary.get('monthly_average', 0)
                if monthly_avg > 0:
                    insights.append({
                        'text': f"Based on current trends, you're on track to earn ₹{monthly_avg:.0f} this month.",
                        'type': 'prediction'
                    })
            
            # General motivational insights
            insights.append({
                'text': "Great job tracking your finances! Consistent monitoring leads to better financial decisions.",
                'type': 'success'
            })
            
        except Exception as e:
            insights.append({
                'text': f"Unable to generate detailed insights: {str(e)}",
                'type': 'info'
            })
        
        return insights if insights else [
            {
                'text': "Keep tracking your financial data to unlock personalized AI insights!",
                'type': 'info'
            }
        ]
