"""
Flask REST API Primary Server
=============================
Provides production REST API endpoints for single prediction, batch CSV processing,
history management, and report generation.
"""

import csv
import io
import json
import os
from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

from database import delete_prediction, get_all_predictions, get_prediction_by_id, save_prediction
from model_loader import load_artifacts
from predict import predict_single_patient
from report_generator import generate_html_report

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/api/feature-schema", methods=["GET"])
def get_feature_schema():
    model, preprocessor, feature_names = load_artifacts()
    protein_features = [f for f in feature_names if f != "gender"]
    return jsonify({
        "success": True,
        "total_features": len(protein_features),
        "proteins": protein_features
    })

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.json or {}
    patient_name = data.get("patient_name", "Anonymous Patient")
    gender = data.get("gender", "Female")
    dob = data.get("dob", "")
    protein_inputs = data.get("protein_inputs", {})

    result = predict_single_patient(patient_name, gender, dob, protein_inputs)

    # Save to SQLite database
    prediction_id = save_prediction(
        patient_name=result["patient_name"],
        gender=result["gender"],
        dob=result["dob"],
        chronological_age=result["chronological_age"],
        predicted_age=result["predicted_biological_age"],
        age_difference=result["age_difference"],
        risk_category=result["risk_category"],
        protein_values=result["protein_values"],
        shap_contributions=result["top_shap_contributions"]
    )
    result["id"] = prediction_id
    return jsonify({"success": True, "data": result})

@app.route("/api/predict-csv", methods=["POST"])
def api_predict_csv():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"success": False, "error": "File must be a CSV"}), 400

    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_reader = csv.DictReader(stream)

    model, preprocessor, feature_names = load_artifacts()
    protein_features = [f for f in feature_names if f != "gender"]

    results = []
    for row in csv_reader:
        p_name = row.get("patient_name") or row.get("patientid") or "Patient"
        gender = row.get("gender", "Female")
        dob = row.get("dob", "")

        protein_inputs = {}
        for p in protein_features:
            val_str = row.get(p, "0")
            try:
                protein_inputs[p] = float(val_str)
            except ValueError:
                protein_inputs[p] = 0.0

        res = predict_single_patient(p_name, gender, dob, protein_inputs)

        pid = save_prediction(
            patient_name=res["patient_name"],
            gender=res["gender"],
            dob=res["dob"],
            chronological_age=res["chronological_age"],
            predicted_age=res["predicted_biological_age"],
            age_difference=res["age_difference"],
            risk_category=res["risk_category"],
            protein_values=res["protein_values"],
            shap_contributions=res["top_shap_contributions"]
        )
        res["id"] = pid
        results.append(res)

    return jsonify({
        "success": True,
        "total_processed": len(results),
        "data": results
    })

@app.route("/api/history", methods=["GET"])
def api_history():
    query = request.args.get("q", "").strip()
    history = get_all_predictions(search_query=query if query else None)
    return jsonify({"success": True, "count": len(history), "data": history})

@app.route("/api/history/<int:prediction_id>", methods=["DELETE"])
def api_delete_history(prediction_id):
    success = delete_prediction(prediction_id)
    return jsonify({"success": success})

@app.route("/api/export-history", methods=["GET"])
def api_export_history():
    history = get_all_predictions()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Patient Name", "Gender", "DOB", "Chronological Age", "Predicted Biological Age", "Age Difference", "Risk Category", "Date Created"])

    for h in history:
        writer.writerow([
            h["id"],
            h["patient_name"],
            h["gender"],
            h["dob"],
            h["chronological_age"],
            h["predicted_age"],
            h["age_difference"],
            h["risk_category"],
            h["created_at"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=liver_age_prediction_history.csv"}
    )

@app.route("/api/download-report/<int:prediction_id>", methods=["GET"])
def api_download_report(prediction_id):
    prediction = get_prediction_by_id(prediction_id)
    if not prediction:
        return "Prediction record not found", 404

    html_report = generate_html_report(prediction)
    return Response(
        html_report,
        mimetype="text/html",
        headers={"Content-Disposition": f"inline;filename=clinical_report_patient_{prediction_id}.html"}
    )

if __name__ == "__main__":
    print("Starting Liver Biological Age Predictor API server on http://localhost:5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)
