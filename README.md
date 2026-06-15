# Decoding Customer Value
### A SQL-Driven Customer Intelligence & Retention Strategy

> A complete end-to-end analytical project for a D2C fashion brand — from raw transactional data to a boardroom-ready retention playbook.

---

## Project Overview

A direct-to-consumer fashion brand selling Clothing, Accessories, Footwear, and Outerwear across the US has never built a structured way to understand its ~3,900 customers. This project answers five core strategic questions:

1. **Who are genuinely loyal customers vs bargain hunters?**
2. **What behavioural patterns today predict high customer value over time?**
3. **Which geographies are underlevered — organic demand vs discount-driven?**
4. **How should the brand restructure its promotional programme?**
5. **What does the ideal customer profile (ICP) look like?**

---

## Repository Structure

```
Decoding-Customer-Value/
├── data/
│   ├── Dataset.csv               # Raw dataset (3,900 customers × 18 columns)
│   └── cleaned_dataset.csv       # Engineered output from data_preparation.py
│
├── sql/
│   └── segmentation_analysis.sql # 6 SQL queries answering all business questions
│
├── src/
│   ├── data_preparation.py       # Data cleaning + feature engineering pipeline
│   ├── run_queries.py            # Execute SQL against cleaned data via DuckDB
│   ├── dashboard.py              # Generate interactive 6-panel HTML dashboard
│   ├── generate_ppt_report.py    # Generate professional PowerPoint (.pptx) report
│
├── reports/
│   ├── dashboard.html            # Interactive Plotly dashboard (open in browser)
│   └── customer_intelligence_presentation.pptx  # 8-slide PowerPoint report
│
└── README.md
```

---

## Deliverables

| # | Deliverable | File |
|---|-------------|------|
| 1 | Cleaned Dataset + Engineered Features | `data/cleaned_dataset.csv` |
| 2 | SQL Segmentation Queries | `sql/segmentation_analysis.sql` |
| 3 | Interactive 6-Panel Dashboard | `reports/dashboard.html` |
| 4 | Customer Intelligence PPT Report | `reports/customer_intelligence_presentation.pptx` |

---

## Engineered Features

| Feature | Logic | Purpose |
|---------|-------|---------|
| `dependency_score` | (Discount + Promo) ÷ 2 | Measures promo reliance (0 = organic, 1 = fully incentivised) |
| `satisfaction_flag` | Rating ≥ 4.0 → 1 | Binary high-satisfaction signal |
| `freq_numeric` | Frequency label → annual count | Normalises purchase frequency |
| `value_tier` | 40% tenure + 40% freq + 20% spend | Composite High / Medium / Low tier |
| `loyalty_volume` | Top 25% by purchase history (≥38) | Validated loyalty definition (Definition A) |
| `loyalty_frequency` | High freq + satisfied | Competing loyalty definition (Definition B) |
| `age_group` | Age bins → Gen Z / Millennial / Gen X / Boomer | Generational cohort label |

**Chosen Loyalty Definition:** Volume-Based (`loyalty_volume`) — validated by higher positive correlation with purchase amount (+0.0142 vs −0.0116).

---

## Dashboard Panels

1. **Customer Value Pyramid** — Distribution of High / Medium / Low value tiers
2. **Promo Dependency vs Retention** — Avg purchase history by loyalty segment and promo tier
3. **Geographic Opportunity Map** — Spend vs promo dependency bubble chart (organic pull zones highlighted)
4. **Category Funnel** — Entry point vs retention anchor by average tenure
5. **ICP Demographics Heatmap** — Avg spend of High-Value customers by age group and gender
6. **Season × Category Risk Matrix** — Promo dependency heatmap identifying sunset candidates

---

## Key Findings

- **43%** of all purchases used a discount or promo code
- Loyal customers with **low promo reliance** spend more ($60.58) than high-promo buyers ($60.04)
- **Arizona, Virginia, Tennessee, Michigan** show organic demand (high spend + low promo dependency)
- **Summer Clothing, Summer Footwear, Fall Outerwear** are the three sunset-priority segments
- **ICP:** Male, Gen X / Boomer, purchasing Accessories weekly, averaging $76–$85/transaction

---

## How to Run

### 1. Install Dependencies
```bash
pip install pandas duckdb plotly reportlab
```

### 2. Run Data Preparation
```bash
python3 src/data_preparation.py
```

### 3. Run SQL Analysis
```bash
python3 src/run_queries.py
```

### 4. Generate Dashboard
```bash
python3 src/dashboard.py
# Open reports/dashboard.html in your browser
```

### 5. Generate PPT Report
```bash
python3 src/generate_ppt_report.py
# Output: reports/customer_intelligence_presentation.pptx
```

---

## Dataset

- **Source:** [Google Drive](https://drive.google.com/file/d/1aJUEgbqHj-Rp4KPh2TRe8MtSMcHZ8Lqk/view)
- **Size:** 3,900 rows × 18 columns
- **No PII:** Customer IDs are anonymised integers

---

*Decoding Customer Value · SQL Consulting Project · June 2025*
