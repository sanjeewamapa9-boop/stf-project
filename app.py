import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import plotly.express as px
from PIL import Image
import io

# --- Page Config & Theme ---
st.set_page_config(page_title="STF Construction Tracker", layout="wide")

# CSS - පෙනුම ලස්සන කිරීමට
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004b91; color: white; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    h1 { color: #004b91; font-family: 'Segoe UI'; border-bottom: 2px solid #004b91; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- Database ---
conn = sqlite3.connect('stf_pro.db', check_same_thread=False)
c = conn.cursor()

def create_tables():
    c.execute('''CREATE TABLE IF NOT EXISTS projects 
                 (id INTEGER PRIMARY KEY, camp_name TEXT, tender_no TEXT, total_budget REAL, img BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_progress 
                 (id INTEGER PRIMARY KEY, project_id INTEGER, update_date DATE, progress_pct INTEGER, remarks TEXT)''')
    conn.commit()

create_tables()

# --- Functions ---
def login():
    st.sidebar.title("🔐 Secure Login")
    user = st.sidebar.text_input("Username")
    pw = st.sidebar.text_input("Password", type="password")
    if user == "admin" and pw == "stf123":
        return True
    return False

# --- UI ---
st.title("🛡️ SRI LANKA POLICE - STF")
st.subheader("Construction Project Monitoring System (Pro)")

menu = ["🏠 මුල් පිටුව", "📝 අලුත් Project", "👷 ප්‍රගතිය සටහන් කිරීම", "📊 Dashboard (HQ Only)"]
choice = st.sidebar.selectbox("පියවර තෝරන්න", menu)

if choice == "🏠 මුල් පිටුව":
    st.image("https://upload.wikimedia.org/wikipedia/en/3/3a/Special_Task_Force_Logo.png", width=150)
    st.write("## සාදරයෙන් පිළිගනිමු!")
    st.info("මෙම පද්ධතිය මගින් STF ඉදිකිරීම් ව්‍යාපෘති වල ප්‍රගතිය මධ්‍යම මට්ටමින් අධීක්ෂණය කරනු ලබයි.")

elif choice == "📝 අලුත් Project":
    st.subheader("📝 නව ටෙන්ඩර් විස්තර ඇතුළත් කිරීම")
    col1, col2 = st.columns(2)
    with col1:
        camp = st.text_input("Camp එකේ නම")
        tender = st.text_input("ටෙන්ඩර් අංකය")
    with col2:
        budget = st.number_input("ඇස්තමේන්තුගත මුදල (Rs.)", min_value=0.0)
        uploaded_file = st.file_uploader("Site Photo එකක් තෝරන්න", type=['jpg', 'png', 'jpeg'])
    
    if st.button("ව්‍යාපෘතිය ඇතුළත් කරන්න"):
        img_byte = uploaded_file.read() if uploaded_file else None
        c.execute("INSERT INTO projects (camp_name, tender_no, total_budget, img) VALUES (?,?,?,?)", 
                  (camp, tender, budget, img_byte))
        conn.commit()
        st.success("✅ දත්ත සාර්ථකව ඇතුළත් විය!")

elif choice == "👷 ප්‍රගතිය සටහන් කිරීම":
    st.subheader("👷 දෛනික වැඩ අවසන් ප්‍රමාණය")
    projs = pd.read_sql_query("SELECT id, camp_name FROM projects", conn)
    if not projs.empty:
        p_dict = {row['camp_name']: row['id'] for _, row in projs.iterrows()}
        selected = st.selectbox("ව්‍යාපෘතිය", list(p_dict.keys()))
        pct = st.select_slider("අවසන් ප්‍රමාණය (%)", options=list(range(0, 101, 10)))
        rem = st.text_area("විශේෂ සටහන්")
        if st.button("Update Progress"):
            c.execute("INSERT INTO daily_progress (project_id, update_date, progress_pct, remarks) VALUES (?,?,?,?)", 
                      (p_dict[selected], date.today(), pct, rem))
            conn.commit()
            st.balloons()
            st.success("ප්‍රගතිය යාවත්කාලීන විය!")

elif choice == "📊 Dashboard (HQ Only)":
    if login():
        st.subheader("📊 HQ Centralized Monitoring Dashboard")
        df = pd.read_sql_query('''
            SELECT p.camp_name, p.tender_no, p.total_budget, d.progress_pct, d.update_date, p.img 
            FROM projects p LEFT JOIN daily_progress d ON p.id = d.project_id
        ''', conn)

        if not df.empty:
            latest = df.sort_values('update_date').groupby('camp_name').last().reset_index()
            
            # Chart
            fig = px.bar(latest, x='camp_name', y='progress_pct', color='progress_pct',
                         title="සෑම කඳවුරකම වර්තමාන වැඩ ප්‍රගතිය", 
                         color_continuous_scale='Blues', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show Data with Image
            for _, row in latest.iterrows():
                with st.expander(f"🔍 {row['camp_name']} - {row['tender_no']}"):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if row['img']:
                            st.image(row['img'], caption="Current Site Status", use_container_width=True)
                        else:
                            st.write("No Image Uploaded")
                    with c2:
                        st.metric("Progress", f"{row['progress_pct']}%")
                        st.write(f"Budget: Rs. {row['total_budget']:,.2f}")
                        st.write(f"Last Updated: {row['update_date']}")
            
            st.download_button("Excel වාර්තාව ලබාගන්න", df.to_csv().encode('utf-8'), "STF_Report.csv", "text/csv")
    else:
        st.error("කරුණාකර නිවැරදි Username සහ Password ඇතුළත් කරන්න.")