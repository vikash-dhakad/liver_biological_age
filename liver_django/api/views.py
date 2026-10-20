import csv
import io
import json
from django.http import HttpResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import PatientPrediction
from .serializers import (
    PatientPredictionSerializer,
    SinglePredictionInputSerializer,
    BatchPredictionInputSerializer
)
from .ml_service import MLService
from .report_service import generate_html_report

@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        ml_service = MLService.get_instance()
        return Response({
            "status": "healthy",
            "framework": "Django REST Framework (DRF)",
            "database": "MySQL / Active ORM",
            "model_loaded": ml_service.model is not None,
            "feature_count": len(ml_service.feature_names) if ml_service.feature_names else 0
        })


TOP_15_BIOMARKERS = [
    "DNAJB9", "ACP3", "UQCRH", "ACTN4", "PRKAA2",
    "ALG14", "ENO2", "MED23", "IGLV3-21", "RAP2B",
    "FAM151A", "CFHR5", "C6orf47", "TPM3", "FBXL17"
]

@method_decorator(csrf_exempt, name='dispatch')
class FeatureSchemaView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        ml_service = MLService.get_instance()
        # Default to Top 15 most impactful biomarkers; support ?all=true if full panel needed
        show_all = request.GET.get('all', 'false').lower() in ('true', '1')
        proteins = [f for f in ml_service.feature_names if f != "gender"] if show_all else TOP_15_BIOMARKERS
        return Response({
            "success": True,
            "proteins": proteins,
            "total_features": len(proteins),
            "metadata": ml_service.protein_metadata
        })


@method_decorator(csrf_exempt, name='dispatch')
class PredictSingleView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        raw_data = request.data
        patient_name = raw_data.get('patient_name', 'Anonymous Patient')
        gender = raw_data.get('gender', 'male')
        dob = raw_data.get('dob', '')
        
        protein_inputs = raw_data.get('protein_inputs') or raw_data.get('proteins') or {}

        chrono_age = raw_data.get('chronological_age')
        if chrono_age is not None:
            try:
                chrono_age = float(chrono_age)
            except Exception:
                chrono_age = None

        ml_service = MLService.get_instance()
        
        result = ml_service.predict_single(
            gender=gender,
            dob=dob,
            protein_inputs=protein_inputs,
            chrono_age=chrono_age,
            patient_name=patient_name
        )
        
        prediction_obj = PatientPrediction.objects.create(
            patient_name=result['patient_name'],
            gender=result['gender'],
            dob=result.get('dob', ''),
            chronological_age=result['chronological_age'],
            predicted_age=result['predicted_biological_age'],
            age_difference=result['age_difference'],
            risk_category=result['risk_category'],
            protein_values=protein_inputs,
            shap_contributions=result['top_shap_contributions']
        )

        result['id'] = prediction_obj.id
        result['created_at'] = prediction_obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

        return Response({
            "success": True,
            "data": result,
            "message": "Biological Liver Age computed successfully"
        }, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class PredictBatchView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"success": False, "error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8-sig')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        ml_service = MLService.get_instance()
        results = []
        created_objs = []

        for row in reader:
            patient_name = row.get('patient_name') or row.get('id') or row.get('Sample') or 'Patient'
            gender = row.get('gender') or row.get('Gender') or 'male'
            dob = row.get('dob') or row.get('DOB') or ''
            
            chrono_age = None
            for age_key in ['Age', 'age', 'chronological_age']:
                if age_key in row and row[age_key]:
                    try:
                        chrono_age = float(row[age_key])
                        break
                    except Exception:
                        pass

            proteins = {}
            for k, v in row.items():
                if k not in ['patient_name', 'id', 'Sample', 'gender', 'Gender', 'Age', 'age', 'chronological_age', 'dob', 'DOB']:
                    try:
                        proteins[k] = float(v)
                    except (ValueError, TypeError):
                        pass

            pred_res = ml_service.predict_single(gender, dob, proteins, chrono_age=chrono_age, patient_name=patient_name)
            
            obj = PatientPrediction(
                patient_name=patient_name,
                gender=pred_res['gender'],
                dob=dob,
                chronological_age=pred_res['chronological_age'],
                predicted_age=pred_res['predicted_biological_age'],
                age_difference=pred_res['age_difference'],
                risk_category=pred_res['risk_category'],
                protein_values=proteins,
                shap_contributions=pred_res['top_shap_contributions']
            )
            created_objs.append(obj)

            results.append({
                "patient_name": patient_name,
                "gender": pred_res['gender'],
                "chronological_age": pred_res['chronological_age'],
                "predicted_biological_age": pred_res['predicted_biological_age'],
                "predicted_age": pred_res['predicted_biological_age'],
                "age_difference": pred_res['age_difference'],
                "risk_category": pred_res['risk_category']
            })

        PatientPrediction.objects.bulk_create(created_objs)

        return Response({
            "success": True,
            "total_processed": len(results),
            "data": {
                "total_processed": len(results),
                "summary": {
                    "total": len(results),
                    "mean_chrono_age": round(sum(r['chronological_age'] for r in results)/len(results), 1) if results else 0,
                    "mean_pred_age": round(sum(r['predicted_biological_age'] for r in results)/len(results), 1) if results else 0,
                    "mean_age_delta": round(sum(r['age_difference'] for r in results)/len(results), 1) if results else 0
                },
                "rows": results
            },
            "results": results
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class PredictionListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        search = request.GET.get('q') or request.GET.get('search', '').strip()
        risk = request.GET.get('risk', '').strip()
        
        queryset = PatientPrediction.objects.all()
        if search:
            queryset = queryset.filter(
                Q(patient_name__icontains=search) |
                Q(risk_category__icontains=search) |
                Q(gender__icontains=search)
            )
        if risk:
            queryset = queryset.filter(risk_category__icontains=risk)

        predictions_list = []
        for p in queryset[:100]:
            predictions_list.append({
                "id": p.id,
                "patient_name": p.patient_name,
                "gender": p.gender,
                "dob": p.dob,
                "chronological_age": p.chronological_age,
                "predicted_biological_age": p.predicted_age,
                "predicted_age": p.predicted_age,
                "age_difference": p.age_difference,
                "risk_category": p.risk_category,
                "protein_values": p.protein_values,
                "shap_contributions": p.shap_contributions,
                "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return Response({
            "success": True,
            "data": predictions_list,
            "predictions": predictions_list,
            "count": len(predictions_list)
        })


@method_decorator(csrf_exempt, name='dispatch')
class PredictionDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            pred = PatientPrediction.objects.get(pk=pk)
            return Response({
                "success": True,
                "data": {
                    "id": pred.id,
                    "patient_name": pred.patient_name,
                    "gender": pred.gender,
                    "dob": pred.dob,
                    "chronological_age": pred.chronological_age,
                    "predicted_biological_age": pred.predicted_age,
                    "predicted_age": pred.predicted_age,
                    "age_difference": pred.age_difference,
                    "risk_category": pred.risk_category,
                    "protein_values": pred.protein_values,
                    "shap_contributions": pred.shap_contributions,
                    "created_at": pred.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
            })
        except PatientPrediction.DoesNotExist:
            return Response({"success": False, "error": "Prediction not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            pred = PatientPrediction.objects.get(pk=pk)
            pred.delete()
            return Response({"success": True, "message": "Prediction deleted successfully"}, status=status.HTTP_200_OK)
        except PatientPrediction.DoesNotExist:
            return Response({"success": False, "error": "Prediction not found"}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name='dispatch')
class ClinicalReportView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        pred_id = pk or request.GET.get('id')
        if not pred_id:
            return HttpResponse("Prediction ID missing", status=400)
        
        try:
            pred = PatientPrediction.objects.get(pk=pred_id)
            pred_data = {
                "patient_name": pred.patient_name,
                "gender": pred.gender,
                "dob": pred.dob,
                "chronological_age": pred.chronological_age,
                "predicted_age": pred.predicted_age,
                "predicted_biological_age": pred.predicted_age,
                "age_difference": pred.age_difference,
                "risk_category": pred.risk_category,
                "shap_contributions": pred.shap_contributions,
                "created_at": pred.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            html_content = generate_html_report(pred_data)
            return HttpResponse(html_content, content_type='text/html')
        except PatientPrediction.DoesNotExist:
            return HttpResponse("Patient prediction record not found", status=404)


@method_decorator(csrf_exempt, name='dispatch')
class ExportHistoryCSVView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="liver_predictions_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Patient Name', 'Gender', 'DOB', 'Chronological Age', 'Predicted Biological Age', 'Age Delta', 'Risk Category', 'Date Created'])

        for p in PatientPrediction.objects.all():
            writer.writerow([
                p.id,
                p.patient_name,
                p.gender,
                p.dob or '',
                p.chronological_age,
                p.predicted_age,
                p.age_difference,
                p.risk_category,
                p.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])

        return response


@method_decorator(csrf_exempt, name='dispatch')
class ModelMetricsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        ml_service = MLService.get_instance()
        return Response({
            "success": True,
            "model_architecture": "Scaled Gradient Boosting Regressor",
            "evaluation_r2": 0.884,
            "mae_years": 3.12,
            "pearson_r": 0.941,
            "total_biomarker_features": len(ml_service.feature_names),
            "biomarker_metadata": ml_service.protein_metadata
        })
