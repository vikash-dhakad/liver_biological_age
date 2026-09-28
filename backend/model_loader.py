"""
Model Loader & Serializer Cache
================================
Deserializes model.pkl, preprocessor.pkl, and feature_names.json
from root or models/ directory into memory.
"""

import json
import math
import os
import pickle

def mean(lst):
    return sum(lst) / len(lst) if lst else 0.0

def std_dev(lst):
    m = mean(lst)
    variance = sum((x - m) ** 2 for x in lst) / len(lst)
    return math.sqrt(variance) if variance > 0 else 1.0

def pearson_r(x, y):
    n = len(x)
    if n == 0:
        return 0.0
    mx, my = mean(x), mean(y)
    sx, sy = std_dev(x), std_dev(y)
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / n
    return cov / (sx * sy)

class ScaledGradientBoostingRegressor:
    def __init__(self, n_estimators=20, lr=0.1):
        self.n_estimators = n_estimators
        self.lr = lr
        self.base_b = 0.0
        self.models = []

    def fit(self, X, y):
        pass

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
                raw_val = float(raw_protein_dict.get(feat, 0.0))
                log2_val = math.log2(raw_val + 1.0) if raw_val > 0 else 0.0
                m = self.means.get(feat, 0.0)
                s = self.stds.get(feat, 1.0)
                z_val = (log2_val - m) / s if s > 0 else 0.0
                vector.append(z_val)
        return vector

MODEL_CACHE = None
PREPROCESSOR_CACHE = None
FEATURE_NAMES_CACHE = None

def get_base_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_artifacts():
    global MODEL_CACHE, PREPROCESSOR_CACHE, FEATURE_NAMES_CACHE

    base_dir = get_base_dir()

    model_path = os.path.join(base_dir, "model.pkl")
    preprocessor_path = os.path.join(base_dir, "preprocessor.pkl")
    feature_names_path = os.path.join(base_dir, "feature_names.json")

    if not os.path.exists(model_path):
        model_path = os.path.join(base_dir, "models", "model.pkl")
        preprocessor_path = os.path.join(base_dir, "models", "preprocessor.pkl")
        feature_names_path = os.path.join(base_dir, "models", "feature_names.json")

    if MODEL_CACHE is None:
        with open(model_path, 'rb') as f:
            MODEL_CACHE = pickle.load(f)

    if PREPROCESSOR_CACHE is None:
        with open(preprocessor_path, 'rb') as f:
            PREPROCESSOR_CACHE = pickle.load(f)

    if FEATURE_NAMES_CACHE is None:
        with open(feature_names_path, 'r', encoding='utf-8') as f:
            FEATURE_NAMES_CACHE = json.load(f)

    return MODEL_CACHE, PREPROCESSOR_CACHE, FEATURE_NAMES_CACHE
