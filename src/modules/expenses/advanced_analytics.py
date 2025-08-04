"""
Advanced Expense Analytics Module
Enhanced analytics for spending pattern recognition, budget comparisons, and optimization suggestions
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
    QScrollArea, QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


@dataclass
class SpendingPattern:
    """Data class for spending pattern analysis"""
    pattern_type: str
    description: str
    frequency: float
    amount_range: Tuple[float, float]
    categories: List[str]
    confidence: float
    recommendation: str


@dataclass
class BudgetComparison:
    """Data class for budget vs actual comparison"""
    category: str
    budget_amount: float
    actual_amount: float
    variance: float
    variance_percent: float
    status: str
    trend: str
    recommendation: str


@dataclass
class OptimizationSuggestion:
    """Data class for expense optimization suggestions"""
    category: str
    suggestion_type: str
    description: str
    potential_savings: float
    difficulty: str
    priority: int
    action_items: List[str]


class AdvancedExpenseAnalytics:
    """Advanced analytics for expense data"""
    
    def __init__(self):
        self.spending_patterns = []
        self.budget_comparisons = []
        self.optimization_suggestions = []
    
    def analyze_spending_patterns(self, data: pd.DataFrame) -> List[SpendingPattern]:
        """Analyze spending patterns in the data"""
        patterns = []
        
        if data.empty:
            return patterns
        
        try:
            # Ensure date column is datetime
            data = data.copy()
            data['date'] = pd.to_datetime(data['date'])
            data['amount'] = pd.to_numeric(data['amount'], errors='coerce')
            
            # Pattern 1: Recurring expenses (same amount, regular intervals)
            recurring_patterns = self._detect_recurring_expenses(data)
            patterns.extend(recurring_patterns)
            
            # Pattern 2: Weekend vs weekday spending
            weekend_pattern = self._analyze_weekend_spending(data)
            if weekend_pattern:
                patterns.append(weekend_pattern)
            
            # Pattern 3: Monthly spending spikes
            spike_patterns = self._detect_spending_spikes(data)
            patterns.extend(spike_patterns)
            
            # Pattern 4: Category-based patterns
            category_patterns = self._analyze_category_patterns(data)
            patterns.extend(category_patterns)
            
            # Pattern 5: Time-of-day patterns (if timestamp available)
            time_patterns = self._analyze_time_patterns(data)
            patterns.extend(time_patterns)
            
        except Exception as e:
            print(f"Error analyzing spending patterns: {e}")
        
        return patterns
    
    def _detect_recurring_expenses(self, data: pd.DataFrame) -> List[SpendingPattern]:
        """Detect recurring expenses with similar amounts and intervals"""
        patterns = []
        
        try:
            # Group by category and amount (with tolerance)
            data['amount_rounded'] = data['amount'].round(-1)  # Round to nearest 10
            
            for category in data['category'].unique():
                cat_data = data[data['category'] == category]
                
                # Look for amounts that appear multiple times
                amount_counts = cat_data['amount_rounded'].value_counts()
                recurring_amounts = amount_counts[amount_counts >= 3]  # At least 3 occurrences
                
                for amount, count in recurring_amounts.items():
                    amount_data = cat_data[cat_data['amount_rounded'] == amount]
                    
                    # Calculate intervals between transactions
                    dates = sorted(amount_data['date'].tolist())
                    if len(dates) >= 3:
                        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                        avg_interval = np.mean(intervals)
                        interval_std = np.std(intervals)
                        
                        # If intervals are consistent (low standard deviation)
                        if interval_std < avg_interval * 0.3:  # 30% tolerance
                            confidence = min(100, (count / len(cat_data)) * 100)
                            
                            pattern = SpendingPattern(
                                pattern_type="Recurring Expense",
                                description=f"Regular {category} expense of ₹{amount:.0f} every {avg_interval:.0f} days",
                                frequency=count,
                                amount_range=(amount * 0.9, amount * 1.1),
                                categories=[category],
                                confidence=confidence,
                                recommendation=f"Consider setting up automatic budget allocation for this recurring {category} expense"
                            )
                            patterns.append(pattern)
        
        except Exception as e:
            print(f"Error detecting recurring expenses: {e}")
        
        return patterns
    
    def _analyze_weekend_spending(self, data: pd.DataFrame) -> Optional[SpendingPattern]:
        """Analyze weekend vs weekday spending patterns"""
        try:
            data_copy = data.copy()
            data_copy['weekday'] = data_copy['date'].dt.weekday
            data_copy['is_weekend'] = data_copy['weekday'].isin([5, 6])
            
            weekend_spending = data_copy[data_copy['is_weekend']]['amount'].sum()
            weekday_spending = data_copy[~data_copy['is_weekend']]['amount'].sum()
            
            weekend_days = len(data_copy[data_copy['is_weekend']]['date'].dt.date.unique())
            weekday_days = len(data_copy[~data_copy['is_weekend']]['date'].dt.date.unique())
            
            if weekend_days > 0 and weekday_days > 0:
                weekend_avg = weekend_spending / weekend_days
                weekday_avg = weekday_spending / weekday_days
                
                if weekend_avg > weekday_avg * 1.3:  # 30% higher on weekends
                    difference_percent = ((weekend_avg - weekday_avg) / weekday_avg) * 100
                    
                    return SpendingPattern(
                        pattern_type="Weekend Spending",
                        description=f"Weekend spending is {difference_percent:.0f}% higher than weekdays",
                        frequency=weekend_days,
                        amount_range=(weekend_avg * 0.8, weekend_avg * 1.2),
                        categories=data_copy[data_copy['is_weekend']]['category'].unique().tolist(),
                        confidence=min(100, difference_percent),
                        recommendation="Consider setting a weekend spending budget to control discretionary expenses"
                    )
        
        except Exception as e:
            print(f"Error analyzing weekend spending: {e}")
        
        return None
    
    def _detect_spending_spikes(self, data: pd.DataFrame) -> List[SpendingPattern]:
        """Detect unusual spending spikes"""
        patterns = []
        
        try:
            # Group by date and calculate daily spending
            daily_spending = data.groupby(data['date'].dt.date)['amount'].sum()
            
            if len(daily_spending) < 7:  # Need at least a week of data
                return patterns
            
            # Calculate rolling average and standard deviation
            rolling_avg = daily_spending.rolling(window=7, min_periods=3).mean()
            rolling_std = daily_spending.rolling(window=7, min_periods=3).std()
            
            # Detect spikes (spending > mean + 2*std)
            threshold = rolling_avg + (2 * rolling_std)
            spikes = daily_spending[daily_spending > threshold]
            
            if len(spikes) > 0:
                spike_categories = []
                for spike_date in spikes.index:
                    day_data = data[data['date'].dt.date == spike_date]
                    spike_categories.extend(day_data['category'].unique())
                
                unique_categories = list(set(spike_categories))
                avg_spike_amount = spikes.mean()
                
                pattern = SpendingPattern(
                    pattern_type="Spending Spikes",
                    description=f"Detected {len(spikes)} spending spikes averaging ₹{avg_spike_amount:.0f}",
                    frequency=len(spikes),
                    amount_range=(spikes.min(), spikes.max()),
                    categories=unique_categories,
                    confidence=min(100, len(spikes) * 20),
                    recommendation="Review spike days to identify triggers and plan for irregular large expenses"
                )
                patterns.append(pattern)
        
        except Exception as e:
            print(f"Error detecting spending spikes: {e}")
        
        return patterns
    
    def _analyze_category_patterns(self, data: pd.DataFrame) -> List[SpendingPattern]:
        """Analyze spending patterns by category"""
        patterns = []
        
        try:
            category_stats = data.groupby('category')['amount'].agg(['sum', 'count', 'mean', 'std']).reset_index()
            total_spending = data['amount'].sum()
            
            for _, row in category_stats.iterrows():
                category = row['category']
                percentage = (row['sum'] / total_spending) * 100
                
                # High-percentage categories
                if percentage > 20:
                    pattern = SpendingPattern(
                        pattern_type="High-Impact Category",
                        description=f"{category} represents {percentage:.1f}% of total spending",
                        frequency=row['count'],
                        amount_range=(row['mean'] - row['std'], row['mean'] + row['std']),
                        categories=[category],
                        confidence=percentage,
                        recommendation=f"Focus on optimizing {category} expenses for maximum impact"
                    )
                    patterns.append(pattern)
                
                # High-variability categories
                if row['std'] > row['mean'] * 0.8:  # High coefficient of variation
                    pattern = SpendingPattern(
                        pattern_type="Variable Spending",
                        description=f"{category} has highly variable spending (CV: {(row['std']/row['mean']):.1f})",
                        frequency=row['count'],
                        amount_range=(row['mean'] - row['std'], row['mean'] + row['std']),
                        categories=[category],
                        confidence=min(100, (row['std']/row['mean']) * 50),
                        recommendation=f"Consider budgeting strategies for {category} to reduce spending variability"
                    )
                    patterns.append(pattern)
        
        except Exception as e:
            print(f"Error analyzing category patterns: {e}")
        
        return patterns
    
    def _analyze_time_patterns(self, data: pd.DataFrame) -> List[SpendingPattern]:
        """Analyze time-based spending patterns"""
        patterns = []
        
        try:
            # Monthly patterns
            data_copy = data.copy()
            data_copy['month'] = data_copy['date'].dt.month
            monthly_spending = data_copy.groupby('month')['amount'].sum()
            
            if len(monthly_spending) >= 3:
                peak_month = monthly_spending.idxmax()
                low_month = monthly_spending.idxmin()
                
                if monthly_spending[peak_month] > monthly_spending[low_month] * 1.5:
                    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
                                 5: 'May', 6: 'June', 7: 'July', 8: 'August',
                                 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
                    
                    pattern = SpendingPattern(
                        pattern_type="Seasonal Pattern",
                        description=f"Peak spending in {month_names[peak_month]}, lowest in {month_names[low_month]}",
                        frequency=len(monthly_spending),
                        amount_range=(monthly_spending.min(), monthly_spending.max()),
                        categories=data_copy['category'].unique().tolist(),
                        confidence=min(100, ((monthly_spending[peak_month] - monthly_spending[low_month]) / monthly_spending[low_month]) * 20),
                        recommendation="Plan for seasonal spending variations in your budget"
                    )
                    patterns.append(pattern)
        
        except Exception as e:
            print(f"Error analyzing time patterns: {e}")
        
        return patterns
    
    def compare_with_budget(self, data: pd.DataFrame, budget_data: Dict[str, float]) -> List[BudgetComparison]:
        """Compare actual spending with budget"""
        comparisons = []
        
        if data.empty or not budget_data:
            return comparisons
        
        try:
            # Calculate actual spending by category
            actual_spending = data.groupby('category')['amount'].sum().to_dict()
            
            # Get historical data for trend analysis
            data_copy = data.copy()
            data_copy['date'] = pd.to_datetime(data_copy['date'])
            current_month = data_copy['date'].dt.to_period('M').max()
            
            # Calculate trends (compare with previous period if available)
            for category, budget_amount in budget_data.items():
                actual_amount = actual_spending.get(category, 0)
                variance = actual_amount - budget_amount
                variance_percent = (variance / budget_amount * 100) if budget_amount > 0 else 0
                
                # Determine status
                if abs(variance_percent) <= 5:
                    status = "On Track"
                elif variance_percent > 5:
                    status = "Over Budget"
                else:
                    status = "Under Budget"
                
                # Calculate trend (simplified - would need more historical data)
                trend = "Stable"  # Placeholder
                
                # Generate recommendation
                if variance_percent > 20:
                    recommendation = f"Significantly over budget. Review {category} expenses and identify cost-cutting opportunities."
                elif variance_percent > 5:
                    recommendation = f"Slightly over budget. Monitor {category} spending closely."
                elif variance_percent < -20:
                    recommendation = f"Well under budget. Consider reallocating funds or increasing {category} budget."
                else:
                    recommendation = f"Budget performance is good for {category}."
                
                comparison = BudgetComparison(
                    category=category,
                    budget_amount=budget_amount,
                    actual_amount=actual_amount,
                    variance=variance,
                    variance_percent=variance_percent,
                    status=status,
                    trend=trend,
                    recommendation=recommendation
                )
                comparisons.append(comparison)
        
        except Exception as e:
            print(f"Error comparing with budget: {e}")
        
        return comparisons
    
    def generate_optimization_suggestions(self, data: pd.DataFrame, patterns: List[SpendingPattern] = None) -> List[OptimizationSuggestion]:
        """Generate expense optimization suggestions"""
        suggestions = []
        
        if data.empty:
            return suggestions
        
        try:
            # Use patterns if provided, otherwise analyze fresh
            if patterns is None:
                patterns = self.analyze_spending_patterns(data)
            
            # Category-based optimization
            category_stats = data.groupby('category')['amount'].agg(['sum', 'count', 'mean']).reset_index()
            total_spending = data['amount'].sum()
            
            for _, row in category_stats.iterrows():
                category = row['category']
                percentage = (row['sum'] / total_spending) * 100
                
                # High-impact categories
                if percentage > 15:
                    potential_savings = row['sum'] * 0.1  # Assume 10% reduction possible
                    
                    suggestion = OptimizationSuggestion(
                        category=category,
                        suggestion_type="High-Impact Reduction",
                        description=f"Reduce {category} spending by 10% for significant savings",
                        potential_savings=potential_savings,
                        difficulty="Medium",
                        priority=1,
                        action_items=[
                            f"Review all {category} expenses for unnecessary items",
                            f"Compare prices and look for alternatives in {category}",
                            f"Set a monthly limit for {category} expenses"
                        ]
                    )
                    suggestions.append(suggestion)
                
                # High-frequency, low-amount categories
                if row['count'] > 10 and row['mean'] < 500:
                    potential_savings = row['count'] * row['mean'] * 0.05  # 5% reduction
                    
                    suggestion = OptimizationSuggestion(
                        category=category,
                        suggestion_type="Frequency Reduction",
                        description=f"Reduce frequency of small {category} purchases",
                        potential_savings=potential_savings,
                        difficulty="Easy",
                        priority=2,
                        action_items=[
                            f"Batch {category} purchases to reduce impulse buying",
                            f"Set a weekly/monthly limit for {category}",
                            f"Use a shopping list for {category} items"
                        ]
                    )
                    suggestions.append(suggestion)
            
            # Pattern-based suggestions
            for pattern in patterns:
                if pattern.pattern_type == "Weekend Spending":
                    suggestion = OptimizationSuggestion(
                        category="Entertainment/Dining",
                        suggestion_type="Behavioral Change",
                        description="Implement weekend spending controls",
                        potential_savings=pattern.amount_range[1] * 0.2 * 8,  # 20% reduction over 8 weekends
                        difficulty="Medium",
                        priority=2,
                        action_items=[
                            "Set a weekend spending budget",
                            "Plan free or low-cost weekend activities",
                            "Use cash for weekend expenses to limit spending"
                        ]
                    )
                    suggestions.append(suggestion)
                
                elif pattern.pattern_type == "Spending Spikes":
                    suggestion = OptimizationSuggestion(
                        category="Emergency/Irregular",
                        suggestion_type="Planning Improvement",
                        description="Create emergency fund to handle spending spikes",
                        potential_savings=pattern.amount_range[1] * 0.1,
                        difficulty="Hard",
                        priority=1,
                        action_items=[
                            "Build an emergency fund for unexpected expenses",
                            "Plan for known irregular expenses (maintenance, etc.)",
                            "Review spike triggers and create prevention strategies"
                        ]
                    )
                    suggestions.append(suggestion)
            
            # Sort suggestions by priority and potential savings
            suggestions.sort(key=lambda x: (x.priority, -x.potential_savings))
        
        except Exception as e:
            print(f"Error generating optimization suggestions: {e}")
        
        return suggestions
    
    def get_comprehensive_analysis(self, data: pd.DataFrame, budget_data: Dict[str, float] = None) -> Dict[str, Any]:
        """Get comprehensive expense analysis"""
        analysis = {
            'spending_patterns': [],
            'budget_comparisons': [],
            'optimization_suggestions': [],
            'summary': {}
        }
        
        try:
            # Analyze spending patterns
            patterns = self.analyze_spending_patterns(data)
            analysis['spending_patterns'] = patterns
            
            # Budget comparison if budget data provided
            if budget_data:
                comparisons = self.compare_with_budget(data, budget_data)
                analysis['budget_comparisons'] = comparisons
            
            # Generate optimization suggestions
            suggestions = self.generate_optimization_suggestions(data, patterns)
            analysis['optimization_suggestions'] = suggestions
            
            # Summary statistics
            total_potential_savings = sum(s.potential_savings for s in suggestions)
            analysis['summary'] = {
                'total_patterns_found': len(patterns),
                'total_optimization_opportunities': len(suggestions),
                'total_potential_savings': total_potential_savings,
                'analysis_date': datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"Error in comprehensive analysis: {e}")
        
        return analysis


class AdvancedExpenseAnalyticsWidget(QWidget):
    """Widget for displaying advanced expense analytics"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.analytics_engine = AdvancedExpenseAnalytics()
        self.setup_ui()

    def setup_ui(self):
        """Setup the advanced analytics UI"""
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

        # Spending Patterns Section
        self.patterns_widget = self.create_patterns_widget()
        content_layout.addWidget(self.patterns_widget)

        # Budget Comparison Section
        self.budget_widget = self.create_budget_widget()
        content_layout.addWidget(self.budget_widget)

        # Optimization Suggestions Section
        self.optimization_widget = self.create_optimization_widget()
        content_layout.addWidget(self.optimization_widget)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def create_patterns_widget(self):
        """Create spending patterns widget"""
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel

        group_box = QGroupBox("Spending Patterns")
        layout = QVBoxLayout(group_box)

        self.patterns_container = QVBoxLayout()
        layout.addLayout(self.patterns_container)

        return group_box

    def create_budget_widget(self):
        """Create budget comparison widget"""
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout

        group_box = QGroupBox("Budget vs Actual Comparison")
        layout = QVBoxLayout(group_box)

        self.budget_container = QVBoxLayout()
        layout.addLayout(self.budget_container)

        return group_box

    def create_optimization_widget(self):
        """Create optimization suggestions widget"""
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout

        group_box = QGroupBox("Optimization Suggestions")
        layout = QVBoxLayout(group_box)

        self.optimization_container = QVBoxLayout()
        layout.addLayout(self.optimization_container)

        return group_box

    def update_analysis(self, data: pd.DataFrame, budget_data: Dict[str, float] = None):
        """Update the analysis display with new data"""
        try:
            # Get comprehensive analysis
            analysis = self.analytics_engine.get_comprehensive_analysis(data, budget_data)

            # Update patterns
            self.update_patterns_display(analysis['spending_patterns'])

            # Update budget comparison
            self.update_budget_display(analysis['budget_comparisons'])

            # Update optimization suggestions
            self.update_optimization_display(analysis['optimization_suggestions'])

        except Exception as e:
            print(f"Error updating advanced analytics: {e}")

    def update_patterns_display(self, patterns: List[SpendingPattern]):
        """Update spending patterns display"""
        from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout

        # Clear existing patterns
        self.clear_layout(self.patterns_container)

        if not patterns:
            no_data_label = QLabel("No significant spending patterns detected.")
            no_data_label.setStyleSheet("color: #666; font-style: italic;")
            self.patterns_container.addWidget(no_data_label)
            return

        for pattern in patterns[:5]:  # Show top 5 patterns
            pattern_frame = QFrame()
            pattern_frame.setObjectName("patternFrame")
            pattern_frame.setStyleSheet("QFrame#patternFrame { border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px; }")

            pattern_layout = QVBoxLayout(pattern_frame)

            # Pattern header
            header_layout = QHBoxLayout()

            type_label = QLabel(pattern.pattern_type)
            type_label.setStyleSheet("font-weight: bold; color: #2196F3;")
            header_layout.addWidget(type_label)

            header_layout.addStretch()

            confidence_label = QLabel(f"Confidence: {pattern.confidence:.0f}%")
            confidence_label.setStyleSheet("color: #666; font-size: 12px;")
            header_layout.addWidget(confidence_label)

            pattern_layout.addLayout(header_layout)

            # Pattern description
            desc_label = QLabel(pattern.description)
            desc_label.setWordWrap(True)
            pattern_layout.addWidget(desc_label)

            # Recommendation
            rec_label = QLabel(f"💡 {pattern.recommendation}")
            rec_label.setWordWrap(True)
            rec_label.setStyleSheet("color: #4CAF50; font-style: italic; margin-top: 5px;")
            pattern_layout.addWidget(rec_label)

            self.patterns_container.addWidget(pattern_frame)

    def update_budget_display(self, comparisons: List[BudgetComparison]):
        """Update budget comparison display"""
        from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QProgressBar

        # Clear existing comparisons
        self.clear_layout(self.budget_container)

        if not comparisons:
            no_data_label = QLabel("No budget data available for comparison.")
            no_data_label.setStyleSheet("color: #666; font-style: italic;")
            self.budget_container.addWidget(no_data_label)
            return

        for comparison in comparisons:
            comp_frame = QFrame()
            comp_frame.setObjectName("comparisonFrame")
            comp_frame.setStyleSheet("QFrame#comparisonFrame { border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px; }")

            comp_layout = QVBoxLayout(comp_frame)

            # Category header
            header_layout = QHBoxLayout()

            category_label = QLabel(comparison.category)
            category_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            header_layout.addWidget(category_label)

            header_layout.addStretch()

            status_color = "#4CAF50" if comparison.status == "On Track" else "#FF9800" if comparison.status == "Over Budget" else "#2196F3"
            status_label = QLabel(comparison.status)
            status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
            header_layout.addWidget(status_label)

            comp_layout.addLayout(header_layout)

            # Budget vs Actual
            amounts_layout = QHBoxLayout()

            budget_label = QLabel(f"Budget: ₹{comparison.budget_amount:.0f}")
            amounts_layout.addWidget(budget_label)

            actual_label = QLabel(f"Actual: ₹{comparison.actual_amount:.0f}")
            amounts_layout.addWidget(actual_label)

            variance_color = "#F44336" if comparison.variance > 0 else "#4CAF50"
            variance_label = QLabel(f"Variance: ₹{comparison.variance:.0f} ({comparison.variance_percent:.1f}%)")
            variance_label.setStyleSheet(f"color: {variance_color};")
            amounts_layout.addWidget(variance_label)

            comp_layout.addLayout(amounts_layout)

            # Progress bar
            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(int(comparison.budget_amount))
            progress_bar.setValue(int(min(comparison.actual_amount, comparison.budget_amount)))

            if comparison.actual_amount > comparison.budget_amount:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")
            else:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")

            comp_layout.addWidget(progress_bar)

            # Recommendation
            rec_label = QLabel(f"💡 {comparison.recommendation}")
            rec_label.setWordWrap(True)
            rec_label.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
            comp_layout.addWidget(rec_label)

            self.budget_container.addWidget(comp_frame)

    def update_optimization_display(self, suggestions: List[OptimizationSuggestion]):
        """Update optimization suggestions display"""
        from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout

        # Clear existing suggestions
        self.clear_layout(self.optimization_container)

        if not suggestions:
            no_data_label = QLabel("No optimization suggestions available.")
            no_data_label.setStyleSheet("color: #666; font-style: italic;")
            self.optimization_container.addWidget(no_data_label)
            return

        for suggestion in suggestions[:5]:  # Show top 5 suggestions
            sugg_frame = QFrame()
            sugg_frame.setObjectName("suggestionFrame")
            sugg_frame.setStyleSheet("QFrame#suggestionFrame { border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px; }")

            sugg_layout = QVBoxLayout(sugg_frame)

            # Suggestion header
            header_layout = QHBoxLayout()

            category_label = QLabel(f"{suggestion.category} - {suggestion.suggestion_type}")
            category_label.setStyleSheet("font-weight: bold; color: #FF9800;")
            header_layout.addWidget(category_label)

            header_layout.addStretch()

            priority_colors = {1: "#F44336", 2: "#FF9800", 3: "#4CAF50"}
            priority_label = QLabel(f"Priority: {suggestion.priority}")
            priority_label.setStyleSheet(f"color: {priority_colors.get(suggestion.priority, '#666')}; font-weight: bold;")
            header_layout.addWidget(priority_label)

            sugg_layout.addLayout(header_layout)

            # Description and savings
            desc_label = QLabel(suggestion.description)
            desc_label.setWordWrap(True)
            sugg_layout.addWidget(desc_label)

            savings_label = QLabel(f"💰 Potential Savings: ₹{suggestion.potential_savings:.0f} | Difficulty: {suggestion.difficulty}")
            savings_label.setStyleSheet("color: #4CAF50; font-weight: bold; margin-top: 5px;")
            sugg_layout.addWidget(savings_label)

            # Action items
            if suggestion.action_items:
                actions_label = QLabel("Action Items:")
                actions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
                sugg_layout.addWidget(actions_label)

                for action in suggestion.action_items:
                    action_label = QLabel(f"• {action}")
                    action_label.setWordWrap(True)
                    action_label.setStyleSheet("margin-left: 15px; color: #666;")
                    sugg_layout.addWidget(action_label)

            self.optimization_container.addWidget(sugg_frame)

    def clear_layout(self, layout):
        """Clear all widgets from a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
