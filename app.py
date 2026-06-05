# ABOUTME: Main entry point for the XAI Food Recommender Streamlit app.
# ABOUTME: Handles product search, scoring, feature-attribution XAI charts, and Ollama chatbot.

import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
import os
from ollama import Client
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# Dataset: Open Food Facts full English CSV export (en.openfoodfacts.org.products.csv.gz)
# Source:  https://world.openfoodfacts.org/data
# ──────────────────────────────────────────────────────────────────────────────
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL = "gpt-oss:120b"  # Cloud model via Ollama API
CSV_PATH = "en.openfoodfacts.org.products.csv.gz"  # Full OFF English dataset

client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
)

# ──────────────────────────────────────────────────────────────────────────────
# APP CONFIGURATION & LAYOUT
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="XAI Food Recommender",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Nutri-Score badges, confidence badges, and card polish
st.markdown("""
<style>
.nutri-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-weight: bold;
    font-size: 0.85em;
    color: white;
    margin-bottom: 4px;
}
.nutri-a { background-color: #038141; }
.nutri-b { background-color: #85bb2f; }
.nutri-c { background-color: #fecb02; color: #333; }
.nutri-d { background-color: #ee8100; }
.nutri-e { background-color: #e63e11; }
.nutri-n { background-color: #aaaaaa; }

.confidence-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.8em;
    font-weight: 600;
    margin-left: 6px;
}
.conf-high   { background-color: #d4edda; color: #155724; }
.conf-medium { background-color: #fff3cd; color: #856404; }
.conf-low    { background-color: #f8d7da; color: #721c24; }

.nova-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.78em;
    font-weight: 600;
    background-color: #e8f4fd;
    color: #1a6a9c;
    margin-left: 4px;
}
</style>
""", unsafe_allow_html=True)

st.title("🌱 Transparent Multi-Objective Food Recommendations")
st.caption("Powered by Open Food Facts (DuckDB) · Explainable AI via Ollama · Navigate using the sidebar ←")

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR: SEARCH & FILTERS
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Search & Filters")
    search_query = st.text_input(
        "Product Name",
        "Milk",
        help="Type any food product name. The search is case-insensitive and matches partial names.",
    )

    st.divider()
    st.header("🥗 Nutritional Filters")
    min_protein = st.number_input(
        "Min Protein (g/100g)", 0.0,
        help="Only show products with at least this much protein per 100 g. Protein is a positive health driver.",
    )
    min_fiber = st.number_input(
        "Min Fiber (g/100g)", 0.0,
        help="Only show products with at least this much dietary fiber per 100 g.",
    )

    st.divider()
    st.header("🚫 Max Limits")
    max_sodium = st.number_input(
        "Max Sodium (mg/100g)", 500.0,
        help="Exclude products with more sodium than this. High sodium is associated with cardiovascular risk.",
    )
    max_sugars = st.number_input(
        "Max Sugars (g/100g)", 20.0,
        help="Exclude products with more total sugars than this.",
    )
    max_sat_fat = st.number_input(
        "Max Saturated Fat (g/100g)", 3.0,
        help="Exclude products with more saturated fat than this. Saturated fat carries a heavier health penalty.",
    )
    max_fat = st.number_input(
        "Max Total Fat (g/100g)", 10.0,
        help="Exclude products with more total fat than this.",
    )
    max_carbs = st.number_input(
        "Max Carbohydrates (g/100g)", 30.0,
        help="Exclude products with more carbohydrates than this.",
    )
    max_energy = st.number_input(
        "Max Energy (kcal/100g)", 200.0,
        help="Exclude products with more energy density than this (kcal per 100 g).",
    )

    st.divider()
    st.header("📊 Personalization Weights")
    st.caption("Adjust how much Health vs. Eco impacts the ranking.")
    health_weight = st.slider(
        "Health Priority", 0, 100, 50, key="hw",
        help="Higher = products are ranked more by their Health Score.",
    )
    eco_weight = st.slider(
        "Eco Priority", 0, 100, 50, key="ew",
        help="Higher = products are ranked more by their Eco Score.",
    )

    st.divider()
    st.caption("📖 [How It Works](/How_It_Works)  |  ❓ [Help & FAQ](/Help)")


# ──────────────────────────────────────────────────────────────────────────────
# HELPER: CONFIDENCE SCORE
# Counts how many key data fields are populated to gauge data completeness.
# ──────────────────────────────────────────────────────────────────────────────
def compute_confidence(row):
    """Return (label, css_class, pct) based on how many key fields are non-zero/non-null."""
    fields = [
        row.get('nutriscore_grade') not in (None, 'n', '', 'N/A'),
        row.get('environmental_score_grade') not in (None, 'n', '', 'N/A'),
        pd.notna(row.get('nova_group')) and row.get('nova_group') != 0,
        row.get('protein', 0) > 0,
        row.get('fiber', 0) > 0,
        row.get('sodium', 0) > 0,
        row.get('sugars', 0) > 0,
        row.get('fat', 0) > 0,
    ]
    score = sum(fields)
    if score >= 6:
        return "🟢 High", "conf-high", score / len(fields)
    elif score >= 3:
        return "🟡 Medium", "conf-medium", score / len(fields)
    else:
        return "🔴 Low", "conf-low", score / len(fields)


# ──────────────────────────────────────────────────────────────────────────────
# HELPER: NUTRI-SCORE HTML BADGE
# ──────────────────────────────────────────────────────────────────────────────
def nutri_badge_html(grade):
    """Return an HTML badge for the given Nutri-Score grade letter."""
    g = str(grade).lower() if pd.notna(grade) else 'n'
    if g not in ('a', 'b', 'c', 'd', 'e'):
        g = 'n'
    label = g.upper() if g != 'n' else '?'
    return f'<span class="nutri-badge nutri-{g}">Nutri-Score {label}</span>'


# ──────────────────────────────────────────────────────────────────────────────
# HELPER: NOVA GROUP LABEL
# ──────────────────────────────────────────────────────────────────────────────
NOVA_LABELS = {
    1: "Unprocessed",
    2: "Culinary ingredient",
    3: "Processed",
    4: "Ultra-processed",
}

def nova_badge_html(nova_group):
    """Return an HTML badge showing the NOVA processing group."""
    try:
        n = int(nova_group)
        label = NOVA_LABELS.get(n, f"NOVA {n}")
    except (TypeError, ValueError):
        return ""
    return f'<span class="nova-badge">NOVA {n} · {label}</span>'


# ──────────────────────────────────────────────────────────────────────────────
# XAI FEATURE ATTRIBUTION
# Computes the signed contribution of each factor to the Health Score.
# This makes the scoring formula transparent and auditable.
# ──────────────────────────────────────────────────────────────────────────────
def compute_feature_contributions(row):
    """
    Decompose the Health Score into signed per-feature contributions.

    Returns a list of (feature_label, contribution_value) tuples, sorted by
    absolute contribution descending. Positive = helped the score, negative = hurt it.
    """
    grade_map = {'a': 40, 'b': 30, 'c': 20, 'd': 10, 'e': 5, 'n': 0}
    g = str(row.get('nutriscore_grade', '')).lower()
    health_base = grade_map.get(g, 0)

    protein_contrib  = +min(row.get('protein', 0), 10) * 2
    fiber_contrib    = +min(row.get('fiber', 0), 5) * 3
    sugars_contrib   = -min(row.get('sugars', 0), 50) / 5
    sat_fat_contrib  = -min(row.get('sat_fat', 0), 10) * 2
    fat_contrib      = -min(row.get('fat', 0), 20) * 1
    carbs_contrib    = -min(row.get('carbs', 0), 50) * 0.2
    sodium_contrib   = -min(row.get('sodium', 0), 2000) / 20

    contributions = [
        ("Nutri-Score grade", health_base),
        ("Protein", round(protein_contrib, 1)),
        ("Fiber", round(fiber_contrib, 1)),
        ("Sugars", round(sugars_contrib, 1)),
        ("Saturated Fat", round(sat_fat_contrib, 1)),
        ("Total Fat", round(fat_contrib, 1)),
        ("Carbohydrates", round(carbs_contrib, 1)),
        ("Sodium", round(sodium_contrib, 1)),
    ]
    return sorted(contributions, key=lambda x: abs(x[1]), reverse=True)


def feature_attribution_chart(row):
    """
    Build a Plotly horizontal bar chart showing each feature's signed contribution
    to the Health Score. Green bars = positive, red bars = negative.
    """
    contribs = compute_feature_contributions(row)
    labels = [c[0] for c in contribs]
    values = [c[1] for c in contribs]
    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in values]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{'+' if v >= 0 else ''}{v}" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        title="Feature Attribution — Health Score Breakdown",
        xaxis_title="Score contribution (pts)",
        yaxis=dict(autorange="reversed"),
        height=320,
        margin=dict(l=10, r=40, t=40, b=10),
        xaxis=dict(zeroline=True, zerolinecolor="gray", zerolinewidth=1),
    )
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# LOCAL DATA FETCHING & VECTORIZED SCORING (DuckDB + Pandas)
# Dataset: Open Food Facts — https://world.openfoodfacts.org/data
# ──────────────────────────────────────────────────────────────────────────────
def fetch_and_score(query, hw, ew, file_path):
    """
    Query the Open Food Facts CSV via DuckDB, apply nutritional filters,
    compute Health/Eco scores, and return ranked results.

    Args:
        query: product name search string
        hw: health weight (0-100)
        ew: eco weight (0-100)
        file_path: path to the compressed CSV file

    Returns:
        (DataFrame, status_message)
    """
    if not os.path.exists(file_path):
        return pd.DataFrame(), "❌ Data file not found. Check `CSV_PATH` variable."

    try:
        sql = f"""
        SELECT
            COALESCE(product_name, 'Unknown Product') AS product_name,
            nutriscore_grade,
            environmental_score_grade,
            nova_group,
            'N/A' as packaging_recycling_code,
            origins,
            image_url,
            COALESCE(proteins_100g, 0)          AS protein,
            COALESCE(fiber_100g, 0)              AS fiber,
            COALESCE(sodium_100g, 0)             AS sodium,
            COALESCE(sugars_100g, 0)             AS sugars,
            COALESCE(fat_100g, 0)                AS fat,
            COALESCE("saturated-fat_100g", 0)    AS sat_fat,
            COALESCE(carbohydrates_100g, 0)      AS carbs,
            COALESCE("energy-kcal_100g", 0)      AS energy
        FROM read_csv_auto('{file_path}')
        WHERE product_name ILIKE '%{query}%'
        LIMIT 100
        """
        df = duckdb.query(sql).df()
        if df.empty:
            return df, "⚠️ No matches found."

        # Apply strict nutritional filters from sidebar
        df = df[
            (df['protein'] >= min_protein) &
            (df['fiber'] >= min_fiber) &
            (df['sodium'] <= max_sodium) &
            (df['sugars'] <= max_sugars) &
            (df['sat_fat'] <= max_sat_fat) &
            (df['fat'] <= max_fat) &
            (df['carbs'] <= max_carbs) &
            (df['energy'] <= max_energy)
        ]

        if df.empty:
            return df, "⚠️ No matches found after applying filters."

        # ── Health Scoring ──────────────────────────────────────────────────
        # Nutri-Score grade provides a base; individual nutrients add/subtract points.
        # Good nutrients: Protein (+2 pts/g, capped at 10g) and Fiber (+3 pts/g, capped at 5g)
        # Bad nutrients: Sugars, Sat Fat, Total Fat, Carbs, Sodium all apply penalties.
        grade_map = {'a': 40, 'b': 30, 'c': 20, 'd': 10, 'e': 5, 'n': 0}
        df['health_base'] = df['nutriscore_grade'].map(grade_map).fillna(0)

        df['health'] = (
            df['health_base']
            + df['protein'].clip(upper=10).mul(2)
            + df['fiber'].clip(upper=5).mul(3)
            - df['sugars'].clip(upper=50).div(5)
            - df['sat_fat'].clip(upper=10).mul(2)
            - df['fat'].clip(upper=20).mul(1)
            - df['carbs'].clip(upper=50).mul(0.2)
            - df['sodium'].clip(upper=2000).div(20)
        ).clip(lower=0, upper=100).round(1)

        # ── Eco Scoring ─────────────────────────────────────────────────────
        # Environmental grade base + packaging bonus + NOVA processing penalty
        df['eco_base'] = df['environmental_score_grade'].map(grade_map).fillna(0)
        df['packaging_score'] = df['packaging_recycling_code'].apply(
            lambda x: 20 if x and 'recyclable' in str(x).lower()
            else (15 if x and 'compostable' in str(x).lower() else 0)
        )
        df['nova_score'] = df['nova_group'].apply(
            lambda x: max(0, 20 - (x * 5)) if pd.notna(x) else 0
        )
        df['eco'] = (df['eco_base'] + df['packaging_score'] + df['nova_score']).clip(lower=0, upper=100).round(1)

        # ── Weighted Score ──────────────────────────────────────────────────
        df['weighted'] = (df['health'] * hw + df['eco'] * ew) / 100
        df = df.sort_values('weighted', ascending=False).reset_index(drop=True)

        return df, "✅ Loaded locally via DuckDB."
    except Exception as e:
        return pd.DataFrame(), f"❌ DuckDB Error: {e}"


# ──────────────────────────────────────────────────────────────────────────────
# OLLAMA CLOUD HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def ollama_chat(messages, system=None):
    """Send a chat request to Ollama Cloud and return (reply_text, error)."""
    all_messages = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)

    try:
        response = client.chat(OLLAMA_MODEL, messages=all_messages, stream=False)
        return response["message"]["content"], None
    except Exception as e:
        msg = str(e)
        if "401" in msg or "unauthorized" in msg.lower():
            return None, "❌ Invalid API key. Set the OLLAMA_API_KEY environment variable."
        return None, f"❌ Ollama Error: {e}"


def run_ollama_analysis(prod, df, health_weight, eco_weight):
    """
    Send product context to Ollama and return the XAI explanation string.

    The prompt requests feature attribution, contrastive explanation,
    personalised insight, and actionable tips — all key XAI requirements.
    """
    best_health_name = df.loc[df['health'].idxmax(), 'product_name']
    best_eco_name    = df.loc[df['eco'].idxmax(), 'product_name']

    prompt = f"""You are an Explainable AI (XAI) assistant for a sustainable food recommender.

Product being analysed: {prod['product_name']}
- Health Score: {prod['health']}/100  |  Eco Score: {prod['eco']}/100
- Processing level (Nova group): {prod.get('nova_group', 'N/A')}  (1 = unprocessed, 4 = ultra-processed)
- Nutrition per 100 g: Protein {prod['protein']} g, Sodium {prod['sodium']} mg, Fiber {prod['fiber']} g, Sugars {prod['sugars']} g
- Fats: Total {prod['fat']} g | Saturated {prod['sat_fat']} g | Carbs {prod['carbs']} g | Energy {prod['energy']} kcal
- Packaging: {prod['packaging_recycling_code']}  |  Origins: {prod['origins']}
- User priorities: Health {health_weight}%, Eco {eco_weight}%
- Top health alternative: {best_health_name} (Health score {df['health'].max()})
- Top eco alternative:    {best_eco_name}    (Eco score {df['eco'].max()})

Please provide:
1. **Feature Attribution** - which specific data points drive the health and eco scores, and by how much.
2. **Contrastive Explanation** - compare this product against the two alternatives with delta metrics.
3. **Personalised Insight** - given the user's {health_weight}/{eco_weight} health/eco weighting, is this a good choice? What trade-offs exist?
4. **Actionable Tips** - one or two concrete suggestions to improve this product's profile or better alternatives to consider.

Keep the tone transparent, evidence-based, and non-judgmental. No medical or financial advice."""

    return ollama_chat([{"role": "user", "content": prompt}])


def run_ollama_chat(prod, df, health_weight, eco_weight, chat_history, user_message):
    """Send a follow-up message with full chat history to Ollama."""
    best_health_name = df.loc[df['health'].idxmax(), 'product_name']
    best_eco_name    = df.loc[df['eco'].idxmax(), 'product_name']

    system_instruction = f"""You are an Explainable AI (XAI) assistant for a sustainable food recommender.
Product: {prod['product_name']}
Health Score: {prod['health']}/100 | Eco Score: {prod['eco']}/100
Nova group: {prod.get('nova_group', 'N/A')} | Protein: {prod['protein']}g | Sodium: {prod['sodium']}mg | Fiber: {prod['fiber']}g | Sugars: {prod['sugars']}g
Fats: Total {prod['fat']}g | Sat Fat {prod['sat_fat']}g | Carbs {prod['carbs']}g | Energy {prod['energy']}kcal
Packaging: {prod['packaging_recycling_code']} | Origins: {prod['origins']}
User priorities: Health {health_weight}%, Eco {eco_weight}%
Alternatives: Health-focused ({best_health_name}), Eco-focused ({best_eco_name})
Guidelines: Feature attribution, contrastive explanations, transparent & non-judgmental. No medical/financial advice."""

    messages = []
    for msg in chat_history:
        role = "assistant" if msg["role"] == "assistant" else "user"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    return ollama_chat(messages, system=system_instruction)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN UI — SEARCH BUTTON & RESULTS
# ──────────────────────────────────────────────────────────────────────────────
if st.button("🔍 Query Local Database", type="primary"):
    df, msg = fetch_and_score(search_query, health_weight, eco_weight, CSV_PATH)
    st.session_state["df"]  = df
    st.session_state["msg"] = msg
    st.session_state.pop("selected", None)
    st.session_state.pop("ollama_analysis", None)
    st.session_state.pop("ollama_error", None)
    st.session_state.pop("chat_history", None)

# ── Results ───────────────────────────────────────────────────────────────────
if "df" in st.session_state and not st.session_state["df"].empty:
    df = st.session_state["df"]
    st.info(st.session_state.get("msg", ""))

    # ── Dashboard summary statistics ─────────────────────────────────────────
    st.subheader("📊 Results Summary")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Products found", len(df))
    m2.metric("Avg Health Score", f"{df['health'].mean():.1f}/100")
    m3.metric("Avg Eco Score", f"{df['eco'].mean():.1f}/100")
    m4.metric("Best Health", f"{df['health'].max()}/100")
    m5.metric("Best Eco", f"{df['eco'].max()}/100")

    st.caption(
        f"Search: **{search_query}** · Health priority: {health_weight}% · "
        f"Eco priority: {eco_weight}% · Ranked by Weighted Score"
    )
    st.divider()

    NO_IMAGE_SVG = (
        "data:image/svg+xml;utf8,"
        "<svg xmlns='http://www.w3.org/2000/svg' width='150' height='150'>"
        "<rect width='150' height='150' fill='%23f0f0f0' rx='8'/>"
        "<text x='75' y='65' font-size='40' text-anchor='middle' dominant-baseline='middle'>🖼️</text>"
        "<text x='75' y='105' font-size='13' text-anchor='middle' fill='%23888' font-family='sans-serif'>No image</text>"
        "</svg>"
    )

    # ── Product cards — 3 per row ─────────────────────────────────────────────
    rows = [df.iloc[i:i+3] for i in range(0, len(df), 3)]
    for row_df in rows:
        cols = st.columns(3)
        for col_idx, (i, row) in enumerate(row_df.iterrows()):
            with cols[col_idx]:
                conf_label, conf_cls, _ = compute_confidence(row)

                # Product name + badges
                st.markdown(f"### {row['product_name']}")
                badge_html = nutri_badge_html(row.get('nutriscore_grade'))
                nova_html = nova_badge_html(row.get('nova_group'))
                conf_html = f'<span class="confidence-badge {conf_cls}">{conf_label} confidence</span>'
                st.markdown(badge_html + nova_html + "<br>" + conf_html, unsafe_allow_html=True)

                has_image = pd.notna(row.get('image_url')) and str(row.get('image_url', '')).strip()
                st.image(row['image_url'] if has_image else NO_IMAGE_SVG, width=150)

                c1, c2, c3 = st.columns(3)
                c1.metric("Health", f"{row['health']}")
                c2.metric("Eco", f"{row['eco']}")
                c3.metric("Score", f"{row['weighted']:.1f}")

                if st.button("📖 Analyze", key=f"btn_{i}"):
                    st.session_state["selected"]     = row.to_dict()
                    st.session_state["chat_history"] = []
                    st.session_state.pop("ollama_analysis", None)
                    st.session_state.pop("ollama_error", None)

                    with st.spinner(f"Asking Ollama about {row['product_name']}…"):
                        analysis, error = run_ollama_analysis(row.to_dict(), df, health_weight, eco_weight)

                    if error:
                        st.session_state["ollama_error"] = error
                    else:
                        st.session_state["ollama_analysis"] = analysis
                        st.session_state["chat_history"].append({
                            "role": "assistant",
                            "content": analysis,
                        })

    # ── Deep Dive Section ─────────────────────────────────────────────────────
    if "selected" in st.session_state:
        prod = st.session_state["selected"]
        st.divider()
        st.subheader(f"📊 Deep Dive: {prod['product_name']}")

        # ── XAI Feature Attribution bar chart (plain-language score breakdown) ──
        st.markdown("#### 🔬 Why did this product get its Health Score?")
        st.caption(
            "Each bar shows how much a specific nutrient or grade helped (green) "
            "or hurt (red) the Health Score. This makes the AI's reasoning transparent."
        )
        st.plotly_chart(feature_attribution_chart(prod), use_container_width=True)

        # ── Confidence detail ──────────────────────────────────────────────────
        conf_label, _, conf_pct = compute_confidence(prod)
        st.markdown(
            f"**Data Confidence:** {conf_label} — "
            f"{int(conf_pct * 100)}% of key data fields are populated for this product."
        )

        # ── Multi-criteria radar chart ─────────────────────────────────────────
        nova_val = prod.get('nova_group') or 0
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=[
                prod['health'],
                prod['eco'],
                max(0, 100 - nova_val * 20),
                min(100, prod['protein'] * 2),
                max(0, 100 - prod['sodium'] / 5),
                50,
            ],
            theta=["Health", "Eco-Footprint", "Low Processing", "Protein", "Low Sodium", "Packaging"],
            fill="toself",
            name=prod['product_name'],
            line_color="#2ecc71",
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title="Product Profile — Multi-Criteria Radar (0 = worst, 100 = best)",
            height=400,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # ── Alternative Engine ─────────────────────────────────────────────────
        st.subheader("🔄 Alternative Engine")
        st.caption("Contrastive comparison: the best alternatives in your current search results.")
        best_health_idx = df['health'].idxmax()
        best_eco_idx    = df['eco'].idxmax()
        best_health_row = df.loc[best_health_idx]
        best_eco_row    = df.loc[best_eco_idx]

        c1, c2 = st.columns(2)
        with c1:
            delta_h = round(best_health_row['health'] - prod['health'], 1)
            st.markdown("**💚 Better for Health:**")
            st.markdown(f"**{best_health_row['product_name']}**")
            st.markdown(
                f"Health: {best_health_row['health']}/100 "
                f"{'(+'+str(delta_h)+' vs this product)' if delta_h > 0 else '(same)'}"
            )
        with c2:
            delta_e = round(best_eco_row['eco'] - prod['eco'], 1)
            st.markdown("**🌍 Better for Earth:**")
            st.markdown(f"**{best_eco_row['product_name']}**")
            st.markdown(
                f"Eco: {best_eco_row['eco']}/100 "
                f"{'(+'+str(delta_e)+' vs this product)' if delta_e > 0 else '(same)'}"
            )

        # ── Ollama XAI Chat ────────────────────────────────────────────────────
        st.subheader("🤖 Explainable AI — Ask the Assistant")
        st.caption(
            "The AI assistant can explain scores, compare products, and suggest improvements. "
            "It is grounded in the product data shown above and does not give medical advice."
        )

        if "ollama_error" in st.session_state:
            st.error(st.session_state["ollama_error"])

        for msg in st.session_state.get("chat_history", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask about trade-offs, scores, or alternatives…"):
            st.session_state["chat_history"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.spinner("Thinking…"):
                reply, error = run_ollama_chat(
                    prod, df, health_weight, eco_weight,
                    st.session_state["chat_history"], prompt
                )

            if error:
                st.error(error)
            else:
                st.session_state["chat_history"].append({"role": "assistant", "content": reply})
                with st.chat_message("assistant"):
                    st.markdown(reply)

elif "msg" in st.session_state:
    st.info(st.session_state["msg"])

else:
    # ── Welcome / onboarding state ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "### 👋 Welcome!\n"
        "Use the **sidebar** to search for a food product and set your nutritional filters, "
        "then click **🔍 Query Local Database** to get personalised recommendations with "
        "transparent AI explanations.\n\n"
        "Not sure where to start? Try searching for **Milk**, **Yogurt**, or **Bread**."
    )
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.info("🔍 **Step 1** — Type a product name in the sidebar and click Query")
    with col_b:
        st.info("📊 **Step 2** — Browse ranked cards and click Analyze on any product")
    with col_c:
        st.info("🤖 **Step 3** — Chat with the AI to understand scores and alternatives")
