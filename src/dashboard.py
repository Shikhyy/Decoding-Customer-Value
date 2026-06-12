"""
dashboard.py
-------------
Generates an interactive, premium-quality founder dashboard (dashboard.html)
with 6 panels covering the full analytical story:
    1. Customer Value Pyramid
    2. Promo Dependency vs Avg Tenure by Segment
    3. Geographic Opportunity Bubble Map
    4. Category Funnel (Entry vs Retention)
    5. ICP Demographics Heatmap
    6. Season × Category Risk Matrix

Designed for non-technical founders — clean, branded, print-ready.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


# ── Brand Palette ─────────────────────────────────────────────────────────────
COLORS = {
    "dark_bg": "#0D1117",
    "card_bg": "#161B22",
    "border":  "#30363D",
    "accent":  "#58A6FF",
    "green":   "#3FB950",
    "red":     "#F85149",
    "amber":   "#D29922",
    "purple":  "#BC8CFF",
    "text":    "#E6EDF3",
    "muted":   "#8B949E",
    "high":    "#3FB950",
    "medium":  "#D29922",
    "low":     "#F85149",
}

FONT = "Inter, system-ui, sans-serif"

# Plotly theme base
LAYOUT_BASE = dict(
    paper_bgcolor=COLORS["card_bg"],
    plot_bgcolor=COLORS["card_bg"],
    font=dict(family=FONT, color=COLORS["text"], size=12),
    margin=dict(l=32, r=32, t=60, b=32),
)


def build_pyramid(df: pd.DataFrame) -> go.Figure:
    """Panel 1: Customer Value Pyramid (Funnel chart)."""
    tier_order = ["High", "Medium", "Low"]
    tier_labels = {"High": "🏆 High Value", "Medium": "⚡ Medium Value", "Low": "📦 Low Value"}
    tier_colors = [COLORS["high"], COLORS["medium"], COLORS["low"]]

    counts = df["value_tier"].value_counts().reindex(tier_order)
    total = counts.sum()
    pcts = (counts / total * 100).round(1)

    fig = go.Figure(go.Funnel(
        y=[tier_labels[t] for t in tier_order],
        x=counts.values,
        textinfo="value+percent initial",
        textposition="inside",
        textfont=dict(size=14, color="white"),
        marker=dict(color=tier_colors),
        connector=dict(line=dict(color=COLORS["border"], width=2)),
        hovertemplate="<b>%{y}</b><br>Count: %{x:,}<br>Share: %{percentInitial:.1%}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="<b>Customer Value Pyramid</b><br><sup>Distribution across 3,900 customers</sup>",
                   font=dict(size=16), x=0.03),
    )
    return fig


def build_promo_retention(df: pd.DataFrame) -> go.Figure:
    """Panel 2: Promo Dependency vs Retention by Loyalty Segment."""
    df = df.copy()
    df["loyalty_label"] = df["chosen_loyalty_flag"].map({1: "Loyal", 0: "Non-Loyal"})
    df["promo_tier"] = df["dependency_score"].apply(
        lambda x: "High" if x == 1.0 else ("Medium" if x == 0.5 else "Low")
    )

    agg = (
        df.groupby(["loyalty_label", "promo_tier"])
        .agg(avg_tenure=("Previous Purchases", "mean"), count=("Customer ID", "count"))
        .reset_index()
    )

    fig = px.bar(
        agg,
        x="promo_tier",
        y="avg_tenure",
        color="loyalty_label",
        barmode="group",
        text=agg["avg_tenure"].round(1),
        color_discrete_map={"Loyal": COLORS["green"], "Non-Loyal": COLORS["red"]},
        category_orders={"promo_tier": ["Low", "Medium", "High"]},
        labels={"promo_tier": "Promo Dependency", "avg_tenure": "Avg Purchase History",
                "loyalty_label": "Loyalty Segment"},
    )
    fig.update_traces(texttemplate="%{text}", textposition="outside")
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="<b>Promo Dependency vs Retention Proxy</b><br><sup>Avg historical purchases by loyalty segment</sup>",
                   font=dict(size=16), x=0.03),
        legend=dict(bgcolor=COLORS["dark_bg"], bordercolor=COLORS["border"], borderwidth=1),
        xaxis=dict(gridcolor=COLORS["border"]),
        yaxis=dict(gridcolor=COLORS["border"]),
    )
    return fig


def build_geo_map(df: pd.DataFrame) -> go.Figure:
    """Panel 3: Geographic Opportunity Bubble Chart (Spend vs Promo Dependency)."""
    geo = (
        df.groupby("Location")
        .agg(
            avg_spend=("Purchase Amount (USD)", "mean"),
            avg_promo=("dependency_score", "mean"),
            count=("Customer ID", "count"),
            pct_high=("value_tier", lambda x: (x == "High").mean() * 100),
        )
        .reset_index()
    )

    # Classify market signal
    def signal(row):
        if row["avg_promo"] < 0.40 and row["avg_spend"] > 60:
            return "Organic Pull"
        elif row["avg_promo"] >= 0.50 and row["avg_spend"] > 60:
            return "Discount-Driven"
        return "Monitor"

    geo["signal"] = geo.apply(signal, axis=1)
    geo = geo.sort_values("avg_spend", ascending=False).head(20)

    color_map = {"Organic Pull": COLORS["green"], "Discount-Driven": COLORS["red"], "Monitor": COLORS["amber"]}
    signal_colors = [color_map[s] for s in geo["signal"]]

    fig = go.Figure()
    for sig, color in color_map.items():
        sub = geo[geo["signal"] == sig]
        fig.add_trace(go.Scatter(
            x=sub["avg_promo"],
            y=sub["avg_spend"],
            mode="markers+text",
            name=sig,
            text=sub["Location"],
            textposition="top center",
            textfont=dict(size=9),
            marker=dict(
                size=sub["count"] / 3,
                color=color,
                opacity=0.8,
                line=dict(width=1, color="white"),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Avg Spend: $%{y:.2f}<br>"
                "Promo Dependency: %{x:.3f}<br>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="<b>Geographic Opportunity Map</b><br><sup>Top 20 states — bubble size = customer count</sup>",
                   font=dict(size=16), x=0.03),
        legend=dict(bgcolor=COLORS["dark_bg"], bordercolor=COLORS["border"], borderwidth=1),
        xaxis=dict(title="Avg Promo Dependency →", gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        yaxis=dict(title="Avg Spend (USD) →", gridcolor=COLORS["border"]),
        shapes=[
            dict(type="line", x0=0.40, x1=0.40, y0=0, y1=1, yref="paper",
                 line=dict(color=COLORS["muted"], dash="dot", width=1)),
            dict(type="line", x0=0, x1=1, xref="paper", y0=60, y1=60,
                 line=dict(color=COLORS["muted"], dash="dot", width=1)),
        ],
        annotations=[
            dict(x=0.38, y=68, text="Organic Pull Zone", showarrow=False,
                 font=dict(color=COLORS["green"], size=10)),
            dict(x=0.52, y=68, text="Discount-Driven Zone", showarrow=False,
                 font=dict(color=COLORS["red"], size=10)),
        ],
    )
    return fig


def build_category_funnel(df: pd.DataFrame) -> go.Figure:
    """Panel 4: Category Funnel — Entry vs Retention."""
    cat = (
        df.groupby("Category")
        .agg(
            avg_tenure=("Previous Purchases", "mean"),
            avg_spend=("Purchase Amount (USD)", "mean"),
            avg_promo=("dependency_score", "mean"),
            pct_high=("value_tier", lambda x: (x == "High").mean() * 100),
        )
        .reset_index()
        .sort_values("avg_tenure", ascending=False)
    )

    cat["role"] = cat["avg_tenure"].apply(
        lambda x: "Retention Anchor" if x >= 25.5 else "Entry Point"
    )
    role_colors = [COLORS["green"] if r == "Retention Anchor" else COLORS["amber"] for r in cat["role"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cat["Category"],
        y=cat["avg_tenure"],
        name="Avg Tenure",
        marker_color=role_colors,
        text=cat["avg_tenure"].round(1),
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Avg Tenure: %{y:.1f} purchases<br>"
            "<extra></extra>"
        ),
    ))
    fig.add_trace(go.Scatter(
        x=cat["Category"],
        y=cat["avg_spend"],
        name="Avg Spend ($)",
        mode="markers+lines",
        yaxis="y2",
        marker=dict(size=10, color=COLORS["accent"]),
        line=dict(color=COLORS["accent"], dash="dot"),
    ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="<b>Category Funnel: Entry Point vs Retention Anchor</b><br><sup>Avg historical purchases + spend overlay</sup>",
                   font=dict(size=16), x=0.03),
        legend=dict(bgcolor=COLORS["dark_bg"], bordercolor=COLORS["border"], borderwidth=1),
        xaxis=dict(gridcolor=COLORS["border"]),
        yaxis=dict(title="Avg Purchase History", gridcolor=COLORS["border"]),
        yaxis2=dict(title="Avg Spend (USD)", overlaying="y", side="right", showgrid=False),
    )
    return fig


def build_icp_heatmap(df: pd.DataFrame) -> go.Figure:
    """Panel 5: ICP Demographics Heatmap — High Value customers by age × gender."""
    high = df[df["value_tier"] == "High"].copy()
    pivot = (
        high.groupby(["age_group", "Gender"])
        .agg(avg_spend=("Purchase Amount (USD)", "mean"))
        .reset_index()
        .pivot(index="age_group", columns="Gender", values="avg_spend")
    )

    age_order = ["Gen Z (18–24)", "Millennials (25–35)", "Gen X (36–50)", "Boomers (51+)"]
    pivot = pivot.reindex([a for a in age_order if a in pivot.index])

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, "#1A2A3A"], [0.5, COLORS["accent"]], [1, COLORS["green"]]],
        text=[[f"${v:.0f}" if not pd.isna(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        hovertemplate="<b>%{y} × %{x}</b><br>Avg Spend: $%{z:.2f}<extra></extra>",
        colorbar=dict(title="Avg Spend ($)", tickfont=dict(color=COLORS["text"])),
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="<b>ICP Demographics Heatmap</b><br><sup>Avg spend of High-Value customers by age group & gender</sup>",
                   font=dict(size=16), x=0.03),
        xaxis=dict(side="bottom"),
    )
    return fig


def build_season_risk(df: pd.DataFrame) -> go.Figure:
    """Panel 6: Season × Category Risk Matrix (Promo Dependency Heatmap)."""
    pivot = (
        df.groupby(["Season", "Category"])
        .agg(avg_promo=("dependency_score", "mean"))
        .reset_index()
        .pivot(index="Season", columns="Category", values="avg_promo")
    )

    season_order = ["Spring", "Summer", "Fall", "Winter"]
    pivot = pivot.reindex([s for s in season_order if s in pivot.index])

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, COLORS["green"]], [0.5, COLORS["amber"]], [1, COLORS["red"]]],
        zmin=0.38, zmax=0.52,
        text=[[f"{v:.3f}" if not pd.isna(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        hovertemplate="<b>%{y} — %{x}</b><br>Avg Promo Dependency: %{z:.3f}<extra></extra>",
        colorbar=dict(title="Promo Dependency", tickfont=dict(color=COLORS["text"])),
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="<b>Season × Category Promo Risk Matrix</b><br><sup>Higher = more discount-reliant (sunset candidates in red)</sup>",
                   font=dict(size=16), x=0.03),
    )
    return fig


def generate_dashboard(
    data_path: str = "data/cleaned_dataset.csv",
    output_path: str = "reports/dashboard.html",
) -> None:
    df = pd.read_csv(data_path)

    fig_pyramid   = build_pyramid(df)
    fig_promo     = build_promo_retention(df)
    fig_geo       = build_geo_map(df)
    fig_cat       = build_category_funnel(df)
    fig_icp       = build_icp_heatmap(df)
    fig_risk      = build_season_risk(df)

    # ── HTML shell ─────────────────────────────────────────────
    css = f"""
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        background: {COLORS['dark_bg']};
        color: {COLORS['text']};
        font-family: {FONT};
        min-height: 100vh;
    }}
    .header {{
        background: linear-gradient(135deg, #0D1117 0%, #161B22 50%, #0D1117 100%);
        border-bottom: 1px solid {COLORS['border']};
        padding: 32px 48px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .header-left h1 {{
        font-size: 26px;
        font-weight: 700;
        background: linear-gradient(90deg, {COLORS['accent']}, {COLORS['purple']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }}
    .header-left p {{
        font-size: 13px;
        color: {COLORS['muted']};
        margin-top: 4px;
    }}
    .badge {{
        background: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 12px;
        color: {COLORS['muted']};
        text-align: right;
    }}
    .badge strong {{ color: {COLORS['text']}; display: block; font-size: 14px; }}
    .kpi-row {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        padding: 24px 48px 0;
    }}
    .kpi {{
        background: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 20px 24px;
        transition: border-color 0.2s;
    }}
    .kpi:hover {{ border-color: {COLORS['accent']}; }}
    .kpi-label {{ font-size: 11px; font-weight: 500; color: {COLORS['muted']}; text-transform: uppercase; letter-spacing: 0.8px; }}
    .kpi-value {{ font-size: 28px; font-weight: 700; color: {COLORS['text']}; margin: 6px 0 2px; }}
    .kpi-sub {{ font-size: 12px; color: {COLORS['muted']}; }}
    .kpi-accent {{ color: {COLORS['accent']}; }}
    .kpi-green  {{ color: {COLORS['green']}; }}
    .kpi-red    {{ color: {COLORS['red']}; }}
    .kpi-amber  {{ color: {COLORS['amber']}; }}
    .dashboard-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        padding: 24px 48px 48px;
    }}
    .chart-card {{
        background: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        overflow: hidden;
        transition: border-color 0.2s, box-shadow 0.2s;
    }}
    .chart-card:hover {{
        border-color: {COLORS['accent']}44;
        box-shadow: 0 0 24px {COLORS['accent']}18;
    }}
    .chart-card .chart-inner {{
        padding: 4px;
    }}
    .footer {{
        text-align: center;
        padding: 24px;
        font-size: 11px;
        color: {COLORS['muted']};
        border-top: 1px solid {COLORS['border']};
    }}
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Decoding Customer Value — Founder Dashboard</title>
  <meta name="description" content="Customer intelligence dashboard for D2C fashion brand — value segmentation, promo dependency, geographic opportunity, and ideal customer profile.">
  <style>{css}</style>
</head>
<body>

<header class="header">
  <div class="header-left">
    <h1>Decoding Customer Value</h1>
    <p>Customer Intelligence &amp; Retention Strategy — D2C Fashion Brand</p>
  </div>
  <div class="badge">
    <strong>3,900 Customers</strong>
    Transactional Dataset · June 2025
  </div>
</header>

<div class="kpi-row">
  <div class="kpi">
    <div class="kpi-label">High-Value Customers</div>
    <div class="kpi-value kpi-green">299</div>
    <div class="kpi-sub">7.7% of customer base</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Avg Promo Dependency</div>
    <div class="kpi-value kpi-amber">43%</div>
    <div class="kpi-sub">Of all purchases used a discount/promo</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Loyal Customers (Vol.)</div>
    <div class="kpi-value kpi-accent">998</div>
    <div class="kpi-sub">25.6% with ≥38 previous purchases</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Sunset Risk Segments</div>
    <div class="kpi-value kpi-red">3</div>
    <div class="kpi-sub">Category × season combos to depromote</div>
  </div>
</div>

<div class="dashboard-grid">
  <div class="chart-card"><div class="chart-inner">
    {fig_pyramid.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})}
  </div></div>
  <div class="chart-card"><div class="chart-inner">
    {fig_promo.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})}
  </div></div>
  <div class="chart-card"><div class="chart-inner">
    {fig_geo.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})}
  </div></div>
  <div class="chart-card"><div class="chart-inner">
    {fig_cat.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})}
  </div></div>
  <div class="chart-card"><div class="chart-inner">
    {fig_icp.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})}
  </div></div>
  <div class="chart-card"><div class="chart-inner">
    {fig_risk.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})}
  </div></div>
</div>

<footer class="footer">
  Decoding Customer Value · Retention Strategy Analysis · Confidential
</footer>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[dashboard] Generated → {output_path}")


if __name__ == "__main__":
    generate_dashboard()
