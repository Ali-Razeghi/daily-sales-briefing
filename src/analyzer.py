"""
Sales Data Analyzer (Community Edition)

╔══════════════════════════════════════════════════════════════════════════╗
║                       COMMUNITY EDITION NOTICE                           ║
║                                                                          ║
║  This version includes basic threshold-based alerts.                     ║
║                                                                          ║
║  The Pro edition adds:                                                   ║
║    - Weekday-aware benchmarking (Mon vs previous Mondays)                ║
║    - Rolling baseline with z-score anomaly detection                     ║
║    - Seasonality & holiday awareness                                     ║
║    - Promotion day detection                                             ║
║    - Context-aware human-readable insights                               ║
║    - Category momentum tracking                                          ║
║    - Predictive forecasting with confidence intervals                    ║
║                                                                          ║
║  Contact: razeghi.a@gmail.com for commercial licensing.                  ║
╚══════════════════════════════════════════════════════════════════════════╝

Fixes from v1 code review:
  - Order count uses unique OrderID (not row count)
  - Trend uses complete calendar range
  - Division-by-zero protection
  - Configurable alert thresholds
  - Data validation layer integration
"""

import logging
from datetime import timedelta
import pandas as pd

logger = logging.getLogger(__name__)


class SalesAnalyzer:
    """Analyzes sales data and generates business insights."""
    
    DEFAULT_THRESHOLDS = {
        'daily_revenue_up_pct': 20.0,
        'daily_revenue_down_pct': 20.0,
        'weekly_change_pct': 15.0,
        'above_average_multiplier': 1.3,
    }
    
    def __init__(self, csv_path, source_type='standard', adapter_kwargs=None,
                 thresholds=None, validate=True):
        from adapters import get_adapter
        from validator import validate_sales_data
        
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
        
        logger.info(f"Loading data from {csv_path} (source_type={source_type})")
        adapter = get_adapter(source_type, **(adapter_kwargs or {}))
        df = adapter.process(csv_path)
        
        if validate:
            df, self.quality_report = validate_sales_data(df)
            if self.quality_report.has_errors:
                raise ValueError(
                    f"Data validation failed:\n{self.quality_report.summary()}"
                )
        else:
            self.quality_report = None
        
        self.df = df.copy()
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        
        if len(self.df) == 0:
            raise ValueError("No valid rows in data after validation")
        
        self.today = self.df['Date'].max()
        self.yesterday = self.today - timedelta(days=1)
        
        self.has_order_id = 'OrderID' in self.df.columns
        if not self.has_order_id:
            logger.warning(
                "No 'OrderID' column found. Order counts will approximate "
                "using row counts. Add OrderID for accurate metrics."
            )
    
    def _count_orders(self, data):
        """Count unique orders. Uses OrderID if available."""
        if len(data) == 0:
            return 0
        if self.has_order_id:
            return data['OrderID'].nunique()
        return len(data)
    
    def _safe_pct_change(self, current, previous):
        """Percent change with division-by-zero protection."""
        if previous is None or previous == 0:
            return None
        return round(((current - previous) / previous) * 100, 1)
    
    def daily_summary(self, date=None):
        if date is None:
            date = self.today
        
        day_data = self.df[self.df['Date'] == date]
        if len(day_data) == 0:
            return None
        
        total_revenue = day_data['Total'].sum()
        total_orders = self._count_orders(day_data)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'day_of_week': date.strftime('%A'),
            'total_revenue': round(total_revenue, 2),
            'total_orders': total_orders,
            'unique_items': day_data['Item'].nunique(),
            'avg_order_value': round(avg_order_value, 2),
            'total_items_sold': int(day_data['Quantity'].sum()),
            'line_items': len(day_data),
        }
    
    def comparison_vs_previous_day(self):
        today_stats = self.daily_summary(self.today)
        yesterday_stats = self.daily_summary(self.yesterday)
        
        if not today_stats:
            return None
        
        if not yesterday_stats:
            return {
                'revenue_change': None, 'revenue_pct': None,
                'orders_change': None, 'orders_pct': None,
                'note': 'No data for previous day'
            }
        
        revenue_change = today_stats['total_revenue'] - yesterday_stats['total_revenue']
        orders_change = today_stats['total_orders'] - yesterday_stats['total_orders']
        
        return {
            'revenue_change': round(revenue_change, 2),
            'revenue_pct': self._safe_pct_change(
                today_stats['total_revenue'], yesterday_stats['total_revenue']
            ),
            'orders_change': orders_change,
            'orders_pct': self._safe_pct_change(
                today_stats['total_orders'], yesterday_stats['total_orders']
            ),
        }
    
    def weekly_comparison(self):
        this_week_start = self.today - timedelta(days=6)
        last_week_end = this_week_start - timedelta(days=1)
        last_week_start = last_week_end - timedelta(days=6)
        
        this_week = self.df[
            (self.df['Date'] >= this_week_start) & (self.df['Date'] <= self.today)
        ]
        last_week = self.df[
            (self.df['Date'] >= last_week_start) & (self.df['Date'] <= last_week_end)
        ]
        
        this_revenue = this_week['Total'].sum() if len(this_week) > 0 else 0
        last_revenue = last_week['Total'].sum() if len(last_week) > 0 else 0
        
        if last_revenue == 0:
            if this_revenue == 0:
                return None
            return {
                'this_week_revenue': round(this_revenue, 2),
                'last_week_revenue': 0,
                'change': round(this_revenue, 2),
                'pct_change': None,
                'note': 'No revenue last week for comparison'
            }
        
        change = this_revenue - last_revenue
        pct = (change / last_revenue) * 100
        
        return {
            'this_week_revenue': round(this_revenue, 2),
            'last_week_revenue': round(last_revenue, 2),
            'change': round(change, 2),
            'pct_change': round(pct, 1),
        }
    
    def top_items(self, n=5, days=7):
        start_date = self.today - timedelta(days=days-1)
        recent = self.df[self.df['Date'] >= start_date]
        
        if len(recent) == 0:
            return []
        
        top = recent.groupby('Item').agg(
            revenue=('Total', 'sum'),
            quantity=('Quantity', 'sum'),
            line_items=('Item', 'count')
        ).sort_values('revenue', ascending=False).head(n)
        
        return [
            {
                'item': item,
                'revenue': round(row['revenue'], 2),
                'quantity': int(row['quantity']),
                'line_items': int(row['line_items']),
            }
            for item, row in top.iterrows()
        ]
    
    def category_breakdown(self, days=7):
        start_date = self.today - timedelta(days=days-1)
        recent = self.df[self.df['Date'] >= start_date]
        
        if len(recent) == 0:
            return []
        
        breakdown = recent.groupby('Category').agg(
            revenue=('Total', 'sum'),
            line_items=('Category', 'count')
        ).sort_values('revenue', ascending=False)
        
        total_revenue = breakdown['revenue'].sum()
        if total_revenue == 0:
            return []
        
        return [
            {
                'category': cat,
                'revenue': round(row['revenue'], 2),
                'line_items': int(row['line_items']),
                'pct': round((row['revenue'] / total_revenue) * 100, 1),
            }
            for cat, row in breakdown.iterrows()
        ]
    
    def daily_revenue_trend(self, days=7):
        """Trend with complete calendar range (fix #3)."""
        start_date = self.today - timedelta(days=days-1)
        recent = self.df[self.df['Date'] >= start_date]
        revenue_by_date = recent.groupby('Date')['Total'].sum()
        
        full_range = pd.date_range(start=start_date, end=self.today, freq='D')
        
        trend = []
        for date in full_range:
            revenue = revenue_by_date.get(date, 0.0)
            trend.append({
                'date': date.strftime('%Y-%m-%d'),
                'day': date.strftime('%a'),
                'revenue': round(float(revenue), 2),
                'has_data': date in revenue_by_date.index,
            })
        
        return trend
    
    def generate_insights(self):
        """
        Generate human-readable insights from the data.
        
        [COMMUNITY EDITION] Returns 2-3 basic insights based on today's data.
        
        [PRO EDITION] Returns 8+ insights including:
            - Weekday comparisons ("Monday sales are 15% below average Mondays")
            - Category momentum ("Drinks category up 23% this week")
            - Item velocity changes ("Pepperoni sales accelerating")
            - Anomaly explanations with possible causes
            - Forecasts ("Based on 30-day trend, expect $650 tomorrow")
        """
        insights = []
        
        # Insight 1: Revenue headline
        summary = self.daily_summary()
        if summary:
            insights.append(
                f"Revenue today: ${summary['total_revenue']:,.2f} "
                f"across {summary['total_orders']} orders."
            )
        
        # Insight 2: Day-over-day context
        comparison = self.comparison_vs_previous_day()
        if comparison and comparison.get('revenue_pct') is not None:
            direction = "up" if comparison['revenue_pct'] > 0 else "down"
            insights.append(
                f"Sales {direction} {abs(comparison['revenue_pct'])}% versus yesterday."
            )
        
        # Insight 3: Top performer
        top = self.top_items(n=1, days=1)
        if top:
            insights.append(
                f"Top performer today: {top[0]['item']} at ${top[0]['revenue']:,.2f}."
            )
        
        return insights
    
    def generate_alerts(self):
        alerts = []
        
        comparison = self.comparison_vs_previous_day()
        if comparison and comparison.get('revenue_pct') is not None:
            pct = comparison['revenue_pct']
            if pct > self.thresholds['daily_revenue_up_pct']:
                alerts.append({
                    'type': 'positive',
                    'title': 'Strong Sales Day',
                    'message': f"Revenue up {pct}% vs yesterday "
                               f"(+${comparison['revenue_change']:.2f})"
                })
            elif pct < -self.thresholds['daily_revenue_down_pct']:
                alerts.append({
                    'type': 'warning',
                    'title': 'Lower Sales Alert',
                    'message': f"Revenue down {abs(pct)}% vs yesterday "
                               f"(-${abs(comparison['revenue_change']):.2f})"
                })
        
        weekly = self.weekly_comparison()
        if weekly and weekly.get('pct_change') is not None:
            pct = weekly['pct_change']
            if pct > self.thresholds['weekly_change_pct']:
                alerts.append({
                    'type': 'positive',
                    'title': 'Weekly Growth',
                    'message': f"This week is up {pct}% vs last week"
                })
            elif pct < -self.thresholds['weekly_change_pct']:
                alerts.append({
                    'type': 'warning',
                    'title': 'Weekly Decline',
                    'message': f"This week is down {abs(pct)}% vs last week"
                })
        
        today_stats = self.daily_summary(self.today)
        if today_stats:
            recent = self.df[self.df['Date'] >= self.today - timedelta(days=6)]
            daily_totals = recent.groupby('Date')['Total'].sum()
            if len(daily_totals) > 1:
                avg = daily_totals.mean()
                if avg > 0:
                    ratio = today_stats['total_revenue'] / avg
                    if ratio > self.thresholds['above_average_multiplier']:
                        alerts.append({
                            'type': 'positive',
                            'title': 'Above Average Day',
                            'message': f"Revenue is {round((ratio - 1) * 100)}% "
                                       f"above the 7-day average"
                        })
        
        return alerts


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    analyzer = SalesAnalyzer('/home/claude/daily_sales_briefing/data/sales_data.csv')
    
    print("=" * 60)
    print("DAILY SALES BRIEFING - ANALYZER TEST (v2)")
    print("=" * 60)
    
    if analyzer.quality_report:
        print("\n" + analyzer.quality_report.summary())
    
    print("\nTODAY'S SUMMARY")
    print("-" * 40)
    summary = analyzer.daily_summary()
    for key, value in summary.items():
        print(f"  {key:20}: {value}")
    
    print(f"\n  CORRECT: {summary['total_orders']} ORDERS (not {summary['line_items']} line items)")
    print(f"  Avg order value = ${summary['avg_order_value']} (accurate, per order)")
    
    print("\n7-DAY TREND (complete calendar, zero on missing days)")
    print("-" * 40)
    for day in analyzer.daily_revenue_trend():
        marker = '' if day['has_data'] else '  [closed/no data]'
        bar = '#' * int(day['revenue'] / 40)
        print(f"  {day['day']} {day['date']}  ${day['revenue']:>7,.2f}  {bar}{marker}")
    
    print("\nALERTS")
    print("-" * 40)
    alerts = analyzer.generate_alerts()
    if alerts:
        for alert in alerts:
            icon = '[+]' if alert['type'] == 'positive' else '[!]'
            print(f"  {icon} {alert['title']}: {alert['message']}")
    else:
        print("  No significant events today.")
    print()
