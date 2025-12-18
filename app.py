import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import base64

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('stf_integrated_system.db', check_same_thread=False)
    c = conn.cursor()
    # ප්‍රොජෙක්ට් එකේ මූලික විස්තර සේව් කරන ටේබල් එක
    c.execute('''CREATE TABLE IF NOT EXISTS projects 
                 (id INTEGER PRIMARY KEY, name TEXT UNIQUE, location TEXT, cost REAL, start_date TEXT, end_date TEXT)''')
    # දිනපතා අප්ඩේට් සහ ෆොටෝ සේව් කරන ටේබල් එක
    c.execute('''CREATE TABLE IF NOT EXISTS daily_updates 
                 (id INTEGER PRIMARY KEY, project_name TEXT, progress INTEGER, status_note TEXT, photo TEXT, update_time TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- UI SETUP ---
st.set_page_config(page_title="STF Master Control", layout="wide")

# Logo (GitHub එකේ logo.png නමින් තිබිය යුතුය)
try:
    st.image("logo.png", width=100)
except:
    pass

st.title("🛡️ STF Construction Management System")
st.markdown("---")

# --- NAVIGATION SIDEBAR ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to Panel:", ["🏢 Project Registration", "👷 Daily Site Update", "📊 HQ Admin Dashboard"])

# --- 1. PROJECT REGISTRATION PANEL ---
if page == "🏢 Project Registration":
    st.header("📍 Register New Project Site")
    st.info("HQ මගින් නව ව්‍යාපෘතියක් පද්ධතියට ඇතුළත් කිරීම මෙතැනින් සිදු කරයි.")
    
    with st.form("reg_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Project Name / ID")
            loc = st.text_input("Site Location")
            cost = st.number_input("Total Budgeted Cost (LKR)", min_value=0.0)
        with col2:
            s_date = st.date_input("Project Start Date")
            e_date = st.date_input("Target Completion Date")
        
        submit_reg = st.form_submit_button("Register Project")
        
        if submit_reg and name:
            try:
                c.execute("INSERT INTO projects (name, location, cost, start_date, end_date) VALUES (?,?,?,?,?)",
                          (name, loc, cost, str(s_date), str(e_date)))
                conn.commit()
                st.success(f"Project '{name}' registered successfully!")
            except:
                st.error("මෙම නමින් ප්‍රොජෙක්ට් එකක් දැනටමත් ඇත.")

# --- 2. DAILY SITE UPDATE PANEL ---
elif page == "👷 Daily Site Update":
    st.header("📝 Daily Progress Update")
    st.write("සයිට් එකේ සිටින නිලධාරියා විසින් දිනපතා විස්තර මෙතැනින් එවන්න.")
    
    # දැනට තියෙන ප්‍රොජෙක්ට් ලිස්ට් එක ගන්නවා
    project_list = pd.read_sql_query("SELECT name FROM projects", conn)['name'].tolist()
    
    if project_list:
        with st.form("update_form", clear_on_submit=True):
            selected_p = st.selectbox("Select Project", project_list)
            prog = st.slider("Current Completion Progress (%)", 0, 100)
            note = st.text_area("Daily Progress / Issues Note")
            up_photo = st.file_uploader("Upload Site Photo (Daily)", type=['jpg', 'png', 'jpeg'])
            
            submit_up = st.form_submit_button("Submit Daily Update")
            
            if submit_up:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                photo_str = ""
                if up_photo:
                    photo_str = base64.b64encode(up_photo.read()).decode()
                
                c.execute("INSERT INTO daily_updates (project_name, progress, status_note, photo, update_time) VALUES (?,?,?,?,?)",
                          (selected_p, prog, note, photo_str, current_time))
                conn.commit()
                st.success("Daily update sent to HQ!")
    else:
        st.warning("මුලින්ම 'Project Registration' එකෙන් ප්‍රොජෙක්ට් එකක් ඇතුළත් කරන්න.")

# --- 3. HQ ADMIN DASHBOARD ---
elif page == "📊 HQ Admin Dashboard":
    st.header("🧐 HQ Central Monitoring Panel")
    
    # Login for HQ
    pw = st.sidebar.text_input("Admin Password", type="password")
    if pw == "stf123":
        # Data merge කරලා ගන්නවා
        query = '''
            SELECT p.name, p.location, p.cost, p.start_date, p.end_date, u.progress, u.status_note, u.photo, u.update_time
            FROM projects p
            LEFT JOIN daily_updates u ON p.name = u.project_name
            WHERE u.id = (SELECT MAX(id) FROM daily_updates WHERE project_name = p.name) OR u.id IS NULL
        '''
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            # සාරාංශය
            m1, m2, m3 = st.columns(3)
            m1.metric("Active Sites", len(df))
            m2.metric("Total Investment", f"LKR {df['cost'].sum():,.2f}")
            m3.metric("Avg. Progress", f"{int(df['progress'].fillna(0).mean())}%")
            
            st.divider()
            
            # දත්ත වගුව
            st.subheader("📋 Master Project List")
            st.dataframe(df.drop(columns=['photo']), use_container_width=True)
            
            # Excel Print
            csv = df.drop(columns=['photo']).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Print/Download Full Report (CSV)", csv, "STF_Master_Report.csv", "text/csv")
            
            st.divider()
            
            # ෆොටෝ බලන තැන
            st.subheader("🖼️ Site Visual Progress")
            for i, row in df.iterrows():
                with st.expander(f"Project: {row['name']} ({row['progress'] if row['progress'] else 0}%)"):
                    col_a, col_b = st.columns([1, 2])
                    with col_a:
                        if row['photo']:
                            st.image(base64.b64decode(row['photo']), use_container_width=True)
                        else:
                            st.write("No photo updated yet.")
                    with col_b:
                        st.write(f"**Location:** {row['location']}")
                        st.write(f"**Cost:** LKR {row
