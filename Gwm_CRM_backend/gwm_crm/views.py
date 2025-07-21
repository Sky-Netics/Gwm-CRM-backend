from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponse

from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework import generics
from rest_framework.parsers import JSONParser

from .models import Company, Contact, Opportunity, Product, Interaction, Task, Notification, Meeting
from .serializers import CompanySerializer, CompanyDetailSerializer, ContactSerializer, OpportunitySerializer, ProductSerializer, InteractionSerializer, TaskSerializer, NotificationSerializer, MeetingSerializer

from datetime import timedelta
import csv
import json
import io

class ExportMixin:
    export_fields = None  # Override this in each viewset
    export_serializer_class = None  # Optional: for JSON export

    @action(detail=False, methods=['get'], url_path='export')
    def export_all(self, request):
        queryset = self.get_queryset()
        model_name = self.queryset.model.__name__.lower()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name}s.csv"'

        writer = csv.writer(response)
        fields = self.export_fields or [field.name for field in self.queryset.model._meta.fields]
        writer.writerow(fields)

        for obj in queryset:
            writer.writerow([getattr(obj, field, '') for field in fields])

        return response

    @action(detail=True, methods=['get'], url_path='export')
    def export_single(self, request, pk=None):
        obj = self.get_object()
        serializer_class = self.export_serializer_class or self.get_serializer_class()
        serializer = serializer_class(obj)
        data = json.dumps(serializer.data, indent=4)

        model_name = obj.__class__.__name__.lower()
        response = HttpResponse(data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{model_name}_{obj.pk}.json"'
        return response

class CompanyViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    # export_fields = ['id', 'name', 'website', 'country', 'industry_category',
    #                  'activity_level', 'acquired_via', 'lead_score', 'notes']
    # parser_classes = [MultiPartParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if Company.objects.filter(name__iexact=request.data.get('name')).exists():
            return Response(
                {"error": "Company with this name already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompanyDetailSerializer
        return CompanySerializer
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], url_path='export')
    def export_all(self, request):
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="companies.csv"'

        writer = csv.writer(response)
        fields = ['id', 'name', 'website', 'country', 'industry_category',
                'activity_level', 'acquired_via', 'lead_score', 'notes']
        writer.writerow(fields)

        for company in queryset:
            writer.writerow([getattr(company, field) for field in fields])

        return response
    
    @action(detail=True, methods=['get'], url_path='export')
    def export_single(self, request, pk=None):
        company = self.get_object()
        serializer = CompanyDetailSerializer(company)
        data = json.dumps(serializer.data, indent=4)

        response = HttpResponse(data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="company_{company.id}.json"'
        return response


class CompanyCSVUploadView(APIView):
    parser_classes = [JSONParser]
    # parser_classes = [MultiPartParser]

    def get(self, request, *args, **kwargs):
        return Response({"message": "Upload endpoint is live!"})

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_file.name.endswith('.csv'):
            return Response({'error': 'File is not a CSV.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            created_count = 0
            errors = []

            for idx, row in enumerate(reader, start=1):
                try:
                    company, created = Company.objects.get_or_create(
                        name=row['name'],
                        defaults={
                            'website': row.get('website', ''),
                            'country': row['country'],
                            'industry_category': int(row['industry_category']),
                            'activity_level': row['activity_level'],
                            'acquired_via': row['acquired_via'],
                            'lead_score': int(row['lead_score']),
                            'notes': row.get('notes', ''),
                        }
                    )
                    if created:
                        created_count += 1
                except Exception as e:
                    errors.append({'row': idx, 'error': str(e)})

            return Response({
                'created': created_count,
                'errors': errors
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': f'Failed to process CSV: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ContactViewSet(viewsets.ModelViewSet, ExportMixin):
    parser_classes = [MultiPartParser, JSONParser]
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    export_fields = ['id', 'full_name', 'position', 'company_email', 'phone_office']


    def create(self, request, *args, **kwargs):
        """
        Create a new contact with file upload support
        Example POST data:
        {
            "company_id": 1,
            "full_name": "John Doe",
            "position": "Manager",
            "company_email": "john@example.com",
            "phone_office": "+1234567890",
            "business_card": [file]
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        if 'document' in request.data and request.data['document'] is None:
            if instance.document:
                instance.document.delete()
                instance.document = None
                instance.save()
        
        return Response(serializer.data)
# class ContactDocumentViewSet(viewsets.ModelViewSet):
#     parser_classes = [JSONParser]
#     serializer_class = ContactDocumentSerializer
#     permission_classes = [IsAuthenticated]
#     renderer_classes = [JSONRenderer]

#     def get_queryset(self):
#         return ContactDocument.objects.filter(
#             contact_id=self.kwargs['contact_pk']
#         )

#     def perform_create(self, serializer):
#         contact = Contact.objects.get(pk=self.kwargs['contact_pk'])
#         serializer.save(contact=contact)

class OpportunityViewSet(viewsets.ModelViewSet, ExportMixin):
    parser_classes = [JSONParser]
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    export_fields = ['id', 'company_id', 'stage', 'expected_value', 'probability']
     
# class InteractionDocumentViewSet(viewsets.ModelViewSet):
#     parser_classes = [JSONParser]
#     serializer_class = InteractionDocumentSerializer
#     permission_classes = [IsAuthenticated]
#     renderer_classes = [JSONRenderer]

     # @action(detail=False, methods=['get'], url_path='export')
    # def export_all(self, request):
    #     queryset = self.get_queryset()
        
    #     response = HttpResponse(content_type='text/csv')
    #     response['Content-Disposition'] = 'attachment; filename="interactions.csv"'

    #     writer = csv.writer(response)
    #     fields = ['id', 'company_id', 'contact_id', 'date', 'type', 'status']
    #     writer.writerow(fields)

    #     for interaction in queryset:
    #         writer.writerow([getattr(interaction, field) for field in fields])

    #     return response

    
    # @action(detail=True, methods=['get'], url_path='export')
    # def export_single(self, request, pk=None):
    #     interaction = self.get_object()
    #     serializer = InteractionSerializer(interaction)
    #     data = json.dumps(serializer.data, indent=4)

    #     response = HttpResponse(data, content_type='application/json')
    #     response['Content-Disposition'] = f'attachment; filename="interaction_{interaction.id}.json"'
    #     return response
    
    # def get_queryset(self):
    #     return InteractionDocument.objects.filter(
    #         interaction_id=self.kwargs['interaction_pk']
    #     )

    # def perform_create(self, serializer):
    #     interaction = Interaction.objects.get(pk=self.kwargs['interaction_pk'])
    #     serializer.save(interaction=interaction)


class ProductViewSet(viewsets.ModelViewSet, ExportMixin):
    parser_classes = [JSONParser]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    export_fields = ['id', 'company_id', 'category', 'volume_offered', 'currency', 'target_price']

class InteractionViewSet(viewsets.ModelViewSet, ExportMixin):
    parser_classes = [MultiPartParser, JSONParser]
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    export_fields = ['id', 'company_id', 'contact_id', 'date', 'type', 'status']

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        if 'document' in request.data and request.data['document'] is None:
            if instance.document:
                instance.document.delete()
                instance.document = None
                instance.save()
        
        return Response(serializer.data)

class TaskViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    # export_fields = ['id', 'title', 'status', 'priority', 'due_date', 'assigned_to_id', 'created_by_id']
    @action(detail=False, methods=['get'], url_path='export')
    def export_all(self, request):
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tasks.csv"'

        writer = csv.writer(response)
        fields = ['id', 'title', 'status', 'priority', 'due_date', 'assigned_to_id', 'created_by_id']
        writer.writerow(fields)

        for task in queryset:
            writer.writerow([getattr(task, field) for field in fields])

        return response

    
    @action(detail=True, methods=['get'], url_path='export')
    def export_single(self, request, pk=None):
        task = self.get_object()
        serializer = TaskSerializer(task)
        data = json.dumps(serializer.data, indent=4)

        response = HttpResponse(data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="task_{task.id}.json"'
        return response

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        return super().get_permissions()

    def get_queryset(self):
        """
        Returns different querysets based on the action:
        - Admin users see all tasks in main endpoint
        - Regular users only see their tasks in my-tasks endpoint
        """
        user = self.request.user

        if self.action == 'my_tasks':
            return Task.objects.filter(assigned_to=user)

        if user.is_staff:
            return Task.objects.all()

        return Task.objects.none()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_tasks(self, request):
        parser_classes = [JSONParser]
        """
        Special endpoint for users to see only their assigned tasks
        URL: /tasks/my-tasks/
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        parser_classes = [JSONParser]
        """Task summary for dashboard"""
        queryset = self.filter_queryset(self.get_queryset())
        user = request.user
        
        data = {
            'total': queryset.count(),
            'open': queryset.filter(status='open').count(),
            'in_progress': queryset.filter(status='in_progress').count(),
            'closed': queryset.filter(status='closed').count(),
            'high_priority': queryset.filter(priority='high').count(),
            'due_soon': queryset.filter(
                due_date__gte=timezone.now(),
                due_date__lte=timezone.now() + timedelta(days=3)
            ).count(),
            'overdue': queryset.filter(
                due_date__lt=timezone.now(),
                status__in=['open', 'in_progress']
            ).count(),
            'user_stats': {
                'assigned_tasks': queryset.filter(assigned_to=user).count(),
                'created_tasks': queryset.filter(created_by=user).count(),
            }
        }
        
        return Response(data)
    
# class InteractionDocumentViewSet(viewsets.ModelViewSet):
#     parser_classes = [JSONParser]
#     serializer_class = InteractionDocumentSerializer
#     permission_classes = [IsAuthenticated]
#     renderer_classes = [JSONRenderer]

#     def get_queryset(self):
#         return InteractionDocument.objects.filter(
#             interaction_id=self.kwargs['interaction_pk']
#         )

#     def perform_create(self, serializer):
#         interaction = Interaction.objects.get(pk=self.kwargs['interaction_pk'])
#         serializer.save(interaction=interaction)

class MeetingViewSet(viewsets.ModelViewSet, ExportMixin):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]
    export_fields = ['id', 'company_id', 'user_ids', 'date']

    def get_queryset(self):
        """Users can only see meetings they're attending"""
        return self.request.user.meetings.all()

class UnreadNotificationsView(generics.ListAPIView):
    parser_classes = [JSONParser]
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            seen=False
        ).order_by('-created_at')

    
class MarkNotificationsReadView(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            user=request.user,
            seen=False
        ).update(seen=True)
        
        return Response({
            'status': 'success',
            'marked_read': updated
        })
    
class AllNotificationsView(generics.ListAPIView):
    parser_classes = [JSONParser]
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

class CompanyFileViewSet(viewsets.ViewSet):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get', 'post', 'delete'], url_path='business-card')
    def business_card(self, request, pk=None):
        return self.handle_file_field(request, pk, 'business_card')

    @action(detail=True, methods=['get', 'post', 'delete'], url_path='catalogs')
    def catalogs(self, request, pk=None):
        return self.handle_file_field(request, pk, 'catalogs')

    @action(detail=True, methods=['get', 'post', 'delete'], url_path='signed-contracts')
    def signed_contracts(self, request, pk=None):
        return self.handle_file_field(request, pk, 'signed_contracts')

    @action(detail=True, methods=['get', 'post', 'delete'], url_path='correspondence')
    def correspondence(self, request, pk=None):
        return self.handle_file_field(request, pk, 'correspondence')

    def handle_file_field(self, request, pk, field_name):
        try:
            company = Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            if not getattr(company, field_name):
                return Response({'error': f'No {field_name.replace("_", " ")} found'}, 
                               status=status.HTTP_404_NOT_FOUND)
            
            file_url = request.build_absolute_uri(getattr(company, field_name).url)
            return Response({'url': file_url})

        elif request.method == 'POST':
            file = request.FILES.get('file')
            if not file:
                return Response({'error': 'No file provided'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Delete old file if exists
            old_file = getattr(company, field_name)
            if old_file:
                old_file.delete(save=False)
            
            setattr(company, field_name, file)
            company.save()
            
            file_url = request.build_absolute_uri(getattr(company, field_name).url)
            return Response({'url': file_url}, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            file = getattr(company, field_name)
            if not file:
                return Response({'error': f'No {field_name.replace("_", " ")} found'}, 
                               status=status.HTTP_404_NOT_FOUND)
            
            file.delete(save=False)
            setattr(company, field_name, None)
            company.save()
            
            return Response(status=status.HTTP_204_NO_CONTENT)