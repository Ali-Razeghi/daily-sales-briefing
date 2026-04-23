"""
Chart Generator for Daily Sales Briefing
Creates clean, professional charts using matplotlib.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter
import os

# Professional color palette (consistent across all charts)
COLORS = {
    'primary': '#2E75B6',      # Professional blue
    'secondary': '#70AD47',    # Green (positive)
    'warning': '#E76F51',      # Orange (warning)
    'accent': '#F4A261',       # Light orange
    'neutral': '#6C757D',      # Gray
    'background': '#F8F9FA',   # Light background
    'text': '#212529',         # Dark text
}

# Category-specific colors (defaults for common restaurant categories)
# Unknown categories will get a color automatically from the extended palette.
_DEFAULT_CATEGORY_COLORS = {
    'Pizza':    '#E76F51',
    'Sides':    '#F4A261',
    'Drinks':   '#2A9D8F',
    'Desserts': '#E9C46A',
}

# Extended palette for unknown categories (colorblind-friendly)
_EXTENDED_PALETTE = [
    '#264653', '#E76F51', '#F4A261', '#2A9D8F', '#E9C46A',
    '#8D6A9F', '#4A7C59', '#C15B6D', '#457B9D', '#A8A878',
    '#D4A373', '#606C38', '#BC6C25', '#A663CC',
]


def _assign_category_color(category, used_colors=None):
    """
    Assign a color to a category.
    Uses defaults for known categories, picks from extended palette for unknown ones.
    Deterministic: the same category name always gets the same color.
    """
    if category in _DEFAULT_CATEGORY_COLORS:
        return _DEFAULT_CATEGORY_COLORS[category]
    
    # Hash the category name to pick a consistent color from the extended palette
    idx = hash(category) % len(_EXTENDED_PALETTE)
    return _EXTENDED_PALETTE[idx]


def _build_category_colormap(categories):
    """Build a complete {category: color} mapping for a list of categories."""
    return {cat: _assign_category_color(cat) for cat in categories}


def _style_axis(ax):
    """Apply consistent styling to chart axes."""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.tick_params(colors=COLORS['text'], labelsize=9)
    ax.grid(axis='y', linestyle='--', alpha=0.3, color='#CCCCCC')
    ax.set_axisbelow(True)


def _currency(x, pos):
    """Format axis labels as currency."""
    return f'${x:,.0f}'


def create_daily_revenue_trend(trend_data, output_path):
    """
    Create a bar chart of daily revenue for the last N days.
    Highlights the most recent day in a different color.
    """
    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=100)
    
    days = [d['day'] for d in trend_data]
    revenues = [d['revenue'] for d in trend_data]
    
    # Color the last bar differently to highlight "today"
    colors = [COLORS['primary']] * (len(days) - 1) + [COLORS['warning']]
    
    bars = ax.bar(days, revenues, color=colors, width=0.6, edgecolor='white', linewidth=1.5)
    
    # Add value labels on top of each bar
    max_rev = max(revenues)
    for bar, rev in zip(bars, revenues):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_rev * 0.02,
                f'${rev:,.0f}', ha='center', fontsize=9, color=COLORS['text'], fontweight='bold')
    
    ax.set_title('7-Day Revenue Trend', fontsize=13, fontweight='bold', 
                 color=COLORS['text'], pad=15, loc='left')
    ax.set_ylabel('Revenue (CAD)', fontsize=10, color=COLORS['text'])
    ax.yaxis.set_major_formatter(FuncFormatter(_currency))
    ax.set_ylim(0, max_rev * 1.15)
    _style_axis(ax)
    
    # Legend
    today_patch = mpatches.Patch(color=COLORS['warning'], label='Today')
    prev_patch = mpatches.Patch(color=COLORS['primary'], label='Previous Days')
    ax.legend(handles=[today_patch, prev_patch], loc='upper left', frameon=False, fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return output_path


def create_top_items_chart(top_items, output_path):
    """
    Horizontal bar chart of top-selling items by revenue.
    """
    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=100)
    
    items = [item['item'] for item in top_items]
    revenues = [item['revenue'] for item in top_items]
    
    # Reverse so the top item appears at the top of the chart
    items.reverse()
    revenues.reverse()
    
    # Gradient colors (top item gets the strongest color)
    colors = [COLORS['primary']] * len(items)
    colors[-1] = COLORS['secondary']  # Top item in green
    
    bars = ax.barh(items, revenues, color=colors, height=0.65, edgecolor='white', linewidth=1.5)
    
    # Add value labels
    max_rev = max(revenues)
    for bar, rev in zip(bars, revenues):
        ax.text(bar.get_width() + max_rev * 0.01, bar.get_y() + bar.get_height()/2,
                f'${rev:,.0f}', va='center', fontsize=9, color=COLORS['text'], fontweight='bold')
    
    ax.set_title('Top 5 Items by Revenue (Last 7 Days)', fontsize=13, fontweight='bold',
                 color=COLORS['text'], pad=15, loc='left')
    ax.set_xlabel('Revenue (CAD)', fontsize=10, color=COLORS['text'])
    ax.xaxis.set_major_formatter(FuncFormatter(_currency))
    ax.set_xlim(0, max_rev * 1.18)
    _style_axis(ax)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return output_path


def create_category_donut(categories, output_path):
    """
    Donut chart showing revenue breakdown by category.
    """
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    
    labels = [cat['category'] for cat in categories]
    values = [cat['revenue'] for cat in categories]
    colormap = _build_category_colormap(labels)
    colors = [colormap[cat] for cat in labels]
    
    # Create donut with a hole in the middle
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors, autopct='%1.1f%%',
        startangle=90, pctdistance=0.80,
        wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2),
        textprops=dict(fontsize=10, color=COLORS['text'])
    )
    
    # Make percent labels bold and white
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9)
    
    # Add total in the center
    total = sum(values)
    ax.text(0, 0.1, f'${total:,.0f}', ha='center', va='center', 
            fontsize=18, fontweight='bold', color=COLORS['text'])
    ax.text(0, -0.15, 'Total', ha='center', va='center',
            fontsize=10, color=COLORS['neutral'])
    
    ax.set_title('Revenue by Category (Last 7 Days)', fontsize=13, fontweight='bold',
                 color=COLORS['text'], pad=15)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return output_path


def generate_all_charts(analyzer, output_dir, date_suffix=None):
    """
    Generate all charts and return paths.
    
    Parameters:
    -----------
    analyzer : SalesAnalyzer
    output_dir : str
    date_suffix : str, optional
        Date suffix for filenames (e.g., '2026-04-20'). If None, uses today's date
        from the analyzer. This prevents overwrites when running multiple days.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Use the analyzer's date so charts match the report they're for
    if date_suffix is None:
        summary = analyzer.daily_summary()
        date_suffix = summary['date'] if summary else 'latest'
    
    paths = {}
    
    # 1. Daily revenue trend
    trend = analyzer.daily_revenue_trend(days=7)
    paths['trend'] = create_daily_revenue_trend(
        trend, os.path.join(output_dir, f'chart_trend_{date_suffix}.png')
    )
    
    # 2. Top items
    top = analyzer.top_items(n=5, days=7)
    paths['top_items'] = create_top_items_chart(
        top, os.path.join(output_dir, f'chart_top_items_{date_suffix}.png')
    )
    
    # 3. Category donut
    categories = analyzer.category_breakdown(days=7)
    paths['categories'] = create_category_donut(
        categories, os.path.join(output_dir, f'chart_categories_{date_suffix}.png')
    )
    
    return paths


if __name__ == '__main__':
    from analyzer import SalesAnalyzer
    
    analyzer = SalesAnalyzer('/home/claude/morning_briefing/data/sales_data.csv')
    paths = generate_all_charts(analyzer, '/home/claude/morning_briefing/reports/')
    
    print("✓ Charts generated:")
    for name, path in paths.items():
        print(f"  - {name}: {path}")
