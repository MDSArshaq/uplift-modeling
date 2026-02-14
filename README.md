# The Persuadable Hunter: Uplift Modeling & Model Auditing

> **"Don't email everyone. Find the customers who change their mind because of your email."**

An end-to-end uplift modeling project that goes beyond model accuracy to address **model calibration, business simulation, and human-in-the-loop auditing** — built on the Hillstrom Email Marketing dataset.

**[Try the Interactive App](https://uplift-modeling-h3ctl3jucjpqdnd6ulmewc.streamlit.app/)** *(Streamlit Cloud)*

---

## The Business Problem

A marketing team sends emails to drive conversions. But not every customer responds the same way:

| Customer Type | Without Email | With Email | Should We Email? |
|---------------|--------------|------------|-----------------|
| **Persuadable** | Won't buy | Will buy | **Yes** |
| **Sure Thing** | Will buy | Will buy | No (waste of money) |
| **Lost Cause** | Won't buy | Won't buy | No (waste of money) |
| **Sleeping Dog** | Will buy | Won't buy | **Never** |

Traditional models optimize for "who is most likely to convert." Uplift models optimize for **"who is most likely to convert *because* of our intervention."**

---

## Key Findings

### The Loyalty Tax

Our T-Learner model correctly identifies Persuadables but suffers from a **calibration failure**: it ranks "Sure Things" (Decile 9) too highly because they have high treatment-group conversion — not because the email *caused* the conversion.

| Decile | Baseline Conv. | Incremental Lift | Profit | Verdict |
|--------|---------------|-----------------|--------|---------|
| **D8** | 0.32% | **+1.22pp** | **+$262** | True Persuadables |
| **D9** | **1.29%** | +0.24pp | **-$53** | Sure Things (Loyalty Tax) |

### Portfolio Surgery

Instead of a strict ranking cutoff, we **surgically exclude** the unprofitable Decile 9:

| Strategy | Profit |
|----------|--------|
| Spray & Pray (email everyone) | $872 |
| T-Learner strict ranking (90%) | $887 |
| **T-Learner + D9 exclusion** | **$921** |

This demonstrates that **uplift models require active human-in-the-loop auditing** — the optimal strategy isn't always the model's top recommendation.

---

## Project Structure

```
uplift-modeling/
├── notebooks/
│   ├── 01_eda_and_randomization.ipynb    # Phase 1: Data exploration & RCT validation
│   ├── 02_t_learner_implementation.ipynb # Phase 2: T-Learner model training
│   ├── 03_evaluation_qini.ipynb          # Phase 3: Qini curve evaluation
│   └── 04_business_simulation.ipynb      # Phase 4: ROI simulation & Loyalty Tax
├── streamlit_app/
│   ├── app.py                            # Phase 5: Interactive Model Auditor
│   ├── utils/
│   │   ├── calculations.py               # Profit & uplift calculations
│   │   └── charts.py                     # Plotly chart builders
│   └── data/                             # App data
├── data/                                 # Raw & processed datasets
├── models/                               # Trained model artifacts
└── requirements.txt                      # Python dependencies
```

---

## Phases

### Phase 1: Data Exploration & RCT Validation
- Loaded the Hillstrom dataset (64,000 customers, email A/B test)
- Validated randomization: treatment and control groups are balanced across all features
- Confirmed a statistically significant treatment effect on conversions

### Phase 2: T-Learner Implementation
- Built a T-Learner (two separate GradientBoosting models for treatment/control)
- Generated uplift scores: `uplift = P(convert | treated) - P(convert | control)`
- Identified top predictive features for uplift

### Phase 3: Model Evaluation (Qini Curves)
- Evaluated model using Qini curves and AUUC (Area Under Uplift Curve)
- T-Learner significantly outperforms random targeting
- Identified calibration anomaly in Decile 9

### Phase 4: Business Simulation & ROI
- Simulated ROI with realistic parameters ($0.10/email, $25/conversion)
- Discovered the "Loyalty Tax": Decile 9 loses $53 despite high baseline conversion
- Demonstrated that Portfolio Surgery (excluding D9) improves profit by $34

### Phase 5: Streamlit Model Auditor
- Interactive app with decile toggle checkboxes
- Real-time profit recalculation as user excludes/includes segments
- The "Aha!" moment: uncheck D9 and watch profit jump

---

## Interactive App

The Streamlit app is a **Model Auditor** — not just a dashboard, but a tool for evaluating and improving the model's targeting strategy.

**Features:**
- Adjustable business parameters (email cost, profit per conversion)
- Individual decile toggle checkboxes
- Toggle Impact Panel showing before/after profit delta
- ROI curve comparing strict ranking vs filtered portfolio
- Color-coded decile profitability chart (D9 in red)

**The "Aha!" Moment:**
1. Open the app — all deciles selected, profit = $887
2. Uncheck Decile 9
3. Profit jumps to $921
4. The model is *better* with human oversight

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11 |
| ML Models | scikit-learn (GradientBoostingClassifier) |
| Data | pandas, NumPy |
| Visualization | Matplotlib, Seaborn, Plotly |
| App | Streamlit |
| Dataset | Hillstrom Email Marketing (RCT) |

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/uplift-modeling.git
cd uplift-modeling

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
cd streamlit_app
streamlit run app.py
```

---

## Interview Talking Points

1. **"I discovered a structural bias in the T-Learner"** — It over-indexes on high-baseline customers because it conflates correlation with causation at the segment level.

2. **"I implemented Portfolio Surgery"** — Rather than trusting the model's strict ranking, I built a human-in-the-loop auditing tool that lets analysts surgically exclude unprofitable segments.

3. **"The insight isn't about Decile 9 specifically"** — It's that uplift models require guardrails on high-loyalty segments. In production, I'd implement a Safety Cap and 5% exploration group.

4. **"I used counterfactual projection"** — Revenue is estimated from RCT uplift rates projected to the full target population, not just the historically treated subset.

---

## License

MIT
