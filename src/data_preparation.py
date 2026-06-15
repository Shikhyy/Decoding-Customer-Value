"""
data_preparation.py
--------------------
Data Preparation & Feature Engineering for the Decoding Customer Value project.
Cleans raw transactional data and engineers customer-level metrics for segmentation.

Engineered Features:
    - dependency_score   : Measures how reliant a customer is on discounts/promos (0 = none, 1 = always)
    - satisfaction_flag  : Binary flag for high satisfaction (Review Rating >= 4.0)
    - value_tier         : Composite customer value ranking (High / Medium / Low)
    - loyalty_volume     : Loyalty Definition A — Volume-based (Top 25% by purchase history)
    - loyalty_frequency  : Loyalty Definition B — Frequency + satisfaction combined
    - chosen_loyalty_flag: The validated, chosen loyalty metric for downstream analysis
    - freq_numeric       : Numeric purchase frequency (visits per year)
    - age_group          : Customer cohort label by age band

Author: Shikhar and Shreya
"""

import pandas as pd
import numpy as np
import os


# ── Frequency → annual visits mapping ────────────────────────────────────────
FREQ_MAP = {
    "Weekly": 52,
    "Bi-Weekly": 26,
    "Fortnightly": 26,
    "Monthly": 12,
    "Every 3 Months": 4,
    "Quarterly": 4,
    "Annually": 1,
}


def load_data(input_path: str) -> pd.DataFrame:
    """Load raw CSV and perform basic validation."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Dataset not found at: {input_path}")
    df = pd.read_csv(input_path)
    expected_cols = {
        "Customer ID", "Age", "Gender", "Category", "Purchase Amount (USD)",
        "Location", "Season", "Review Rating", "Subscription Status",
        "Discount Applied", "Promo Code Used", "Previous Purchases",
        "Payment Method", "Frequency of Purchases",
    }
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")
    print(f"[load]  Loaded {len(df):,} rows × {len(df.columns)} columns.")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing values with domain-appropriate defaults."""
    # Review Rating — impute with median (data is close to normal; mean ≈ median)
    before = df["Review Rating"].isna().sum()
    median_rating = df["Review Rating"].median()
    df["Review Rating"] = df["Review Rating"].fillna(median_rating)
    print(f"[clean] Imputed {before} missing 'Review Rating' values with median ({median_rating:.1f}).")
    return df


def engineer_dependency_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Promo Dependency Score (0 – 1).

    Logic: Both 'Discount Applied' and 'Promo Code Used' capture whether
    a purchase was facilitated by an incentive. Averaging them gives a score
    that represents the degree to which a customer relies on promotions:
        0.0  → no incentives used  (organic buyer)
        0.5  → partial promo usage (one of two applied)
        1.0  → full promo reliance (both discount + promo applied)

    Business use: Segments with high avg dependency are likely bargain hunters
    rather than intrinsically motivated buyers.
    """
    df["dependency_score"] = (
        df["Discount Applied"].map({"Yes": 1, "No": 0})
        + df["Promo Code Used"].map({"Yes": 1, "No": 0})
    ) / 2.0
    return df


def engineer_satisfaction_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Satisfaction Flag (0 / 1).

    A rating ≥ 4.0 on a 5-point scale is treated as 'satisfied'.
    This threshold is consistent with standard NPS/CSAT practices where
    4–5 is 'promoter territory'.
    """
    df["satisfaction_flag"] = (df["Review Rating"] >= 4.0).astype(int)
    return df


def engineer_freq_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Map purchase frequency label → annual purchase count."""
    df["freq_numeric"] = df["Frequency of Purchases"].map(FREQ_MAP)
    return df


def engineer_value_tier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Value Tier (High / Medium / Low).

    Composite score formula (weights chosen to reflect business priorities):
        40% × previous_purchases_rank   — historical tenure is the strongest LTV proxy
        40% × frequency_rank            — high frequency = high engagement
        20% × spend_rank                — single-transaction spend matters least (wide range but low signal)

    Tier boundaries:
        High   : Top 25%  (composite ≥ 0.75)
        Medium : Middle   (0.40 ≤ composite < 0.75)
        Low    : Bottom   (composite < 0.40)
    """
    df["_vol_rank"] = df["Previous Purchases"].rank(pct=True)
    df["_spend_rank"] = df["Purchase Amount (USD)"].rank(pct=True)
    df["_freq_rank"] = df["freq_numeric"].rank(pct=True)

    df["composite_value_score"] = (
        df["_vol_rank"] * 0.40
        + df["_freq_rank"] * 0.40
        + df["_spend_rank"] * 0.20
    )

    def _assign_tier(score: float) -> str:
        if score >= 0.75:
            return "High"
        elif score >= 0.40:
            return "Medium"
        return "Low"

    df["value_tier"] = df["composite_value_score"].apply(_assign_tier)
    df.drop(columns=["_vol_rank", "_spend_rank", "_freq_rank"], inplace=True)
    return df


def engineer_loyalty_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Two Competing Loyalty Definitions.

    Definition A — Volume-Based Loyalty (chosen):
        Customers in the top quartile of 'Previous Purchases' (≥ 38).
        Rationale: Historical purchase volume is the most direct measure of
        proven loyalty. It captures customers who repeatedly returned without
        being induced to do so in this specific transaction.

    Definition B — Frequency + Satisfaction Loyalty:
        Customers who buy at least bi-weekly AND have a high satisfaction rating.
        Rationale: High frequency + satisfaction suggests an engaged, happy buyer
        who is likely to continue. However, this is a more aspirational measure
        that mixes intention with behaviour.

    Validation:
        Both are correlated with 'Purchase Amount (USD)'. The one with higher
        correlation and better internal consistency is selected as the primary flag.
    """
    vol_threshold = df["Previous Purchases"].quantile(0.75)  # dynamic, not hardcoded
    df["loyalty_volume"] = (df["Previous Purchases"] >= vol_threshold).astype(int)
    df["loyalty_frequency"] = (
        (df["freq_numeric"] >= 26) & (df["satisfaction_flag"] == 1)
    ).astype(int)

    corr_vol = df["loyalty_volume"].corr(df["Purchase Amount (USD)"])
    corr_freq = df["loyalty_frequency"].corr(df["Purchase Amount (USD)"])

    print(f"[loyalty] Volume-Based correlation with spend: {corr_vol:+.4f}")
    print(f"[loyalty] Frequency-Based correlation with spend: {corr_freq:+.4f}")
    print(
        f"[loyalty] → Choosing: {'Volume-Based' if abs(corr_vol) >= abs(corr_freq) else 'Frequency-Based'}"
    )

    # Choose based on higher absolute correlation
    df["chosen_loyalty_flag"] = (
        df["loyalty_volume"] if abs(corr_vol) >= abs(corr_freq) else df["loyalty_frequency"]
    )
    return df


def engineer_age_group(df: pd.DataFrame) -> pd.DataFrame:
    """Segment customers into generational cohorts."""
    bins = [0, 24, 35, 50, 120]
    labels = ["Gen Z (18–24)", "Millennials (25–35)", "Gen X (36–50)", "Boomers (51+)"]
    df["age_group"] = pd.cut(df["Age"], bins=bins, labels=labels, right=True)
    return df


def prepare_data(
    input_path: str = "data/Dataset.csv",
    output_path: str = "data/cleaned_dataset.csv",
) -> pd.DataFrame:
    """Full pipeline: load → clean → engineer → save."""
    df = load_data(input_path)
    df = handle_missing_values(df)
    df = engineer_dependency_score(df)
    df = engineer_satisfaction_flag(df)
    df = engineer_freq_numeric(df)
    df = engineer_value_tier(df)
    df = engineer_loyalty_flags(df)
    df = engineer_age_group(df)

    df.to_csv(output_path, index=False)
    print(f"\n[done]  Cleaned dataset saved → {output_path}")
    print(f"        Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"\nValue Tier distribution:\n{df['value_tier'].value_counts()}")
    print(f"\nChosen Loyalty distribution:\n{df['chosen_loyalty_flag'].value_counts()}")
    return df


if __name__ == "__main__":
    prepare_data()
