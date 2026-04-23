# Daily Sales Briefing — Community Edition

**Automated daily sales reports for small businesses — delivered to your inbox every morning.**

A Python tool that reads yesterday's sales data, analyzes it, generates a polished PDF report with charts, and emails it to the business owner. Built for small businesses (restaurants, cafés, retail shops) that want a quick daily overview without logging into complex dashboards.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Edition](https://img.shields.io/badge/edition-community-orange.svg)
![License](https://img.shields.io/badge/license-Portfolio_Use_Only-red.svg)

---

## About This Edition

This repository contains the **Community Edition** — a **feature-limited portfolio demonstration**. The full Pro Edition includes additional features (see Feature Matrix below) and is available as a commercial product.

**This Community Edition is for:**
- Code review and portfolio evaluation
- Learning and personal experimentation
- Evaluating the core architecture

**For commercial deployment**, contact me for the Pro Edition with full features, setup service, and ongoing support.

---

## What This Is (And What It Isn't)

**This is** an automated daily reporting pipeline. You give it sales data, it generates a PDF and emails it on a schedule.

**This is not** an interactive web dashboard. There is no UI, no filtering, no drill-down. If you need that, consider pairing this with Streamlit or Metabase.

---

## Feature Matrix

| Feature | Community Edition | Pro Edition |
|---|:---:|:---:|
| **Data Sources** | | |
| Standard CSV import | ✅ | ✅ |
| Basic Excel import with column mapping | ✅ | ✅ |
| Square POS direct import | Stub only | ✅ Full |
| Shopify POS direct import | Stub only | ✅ Full |
| Clover POS adapter | ❌ | ✅ |
| Lightspeed Restaurant adapter | ❌ | ✅ |
| Advanced Excel (multi-sheet, formulas) | ❌ | ✅ |
| **Analysis** | | |
| Daily summary metrics | ✅ | ✅ |
| Day-over-day comparison | ✅ | ✅ |
| Week-over-week comparison | ✅ | ✅ |
| Top items + category breakdown | ✅ | ✅ |
| Threshold-based alerts | ✅ | ✅ |
| Weekday-aware benchmarking | ❌ | ✅ |
| Rolling baseline + z-score anomalies | ❌ | ✅ |
| Seasonality & holiday awareness | ❌ | ✅ |
| Context-aware human-readable insights | Basic (2-3) | ✅ (8+) |
| Category momentum tracking | ❌ | ✅ |
| Predictive forecasting | ❌ | ✅ |
| **Reporting** | | |
| Branded PDF report | ✅ | ✅ |
| Business name in header | ✅ | ✅ |
| Customer logo in header | ❌ | ✅ |
| Custom color themes | ❌ | ✅ |
| Multi-page dynamic scaling | Basic | ✅ Advanced |
| **Delivery** | | |
| Gmail SMTP delivery | ✅ | ✅ |
| Environment variable credentials | ✅ | ✅ |
| Email retry on failure | 1 retry | Exponential backoff + fallback SMTP |
| Rich HTML email body with insights | Basic | ✅ Full |
| SMS / WhatsApp delivery | ❌ | ✅ |
| Slack channel delivery | ❌ | ✅ |
| **Operations** | | |
| Data validation layer | ✅ | ✅ |
| Structured logging | ✅ | ✅ |
| Configurable alert thresholds | ✅ | ✅ |
| Single-business config | ✅ | ✅ |
| Multi-business / multi-location | ❌ | ✅ |
| Setup & deployment service | ❌ | ✅ |
| Ongoing support | ❌ | ✅ |

**Contact:** razeghi.a@gmail.com for Pro Edition licensing.

---

## Quick Start (Community Edition)

**Requirements:** Python 3.9 or higher

```bash
git clone https://github.com/Ali-Razeghi/daily-sales-briefing.git
cd daily-sales-briefing
pip install -r requirements.txt

# Create your config from the template
cp config/config.ini.example config/config.ini

# Try it with the included sample data
python src/main.py --no-email
```

The PDF will be saved to `reports/briefing_YYYY-MM-DD.pdf`.

---

## Input Data Format

```csv
Date,OrderID,Category,Item,Quantity,Price,Total,PaymentMethod
2026-04-20,ORD-1001,Pizza,Margherita,1,14.99,14.99,Card
2026-04-20,ORD-1001,Drinks,Coke,2,2.99,5.98,Card
```

Required columns: `Date`, `Category`, `Item`, `Quantity`, `Price`, `Total`. 
`OrderID` strongly recommended for accurate order counts.

See `INPUT_GUIDE.md` for details on handling real customer data.

---

## Email Setup

Recommended: use environment variables for credentials.

```bash
export BRIEFING_SMTP_EMAIL="you@gmail.com"
export BRIEFING_SMTP_PASSWORD="your-gmail-app-password"
```

For Gmail, you need an App Password (not your regular password):
https://myaccount.google.com/apppasswords

Then run:
```bash
python src/main.py
```

---

## Production Deployment

For production, prefer cron (Linux/macOS) or Task Scheduler (Windows).

**Example cron entry** (daily at 8:00 AM):
```cron
0 8 * * * cd /path/to/daily_sales_briefing && /usr/bin/python3 src/main.py
```

---

## Project Structure

```
daily_sales_briefing/
├── src/
│   ├── main.py                 # Pipeline entry point
│   ├── analyzer.py             # Sales analysis (basic version)
│   ├── adapters.py             # Data adapters (CSV + basic Excel)
│   ├── validator.py            # Data quality validation
│   ├── chart_generator.py      # Matplotlib charts
│   ├── pdf_generator.py        # ReportLab PDFs
│   ├── email_sender.py         # SMTP delivery
│   ├── scheduler.py            # Daily scheduler (demo)
│   └── generate_sample_data.py # Creates sample data
├── config/
│   └── config.ini.example      # Configuration template
├── data/
│   └── sales_data.csv          # Sample data (30 days)
├── reports/                    # Generated PDFs
├── logs/                       # Rotating log files
├── requirements.txt
├── LICENSE
├── README.md
├── INPUT_GUIDE.md              # Real-world data handling
├── sample_report.pdf           # Example output
└── sample_report_page1.jpg     # Preview image
```

---

## Tech Stack

- **pandas** — data analysis
- **matplotlib** — chart generation
- **ReportLab** — PDF creation
- **smtplib** — email delivery (standard library)
- **schedule** — daily scheduling
- **logging** — structured logging (standard library)

---

## License

This project is provided for **portfolio demonstration and personal evaluation only**. Commercial use, redistribution, or modification without written permission is not allowed.

For commercial licensing or the Pro Edition, contact: **razeghi.a@gmail.com**

See [LICENSE](LICENSE) for full terms.

---

## Author

**Ali Razeghi** — Python developer focused on practical data solutions for business problems.

- GitHub: [@Ali-Razeghi](https://github.com/Ali-Razeghi)
- LinkedIn: [linkedin.com/in/razeghi-ali](https://www.linkedin.com/in/razeghi-ali/)
- Email: razeghi.a@gmail.com

Built as a portfolio project demonstrating end-to-end Python development: data validation, analysis, visualization, document generation, email automation, and scheduled deployment.
