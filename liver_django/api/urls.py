from django.urls import path
from .views import (
    HealthCheckView,
    FeatureSchemaView,
    PredictSingleView,
    PredictBatchView,
    PredictionListView,
    PredictionDetailView,
    ClinicalReportView,
    ExportHistoryCSVView,
    ModelMetricsView
)

urlpatterns = [
    # Core Health & Schema
    path('health/', HealthCheckView.as_view(), name='api-health'),
    path('health', HealthCheckView.as_view()),
    path('feature-schema/', FeatureSchemaView.as_view(), name='api-feature-schema'),
    path('feature-schema', FeatureSchemaView.as_view()),
    
    # Single & Batch Prediction
    path('predict/', PredictSingleView.as_view(), name='api-predict-single'),
    path('predict', PredictSingleView.as_view()),
    path('predict/batch/', PredictBatchView.as_view(), name='api-predict-batch'),
    path('predict/batch', PredictBatchView.as_view()),
    path('predict-batch/', PredictBatchView.as_view()),
    path('predict-batch', PredictBatchView.as_view()),

    # History & Search Records
    path('predictions/', PredictionListView.as_view(), name='api-prediction-list'),
    path('predictions', PredictionListView.as_view()),
    path('history/', PredictionListView.as_view()),
    path('history', PredictionListView.as_view()),
    path('history/<int:pk>/', PredictionDetailView.as_view()),
    path('history/<int:pk>', PredictionDetailView.as_view()),
    path('predictions/<int:pk>/', PredictionDetailView.as_view(), name='api-prediction-detail'),
    path('predictions/<int:pk>', PredictionDetailView.as_view()),

    # Reports & Export
    path('predictions/<int:pk>/report/', ClinicalReportView.as_view(), name='api-prediction-report-pk'),
    path('download-report/<int:pk>/', ClinicalReportView.as_view()),
    path('download-report/<int:pk>', ClinicalReportView.as_view()),
    path('report/', ClinicalReportView.as_view(), name='api-prediction-report'),
    path('report', ClinicalReportView.as_view()),
    path('export-history/', ExportHistoryCSVView.as_view(), name='api-export-history'),
    path('export-history', ExportHistoryCSVView.as_view()),

    # Model Metrics
    path('metrics/', ModelMetricsView.as_view(), name='api-metrics'),
    path('metrics', ModelMetricsView.as_view()),
]
