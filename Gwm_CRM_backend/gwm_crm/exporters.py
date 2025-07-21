import csv
import json
from django.http import HttpResponse
from django.forms.models import model_to_dict
from io import StringIO, BytesIO
from datetime import datetime
from .models import Company, Contact, Opportunity, Product, Interaction, Task

class ModelExporter:
    @classmethod
    def export_queryset(cls, queryset, model_name, format_type):
        """Remove format parameter from method signature"""
        if format_type == 'csv':
            return cls._to_csv(queryset, model_name)
        elif format_type == 'json':
            return cls._to_json(queryset, model_name)
        return cls._to_csv(queryset, model_name)

    @staticmethod
    def _to_csv(queryset, model_name):
        buffer = StringIO()
        writer = csv.writer(buffer)
        
        # Write headers
        if queryset.exists():
            first = queryset.first()
            writer.writerow([field.name for field in first._meta.fields])
        
        # Write data
        for obj in queryset:
            writer.writerow([getattr(obj, field.name) for field in obj._meta.fields])
        
        response = HttpResponse(buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name}s_{datetime.now().date()}.csv"'
        return response

    @staticmethod
    def _to_json(queryset_or_instance, model_name):
        # Handle both querysets and single instances
        if hasattr(queryset_or_instance, '_meta'):  # Single instance
            data = [model_to_dict(queryset_or_instance)]
        else:  # Queryset
            data = list(queryset_or_instance.values())
            
        response = HttpResponse(
            json.dumps(data, indent=2, default=str),  # Handle dates
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{model_name}_{datetime.now().date()}.json"'
        return response

    @staticmethod
    def _to_text(queryset, model_name):
        buffer = StringIO()
        for obj in queryset:
            buffer.write(f"{obj}\n")
        response = HttpResponse(buffer.getvalue(), content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{model_name}s_{datetime.now().date()}.txt"'
        return response