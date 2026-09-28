from django.contrib import admin
from django.utils.html import format_html
from .models import PatientPrediction

@admin.register(PatientPrediction)
class PatientPredictionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'patient_name',
        'gender_badge',
        'chronological_age',
        'predicted_age',
        'age_difference_display',
        'risk_category_badge',
        'created_at'
    )
    list_filter = ('risk_category', 'gender', 'created_at')
    search_fields = ('patient_name', 'risk_category', 'notes')
    readonly_fields = ('created_at', 'predicted_age', 'age_difference', 'shap_contributions')
    list_per_page = 25

    def gender_badge(self, obj):
        color = "#3182ce" if obj.gender.lower() == "male" else "#d53f8c"
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.gender.upper()
        )
    gender_badge.short_description = "Gender"

    def age_difference_display(self, obj):
        diff = obj.age_difference
        color = "#e53e3e" if diff > 3.0 else ("#38a169" if diff < -3.0 else "#d69e2e")
        sign = "+" if diff > 0 else ""
        return format_html(
            '<strong style="color: {};">{}{:.2f} yrs</strong>',
            color,
            sign,
            diff
        )
    age_difference_display.short_description = "Δ Acceleration"

    def risk_category_badge(self, obj):
        colors = {
            'High Risk': '#fed7d7',
            'Low Risk': '#c6f6d5',
            'Moderate Risk': '#feebc8'
        }
        text_colors = {
            'High Risk': '#c53030',
            'Low Risk': '#22543d',
            'Moderate Risk': '#744210'
        }
        bg = colors.get(obj.risk_category, '#edf2f7')
        fg = text_colors.get(obj.risk_category, '#2d3748')
        return format_html(
            '<span style="background: {}; color: {}; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">{}</span>',
            bg,
            fg,
            obj.risk_category
        )
    risk_category_badge.short_description = "Risk Status"
