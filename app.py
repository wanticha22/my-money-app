import streamlit as st
import sqlite3
import pandas as pd
import calendar
from datetime import datetime

# --- 1. ตกแต่ง UI ด้วย CSS สไตล์ Minimalist / Pastel ---
st.set_page_config(page_title="My Money Plan", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FAFAF7; }
    h1, h2, h3 { color: #6D7966; font-family: 'Helvetica Neue', sans-serif; font-weight: 400; }
    div[data-testid="stMetricValue"] { color: #809671; font-weight: bold; }
    .css-1d391kg { background-color: #F0F2EB; border-radius: 15px; padding: 20px; }
    div[data-testid="stExpander"] { background-color: #FFFFFF; border-radius: 10px; border: 1px solid #EBEBEB; }
    </style>
""", unsafe_allow_html=True)

# --- 2. สร้างและเชื่อมต่อ Database (SQLite) ---
conn = sqlite3.connect('money_plan.db', check_same_thread=False)
c = conn.cursor()

# สร้างตารางถ้ายังไม่มี
c.execute('''CREATE TABLE IF NOT EXISTS credit_cards (
                month_year TEXT PRIMARY KEY, ktc REAL, kbank REAL, central REAL, 
                firstchoice REAL, uob REAL, saved_for_pay REAL, others_debt REAL, net_cc_pay REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS monthly_plan (
                month_year TEXT PRIMARY KEY, salary REAL, condo REAL, electric REAL, 
                water REAL, internet REAL, sub REAL, support REAL, social REAL, 
                parent REAL, savings REAL, invest REAL, others REAL, cc_pay REAL)''')
conn.commit()

st.title("🌱 My Money Plan 2026")

# เลือกเดือน
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
selected_month = st.selectbox("เลือกเดือนที่ต้องการจัดการ", months)
year = 2026
month_idx = months.index(selected_month) + 1
days_in_month = calendar.monthrange(year, month_idx)[1]
month_id = f"{year}-{month_idx:02d}"

# จัดหน้าจอเป็น 2 แท็บ
tab1, tab2, tab3 = st.tabs(["📊 Dashboard & จัดการเงินเดือน", "💳 จัดการหนี้บัตรเครดิต", "🗄️ ดูข้อมูลใน Database"])

# --- TAB 2: จัดการหนี้บัตรเครดิต (ทำก่อนเพื่อส่งยอดไป Tab 1) ---
with tab2:
    st.subheader(f"ภาระบัตรเครดิตเดือน {selected_month} {year}")
    
    # ดึงข้อมูลเดิมมาแสดงถ้ามี
    c.execute("SELECT * FROM credit_cards WHERE month_year=?", (month_id,))
    cc_data = c.fetchone()
    cc_defaults = cc_data[1:] if cc_data else [0.0]*8

    with st.form("cc_form"):
        col1, col2 = st.columns(2)
        with col1:
            ktc = st.number_input("KTC", value=float(cc_defaults[0]))
            kbank = st.number_input("KBANK", value=float(cc_defaults[1]))
            central = st.number_input("CENTRAL", value=float(cc_defaults[2]))
            firstchoice = st.number_input("FIRSTCHOICE", value=float(cc_defaults[3]))
            uob = st.number_input("UOB", value=float(cc_defaults[4]))
        with col2:
            saved_for_pay = st.number_input("หัก: เงินที่โอนไปรอจ่ายแล้ว", value=float(cc_defaults[5]))
            others_debt = st.number_input("หัก: เงินที่รอคนอื่นโอนคืน", value=float(cc_defaults[6]))
        
        submit_cc = st.form_submit_button("บันทึกข้อมูลบัตรเครดิต")
        
        if submit_cc:
            sum_all = ktc + kbank + central + firstchoice + uob
            net_cc_pay = sum_all - saved_for_pay - others_debt
            
            c.execute('''INSERT OR REPLACE INTO credit_cards 
                         (month_year, ktc, kbank, central, firstchoice, uob, saved_for_pay, others_debt, net_cc_pay) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                      (month_id, ktc, kbank, central, firstchoice, uob, saved_for_pay, others_debt, net_cc_pay))
            conn.commit()
            st.success(f"บันทึกสำเร็จ! ยอดบัตรที่ต้องควักจ่ายจริงคือ: {net_cc_pay:,.2f} บาท")

# --- TAB 1: จัดการเงินเดือน & Dashboard ---
with tab1:
    # ดึงยอดบัตรเครดิตสุทธิมาเตรียมไว้
    c.execute("SELECT net_cc_pay FROM credit_cards WHERE month_year=?", (month_id,))
    cc_result = c.fetchone()
    current_cc_pay = cc_result[0] if cc_result else 0.0

    st.subheader(f"จัดสรรงบประมาณเดือน {selected_month} {year} (จำนวน {days_in_month} วัน)")
    
    # ดึงข้อมูลเดิม
    c.execute("SELECT * FROM monthly_plan WHERE month_year=?", (month_id,))
    mp_data = c.fetchone()
    mp_defaults = mp_data[1:] if mp_data else [0.0]*13

    with st.form("monthly_form"):
        salary = st.number_input("💰 เงินเดือนรับสุทธิ", value=float(mp_defaults[0]))
        
        st.markdown("**รายจ่ายคงที่ (Fix Costs)**")
        c1, c2, c3, c4 = st.columns(4)
        condo = c1.number_input("ค่าคอนโด", value=float(mp_defaults[1]))
        electric = c2.number_input("ค่าไฟ", value=float(mp_defaults[2]))
        water = c3.number_input("ค่าน้ำ", value=float(mp_defaults[3]))
        internet = c4.number_input("ค่าเน็ต", value=float(mp_defaults[4]))
        
        c1, c2, c3, c4 = st.columns(4)
        sub = c1.number_input("Subscription", value=float(mp_defaults[5]))
        support = c2.number_input("Support", value=float(mp_defaults[6]))
        social = c3.number_input("ประกันสังคม+เน็ต", value=float(mp_defaults[7]))
        parent = c4.number_input("ให้พ่อแม่", value=float(mp_defaults[8]))
        
        st.markdown("**การออมและลงทุน**")
        c1, c2, c3 = st.columns(3)
        savings = c1.number_input("เงินเก็บ", value=float(mp_defaults[9]))
        invest = c2.number_input("ลงทุน (DCA)", value=float(mp_defaults[10]))
        others = c3.number_input("อื่นๆ", value=float(mp_defaults[11]))
        
        # แสดงยอดบัตรเครดิตที่ดึงมา
        st.info(f"💳 ยอดบัตรเครดิตที่ดึงมาอัตโนมัติ: {current_cc_pay:,.2f} บาท")
        
        submit_mp = st.form_submit_button("คำนวณและบันทึกงบเดือนนี้")

        if submit_mp:
            c.execute('''INSERT OR REPLACE INTO monthly_plan 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                      (month_id, salary, condo, electric, water, internet, sub, support, social, parent, savings, invest, others, current_cc_pay))
            conn.commit()
            st.success("อัปเดตแผนการเงินเรียบร้อย!")

    # --- แสดงผล Dashboard อัตโนมัติ ---
    if submit_mp or mp_data:
        total_expenses = condo + electric + water + internet + sub + support + social + parent + savings + invest + others + current_cc_pay
        usable_money = salary - total_expenses
        daily_budget = usable_money / days_in_month
        make_transfer = electric + water + internet + sub + support + social + current_cc_pay
        kept_transfer = condo + savings + invest
        
        st.markdown("---")
        st.subheader("บทสรุปการเงิน (Executive Summary)")
        
        colA, colB, colC = st.columns(3)
        colA.metric("งบกินใช้รายวัน (บาท/วัน)", f"฿ {daily_budget:,.2f}")
        colB.metric("โอนไปจ่ายบิล (Make)", f"฿ {make_transfer:,.2f}")
        colC.metric("โอนไปเก็บ/สินทรัพย์ (Kept)", f"฿ {kept_transfer:,.2f}")
        
        st.write(f"*คำนวณจาก: เงินเหลือสุทธิ ฿ {usable_money:,.2f} หารด้วย {days_in_month} วัน")

# --- TAB 3: ดูข้อมูล Database ---
with tab3:
    st.write("ตารางงบรายเดือน")
    st.dataframe(pd.read_sql_query("SELECT * FROM monthly_plan", conn))
    st.write("ตารางบัตรเครดิต")
    st.dataframe(pd.read_sql_query("SELECT * FROM credit_cards", conn))