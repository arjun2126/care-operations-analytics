# Model Card: Claim-Review Risk Score

## Project/Model Purpose

A claim-review risk score that helps analysts decide which claims to look at first. It is part of the Care Operations Analytics portfolio project for a fictional Canadian care-services provider.

---

## Intended Use and Non-Intended Use

### Intended Use
- Prioritizing claims for analyst review
- Identifying high-value, high-risk claims for manual inspection
- Supporting data-driven decision-making in a consulting context
- Portfolio demonstration of analytical capabilities

### Non-Intended Use
- **NOT** an automated approval/rejection system
- **NOT** a clinical model or care decision tool
- **NOT** a production deployment
- **NOT** a tool for determining individual client eligibility
- **NOT** a replacement for human analyst judgment

---

## Synthetic Data Statement

All data used to train, evaluate, and deploy this model is entirely synthetic and fictional. No real personal, healthcare, client, employee, or company data is used. The data was generated using the Faker library configured for Canadian locale. This model must not be applied to real-world data without significant modification and validation.

---

## Target Definition

**Target**: `is_high_risk_target` = 1 if **any** of the following is true:
1. `claim_status` == "Rejected"
2. `duplicate_candidate_flag` == True

**Target = 0** otherwise (Approved or Pending Review without duplicate flag).

**Rationale**: This definition captures claims that either failed the claims process or have documented risk indicators. It represents a defensible, pre-decision label based on available synthetic fields.

**Note**: The target combines rejection status and duplicate flag. In a production setting, these would be separate review triggers.

---

## Input Features

| Feature | Description | Type |
|---------|-------------|------|
| `log_claim_amount` | Log-transformed claim amount | Numeric |
| `claim_amount_per_hour` | Claim amount divided by completed hours | Numeric |
| `hours_variance_pct` | Percentage difference between completed and scheduled hours | Numeric |
| `has_late_submission` | Whether claim was submitted late | Binary |
| `has_duplicate_flag` | Whether claim is flagged as duplicate candidate | Binary |
| `doc_delay_days` | Documentation delay days | Integer |
| `funding_type` | Funder funding category (one-hot encoded) | Categorical |
| `service_type` | Type of care service (one-hot encoded) | Categorical |

### Features NOT Used (Leakage Prevention)
- `rejection_reason` — Directly reveals outcome
- `exception_status` / `exception_type` — Post-decision fields
- Any field that would be unknown at review time

---

## Evaluation Method and Metrics

### Method
- **Model**: Logistic Regression with `class_weight="balanced"` in a sklearn Pipeline
- **Preprocessing**: ColumnTransformer with StandardScaler for numeric features and OneHotEncoder(handle_unknown="ignore") for categorical features
- **Split**: 75/25 train/test split with stratification
- **Seed**: Random seed = 42 (deterministic)

### Metrics (test set)
| Metric | Value |
|--------|-------|
| Precision | 0.632 |
| Recall | 0.299 |
| F1 Score | 0.406 |
| ROC-AUC | 0.675 |
| Train samples | 5,442 |
| Test samples | 1,815 |
| Positive class | 1,057 |
| Negative class | 6,200 |
| Confusion matrix | TN=1,505, FP=46, FN=185, TP=79 |

**Note**: The model has modest recall, meaning it identifies a limited proportion of actual high-risk claims. This is expected with synthetic data and a balanced model prioritizing interpretability over raw performance.

---

## Explainability Approach

The model uses **LogisticRegression** which is inherently interpretable:
- Each feature has a coefficient indicating its contribution to the risk score
- Risk scores range from 0 to 1
- Risk bands: Low (< 0.35), Medium (0.35–0.65), High (≥ 0.65)
- A human-readable `reason_summary` is generated from feature values (e.g., "Late submission; High value; Provincial funder")

**Important**: The reason summary is a rule-based approximation, not a model explanation. It describes contributing factors, not feature coefficients.

---

## Limitations

1. **Synthetic data**: The model is trained on fictional data and cannot be applied to real-world scenarios without significant modification.
2. **Small sample**: With ~7,257 claims and ~752 rejected, some classes have limited representation.
3. **Single year**: Data spans only 2024; temporal patterns cannot be validated.
4. **Simplified target**: The target combines rejection and duplicate flag; real-world review triggers may be more nuanced.
5. **No temporal validation**: The train/test split is random, not time-based.
6. **Feature limitations**: Some features (e.g., funding utilization) are simplified due to synthetic data constraints.
7. **Class imbalance**: Despite using `class_weight="balanced"`, the minority class may still be underrepresented.

---

## Why This Is Not a Real Decision Engine

The points above are worth repeating in one place because they are the most important caveats:

1. **Synthetic data**: The model has no real-world validation.
2. **No human oversight**: Automated claim decisions require human review and accountability.
3. **Regulatory and ethical responsibility**: Real claims processing is regulated and involves vulnerable populations; automated decisions are not acceptable.
4. **Purpose mismatch**: It was designed for triage prioritization, not automated approval or rejection.

There is no real data, no real client, and no production deployment behind this model. It makes no clinical or automated decisions. Privacy is not a concern because every record is fictional.

**This is a portfolio demonstration. It must never be deployed as a production system.**
