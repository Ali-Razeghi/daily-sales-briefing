"""
Data Validation Layer

Real-world customer data is messy. This module validates input data
and reports quality issues before they break the analysis pipeline.

Catches common issues:
- Missing required columns
- Null values in critical fields
- Invalid dates
- Negative or zero quantities
- Mismatched Price × Quantity vs Total
- Duplicate rows
- Future dates
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataQualityReport:
    """Container for validation results."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.rows_checked = 0
        self.rows_dropped = 0
    
    def add_error(self, msg):
        self.errors.append(msg)
        logger.error(msg)
    
    def add_warning(self, msg):
        self.warnings.append(msg)
        logger.warning(msg)
    
    def add_info(self, msg):
        self.info.append(msg)
        logger.info(msg)
    
    @property
    def has_errors(self):
        return len(self.errors) > 0
    
    @property
    def has_warnings(self):
        return len(self.warnings) > 0
    
    def summary(self):
        """Print a human-readable summary."""
        lines = []
        lines.append(f"Data Quality Report")
        lines.append(f"  Rows checked:  {self.rows_checked}")
        lines.append(f"  Rows dropped:  {self.rows_dropped}")
        lines.append(f"  Errors:        {len(self.errors)}")
        lines.append(f"  Warnings:      {len(self.warnings)}")
        
        if self.errors:
            lines.append("\n  ERRORS:")
            for e in self.errors:
                lines.append(f"    - {e}")
        
        if self.warnings:
            lines.append("\n  WARNINGS:")
            for w in self.warnings:
                lines.append(f"    - {w}")
        
        return "\n".join(lines)


def validate_sales_data(df, required_columns=None, strict=False):
    """
    Validate a sales DataFrame and return (cleaned_df, report).
    
    Parameters:
    -----------
    df : pd.DataFrame
        Raw sales data to validate
    required_columns : list, optional
        Required column names. Defaults to our standard schema.
    strict : bool
        If True, raise on any error. If False, drop bad rows and continue.
    
    Returns:
    --------
    (cleaned_df, report) : tuple
        Cleaned DataFrame and DataQualityReport
    """
    if required_columns is None:
        required_columns = ['Date', 'Category', 'Item', 'Quantity', 'Price', 'Total']
    
    report = DataQualityReport()
    report.rows_checked = len(df)
    
    # Check 1: Required columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        msg = f"Missing required columns: {missing_cols}"
        report.add_error(msg)
        if strict:
            raise ValueError(msg)
        return df, report
    
    original_len = len(df)
    df = df.copy()
    
    # Check 2: Empty DataFrame
    if len(df) == 0:
        report.add_error("DataFrame is empty")
        return df, report
    
    # Check 3: Null values in critical columns
    null_counts = df[required_columns].isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            pct = (count / len(df)) * 100
            report.add_warning(
                f"Column '{col}' has {count} null values ({pct:.1f}%). "
                f"These rows will be dropped."
            )
    
    df = df.dropna(subset=required_columns)
    
    # Check 4: Date validity
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        invalid_dates = df['Date'].isnull().sum()
        if invalid_dates > 0:
            report.add_warning(
                f"{invalid_dates} rows had invalid dates. They will be dropped."
            )
            df = df.dropna(subset=['Date'])
    except Exception as e:
        report.add_error(f"Could not parse dates: {e}")
    
    # Check 5: Future dates
    today = pd.Timestamp.now().normalize()
    future_dates = (df['Date'] > today).sum()
    if future_dates > 0:
        report.add_warning(
            f"{future_dates} rows have future dates. "
            f"This may indicate data entry errors."
        )
    
    # Check 6: Numeric validity
    for col in ['Quantity', 'Price', 'Total']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        invalid = df[col].isnull().sum()
        if invalid > 0:
            report.add_warning(
                f"Column '{col}' had {invalid} non-numeric values. Rows dropped."
            )
    df = df.dropna(subset=['Quantity', 'Price', 'Total'])
    
    # Check 7: Negative or zero quantities
    bad_qty = (df['Quantity'] <= 0).sum()
    if bad_qty > 0:
        report.add_warning(
            f"{bad_qty} rows have quantity <= 0 (possibly refunds or voids). "
            f"These will be excluded from totals."
        )
        df = df[df['Quantity'] > 0]
    
    # Check 8: Negative prices or totals
    bad_price = (df['Price'] < 0).sum()
    if bad_price > 0:
        report.add_warning(f"{bad_price} rows have negative prices. Dropped.")
        df = df[df['Price'] >= 0]
    
    bad_total = (df['Total'] < 0).sum()
    if bad_total > 0:
        report.add_warning(f"{bad_total} rows have negative totals (refunds?). Dropped.")
        df = df[df['Total'] >= 0]
    
    # Check 9: Price × Quantity should roughly match Total
    # Allow small floating point differences
    expected_total = (df['Price'] * df['Quantity']).round(2)
    diff = (df['Total'] - expected_total).abs()
    mismatches = (diff > 0.05).sum()
    if mismatches > 0:
        pct = (mismatches / len(df)) * 100
        report.add_info(
            f"{mismatches} rows ({pct:.1f}%) have Total != Price × Quantity. "
            f"This may be due to discounts or taxes."
        )
    
    # Check 10: Exact duplicate rows
    # If OrderID column exists, duplicates are rows with same OrderID + Item
    # (same item listed twice in one order, which shouldn't happen — items should be merged into quantity)
    # If no OrderID, we can't reliably detect duplicates without false positives,
    # so only warn on exact full-row duplicates.
    if 'OrderID' in df.columns:
        dup_mask = df.duplicated(subset=['OrderID', 'Item'], keep='first')
        duplicates = dup_mask.sum()
        if duplicates > 0:
            report.add_warning(
                f"{duplicates} rows have duplicate OrderID+Item combinations. "
                f"These should be merged into quantity. Keeping first occurrence."
            )
            df = df[~dup_mask]
    else:
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            report.add_info(
                f"{duplicates} rows are identical across all columns. "
                f"Without OrderID, cannot distinguish duplicates from legitimate repeats. "
                f"Keeping all rows."
            )
    
    # Format Date back to string for consistency
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    
    report.rows_dropped = original_len - len(df)
    
    if report.rows_dropped > 0:
        pct = (report.rows_dropped / original_len) * 100
        report.add_info(
            f"Total rows dropped: {report.rows_dropped} ({pct:.1f}% of input)"
        )
    
    return df, report


if __name__ == '__main__':
    # Test with our generated data
    import logging
    logging.basicConfig(level=logging.INFO)
    
    df = pd.read_csv('/home/claude/daily_sales_briefing/data/sales_data.csv')
    print(f"Loaded {len(df)} rows from CSV")
    
    cleaned, report = validate_sales_data(df)
    print()
    print(report.summary())
    print()
    print(f"Cleaned DataFrame: {len(cleaned)} rows")
