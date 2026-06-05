# ABOUTME: How It Works page — explains the XAI scoring methodology in plain language.
# ABOUTME: Part of the multi-page Streamlit app for the HCI Food Recommender.

import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="How It Works — Food Recommender", layout="wide")

st.title("🔍 How It Works")
st.caption("A plain-language guide to how our AI recommends and explains food products.")

st.divider()

# ── Overview ──────────────────────────────────────────────────────────────────
st.header("🌱 What does this platform do?")
st.markdown("""
This platform helps you discover food products that match **your personal priorities** — 
whether you care more about health, environmental impact, or a balance of both.

It pulls real data from the **Open Food Facts** database (millions of products worldwide),
scores each product using a transparent formula, and lets an AI assistant explain
*why* any given product received its scores.
""")

st.divider()

# ── Scoring explained ─────────────────────────────────────────────────────────
st.header("📊 How are scores calculated?")

col1, col2 = st.columns(2)

with col1:
    st.subheader("💚 Health Score (0–100)")
    st.markdown("""
    The Health Score is built from two sources:

    **1. Nutri-Score grade** (official EU label)
    | Grade | Points |
    |-------|--------|
    | A     | 40     |
    | B     | 30     |
    | C     | 20     |
    | D     | 10     |
    | E     | 5      |

    **2. Nutrient adjustments** on top of the base grade:

    ✅ **Bonuses** (the more, the better)
    - Protein: up to +20 pts
    - Fiber: up to +15 pts

    ⛔ **Penalties** (the more, the worse)
    - Sugars, Saturated fat, Total fat, Carbohydrates, Sodium

    The final score is clamped between 0 and 100.
    """)

with col2:
    st.subheader("🌍 Eco Score (0–100)")
    st.markdown("""
    The Eco Score combines three factors:

    **1. Environmental Score grade** (official eco-label)
    — same A–E point table as Nutri-Score.

    **2. Packaging**
    - Recyclable packaging: +20 pts
    - Compostable packaging: +15 pts

    **3. Processing level (NOVA group)**
    | NOVA | Meaning | Points |
    |------|---------|--------|
    | 1    | Unprocessed | +15 |
    | 2    | Processed culinary | +10 |
    | 3    | Processed | +5  |
    | 4    | Ultra-processed | 0  |

    The final score is clamped between 0 and 100.
    """)

st.divider()

# ── Weighted score ─────────────────────────────────────────────────────────────
st.header("⚖️ Personalization — Weighted Score")
st.markdown("""
You control how much weight is given to Health vs. Eco using the sliders in the sidebar.

```
Weighted Score = (Health Score × Health Priority  +  Eco Score × Eco Priority) / 100
```

Products are **ranked by this weighted score**, so adjusting the sliders changes which products appear at the top.
""")

# Interactive example radar
st.subheader("Example: what a product profile looks like")
fig = go.Figure()
fig.add_trace(go.Scatterpolar(
    r=[72, 55, 80, 60, 70, 50],
    theta=["Health", "Eco-Footprint", "Low Processing", "Protein", "Low Sodium", "Packaging"],
    fill="toself",
    name="Example Product",
    line_color="#2ecc71",
))
fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    title="Radar Chart — each axis shows one dimension of quality (0 = worst, 100 = best)",
    height=400,
)
st.plotly_chart(fig, use_container_width=True)
st.caption("The filled area shows the product's profile. A larger area means better overall quality.")

st.divider()

# ── XAI techniques ────────────────────────────────────────────────────────────
st.header("🤖 Explainable AI (XAI) Techniques")

st.markdown("""
We use three complementary XAI techniques to make the AI's reasoning transparent:
""")

xai1, xai2, xai3 = st.columns(3)

with xai1:
    st.markdown("### 📊 Feature Attribution")
    st.markdown("""
    A **bar chart** shows exactly how much each nutrient contributed (positively or negatively) 
    to the Health Score. You can see at a glance whether high protein boosted the score 
    or whether too much saturated fat dragged it down.
    """)

with xai2:
    st.markdown("### 🔄 Contrastive Explanation")
    st.markdown("""
    The AI compares the selected product against the **best health alternative** and 
    **best eco alternative** in your search results — showing the delta in key metrics 
    so you can make an informed trade-off.
    """)

with xai3:
    st.markdown("### 💬 Conversational AI")
    st.markdown("""
    A chatbot backed by a large language model lets you ask **follow-up questions** 
    in plain English: *"Why is the eco score low?"*, *"What would make this healthier?"*, etc.
    The AI always grounds its answers in the actual product data shown on screen.
    """)

st.divider()

# ── Confidence ────────────────────────────────────────────────────────────────
st.header("🎯 Confidence Score")
st.markdown("""
Each product card shows a **Confidence** indicator. This reflects how complete the data is:

| Confidence | Meaning |
|------------|---------|
| 🟢 High    | Nutri-Score, Eco-Score, NOVA group, and key nutrients are all present |
| 🟡 Medium  | Some fields are missing; score is estimated from available data |
| 🔴 Low     | Most nutritional data is missing; treat this score with caution |

Missing data fields are filled with `0` so the formula still runs, but the confidence badge 
tells you how much to trust the result.
""")

st.divider()

# ── Data source ───────────────────────────────────────────────────────────────
st.header("📁 Data Source")
st.markdown("""
All product data comes from **[Open Food Facts](https://world.openfoodfacts.org/)** — 
a free, open, collaborative database of food products from around the world.

- **File used:** `en.openfoodfacts.org.products.csv.gz` (full English export)
- **Query engine:** DuckDB — reads the compressed CSV directly without loading it fully into memory
- **No personal data** is collected or stored by this platform
""")
