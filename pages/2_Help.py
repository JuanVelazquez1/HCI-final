# ABOUTME: Help & FAQ page — answers common user questions about the platform.
# ABOUTME: Part of the multi-page Streamlit app for the HCI Food Recommender.

import streamlit as st

st.set_page_config(page_title="Help & FAQ — Food Recommender", layout="wide")

st.title("❓ Help & FAQ")
st.caption("Everything you need to know to get the most out of the Food Recommender.")

st.divider()

# ── Quick start ───────────────────────────────────────────────────────────────
st.header("🚀 Quick Start Guide")

with st.expander("Step 1 — Search for a product", expanded=True):
    st.markdown("""
    1. In the **sidebar on the left**, type a food product name in the **"Product Name"** box.  
       Examples: `Milk`, `Oat milk`, `Yogurt`, `Chocolate`, `Bread`
    2. Click **"🔍 Query Local Database"** (the big button on the main page).
    3. Wait a few seconds while the database is queried — results appear as product cards.
    """)

with st.expander("Step 2 — Understand the product cards"):
    st.markdown("""
    Each card shows:
    - **Product image** (or a placeholder if none is available)
    - **Health Score** — how nutritious the product is (0–100, higher = better)
    - **Eco Score** — how environmentally friendly it is (0–100, higher = better)
    - **Weighted Score** — a combined score based on your personal priorities
    - **Confidence badge** — how complete the underlying data is
    - **Nutri-Score badge** — the official EU nutrition label (A to E)
    - **NOVA group** — how processed the product is (1 = natural, 4 = ultra-processed)
    
    Click **"📖 Analyze"** on any card to get a deep-dive AI explanation.
    """)

with st.expander("Step 3 — Explore the AI explanation"):
    st.markdown("""
    After clicking **Analyze**, you'll see:
    - A **feature attribution bar chart** — shows which nutrients pushed the score up or down
    - A **radar chart** — visual multi-criteria profile of the product
    - **Alternative products** — better health or eco options from your search
    - An **AI chatbot** — ask follow-up questions like "Why is the eco score low?" or 
      "What's a healthier alternative?"
    """)

with st.expander("Step 4 — Personalise your results"):
    st.markdown("""
    Use the sidebar sliders:
    - **Health Priority** (0–100): how much you value nutrition
    - **Eco Priority** (0–100): how much you value environmental impact
    
    Setting Health = 80, Eco = 20 means the ranking prioritises nutritious products.  
    Setting Health = 0, Eco = 100 means only eco-friendliness drives the ranking.
    """)

st.divider()

# ── FAQ ───────────────────────────────────────────────────────────────────────
st.header("🙋 Frequently Asked Questions")

faq_items = [
    (
        "What data does this platform use?",
        """All product data comes from **Open Food Facts** — a free, open-source, 
        collaborative database of food products maintained by volunteers worldwide.  
        We use the full English CSV export (`en.openfoodfacts.org.products.csv.gz`).
        No personal data is collected by this app.""",
    ),
    (
        "Why do some products show 'No image'?",
        """Not every product in the Open Food Facts database has an associated image URL.  
        When no image is available, a placeholder graphic is shown instead.  
        This is a data completeness issue in the source dataset, not a bug.""",
    ),
    (
        "Why does my search return no results?",
        """Try these fixes:
        1. Use a more general term (e.g. `milk` instead of `organic skimmed milk`)
        2. Check your **nutritional filter** values — if you've set very strict limits 
           (e.g. Max Sugars = 0), most products will be filtered out. Reset filters by 
           refreshing the page.
        3. Some product names in the database are in their original language — try English 
           or the local language.""",
    ),
    (
        "What does the Confidence badge mean?",
        """The confidence indicator tells you how complete the product's data is:
        - 🟢 **High** — Nutri-Score, Eco-Score, NOVA group, and all key nutrients present
        - 🟡 **Medium** — some fields missing; score estimated from available data
        - 🔴 **Low** — most data missing; treat the score with caution
        
        Missing fields are filled with `0` so the scoring formula can still run, 
        but the result may not fully reflect reality.""",
    ),
    (
        "What is the NOVA group?",
        """NOVA is a food classification system based on **processing level**:
        - **NOVA 1** — Unprocessed or minimally processed foods (fresh fruit, plain meat, eggs)
        - **NOVA 2** — Processed culinary ingredients (oils, butter, flour, salt)
        - **NOVA 3** — Processed foods (canned vegetables, cheese, cured meat)
        - **NOVA 4** — Ultra-processed foods (soft drinks, packaged snacks, instant noodles)
        
        Lower NOVA = less processed = better for your Eco Score.""",
    ),
    (
        "What is the Nutri-Score?",
        """Nutri-Score is an **official European nutrition label** that rates products A–E:
        - **A (dark green)** — most nutritious
        - **B (light green)** — good nutritional quality
        - **C (yellow)** — average
        - **D (orange)** — below average
        - **E (red)** — least nutritious
        
        It's calculated by European food authorities based on calories, sugars, 
        saturated fat, sodium, fruits/vegetables, fibre, and protein.""",
    ),
    (
        "Can I trust the AI chatbot's answers?",
        """The AI chatbot (powered by Ollama) is grounded in the actual product data 
        shown on screen — it explains scores, compares alternatives, and suggests 
        improvements based on real numbers.
        
        However:
        - It does **not** give medical or dietary advice
        - It cannot access real-time data or the internet
        - Occasionally it may produce inaccurate or overly general responses
        
        Always consult a qualified nutritionist for personalised dietary guidance.""",
    ),
    (
        "How is the Weighted Score calculated?",
        """```
        Weighted Score = (Health Score × Health Priority  +  Eco Score × Eco Priority) / 100
        ```
        
        Adjust the **Health Priority** and **Eco Priority** sliders in the sidebar to 
        change how products are ranked. For example:
        - Health = 100, Eco = 0 → pure health ranking
        - Health = 50, Eco = 50 → balanced ranking (default)
        - Health = 0, Eco = 100 → pure eco ranking""",
    ),
    (
        "Why are some scores 0?",
        """A score of 0 usually means:
        1. The nutritional data for that product is **missing** in the database, or  
        2. The product's nutrients all received maximum penalties with no bonuses to offset them.
        
        Check the **Confidence badge** — if it shows 🔴 Low, the score is unreliable.""",
    ),
    (
        "How do I reset the filters?",
        """Refresh the browser page (F5 or Ctrl+R). All sidebar filters reset to their defaults:
        - Min Protein / Fiber: 0 g
        - Max Sodium: 500 mg
        - Max Sugars: 20 g
        - Max Saturated Fat: 3 g
        - Max Total Fat: 10 g
        - Max Carbohydrates: 30 g
        - Max Energy: 200 kcal
        - Health / Eco Priority: 50 each""",
    ),
]

for question, answer in faq_items:
    with st.expander(f"❓ {question}"):
        st.markdown(answer)

st.divider()

# ── Contact / About ───────────────────────────────────────────────────────────
st.header("ℹ️ About this Platform")
st.markdown("""
This platform was built as a final project for **HCI 11755 — Human-Computer Interaction, Summer 2026**.

**Tech stack:**
- 🐍 Python + Streamlit (web framework)
- 🦆 DuckDB (in-process SQL query engine for the CSV dataset)
- 🤖 Ollama (LLM-based XAI explanations)
- 📊 Plotly (interactive charts)
- 📦 Open Food Facts (dataset)

**Design approach:** User-Centered Design with iterative usability testing.

For technical issues, please refer to the `README.md` in the project repository.
""")
