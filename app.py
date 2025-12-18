import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import base64

# --- DATABASE SETUP ---
conn = sqlite3.connect('stf_final_master.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, name TEXT UNIQUE, location TEXT, cost REAL, start_date TEXT, end_date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS daily_updates 
             (id INTEGER PRIMARY KEY, project_name TEXT, progress INTEGER, status_note TEXT, photo TEXT, update_time TEXT)''')
conn.commit()

# --- UI SETUP ---
st.set_page_config(page_title="STF Monitoring System", layout="wide")

try:
    st.image("logo.png", width=100)
except:
    pass

st.title("🛡️ STF Construction Management System")
st.markdown("---")

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation Menu:", ["🏢 Project Registration", "👷 Daily Site Update", "📊 HQ Admin Dashboard"])

# --- 1. PROJECT REGISTRATION ---
if page == "🏢 Project Registration":
    st.header("📍 Register New Project")
    with st.form("reg_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Project Name / ID")
            loc = st.text_input("Location")
            cost = st.number_input("Total Cost (LKR)", min_value=0.0)
        with col2:
            s_date = st.date_input("Start Date")
            e_date = st.date_input("Target End Date")
        if st.form_submit_button("Register Project"):
            if name:
                try:
                    c.execute("INSERT INTO projects (name, location, cost, start_date, end_date) VALUES (?,?,?,?,?)", (name, loc, cost, str(s_date), str(e_date)))
                    conn.commit()
                    st.success("Project Registered!")
                except:
                    st.error("Already exists!")

# --- 2. DAILY SITE UPDATE ---
elif page == "👷 Daily Site Update":
    st.header("📝 Daily Update")
    project_list = pd.read_sql_query("SELECT name FROM projects", conn)['name'].tolist()
    if project_list:
        with st.form("up_form", clear_on_submit=True):
            p_select = st.selectbox("Select Project", project_list)
            prog = st.slider("Progress %", 0, 100)
            note = st.text_area("Daily Note")
            up_photo = st.file_uploader("Site Photo", type=['jpg','png','jpeg'])
            if st.form_submit_button("Submit"):
                photo_str = base64.b64encode(up_photo.read()).decode() if up_photo else ""
                c.execute("INSERT INTO daily_updates (project_name, progress, status_note, photo, update_time) VALUES (?,?,?,?,?)",
                          (p_select, prog, note, photo_str, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Update Sent!")
    else: st.warning("No projects registered.")

# --- 3. HQ ADMIN DASHBOARD ---
elif page == "📊 HQ Admin Dashboard":
    st.header("🧐 HQ Central Panel")
    if st.sidebar.text_input("Admin Password", type="password") == "stf123":
        query = '''SELECT p.name, p.location, p.cost, p.start_date, p.end_date, u.progress, u.status_note, u.photo, u.update_time
                   FROM projects p LEFT JOIN daily_updates u ON p.name = u.project_name
                   WHERE u.id = (SELECT MAX(id) FROM daily_updates WHERE project_name = p.name) OR u.id IS NULL'''
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            st.dataframe(df.drop(columns=['photo']), use_container_width=True)
            st.download_button("📥 Download Excel", df.drop(columns=['photo']).to_csv(index=False).encode('utf-8'), "Report.csv", "text/csv")
            for i, row in df.iterrows():
                with st.expander(f"View: {row['name']} ({row['progress'] if row['progress'] else 0}%)"):
                    ca, cb = st.columns([1, 2])
                    with ca:
                        if row['photo']: st.image(base64.b64decode(row['photo']), use_container_width=True)
                    with cb:
                        st.write(f"**Cost:** LKR {row['cost']:,.2f}")
                        st.write(f"**Note:** {row['status_note']}")
        else: st.info("No data yet.")
    else: st.error("Enter password in sidebar.")
