from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from gwm_crm.models import Company

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    company = serializers.PrimaryKeyRelatedField(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    # meetings = serializers.SerializerMethodField()
    # tasks = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'full_name', 'company', 'company_name']
        read_only_fields = ['email', 'username', 'first_name', 'last_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    # def get_meetings(self, obj):
    #     from gwm_crm.serializers import MeetingSerializer 
    #     meetings = obj.meetings.all()
    #     return MeetingSerializer(meetings, many=True, context=self.context).data
    
    # def get_tasks(self, obj):
    #     from gwm_crm.serializers import TaskSerializer 
    #     tasks = obj.assigned_tasks.all()
    #     return TaskSerializer(tasks, many=True, context=self.context).data
    
class RegisterSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company', 
        write_only=True,
        required=False
    )
    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'first_name', 'last_name', 'company_id')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        company = validated_data.pop('company', None)

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username'),
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            company=company
        )
        return user

class LoginSerializer(serializers.Serializer):
    email_or_username = serializers.CharField()
    password = serializers.CharField()

    # def validate(self, data):
    #     user = authenticate(**data)
    #     # user = User.objects.filter(is_active=True).first()
    #     if user and user.is_active:
    #         return user
    #     raise serializers.ValidationError('No active users available')
    
    def validate(self, data):
        email_or_username = data.get('email_or_username')
        password = data.get('password')
        
        if '@' in email_or_username:
            kwargs = {'email': email_or_username}
        else:
            kwargs = {'username': email_or_username}
        
        try:
            user = User.objects.get(**kwargs)
        except User.DoesNotExist:
            raise serializers.ValidationError('No user with given credentials found')
        
        user = authenticate(username=user.email, password=password)  # Note: we use email as username for auth
        
        if user and user.is_active:
            return user
        raise serializers.ValidationError('Incorrect credentials or inactive account')
    
class AssignCompanySerializer(serializers.Serializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        write_only=True
    )

class UserDetailSerializer(serializers.Serializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    # meetings = serializers.SerializerMethodField()
    # tasks = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 
                'is_active', 'date_joined', 'company', 'company_name']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    # def get_meetings(self, obj):
    #     from gwm_crm.serializers import MeetingSerializer 
    #     meetings = obj.meetings.all()
    #     return MeetingSerializer(meetings, many=True, context=self.context).data
    
    # def get_tasks(self, obj):
    #     from gwm_crm.serializers import TaskSerializer 
    #     tasks = obj.assigned_tasks.all()
    #     return TaskSerializer(tasks, many=True, context=self.context).data
    

