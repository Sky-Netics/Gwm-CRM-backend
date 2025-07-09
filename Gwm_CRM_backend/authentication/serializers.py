from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from gwm_crm.models import Company

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    company = serializers.PrimaryKeyRelatedField(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'company', 'company_name']
        read_only_fields = ['email', 'first_name', 'last_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
class RegisterSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company', 
        write_only=True,
        required=False
    )
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'company_id')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        company = validated_data.pop('company', None)

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            company=company
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError('Incorrect Credentials')
    
class AssignCompanySerializer(serializers.Serializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        write_only=True
    )

