#!/usr/bin/env python3
"""
Test script to verify schema normalization is working correctly.
"""

import pandas as pd
from finance_tracker.bank_reader import BankStatementReader

def test_schema_normalization():
    """Test the schema normalization functionality."""
    print("🧪 Testing Schema Normalization")
    print("=" * 50)
    
    # Initialize the reader
    reader = BankStatementReader("./data")
    
    # Test schema config loading
    print("\n📋 Schema Configurations Loaded:")
    schema_info = reader.get_schema_info()
    for bank_name, info in schema_info.items():
        print(f"  • {bank_name}: {info['formats']}")
    
    # Test individual bank data loading
    print("\n🏦 Testing Individual Bank Data:")
    banks = reader.detect_bank_folders()
    
    for bank in banks:
        print(f"\n--- {bank.upper()} ---")
        bank_data = reader.read_bank_statements(bank)
        
        if not bank_data.empty:
            print(f"  Transactions loaded: {len(bank_data)}")
            print(f"  Columns: {list(bank_data.columns)}")
            
            # Check if standard columns exist
            standard_cols = ['date', 'amount', 'category', 'description', 'bank']
            missing_cols = [col for col in standard_cols if col not in bank_data.columns]
            
            if missing_cols:
                print(f"  ⚠️  Missing standard columns: {missing_cols}")
            else:
                print("  ✅ All standard columns present")
                
            # Show sample data
            print("  Sample data:")
            sample_cols = ['date', 'amount', 'category', 'description']
            available_cols = [col for col in sample_cols if col in bank_data.columns]
            print(bank_data[available_cols].head(3).to_string(index=False))
        else:
            print(f"  ❌ No data loaded for {bank}")
    
    # Test combined data
    print("\n🔄 Testing Combined Data:")
    combined_data = reader.get_combined_data()
    
    if not combined_data.empty:
        print(f"  Total transactions: {len(combined_data)}")
        print(f"  Banks: {list(combined_data['bank'].unique()) if 'bank' in combined_data.columns else 'N/A'}")
        print(f"  Date range: {combined_data['date'].min()} to {combined_data['date'].max()}" if 'date' in combined_data.columns else "No date column")
        print(f"  Amount range: ${combined_data['amount'].min():.2f} to ${combined_data['amount'].max():.2f}" if 'amount' in combined_data.columns else "No amount column")
        
        # Check data types
        print("\n  📊 Data Types:")
        for col in ['date', 'amount', 'category', 'description']:
            if col in combined_data.columns:
                print(f"    {col}: {combined_data[col].dtype}")
    else:
        print("  ❌ No combined data available")
    
    print("\n✅ Schema normalization test completed!")

if __name__ == "__main__":
    test_schema_normalization()