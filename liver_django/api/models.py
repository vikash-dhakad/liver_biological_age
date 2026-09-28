from django.db import models

class PatientPrediction(models.Model):
    """
    Stores patient metadata, physiological inputs, predicted biological age,
    age delta acceleration, risk classification, and SHAP biomarker attributions.
    """
    RISK_CHOICES = [
        ('Low Risk', 'Low Risk (Protective)'),
        ('Moderate Risk', 'Moderate Risk (Normal Aging)'),
        ('High Risk', 'High Risk (Accelerated Aging)'),
    ]

    patient_name = models.CharField(max_length=150, default='Anonymous', verbose_name="Patient Name")
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], verbose_name="Gender")
    dob = models.CharField(max_length=50, blank=True, null=True, verbose_name="Date of Birth")
    chronological_age = models.FloatField(verbose_name="Chronological Age (Years)")
    predicted_age = models.FloatField(verbose_name="Predicted Biological Liver Age")
    age_difference = models.FloatField(verbose_name="Age Acceleration Delta (Δ Years)")
    risk_category = models.CharField(max_length=50, choices=RISK_CHOICES, verbose_name="Risk Tier")
    
    # Store raw input biomarker values as JSON
    protein_values = models.JSONField(default=dict, verbose_name="Input Biomarker Quantities")
    
    # Store ranked SHAP contribution breakdown as JSON
    shap_contributions = models.JSONField(default=list, verbose_name="SHAP Feature Attributions")
    
    notes = models.TextField(blank=True, null=True, verbose_name="Clinical Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")

    class Meta:
        db_table = 'patient_predictions'
        ordering = ['-created_at']
        verbose_name = 'Patient Prediction & Biomarker Analysis'
        verbose_name_plural = 'Patient Predictions & Biomarker Analyses'

    def __str__(self):
        return f"{self.patient_name} - Age: {self.chronological_age} → Bio: {self.predicted_age:.2f} ({self.risk_category})"
