"""
Daily Sales Briefing - Main Entry Point

Runs the full pipeline:
  1. Load & validate sales data
  2. Analyze it
  3. Generate charts
  4. Build PDF report
  5. Send via email (optional)

Usage:
  python3 main.py                 # Full pipeline with email
  python3 main.py --no-email      # Generate PDF only
  python3 main.py --config PATH   # Use a different config file
  python3 main.py --verbose       # Verbose logging for debugging

Security: Email credentials can be set via environment variables:
  BRIEFING_SMTP_EMAIL    — sender email
  BRIEFING_SMTP_PASSWORD — sender password (Gmail App Password)
"""

import argparse
import configparser
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Ensure src/ is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import SalesAnalyzer
from chart_generator import generate_all_charts
from pdf_generator import generate_pdf
from email_sender import send_briefing_email


def setup_logging(project_root, verbose=False):
    """Configure structured logging with both file and console output."""
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    
    # Root logger
    root = logging.getLogger()
    root.setLevel(log_level)
    # Clear any handlers set elsewhere
    for h in list(root.handlers):
        root.removeHandler(h)
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    root.addHandler(console)
    
    # Rotating file handler (keeps last 7 days of logs, 1MB each)
    log_file = os.path.join(log_dir, 'briefing.log')
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=7, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    root.addHandler(file_handler)
    
    return logging.getLogger('main')


def load_config(config_path):
    """Load configuration from INI file."""
    if not os.path.exists(config_path):
        example_path = config_path + '.example'
        if os.path.exists(example_path):
            print(f"Config file not found: {config_path}")
            print(f"Copy {example_path} to {config_path} and fill in your details.")
        else:
            print(f"Config file not found: {config_path}")
        sys.exit(1)
    
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def get_alert_thresholds(config):
    """Extract alert thresholds from config, with fallback to defaults."""
    if 'alerts' not in config:
        return None
    
    thresholds = {}
    for key in ['daily_revenue_up_pct', 'daily_revenue_down_pct', 
                'weekly_change_pct', 'above_average_multiplier']:
        if config.has_option('alerts', key):
            thresholds[key] = config.getfloat('alerts', key)
    
    return thresholds if thresholds else None


def get_adapter_kwargs(config):
    """Build adapter kwargs for Excel source if configured."""
    source_type = config.get('data', 'source_type', fallback='standard')
    
    if source_type != 'excel':
        return {}
    
    if 'excel_mapping' not in config:
        raise ValueError(
            "source_type is 'excel' but [excel_mapping] section is missing from config"
        )
    
    mapping = config['excel_mapping']
    
    # Column mapping from config to adapter format
    column_map = {}
    mapping_keys = {
        'date_col': 'Date',
        'category_col': 'Category',
        'item_col': 'Item',
        'quantity_col': 'Quantity',
        'price_col': 'Price',
        'total_col': 'Total',
        'order_id_col': 'OrderID',
    }
    
    for config_key, std_col in mapping_keys.items():
        if config_key in mapping and mapping[config_key].strip():
            column_map[std_col] = mapping[config_key]
    
    kwargs = {'column_map': column_map}
    if 'sheet_name' in mapping and mapping['sheet_name'].strip():
        kwargs['sheet_name'] = mapping['sheet_name']
    
    return kwargs


def run_pipeline(config, logger, send_email=True):
    """Execute the full briefing generation pipeline."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    csv_path = config['data']['csv_path']
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(project_root, csv_path)
    
    output_dir = config['output']['pdf_output_dir']
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(project_root, output_dir)
    
    business_name = config['business']['name']
    source_type = config.get('data', 'source_type', fallback='standard')
    
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info(f"Daily Sales Briefing — {business_name}")
    logger.info(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Step 1: Load and analyze
    logger.info("Step 1/4: Loading and analyzing data...")
    if not os.path.exists(csv_path):
        logger.error(f"Sales data file not found: {csv_path}")
        return False
    
    try:
        adapter_kwargs = get_adapter_kwargs(config)
        thresholds = get_alert_thresholds(config)
        
        analyzer = SalesAnalyzer(
            csv_path,
            source_type=source_type,
            adapter_kwargs=adapter_kwargs,
            thresholds=thresholds,
        )
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return False
    
    summary = analyzer.daily_summary()
    if not summary:
        logger.error(f"No data available for today.")
        return False
    
    logger.info(f"  Date:    {summary['date']} ({summary['day_of_week']})")
    logger.info(f"  Revenue: ${summary['total_revenue']:,.2f}")
    logger.info(f"  Orders:  {summary['total_orders']}")
    
    # Log data quality summary
    if analyzer.quality_report and analyzer.quality_report.has_warnings:
        logger.warning(
            f"Data quality issues detected. "
            f"{len(analyzer.quality_report.warnings)} warnings logged."
        )
    
    # Step 2: Generate charts
    logger.info("Step 2/4: Generating charts...")
    try:
        chart_paths = generate_all_charts(analyzer, output_dir, date_suffix=summary['date'])
        for name in chart_paths:
            logger.debug(f"  Created: chart_{name}_{summary['date']}.png")
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        return False
    
    # Step 3: Build PDF
    logger.info("Step 3/4: Building PDF report...")
    pdf_filename = f"briefing_{summary['date']}.pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)
    
    try:
        generate_pdf(analyzer, chart_paths, pdf_path, business_name=business_name)
        file_size_kb = os.path.getsize(pdf_path) / 1024
        logger.info(f"  Created: {pdf_filename} ({file_size_kb:.1f} KB)")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return False
    
    # Step 4: Send email
    if send_email:
        logger.info("Step 4/4: Sending email...")
        
        try:
            email_config = {
                'smtp_server': config['email']['smtp_server'],
                'smtp_port': config['email']['smtp_port'],
                'use_tls': config['email']['use_tls'],
                'sender_email': config['email']['sender_email'],
                'sender_password': config['email']['sender_password'],
                'recipient_email': config['email']['recipient_email'],
            }
            
            # Environment variables take priority (resolved inside send_briefing_email)
            env_email = os.environ.get('BRIEFING_SMTP_EMAIL')
            env_password = os.environ.get('BRIEFING_SMTP_PASSWORD')
            
            has_config_creds = (
                'your-email' not in email_config['sender_email']
                and 'your-app-password' not in email_config['sender_password']
            )
            
            if not env_email and not env_password and not has_config_creds:
                logger.warning(
                    "  Email credentials not configured. Skipping email delivery. "
                    "Set BRIEFING_SMTP_EMAIL/BRIEFING_SMTP_PASSWORD or update config.ini."
                )
            else:
                send_briefing_email(email_config, analyzer, pdf_path, business_name)
                logger.info(f"  Sent to: {email_config['recipient_email']}")
        except Exception as e:
            logger.error(f"  Email delivery failed: {e}")
            logger.info(f"  PDF is still available at: {pdf_path}")
            # Don't fail the whole pipeline if email fails — PDF is generated
            return True
    else:
        logger.info("Step 4/4: Email skipped (--no-email)")
    
    logger.info("=" * 60)
    logger.info(f"Done. Report: {pdf_path}")
    logger.info("=" * 60)
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Daily Sales Briefing - Automated daily business reports'
    )
    parser.add_argument(
        '--config', default='config/config.ini',
        help='Path to config file (default: config/config.ini)'
    )
    parser.add_argument(
        '--no-email', action='store_true',
        help='Generate PDF only, do not send email'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Enable debug-level logging'
    )
    args = parser.parse_args()
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logger = setup_logging(project_root, verbose=args.verbose)
    
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(project_root, config_path)
    
    try:
        config = load_config(config_path)
        success = run_pipeline(config, logger, send_email=not args.no_email)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
