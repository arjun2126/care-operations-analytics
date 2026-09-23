import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix,
)
from src.feature_engineering import build_risk_features, get_risk_feature_columns, encode_categorical_features
from src.config import config

RANDOM_SEED = config.random_seed
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
MODEL_PATH = os.path.join(PROCESSED_DIR, "risk_model")
METRICS_PATH = os.path.join(PROCESSED_DIR, "risk_model_metrics.csv")
SCORES_PATH = os.path.join(PROCESSED_DIR, "risk_scores.csv")


def _load_claims_data() -> pd.DataFrame:
    claims_path = os.path.join(PROCESSED_DIR, "claims.csv")
    visits_path = os.path.join(PROCESSED_DIR, "service_visits.csv")
    funders_path = os.path.join(PROCESSED_DIR, "funders.csv")

    if not all(os.path.exists(p) for p in [claims_path, visits_path, funders_path]):
        return pd.DataFrame()

    claims = pd.read_csv(claims_path)
    visits = pd.read_csv(visits_path)
    funders = pd.read_csv(funders_path)

    merged = claims.merge(
        visits[["visit_id", "service_type", "completed_hours", "scheduled_hours", "hourly_rate"]],
        on="visit_id", how="left",
    )
    merged = merged.merge(
        funders[["funder_id", "funding_type"]], on="funder_id", how="left",
    )
    return merged


def _build_model_data() -> "Optional[Tuple[pd.DataFrame, pd.Series, pd.DataFrame]]":
    claims = _load_claims_data()
    if claims.empty or len(claims) < 10:
        return None

    df = build_risk_features(claims)
    if df.empty:
        return None

    feature_cols = get_risk_feature_columns()
    existing_features = [c for c in feature_cols if c in df.columns]

    df_encoded = encode_categorical_features(df)
    available_features = [c for c in existing_features if c in df_encoded.columns]

    if len(available_features) < 2:
        return None

    X = df_encoded[available_features].fillna(0)
    y = df_encoded["is_high_risk_target"].astype(int)

    if y.sum() == 0 or y.sum() == len(y):
        return None

    return X, y, df_encoded


def train_model() -> "Optional[dict]":
    result = _build_model_data()
    if result is None:
        return None

    X, y, df_encoded = result
    feature_cols = [c for c in X.columns]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(
        class_weight="balanced",
        random_state=RANDOM_SEED,
        max_iter=1000,
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    metrics = {
        "precision": round(precision_score(y_test, y_pred), 4),
        "recall": round(recall_score(y_test, y_pred), 4),
        "f1": round(f1_score(y_test, y_pred), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4) if len(set(y_test)) == 2 else None,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "positive_class_count": int(y.sum()),
        "negative_class_count": int(len(y) - y.sum()),
        "feature_count": len(feature_cols),
    }

    cm = confusion_matrix(y_test, y_pred)
    metrics["confusion_matrix_tn"] = int(cm[0][0])
    metrics["confusion_matrix_fp"] = int(cm[0][1])
    metrics["confusion_matrix_fn"] = int(cm[1][0])
    metrics["confusion_matrix_tp"] = int(cm[1][1])

    return {
        "model": model,
        "scaler": scaler,
        "feature_cols": feature_cols,
        "metrics": metrics,
        "df_encoded": df_encoded,
    }


def generate_risk_scores() -> "Optional[pd.DataFrame]":
    result = _build_model_data()
    if result is None:
        return None

    X, y, df_encoded = result
    model_data = train_model()
    if model_data is None:
        return None

    model = model_data["model"]
    scaler = model_data["scaler"]
    feature_cols = model_data["feature_cols"]

    X_scaled = scaler.transform(X[feature_cols].fillna(0))
    risk_scores = model.predict_proba(X_scaled)[:, 1]

    df_encoded["risk_score"] = np.round(risk_scores, 4)
    df_encoded["risk_band"] = pd.cut(
        df_encoded["risk_score"],
        bins=[-0.01, 0.35, 0.65, 1.01],
        labels=["Low", "Medium", "High"],
        right=True,
    ).astype(str)

    reason_parts = []
    if "documentation_delay_days" in df_encoded.columns:
        reason_parts.append(pd.cut(
            df_encoded["documentation_delay_days"].fillna(0),
            bins=[-1, 0, 5, 15, 100],
            labels=["No delay", "Minor delay (1-5d)", "Moderate delay (6-15d)", "Severe delay (>15d)"],
        ).astype(str))
    if "submitted_late_flag" in df_encoded.columns:
        reason_parts.append(df_encoded["submitted_late_flag"].map({True: "Late submission", False: "On-time"}).astype(str))
    if "duplicate_candidate_flag" in df_encoded.columns:
        reason_parts.append(df_encoded["duplicate_candidate_flag"].map({True: "Duplicate candidate", False: "No duplicate flag"}).astype(str))
    if "claim_amount" in df_encoded.columns:
        reason_parts.append(pd.cut(
            df_encoded["claim_amount"].fillna(0),
            bins=[-1, 0, 200, 500, 10000],
            labels=["Low value", "Medium value", "High value", "Very high value"],
        ).astype(str))
    if "funding_type" in df_encoded.columns:
        reason_parts.append(df_encoded["funding_type"].fillna("Unknown").map({
            "Provincial": "Provincial funder", "Federal": "Federal funder",
            "Municipal": "Municipal funder", "Private Insurance": "Private insurance",
            "Unknown": "Unknown funder"
        }).astype(str))

    reason_df = pd.DataFrame({f"part_{i}": part for i, part in enumerate(reason_parts)})
    df_encoded["reason_summary"] = reason_df.apply(lambda row: "; ".join([str(v) for v in row if str(v) != "nan"]), axis=1)
    df_encoded["reason_summary"] = df_encoded["reason_summary"].replace("", "Standard review")

    output = df_encoded[[
        "claim_id", "client_id", "funder_id", "claim_amount", "claim_status",
        "risk_score", "risk_band", "reason_summary", "is_high_risk_target",
    ]].copy()
    output["risk_score"] = output["risk_score"].round(4)

    return output


def save_model_outputs() -> dict:
    model_data = train_model()
    if model_data is None:
        return {"success": False, "error": "Could not build model data"}

    risk_df = generate_risk_scores()
    if risk_df is None:
        return {"success": False, "error": "Could not generate risk scores"}

    try:
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        joblib.dump(model_data["model"], MODEL_PATH + ".joblib")
        joblib.dump(model_data["scaler"], PROCESSED_DIR + "/risk_scaler.joblib")
        risk_df.to_csv(SCORES_PATH, index=False)

        metrics_df = pd.DataFrame([model_data["metrics"]])
        metrics_df.to_csv(METRICS_PATH, index=False)

        return {
            "success": True,
            "metrics": model_data["metrics"],
            "risk_df": risk_df,
            "model_path": MODEL_PATH + ".joblib",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_risk_model():
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    logger.info("Starting claim-review risk model...")
    result = save_model_outputs()

    if result["success"]:
        m = result["metrics"]
        logger.info(f"Risk model complete: Precision={m['precision']}, Recall={m['recall']}, F1={m['f1']}, ROC-AUC={m['roc_auc']}")
        logger.info(f"Risk scores saved to {SCORES_PATH}")
        high = result['risk_df'][result['risk_df']['risk_band'] == 'High'].shape[0]
        med = result['risk_df'][result['risk_df']['risk_band'] == 'Medium'].shape[0]
        low = result['risk_df'][result['risk_df']['risk_band'] == 'Low'].shape[0]
        logger.info(f"High-risk claims: {high}, Medium-risk: {med}, Low-risk: {low}")
    else:
        logger.error(f"Risk model failed: {result.get('error', 'Unknown error')}")
        logger.info("Ensure processed data files exist by running: python -m src.pipeline")


if __name__ == "__main__":
    run_risk_model()