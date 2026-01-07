import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import pytz 

st.set_page_config(page_title="H&H Hospitality Clock", page_icon="🕒")

# --- TIMEZONE SETUP ---
# This ensures "now" is always LA time, regardless of where the server is.
pacific = pytz.timezone('America/Los_Angeles')

st.title("🕒 H&H Hospitality Time Clock")

conn = st.connection("gsheets", type=GSheetsConnection)
employees = ["Alla Soykin", "Halina Maruha", "Sam DeSurra", "Alexandra Corral"]
name = st.selectbox("Select Your Name", employees)

def update_logs(employee_name, action):
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

# --- BI-WEEKLY CALCULATIONS ---
st.subheader(f"Summary for {name}")

try:
    # 1. Read the data
    df = conn.read(worksheet="Sheet1", ttl=0)st.divider()

# --- BI-WEEKLY CALCULATIONS (CRASH-PROOF VERSION) ---
st.subheader(f"Summary for {name}")

try:
    # 1. Read the data
    df = conn.read(worksheet="Sheet1", ttl=0)
    
    # 2. Check if the sheet is empty
    if df.empty:
        st.info("The log is empty. Start by clocking in!")
    else:
        # 3. Clean the Date column (ignore errors if a row is messy)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df = df.dropna(subset=['Date']) # Remove any rows that have a broken date

        # 4. Figure out the 2-week window (Jan 5, 2026 anchor)
        start_anchor = datetime(2026, 1, 5).date()
        today = datetime.now(pacific).date()
        
        # This part calculates which 14-day block we are in
        days_passed = (today - start_anchor).days
        period_start = start_anchor + timedelta(days=(max(0, days_passed) // 14) * 14)
        period_end = period_start + timedelta(days=13)

        st.write(f"📅 **Current Pay Period:** {period_start} to {period_end}")

        # 5. Filter for this person and this period
        mask = (df['Date'] >= period_start) & (df['Date'] <= period_end) & (df['Name'] == name)
        period_df = df.loc[mask].copy()

        if not period_df.empty:
            st.dataframe(period_df, use_container_width=True)
            
            # 6. Calculate Hours
            period_df['Timestamp'] = pd.to_datetime(period_df['Date'].astype(str) + ' ' + period_df['Time'])
            period_df = period_df.sort_values('Timestamp')

            total_hours = 0.0
            for i in range(len(period_df) - 1):
                row1 = period_df.iloc[i]
                row2 = period_df.iloc[i+1]
                
                if row1['Action'] == "Clock In" and row2['Action'] == "Clock Out":
                    duration = row2['Timestamp'] - row1['Timestamp']
                    total_hours += duration.total_seconds() / 3600

            st.metric("Total Hours Worked", f"{total_hours:.2f} hrs")
        else:
            st.warning(f"No records found for {name} in this period.")

except Exception as e:
    # This shows us EXACTLY what the error is instead of just crashing
    st.error(f"Something went wrong: {e}")
