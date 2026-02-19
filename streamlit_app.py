import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="HN Hospitality Clock", page_icon="🕒")

pacific = pytz.timezone('America/Los_Angeles')
st.title("🕒 HN Hospitality Time Clock")

# Stable connection
conn = st.connection("gsheets", type=GSheetsConnection)

employees = ["Alla Soykin", "Halina Maruha", "Sam DeSurra", "Alexandra Corral", "Elizabeth Knight"]
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
        # This version uses the dot-style which matches your [connections.gsheets] header
        sheet_url = st.secrets.connections.gsheets.spreadsheet
        
        # 1. Read the data
        existing_df = conn.read(spreadsheet=sheet_url, worksheet="Sheet1", ttl=0)
        
        # 2. Filter out "Unnamed" columns
        existing_df = existing_df.loc[:, ~existing_df.columns.str.contains('^Unnamed')]
        
        # 3. Combine old data with new row
        updated_df = pd.concat([existing_df, new_entry], ignore_index=True)
        
        # 4. Update the sheet
        conn.update(spreadsheet=sheet_url, worksheet="Sheet1", data=updated_df)
        
        return now
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")
        return None

col1, col2 = st.columns(2)
with col1:
    if st.button("✅ Clock In", use_container_width=True):
        res = update_logs(name, "Clock In")
        if res: st.success(f"Clocked IN at {res.strftime('%I:%M %p')}")

with col2:
    if st.button("🛑 Clock Out", use_container_width=True):
        res = update_logs(name, "Clock Out")
        if res: st.error(f"Clocked OUT at {res.strftime('%I:%M %p')}")

st.divider()
st.subheader(f"Summary for {name}")

try:
    # Use the same secret path here!
    sheet_url = st.secrets.connections.gsheets.spreadsheet
    df = conn.read(spreadsheet=sheet_url, worksheet="Sheet1", ttl=0)
    
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df = df.dropna(subset=['Date'])

        # Pay Period Logic
        start_anchor = datetime(2026, 1, 5).date()
        today = datetime.now(pacific).date()
        days_passed = (today - start_anchor).days
        period_start = start_anchor + timedelta(days=(max(0, days_passed) // 14) * 14)
        period_end = period_start + timedelta(days=13)

        st.write(f"📅 **Current Pay Period:** {period_start} to {period_end}")

        mask = (df['Date'] >= period_start) & (df['Date'] <= period_end) & (df['Name'] == name)
        period_df = df.loc[mask].copy()

        if not period_df.empty:
            st.dataframe(period_df, use_container_width=True)
            period_df['Timestamp'] = pd.to_datetime(period_df['Date'].astype(str) + ' ' + period_df['Time'])
            period_df = period_df.sort_values('Timestamp')

            total_hours = 0.0
            for i in range(len(period_df) - 1):
                r1, r2 = period_df.iloc[i], period_df.iloc[i+1]
                if r1['Action'] == "Clock In" and r2['Action'] == "Clock Out":
                    total_hours += (r2['Timestamp'] - r1['Timestamp']).total_seconds() / 3600
            st.metric("Total Hours Worked", f"{total_hours:.2f} hrs")
except Exception as e:
    st.info("Start clocking in to see your summary!")
