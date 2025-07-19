from rest_framework import serializers
from .models import Company, Contact, Opportunity, Product, Interaction, ContactDocument, Task, Meeting, InteractionDocument, Notification
from authentication.models import User 
from authentication.serializers import UserSerializer

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'website', 'country', 'industry_category',
            'activity_level', 'acquired_via', 'lead_score', 'notes', 'business_card',
            'catalogs', 'signed_contracts', 'correspondence'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'website': {'required': False},
            'business_card': {'required': False},
            'catalogs': {'required': False},
            'signed_contracts': {'required': False},
            'correspondence': {'required': False},
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
            'customer_specific_conditions'
        ]
        extra_kwargs = {
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
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Interaction
        fields = [
            'id', 'company_id', 'contact_id', 'date', 'type', 'status',
            'summary', 'assigned_to_id', 'documents'
        ]
        extra_kwargs = {
            'date': {'read_only': True},
            # 'attachments': {'required': False},
        }

class InteractionDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractionDocument
        fields = ['id', 'file', 'uploaded_at', 'name']
        read_only_fields = ['uploaded_at', 'name']

class TaskSerializer(serializers.ModelSerializer):
    # assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='assigned_to',
        write_only=True,
        required=False
    )
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'due_date', 'created_at', 'updated_at',
            'assigned_to_id',
            'created_by',
            'company',
            'opportunity',
            'interaction'
        ]
        read_only_fields = ['created_by']

class MeetingSerializer(serializers.ModelSerializer):
    user_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        source='users',
        write_only=True,
        required=False
    )
    
    attendees = UserSerializer(
        source='users',
        many=True,
        read_only=True
    )

    class Meta:
        model = Meeting
        fields = ['id', 'company', 'date', 'report', 'attachment', 'user_ids', 'attendees']

class CompanyDetailSerializer(CompanySerializer):
    contacts = ContactSerializer(many=True, read_only=True)
    opportunities = OpportunitySerializer(many=True, read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    interactions = InteractionSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    meetings = MeetingSerializer(many=True, read_only=True)

    class Meta(CompanySerializer.Meta):
        fields = CompanySerializer.Meta.fields + [
            'contacts', 'opportunities', 'products', 'interactions', 'tasks', 'meetings'
        ]

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'type',
            'seen',
            'created_at',
            'related_object_id',
        ]