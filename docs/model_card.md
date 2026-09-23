# Model Card: Claim-Review Risk Score

## Project/Model Purpose

This is a claim-review risk scoring model designed to help analysts prioritize which claims should be reviewed first. It is part of the Care Operations Analytics portfolio project for a fictional Canadian care-services provider.

**Purpose**: Provide a transparent, interpretable prioritization aid for claim triage.

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
- **Model**: Logistic Regression with `class_weight="balanced"`
- **Preprocessing**: StandardScaler for numeric features
- **Split**: 75/25 train/test split with stratification
- **Seed**: Random seed = 42 (deterministic)

### Metrics
| Metric | Value |
|--------|-------|
| Precision | Model-dependent |
| Recall | Model-dependent |
| F1 Score | Model-dependent |
| ROC-AUC | Model-dependent |
| Confusion Matrix | Model-dependent |

**Note**: Metrics are calculated on a held-out test set. If the dataset does not support both classes, the model gracefully handles the edge case and returns no results.

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

## Ethical and Privacy Boundaries

- **No real data**: All data is synthetic. No privacy concerns exist.
- **No clinical decisions**: The model does not make or influence care decisions.
- **No automated decisions**: The model provides prioritization suggestions only.
- **No bias claims**: Synthetic data cannot be used to assess real-world bias.
- **Transparency**: All features, target definitions, and model parameters are documented.

---

## Why It Must Not Be Used as a Real Automated Decision Engine

1. **Synthetic data**: The model has no real-world validation.
2. **Interpretability limitations**: The reason summary is rule-based, not a true model explanation.
3. **No human oversight**: Automated claim decisions require human review and accountability.
4. **Regulatory compliance**: Real claims processing is subject to healthcare regulations that require human oversight.
5. **Ethical responsibility**: Care services involve vulnerable populations; automated decisions could cause harm.
6. **Purpose mismatch**: This model was designed for triage prioritization, not automated approval/rejection.

**This model is a portfolio demonstration tool. It must never be deployed as a production system.**
