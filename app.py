import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(
    page_title="Energy Analytics Platform",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Energy Analytics Platform")

# ---------------------------
# FILE UPLOAD
# ---------------------------
uploaded_file = st.file_uploader(
    "Upload CSV File",
    type=["csv"]
)

if uploaded_file is not None:

    # ---------------------------
    # READ CSV
    # ---------------------------
    df = pd.read_csv(uploaded_file)

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    st.write("Columns Found:")
    st.write(list(df.columns))

    # ---------------------------
    # DATASET MAPPING
    # ---------------------------
    st.subheader("⚙ Dataset Mapping")

    all_columns = list(df.columns)

    date_column = st.selectbox(
        "Select Date Column",
        all_columns
    )

    time_options = ["None"] + all_columns

    time_column = st.selectbox(
        "Select Time Column (Optional)",
        time_options
    )

    power_options = [
        col for col in df.columns
        if col not in [date_column, time_column]
    ]

    power_column = st.selectbox(
        "Select Consumption Column",
        power_options
    )

    df[power_column] = pd.to_numeric(
        df[power_column],
        errors="coerce"
    )

    # ---------------------------
    # TIMESTAMP CREATION
    # ---------------------------
    try:

        if time_column != "None":

            df["Timestamp"] = pd.to_datetime(
                df[date_column].astype(str)
                + " "
                + df[time_column].astype(str),
                dayfirst=True,
                errors="coerce"
            )

        else:

            df["Timestamp"] = pd.to_datetime(
                df[date_column],
                dayfirst=True,
                errors="coerce"
            )

        df = df.dropna(subset=["Timestamp"])
        df = df.dropna(subset=[power_column])

        if df.empty:

            st.error(
                "No valid rows found. Check your selected Date, Time and Consumption columns."
            )
            st.stop()

    except Exception as e:

        st.error(f"Timestamp creation failed: {e}")
        st.stop()

    df = df.sort_values("Timestamp")

    # ---------------------------
    # DATE FILTER
    # ---------------------------
    try:

        min_date = df["Timestamp"].min().date()
        max_date = df["Timestamp"].max().date()

        date_range = st.date_input(
            "📅 Select Date Range",
            value=(min_date, max_date)
        )

        if len(date_range) == 2:

            start_date, end_date = date_range

            df = df[
                (df["Timestamp"].dt.date >= start_date)
                &
                (df["Timestamp"].dt.date <= end_date)
            ]

    except Exception as e:

        st.warning(
            f"Date filter disabled: {e}"
        )

    # ---------------------------
    # KPI VALUES
    # ---------------------------
    power = pd.to_numeric(
        df[power_column],
        errors="coerce"
    ).dropna()

    total_power = power.sum()
    avg_power = power.mean()
    peak_power = power.max()

    # ---------------------------
    # COST ANALYSIS
    # ---------------------------
    rate = st.number_input(
        "Electricity Rate (₹ per unit)",
        min_value=0.0,
        value=8.0,
        step=0.5
    )

    df["Month"] = (
        df["Timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly_usage = (
        df.groupby("Month")[power_column]
        .sum()
        .reset_index()
    )

    monthly_usage["Estimated_Cost"] = (
        monthly_usage[power_column] * rate
    )

    total_cost = (
        monthly_usage["Estimated_Cost"]
        .sum()
    )

    # ---------------------------
    # KPI CARDS
    # ---------------------------
    st.subheader("📊 Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Consumption",
            f"{total_power:,.2f}"
        )

    with col2:
        st.metric(
            "Average Consumption",
            f"{avg_power:.2f}"
        )

    with col3:
        st.metric(
            "Peak Consumption",
            f"{peak_power:.2f}"
        )

    with col4:
        st.metric(
            "Estimated Cost",
            f"₹ {total_cost:,.2f}"
        )

    # ---------------------------
    # DATE RANGE INFO
    # ---------------------------
    st.subheader("📅 Data Range")

    st.write(
        "Start Date:",
        df["Timestamp"].min()
    )

    st.write(
        "End Date:",
        df["Timestamp"].max()
    )

    # ---------------------------
    # TREND CHART
    # ---------------------------
    st.subheader("📈 Consumption Trend")

    trend_fig = px.line(
        df.head(1000),
        x="Timestamp",
        y=power_column,
        title=f"{power_column} Over Time"
    )

    st.plotly_chart(
        trend_fig,
        use_container_width=True
    )

    # ---------------------------
    # MONTHLY TABLE
    # ---------------------------
    st.subheader("📋 Monthly Cost Breakdown")

    st.dataframe(
        monthly_usage[
            ["Month", "Estimated_Cost"]
        ]
    )

    # ---------------------------
    # DOWNLOAD REPORT
    # ---------------------------
    csv = monthly_usage.to_csv(index=False)

    st.download_button(
        label="📥 Download Monthly Report",
        data=csv,
        file_name="monthly_energy_report.csv",
        mime="text/csv"
    )

    # ---------------------------
    # COST CHART
    # ---------------------------
    st.subheader("📊 Monthly Cost Trend")

    cost_fig = px.bar(
        monthly_usage,
        x="Month",
        y="Estimated_Cost",
        title="Monthly Electricity Cost"
    )

    st.plotly_chart(
        cost_fig,
        use_container_width=True
    )


    # ---------------------------
    # TOP 10 RECORDS
    # ---------------------------
    st.subheader("⚡ Top 10 Peak Consumption Records")

    top_usage = df.nlargest(
        10,
        power_column
    )[
        ["Timestamp", power_column]
    ]

    st.dataframe(top_usage)

    # ---------------------------
    # INSIGHTS
    # ---------------------------
    highest_month = monthly_usage.loc[
        monthly_usage[power_column].idxmax()
    ]

    lowest_month = monthly_usage.loc[
        monthly_usage[power_column].idxmin()
    ]

    st.subheader("🧠 Automated Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Highest Consumption Month",
            highest_month["Month"]
        )

    with col2:
        st.metric(
            "Lowest Consumption Month",
            lowest_month["Month"]
        )

    st.success(
        f"Highest consumption month was {highest_month['Month']}"
    )

    st.info(
        f"Lowest consumption month was {lowest_month['Month']}"
    )

    st.write(
        f"Peak recorded consumption: {peak_power:.2f}"
    )

    st.write(
        f"Average consumption: {avg_power:.2f}"
    )

else:

    st.info(
        "Upload a CSV file to start analysis."
    )