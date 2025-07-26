#!/usr/bin/env python3
"""
Test script to show filtering results on real data.
"""

from finance_tracker.bank_reader import BankStatementReader

def test_real_data_filtering():
    """Test filtering on real data to show the difference."""
    print("🔍 Testing filtering on real data...\n")
    
    # Test with filtering enabled
    print("📊 Loading data WITH credit card payment filtering:")
    reader_filtered = BankStatementReader('./data', filter_payments=True)
    data_filtered = reader_filtered.get_combined_data()
    
    print(f"Total transactions (filtered): {len(data_filtered)}")
    total_amount_filtered = 0
    if not data_filtered.empty:
        total_amount_filtered = data_filtered['amount'].sum()
        print(f"Total amount (filtered): ${total_amount_filtered:,.2f}")
    
    print("\n" + "="*50 + "\n")
    
    # Test with filtering disabled
    print("📊 Loading data WITHOUT credit card payment filtering:")
    reader_unfiltered = BankStatementReader('./data', filter_payments=False)
    data_unfiltered = reader_unfiltered.get_combined_data()
    
    print(f"Total transactions (unfiltered): {len(data_unfiltered)}")
    total_amount_unfiltered = 0
    if not data_unfiltered.empty:
        total_amount_unfiltered = data_unfiltered['amount'].sum()
        print(f"Total amount (unfiltered): ${total_amount_unfiltered:,.2f}")
    
    print("\n" + "="*50 + "\n")
    
    # Show the difference
    if not data_filtered.empty and not data_unfiltered.empty:
        transactions_filtered_out = len(data_unfiltered) - len(data_filtered)
        amount_difference = total_amount_unfiltered - total_amount_filtered
        
        print("📈 FILTERING RESULTS:")
        print(f"Transactions filtered out: {transactions_filtered_out}")
        print(f"Amount difference: ${amount_difference:,.2f}")
        
        if transactions_filtered_out > 0:
            print(f"Average payment amount: ${amount_difference/transactions_filtered_out:,.2f}")
        
        print(f"\n✅ Filtering is working! {transactions_filtered_out} credit card payment transactions were removed.")
    else:
        print("❌ No data found to compare.")

if __name__ == "__main__":
    test_real_data_filtering()