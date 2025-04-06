import streamlit as st
import mysql.connector
from decimal import Decimal
from datetime import datetime

# DB connection
conn = mysql.connector.connect(
    host="db4free.net",
    user="param8000",
    password="12345678",
    database="tenantdb",
    port=3306
)
cur = conn.cursor(dictionary=True)

st.set_page_config(layout="wide")

st.title("🚰 Water Usage Entry System")

# 👤 Tenant dropdown
cur.execute("SELECT Name FROM Tenants WHERE Status = 'Active'")
tenant_names = [row["Name"] for row in cur.fetchall()]
name = st.selectbox("👤 Select Tenant", tenant_names)

# 📅 Date selector
selected_date = st.date_input(
    "📅 Select a date in the desired month", value=datetime.today())
month = selected_date.strftime('%b-%y')
st.markdown(f"### 🗓️ Recording for: **{month}**")

# Get most recent record for this tenant
cur.execute("""
    SELECT Month, Hot_Water_Reading, Cold_Water_Reading
    FROM WaterUsageLog
    WHERE Name = %s
    ORDER BY STR_TO_DATE(Month, '%%b-%%y') DESC
    LIMIT 1
""", (name,))
latest = cur.fetchone()

if latest:
    latest_hot = Decimal(str(latest["Hot_Water_Reading"]))
    latest_cold = Decimal(str(latest["Cold_Water_Reading"]))
    latest_month = latest["Month"]
    st.info(
        f"📘 Latest Recorded Reading ({latest_month}): 🔥 {latest_hot} L, ❄️ {latest_cold} L")
else:
    cur.execute("""
        SELECT Initial_Hot_Water_Reading, Initial_Cold_Water_Reading
        FROM Tenants WHERE Name = %s
    """, (name,))
    initial = cur.fetchone()
    if not initial:
        st.error("❌ Tenant not found.")
        st.stop()
    latest_hot = Decimal(str(initial["Initial_Hot_Water_Reading"]))
    latest_cold = Decimal(str(initial["Initial_Cold_Water_Reading"]))
    st.info(
        f"🆕 No logs found. Using initial readings: 🔥 {latest_hot} L, ❄️ {latest_cold} L")

# Layout columns for better distribution
col1, col2 = st.columns(2)

# 📘 Show last few records (optional)
with col1:
    st.markdown("---")
    if st.checkbox("📂 Show Previous Records"):
        st.subheader("📊 Previous Records")
        cur.execute("""
            SELECT Month, Hot_Water_Reading, Cold_Water_Reading
            FROM WaterUsageLog
            WHERE Name = %s
            ORDER BY STR_TO_DATE(Month, '%%b-%%y')
            LIMIT 3
        """, (name,))
        rows = cur.fetchall()
        if rows:
            for row in rows:
                st.write(
                    f"🗓️ {row['Month']} - 🔥 {row['Hot_Water_Reading']} L, ❄️ {row['Cold_Water_Reading']} L")
        else:
            st.write("⚠️ No previous records found.")

# 📜 Show full WaterUsageLog table
with col2:
    st.markdown("---")
    if st.checkbox("📋 Show Full WaterUsageLog Table"):
        cur.execute(
            "SELECT * FROM WaterUsageLog ORDER BY STR_TO_DATE(Month, '%%b-%%y')")
        full_table = cur.fetchall()
        if full_table:
            st.dataframe(full_table)
        else:
            st.write("⚠️ No records found in WaterUsageLog.")

# 🧾 Current readings
st.markdown("---")
col3, col4 = st.columns(2)
with col3:
    current_hot = st.number_input(
        "🔥 Current Hot Water Reading (L)", min_value=int(latest_hot), value=int(latest_hot), step=1)
with col4:
    current_cold = st.number_input(
        "❄️ Current Cold Water Reading (L)", min_value=int(latest_cold), value=int(latest_cold), step=1)

# 🧮 Calculate usage
hot_usage = Decimal(current_hot) - latest_hot
cold_usage = Decimal(current_cold) - latest_cold
total_usage = hot_usage + cold_usage

# 📦 Get tenant info
cur.execute(
    "SELECT Rent, House, `Water Paise per Litre` FROM Tenants WHERE Name = %s", (name,))
tenant = cur.fetchone()
if not tenant:
    st.error("❌ Tenant not found in database.")
    st.stop()

rent = Decimal(str(tenant["Rent"]))
house = tenant["House"]
water_rate = Decimal(str(tenant["Water Paise per Litre"]))  # paise per litre

# 💸 Calculate cost
water_cost_paise = total_usage * water_rate
water_cost_rupees = water_cost_paise
final_total = rent + water_cost_rupees

st.success(
    f"💰 Rent: ₹{rent}, 🚿 Water Cost: ₹{water_cost_rupees:.2f}, 🧾 Total: ₹{final_total:.2f}")

# 💾 Submit to DB
if st.button("💾 Submit"):
    cur.execute(
        "SELECT * FROM WaterUsageLog WHERE Name = %s AND Month = %s", (name, month))
    if cur.fetchone():
        st.warning("⚠️ Record for this tenant and month already exists.")
    else:
        cur.execute("""
            INSERT INTO WaterUsageLog (
                Month, Name, Hot_Water_Reading, Cold_Water_Reading,
                Hot_Water_Usage, Cold_Water_Usage, Water_Cost,
                Rent, House, Total_Amount
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            str(month), str(name), int(current_hot), int(current_cold),
            float(hot_usage), float(cold_usage), float(water_cost_rupees),
            float(rent), str(house), float(final_total)
        ))
        conn.commit()
        st.success("✅ Record saved successfully!")

cur.close()
conn.close()
