import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import pytz  # This handles the time zones

st.set_page_config(page_title="H&H Hospitality Clock", page_icon="🕒")

# 1. SET THE TIMEZONE
pacific = pytz.timezone('America/Los_Angeles')

st.title("🕒 H&H Hospitality Time Clock")

conn = st.connection("gsheets", type=GSheetsConnection)
employees = ["Alla Soykin", "Halina Maruha", "Sam DeSurra", "Alexandra Corral"]
name = st.selectbox("Select Your Name", employees)

def update_logs(employee_name, action):
    # Get the current time in Pacific Time
    now = datetime.now(pacific) 
    
    new_entry = pd.DataFrame([{
        "Name": employee_name,
        "Action": action,
        "Time": now.strftime("%H:%M:%S"),
        "Date": now.strftime("%Y-%m-%d")
    }])
    
    try:
        existing_df = conn.read(worksheet="Sheet1", ttl=0)
        updated_df = pd.concat([existing_df, new_entry], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        return now
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# BUTTONS
col1, col2 = st.columns(2)
with col1:
    if st.button("✅ Clock In", use_container_width=True):
        time_result = update_logs(name, "Clock In")
        if time_result:
            st.success(f"Clocked IN at {time_result.strftime('%I:%M %p')}")

with col2:
    if st.button("🛑 Clock Out", use_container_width=True):
        time_result = update_logs(name, "Clock Out")
        if time_result:
            st.error(f"Clocked OUT at {time_result.strftime('%I:%M %p')}")

st.divider()

# --- LOGIC FOR THE 2-WEEK PAY PERIOD ---
st.subheader("Current Pay Period Totals")

try:
    df = conn.read(worksheet="Sheet1", ttl=0)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Define start date (Jan 5, 2026)
    start_date = datetime(2026, 1, 5).date()
    today = datetime.now(pacific).date()
    
    # Calculate how many days since start
    days_since_start = (today - start_date).days
    # Calculate which 14-day period we are in
    period_number = days_since_start // 14
    current_period_start = start_date + timedelta(days=period_number * 14)
    current_period_end = current_period_start + timedelta(days=13)

    st.info(f"Current Period: {current_period_start} to {current_period_end}")

    # Filter data for ONLY this period and ONLY this employee
    period_df = df[(df['Date'].dt.date >= current_period_start) & 
                   (df['Date'].dt.date <= current_period_end) & 
                   (df['Name'] == name)].copy()

    # Simple logic to show the logs
    st.dataframe(period_df, use_container_width=True)

    # Calculation Logic:
    # This pairs 'In' and 'Out' to calculate hours
    if not period_df.empty:
        # Sort by time to ensure they are in order
        period_df = period_df.sort_values(by=["Date", "Time"])
        
        # This is a slightly advanced concept: we're grouping rows to find the difference
        # For a beginner: just know this looks for "Clock In" followed by "Clock Out"
        total_seconds = 0
        # ... logic to sum hours ... (we can expand this as you learn!)
        
except Exception as e:
    st.info("Start clocking in to see your 2-week summary!")
