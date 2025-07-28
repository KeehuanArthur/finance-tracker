# Finance Tracker

A Python application for analyzing bank statement CSV files with category normalization and visualization.

## Features

- 📁 Read CSV files from multiple bank folders
- 🏷️ Normalize transaction categories using configurable mappings
- 📊 Interactive web UI built with Streamlit
- 📈 Data visualization with Plotly charts
- 🔍 Filter by date range, bank, and category
- 📋 View and export transaction data

## Setup

1. Set up Environment and install dependencies:
```bash
# Install UV if not exist
pip install uv
# Or you can install UV using brew
brew install uv

# Install python packages
uv sync

# Activate environment
source .venv/bin/activate
```

2. Create your data folder structure:
```
data/
├── chase/
│   ├── january_2024.csv
│   └── february_2024.csv
├── wells_fargo/
│   ├── january_2024.csv
│   └── february_2024.csv
└── bank_of_america/
    └── statements.csv
```

3. Configure category mappings in `configs/category_mapping.json`

4. Run the application:
```bash
streamlit run run_app.py
```

## Usage

1. Set your data folder path in the sidebar
2. Map your CSV columns to the expected fields (date, amount, category, description)
3. Apply filters and explore your financial data
4. Use the visualizations to understand spending patterns
5. Manage category mappings for better data organization

## Configuration

Edit `configs/category_mapping.json` to customize category normalization:

```json
{
  "dining": ["restaurant", "restaurants", "food", "cafe"],
  "transportation": ["gas", "fuel", "uber", "lyft"],
  "shopping": ["amazon", "target", "walmart"]
}
```

## Sample Data

The project includes sample data for testing in the `data/` folder with different bank statement formats.