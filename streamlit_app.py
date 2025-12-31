import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(page_title="HNH Time Clock", page_icon="🕒")

st.title("🕒 Employee Time Clock")
st.markdown("Select your name and click the button to log your time.")

# Connect to Google Sheets (using the secrets we will set up)
conn = st.connection("gsheets", type=GSheetsConnection)

# Employee List (You can add more names here as you grow!)
employees = [
    "Alice Smith", 
    "Bob Jones", 
    "Charlie Brown", 
    "Dana White", 
    "Eve Adams", 
    "Frank Miller"
]

name = st.selectbox("Employee Name", employees)

col1, col2 = st.columns(2)

with col1:
    if st.button("✅ Clock In", use_container_width=True):
        now = datetime.now()
        new_data = pd.DataFrame([{
            "Name": name,
            "Action": "Clock In",
            "Time": now.strftime("%H:%M:%S"),
            "Date": now.strftime("%Y-%m-%d")
        }])
        # Read existing, add new, and update
        existing_df = conn.read()
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        conn.update(data=updated_df)
        st.success(f"Clocked IN at {now.strftime('%I:%M %p')}")

with col2:
    if st.button("🛑 Clock Out", use_container_width=True):
        now = datetime.now()
        new_data = pd.DataFrame([{
            "Name": name,
            "Action": "Clock Out",
            "Time": now.strftime("%H:%M:%S"),
            "Date": now.strftime("%Y-%m-%d")
        }])
        existing_df = conn.read()
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        conn.update(data=updated_df)
        st.error(f"Clocked OUT at {now.strftime('%I:%M %p')}")

# Recent Activity Table
st.divider()
st.subheader("Recent Activity")
recent_data = conn.read()
st.dataframe(recent_data.tail(10), use_container_width=True)
