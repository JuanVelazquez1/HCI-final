# 🌱 XAI Food Recommender

A **Transparent Multi-Objective Food Recommendation** web platform built with Streamlit.
Recommends food products from the Open Food Facts database using explainable AI (XAI) techniques,
making every scoring decision visible and understandable to non-technical users.

Built as a final project for **HCI 11755 — Human-Computer Interaction, Summer Semester 2026**.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web framework | [Streamlit](https://streamlit.io/) |
| Query engine | [DuckDB](https://duckdb.org/) — queries the compressed CSV directly |
| LLM / XAI chat | [Ollama](https://ollama.com/) cloud API (`gpt-oss:120b`) |
| Charts | [Plotly](https://plotly.com/python/) |
| Dataset | [Open Food Facts](https://world.openfoodfacts.org/data) |
| Language | Python 3.11+ |

---

## Setup & Run

### 1. Prerequisites

- Python 3.11+
- The Open Food Facts dataset file (see below)
- An Ollama cloud API key

### 2. Clone and install

```bash
git clone <repo-url>
cd HCI-final
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment variables

Create a `.env` file in the project root (never commit this file):

```
OLLAMA_API_KEY=your_ollama_api_key_here
```

### 4. Dataset

Download the full English Open Food Facts CSV export:

- **URL:** https://world.openfoodfacts.org/data
- **File:** `en.openfoodfacts.org.products.csv.gz`
- Place it in the project root alongside `app.py`

The file is ~1.2 GB compressed. DuckDB reads it directly without extracting.

### 5. Run the app

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## Project Structure

```
HCI-final/
├── app.py                          # Main page — search, product cards, deep-dive XAI
├── pages/
│   ├── 1_How_It_Works.py           # XAI methodology explainer page
│   └── 2_Help.py                   # Help & FAQ page
├── requirements.txt                # Python dependencies (pinned)
├── requirements.md                 # Human-readable project requirements
├── .env                            # API keys (not committed)
├── .gitignore
└── en.openfoodfacts.org.products.csv.gz   # Dataset (not committed — too large)
```

---

## XAI Techniques

### 1. Feature Attribution Bar Chart (`app.py` — `compute_feature_contributions`, `feature_attribution_chart`)

A horizontal bar chart decomposes the **Health Score** into signed per-nutrient contributions:
- **Green bars** = nutrients that boosted the score (protein, fiber, Nutri-Score grade)
- **Red bars** = nutrients that penalised the score (sugars, saturated fat, sodium, etc.)

This is equivalent to a local linear SHAP explanation — users can see exactly which ingredient drove a high or low score.

### 2. Confidence Score (`app.py` — `compute_confidence`)

Each product card shows a **🟢 High / 🟡 Medium / 🔴 Low** confidence badge based on how many of the 8 key data fields (Nutri-Score, Eco-Score, NOVA group, protein, fiber, sodium, sugars, fat) are populated. This tells users how much to trust the computed score.

### 3. Multi-Criteria Radar Chart (`app.py` — Deep Dive section)

A spider/radar chart visualises 6 dimensions simultaneously: Health, Eco-Footprint, Low Processing, Protein, Low Sodium, and Packaging. This gives a spatial overview of the product's strengths and weaknesses.

### 4. Contrastive Explanation (`app.py` — Alternative Engine)

The "Alternative Engine" shows the **best health alternative** and **best eco alternative** from the current search results, with delta scores to make the comparison concrete: *"+12 pts vs this product"*.

### 5. Conversational XAI (`app.py` — `run_ollama_analysis`, `run_ollama_chat`)

An Ollama-backed chatbot provides:
- Natural language feature attribution
- Contrastive product comparisons
- Personalised insights based on the user's health/eco weighting
- Actionable improvement suggestions

The system prompt is grounded in the actual product data so the LLM cannot hallucinate scores.

---

## Scoring Formulas

### Health Score (0–100)

```
health = nutriscore_base
       + protein.clip(10) × 2
       + fiber.clip(5) × 3
       − sugars.clip(50) / 5
       − sat_fat.clip(10) × 2
       − fat.clip(20) × 1
       − carbs.clip(50) × 0.2
       − sodium.clip(2000) / 20
```

Nutri-Score base: A=40, B=30, C=20, D=10, E=5, unknown=0.

### Eco Score (0–100)

```
eco = environmental_score_base + packaging_score + nova_score
```

- `packaging_score`: recyclable=20, compostable=15, other=0
- `nova_score`: max(0, 20 − nova_group × 5)

### Weighted Score

```
weighted = (health × health_priority + eco × eco_priority) / 100
```

Users control `health_priority` and `eco_priority` (0–100) via sidebar sliders.

---

## Dataset Source & Structure

**Open Food Facts** — https://world.openfoodfacts.org/

- Free, open, collaborative database maintained by volunteers worldwide
- Full English export: `en.openfoodfacts.org.products.csv.gz`
- Key columns used: `product_name`, `nutriscore_grade`, `environmental_score_grade`, `nova_group`, `image_url`, `origins`, `proteins_100g`, `fiber_100g`, `sodium_100g`, `sugars_100g`, `fat_100g`, `saturated-fat_100g`, `carbohydrates_100g`, `energy-kcal_100g`
- Missing values are filled with `0` via `COALESCE` in the DuckDB SQL query

---

## Security

- API keys are loaded from `.env` via `python-dotenv` — never hardcoded
- `.env` is listed in `.gitignore`
- The dataset file is not committed (too large; users must download it separately)
