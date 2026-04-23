# Input Data Guide

This document explains exactly what data Daily Sales Briefing needs, what formats it supports, and how to handle real-world customer data.

---

## The Standard Format

At its core, the tool needs sales data in a CSV with these **six columns**:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `Date` | Text (YYYY-MM-DD) | The day of the sale | `2026-04-20` |
| `Category` | Text | Product category | `Pizza` |
| `Item` | Text | Product name | `Margherita` |
| `Quantity` | Integer | Number of units sold | `2` |
| `Price` | Decimal | Unit price | `14.99` |
| `Total` | Decimal | Line total (Quantity × Price) | `29.98` |

### Example CSV

```csv
Date,Category,Item,Quantity,Price,Total
2026-04-20,Pizza,Margherita,1,14.99,14.99
2026-04-20,Drinks,Coke,2,2.99,5.98
2026-04-20,Sides,Garlic Bread,1,6.99,6.99
```

Each row represents a **line item** in an order, not an entire order. One order with three items produces three rows.

---

## Real-World Reality Check

Most small businesses do **not** have data in this exact format. Here's what you'll actually encounter when working with customers:

### Reality 1 — Paper Records (30–40% of small shops)

Many small shops track sales by hand. They write receipts on paper and total them up at the end of the day. **No digital data exists.**

**Your options:**
- Ask if they use any POS system at all (even a simple one)
- If they don't, the Daily Sales Briefing is not a fit — suggest they start with a free POS app first (Square has a free tier)
- Or, sell them a different service: you build a daily-entry web form, they type in totals, you generate the briefing

### Reality 2 — POS System Exports (40–50%)

The customer uses a POS system and can export data. Common systems in Canada:

- **Square** — very popular, widely used in cafés and retail
- **Clover** — pushed by Moneris (major Canadian payment processor)
- **Lightspeed** — Canadian company, strong in restaurants
- **Toast** — US-based, growing in restaurants
- **Shopify POS** — strong in retail

Each system exports data in a **different format** with different column names. This is where **adapters** come in (see `src/adapters.py`).

### Reality 3 — Manual Excel (20–30%)

The customer keeps a simple Excel file that they (or their staff) update each day. Every business's Excel looks different. Common variations:

- Columns in English, Persian, Arabic, French, etc.
- Date formats like `4/20/2026`, `20-Apr-2026`, `2026/04/20`
- Prices with currency symbols: `$14.99`, `14.99 CAD`, `14,99`
- One sheet per month, or one giant sheet for the year
- Summary rows mixed in with data rows

This is where you earn your consulting fee — cleaning messy Excel into a usable format.

---

## How to Handle Each Format

### Option A: Customer Can Give Standard CSV

This is the easiest case. Just put their file at `data/sales_data.csv` and run:

```bash
python src/main.py --no-email
```

### Option B: Customer Uses Square POS

Square can export sales data as CSV. Here's the workflow:

1. Log into Square Dashboard
2. Go to Reports → Sales → Items
3. Filter by date range
4. Click Export → CSV

In your `config.ini`:

```ini
[data]
csv_path = data/square_export.csv
source_type = square
```

The `SquarePOSAdapter` in `src/adapters.py` handles the column mapping.

### Option C: Customer Uses Shopify POS

Export orders from Shopify admin:

1. Orders → Export → Plain CSV

In your `config.ini`:

```ini
[data]
csv_path = data/shopify_export.csv
source_type = shopify
```

### Option D: Custom Excel File

When the customer sends you a unique Excel format, you need to write a custom mapping. Edit `src/main.py` and use `ExcelAdapter`:

```python
from adapters import ExcelAdapter

adapter = ExcelAdapter(
    column_map={
        'Date': 'Sale Date',              # their column name
        'Category': 'Product Type',
        'Item': 'Product',
        'Quantity': 'Qty',
        'Price': 'Unit Price',
        'Total': 'Amount',
    },
    sheet_name='April'  # which Excel sheet
)
df = adapter.process('/path/to/customer_file.xlsx')
```

### Option E: Unsupported POS System

If the customer uses a POS system not listed above (Clover, Toast, Lightspeed, etc.), you need to write a new adapter. Follow the pattern in `src/adapters.py` — inherit from `BaseAdapter`, implement `load()` and `transform()`, and register it in the `get_adapter()` factory.

---

## Sales Process — What to Ask a Potential Customer

When meeting a small business owner, here's a simple checklist:

**1. Do you track daily sales electronically?**
- Yes → go to step 2
- No → this tool isn't a fit yet. Offer a different service or suggest Square first.

**2. What system do you use?**
- Square / Shopify → supported out of the box
- Clover / Toast / Lightspeed → you'll build a custom adapter (adds 1–2 days to delivery)
- Excel / Google Sheets → custom column mapping (a few hours)
- Custom software → need to see a sample file before quoting

**3. Can you send me a sample export (last 30 days)?**

Before quoting or committing, **always look at actual data first**. The file might be messy, have missing columns, use a weird format, or contain errors. You need to see it before promising anything.

**4. How do you want the briefing delivered?**
- Email (included in the tool)
- Text message / WhatsApp (add-on)
- Printed on paper (add-on — you'd set up auto-print)

---

## Pricing Guidance

This is guidance, not advice — adjust based on your market:

| Scenario | Setup Fee | Monthly Fee |
|----------|-----------|-------------|
| Standard CSV customer | $100–200 | $20–30 |
| Square or Shopify | $200–400 | $30–50 |
| Custom Excel | $300–500 | $30–50 |
| New POS adapter needed | $500–800 | $40–60 |
| Multi-location, custom alerts | $800–1500 | $80–150 |

The monthly fee covers hosting (if you host it), adjustments, and support. For customers who want to run it themselves on their own computer, charge only the setup fee plus maybe $50/year for occasional updates.

---

## Quality Checks — Before Delivering to a Customer

Before handing off the tool to a paying customer, verify:

- [ ] You've tested with **their actual data**, not sample data
- [ ] The PDF renders correctly with their business name and logo
- [ ] Email delivers reliably to their address (test for 3 days)
- [ ] The scheduled time matches their preference (many owners want 7 AM, not 8)
- [ ] Alerts trigger correctly on their data (run on a known bad day to verify)
- [ ] You've documented how they add a new product category
- [ ] They know how to contact you if something breaks

---

## What to Do When Data Is Missing or Wrong

Real-world data is messy. Here are common issues and fixes:

**Missing dates** — Some rows have no date
→ Skip those rows or ask the customer what happened

**Negative totals** — Refunds or voids
→ Decide with the customer: include (net revenue) or exclude (gross sales)

**Duplicate rows** — Same transaction exported twice
→ Deduplicate using a unique order ID

**Wrong date format** — US format `MM/DD/YYYY` vs European `DD/MM/YYYY`
→ Use `pd.to_datetime(df['Date'], dayfirst=True)` for European

**Missing categories** — Items without a category
→ The adapter fills these with `Uncategorized` by default

**Cash vs card** — Customer wants to track payment method
→ Add a `Payment Method` column; modify the analyzer to split by payment type

---

## Summary

The key insight: **the code is the easy part. Data is the hard part.** Most of your time on a real project will go into understanding the customer's data, writing a clean adapter, and handling edge cases. The briefing pipeline itself is stable and well-tested.

When a customer asks "can you build this for me?", the honest answer is:

> "Yes — but first let me see a sample of your actual sales data. I can give you a firm quote after I look at it."

That single sentence will save you from underquoting, scope creep, and unhappy customers.
