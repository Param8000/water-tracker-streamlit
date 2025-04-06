from datetime import datetime, date
from decimal import Decimal
import mysql.connector
import streamlit as st
st.set_page_config(layout="wide")  # ✅ FIRST command


# 📦 Cached DB connection

@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host="db4free.net",
        user="param8000",
        password="12345678",
        database="tenantdb",
        port=3306
    )


def get_cursor():
    conn = get_connection()
    try:
        conn.ping(reconnect=True, attempts=3, delay=2)
    except mysql.connector.errors.OperationalError:
        st.error("❌ Lost connection to the database. Please restart the app.")
        st.stop()
    return conn, conn.cursor(dictionary=True)


conn, cur = get_cursor()

# 📦 Cached active tenants


@st.cache_data(ttl=300)
def get_active_tenants():
    conn, cur = get_cursor()
    cur.execute("SELECT Name FROM Tenants WHERE Status = 'Active'")
    return [row["Name"] for row in cur.fetchall()]


st.title("😀 Water Usage Entry System")

# 👤 Tenant dropdown
tenant_names = get_active_tenants()
name = st.selectbox("👤 Select Tenant", tenant_names)

# 🗕️ Date selector
try:
    today = date.today()
except Exception as e:
    st.error("❌ Unable to access system date. Please check your system clock.")
    st.stop()

selected_date = st.date_input(
    "🗕️ Select a date in the desired month", value=today)
month = selected_date.strftime('%b-%y')
st.markdown(f"### 🗓️ Recording for: **{month}**")

# Get max recorded reading ever for this tenant
conn, cur = get_cursor()
cur.execute("""
    SELECT MAX(Hot_Water_Reading) AS Max_Hot, MAX(Cold_Water_Reading) AS Max_Cold
    FROM WaterUsageLog
    WHERE Name = %s
""", (name,))
max_record = cur.fetchone()

if max_record["Max_Hot"] is not None and max_record["Max_Cold"] is not None:
    latest_hot = Decimal(str(max_record["Max_Hot"]))
    latest_cold = Decimal(str(max_record["Max_Cold"]))
    st.info(
        f"📘 Highest Recorded Reading: 🔥 {latest_hot} L, ❄️ {latest_cold} L")
else:
    # No records found, use initial reading
    conn, cur = get_cursor()
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
        f"🆑 No logs found. Using initial readings: 🔥 {latest_hot} L, ❄️ {latest_cold} L")

# Layout columns for better distribution
col1, col2 = st.columns(2)

# 📘 Show last few records (optional)
with col1:
    st.markdown("---")
    if st.checkbox("📂 Show Previous Records"):
        st.subheader("📊 Previous Records")
        conn, cur = get_cursor()
        cur.execute("""
            SELECT Month, Hot_Water_Reading, Cold_Water_Reading
            FROM WaterUsageLog
            WHERE Name = %s
            ORDER BY STR_TO_DATE(CONCAT('01-', Month), '%d-%b-%y') DESC
        """, (name,))
        rows = cur.fetchall()
        if rows:
            for row in reversed(rows):
                st.write(
                    f"🗓️ {row['Month']} - 🔥 {row['Hot_Water_Reading']} L, ❄️ {row['Cold_Water_Reading']} L")
        else:
            st.write("⚠️ No previous records found.")

# 📜 Show full WaterUsageLog table
with col2:
    st.markdown("---")
    if st.checkbox("📋 Show Full WaterUsageLog Table"):
        conn, cur = get_cursor()
        cur.execute(
            "SELECT * FROM WaterUsageLog ORDER BY STR_TO_DATE(CONCAT('01-', Month), '%d-%b-%y')")
        full_table = cur.fetchall()
        if full_table:
            st.dataframe(full_table)
        else:
            st.write("⚠️ No records found in WaterUsageLog.")

# 🧾 Current readings (must always increase)
st.markdown("---")
col3, col4 = st.columns(2)
with col3:
    current_hot = st.number_input(
        "🔥 Current Hot Water Reading (L)",
        min_value=int(latest_hot),
        value=int(latest_hot),
        step=1,
        help="Cannot be less than the previous reading"
    )
with col4:
    current_cold = st.number_input(
        "❄️ Current Cold Water Reading (L)",
        min_value=int(latest_cold),
        value=int(latest_cold),
        step=1,
        help="Cannot be less than the previous reading"
    )

# 🧺 Calculate usage
hot_usage = Decimal(current_hot) - latest_hot
cold_usage = Decimal(current_cold) - latest_cold
total_usage = hot_usage + cold_usage

# 📦 Get tenant info
conn, cur = get_cursor()
cur.execute(
    "SELECT Rent, House, `Water_Paise_per_Litre` FROM Tenants WHERE Name = %s", (name,))
tenant = cur.fetchone()
if not tenant:
    st.error("❌ Tenant not found in database.")
    st.stop()

rent = Decimal(str(tenant["Rent"]))
house = tenant["House"]
water_rate = Decimal(str(tenant["Water_Paise_per_Litre"]))

# 💡 Show tenant info
st.info(
    f"📄 Water Rate: {water_rate} paise per litre, Water Usage: {total_usage} L")

# 💸 Calculate cost
water_cost_paise = total_usage * water_rate
water_cost_rupees = water_cost_paise
final_total = rent + water_cost_rupees

st.success(
    f"💰 Rent: ₹{rent}, 🚿 Water Cost: ₹{water_cost_rupees:.2f}, 🧾 Total: ₹{final_total:.2f}")

# 💾 Submit to DB
if st.button("💾 Submit"):
    conn, cur = get_cursor()
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
