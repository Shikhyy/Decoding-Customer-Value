-- ============================================================
-- segmentation_analysis.sql
-- Customer Segmentation & Analysis
-- Decoding Customer Value — D2C Fashion Brand
--
-- Run via: python3 src/run_queries.py
-- Dataset: cleaned_dataset (loaded from data/cleaned_dataset.csv)
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- Q1: LOYALTY VS DISCOUNT DEPENDENCY
-- Who are genuinely loyal customers vs bargain hunters?
-- Segments customers by proven loyalty (chosen_loyalty_flag)
-- and promo reliance, revealing if promo spend is building
-- lasting value or just buying temporary transactions.
-- ────────────────────────────────────────────────────────────
SELECT
    CASE WHEN chosen_loyalty_flag = 1 THEN 'Loyal' ELSE 'Non-Loyal' END     AS loyalty_segment,
    CASE
        WHEN dependency_score = 1.0 THEN 'High — Both Discount + Promo'
        WHEN dependency_score = 0.5 THEN 'Medium — One Incentive Only'
        ELSE                              'Low — No Incentives Used'
    END                                                                       AS promo_reliance,
    COUNT(*)                                                                  AS customer_count,
    ROUND(AVG("Purchase Amount (USD)"), 2)                                   AS avg_spend_usd,
    ROUND(AVG("Previous Purchases"), 1)                                       AS avg_previous_purchases,
    ROUND(AVG(satisfaction_flag) * 100, 1)                                   AS pct_satisfied
FROM cleaned_dataset
GROUP BY 1, 2
ORDER BY loyalty_segment DESC, avg_spend_usd DESC;


-- ────────────────────────────────────────────────────────────
-- Q2: BEHAVIORAL PATTERNS PREDICTING HIGH VALUE
-- What combination of frequency, satisfaction, and tenure
-- is most associated with being in the High value tier?
-- ────────────────────────────────────────────────────────────
SELECT
    "Frequency of Purchases"                                                  AS purchase_frequency,
    CASE
        WHEN "Previous Purchases" >= 38 THEN 'High Tenure (38+)'
        WHEN "Previous Purchases" >= 20 THEN 'Mid Tenure (20–37)'
        ELSE                                 'Low Tenure (<20)'
    END                                                                       AS tenure_band,
    COUNT(*)                                                                  AS customer_count,
    ROUND(AVG("Purchase Amount (USD)"), 2)                                   AS avg_spend_usd,
    ROUND(SUM(CASE WHEN value_tier = 'High' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                                              AS pct_high_value,
    ROUND(AVG(satisfaction_flag) * 100, 1)                                   AS pct_satisfied
FROM cleaned_dataset
GROUP BY 1, 2
HAVING COUNT(*) > 30
ORDER BY pct_high_value DESC, avg_spend_usd DESC;


-- ────────────────────────────────────────────────────────────
-- Q3: GEOGRAPHIC OPPORTUNITY MAP
-- Which states signal organic demand (high spend, low promo
-- dependency) vs discount-driven volume (high spend, high promo)?
-- These are the whitespace markets for targeted brand expansion.
-- ────────────────────────────────────────────────────────────
SELECT
    Location                                                                   AS state,
    COUNT(*)                                                                   AS customer_count,
    ROUND(AVG("Purchase Amount (USD)"), 2)                                    AS avg_spend_usd,
    ROUND(AVG(dependency_score), 3)                                            AS avg_promo_dependency,
    ROUND(AVG("Previous Purchases"), 1)                                        AS avg_tenure,
    ROUND(SUM(CASE WHEN value_tier = 'High' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                                               AS pct_high_value,
    CASE
        WHEN AVG(dependency_score) < 0.40 AND AVG("Purchase Amount (USD)") > 60
             THEN 'Organic Pull — Priority Expand'
        WHEN AVG(dependency_score) >= 0.50 AND AVG("Purchase Amount (USD)") > 60
             THEN 'Discount-Driven — Sunset Promos'
        ELSE 'Monitor'
    END                                                                        AS market_signal
FROM cleaned_dataset
GROUP BY 1
ORDER BY avg_spend_usd DESC, avg_promo_dependency ASC
LIMIT 20;


-- ────────────────────────────────────────────────────────────
-- Q4: PROMOTIONAL RESTRUCTURING — SEGMENTS TO SUNSET
-- Which category × season combos show high promo dependency
-- AND high concentration of low-value customers?
-- These are the prime targets for the discount sunset plan.
-- ────────────────────────────────────────────────────────────
SELECT
    Category                                                                   AS category,
    Season                                                                     AS season,
    COUNT(*)                                                                   AS customer_count,
    ROUND(AVG(dependency_score), 3)                                            AS avg_promo_dependency,
    ROUND(SUM(CASE WHEN value_tier = 'Low'  THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                                               AS pct_low_value,
    ROUND(SUM(CASE WHEN value_tier = 'High' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                                               AS pct_high_value,
    ROUND(AVG("Previous Purchases"), 1)                                        AS avg_tenure,
    ROUND(AVG("Purchase Amount (USD)"), 2)                                     AS avg_spend_usd
FROM cleaned_dataset
GROUP BY 1, 2
HAVING avg_promo_dependency >= 0.45 AND pct_low_value >= 28.0
ORDER BY pct_low_value DESC, avg_promo_dependency DESC;


-- ────────────────────────────────────────────────────────────
-- Q5: IDEAL CUSTOMER PROFILE (ICP)
-- Full demographic and behavioral breakdown of High-value
-- customers to define a precise acquisition target.
-- ────────────────────────────────────────────────────────────
SELECT
    Gender                                                                     AS gender,
    age_group,
    Category                                                                   AS preferred_category,
    "Payment Method"                                                           AS preferred_payment,
    COUNT(*)                                                                   AS customer_count,
    ROUND(AVG("Purchase Amount (USD)"), 2)                                    AS avg_spend_usd,
    ROUND(AVG("Previous Purchases"), 1)                                        AS avg_tenure,
    ROUND(AVG(dependency_score), 3)                                            AS avg_promo_dependency,
    ROUND(AVG(satisfaction_flag) * 100, 1)                                    AS pct_satisfied
FROM cleaned_dataset
WHERE value_tier = 'High'
GROUP BY 1, 2, 3, 4
ORDER BY customer_count DESC
LIMIT 10;


-- ────────────────────────────────────────────────────────────
-- Q6: CATEGORY FUNNEL — ENTRY VS RETENTION CATEGORIES
-- Accessories = Retention anchor (highest avg tenure).
-- Outerwear   = Entry point (lowest avg tenure).
-- This informs where to acquire vs where to cross-sell.
-- ────────────────────────────────────────────────────────────
SELECT
    Category                                                                   AS category,
    COUNT(*)                                                                   AS total_transactions,
    ROUND(AVG("Previous Purchases"), 2)                                        AS avg_tenure,
    ROUND(AVG("Purchase Amount (USD)"), 2)                                     AS avg_spend_usd,
    ROUND(AVG(dependency_score), 3)                                            AS avg_promo_dependency,
    ROUND(SUM(CASE WHEN value_tier = 'High' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                                               AS pct_high_value,
    CASE
        WHEN AVG("Previous Purchases") >= 25.5 THEN 'Retention Anchor'
        ELSE                                        'Acquisition / Entry Point'
    END                                                                        AS funnel_role
FROM cleaned_dataset
GROUP BY 1
ORDER BY avg_tenure DESC;
