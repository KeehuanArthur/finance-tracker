import pandas as pd
import os
import json
from typing import Dict, List, Optional
import glob
from datetime import datetime

class BankStatementReader:
    def __init__(self, data_folder: str, config_folder: str = "./configs", filter_payments: bool = True):
        self.data_folder = data_folder
        self.config_folder = config_folder
        self.bank_data = {}
        self.schema_configs = {}
        self.filter_payments = filter_payments
        self.load_schema_configs()
        
    def load_schema_configs(self):
        """Load schema configuration files for all banks."""
        if not os.path.exists(self.config_folder):
            print(f"Config folder '{self.config_folder}' does not exist!")
            return
            
        config_files = glob.glob(os.path.join(self.config_folder, "*_schema.json"))
        
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    bank_name = config.get('bank_name')
                    if bank_name:
                        self.schema_configs[bank_name] = config
                        print(f"Loaded schema config for {bank_name}")
            except Exception as e:
                print(f"Error loading config {config_file}: {e}")
        
    def detect_bank_folders(self) -> List[str]:
        """Detect all bank folders in the data directory."""
        if not os.path.exists(self.data_folder):
            return []
        
        folders = [f for f in os.listdir(self.data_folder) 
                  if os.path.isdir(os.path.join(self.data_folder, f))]
        return folders
    
    def detect_csv_format(self, df: pd.DataFrame, bank_name: str) -> Optional[Dict]:
        """Detect which format configuration matches the CSV columns."""
        if bank_name not in self.schema_configs:
            return None
            
        schema_mappings = self.schema_configs[bank_name].get('schema_mappings', [])
        
        for mapping in schema_mappings:
            column_mappings = mapping.get('column_mappings', {})
            # Check if all required columns exist in the DataFrame
            required_columns = list(column_mappings.values())
            if all(col in df.columns for col in required_columns):
                return mapping
                
        return None
    
    def normalize_amount_column(self, df: pd.DataFrame, amount_config: Dict) -> pd.DataFrame:
        """Normalize amount columns based on configuration."""
        df = df.copy()
        
        if amount_config['type'] == 'single_column':
            # Single amount column (like Chase or Apple Card)
            amount_col = amount_config['column']
            if amount_col in df.columns:
                df['amount'] = pd.to_numeric(df[amount_col], errors='coerce')
                
                # Handle different sign conventions
                sign_convention = amount_config.get('sign_convention', 'negative_for_debits')
                if sign_convention == 'positive_for_purchases_negative_for_payments':
                    # Apple Card style: purchases are positive, payments are negative
                    # Keep as-is since purchases should be positive
                    pass
                elif sign_convention == 'negative_for_debits':
                    # Chase style: purchases are negative, payments are positive
                    # Flip the sign to make purchases positive
                    df['amount'] = -df['amount']
        
        elif amount_config['type'] == 'split_columns':
            # Split debit/credit columns (like Wells Fargo)
            debit_col = amount_config['debit_column']
            credit_col = amount_config['credit_column']
            
            if debit_col in df.columns and credit_col in df.columns:
                # Convert to numeric, filling NaN with 0
                debit_amounts = pd.to_numeric(df[debit_col], errors='coerce').fillna(0)
                credit_amounts = pd.to_numeric(df[credit_col], errors='coerce').fillna(0)
                
                # For Wells Fargo: debits should be positive (spending), credits should be positive (income)
                # Combine: both debits and credits as positive values
                df['amount'] = debit_amounts + credit_amounts
        
        return df
    
    def filter_credit_card_payments(self, df: pd.DataFrame, bank_name: str) -> pd.DataFrame:
        """Filter out credit card payments to show only actual spending."""
        if df.empty or not self.filter_payments:
            return df
            
        df_filtered = df.copy()
        
        # Define patterns for credit card payments by bank
        if bank_name == 'chase':
            # Chase: Filter out transactions where Type = "Payment"
            if 'Type' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['Type'] != 'Payment']
            elif 'type' in df_filtered.columns:  # normalized column name
                df_filtered = df_filtered[df_filtered['type'] != 'Payment']
                
        elif bank_name == 'apple_card':
            # Apple Card: Filter out transactions where Type = "Payment" and Category = "Payment"
            if 'Type' in df_filtered.columns and 'Category' in df_filtered.columns:
                df_filtered = df_filtered[~((df_filtered['Type'] == 'Payment') & (df_filtered['Category'] == 'Payment'))]
            elif 'type' in df_filtered.columns and 'category' in df_filtered.columns:  # normalized column names
                df_filtered = df_filtered[~((df_filtered['type'] == 'Payment') & (df_filtered['category'] == 'Payment'))]
                
        elif bank_name == 'wells_fargo':
            # Wells Fargo: Filter out transactions that look like credit card payments
            # This might include descriptions containing "CREDIT CARD PAYMENT" or similar
            if 'description' in df_filtered.columns:
                payment_patterns = ['CREDIT CARD PAYMENT', 'CC PAYMENT', 'CARD PAYMENT']
                for pattern in payment_patterns:
                    df_filtered = df_filtered[~df_filtered['description'].str.contains(pattern, case=False, na=False)]
            elif 'merchant' in df_filtered.columns:  # original column name
                payment_patterns = ['CREDIT CARD PAYMENT', 'CC PAYMENT', 'CARD PAYMENT']
                for pattern in payment_patterns:
                    df_filtered = df_filtered[~df_filtered['merchant'].str.contains(pattern, case=False, na=False)]
        
        # Generic filtering for any bank - look for common payment descriptions
        if 'description' in df_filtered.columns:
            generic_payment_patterns = [
                'PAYMENT THANK YOU',
                'AUTOPAY',
                'ONLINE PAYMENT',
                'MOBILE PAYMENT',
                'ACH DEPOSIT INTERNET TRANSFER'
            ]
            for pattern in generic_payment_patterns:
                df_filtered = df_filtered[~df_filtered['description'].str.contains(pattern, case=False, na=False)]
        
        rows_removed = len(df) - len(df_filtered)
        if rows_removed > 0:
            print(f"Filtered out {rows_removed} credit card payment transactions for {bank_name}")
            
        return df_filtered
    
    def normalize_date_column(self, df: pd.DataFrame, date_col: str, date_format: str) -> pd.DataFrame:
        """Normalize date column."""
        df = df.copy()
        
        if date_col in df.columns:
            try:
                # Try to parse with specified format first
                df['date'] = pd.to_datetime(df[date_col], format=date_format, errors='coerce')
                
                # If that fails, try automatic parsing
                if df['date'].isna().all():
                    df['date'] = pd.to_datetime(df[date_col], errors='coerce')
                    
            except Exception as e:
                print(f"Error parsing dates: {e}")
                # Fallback to automatic parsing
                df['date'] = pd.to_datetime(df[date_col], errors='coerce')
        
        return df
    
    def normalize_dataframe(self, df: pd.DataFrame, bank_name: str) -> pd.DataFrame:
        """Normalize a DataFrame to common schema."""
        if df.empty:
            return df
            
        # Detect the format
        format_config = self.detect_csv_format(df, bank_name)
        if not format_config:
            print(f"No matching format found for {bank_name}")
            return df
            
        print(f"Using format '{format_config['format_name']}' for {bank_name}")
        
        normalized_df = df.copy()
        column_mappings = format_config.get('column_mappings', {})
        
        # Map columns to common names
        for common_name, original_name in column_mappings.items():
            if original_name in df.columns and common_name != original_name:
                normalized_df[common_name] = df[original_name]
        
        # Normalize amount column
        amount_config = format_config.get('amount_handling', {})
        if amount_config:
            normalized_df = self.normalize_amount_column(normalized_df, amount_config)
        
        # Normalize date column
        date_format = format_config.get('date_format', '%Y-%m-%d')
        date_col = column_mappings.get('date')
        if date_col:
            normalized_df = self.normalize_date_column(normalized_df, date_col, date_format)
        
        # Add metadata
        normalized_df['bank'] = bank_name
        
        return normalized_df
    
    def read_bank_statements(self, bank_name: str) -> pd.DataFrame:
        """Read and normalize all CSV files for a specific bank."""
        bank_folder = os.path.join(self.data_folder, bank_name)
        csv_files = glob.glob(os.path.join(bank_folder, "*.csv")) + glob.glob(os.path.join(bank_folder, "*.CSV"))
        
        if not csv_files:
            return pd.DataFrame()
        
        all_data = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                df['source_file'] = os.path.basename(csv_file)
                
                # Filter out credit card payments before normalization if enabled
                if self.filter_payments:
                    df_filtered = self.filter_credit_card_payments(df, bank_name)
                else:
                    df_filtered = df
                
                # Normalize the DataFrame
                normalized_df = self.normalize_dataframe(df_filtered, bank_name)
                all_data.append(normalized_df)
                
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
                
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return combined_df
        return pd.DataFrame()
    
    def load_all_statements(self) -> Dict[str, pd.DataFrame]:
        """Load and normalize statements from all bank folders."""
        banks = self.detect_bank_folders()
        
        for bank in banks:
            self.bank_data[bank] = self.read_bank_statements(bank)
            
        return self.bank_data
    
    def get_combined_data(self) -> pd.DataFrame:
        """Combine all normalized bank data into a single DataFrame."""
        if not self.bank_data:
            self.load_all_statements()
            
        all_data = []
        for bank, df in self.bank_data.items():
            if not df.empty:
                all_data.append(df)
                
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Ensure we have the common columns
            common_columns = ['date', 'amount', 'category', 'description', 'bank', 'source_file']
            for col in common_columns:
                if col not in combined_df.columns:
                    combined_df[col] = None
                    
            return combined_df
        return pd.DataFrame()
    
    def get_schema_info(self) -> Dict:
        """Get information about loaded schemas."""
        info = {}
        for bank_name, config in self.schema_configs.items():
            formats = [mapping['format_name'] for mapping in config.get('schema_mappings', [])]
            info[bank_name] = {
                'formats': formats,
                'config_loaded': True
            }
        return info