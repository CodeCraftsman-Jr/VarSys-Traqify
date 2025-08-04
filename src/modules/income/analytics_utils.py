"""
Income Analytics Utilities
Provides utility functions for data processing, export, and analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import os

from PySide6.QtWidgets import QMessageBox, QFileDialog, QProgressDialog
from PySide6.QtCore import QThread, Signal, QObject


class DataExportWorker(QThread):
    """Worker thread for data export operations"""
    
    progress_updated = Signal(int)
    export_completed = Signal(str)
    export_failed = Signal(str)
    
    def __init__(self, data: pd.DataFrame, filename: str, export_type: str):
        super().__init__()
        self.data = data
        self.filename = filename
        self.export_type = export_type
    
    def run(self):
        """Run the export operation"""
        try:
            self.progress_updated.emit(10)
            
            if self.export_type == 'csv':
                self.data.to_csv(self.filename, index=False)
            elif self.export_type == 'excel':
                with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
                    # Main data sheet
                    self.data.to_excel(writer, sheet_name='Income Data', index=False)
                    self.progress_updated.emit(40)
                    
                    # Summary statistics sheet
                    summary_stats = IncomeAnalyticsUtils.calculate_comprehensive_stats(self.data)
                    summary_df = pd.DataFrame([summary_stats])
                    summary_df.to_excel(writer, sheet_name='Summary Statistics', index=False)
                    self.progress_updated.emit(70)
                    
                    # Monthly breakdown sheet
                    monthly_breakdown = IncomeAnalyticsUtils.get_monthly_breakdown(self.data)
                    monthly_breakdown.to_excel(writer, sheet_name='Monthly Breakdown', index=False)
                    self.progress_updated.emit(90)
            
            self.progress_updated.emit(100)
            self.export_completed.emit(self.filename)
            
        except Exception as e:
            self.export_failed.emit(str(e))


class IncomeAnalyticsUtils:
    """Utility class for income analytics operations"""
    
    @staticmethod
    def calculate_comprehensive_stats(data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive statistics for income data"""
        if data.empty:
            return {}
        
        stats = {}
        
        # Basic statistics
        stats['total_income'] = float(data['earned'].sum())
        stats['average_daily'] = float(data['earned'].mean())
        stats['median_daily'] = float(data['earned'].median())
        stats['std_deviation'] = float(data['earned'].std())
        stats['min_daily'] = float(data['earned'].min())
        stats['max_daily'] = float(data['earned'].max())
        
        # Goal-related statistics
        if 'goal_inc' in data.columns:
            stats['average_goal'] = float(data['goal_inc'].mean())
            stats['total_goals'] = float(data['goal_inc'].sum())
            goals_met = len(data[data['progress'] >= 100])
            stats['goals_met'] = goals_met
            stats['goal_achievement_rate'] = float((goals_met / len(data)) * 100) if len(data) > 0 else 0
        
        # Time-based statistics
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        
        # Current month
        current_month = date.today().month
        current_year = date.today().year
        current_month_data = data_copy[
            (data_copy['date'].dt.month == current_month) & 
            (data_copy['date'].dt.year == current_year)
        ]
        stats['current_month_income'] = float(current_month_data['earned'].sum())
        stats['current_month_days'] = len(current_month_data)
        
        # Previous month for comparison
        if current_month == 1:
            prev_month, prev_year = 12, current_year - 1
        else:
            prev_month, prev_year = current_month - 1, current_year
        
        prev_month_data = data_copy[
            (data_copy['date'].dt.month == prev_month) & 
            (data_copy['date'].dt.year == prev_year)
        ]
        stats['previous_month_income'] = float(prev_month_data['earned'].sum())
        
        # Growth rate
        if stats['previous_month_income'] > 0:
            stats['month_over_month_growth'] = float(
                ((stats['current_month_income'] - stats['previous_month_income']) / 
                 stats['previous_month_income']) * 100
            )
        else:
            stats['month_over_month_growth'] = 0.0
        
        # Consistency metrics
        stats['coefficient_of_variation'] = float((stats['std_deviation'] / stats['average_daily']) * 100) if stats['average_daily'] > 0 else 0
        
        # Streak calculation
        stats['current_streak'] = IncomeAnalyticsUtils.calculate_goal_streak(data)
        stats['longest_streak'] = IncomeAnalyticsUtils.calculate_longest_streak(data)
        
        # Income source analysis
        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings', 
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']
        
        source_stats = {}
        for source in income_sources:
            if source in data.columns:
                source_total = float(data[source].sum())
                source_avg = float(data[source].mean())
                source_percentage = (source_total / stats['total_income']) * 100 if stats['total_income'] > 0 else 0
                
                source_stats[f'{source}_total'] = source_total
                source_stats[f'{source}_average'] = source_avg
                source_stats[f'{source}_percentage'] = source_percentage
        
        stats.update(source_stats)
        
        # Day of week analysis
        data_copy['day_of_week'] = data_copy['date'].dt.day_name()
        day_stats = data_copy.groupby('day_of_week')['earned'].agg(['mean', 'sum']).to_dict()
        
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            if day in day_stats['mean']:
                stats[f'{day.lower()}_average'] = float(day_stats['mean'][day])
                stats[f'{day.lower()}_total'] = float(day_stats['sum'][day])
        
        return stats
    
    @staticmethod
    def get_monthly_breakdown(data: pd.DataFrame) -> pd.DataFrame:
        """Get monthly breakdown of income data"""
        if data.empty:
            return pd.DataFrame()
        
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['year_month'] = data_copy['date'].dt.to_period('M')
        
        # Group by month and calculate statistics
        monthly_stats = data_copy.groupby('year_month').agg({
            'earned': ['sum', 'mean', 'count', 'std'],
            'goal_inc': ['sum', 'mean'],
            'progress': 'mean'
        }).round(2)
        
        # Flatten column names
        monthly_stats.columns = ['_'.join(col).strip() for col in monthly_stats.columns]
        monthly_stats = monthly_stats.reset_index()
        
        # Calculate additional metrics
        monthly_stats['goal_achievement_rate'] = (
            data_copy.groupby('year_month').apply(
                lambda x: (len(x[x['progress'] >= 100]) / len(x)) * 100
            ).round(2).values
        )
        
        # Add income source breakdown
        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings', 
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']
        
        for source in income_sources:
            if source in data_copy.columns:
                monthly_stats[f'{source}_total'] = (
                    data_copy.groupby('year_month')[source].sum().round(2).values
                )
        
        return monthly_stats
    
    @staticmethod
    def calculate_goal_streak(data: pd.DataFrame) -> int:
        """Calculate current goal achievement streak"""
        if data.empty or 'progress' not in data.columns:
            return 0
        
        # Sort by date descending
        sorted_data = data.sort_values('date', ascending=False)
        
        streak = 0
        for _, row in sorted_data.iterrows():
            if row['progress'] >= 100:
                streak += 1
            else:
                break
        
        return streak
    
    @staticmethod
    def calculate_longest_streak(data: pd.DataFrame) -> int:
        """Calculate longest goal achievement streak"""
        if data.empty or 'progress' not in data.columns:
            return 0
        
        # Sort by date ascending
        sorted_data = data.sort_values('date', ascending=True)
        
        max_streak = 0
        current_streak = 0
        
        for _, row in sorted_data.iterrows():
            if row['progress'] >= 100:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    @staticmethod
    def get_income_trends(data: pd.DataFrame, period: str = 'weekly') -> pd.DataFrame:
        """Get income trends for specified period"""
        if data.empty:
            return pd.DataFrame()
        
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        
        if period == 'daily':
            grouped = data_copy.groupby(data_copy['date'].dt.date)
        elif period == 'weekly':
            grouped = data_copy.groupby(data_copy['date'].dt.to_period('W'))
        elif period == 'monthly':
            grouped = data_copy.groupby(data_copy['date'].dt.to_period('M'))
        else:
            raise ValueError("Period must be 'daily', 'weekly', or 'monthly'")
        
        trends = grouped.agg({
            'earned': ['sum', 'mean', 'count'],
            'goal_inc': ['sum', 'mean'],
            'progress': 'mean'
        }).round(2)
        
        # Flatten column names
        trends.columns = ['_'.join(col).strip() for col in trends.columns]
        trends = trends.reset_index()
        
        # Calculate trend direction
        if len(trends) > 1:
            trends['trend'] = trends['earned_sum'].diff().apply(
                lambda x: 'up' if x > 0 else 'down' if x < 0 else 'stable'
            )
        else:
            trends['trend'] = 'stable'
        
        return trends
    
    @staticmethod
    def export_data_with_progress(data: pd.DataFrame, filename: str, export_type: str = 'excel') -> bool:
        """Export data with progress dialog"""
        try:
            # Create progress dialog
            progress = QProgressDialog("Exporting data...", "Cancel", 0, 100)
            progress.setWindowTitle("Export Progress")
            progress.show()
            
            # Create and start worker thread
            worker = DataExportWorker(data, filename, export_type)
            
            def update_progress(value):
                progress.setValue(value)
            
            def export_completed(filename):
                progress.close()
                QMessageBox.information(None, "Export Complete", f"Data exported successfully to:\n{filename}")
            
            def export_failed(error):
                progress.close()
                QMessageBox.critical(None, "Export Failed", f"Failed to export data:\n{error}")
            
            worker.progress_updated.connect(update_progress)
            worker.export_completed.connect(export_completed)
            worker.export_failed.connect(export_failed)
            
            worker.start()
            worker.wait()  # Wait for completion
            
            return True
            
        except Exception as e:
            QMessageBox.critical(None, "Export Error", f"An error occurred during export:\n{str(e)}")
            return False
    
    @staticmethod
    def generate_insights_report(data: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive insights report"""
        if data.empty:
            return {'insights': [], 'recommendations': []}
        
        insights = []
        recommendations = []
        
        stats = IncomeAnalyticsUtils.calculate_comprehensive_stats(data)
        
        # Income performance insights
        if stats.get('goal_achievement_rate', 0) >= 80:
            insights.append("🎯 Excellent goal achievement! You're meeting your targets consistently.")
        elif stats.get('goal_achievement_rate', 0) >= 60:
            insights.append("📈 Good progress on goals, but there's room for improvement.")
        else:
            insights.append("⚠️ Goal achievement is below expectations. Consider reviewing your targets.")
            recommendations.append("Review and adjust your daily income goals to be more realistic.")
        
        # Consistency insights
        cv = stats.get('coefficient_of_variation', 0)
        if cv < 20:
            insights.append("✅ Your income is very consistent with low variability.")
        elif cv < 40:
            insights.append("📊 Your income shows moderate variability.")
        else:
            insights.append("📈 Your income is highly variable. Consider diversifying income sources.")
            recommendations.append("Focus on building more stable, recurring income streams.")
        
        # Growth insights
        growth = stats.get('month_over_month_growth', 0)
        if growth > 10:
            insights.append(f"🚀 Excellent growth! Income increased by {growth:.1f}% this month.")
        elif growth > 0:
            insights.append(f"📈 Positive growth of {growth:.1f}% this month.")
        elif growth < -10:
            insights.append(f"📉 Significant decline of {abs(growth):.1f}% this month.")
            recommendations.append("Analyze factors causing income decline and develop recovery strategies.")
        
        # Source diversification insights
        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings', 
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']
        
        source_contributions = {}
        total_income = stats.get('total_income', 0)
        
        for source in income_sources:
            source_total = stats.get(f'{source}_total', 0)
            if source_total > 0 and total_income > 0:
                percentage = (source_total / total_income) * 100
                source_contributions[source] = percentage
        
        if source_contributions:
            top_source = max(source_contributions, key=source_contributions.get)
            top_percentage = source_contributions[top_source]
            
            if top_percentage > 60:
                insights.append(f"⚠️ Heavy dependence on {top_source.replace('_', ' ').title()} ({top_percentage:.1f}% of income).")
                recommendations.append("Diversify income sources to reduce dependency risk.")
            elif top_percentage > 40:
                insights.append(f"📊 {top_source.replace('_', ' ').title()} is your primary income source ({top_percentage:.1f}%).")
            
            # Identify growing sources
            for source, percentage in source_contributions.items():
                if percentage > 15 and percentage < 30:
                    insights.append(f"🌱 {source.replace('_', ' ').title()} shows potential for growth ({percentage:.1f}% of income).")
        
        # Streak insights
        current_streak = stats.get('current_streak', 0)
        longest_streak = stats.get('longest_streak', 0)
        
        if current_streak >= 7:
            insights.append(f"🔥 Amazing streak! {current_streak} consecutive days of goal achievement.")
        elif current_streak >= 3:
            insights.append(f"💪 Good momentum with {current_streak} consecutive successful days.")
        
        if longest_streak > current_streak and longest_streak >= 7:
            insights.append(f"🏆 Your best streak was {longest_streak} days. You can achieve it again!")
            recommendations.append("Analyze what made your longest streak successful and replicate those conditions.")
        
        return {
            'insights': insights,
            'recommendations': recommendations,
            'statistics': stats
        }
