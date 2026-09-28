from rest_framework import serializers
from .models import PatientPrediction

class PatientPredictionSerializer(serializers.ModelSerializer):
    """
    Serializer for full PatientPrediction records including SHAP breakdown.
    """
    class Meta:
        model = PatientPrediction
        fields = '__all__'
        read_only_fields = ('id', 'predicted_age', 'age_difference', 'risk_category', 'shap_contributions', 'created_at')


class SinglePredictionInputSerializer(serializers.Serializer):
    """
    Validates incoming clinical patient data and biomarker inputs.
    """
    patient_name = serializers.CharField(max_length=150, required=False, default="Anonymous")
    gender = serializers.ChoiceField(choices=['male', 'female', 'Male', 'Female', '1', '0'])
    dob = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    chronological_age = serializers.FloatField(min_value=1.0, max_value=120.0)
    proteins = serializers.DictField(child=serializers.FloatField(), required=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_gender(self, value):
        val_str = str(value).lower()
        if val_str in ['male', '1', 'm']:
            return 'male'
        elif val_str in ['female', '0', 'f']:
            return 'female'
        return 'male'


class BatchPredictionInputSerializer(serializers.Serializer):
    """
    Validates batch CSV file uploads.
    """
    file = serializers.FileField()
