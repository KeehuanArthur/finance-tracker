# Credit Card Payment Filtering

## Overview

The finance tracker now includes automatic filtering of credit card payments to show only actual spending, not payments made to credit card companies.

## How It Works

### Automatic Detection

The system automatically detects and filters out credit card payments based on:

**Chase Bank:**
- Transactions with `Type = "Payment"`
- Examples: "Payment Thank You-Mobile"

**Apple Card:**
- Transactions with both `Type = "Payment"` AND `Category = "Payment"`
- Examples: "ACH DEPOSIT INTERNET TRANSFER FROM ACCOUNT ENDING IN XXXX"

**Wells Fargo:**
- Transactions containing payment-related keywords in descriptions
- Examples: "CREDIT CARD PAYMENT", "CC PAYMENT", "CARD PAYMENT"

**Generic Filtering (All Banks):**
- Descriptions containing: "PAYMENT THANK YOU", "AUTOPAY", "ONLINE PAYMENT", "MOBILE PAYMENT", "ACH DEPOSIT INTERNET TRANSFER"

### Configuration

In the Streamlit app sidebar, you can:
- ✅ **Enable filtering** (default): Shows only actual spending
- ❌ **Disable filtering**: Shows all transactions including payments

### Benefits

**With Filtering Enabled:**
- See only money you actually spent on goods and services
- Get accurate spending analysis and budgeting insights
- Avoid double-counting (spending + payment to credit card)

**Example Results:**
- Total transactions: 125 (filtered) vs 135 (unfiltered)
- Total spending: $-9,302.07 (actual spending) vs $529.55 (including payments)
- Filtered out: 10 payment transactions worth $9,831.62

## Technical Implementation

### Files Modified
- `bank_reader.py`: Added `filter_credit_card_payments()` method
- `app.py`: Added UI toggle and filtering configuration

### Testing
Run the test scripts to verify functionality:
```bash
python test_payment_filtering.py  # Unit tests
python test_real_data.py         # Real data comparison
```

## Usage

1. **Default Behavior**: Filtering is enabled by default
2. **Toggle Option**: Use the sidebar checkbox to enable/disable
3. **Status Display**: The app shows filtering status and transaction counts
4. **Real-time Updates**: Changes apply immediately when toggling the option

This feature ensures you get accurate insights into your actual spending patterns without the noise of credit card payment transactions.