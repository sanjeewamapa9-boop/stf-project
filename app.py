import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Database setup
conn = sqlite3.connect('stf_projects.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, name TEXT, location TEXT, start_date TEXT, end_date TEXT, progress INTEGER)''')
conn.commit()

# UI Setup
st.set_page_config(page_title="STF Monitoring", layout="wide")

# --- LOGO SECTION ---
# ඔයා අප්ලෝඩ් කරපු ලෝගෝ එකේ නම logo.png නෙමෙයි නම්, පහත නම වෙනස් කරන්න
try:
    st.image("logo.png", width=120) 
except:
    st.info("Logo image not found. Please upload it via GitHub.")

st.title("STF Construction Monitoring System")
st.markdown("---")

# Data Entry Section
with st.expander("➕ Add New Project Details"):
    with st.form("project_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_name = st.text_input("Project Name")
            p_loc = st.text_input("Location")
        with col2:
            p_start = st.date_input("Start Date", datetime.now())
            p_end = st.date_input("Target End Date", datetime.now())
        
        p_progress = st.slider("Completion Progress (%)", 0, 100, 0)
        
        submit = st.form_submit_button("Save Project Data")
        
        if submit and p_name:
            c.execute("INSERT INTO projects (name, location, start_date, end_date, progress) VALUES (?,?,?,?,?)",
                      (p_name, p_loc, str(p_start), str(p_end), p_progress))
            conn.commit()
            st.success(f"Project '{p_name}' saved successfully!")

# Display Section
st.subheader("📋 Ongoing Projects Status")
df = pd.read_sql_query("SELECT name as 'Project', location as 'Location', start_date as 'Start Date', end_date as 'End Date', progress as 'Progress (%)' FROM projects", conn)

if not df.empty:
    st.dataframe(df, use_container_width=True)
    st.subheader("📊 Progress Overview")
    st.bar_chart(df.set_index('Project')['Progress (%)'])
else:
    st.info("No projects added yet.")
