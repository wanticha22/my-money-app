import streamlit as st
import sqlite3
import pandas as pd
import calendar
from datetime import datetime

# --- 1. ตั้งค่า Theme, บังคับ Light Mode และปรับ Font Noto Sans Thai ---
st.set_page_config(page_title="My Money Plan", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* นำเข้า Font Noto Sans Thai */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600&display=swap');
    
    * {
        font-family: 'Noto Sans Thai', sans-serif !important;
    }
    
    /* บังคับ Light Mode ด้วยพื้นหลังสีโทนสว่างสบายตา (Soft Minimalist) */
    .stApp { 
        background-color: #FAFAF7 !important; 
        color: #4A4A4A !important;
    }
    
    /* ปรับแต่งส่วนหัวและ Card */
    h1, h2, h3, h4 { color: #5C6B50; font-weight: 500; }
    div[data-testid="stMetricValue"] { color: #7B8F68; font-weight: 600; }
    
    /* ปรับกรอบให้โค้งมน (Soft outlines) เหมือนแอปในมือถือ */
    .css-1d391kg, div[data-testid="stForm"], div.stDataFrame { 
        background-color: #FFFFFF; 
        border-radius: 16px; 
        padding: 24px; 
        border: 1px solid #EAEAEA;
        box-shadow: 0 4px 10px rgba(0,0,0,0.02);
    }
    
    /* แต่ง Tab ให้สวยงามและเด่นชัด */
    button[data-baseweb="tab"] { font-size: 16px; color: #9E9E9E; }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #5C6B50;
        border-bottom: 2px solid #5C6B50;
    }
    
    /* ซ่อนแถบเมนูขวาบนที่ไม่จำเป็นของ Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. Database Setup ---
conn = sqlite3.connect('money_plan.db', check_same_thread=False)
c = conn.cursor()

# สร้างตาราง Transaction บัตรเครดิต (ใหม่)
c.execute('''CREATE TABLE IF NOT EXISTS cc_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_year TEXT,
                date_time TEXT,
                card_name TEXT,
                txn_type TEXT,
                amount REAL,
                note TEXT
            )''')

# สร้างตารางแผนการเงิน
c.execute('''CREATE TABLE IF NOT EXISTS monthly_plan (
                month_year TEXT PRIMARY KEY, salary REAL, condo REAL, electric REAL, 
                water REAL, internet REAL, sub REAL, support REAL, social REAL, 
                parent REAL, savings REAL, invest REAL, others REAL)''')
conn.commit()

st.markdown("## 🌱 My Money Plan 2026")

# เลือกเดือน
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
selected_month = st.selectbox("📅 เลือกเดือนที่ต้องการจัดการ", months)
year = 2026
month_idx = months.index(selected_month) + 1
days_in_month = calendar.monthrange(year, month_idx)[1]
month_id = f"{year}-{month_idx:02d}"

# --- จัดลำดับ Tab ใหม่ตาม Requirement ---
tab1, tab2, tab3 = st.tabs(["💳 จัดการหนี้บัตรเครดิต", "🪴 Dashboard & งบเดือน", "🗄️ Database"])

# ==========================================
# TAB 1: 💳 บันทึกรายการบัตรเครดิต (Transaction-based)
# ==========================================
with tab1:
    st.markdown("#### บันทึกรายการใช้จ่ายผ่านบัตรเครดิต (ราย Transaction)")
    
    with st.form("cc_txn_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            card_name = st.selectbox("เลือกบัตรเครดิต", ["KTC", "KBANK", "CENTRAL", "FIRSTCHOICE", "UOB"])
            txn_type = st.selectbox("ประเภทรายการ", ["รูดใช้เอง", "คนอื่นฝากรูด", "โอนเงินไปรอจ่ายแล้ว"])
        with col2:
            amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=100.0)
            note = st.text_input("บันทึกช่วยจำ (Note)", placeholder="เช่น กินข้าว, A ฝากซื้อของ, โอนเข้า Kept ไว้จ่ายบัตร")
            
        submit_txn = st.form_submit_button("บันทึก Transaction")
        
        if submit_txn and amount > 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("INSERT INTO cc_transactions (month_year, date_time, card_name, txn_type, amount, note) VALUES (?, ?, ?, ?, ?, ?)", 
                      (month_id, now, card_name, txn_type, amount, note))
            conn.commit()
            st.success("✔️ บันทึกรายการสำเร็จ!")
            
    # แสดงรายการ Transaction ของเดือนนี้
    st.markdown("---")
    st.markdown(f"**ประวัติการใช้บัตรเครดิต ประจำเดือน {selected_month}**")
    df_txns = pd.read_sql_query(f"SELECT date_time as 'วัน-เวลา', card_name as 'บัตร', txn_type as 'ประเภท', amount as 'ยอดเงิน', note as 'บันทึก' FROM cc_transactions WHERE month_year='{month_id}' ORDER BY id DESC", conn)
    
    if not df_txns.empty:
        # ตกแต่ง DataFrame
        st.dataframe(df_txns, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีรายการในเดือนนี้")

# ==========================================
# คำนวณยอดบัตรเครดิตอัตโนมัติ สำหรับดึงไป Tab 2
# ==========================================
c.execute("SELECT txn_type, SUM(amount) FROM cc_transactions WHERE month_year=? GROUP BY txn_type", (month_id,))
txn_summaries = dict(c.fetchall())
self_spend = txn_summaries.get("รูดใช้เอง", 0.0)
others_spend = txn_summaries.get("คนอื่นฝากรูด", 0.0)
saved_pay = txn_summaries.get("โอนเงินไปรอจ่ายแล้ว", 0.0)

# หนี้บัตรที่ต้องควักกระเป๋าจ่ายจริง = ยอดที่รูดใช้เอง - ยอดที่โอนไปเก็บรอจ่ายแล้ว
net_cc_pay = self_spend - saved_pay
if net_cc_pay < 0: 
    net_cc_pay = 0

# ==========================================
# TAB 2: 📊 Dashboard & จัดการเงินเดือน
# ==========================================
with tab2:
    st.markdown(f"#### จัดสรรงบประมาณเดือน {selected_month} {year}")
    
    c.execute("SELECT * FROM monthly_plan WHERE month_year=?", (month_id,))
    mp_data = c.fetchone()
    mp_defaults = mp_data[1:] if mp_data else [0.0]*12

    with st.form("monthly_form"):
        salary = st.number_input("💰 เงินเดือนรับสุทธิ", value=float(mp_defaults[0]), step=1000.0)
        
        st.markdown("**รายจ่ายคงที่ (Fix Costs)**")
        c1, c2, c3, c4 = st.columns(4)
        condo = c1.number_input("ค่าคอนโด", value=float(mp_defaults[1]), step=100.0)
        electric = c2.number_input("ค่าไฟ", value=float(mp_defaults[2]), step=100.0)
        water = c3.number_input("ค่าน้ำ", value=float(mp_defaults[3]), step=100.0)
        internet = c4.number_input("ค่าเน็ต", value=float(mp_defaults[4]), step=100.0)
        
        c1, c2, c3, c4 = st.columns(4)
        sub = c1.number_input("Subscription", value=float(mp_defaults[5]), step=100.0)
        support = c2.number_input("Support", value=float(mp_defaults[6]), step=100.0)
        social = c3.number_input("ประกันสังคม+เน็ต", value=float(mp_defaults[7]), step=100.0)
        parent = c4.number_input("ให้พ่อแม่", value=float(mp_defaults[8]), step=100.0)
        
        st.markdown("**การออมและลงทุน**")
        c1, c2, c3 = st.columns(3)
        savings = c1.number_input("เงินเก็บ", value=float(mp_defaults[9]), step=1000.0)
        invest = c2.number_input("ลงทุน", value=float(mp_defaults[10]), step=1000.0)
        others = c3.number_input("อื่นๆ", value=float(mp_defaults[11]), step=100.0)
        
        # แสดงยอดหนี้ที่คำนวณมาจาก Tab 1 ให้เห็นแบบสดๆ
        st.info(f"💳 หนี้บัตรที่ต้องกันเงินไว้จ่าย: **฿ {net_cc_pay:,.2f}** \n(คำนวณจาก: รูดใช้เอง ฿{self_spend:,.0f} หักลบกับที่ โอนรอจ่ายไปแล้ว ฿{saved_pay:,.0f})")
        
        submit_mp = st.form_submit_button("คำนวณและอัปเดตแผนเงินเดือน")

        if submit_mp:
            c.execute('''INSERT OR REPLACE INTO monthly_plan 
                         (month_year, salary, condo, electric, water, internet, sub, support, social, parent, savings, invest, others)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                      (month_id, salary, condo, electric, water, internet, sub, support, social, parent, savings, invest, others))
            conn.commit()
            st.success("✔️ อัปเดตข้อมูลเรียบร้อย!")

    # --- Dashboard สรุปผล ---
    total_expenses = condo + electric + water + internet + sub + support + social + parent + savings + invest + others + net_cc_pay
    usable_money = salary - total_expenses
    daily_budget = usable_money / days_in_month if days_in_month else 0
    make_transfer = electric + water + internet + sub + support + social + net_cc_pay
    kept_transfer = condo + savings + invest
    
    st.markdown("---")
    st.markdown("### 📊 บทสรุปภาพรวม (Dashboard)")
    
    colA, colB, colC = st.columns(3)
    colA.metric("☕ งบกินใช้รายวัน (บาท/วัน)", f"฿ {daily_budget:,.2f}")
    colB.metric("📱 โอนไปจ่ายบิล (Make)", f"฿ {make_transfer:,.2f}")
    colC.metric("🏦 โอนไปเก็บ/สินทรัพย์ (Kept)", f"฿ {kept_transfer:,.2f}")
    
    st.caption(f"💡 วิธีคิดงบรายวัน: เงินเหลือสุทธิ ฿ {usable_money:,.2f} ÷ {days_in_month} วัน")

# ==========================================
# TAB 3: 🗄️ ดูข้อมูล Database
# ==========================================
with tab3:
    st.markdown("#### ตารางฐานข้อมูล Transaction บัตรเครดิต")
    st.dataframe(pd.read_sql_query("SELECT * FROM cc_transactions", conn), use_container_width=True)
    st.markdown("#### ตารางฐานข้อมูล แผนการเงิน")
    st.dataframe(pd.read_sql_query("SELECT * FROM monthly_plan", conn), use_container_width=True)
