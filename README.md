# water-tracker-streamlit

# 🚰 Water Usage Tracker

A simple program to track water usage per tenant/user, calculate total consumption, and compute water cost using MySQL as the database.

---

## 📦 Features

- 🔍 Track hot and cold water usage per tenant
- 💰 Calculate total water cost based on usage and rates
- 📊 View consumption history
- 🧮 Realtime updates and analytics
- 💾 MySQL-powered persistent storage

---

## 🛠️ Tech Stack

- ✅ Python (Streamlit / Flask / Discord Bot)
- ✅ MySQL
- ✅ SQLAlchemy / mysql-connector-python (optional)
- ✅ Railway / PlanetScale / local MySQL (DB hosting)

---

## 📐 Database Schema

### Table: `tenants`

| Column        | Type     | Description                |
|---------------|----------|----------------------------|
| `id`          | INT PK   | Tenant ID                  |
| `name`        | VARCHAR  | Tenant's name              |
| `rate`        | FLOAT    | Cost in paise per litre    |

### Table: `water_usage`

| Column         | Type     | Description                          |
|----------------|----------|--------------------------------------|
| `id`           | INT PK   | Record ID                            |
| `tenant_id`    | INT FK   | Linked to `tenants(id)`              |
| `date`         | DATE     | Usage date                           |
| `hot_water_l`  | FLOAT    | Hot water used (litres)              |
| `cold_water_l` | FLOAT    | Cold water used (litres)             |
| `total_cost`   | FLOAT    | Cost = (hot + cold) × rate           |

---
