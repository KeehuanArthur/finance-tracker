# Schema Normalization System

This document explains the improved schema normalization system that automatically handles different CSV formats from various banks.

## Overview

The finance tracker now automatically normalizes different bank CSV schemas into a common format, eliminating the need for manual column mapping in the UI.

## How It Works

### 1. Configuration Files

Each bank has its own schema configuration file in the `configs/` folder:

- `configs/chase_schema.json` - Chase bank formats
- `configs/chase_amazon_schema.json` - Chase Amazon card formats
- `configs/wells_fargo_schema.json` - Wells Fargo formats
- `configs/apple_card_schema.json` - Apple Card formats
- Add more as needed: `configs/{bank_name}_schema.json`

### 2. Schema Configuration Format

```json
{
  "bank_name": "chase",
  "schema_mappings": [
    {
      "format_name": "chase_current",
      "column_mappings": {
        "date": "Transaction Date",
        "amount": "Amount",
        "category": "Category",
        "description": "Description"
      },
      "amount_handling": {
        "type": "single_column",
        "column": "Amount",
        "sign_convention": "negative_for_debits"
      },
      "date_format": "%m/%d/%Y"
    }
  ]
}
```

### 3. Supported Amount Handling Types

#### Single Column (Chase style)
```json
"amount_handling": {
  "type": "single_column",
  "column": "Amount",
  "sign_convention": "negative_for_debits"
}
```

#### Split Columns (Wells Fargo style)
```json
"amount_handling": {
  "type": "split_columns",
  "debit_column": "debit_amount",
  "credit_column": "credit_amount",
  "sign_convention": "positive_for_credits"
}
```

## Common Schema

All bank data is normalized to these standard columns:

- `date` - Transaction date (datetime)
- `amount` - Transaction amount (float, negative for debits, positive for credits)
- `category` - Transaction category (string)
- `description` - Transaction description (string)
- `bank` - Source bank name (string)
- `source_file` - Original CSV filename (string)

## Adding New Banks

To add support for a new bank:

1. **Create schema config file**: `configs/{bank_name}_schema.json`

2. **Define column mappings**: Map the bank's CSV columns to standard names

3. **Configure amount handling**: Specify how to handle amount columns

4. **Set date format**: Specify the date format used by the bank

5. **Test**: Place CSV files in `data/{bank_name}/` folder and run the test

### Example: Adding Bank of America

```json
{
  "bank_name": "bank_of_america",
  "schema_mappings": [
    {
      "format_name": "boa_standard",
      "column_mappings": {
        "date": "Date",
        "amount": "Amount",
        "category": "Category",
        "description": "Description"
      },
      "amount_handling": {
        "type": "single_column",
        "column": "Amount",
        "sign_convention": "negative_for_debits"
      },
      "date_format": "%m/%d/%Y"
    }
  ]
}
```

## Multiple Formats Per Bank

Banks can have multiple CSV formats (e.g., old vs new format). The system automatically detects which format matches the CSV columns:

```json
{
  "bank_name": "chase",
  "schema_mappings": [
    {
      "format_name": "chase_legacy",
      "column_mappings": {
        "date": "date",
        "amount": "amount",
        "category": "category",
        "description": "description"
      }
    },
    {
      "format_name": "chase_current",
      "column_mappings": {
        "date": "Transaction Date",
        "amount": "Amount",
        "category": "Category",
        "description": "Description"
      }
    }
  ]
}
```

## Testing

Run the test script to verify schema normalization:

```bash
python test_schema_normalization.py
```

This will:
- Load all schema configurations
- Test individual bank data loading
- Verify column normalization
- Test combined data functionality
- Show sample normalized data

## Benefits

1. **Automatic Schema Detection**: No manual column mapping required
2. **Consistent Data Format**: All banks use the same column names
3. **Amount Normalization**: Handles different amount column formats automatically
4. **Date Standardization**: Converts all dates to consistent datetime format
5. **Extensible**: Easy to add new banks by creating config files
6. **Multiple Format Support**: Each bank can have multiple CSV formats

## File Structure

```
finance-tracker/
├── configs/
│   ├── chase_schema.json
│   ├── wells_fargo_schema.json
│   └── category_mapping.json
├── data/
│   ├── chase/
│   │   ├── january_2024.csv
│   │   └── Chase7026_Activity20250616_20250715_20250722.CSV
│   └── wells_fargo/
│       └── january_2024.csv
├── app.py
├── bank_reader.py
└── test_schema_normalization.py
```

## Migration from Old System

The old system required manual column mapping in the UI. The new system:

1. **Eliminates manual mapping**: Columns are automatically mapped based on config files
2. **Simplifies UI**: No more column selection dropdowns
3. **Improves reliability**: Consistent data processing across all banks
4. **Reduces errors**: No more manual configuration mistakes

## Troubleshooting

### Schema Not Detected
- Verify the config file exists: `configs/{bank_name}_schema.json`
- Check that column names in config match CSV headers exactly
- Ensure the bank folder name matches the `bank_name` in config

### Amount Calculation Issues
- For split columns: Verify `debit_column` and `credit_column` names
- For single column: Check `column` name and `sign_convention`
- Test with sample data to verify calculations

### Date Parsing Errors
- Check `date_format` matches the actual date format in CSV
- The system falls back to automatic parsing if format fails
- Verify date column name in `column_mappings`