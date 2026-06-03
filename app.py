import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
import os
from ollama import Client
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# 🔧 HARDCODED CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL = "gpt-oss:120b"  # 🤖 Cloud model
CSV_PATH = "en.openfoodfacts.org.products.csv.gz"  # 📁 Ensure this file exists

client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
)

# ──────────────────────────────────────────────────────────────────────────────
# 1. APP CONFIGURATION & LAYOUT
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Local XAI Food Recommender", layout="wide")
st.title("🌱 Transparent Multi-Objective Food Recommendations")
st.caption("Powered by Local Open Food Facts CSV (DuckDB) & Ollama Cloud XAI")

# ──────────────────────────────────────────────────────────────────────────────
# 2. SIDEBAR: CONFIGURATION & DATA PATH
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # st.header("⚙️ Configuration")
    # api_key_set = bool(os.environ.get("OLLAMA_API_KEY"))
    # st.info(f"🔑 Ollama API Key: {'✅ Set via env' if api_key_set else '❌ OLLAMA_API_KEY not set'}")
    # st.info(f"🤖 Model: `{OLLAMA_MODEL}`")
    
    # st.divider()
    st.header("🔍 Search & Filters")
    search_query = st.text_input("Product Name", "Milk")
    
    st.divider()
    st.header("🥗 Nutritional Filters")
    # Minimum thresholds (Good stuff)
    min_protein = st.number_input("Min Protein (g/100g)", 0.0)
    min_fiber = st.number_input("Min Fiber (g/100g)", 0.0)
    
    st.divider()
    st.header("🚫 Max Limits (Bad stuff)")
    # Maximum thresholds (Bad stuff)
    max_sodium = st.number_input("Max Sodium (mg/100g)", 500.0)
    max_sugars = st.number_input("Max Sugars (g/100g)", 20.0)
    max_sat_fat = st.number_input("Max Saturated Fat (g/100g)", 3.0)
    max_fat = st.number_input("Max Total Fat (g/100g)", 10.0)
    max_carbs = st.number_input("Max Carbohydrates (g/100g)", 30.0)
    max_energy = st.number_input("Max Energy (kcal/100g)", 200.0)
    
    st.divider()
    st.header("📊 Personalization Weights")
    health_weight = st.slider("Health Priority", 0, 100, 50, key="hw")
    eco_weight = st.slider("Eco Priority", 0, 100, 50, key="ew")

# ──────────────────────────────────────────────────────────────────────────────

# 3. LOCAL DATA FETCHING & VECTORIZED SCORING (DuckDB + Pandas)
# ──────────────────────────────────────────────────────────────────────────────
def fetch_and_score(query, hw, ew, file_path):
    if not os.path.exists(file_path):
        return pd.DataFrame(), "❌ Data file not found. Check `CSV_PATH` variable."
        
    try:
        # Updated SQL to fetch new nutritional columns
        sql = f"""
        SELECT
            COALESCE(product_name, 'Unknown Product') AS product_name,
            nutriscore_grade,
            environmental_score_grade,
            nova_group,
            'N/A' as packaging_recycling_code,
            origins,
            image_url,
            COALESCE(proteins_100g, 0) AS protein,
            COALESCE(fiber_100g, 0) AS fiber,
            COALESCE(sodium_100g, 0) AS sodium,
            COALESCE(sugars_100g, 0) AS sugars,
            COALESCE(fat_100g, 0) AS fat,
            COALESCE("saturated-fat_100g", 0) AS sat_fat,
            COALESCE(carbohydrates_100g, 0) AS carbs,
            COALESCE("energy-kcal_100g", 0) AS energy
        FROM read_csv_auto('{file_path}')
        WHERE product_name ILIKE '%{query}%'
        LIMIT 100
        """
        df = duckdb.query(sql).df()
        if df.empty:
            return df, "⚠️ No matches found."

        # Apply Nutritional Filters (Strict filtering)
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

        # ──────────────────────────────────────────────────────────────────
        # UPDATED HEALTH SCORING LOGIC
        # ──────────────────────────────────────────────────────────────────
        grade_map = {'a': 40, 'b': 30, 'c': 20, 'd': 10, 'e': 5, 'n': 0}
        df['health_base'] = df['nutriscore_grade'].map(grade_map).fillna(0)
        
        # Eco Scoring (Unchanged)
        df['eco_base'] = df['environmental_score_grade'].map(grade_map).fillna(0)
        df['packaging_score'] = df['packaging_recycling_code'].apply(
            lambda x: 20 if x and 'recyclable' in str(x).lower() else (15 if x and 'compostable' in str(x).lower() else 0)
        )
        df['nova_score'] = df['nova_group'].apply(
            lambda x: max(0, 20 - (x * 5)) if pd.notna(x) else 0
        )

        # Health Formula: Good stuff (+) vs Bad stuff (-)
        # Protein & Fiber are positive drivers
        # Sugars, Sat Fat, Total Fat, Carbs, Sodium are negative drivers
        df['health'] = (
            df['health_base']
            # Good nutrients
            + df['protein'].clip(upper=10).mul(2)   # +2 pts per gram (capped)
            + df['fiber'].clip(upper=5).mul(3)     # +3 pts per gram (capped)
            # Bad nutrients (Penalties)
            - df['sugars'].clip(upper=50).div(5)   # -0.2 pts per gram
            - df['sat_fat'].clip(upper=10).mul(2)  # -2 pts per gram (heavier penalty)
            - df['fat'].clip(upper=20).mul(1)      # -1 pt per gram
            - df['carbs'].clip(upper=50).mul(0.2)  # -0.2 pts per gram
            - df['sodium'].clip(upper=2000).div(20) # -0.05 pts per mg
        ).clip(lower=0, upper=100).round(1)

        # Eco Scoring
        df['eco'] = (df['eco_base'] + df['packaging_score'] + df['nova_score']).clip(lower=0, upper=100).round(1)
        
        # Weighted Score
        df['weighted'] = (df['health'] * hw + df['eco'] * ew) / 100
        df = df.sort_values('weighted', ascending=False).reset_index(drop=True)
        
        return df, "✅ Loaded locally via DuckDB."
    except Exception as e:
        return pd.DataFrame(), f"❌ DuckDB Error: {e}"


# ──────────────────────────────────────────────────────────────────────────────

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
    """Send product context to Ollama and return the explanation string."""
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


# 4. MAIN UI
# ──────────────────────────────────────────────────────────────────────────────
if st.button("🔍 Query Local Database"):
    df, msg = fetch_and_score(search_query, health_weight, eco_weight, CSV_PATH)
    st.session_state["df"]  = df
    st.session_state["msg"] = msg
    st.session_state.pop("selected", None)
    st.session_state.pop("ollama_analysis", None)
    st.session_state.pop("ollama_error", None)
    st.session_state.pop("chat_history", None)

# Render results if we have them
if "df" in st.session_state and not st.session_state["df"].empty:
    df  = st.session_state["df"]
    st.info(st.session_state.get("msg", ""))
    st.success(f"Retrieved {len(df)} products from local compressed file.")

    NO_IMAGE_SVG = (
        "data:image/svg+xml;utf8,"
        "<svg xmlns='http://www.w3.org/2000/svg' width='150' height='150'>"
        "<rect width='150' height='150' fill='%23f0f0f0' rx='8'/>"
        "<text x='75' y='65' font-size='40' text-anchor='middle' dominant-baseline='middle'>🖼️</text>"
        "<text x='75' y='105' font-size='13' text-anchor='middle' fill='%23888' font-family='sans-serif'>No image</text>"
        "</svg>"
    )

    rows = [df.iloc[i:i+3] for i in range(0, len(df), 3)]
    for row_df in rows:
        cols = st.columns(3)
        for col_idx, (i, row) in enumerate(row_df.iterrows()):
            with cols[col_idx]:
                st.markdown(f"### {row['product_name']}")
                has_image = pd.notna(row.get('image_url')) and str(row.get('image_url', '')).strip()
                st.image(row['image_url'] if has_image else NO_IMAGE_SVG, width=150)
                st.metric("Health Score", f"{row['health']}/100")
                st.metric("Eco Score",    f"{row['eco']}/100")
                st.metric("Weighted",     f"{row['weighted']:.1f}")

                if st.button(f"📖 Analyze", key=f"btn_{i}"):
                    st.session_state["selected"]      = row.to_dict()
                    st.session_state["chat_history"]  = []
                    st.session_state.pop("ollama_analysis", None)
                    st.session_state.pop("ollama_error", None)

                    with st.spinner(f"Asking Ollama about {row['product_name']}…"):
                        analysis, error = run_ollama_analysis(row.to_dict(), df, health_weight, eco_weight)

                    if error:
                        st.session_state["ollama_error"] = error
                    else:
                        st.session_state["ollama_analysis"] = analysis
                        st.session_state["chat_history"].append({
                            "role":    "assistant",
                            "content": analysis,
                        })

    # ──────────────────────────────────────────────────────────────────────────
    # 5. DEEP DIVE SECTION
    # ──────────────────────────────────────────────────────────────────────────
    if "selected" in st.session_state:
        prod = st.session_state["selected"]
        st.divider()
        st.subheader(f"📊 Deep Dive: {prod['product_name']}")

        nova_val = prod.get('nova_group') or 0
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
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
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title="Product Profile (Multi-Criteria Radar)",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🔄 Alternative Engine")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Better for Health:** {df.loc[df['health'].idxmax(), 'product_name']} (Score: {df['health'].max()})")
        with c2:
            st.markdown(f"**Better for Earth:** {df.loc[df['eco'].idxmax(), 'product_name']} (Score: {df['eco'].max()})")

        # ── Ollama XAI Chat ──────────────────────────────────────────────────
        st.subheader("🤖 Explainable AI (Ollama Chatbot)")

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