"""
Production Zero-Dependency Python HTTP Web & API Server
========================================================
Runs out-of-the-box on standard Python 3 with built-in http.server, sqlite3, json, pickle, and math.
Provides web UI and all REST API endpoints on http://localhost:5000.
"""

import csv
import io
import json
import math
import os
import pickle
import sqlite3
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# Core Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
DB_PATH = os.path.join(os.path.dirname(__file__), "predictions.db")

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

MODEL_CACHE = None
PREPROCESSOR_CACHE = None
FEATURE_NAMES_CACHE = None

def load_artifacts():
    global MODEL_CACHE, PREPROCESSOR_CACHE, FEATURE_NAMES_CACHE
    if MODEL_CACHE is None:
        model_path = os.path.join(BASE_DIR, "model.pkl")
        preprocessor_path = os.path.join(BASE_DIR, "preprocessor.pkl")
        feature_names_path = os.path.join(BASE_DIR, "feature_names.json")

        with open(model_path, 'rb') as f:
            MODEL_CACHE = pickle.load(f)
        with open(preprocessor_path, 'rb') as f:
            PREPROCESSOR_CACHE = pickle.load(f)
        with open(feature_names_path, 'r', encoding='utf-8') as f:
            FEATURE_NAMES_CACHE = json.load(f)

    return MODEL_CACHE, PREPROCESSOR_CACHE, FEATURE_NAMES_CACHE

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT DEFAULT 'Anonymous',
            gender TEXT NOT NULL,
            dob TEXT,
            chronological_age REAL NOT NULL,
            predicted_age REAL NOT NULL,
            age_difference REAL NOT NULL,
            risk_category TEXT NOT NULL,
            protein_values TEXT NOT NULL,
            shap_contributions TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_prediction_db(patient_name, gender, dob, chronological_age, predicted_age, age_difference, risk_category, protein_values, shap_contributions):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions (patient_name, gender, dob, chronological_age, predicted_age, age_difference, risk_category, protein_values, shap_contributions, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_name, gender, dob, chronological_age, predicted_age, age_difference, risk_category,
        json.dumps(protein_values), json.dumps(shap_contributions), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    prediction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return prediction_id

def get_all_predictions_db(search_query=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if search_query:
        query = "%" + search_query + "%"
        cursor.execute("SELECT * FROM predictions WHERE patient_name LIKE ? OR risk_category LIKE ? OR gender LIKE ? ORDER BY id DESC", (query, query, query))
    else:
        cursor.execute("SELECT * FROM predictions ORDER BY id DESC")

    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "patient_name": r["patient_name"],
            "gender": r["gender"],
            "dob": r["dob"],
            "chronological_age": r["chronological_age"],
            "predicted_age": r["predicted_age"],
            "age_difference": r["age_difference"],
            "risk_category": r["risk_category"],
            "protein_values": json.loads(r["protein_values"]),
            "shap_contributions": json.loads(r["shap_contributions"]),
            "created_at": r["created_at"]
        })
    conn.close()
    return results

def get_prediction_by_id_db(prediction_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"],
            "patient_name": row["patient_name"],
            "gender": row["gender"],
            "dob": row["dob"],
            "chronological_age": row["chronological_age"],
            "predicted_age": row["predicted_age"],
            "age_difference": row["age_difference"],
            "risk_category": row["risk_category"],
            "protein_values": json.loads(row["protein_values"]),
            "shap_contributions": json.loads(row["shap_contributions"]),
            "created_at": row["created_at"]
        }
    return None

def delete_prediction_db(prediction_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions WHERE id = ?", (prediction_id,))
    conn.commit()
    conn.close()

def calculate_chronological_age(dob_str):
    if not dob_str:
        return 45.0
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return float(age)
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

def predict_single(patient_name, gender, dob, protein_inputs):
    model, preprocessor, feature_names = load_artifacts()
    chrono_age = calculate_chronological_age(dob)

    input_vector = preprocessor.transform_single(gender, protein_inputs)
    raw_pred = model.predict([input_vector])[0]

    baseline = model.base_b if hasattr(model, 'base_b') and model.base_b > 0 else 44.26
    raw_delta = (raw_pred - baseline) / 8.0
    bounded_delta = max(-14.0, min(14.0, raw_delta))

    predicted_age = round(max(18.0, min(85.0, chrono_age + bounded_delta)), 1)
    age_diff = round(predicted_age - chrono_age, 1)
    risk_info = determine_risk_category(chrono_age, predicted_age)

    shap_contributions = []
    for (j, weight) in model.models:
        feat_name = feature_names[j]
        val = input_vector[j]
        contrib = (weight * val) / 8.0
        shap_contributions.append({
            "feature": feat_name,
            "val": val,
            "shap_value": round(float(contrib), 4),
            "impact": "Increases Age" if contrib > 0 else "Decreases Age"
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
        "age_difference": age_diff,
        "baseline_mean_age": round(baseline, 1),
        "risk_category": risk_info["category"],
        "risk_description": risk_info["description"],
        "badge_class": risk_info["badge_class"],
        "top_shap_contributions": shap_sorted[:15],
        "protein_values": protein_inputs
    }

class ServerHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_html(self, html_content, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def _send_static(self, filepath, mime_type):
        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.end_headers()
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "File Not Found")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self._send_static(os.path.join(FRONTEND_DIR, "index.html"), "text/html")
        elif path.startswith("/css/"):
            self._send_static(os.path.join(FRONTEND_DIR, path[1:]), "text/css")
        elif path.startswith("/js/"):
            self._send_static(os.path.join(FRONTEND_DIR, path[1:]), "application/javascript")
        elif path == "/api/feature-schema":
            model, preprocessor, feature_names = load_artifacts()
            proteins = [f for f in feature_names if f != "gender"]
            self._send_json({"success": True, "proteins": proteins})
        elif path == "/api/history":
            q = query_params.get("q", [""])[0]
            records = get_all_predictions_db(search_query=q if q else None)
            self._send_json({"success": True, "count": len(records), "data": records})
        elif path.startswith("/api/download-report/"):
            rec_id = int(path.split("/")[-1])
            rec = get_prediction_by_id_db(rec_id)
            if rec:
                from report_generator import generate_html_report
                html = generate_html_report(rec)
                self._send_html(html)
            else:
                self.send_error(404, "Report Record Not Found")
        elif path == "/api/export-history":
            records = get_all_predictions_db()
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Patient Name", "Gender", "DOB", "Chronological Age", "Predicted Biological Age", "Age Difference", "Risk Category", "Date Created"])
            for r in records:
                writer.writerow([r["id"], r["patient_name"], r["gender"], r["dob"], r["chronological_age"], r["predicted_age"], r["age_difference"], r["risk_category"], r["created_at"]])

            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", "attachment;filename=liver_prediction_history.csv")
            self.end_headers()
            self.wfile.write(output.getvalue().encode("utf-8"))
        else:
            self.send_error(404, "Endpoint Not Found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

            if path == "/api/predict":
                data = json.loads(body)
                p_name = data.get("patient_name", "Anonymous Patient")
                gender = data.get("gender", "Female")
                dob = data.get("dob", "")
                protein_inputs = data.get("protein_inputs", {})

                result = predict_single(p_name, gender, dob, protein_inputs)

                pid = save_prediction_db(
                    result["patient_name"], result["gender"], result["dob"],
                    result["chronological_age"], result["predicted_biological_age"],
                    result["age_difference"], result["risk_category"],
                    result["protein_values"], result["top_shap_contributions"]
                )
                result["id"] = pid
                self._send_json({"success": True, "data": result})
            else:
                self._send_json({"success": False, "error": "Endpoint not found"}, 404)
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, 500)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/history/"):
            rec_id = int(path.split("/")[-1])
            delete_prediction_db(rec_id)
            self._send_json({"success": True})

def main():
    init_db()
    load_artifacts()
    port = int(os.environ.get('PORT', 5000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, ServerHandler)
    print("======================================================================")
    print(" LIVER BIOLOGICAL AGE PREDICTOR WEB APP RUNNING                      ")
    print("======================================================================\n")
    print(f" Access Web Application UI: http://localhost:{port}\n")
    httpd.serve_forever()

if __name__ == '__main__':
    main()
