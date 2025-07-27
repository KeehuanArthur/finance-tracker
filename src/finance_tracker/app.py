import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from finance_tracker.bank_reader import BankStatementReader
from finance_tracker.category_normalizer import CategoryNormalizer
from finance_tracker.notes_manager import NotesManager

st.set_page_config(page_title="Finance Tracker", layout="wide")

def load_data(data_folder, filter_payments=True):
    """Load and process bank statement data."""
    
    reader = BankStatementReader(data_folder, filter_payments=filter_payments)
    normalizer = CategoryNormalizer()
    
    # Get combined normalized data
    combined_data = reader.get_combined_data()
    
    if combined_data.empty:
        return pd.DataFrame(), normalizer, reader, None
    
    # Normalize categories if category column exists
    if 'category' in combined_data.columns:
        combined_data = normalizer.normalize_dataframe(combined_data)
    
    # Initialize notes manager and add notes to data
    notes_manager = NotesManager(notes_file=os.path.join(data_folder, "notes_database.json"))
    combined_data = notes_manager.add_notes_to_dataframe(combined_data)
    
    return combined_data, normalizer, reader, notes_manager

def main():
    st.title("🏦 Finance Tracker")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Data folder selection
    data_folder = st.sidebar.text_input("Data Folder Path", value="./data")
    
    if not os.path.exists(data_folder):
        st.sidebar.error(f"Data folder '{data_folder}' does not exist!")
        return
    
    # Credit card payment filtering option
    filter_payments = st.sidebar.checkbox(
        "Filter out credit card payments",
        value=True,
        help="When enabled, credit card payments to credit card companies will be filtered out, showing only actual spending."
    )
    
    # Load data
    data, normalizer, reader, notes_manager = load_data(data_folder, filter_payments)
    
    if data.empty:
        st.warning("No data found in the specified folder!")
        return
    
    # Show filtering status
    if filter_payments:
        st.sidebar.success(f"Loaded {len(data)} transactions (credit card payments filtered)")
    else:
        st.sidebar.success(f"Loaded {len(data)} transactions (no filtering applied)")
    
    # Display schema information
    st.sidebar.header("Schema Information")
    schema_info = reader.get_schema_info()
    for bank_name, info in schema_info.items():
        st.sidebar.write(f"**{bank_name.title()}:**")
        st.sidebar.write(f"- Formats: {', '.join(info['formats'])}")
    
    # Display available columns
    st.sidebar.write("**Available Columns:**")
    st.sidebar.write(list(data.columns))
    
    # Show filtering information
    if filter_payments:
        st.sidebar.write("**Filtering Applied:**")
        st.sidebar.write("✅ Credit card payments filtered out")
        st.sidebar.write("- Chase: Payment transactions")
        st.sidebar.write("- Apple Card: Payment category transactions")
        st.sidebar.write("- Generic: Payment descriptions")
    else:
        st.sidebar.write("**Filtering Applied:**")
        st.sidebar.write("❌ No filtering applied")
    
    # Since data is now normalized, we use standard column names
    date_col = 'date'
    amount_col = 'amount'
    category_col = 'category'
    description_col = 'description'
    
    # Verify required columns exist
    if date_col not in data.columns:
        st.error("Date column not found in normalized data")
        return
    if amount_col not in data.columns:
        st.error("Amount column not found in normalized data")
        return
    
    # Main dashboard
    st.header("📊 Dashboard")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Date range filter
        min_date = data[date_col].min().date()
        max_date = data[date_col].max().date()
        
        # Calculate previous month as default
        today = datetime.now().date()
        # Get first day of current month
        first_day_current_month = today.replace(day=1)
        # Get last day of previous month
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        # Get first day of previous month
        first_day_previous_month = last_day_previous_month.replace(day=1)
        
        # Use previous month as default, but constrain to available data range
        default_start = max(first_day_previous_month, min_date)
        default_end = min(last_day_previous_month, max_date)
        
        date_range = st.date_input(
            "Date Range",
            value=(default_start, default_end),
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        # Bank filter
        if 'bank' in data.columns:
            banks = ['All'] + list(data['bank'].unique())
            selected_bank = st.selectbox("Bank", banks)
        else:
            selected_bank = 'All'
    
    with col3:
        # Category filter
        if 'normalized_category' in data.columns:
            categories = ['All'] + list(data['normalized_category'].unique())
            selected_category = st.selectbox("Category", categories)
        else:
            categories = ['All']
            selected_category = 'All'
    
    # Apply filters
    filtered_data = data.copy()
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_data = filtered_data[
            (filtered_data[date_col].dt.date >= start_date) & 
            (filtered_data[date_col].dt.date <= end_date)
        ]
    
    if selected_bank != 'All' and 'bank' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['bank'] == selected_bank]
    
    if selected_category != 'All' and 'normalized_category' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['normalized_category'] == selected_category]
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_transactions = len(filtered_data)
        st.metric("Total Transactions", total_transactions)
    
    with col2:
        total_amount = filtered_data[amount_col].sum()
        st.metric("Total Amount", f"${total_amount:,.2f}")
    
    with col3:
        avg_amount = filtered_data[amount_col].mean()
        st.metric("Average Amount", f"${avg_amount:,.2f}")
    
    with col4:
        if 'normalized_category' in filtered_data.columns:
            unique_categories = filtered_data['normalized_category'].nunique()
            st.metric("Unique Categories", unique_categories)
    
    # Visualizations
    st.header("📈 Visualizations")
    
    # Time series chart
    st.subheader("Spending Over Time")
    
    # Group by options
    group_by = st.selectbox("Group by", ["Day", "Week", "Month"])
    
    if group_by == "Day":
        time_grouped = filtered_data.groupby(filtered_data[date_col].dt.date)[amount_col].sum().reset_index()
    elif group_by == "Week":
        time_grouped = filtered_data.groupby(filtered_data[date_col].dt.to_period('W'))[amount_col].sum().reset_index()
        time_grouped[date_col] = time_grouped[date_col].dt.to_timestamp()
    else:  # Month
        time_grouped = filtered_data.groupby(filtered_data[date_col].dt.to_period('M'))[amount_col].sum().reset_index()
        time_grouped[date_col] = time_grouped[date_col].dt.to_timestamp()
    
    fig_time = px.bar(time_grouped, x=date_col, y=amount_col, 
                       title=f"Spending by {group_by}")
    st.plotly_chart(fig_time, use_container_width=True)
    
    # Category breakdown
    if 'normalized_category' in filtered_data.columns:
        st.subheader("Spending by Category")
        
        # Date range filter specifically for category analysis
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            category_date_range = st.date_input(
                "Category Analysis Date Range",
                value=(default_start, default_end),
                min_value=min_date,
                max_value=max_date,
                key="category_date_filter"
            )
        
        with col_filter2:
            # Option to use main filter or custom date range
            use_main_filter = st.checkbox("Use main dashboard date filter", value=True)
        
        # Apply date filter for category analysis
        if use_main_filter:
            category_data = filtered_data.copy()
        else:
            category_data = data.copy()
            if len(category_date_range) == 2:
                cat_start_date, cat_end_date = category_date_range
                category_data = category_data[
                    (category_data[date_col].dt.date >= cat_start_date) & 
                    (category_data[date_col].dt.date <= cat_end_date)
                ]
        
        category_grouped = category_data.groupby('normalized_category')[amount_col].sum().reset_index()
        category_grouped = category_grouped.sort_values(amount_col, ascending=False)
        
        # Display date range being used for category analysis
        if use_main_filter and len(date_range) == 2:
            st.info(f"📅 Using main dashboard date range: {date_range[0]} to {date_range[1]}")
        elif not use_main_filter and len(category_date_range) == 2:
            st.info(f"📅 Using custom date range: {category_date_range[0]} to {category_date_range[1]}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = px.pie(category_grouped, values=amount_col, names='normalized_category',
                            title="Category Distribution")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(category_grouped, x='normalized_category', y=amount_col,
                            title="Spending by Category")
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Display summary statistics for the category analysis
        st.write("**Category Analysis Summary:**")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            total_category_spending = category_grouped[amount_col].sum()
            st.metric("Total Spending", f"${total_category_spending:,.2f}")
        
        with col_stat2:
            num_categories = len(category_grouped)
            st.metric("Number of Categories", num_categories)
        
        with col_stat3:
            if len(category_grouped) > 0:
                top_category = category_grouped.iloc[0]
                st.metric("Top Category", f"{top_category['normalized_category']}")
                st.caption(f"${top_category[amount_col]:,.2f}")
    
    # Data table
    st.header("📋 Transaction Data")
    
    # Display options - use available columns (including notes)
    available_columns = [col for col in [date_col, amount_col, category_col, description_col, 'bank', 'source_file', 'notes']
                        if col in filtered_data.columns]
    
    show_columns = st.multiselect(
        "Select columns to display",
        options=filtered_data.columns.tolist(),
        default=available_columns
    )
    
    if show_columns:
        # Sorting controls
        col1, col2 = st.columns(2)
        with col1:
            sort_column = st.selectbox(
                "Sort by",
                options=show_columns,
                index=show_columns.index(date_col) if date_col in show_columns else 0
            )
        with col2:
            sort_ascending = st.selectbox(
                "Sort order",
                options=["Descending", "Ascending"],
                index=0
            ) == "Ascending"
        
        # Create a copy of the data for sorting and display
        # Always include transaction_id for notes functionality, even if not displayed
        columns_to_include = show_columns.copy()
        if 'transaction_id' not in columns_to_include and 'transaction_id' in filtered_data.columns:
            columns_to_include.append('transaction_id')
        
        display_data = filtered_data[columns_to_include].copy()
        
        # Sort the data based on user selection
        display_data = display_data.sort_values(sort_column, ascending=sort_ascending)
        
        # Configure column formatting for proper display and editing
        column_config = {}
        if amount_col in show_columns and amount_col in display_data.columns:
            column_config[amount_col] = st.column_config.NumberColumn(
                amount_col,
                format="$%.2f",
                help="Transaction amount",
                disabled=True  # Don't allow editing amounts
            )
        
        # Configure notes column as editable if present
        if 'notes' in show_columns and 'notes' in display_data.columns:
            column_config['notes'] = st.column_config.TextColumn(
                'notes',
                help="Click to add or edit notes for this transaction",
                max_chars=500,
                width="medium"
            )
        
        # Make other columns non-editable except notes
        for col in show_columns:
            if col not in column_config and col != 'notes':
                if col == date_col:
                    column_config[col] = st.column_config.DatetimeColumn(
                        col,
                        disabled=True
                    )
                else:
                    column_config[col] = st.column_config.TextColumn(
                        col,
                        disabled=True
                    )
        
        # Use st.data_editor for editable notes
        if notes_manager is not None:
            # Hide transaction_id column from display but keep it in data
            if 'transaction_id' in display_data.columns and 'transaction_id' not in show_columns:
                column_config['transaction_id'] = None  # This hides the column
            
            edited_data = st.data_editor(
                display_data,
                use_container_width=True,
                column_config=column_config,
                hide_index=True,
                key="transaction_editor"
            )
            
            # Check if notes were edited and save them
            if 'notes' in edited_data.columns and 'transaction_id' in edited_data.columns:
                # Use session state to track if we need to save
                if 'last_edited_data' not in st.session_state:
                    st.session_state.last_edited_data = display_data.copy()
                
                # Compare with the last known state
                notes_changed = False
                changes_made = []
                
                # Check each row for changes
                for idx in edited_data.index:
                    if idx in st.session_state.last_edited_data.index:
                        old_note = str(st.session_state.last_edited_data.loc[idx, 'notes']) if 'notes' in st.session_state.last_edited_data.columns else ""
                        new_note = str(edited_data.loc[idx, 'notes']) if not pd.isna(edited_data.loc[idx, 'notes']) else ""
                        
                        # Clean up the notes (remove 'nan' strings)
                        if old_note == 'nan':
                            old_note = ""
                        if new_note == 'nan':
                            new_note = ""
                        
                        if old_note != new_note:
                            transaction_id = str(edited_data.loc[idx, 'transaction_id'])
                            success = notes_manager.set_note(transaction_id, new_note)
                            if success:
                                notes_changed = True
                                changes_made.append(f"Updated note for transaction {transaction_id[:8]}...")
                                # Update session state
                                st.session_state.last_edited_data.loc[idx, 'notes'] = new_note
                
                if notes_changed:
                    st.success(f"✅ Notes saved successfully! ({len(changes_made)} changes)")
                    # Clear the cache to force data reload
                    if hasattr(st, 'cache_data'):
                        st.cache_data.clear()
            
            # Add manual save button and debug info
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Manual Save", help="Force save all current notes"):
                    saved_count = 0
                    for idx in edited_data.index:
                        if 'notes' in edited_data.columns and 'transaction_id' in edited_data.columns:
                            note = str(edited_data.loc[idx, 'notes']) if not pd.isna(edited_data.loc[idx, 'notes']) else ""
                            if note and note != 'nan':
                                transaction_id = str(edited_data.loc[idx, 'transaction_id'])
                                if notes_manager.set_note(transaction_id, note):
                                    saved_count += 1
                    st.success(f"✅ Manually saved {saved_count} notes!")
            
            with col2:
                if st.button("🔄 Refresh Data", help="Reload data from database"):
                    if 'last_edited_data' in st.session_state:
                        del st.session_state.last_edited_data
                    st.rerun()
            
            with col3:
                # Show debug info
                if st.button("🔍 Debug Info"):
                    st.write("**Debug Information:**")
                    st.write(f"- Notes in edited data: {edited_data['notes'].notna().sum() if 'notes' in edited_data.columns else 0}")
                    st.write(f"- Transaction IDs present: {'transaction_id' in edited_data.columns}")
                    st.write(f"- Session state has last_edited_data: {'last_edited_data' in st.session_state}")
        else:
            # Fallback to regular dataframe if notes manager is not available
            st.dataframe(
                display_data,
                use_container_width=True,
                column_config=column_config
            )
    
    # Notes Statistics
    if notes_manager is not None:
        st.header("📝 Notes Statistics")
        
        notes_stats = notes_manager.get_statistics()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Notes", notes_stats['total_notes'])
        
        with col2:
            st.metric("Total Characters", f"{notes_stats['total_characters']:,}")
        
        with col3:
            avg_length = notes_stats['average_note_length']
            st.metric("Avg Note Length", f"{avg_length:.1f} chars")
        
        with col4:
            if notes_stats['last_updated']:
                last_updated = datetime.fromisoformat(notes_stats['last_updated'].replace('Z', '+00:00'))
                st.metric("Last Updated", last_updated.strftime("%m/%d/%Y"))
        
        # Notes management tools
        if notes_stats['total_notes'] > 0:
            st.subheader("Notes Management")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Search Notes", help="Search through all notes"):
                    search_term = st.text_input("Search for:", key="notes_search")
                    if search_term:
                        matching_notes = notes_manager.search_notes(search_term)
                        if matching_notes:
                            st.write(f"Found {len(matching_notes)} notes containing '{search_term}':")
                            for transaction_id, note in matching_notes.items():
                                st.write(f"**{transaction_id[:8]}...**: {note[:100]}{'...' if len(note) > 100 else ''}")
                        else:
                            st.info("No notes found containing that search term.")
            
            with col2:
                if st.button("💾 Backup Notes", help="Create a backup of all notes"):
                    backup_path = f"./data/notes_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    if notes_manager.backup_notes(backup_path):
                        st.success(f"✅ Notes backed up to: {backup_path}")
                    else:
                        st.error("❌ Failed to create backup")
    
    # Category mapping management
    if 'normalized_category' in data.columns:
        st.header("🏷️ Category Mapping")
        
        unmapped = normalizer.get_unmapped_categories(data, category_col)
        if unmapped:
            st.warning(f"Found {len(unmapped)} unmapped categories:")
            st.write(unmapped)
            
            st.info("To add mappings, edit the `configs/category_mapping.json` file and restart the app.")
    
    # Schema management section
    st.header("🔧 Schema Management")
    
    st.write("**Bank Schema Status:**")
    for bank_name, info in schema_info.items():
        with st.expander(f"{bank_name.title()} Schema"):
            st.write(f"**Supported Formats:** {', '.join(info['formats'])}")
            st.write(f"**Configuration File:** `configs/{bank_name}_schema.json`")
            
            # Show sample of data for this bank
            bank_data = data[data['bank'] == bank_name] if 'bank' in data.columns else pd.DataFrame()
            if not bank_data.empty:
                st.write(f"**Sample Data ({len(bank_data)} transactions):**")
                st.dataframe(bank_data.head())

if __name__ == "__main__":
    main()