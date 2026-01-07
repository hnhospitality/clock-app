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
    df = conn.read(worksheet="Sheet1", ttl=0)
    
    # 2. Tell Python that the 'Date' column is actually dates, not just text
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    # 3. Figure out the 2-week window
    start_anchor = datetime(2026, 1, 5).date()
    today = datetime.now(pacific).date()
    
    days_passed = (today - start_anchor).days
    period_start = start_anchor + timedelta(days=(days_passed // 14) * 14)
    period_end = period_start + timedelta(days=13)

    st.write(f"**Current Pay Period:** {period_start} to {period_end}")

    # 4. Filter data for this person and this date range
    mask = (df['Date'] >= period_start) & (df['Date'] <= period_end) & (df['Name'] == name)
    period_df = df.loc[mask].copy()

    if not period_df.empty:
        st.dataframe(period_df, use_container_width=True)
        
        # --- TOTAL HOURS MATH ---
        # We combine Date and Time into one 'Timestamp' so we can subtract them
        period_df['Timestamp'] = pd.to_datetime(period_df['Date'].astype(str) + ' ' + period_df['Time'])
        period_df = period_df.sort_values('Timestamp')

        total_hours = 0.0
        # This loop looks for an 'In' followed by an 'Out'
        for i in range(len(period_df) - 1):
            row1 = period_df.iloc[i]
            row2 = period_df.iloc[i+1]
            
            if row1['Action'] == "Clock In" and row2['Action'] == "Clock Out":
                duration = row2['Timestamp'] - row1['Timestamp']
                total_hours += duration.total_seconds() / 3600 # Convert seconds to hours

        st.metric("Total Hours Worked", f"{total_hours:.2f} hrs")
    else:
        st.info("No activity recorded for this pay period.")

except Exception as e:
    st.warning("Ready for your first entry!")
