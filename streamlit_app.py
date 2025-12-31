import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Company Time Clock", page_icon="🕒")

st.title("🕒 Employee Time Clock")

# Connect with a cache reset time (ttl)
conn = st.connection("gsheets", type=GSheetsConnection)

employees = ["Alice Smith", "Bob Jones", "Charlie Brown", "Dana White", "Eve Adams", "Frank Miller"]
name = st.selectbox("Employee Name", employees)

col1, col2 = st.columns(2)

# Helper function to handle the update
def update_logs(employee_name, action):
    now = datetime.now()
    new_entry = pd.DataFrame([{
        "Name": employee_name,
        "Action": action,
        "Time": now.strftime("%H:%M:%S"),
        "Date": now.strftime("%Y-%m-%d")
    }])
    
    try:
        # We specify worksheet="Sheet1" clearly here
        existing_df = conn.read(worksheet="Sheet1", ttl=0)
        updated_df = pd.concat([existing_df, new_entry], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        return now
    except Exception as e:
        st.error(f"Error connecting to sheet: {e}")
        return None

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
st.subheader("Recent Activity")
try:
    # Refresh data to show latest logs
    df = conn.read(worksheet="Sheet1", ttl=0)
    st.dataframe(df.tail(10), use_container_width=True)
except:
    st.info("No logs found yet. Be the first to clock in!")
