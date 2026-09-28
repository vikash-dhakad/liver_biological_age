"""
Database Persistence Layer (SQLite3)
=====================================
Stores predictions, chronological age, predicted biological age, risk category,
and timestamp. Supports search, deletion, and CSV exporting.
"""

import csv
import json
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "predictions.db")

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

def save_prediction(patient_name, gender, dob, chronological_age, predicted_age, age_difference, risk_category, protein_values, shap_contributions):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions (patient_name, gender, dob, chronological_age, predicted_age, age_difference, risk_category, protein_values, shap_contributions, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_name,
        gender,
        dob,
        chronological_age,
        predicted_age,
        age_difference,
        risk_category,
        json.dumps(protein_values),
        json.dumps(shap_contributions),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    prediction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return prediction_id

def get_all_predictions(search_query=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if search_query:
        query = "%" + search_query + "%"
        cursor.execute("""
            SELECT * FROM predictions 
            WHERE patient_name LIKE ? OR risk_category LIKE ? OR gender LIKE ?
            ORDER BY id DESC
        """, (query, query, query))
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

def get_prediction_by_id(prediction_id):
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

def delete_prediction(prediction_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions WHERE id = ?", (prediction_id,))
    conn.commit()
    conn.close()
    return True

# Initialize database on module load
init_db()
