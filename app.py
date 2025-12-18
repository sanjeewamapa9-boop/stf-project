import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Database setup
conn = sqlite3.connect('stf_master_db.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, name TEXT, location TEXT, cost REAL, start_date TEXT, end_date TEXT, progress INTEGER, entry_time TEXT)''')
conn.commit()

# UI Setup
st.set_page_config(page_title="STF Monitoring System", layout="wide")

# Logo
try:
    st.image("logo.png", width=100)
except:
    pass

st.title("STF Construction Monitoring System")

# --- SIDEBAR LOGIN FOR HQ ---
st.sidebar.title("Login Section")
is_admin = st.sidebar.checkbox("Login as HQ Admin")

if is_admin:
    password = st.sidebar.text_input("Enter Admin Password", type="password")
    if password == "stf123": # මෙතන password එක ඔයාට ඕන එකක් දාන්න
        st.sidebar.success("Logged in as HQ")
        mode = "HQ Admin"
    else:
        st.sidebar.error("Incorrect Password")
        mode = "Public"
else:
    mode = "Public"

# --- MAIN INTERFACE ---

if mode == "Public":
    st.header("➕ Site Progress Update (Public)")
    st.info("සයිට් එකේ තොරතුරු පහත ෆෝම් එකෙන් ඇතුළත් කරන්න.")
    
    with st.form("site_entry", clear_on_submit=True):
        p_name = st.text_input("Project Name / Description")
        p_loc = st.text_input("Location (Site Name)")
        
        col1, col2 = st.columns(2)
        with col1:
            p_cost = st.number_input("Estimated Cost (LKR)", min_value=0.0)
            p_start = st.date_input("Start Date", datetime.now())
        with col2:
            p_progress = st.slider("Current Progress (%)", 0, 100, 0)
            p_end = st.date_input("Expected End Date", datetime.now())
            
        submit = st.form_submit_button("Submit Data to HQ")
        
        if submit and p_name:
            entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO projects (name, location, cost, start_date, end_date, progress, entry_time) VALUES (?,?,?,?,?,?,?)",
                      (p_name, p_loc, p_cost, str(p_start), str(p_end), p_progress, entry_time))
            conn.commit()
            st.success("✅ දත්ත සාර්ථකව HQ වෙත යවන ලදී!")

else: # HQ Admin Mode
    st.header("📊 HQ Management Dashboard")
    
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    
    if not df.empty:
        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Projects", len(df))
        m2.metric("Total Cost", f"LKR {df['cost'].sum():,.2f}")
        m3.metric("Avg. Progress", f"{int(df['progress'].mean())}%")
        
        st.divider()
        
        # Data Table
        st.subheader("📋 Detailed Project Report")
        st.dataframe(df, use_container_width=True)
        
        # Excel / CSV Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Report as Excel (CSV)",
            data=csv,
            file_name=f'STF_Report_{datetime.now().date()}.csv',
            mime='text/csv',
        )
        
        # Charts
        st.subheader("📈 Progress Analysis")
        st.bar_chart(df.set_index('name')['progress'])
    else:
        st.warning("තවමත් කිසිදු දත්තයක් ඇතුළත් කර නොමැත.")
