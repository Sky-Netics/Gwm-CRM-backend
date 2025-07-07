from django.shortcuts import render


from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Company, Contact, ContactDocument, Opportunity, Product, Interaction
from .serializers import CompanySerializer, ContactSerializer, ContactDocumentSerializer, OpportunitySerializer, ProductSerializer, InteractionSerializer

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



