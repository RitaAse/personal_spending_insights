import streamlit as st
import pandas as pd

# -------------------
# CONFIG
# -------------------
st.set_page_config(layout="wide")

# -------------------
# LOAD DATA
# -------------------
df = pd.read_csv("budget_data_cleaned_features.csv")
df['date_time'] = pd.to_datetime(df['date_time'])

# -------------------
# SIDEBAR (LEFT)
# -------------------
st.sidebar.title("🔎 Filters")

# YEAR FILTER
# -------------------
years = sorted(df['year'].unique().tolist())
year_options = ["All"] + years

selected_year = st.sidebar.radio("Select Year", year_options)

# -------------------
# MONTH FILTER
# -------------------
months = ['January','February','March','April','May','June','July','August','September','October','November','December']
month_options = ["All"] + months

selected_month = st.sidebar.radio("Select Month", month_options)

# Category Filter
categories = sorted(df['category'].unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Select Category",
    ["All"] + categories,
    default=["All"]
)
# Handle "All" selection
if "All" in selected_categories:
    selected_categories = categories


# Apply filters
filtered_df = df.copy()

# Apply year filter
if selected_year != "All":
    filtered_df = filtered_df[filtered_df['year'] == selected_year]

# Apply month filter
if selected_month != "All":
    filtered_df = filtered_df[filtered_df['month'] == selected_month]

# Apply category + amount filters
filtered_df = filtered_df[
    (filtered_df['category'].isin(selected_categories))
    ]

# SHOW CURRENT VIEW LABEL (Step 3)
# -------------------
if selected_year == "All" and selected_month == "All":
    st.info("📊 Viewing: All Years Overview")
elif selected_year != "All" and selected_month == "All":
    st.info(f"📊 Viewing: Full Year {selected_year}")
elif selected_year != "All" and selected_month != "All":
    st.info(f"📊 Viewing: {selected_month} {selected_year}")
else:
    st.info(f"📊 Viewing: {selected_month} across all years")



# -------------------
# MAIN LAYOUT (2 COLUMNS)
# -------------------
main_col, insight_col = st.columns([3, 1])  # right column = insights

# -------------------
# MAIN DASHBOARD
# -------------------
with main_col:
    
    min_date = df['date_time'].min().date()
    max_date = df['date_time'].max().date()

    st.title("💰 Fimo: Personal Spending Insights Dashboard")
    st.markdown("""
    Your financial assistant that helps you understand and control spending.
            
    This dashboard helps you understand **where your money goes**,  
    identify **spending patterns**, and discover **ways to optimize your budget**.
    """)
    st.caption(f"📅 Data covers transactions from {min_date} to {max_date}. Use filters to see monthly or yearly breakdowns.")

        # KPIs
    col1, col2, col3 = st.columns(3)
    total = filtered_df['amount'].sum()
    transactions = len(filtered_df)
    avg_spend = filtered_df['amount'].mean()
    
    col1.metric("Total Spending", f"${total:,.2f}", "Filter by Month/Year")
    col2.metric("Number of purchases", transactions, "Filter by Month/Year")
    col3.metric("Average Spend", f"${avg_spend:,.2f}", "Filter by Month/Year")
    st.divider()

        # ADVANCED INSIGHTS (DETAILED CATEGORY VIEW)
    # -------------------
    st.info("Want to explore exactly how your money was spent? Expand the section below!")
    with st.expander("🔍 See Detailed Spending by Category"):
        
                # Describe the period dynamically
        if selected_year == "All" and selected_month == "All":
            period_text = "all years"
        elif selected_year != "All" and selected_month == "All":
            period_text = f"the year {selected_year}"
        elif selected_year != "All" and selected_month != "All":
            period_text = f"{selected_month} {selected_year}"
        else:
            period_text = f"{selected_month} across all years"

        st.write(f"Here’s a detailed breakdown of your purchases for **{period_text}**:")

        if not filtered_df.empty:
            # Already computed for charts
            category_sum = filtered_df.groupby('category')['amount'].sum().sort_values(ascending=False)
            category_count = filtered_df['category'].value_counts()

            # Build detailed table
            category_df = pd.DataFrame({
                'Category': category_sum.index,  # Categories ordered by Total Spent
                'Number of Purchases': category_count[category_sum.index].values,
                'Total Spent': category_sum.values
            })

        # Keep a numeric column for highlighting
            category_df['Total Spent Numeric'] = category_df['Total Spent']

            # Format Total Spent for display (1 decimal, no trailing zeros)
            category_df['Total Spent'] = category_df['Total Spent'].apply(
                lambda x: f"{x:.1f}".rstrip('0').rstrip('.') if x % 1 else f"{int(x)}"
            )

            # Highlight top spender using numeric column
            def highlight_top_total_spent(row):
                if row['Total Spent Numeric'] == category_df['Total Spent Numeric'].max():
                    return ['background-color: #FFD700']*len(row)
                else:
                    return ['']*len(row)

            st.dataframe(category_df.style.apply(highlight_top_total_spent, axis=1))
        else:
            st.info("No data available for this selection")

    monthly_trend = df.groupby('month')['amount'].sum().reindex(months)

    # Convert to DataFrame
    monthly_df = monthly_trend.reset_index()
    monthly_df.columns = ['month', 'amount']

    # Add highlight column
    monthly_df['highlight'] = monthly_df['month'] == selected_month

    st.bar_chart(monthly_df.set_index('month')['amount'])

    st.info(f"📍 Viewing: {selected_month} {selected_year}")


    # CATEGORY ANALYSIS
    st.subheader("🏪 Spending by Category")

    col1, col2 = st.columns(2)

    category_sum = filtered_df.groupby('category')['amount'].sum().sort_values(ascending=False)
    category_count = filtered_df['category'].value_counts()

    with col1:
        st.write("Total Spending")
        st.bar_chart(category_sum)

    with col2:
        st.write("Number of Purchases")
        st.bar_chart(category_count)

    st.divider()

    # TIME ANALYSIS
    st.subheader("📅 Spending Trends")

    col1, col2 = st.columns(2)

    monthly_trend = filtered_df.groupby('month')['amount'].sum().reindex(months)
    weekday_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    weekday_trend = filtered_df.groupby('day')['amount'].sum().reindex(weekday_order)

    with col1:
        st.write("Monthly Spending")
        st.line_chart(monthly_trend)

    with col2:
        st.write("Weekday Spending")
        st.bar_chart(weekday_trend)

    # -------------------


# RIGHT PANEL (INSIGHTS ON DEMAND)
# -------------------
with insight_col:

    st.subheader("💡 Insights Panel")

    # Monthly insights

    monthly_insights = pd.read_csv("monthly_insights.csv")
    if selected_year != "All" and selected_month != "All":
        month_data = monthly_insights[
            (monthly_insights['year'] == selected_year) &
            (monthly_insights['month'] == selected_month)
        ]

        if not month_data.empty:
            total = month_data['total_spent'].values[0]
            transactions = month_data['transactions'].values[0]
            top_cat = month_data['top_category'].values[0]
        else:
            st.warning("No data available for this selection")
            total = transactions = top_cat = None
      
    elif selected_year != "All" and selected_month == "All":
        # Year insights computed live
        year_df = df[df['year'] == selected_year]
        total = year_df['amount'].sum()
        transactions = len(year_df)
        top_cat = year_df.groupby('category')['amount'].sum().idxmax()

    else:  # All years
        total = df['amount'].sum()
        transactions = len(df)
        top_cat = df.groupby('category')['amount'].sum().idxmax()

                # -------------------
    # Display Metrics & Button Insights (Step 5)
    # -------------------
    if total is not None:
        if st.button("Show Summary"):
            st.info(f"""
            - Total Spending: ${total:,.2f}
            - Transactions: {transactions}
            - Top Category: {top_cat}
            """)

        st.metric("Total Spending", f"${total:,.0f}")
        st.metric("Transactions", int(transactions))
        st.metric("Top Category", top_cat)
        # Comparison Logic
        # -------------------
        if selected_month != "All" and selected_year != "All":
            # Month-to-month comparison
            with st.expander("📊 Compare with Previous Month"):
                current_index = months.index(selected_month)
                if current_index > 0:
                    previous_month = months[current_index - 1]
                    current_data = monthly_insights[
                        (monthly_insights['year'] == selected_year) &
                        (monthly_insights['month'] == selected_month)
                    ]
                    previous_data = monthly_insights[
                        (monthly_insights['year'] == selected_year) &
                        (monthly_insights['month'] == previous_month)
                    ]
                    if not current_data.empty and not previous_data.empty:
                        current_total = current_data['total_spent'].values[0]
                        previous_total = previous_data['total_spent'].values[0]
                        if previous_total > 0:
                            change_pct = ((current_total - previous_total) / previous_total) * 100
                            if change_pct > 0:
                                st.warning(f"📈 Spending increased by {change_pct:.1f}% compared to {previous_month}")
                            elif change_pct < 0:
                                st.success(f"📉 Spending decreased by {abs(change_pct):.1f}% compared to {previous_month}")
                            else:
                                st.info("No change in spending compared to previous month")
                    else:
                        st.info("No data available for comparison with previous month")
                else:
                    st.info("No previous month available for comparison")

        elif selected_year != "All" and selected_month == "All":
            # Year-to-year comparison
            with st.expander("📊 Compare with Previous Year"):
                previous_year = str(int(selected_year) - 1)
                current_year_total = total
                previous_year_df = df[df['year'] == previous_year]
                previous_total = previous_year_df['amount'].sum() if not previous_year_df.empty else None

                if previous_total is not None and previous_total > 0:
                    change_pct = ((current_year_total - previous_total) / previous_total) * 100
                    if change_pct > 0:
                        st.warning(f"📈 Spending increased by {change_pct:.1f}% compared to {previous_year}")
                    elif change_pct < 0:
                        st.success(f"📉 Spending decreased by {abs(change_pct):.1f}% compared to {previous_year}")
                    else:
                        st.info(f"No change in spending compared to {previous_year}")
                else:
                    st.info("No previous year data available for comparison")

    else:
        st.warning("No data available for this selection")
    
    # Compute insights
    if not filtered_df.empty:
        top_category = category_sum.idxmax()
        peak_month = monthly_trend.idxmax()
    else:
        top_category = None
        peak_month = None

    # BUTTON-BASED INSIGHTS (progressive disclosure)

    if st.button("Show Top Spending Insight"):
        st.info(f"You spend the most in **{top_category}**.")

    if st.button("Show Peak Month Insight"):
        st.info(f"Your highest spending month is **{peak_month}**.")

    if st.button("Show Behavior Insight"):
        st.info("""
        Your overall spending is driven more by **frequency of purchases** 
        rather than cost per transaction.
        """)

    if st.button("Show Recommendation"):
        st.success("""
        - Reduce frequent purchases (coffee, restaurants)
        - Plan ahead for high-spending months
        - Track categories with frequent transactions
        """)

    # # OPTIONAL ADVANCED INSIGHT
    # with st.expander("🔍 Advanced Insights"):
    #     st.write("Detailed category breakdown")
    #     st.dataframe(category_sum)