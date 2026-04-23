"""
Data Adapters for Daily Sales Briefing (Community Edition)

╔══════════════════════════════════════════════════════════════════════════╗
║                       COMMUNITY EDITION NOTICE                           ║
║                                                                          ║
║  This version includes Standard CSV and basic Excel adapters only.       ║
║                                                                          ║
║  The Pro edition adds:                                                   ║
║    - Square POS direct import (automatic column mapping)                 ║
║    - Shopify POS direct import (multi-line order reconstruction)         ║
║    - Clover POS adapter                                                  ║
║    - Lightspeed Restaurant adapter                                       ║
║    - Full Excel adapter with sheet/cell range selection                  ║
║    - Custom adapter framework for proprietary POS systems                ║
║                                                                          ║
║  Contact: razeghi.a@gmail.com for commercial licensing.                  ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """
    Base class for all data adapters.
    
    Required columns after transformation:
      - Date, Category, Item, Quantity, Price, Total
    
    Optional columns (recommended for accurate metrics):
      - OrderID, PaymentMethod, Location
    """
    
    REQUIRED_COLUMNS = ['Date', 'Category', 'Item', 'Quantity', 'Price', 'Total']
    OPTIONAL_COLUMNS = ['OrderID', 'PaymentMethod', 'Location']
    
    @abstractmethod
    def load(self, file_path):
        pass
    
    @abstractmethod
    def transform(self, raw_df):
        pass
    
    def validate(self, df):
        missing = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(
                f"After transformation, these required columns are missing: {missing}."
            )
        if df.empty:
            raise ValueError("No data rows found after transformation.")
        return True
    
    def process(self, file_path):
        raw = self.load(file_path)
        transformed = self.transform(raw)
        self.validate(transformed)
        
        output_columns = list(self.REQUIRED_COLUMNS)
        for col in self.OPTIONAL_COLUMNS:
            if col in transformed.columns:
                output_columns.append(col)
        return transformed[output_columns]


class StandardCSVAdapter(BaseAdapter):
    """
    Adapter for CSV files in our standard format.
    
    Expected columns:
        Required: Date, Category, Item, Quantity, Price, Total
        Optional: OrderID, PaymentMethod, Location
    """
    
    def load(self, file_path):
        return pd.read_csv(file_path)
    
    def transform(self, raw_df):
        return raw_df


class SquarePOSAdapter(BaseAdapter):
    """
    Adapter for Square POS exports. [PRO EDITION FEATURE]
    
    The Pro implementation handles:
        - Automatic column detection across Square export variants
        - Multi-location splits
        - Refund and void handling
        - Discount line item reconciliation
        - Timezone normalization
        - Service charge separation
    
    Community users: Export your Square data as CSV, rename columns to
    match the standard schema, and use StandardCSVAdapter.
    """
    
    def load(self, file_path):
        raise NotImplementedError(
            "Square POS adapter is available in the Pro edition. "
            "Community workaround: export Square data, rename columns to "
            "(Date, Category, Item, Quantity, Price, Total), then use StandardCSVAdapter."
        )
    
    def transform(self, raw_df):
        raise NotImplementedError("See load() — Pro edition only.")


class ShopifyPOSAdapter(BaseAdapter):
    """
    Adapter for Shopify order exports. [PRO EDITION FEATURE]
    
    The Pro implementation handles:
        - Multi-line order reconstruction
        - Tax and shipping handling
        - Refund correlation
        - Multi-currency normalization
    """
    
    def load(self, file_path):
        raise NotImplementedError(
            "Shopify adapter is available in the Pro edition. "
            "Contact razeghi.a@gmail.com for commercial licensing."
        )
    
    def transform(self, raw_df):
        raise NotImplementedError("See load() — Pro edition only.")


class ExcelAdapter(BaseAdapter):
    """
    Generic Excel adapter with column mapping (basic version).
    
    The Pro edition adds multi-sheet aggregation, cell range selection,
    formula evaluation, merged cell handling, and auto-detection of header rows.
    """
    
    def __init__(self, column_map, sheet_name=0):
        self.column_map = column_map
        self.sheet_name = sheet_name
    
    def load(self, file_path):
        return pd.read_excel(file_path, sheet_name=self.sheet_name)
    
    def transform(self, raw_df):
        df = pd.DataFrame()
        for std_col, source_col in self.column_map.items():
            if source_col not in raw_df.columns:
                raise KeyError(
                    f"Column '{source_col}' not found in Excel. "
                    f"Available: {list(raw_df.columns)}"
                )
            df[std_col] = raw_df[source_col]
        
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df['Quantity'] = df['Quantity'].astype(int)
        df['Price'] = df['Price'].astype(float)
        df['Total'] = df['Total'].astype(float)
        df['Category'] = df['Category'].fillna('Uncategorized')
        return df


def get_adapter(source_type, **kwargs):
    """
    Factory function.
    
    Community Edition supports: 'standard', 'excel'
    Pro Edition adds: 'square', 'shopify', 'clover', 'lightspeed'
    """
    adapters = {
        'standard': StandardCSVAdapter,
        'square': SquarePOSAdapter,
        'shopify': ShopifyPOSAdapter,
        'excel': ExcelAdapter,
    }
    
    if source_type not in adapters:
        raise ValueError(
            f"Unknown source type '{source_type}'. "
            f"Community Edition supports: 'standard', 'excel'. "
            f"Pro Edition adds: 'square', 'shopify', 'clover', 'lightspeed'."
        )
    
    adapter_class = adapters[source_type]
    
    if source_type == 'excel':
        if 'column_map' not in kwargs:
            raise ValueError("ExcelAdapter requires 'column_map' parameter.")
        return adapter_class(**kwargs)
    
    return adapter_class()
