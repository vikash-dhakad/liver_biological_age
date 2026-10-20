import os
import sys
import json
import math
import pickle
from datetime import datetime
from pathlib import Path
from django.conf import settings

ROOT_DIR = Path(settings.BASE_DIR).parent

class ScaledGradientBoostingRegressor:
    def __init__(self, n_estimators=20, lr=0.1):
        self.n_estimators = n_estimators
        self.lr = lr
        self.base_b = 0.0
        self.models = []

    def predict(self, X):
        n_samples = len(X)
        preds = [self.base_b] * n_samples
        for i in range(n_samples):
            for (feat, weight) in self.models:
                preds[i] += weight * X[i][feat]
        return preds

class ScaledPreprocessor:
    def __init__(self, feature_names, means, stds):
        self.feature_names = feature_names
        self.means = means
        self.stds = stds

    def transform_single(self, gender_val, raw_protein_dict):
        vector = []
        for feat in self.feature_names:
            if feat == "gender":
                vector.append(1.0 if str(gender_val).lower() in ["male", "1", "m"] else 0.0)
            else:
                try:
                    val = raw_protein_dict.get(feat, 0.0)
                    raw_val = float(val) if val is not None and str(val).strip() != '' else 0.0
                except (ValueError, TypeError):
                    raw_val = 0.0
                if abs(raw_val) < 20.0 and raw_val != 0.0:
                    z_val = raw_val
                elif raw_val > 0:
                    log2_val = math.log2(raw_val + 1.0)
                    m = self.means.get(feat, 0.0)
                    s = self.stds.get(feat, 1.0)
                    z_val = (log2_val - m) / s if s > 0 else 0.0
                else:
                    z_val = 0.0
                vector.append(z_val)
        return vector

class MLUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == 'ScaledGradientBoostingRegressor':
            return ScaledGradientBoostingRegressor
        if name == 'ScaledPreprocessor':
            return ScaledPreprocessor
        return super().find_class(module, name)

def calculate_chronological_age(dob_str):
    if not dob_str:
        return 45.0
    try:
        dob = datetime.strptime(str(dob_str)[:10], "%Y-%m-%d")
        today = datetime.now()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return float(age)
    except Exception:
        try:
            return float(dob_str)
        except Exception:
            return 45.0

def determine_risk_category(chronological_age, predicted_age):
    diff = predicted_age - chronological_age
    if diff <= -3.0:
        return {
            "category": "Healthy / Young Liver",
            "code": "HEALTHY",
            "description": f"Your liver biological age looks like a {predicted_age:.0f}-year-old liver ({abs(diff):.1f} years younger than your actual chronological age!).",
            "badge_class": "badge-healthy"
        }
    elif diff >= 4.0:
        return {
            "category": "Accelerated Aging Risk",
            "code": "ACCELERATED",
            "description": f"Your liver biological age looks like a {predicted_age:.0f}-year-old liver ({diff:.1f} years older than your actual chronological age). Lifestyle/clinical evaluation recommended.",
            "badge_class": "badge-accelerated"
        }
    else:
        return {
            "category": "Normal Aging Pattern",
            "code": "NORMAL",
            "description": f"Your liver biological age looks like a {predicted_age:.0f}-year-old liver (closely matching your chronological age).",
            "badge_class": "badge-normal"
        }

class MLService:
    _instance = None
    model = None
    preprocessor = None
    feature_names = None
    protein_metadata = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load_artifacts()
        return cls._instance

    def load_artifacts(self):
        import __main__
        __main__.ScaledGradientBoostingRegressor = ScaledGradientBoostingRegressor
        __main__.ScaledPreprocessor = ScaledPreprocessor

        model_path = os.path.join(ROOT_DIR, "model.pkl")
        preprocessor_path = os.path.join(ROOT_DIR, "preprocessor.pkl")
        feature_names_path = os.path.join(ROOT_DIR, "feature_names.json")
        metadata_path = os.path.join(ROOT_DIR, "protein_metadata.json")

        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = MLUnpickler(f).load()
        
        if os.path.exists(preprocessor_path):
            with open(preprocessor_path, 'rb') as f:
                self.preprocessor = MLUnpickler(f).load()

        if os.path.exists(feature_names_path):
            with open(feature_names_path, 'r', encoding='utf-8') as f:
                self.feature_names = json.load(f)
        else:
            self.feature_names = []

        self.protein_metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                raw_meta = json.load(f)
                if isinstance(raw_meta, list):
                    for item in raw_meta:
                        if isinstance(item, dict) and "name" in item:
                            self.protein_metadata[item["name"]] = item
                elif isinstance(raw_meta, dict):
                    self.protein_metadata = raw_meta

    def predict_single(self, gender, dob, protein_inputs, chrono_age=None, patient_name="Anonymous"):
        if self.preprocessor is None or self.model is None:
            self.load_artifacts()

        if chrono_age is None:
            chrono_age = calculate_chronological_age(dob)

        input_vector = self.preprocessor.transform_single(gender, protein_inputs)
        raw_pred = self.model.predict([input_vector])[0]

        baseline = self.model.base_b if hasattr(self.model, 'base_b') and self.model.base_b > 0 else 44.26
        raw_delta = (raw_pred - baseline) / 8.0
        bounded_delta = max(-14.0, min(14.0, raw_delta))

        predicted_age = round(max(18.0, min(85.0, chrono_age + bounded_delta)), 1)
        age_diff = round(predicted_age - chrono_age, 1)
        risk_info = determine_risk_category(chrono_age, predicted_age)

        shap_contributions = []
        for (j, weight) in getattr(self.model, 'models', []):
            if j < len(self.feature_names):
                feat_name = self.feature_names[j]
                val = input_vector[j]
                contrib = (weight * val) / 8.0
                meta = self.protein_metadata.get(feat_name, {})
                shap_contributions.append({
                    "feature": feat_name,
                    "val": val,
                    "shap_value": round(float(contrib), 4),
                    "importance": round(float(contrib), 4),
                    "impact": "Increases Age" if contrib > 0 else "Decreases Age",
                    "full_name": meta.get("full_name", feat_name),
                    "uniprot_id": meta.get("uniprot_id", "N/A"),
                    "function": meta.get("function", "Proteomic aging biomarker"),
                    "biological_impact": meta.get("biological_impact", "Modulates liver metabolic aging"),
                    "direction": "accelerates" if contrib > 0 else "protective"
                })

        unique_shap = {}
        for item in shap_contributions:
            f = item["feature"]
            if f not in unique_shap or abs(item["shap_value"]) > abs(unique_shap[f]["shap_value"]):
                unique_shap[f] = item

        shap_sorted = sorted(list(unique_shap.values()), key=lambda x: abs(x["shap_value"]), reverse=True)

        return {
            "patient_name": patient_name or "Anonymous Patient",
            "gender": "Male" if str(gender).lower() in ["male", "1", "m"] else "Female",
            "dob": dob,
            "chronological_age": round(chrono_age, 1),
            "predicted_biological_age": predicted_age,
            "predicted_age": predicted_age,
            "age_difference": age_diff,
            "baseline_mean_age": round(baseline, 1),
            "risk_category": risk_info["category"],
            "risk_description": risk_info["description"],
            "badge_class": risk_info["badge_class"],
            "top_shap_contributions": shap_sorted[:15],
            "shap_contributions": shap_sorted[:15],
            "protein_values": protein_inputs
        }
