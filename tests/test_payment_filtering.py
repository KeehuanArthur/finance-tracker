#!/usr/bin/env python3
"""
Test script to verify credit card payment filtering functionality.
"""

import pandas as pd
from finance_tracker.bank_reader import BankStatementReader

def test_chase_filtering():
    """Test Chase credit card payment filtering."""
    print("Testing Chase payment filtering...")
    
    # Create sample Chase data
    chase_data = pd.DataFrame({
        'Transaction Date': ['07/13/2025', '07/12/2025', '07/13/2025'],
        'Post Date': ['07/14/2025', '07/14/2025', '07/14/2025'],
        'Description': ['Payment Thank You-Mobile', 'HCTRA EZ TAG REBILL', 'H-E-B #659'],
        'Category': ['', 'Travel', 'Groceries'],
        'Type': ['Payment', 'Sale', 'Sale'],
        'Amount': [183.13, -10.00, -21.39],
        'Memo': ['', '', '']
    })
    
    reader = BankStatementReader('./data', filter_payments=True)
    filtered_data = reader.filter_credit_card_payments(chase_data, 'chase')
    
    print(f"Original transactions: {len(chase_data)}")
    print(f"After filtering: {len(filtered_data)}")
    print(f"Filtered out: {len(chase_data) - len(filtered_data)} payment transactions")
    
    # Should filter out the payment transaction
    assert len(filtered_data) == 2, f"Expected 2 transactions, got {len(filtered_data)}"
    assert 'Payment Thank You-Mobile' not in filtered_data['Description'].values
    print("✅ Chase filtering test passed!\n")

def test_apple_card_filtering():
    """Test Apple Card payment filtering."""
    print("Testing Apple Card payment filtering...")
    
    # Create sample Apple Card data
    apple_data = pd.DataFrame({
        'Transaction Date': ['06/28/2025', '06/27/2025', '06/25/2025'],
        'Clearing Date': ['06/28/2025', '06/29/2025', '06/27/2025'],
        'Description': ['ACH DEPOSIT INTERNET TRANSFER FROM ACCOUNT ENDING IN 7240', 'APPLE CAFFE PL5', 'APPLE CAFFE PL5'],
        'Merchant': ['Ach Deposit Internet Transfer', 'Caffè Macs', 'Caffè Macs'],
        'Category': ['Payment', 'Restaurants', 'Restaurants'],
        'Type': ['Payment', 'Purchase', 'Purchase'],
        'Amount (USD)': [-185.53, 8.00, 8.00],
        'Purchased By': ['Keehuan Lee', 'Keehuan Lee', 'Keehuan Lee']
    })
    
    reader = BankStatementReader('./data', filter_payments=True)
    filtered_data = reader.filter_credit_card_payments(apple_data, 'apple_card')
    
    print(f"Original transactions: {len(apple_data)}")
    print(f"After filtering: {len(filtered_data)}")
    print(f"Filtered out: {len(apple_data) - len(filtered_data)} payment transactions")
    
    # Should filter out the payment transaction
    assert len(filtered_data) == 2, f"Expected 2 transactions, got {len(filtered_data)}"
    assert 'ACH DEPOSIT INTERNET TRANSFER' not in filtered_data['Description'].values
    print("✅ Apple Card filtering test passed!\n")

def test_no_filtering():
    """Test that filtering can be disabled."""
    print("Testing disabled filtering...")
    
    chase_data = pd.DataFrame({
        'Transaction Date': ['07/13/2025', '07/12/2025'],
        'Description': ['Payment Thank You-Mobile', 'H-E-B #659'],
        'Type': ['Payment', 'Sale'],
        'Amount': [183.13, -21.39]
    })
    
    reader = BankStatementReader('./data', filter_payments=False)
    # When filtering is disabled, we should get all transactions
    filtered_data = reader.filter_credit_card_payments(chase_data, 'chase')
    
    print(f"Original transactions: {len(chase_data)}")
    print(f"After filtering (disabled): {len(filtered_data)}")
    
    # Should not filter anything when disabled
    assert len(filtered_data) == len(chase_data), f"Expected {len(chase_data)} transactions, got {len(filtered_data)}"
    print("✅ Disabled filtering test passed!\n")

if __name__ == "__main__":
    print("🧪 Testing Credit Card Payment Filtering\n")
    
    try:
        test_chase_filtering()
        test_apple_card_filtering()
        test_no_filtering()
        print("🎉 All tests passed! Credit card payment filtering is working correctly.")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()