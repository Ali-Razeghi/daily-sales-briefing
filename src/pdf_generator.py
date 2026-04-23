"""
PDF Report Generator for Daily Sales Briefing
Creates a professional, branded PDF report using ReportLab.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from datetime import datetime
import os


# Color scheme (consistent with charts)
COLORS = {
    'primary': HexColor('#2E75B6'),
    'secondary': HexColor('#70AD47'),
    'warning': HexColor('#E76F51'),
    'accent': HexColor('#F4A261'),
    'neutral': HexColor('#6C757D'),
    'bg_light': HexColor('#F8F9FA'),
    'text_dark': HexColor('#212529'),
    'text_light': HexColor('#FFFFFF'),
    'border': HexColor('#DEE2E6'),
}


def _build_styles():
    """Build custom paragraph styles."""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='BusinessName', parent=styles['Heading1'],
        fontSize=22, textColor=COLORS['text_light'],
        alignment=TA_LEFT, spaceAfter=2, fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='ReportDate', parent=styles['Normal'],
        fontSize=11, textColor=COLORS['text_light'],
        alignment=TA_LEFT, fontName='Helvetica'
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader', parent=styles['Heading2'],
        fontSize=14, textColor=COLORS['text_dark'],
        alignment=TA_LEFT, spaceBefore=14, spaceAfter=8,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='KPILabel', parent=styles['Normal'],
        fontSize=9, textColor=COLORS['neutral'],
        alignment=TA_CENTER, fontName='Helvetica'
    ))
    
    styles.add(ParagraphStyle(
        name='KPIValue', parent=styles['Normal'],
        fontSize=18, textColor=COLORS['text_dark'],
        alignment=TA_CENTER, fontName='Helvetica-Bold',
        spaceBefore=2
    ))
    
    styles.add(ParagraphStyle(
        name='KPIChange', parent=styles['Normal'],
        fontSize=9, alignment=TA_CENTER, fontName='Helvetica-Bold',
        spaceBefore=2
    ))
    
    styles.add(ParagraphStyle(
        name='AlertTitle', parent=styles['Normal'],
        fontSize=10, textColor=COLORS['text_dark'],
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='AlertMessage', parent=styles['Normal'],
        fontSize=9, textColor=COLORS['text_dark'],
        fontName='Helvetica'
    ))
    
    styles.add(ParagraphStyle(
        name='FooterText', parent=styles['Normal'],
        fontSize=8, textColor=COLORS['neutral'],
        alignment=TA_CENTER, fontName='Helvetica'
    ))
    
    return styles


def _header(business_name, report_date):
    """Create the header banner."""
    styles = _build_styles()
    
    header_data = [[
        Paragraph(f"<b>{business_name}</b>", styles['BusinessName']),
        Paragraph(f"Daily Sales Briefing<br/>{report_date}", 
                  ParagraphStyle('HeaderRight', 
                                 parent=styles['ReportDate'],
                                 alignment=TA_RIGHT)),
    ]]
    
    header = Table(header_data, colWidths=[4*inch, 3*inch])
    header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLORS['primary']),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
    ]))
    return header


def _kpi_card(label, value, change=None, change_type='neutral'):
    """Build a single KPI card as a table cell."""
    styles = _build_styles()
    
    cell_contents = [
        Paragraph(label, styles['KPILabel']),
        Paragraph(value, styles['KPIValue']),
    ]
    
    if change is not None:
        color = COLORS['secondary'] if change_type == 'positive' else (
            COLORS['warning'] if change_type == 'negative' else COLORS['neutral']
        )
        arrow = '↑' if change_type == 'positive' else ('↓' if change_type == 'negative' else '→')
        change_style = ParagraphStyle(
            'ChangeStyle', parent=styles['KPIChange'],
            textColor=color
        )
        cell_contents.append(Paragraph(f"{arrow} {change}", change_style))
    
    return cell_contents


def _kpi_row(daily_summary, comparison):
    """Build the 4-card KPI row."""
    # Revenue with change vs yesterday
    rev_change = None
    rev_type = 'neutral'
    if comparison:
        pct = comparison['revenue_pct']
        rev_change = f"{abs(pct):.1f}% vs yesterday"
        rev_type = 'positive' if pct > 0 else 'negative'
    
    # Orders with change
    ord_change = None
    ord_type = 'neutral'
    if comparison:
        pct = comparison['orders_pct']
        ord_change = f"{abs(pct):.1f}% vs yesterday"
        ord_type = 'positive' if pct > 0 else 'negative'
    
    card1 = _kpi_card("REVENUE", f"${daily_summary['total_revenue']:,.2f}", 
                      rev_change, rev_type)
    card2 = _kpi_card("ORDERS", f"{daily_summary['total_orders']}", 
                      ord_change, ord_type)
    card3 = _kpi_card("AVG ORDER", f"${daily_summary['avg_order_value']:.2f}")
    card4 = _kpi_card("ITEMS SOLD", f"{daily_summary['total_items_sold']}")
    
    # Put each card in a nested table so the content stacks vertically
    def _stack(items):
        data = [[item] for item in items]
        t = Table(data, colWidths=[1.65*inch])
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return t
    
    kpi_table = Table(
        [[_stack(card1), _stack(card2), _stack(card3), _stack(card4)]],
        colWidths=[1.72*inch] * 4
    )
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_light']),
        ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
        ('LINEAFTER', (0, 0), (-2, -1), 1, COLORS['border']),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
    ]))
    return kpi_table


def _alerts_section(alerts):
    """Build the alerts section."""
    styles = _build_styles()
    
    if not alerts:
        row_data = [[
            Paragraph("✓", ParagraphStyle('Icon', fontSize=16, 
                                           textColor=COLORS['secondary'],
                                           alignment=TA_CENTER)),
            [
                Paragraph("<b>All systems normal</b>", styles['AlertTitle']),
                Paragraph("No significant events today. Operations are running within normal range.", 
                          styles['AlertMessage']),
            ]
        ]]
        color = COLORS['bg_light']
    else:
        rows = []
        for alert in alerts:
            icon_color = COLORS['secondary'] if alert['type'] == 'positive' else COLORS['warning']
            icon = "↑" if alert['type'] == 'positive' else "!"
            rows.append([
                Paragraph(icon, ParagraphStyle('Icon', fontSize=16,
                                                textColor=icon_color,
                                                alignment=TA_CENTER,
                                                fontName='Helvetica-Bold')),
                [
                    Paragraph(f"<b>{alert['title']}</b>", styles['AlertTitle']),
                    Paragraph(alert['message'], styles['AlertMessage']),
                ]
            ])
        row_data = rows
        color = HexColor('#FFF8E1')  # Light yellow for alerts
    
    alert_table = Table(row_data, colWidths=[0.5*inch, 6.5*inch])
    
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, -1), color),
        ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]
    
    # Add separator lines between alerts
    for i in range(len(row_data) - 1):
        style_commands.append(('LINEBELOW', (0, i), (-1, i), 0.5, COLORS['border']))
    
    alert_table.setStyle(TableStyle(style_commands))
    return alert_table


def _top_items_table(top_items):
    """Build a clean table of top items."""
    styles = _build_styles()
    
    header_style = ParagraphStyle('TableHeader', fontSize=9, fontName='Helvetica-Bold',
                                   textColor=COLORS['text_light'], alignment=TA_LEFT)
    cell_style = ParagraphStyle('TableCell', fontSize=9, fontName='Helvetica',
                                 textColor=COLORS['text_dark'], alignment=TA_LEFT)
    num_style = ParagraphStyle('TableNum', fontSize=9, fontName='Helvetica',
                                textColor=COLORS['text_dark'], alignment=TA_RIGHT)
    
    data = [[
        Paragraph("#", header_style),
        Paragraph("ITEM", header_style),
        Paragraph("QTY", ParagraphStyle('Hr', parent=header_style, alignment=TA_RIGHT)),
        Paragraph("LINE ITEMS", ParagraphStyle('Hr', parent=header_style, alignment=TA_RIGHT)),
        Paragraph("REVENUE", ParagraphStyle('Hr', parent=header_style, alignment=TA_RIGHT)),
    ]]
    
    for i, item in enumerate(top_items, 1):
        data.append([
            Paragraph(str(i), cell_style),
            Paragraph(item['item'], cell_style),
            Paragraph(f"{item['quantity']}", num_style),
            Paragraph(f"{item['line_items']}", num_style),
            Paragraph(f"${item['revenue']:,.2f}", num_style),
        ])
    
    table = Table(data, colWidths=[0.4*inch, 2.5*inch, 0.8*inch, 1*inch, 1.3*inch])
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        # Body rows - alternating
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, COLORS['bg_light']]),
        # All cells
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
    ]))
    return table


def _footer_text(business_name):
    """Footer text at bottom of report."""
    styles = _build_styles()
    return Paragraph(
        f"Generated by Daily Sales Briefing &nbsp;•&nbsp; "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;•&nbsp; "
        f"Confidential report for {business_name}",
        styles['FooterText']
    )


def generate_pdf(analyzer, chart_paths, output_path, business_name="Pizza Corner"):
    """
    Generate a complete morning briefing PDF report.
    
    Parameters:
    -----------
    analyzer : SalesAnalyzer
        The analyzer instance with loaded sales data
    chart_paths : dict
        Dictionary with paths to generated chart PNGs
    output_path : str
        Where to save the PDF
    business_name : str
        Name of the business (shown in header)
    """
    styles = _build_styles()
    
    # Gather all data
    summary = analyzer.daily_summary()
    comparison = analyzer.comparison_vs_previous_day()
    alerts = analyzer.generate_alerts()
    top_items = analyzer.top_items(n=5, days=7)
    
    # Format date nicely
    report_date = datetime.strptime(summary['date'], '%Y-%m-%d')
    date_str = report_date.strftime('%A, %B %d, %Y')
    
    # Build document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.5*inch, rightMargin=0.5*inch,
        topMargin=0, bottomMargin=0.4*inch,
        title=f"Daily Sales Briefing - {business_name} - {summary['date']}",
        author="Daily Sales Briefing"
    )
    
    # Build content flow
    content = []
    
    # 1. Header banner (full width, no margins)
    content.append(_header(business_name, date_str))
    content.append(Spacer(1, 0.25*inch))
    
    # 2. KPI cards
    content.append(Paragraph("Today's Performance", styles['SectionHeader']))
    content.append(_kpi_row(summary, comparison))
    content.append(Spacer(1, 0.2*inch))
    
    # 3. Alerts
    content.append(Paragraph("Intelligent Alerts", styles['SectionHeader']))
    content.append(_alerts_section(alerts))
    content.append(Spacer(1, 0.2*inch))
    
    # 4. Revenue trend chart
    content.append(Paragraph("Revenue Trend", styles['SectionHeader']))
    if os.path.exists(chart_paths['trend']):
        trend_img = Image(chart_paths['trend'], width=7.2*inch, height=3.1*inch)
        content.append(trend_img)
    content.append(Spacer(1, 0.2*inch))
    
    # 5. Two-column: Top items chart + Category donut
    if os.path.exists(chart_paths['top_items']) and os.path.exists(chart_paths['categories']):
        content.append(Paragraph("Top Items & Category Breakdown", styles['SectionHeader']))
        items_img = Image(chart_paths['top_items'], width=4.2*inch, height=2*inch)
        cat_img = Image(chart_paths['categories'], width=2.8*inch, height=2*inch)
        two_col = Table([[items_img, cat_img]], colWidths=[4.3*inch, 2.9*inch])
        two_col.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        content.append(two_col)
    content.append(Spacer(1, 0.2*inch))
    
    # 6. Detailed top items table
    content.append(Paragraph("Top Items — Detailed View", styles['SectionHeader']))
    content.append(_top_items_table(top_items))
    content.append(Spacer(1, 0.3*inch))
    
    # 7. Footer
    content.append(HRFlowable(width="100%", thickness=0.5, color=COLORS['border']))
    content.append(Spacer(1, 0.1*inch))
    content.append(_footer_text(business_name))
    
    # Build PDF
    doc.build(content)
    return output_path


if __name__ == '__main__':
    from analyzer import SalesAnalyzer
    from chart_generator import generate_all_charts
    
    # Load data and generate charts
    analyzer = SalesAnalyzer('/home/claude/morning_briefing/data/sales_data.csv')
    chart_paths = generate_all_charts(analyzer, '/home/claude/morning_briefing/reports/')
    
    # Generate PDF
    pdf_path = '/home/claude/morning_briefing/reports/morning_briefing.pdf'
    generate_pdf(analyzer, chart_paths, pdf_path, business_name="Pizza Corner")
    
    print(f"✓ PDF generated: {pdf_path}")
    
    # Show file size
    size_kb = os.path.getsize(pdf_path) / 1024
    print(f"  File size: {size_kb:.1f} KB")
