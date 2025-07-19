from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework import generics

from .models import Company, Contact, ContactDocument, Opportunity, Product, Interaction, Task, InteractionDocument, Notification
from .serializers import CompanySerializer, CompanyDetailSerializer, ContactSerializer, ContactDocumentSerializer, OpportunitySerializer, ProductSerializer, InteractionSerializer, TaskSerializer, InteractionDocumentSerializer, NotificationSerializer

from datetime import timedelta
import csv
import io

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

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

class CompanyCSVUploadView(APIView):
    parser_classes = [MultiPartParser]

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
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

class InteractionDocumentViewSet(viewsets.ModelViewSet):
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
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

class InteractionViewSet(viewsets.ModelViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        """Return tasks based on user permissions"""
        user = self.request.user
        
        # For staff users: show all tasks
        if user.is_staff:
            return Task.objects.all()
        
        # For regular users: show assigned tasks or tasks from their companies
        query = Q(assigned_to=user)
    
        # Add company tasks if user has a company
        if user.company:
            query |= Q(company=user.company) 
        
        return Task.objects.filter(query).distinct()
    

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get tasks assigned to current user"""
        tasks = self.get_queryset().filter(assigned_to=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
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

class UnreadNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            seen=False
        ).order_by('-created_at')

    
class MarkNotificationsReadView(APIView):
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
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
