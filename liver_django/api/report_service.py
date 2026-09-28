import io
from datetime import datetime

def generate_html_report(prediction):
    patient_name = prediction.get("patient_name", "Anonymous Patient")
    gender = prediction.get("gender", "N/A")
    dob = prediction.get("dob", "N/A")

    chrono_age = float(prediction.get("chronological_age", 45.0))
    pred_age = float(prediction.get("predicted_age") or prediction.get("predicted_biological_age", 45.0))
    diff = float(prediction.get("age_difference", pred_age - chrono_age))
    risk_cat = prediction.get("risk_category", "Moderate Risk")
    created_at = prediction.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    shap_data = prediction.get("shap_contributions") or prediction.get("top_shap_contributions") or []
    
    shap_rows = ""
    for s in shap_data[:12]:
        val = float(s.get("importance") or s.get("shap_value", 0.0))
        impact_color = "#e53e3e" if val > 0 else "#38a169"
        feat = s.get("feature", "Biomarker")
        name = s.get("full_name", feat)
        direction = "Accelerates Aging" if val > 0 else "Protective"
        shap_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #edf2f7; font-weight: 600;">{feat} <span style="font-size: 11px; color: #718096; display: block;">{name}</span></td>
            <td style="padding: 12px; border-bottom: 1px solid #edf2f7; color: {impact_color}; font-weight: 700;">{val:+.2f} yrs</td>
            <td style="padding: 12px; border-bottom: 1px solid #edf2f7;"><span style="background: {'#feebc8' if val > 0 else '#c6f6d5'}; color: {'#c05621' if val > 0 else '#22543d'}; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">{direction}</span></td>
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
            .card {{ background: #ffffff; border-radius: 12px; padding: 35px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); max-width: 850px; margin: 0 auto; border: 1px solid #e2e8f0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ebf8ff; padding-bottom: 20px; }}
            .title {{ color: #2b6cb0; font-size: 24px; font-weight: 700; margin: 0; }}
            .badge {{ display: inline-block; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 14px; background: #ebf8ff; color: #2b6cb0; border: 1px solid #bee3f8; }}
            .action-bar {{ max-width: 850px; margin: 0 auto 20px auto; display: flex; justify-content: flex-end; gap: 10px; }}
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
                    <p style="color: #718096; margin-top: 6px; font-size: 14px;">Patient Name: <strong>{patient_name}</strong> | Gender: <strong>{gender.capitalize()}</strong> | DOB: <strong>{dob or 'N/A'}</strong></p>
                </div>
                <div class="badge">{risk_cat}</div>
            </div>

            <div class="metrics">
                <div class="metric-box">
                    <div class="metric-val">{chrono_age:.1f}</div>
                    <div class="metric-lbl">Chronological Age</div>
                </div>
                <div class="metric-box">
                    <div class="metric-val" style="color: {'#e53e3e' if diff > 3 else '#38a169'};">{pred_age:.1f}</div>
                    <div class="metric-lbl">Biological Liver Age</div>
                </div>
                <div class="metric-box">
                    <div class="metric-val" style="color: {'#e53e3e' if diff > 3 else '#38a169'};">{diff:+.1f} yrs</div>
                    <div class="metric-lbl">Age Acceleration Delta</div>
                </div>
            </div>

            <div style="background: #edf2f7; padding: 15px; border-radius: 8px; margin-bottom: 25px;">
                <strong>Clinical Interpretation:</strong> 
                {"This patient shows accelerated hepatic aging markers. Key inflammatory and metabolic proteomic pathways indicate elevated biological stress." if diff > 3 else "This patient exhibits healthy/protective proteomic profile consistent with younger or normal liver aging."}
            </div>

            <h3 style="color: #2d3748; margin-bottom: 10px;">🔍 Top Biomarker Attributions (Explainable AI / SHAP)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Biomarker (Protein)</th>
                        <th>Impact on Liver Age</th>
                        <th>Aging Modulation</th>
                    </tr>
                </thead>
                <tbody>
                    {shap_rows}
                </tbody>
            </table>

            <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #a0aec0; text-align: center;">
                Generated on {created_at} • Powered by Explainable AI (SHAP & Django REST Framework) • For Clinical Research Use
            </div>
        </div>
    </body>
    </html>
    """
    return html
