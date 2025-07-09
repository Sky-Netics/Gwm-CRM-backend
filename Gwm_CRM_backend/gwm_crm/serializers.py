from rest_framework import serializers
from .models import Company, Contact, Opportunity, Product, Interaction, ContactDocument
from authentication.models import User 
from authentication.serializers import UserSerializer

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'website', 'country', 'industry_category',
            'activity_level', 'acquired_via', 'lead_score', 'notes'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'website': {'required': False},
        }

    def validate_name(self, value):
        """Ensure company name is unique"""
        if Company.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A company with this name already exists.")
        return value

class ContactSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company'
    )
    
    class Meta:
        model = Contact
        fields = [
            'id', 'company_id', 'full_name', 'position', 'company_email',
            'personal_email', 'phone_office', 'phone_mobile', 'address',
            'customer_specific_conditions', 'business_card'
        ]
        extra_kwargs = {
            'business_card': {'required': False},
            'document': {'required': False},
        }

class ContactDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactDocument
        fields = ['id', 'file', 'uploaded_at', 'name']
        read_only_fields = ['uploaded_at', 'name']

class ContactDetailSerializer(ContactSerializer):
    documents = ContactDocumentSerializer(many=True, read_only=True)
    
    class Meta(ContactSerializer.Meta):
        fields = ContactSerializer.Meta.fields + ['documents']

class OpportunitySerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company'
    )
    
    class Meta:
        model = Opportunity
        fields = [
            'id', 'company_id', 'stage', 'expected_value',
            'expected_close_date', 'probability'
        ]

class ProductSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'company_id', 'category', 'price_list', 'price_list_expiry',
            'volume_offered', 'delivery_terms', 'packaging', 'payment_terms',
            'product_specifications', 'target_price'
        ]
        extra_kwargs = {
            'price_list': {'required': False},
        }

class InteractionSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
    )
    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        source='contact',
        required=False,
        allow_null=True
    )
    # assigned_to_id = serializers.PrimaryKeyRelatedField(
    #     queryset=User.objects.all(),
    #     source='assigned_to',
    #     required=False,
    #     allow_null=True
    # )
    
    class Meta:
        model = Interaction
        fields = [
            'id', 'company_id', 'contact_id', 'date', 'type', 'status',
            'summary'
        ]
        extra_kwargs = {
            'date': {'read_only': True},
            # 'attachments': {'required': False},
        }


class CompanyDetailSerializer(CompanySerializer):
    contacts = ContactSerializer(many=True, read_only=True)
    opportunities = OpportunitySerializer(many=True, read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    interactions = InteractionSerializer(many=True, read_only=True)
    
    class Meta(CompanySerializer.Meta):
        fields = CompanySerializer.Meta.fields + [
            'contacts', 'opportunities', 'products', 'interactions'
        ]