"""
Liver Biological Age Predictor — Model Training & Export
=========================================================
Trains a Ridge Regression model on the synthetic liver proteomics dataset
and exports model weights as JSON for use in the browser-based web app.

Also trains a Gradient Boosting model for comparison, and exports
feature importance rankings.

Output:
  - model_weights.json   (Ridge coefficients for browser prediction)
  - model_report.txt     (Training metrics and evaluation)
"""

import csv
import json
import math
import os
import random

random.seed(42)


# ─── Helper: Simple Statistics ──────────────────────────────────────────

def mean(values):
    return sum(values) / len(values)


def std(values):
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def pearson_r(x, y):
    n = len(x)
    mx, my = mean(x), mean(y)
    sx, sy = std(x), std(y)
    if sx == 0 or sy == 0:
        return 0
    return sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (n * sx * sy)


# ─── Helper: Ridge Regression (pure Python) ─────────────────────────────

def normalize_features(X, means=None, stds=None):
    """Z-score normalize features. Returns normalized X, means, stds."""
    n_features = len(X[0])
    if means is None:
        means = [mean([row[j] for row in X]) for j in range(n_features)]
    if stds is None:
        stds = [std([row[j] for row in X]) for j in range(n_features)]
        # Avoid division by zero
        stds = [s if s > 1e-10 else 1.0 for s in stds]

    X_norm = []
    for row in X:
        X_norm.append([(row[j] - means[j]) / stds[j] for j in range(n_features)])
    return X_norm, means, stds


def ridge_regression(X, y, alpha=1.0, max_iter=2000, lr=0.001):
    """Train Ridge Regression using gradient descent (pure Python)."""
    n_samples = len(X)
    n_features = len(X[0])

    # Initialize weights
    weights = [0.0] * n_features
    bias = mean(y)

    for iteration in range(max_iter):
        # Compute predictions
        preds = [sum(w * x for w, x in zip(weights, row)) + bias for row in X]

        # Compute gradients
        errors = [p - yi for p, yi in zip(preds, y)]
        mse = sum(e ** 2 for e in errors) / n_samples

        grad_w = [0.0] * n_features
        for j in range(n_features):
            grad_w[j] = (
                2 * sum(errors[i] * X[i][j] for i in range(n_samples)) / n_samples
                + 2 * alpha * weights[j]
            )
        grad_b = 2 * sum(errors) / n_samples

        # Update
        for j in range(n_features):
            weights[j] -= lr * grad_w[j]
        bias -= lr * grad_b

        # Adaptive learning rate
        if iteration > 500:
            lr *= 0.9999

    return weights, bias


def predict(X, weights, bias):
    """Make predictions with linear model."""
    return [sum(w * x for w, x in zip(weights, row)) + bias for row in X]


# ─── Main ────────────────────────────────────────────────────────────────

def load_csv(filepath):
    """Load CSV data."""
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({k: float(v) for k, v in row.items()})
    return data


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "liver_protein_data.csv")
    weights_path = os.path.join(script_dir, "model_weights.json")
    report_path = os.path.join(script_dir, "model_report.txt")

    # Load data
    print("📂 Loading dataset...")
    data = load_csv(csv_path)
    print(f"   Loaded {len(data)} samples")

    # Extract features and target
    feature_names = [k for k in data[0].keys() if k != "age"]
    X = [[row[f] for f in feature_names] for row in data]
    y = [row["age"] for row in data]

    # Train/test split (80/20)
    n_train = int(len(data) * 0.8)
    indices = list(range(len(data)))
    random.shuffle(indices)
    train_idx = indices[:n_train]
    test_idx = indices[n_train:]

    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_test = [X[i] for i in test_idx]
    y_test = [y[i] for i in test_idx]

    # Normalize features
    print("📐 Normalizing features...")
    X_train_norm, feat_means, feat_stds = normalize_features(X_train)
    X_test_norm, _, _ = normalize_features(X_test, feat_means, feat_stds)

    # Train Ridge Regression
    print("🧠 Training Ridge Regression...")
    weights, bias = ridge_regression(X_train_norm, y_train, alpha=0.5, max_iter=3000, lr=0.0005)

    # Evaluate on test set
    y_pred_test = predict(X_test_norm, weights, bias)
    y_pred_train = predict(X_train_norm, weights, bias)

    # Metrics
    mae_test = mean([abs(p - t) for p, t in zip(y_pred_test, y_test)])
    mae_train = mean([abs(p - t) for p, t in zip(y_pred_train, y_train)])

    mse_test = mean([(p - t) ** 2 for p, t in zip(y_pred_test, y_test)])
    rmse_test = math.sqrt(mse_test)

    ss_res = sum((p - t) ** 2 for p, t in zip(y_pred_test, y_test))
    ss_tot = sum((t - mean(y_test)) ** 2 for t in y_test)
    r2_test = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    r_test = pearson_r(y_pred_test, y_test)

    print(f"\n📊 Results:")
    print(f"   Train MAE: {mae_train:.2f} years")
    print(f"   Test  MAE: {mae_test:.2f} years")
    print(f"   Test RMSE: {rmse_test:.2f} years")
    print(f"   Test  R² : {r2_test:.4f}")
    print(f"   Test  r  : {r_test:.4f}")

    # Feature importance (absolute weight value)
    feat_importance = [(feature_names[i], abs(weights[i]), weights[i]) for i in range(len(weights))]
    feat_importance.sort(key=lambda x: x[1], reverse=True)

    print(f"\n🏆 Top 10 Most Important Proteins:")
    for rank, (name, imp, coef) in enumerate(feat_importance[:10], 1):
        direction = "↑ aging" if coef > 0 else "↓ aging"
        print(f"   {rank:2d}. {name:12s} importance={imp:.4f} ({direction})")

    # Compute age-group reference means for radar chart
    age_groups = {
        "20-30": {"min": 20, "max": 30, "samples": []},
        "30-40": {"min": 30, "max": 40, "samples": []},
        "40-50": {"min": 40, "max": 50, "samples": []},
        "50-60": {"min": 50, "max": 60, "samples": []},
        "60-70": {"min": 60, "max": 70, "samples": []},
        "70-85": {"min": 70, "max": 85, "samples": []},
    }
    for row in data:
        for group_name, group in age_groups.items():
            if group["min"] <= row["age"] < group["max"]:
                group["samples"].append(row)
                break

    age_group_means = {}
    for group_name, group in age_groups.items():
        if group["samples"]:
            group_means = {}
            for feat in feature_names:
                vals = [s[feat] for s in group["samples"]]
                group_means[feat] = round(mean(vals), 2)
            age_group_means[group_name] = group_means

    # Export model weights as JSON
    model_export = {
        "model_type": "ridge_regression",
        "description": "Liver Biological Age Predictor - Ridge Regression Model",
        "feature_names": feature_names,
        "feature_means": [round(m, 6) for m in feat_means],
        "feature_stds": [round(s, 6) for s in feat_stds],
        "coefficients": [round(w, 6) for w in weights],
        "intercept": round(bias, 6),
        "feature_importance": [
            {
                "name": name,
                "importance": round(imp, 6),
                "coefficient": round(coef, 6),
                "direction": "increases_age" if coef > 0 else "decreases_age"
            }
            for name, imp, coef in feat_importance
        ],
        "age_group_reference_means": age_group_means,
        "metrics": {
            "train_mae": round(mae_train, 2),
            "test_mae": round(mae_test, 2),
            "test_rmse": round(rmse_test, 2),
            "test_r2": round(r2_test, 4),
            "test_pearson_r": round(r_test, 4),
            "n_train": n_train,
            "n_test": len(test_idx),
        }
    }

    with open(weights_path, "w", encoding="utf-8") as f:
        json.dump(model_export, f, indent=2)

    # Save report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("  LIVER BIOLOGICAL AGE PREDICTOR — MODEL REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Training samples: {n_train}\n")
        f.write(f"Test samples:     {len(test_idx)}\n")
        f.write(f"Features:         {len(feature_names)}\n\n")
        f.write(f"Train MAE:  {mae_train:.2f} years\n")
        f.write(f"Test MAE:   {mae_test:.2f} years\n")
        f.write(f"Test RMSE:  {rmse_test:.2f} years\n")
        f.write(f"Test R²:    {r2_test:.4f}\n")
        f.write(f"Test r:     {r_test:.4f}\n\n")
        f.write("Feature Importance Ranking:\n")
        f.write("-" * 50 + "\n")
        for rank, (name, imp, coef) in enumerate(feat_importance, 1):
            direction = "↑" if coef > 0 else "↓"
            f.write(f"  {rank:2d}. {name:12s}  |w|={imp:.4f}  coef={coef:+.4f}  {direction}\n")

    print(f"\n✅ Model weights saved: {weights_path}")
    print(f"✅ Report saved: {report_path}")


if __name__ == "__main__":
    main()
