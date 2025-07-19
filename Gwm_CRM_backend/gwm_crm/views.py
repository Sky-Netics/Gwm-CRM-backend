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



from .models import Company, Contact, ContactDocument, Opportunity, Product, Interaction, Task, InteractionDocument, Notification, Meeting
from .serializers import CompanySerializer, CompanyDetailSerializer, ContactSerializer, ContactDocumentSerializer, OpportunitySerializer, ProductSerializer, InteractionSerializer, TaskSerializer, InteractionDocumentSerializer, NotificationSerializer, MeetingSerializer
from .exporters import ModelExporter

from datetime import timedelta
import csv
import json
import io

class CompanyViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
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
        
class ContactViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]


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
    
class ContactDocumentViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    serializer_class = ContactDocumentSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        return ContactDocument.objects.filter(
            contact_id=self.kwargs['contact_pk']
        )

    def perform_create(self, serializer):
        contact = Contact.objects.get(pk=self.kwargs['contact_pk'])
        serializer.save(contact=contact)

class OpportunityViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

class InteractionDocumentViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    serializer_class = InteractionDocumentSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        return InteractionDocument.objects.filter(
            interaction_id=self.kwargs['interaction_pk']
        )

    def perform_create(self, serializer):
        interaction = Interaction.objects.get(pk=self.kwargs['interaction_pk'])
        serializer.save(interaction=interaction)

class ProductViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

class InteractionViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

class TaskViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

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
    
class InteractionDocumentViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser]
    serializer_class = InteractionDocumentSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        return InteractionDocument.objects.filter(
            interaction_id=self.kwargs['interaction_pk']
        )

    def perform_create(self, serializer):
        interaction = Interaction.objects.get(pk=self.kwargs['interaction_pk'])
        serializer.save(interaction=interaction)

class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]

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
