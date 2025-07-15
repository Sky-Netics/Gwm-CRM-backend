from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Company, Contact, ContactDocument, Opportunity, Product, Interaction, Task
from .serializers import CompanySerializer, CompanyDetailSerializer, ContactSerializer, ContactDocumentSerializer, OpportunitySerializer, ProductSerializer, InteractionSerializer, TaskSerializer

from datetime import timedelta

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]


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
    
class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]


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

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

class InteractionViewSet(viewsets.ModelViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticated]


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # filterset_fields = {
    #     'status': ['exact'],
    #     'priority': ['exact'],
    #     'company': ['exact'],
    #     'opportunity': ['exact'],
    #     'interaction': ['exact'],
    #     'assigned_to': ['exact'],
    #     'due_date': ['gte', 'lte', 'exact'],
    # }
    # search_fields = ['title', 'description']
    # ordering_fields = ['due_date', 'priority', 'created_at']
    # ordering = ['-due_date']

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