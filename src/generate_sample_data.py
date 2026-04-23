"""
Generate realistic sample sales data for a pizza restaurant.
Creates 30 days of historical data with proper OrderID tracking.

Each order contains 1-4 line items, which is realistic for a pizza restaurant.
This addresses the bug where len(rows) was being used as the order count.
"""

import pandas as pd
from datetime import datetime, timedelta
import random

# Configuration
DAYS = 30
START_DATE = datetime.now() - timedelta(days=DAYS)

# Menu with realistic prices (CAD)
menu = {
    'Pizza': {
        'Margherita': 14.99, 'Pepperoni': 16.99, 'Hawaiian': 17.99,
        'Vegetarian': 15.99, 'Meat Lovers': 19.99, 'BBQ Chicken': 18.99,
    },
    'Sides': {
        'Garlic Bread': 6.99, 'Caesar Salad': 8.99,
        'Chicken Wings': 12.99, 'Mozzarella Sticks': 9.99,
    },
    'Drinks': {
        'Coke': 2.99, 'Sprite': 2.99, 'Water': 1.99, 'Coffee': 3.49,
    },
    'Desserts': {
        'Tiramisu': 7.99, 'Cheesecake': 7.99, 'Ice Cream': 5.99,
    }
}

day_multiplier = {
    0: 0.7, 1: 0.8, 2: 0.85, 3: 0.95, 4: 1.3, 5: 1.4, 6: 1.1,
}

category_weights = {
    'Pizza': 0.55, 'Sides': 0.20, 'Drinks': 0.20, 'Desserts': 0.05,
}

payment_methods = ['Card', 'Cash', 'Card', 'Card', 'Debit']


def generate_order_items(order_id, order_date):
    """Generate 1-4 unique items for a single order.
    If the same item is picked twice, increase quantity instead of duplicating."""
    num_items = random.choices([1, 2, 3, 4], weights=[0.35, 0.40, 0.20, 0.05])[0]
    payment = random.choice(payment_methods)
    
    # Use dict to merge duplicates into quantity
    items_dict = {}
    
    for _ in range(num_items):
        category = random.choices(
            list(category_weights.keys()),
            weights=list(category_weights.values())
        )[0]
        item = random.choice(list(menu[category].keys()))
        price = menu[category][item]
        
        if item in items_dict:
            # Same item chosen again → increase quantity
            items_dict[item]['Quantity'] += 1
        else:
            items_dict[item] = {
                'Date': order_date.strftime('%Y-%m-%d'),
                'OrderID': order_id,
                'Category': category,
                'Item': item,
                'Quantity': 1,
                'Price': price,
                'PaymentMethod': payment,
            }
    
    # Calculate totals
    items = []
    for item_data in items_dict.values():
        item_data['Total'] = round(item_data['Price'] * item_data['Quantity'], 2)
        items.append(item_data)
    
    return items


records = []
order_counter = 1000

for day_offset in range(DAYS):
    current_date = START_DATE + timedelta(days=day_offset)
    day_of_week = current_date.weekday()
    
    base_orders = random.randint(25, 40)
    orders_today = int(base_orders * day_multiplier[day_of_week])
    
    if random.random() < 0.1:
        orders_today = int(orders_today * 1.3)
    elif random.random() < 0.05:
        orders_today = int(orders_today * 0.6)
    
    for _ in range(orders_today):
        order_id = f"ORD-{order_counter:05d}"
        order_items = generate_order_items(order_id, current_date)
        records.extend(order_items)
        order_counter += 1


df = pd.DataFrame(records)
output_path = '/home/claude/daily_sales_briefing/data/sales_data.csv'
df.to_csv(output_path, index=False)

print(f"✓ Generated {len(df)} line items across {DAYS} days")
print(f"✓ Total unique orders: {df['OrderID'].nunique()}")
print(f"✓ Average items per order: {len(df) / df['OrderID'].nunique():.2f}")
print(f"✓ Total revenue: ${df['Total'].sum():,.2f}")
print(f"✓ Saved to: {output_path}")
print()
print("First 5 rows (note OrderID column):")
print(df.head().to_string())
