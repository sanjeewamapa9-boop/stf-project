import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import base64
import plotly.express as px

# --- DATABASE SETUP ---
conn = sqlite3.connect('stf_master_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, name TEXT UNIQUE, location TEXT, cost REAL, start_date TEXT, end_date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS daily_updates 
             (id INTEGER PRIMARY KEY, project_name TEXT, progress INTEGER, status_note TEXT, photo TEXT, update_time TEXT)''')
conn.commit()

# --- MODERN UI SETUP ---
st.set_page_config(page_title="STF Analytics Hub", layout="wide")

# CSS for styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetricValue"] { font-size: 25px; color: #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

try:
    st.image("logo.png", width=80)
except:
    pass

st.title("🛡️ STF Construction Monitoring Hub")
st.markdown("---")

# --- NAVIGATION ---
page = st.sidebar.radio("Main Menu", ["🏢 Project Registration", "👷 Daily Site Update", "📊 HQ Admin Dashboard"])

# --- 1. PROJECT REGISTRATION ---
if page == "🏢 Project Registration":
    st.header("📍 Register New Project")
    with st.form("reg_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Project Name")
            loc = st.text_input("Location")
        with col2:
            cost = st.number_input("Budget (LKR)", min_value=0.0)
            dates = st.date_input("Timeline", [datetime.now(), datetime.now()])
        if st.form_submit_button("Create Project"):
            if name:
                try:
                    c.execute("INSERT INTO projects (name, location, cost, start_date, end_date) VALUES (?,?,?,?,?)", 
                              (name, loc, cost, str(dates[0]), str(dates[1])))
                    conn.commit()
                    st.success("Project Successfully Registered!")
                except: st.error("Project ID already exists.")

# --- 2. DAILY SITE UPDATE ---
elif page == "👷 Daily Site Update":
    st.header("📝 Daily Progress")
    project_list = pd.read_sql_query("SELECT name FROM projects", conn)['name'].tolist()
    if project_list:
        with st.form("up_form", clear_on_submit=True):
            p_select = st.selectbox("Select Project Site", project_list)
            prog = st.select_slider("Current Progress (%)", options=list(range(0, 101)))
            note = st.text_area("Observations")
            up_photo = st.file_uploader("Site Photo", type=['jpg','png','jpeg'])
            if st.form_submit_button("Sync Update"):
                photo_str = base64.b64encode(up_photo.read()).decode() if up_photo else ""
                c.execute("INSERT INTO daily_updates (project_name, progress, status_note, photo, update_time) VALUES (?,?,?,?,?)",
                          (p_select, prog, note, photo_str, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Daily Update Recorded!")
    else: st.warning("Please register a project first.")

# --- 3. HQ ADMIN DASHBOARD ---
elif page == "📊 HQ Admin Dashboard":
    st.header("🧐 Strategic Intelligence")
    if st.sidebar.text_input("Security Key", type="password") == "stf123":
        query = '''SELECT p.name, p.location, p.cost, p.start_date, p.end_date, u.progress, u.status_note, u.photo, u.update_time
                   FROM projects p LEFT JOIN daily_updates u ON p.name = u.project_name
                   WHERE u.id = (SELECT MAX(id) FROM daily_updates WHERE project_name = p.name) OR u.id IS NULL'''
        df = pd.read_sql_query(query, conn)
        df['progress'] = df['progress'].fillna(0)

        if not df.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Active Projects", len(df))
            m2.metric("Avg. Progress", f"{int(df['progress'].mean())}%")
            m3.metric("Total Investment", f"LKR {df['cost'].sum():,.0f}")

            st.markdown("### 📉 Progress Analytics")
            fig = px.bar(df, x='name', y='progress', color='progress', color_continuous_scale='Blues')
            fig.update_layout(template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Inventory & Visual Records")
            for i, row in df.iterrows():
                with st.expander(f"📌 {row['name']} - {row['progress']}%"):
                    ca, cb = st.columns([1, 2])
                    with ca:
                        if row['photo']: st.image(base64.b64decode(row['photo']), use_container_width=True)
                    with cb:
                        st.write(f"**Cost:** LKR {row['cost']:,.2f}")
                        st.write(f"**Update:** {row['status_note']}")
        else: st.info("Database is empty.")
    else: st.error("Enter valid password.")
