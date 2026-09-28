"""
Clinical PDF & Printable Report Generator
=========================================
Generates downloadable, printable clinical PDF/HTML reports with auto-print PDF trigger,
patient demographics, predicted biological age, risk category, and SHAP biomarker contributions.
"""

import io
import os
from datetime import datetime

def generate_html_report(prediction):
    patient_name = prediction.get("patient_name", "Anonymous Patient")
    gender = prediction.get("gender", "N/A")
    dob = prediction.get("dob", "N/A")

    # Support both predicted_biological_age (from API) and predicted_age (from DB)
    chrono_age = prediction.get("chronological_age", 45.0)
    pred_age = prediction.get("predicted_biological_age") or prediction.get("predicted_age") or 45.0
    diff = prediction.get("age_difference", 0.0)

    try:
        chrono_age = float(chrono_age)
    except Exception:
        chrono_age = 45.0

    try:
        pred_age = float(pred_age)
    except Exception:
        pred_age = 45.0

    try:
        diff = float(diff)
    except Exception:
        diff = pred_age - chrono_age

    risk_cat = prediction.get("risk_category", "Normal Aging Pattern")
    risk_desc = prediction.get("risk_description", f"Your liver biological age looks like a {pred_age:.0f}-year-old liver.")
    created_at = prediction.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


    shap_rows = ""
    shap_data = prediction.get("top_shap_contributions") or prediction.get("shap_contributions") or []
    for s in shap_data[:12]:
        val = s.get("shap_value", 0.0)
        impact_color = "#e53e3e" if val > 0 else "#38a169"
        feat = s.get("feature", "Biomarker")
        imp = s.get("impact", "Baseline")
        shap_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #edf2f7; font-weight: 600;">{feat}</td>
            <td style="padding: 10px; border-bottom: 1px solid #edf2f7; color: {impact_color}; font-weight: 700;">{val:+.4f} yrs</td>
            <td style="padding: 10px; border-bottom: 1px solid #edf2f7;">{imp}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Clinical Report - {patient_name} - Liver Biological Age</title>
        <style>
            @media print {{
                body {{ background: #ffffff !important; padding: 0 !important; }}
                .no-print {{ display: none !important; }}
                .card {{ box-shadow: none !important; border: 1px solid #e2e8f0 !important; max-width: 100% !important; }}
            }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f7fafc; color: #2d3748; margin: 0; padding: 40px; }}
            .card {{ background: #ffffff; border-radius: 12px; padding: 35px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); max-width: 800px; margin: 0 auto; border: 1px solid #e2e8f0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ebf8ff; padding-bottom: 20px; }}
            .title {{ color: #2b6cb0; font-size: 24px; font-weight: 700; margin: 0; }}
            .badge {{ display: inline-block; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 14px; background: #ebf8ff; color: #2b6cb0; border: 1px solid #bee3f8; }}
            .action-bar {{ max-width: 800px; margin: 0 auto 20px auto; display: flex; justify-content: flex-end; gap: 10px; }}
            .btn-print {{ background: #3182ce; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; }}
            .btn-print:hover {{ background: #2b6cb0; }}
            .metrics {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 30px 0; }}
            .metric-box {{ background: #f7fafc; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #e2e8f0; }}
            .metric-val {{ font-size: 32px; font-weight: 800; color: #2b6cb0; }}
            .metric-lbl {{ font-size: 12px; color: #718096; text-transform: uppercase; margin-top: 5px; font-weight: 600; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ text-align: left; background: #ebf8ff; padding: 12px; font-size: 12px; text-transform: uppercase; color: #2b6cb0; border-bottom: 2px solid #bee3f8; }}
        </style>
    </head>
    <body>
        <div class="action-bar no-print">
            <button class="btn-print" onclick="window.print()">🖨️ Save as PDF / Print Report</button>
        </div>

        <div class="card">
            <div class="header">
                <div>
                    <h1 class="title">🩺 Liver Biological Age Clinical Report</h1>
                    <p style="color: #718096; margin-top: 6px; font-size: 14px;">Patient Name: <strong>{patient_name}</strong> | Gender: <strong>{gender}</strong> | DOB: <strong>{dob}</strong></p>
                </div>
                <div class="badge">{risk_cat}</div>
            </div>

            <div class="metrics">
                <div class="metric-box">
                    <div class="metric-val">{chrono_age:.1f} yrs</div>
                    <div class="metric-lbl">Chronological Age</div>
                </div>
                <div class="metric-box" style="background: #ebf8ff; border-color: #bee3f8;">
                    <div class="metric-val" style="color: #2b6cb0;">{pred_age:.1f} yrs</div>
                    <div class="metric-lbl">Predicted Biological Age</div>
                </div>
                <div class="metric-box">
                    <div class="metric-val" style="color: { '#e53e3e' if diff > 0 else '#38a169' };">{diff:+.1f} yrs</div>
                    <div class="metric-lbl">Age Difference</div>
                </div>
            </div>

            <div style="background: #f7fafc; padding: 18px; border-radius: 8px; border-left: 5px solid #3182ce; font-size: 14px; margin-bottom: 30px;">
                <strong>Clinical Assessment:</strong> {risk_desc}
            </div>

            <h3 style="color: #2b6cb0; margin-top: 30px; border-bottom: 1px solid #edf2f7; padding-bottom: 10px;">🧬 Key Biomarker SHAP Impact (Top Drivers)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Biomarker Feature</th>
                        <th>SHAP Impact (Years)</th>
                        <th>Directional Impact</th>
                    </tr>
                </thead>
                <tbody>
                    {shap_rows}
                </tbody>
            </table>

            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #edf2f7; display: flex; justify-content: space-between; font-size: 12px; color: #a0aec0;">
                <span>Liver Biological Age Predictor AI System</span>
                <span>Report Date: {created_at}</span>
            </div>
        </div>

        <script>
            window.addEventListener('load', function() {{
                setTimeout(function() {{
                    window.print();
                }}, 500);
            }});
        </script>
    </body>
    </html>
    """
    return html
