from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import viewsets, status, filters
from rest_framework.views import APIView

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, AssignCompanySerializer, UserDetailSerializer
from .models import User

from gwm_crm.models import Task, Meeting
from gwm_crm.serializers import TaskSerializer, MeetingSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user
    
class AssignCompanyView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignCompanySerializer

    def update(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user.company = serializer.validated_data['company_id']
        user.save()
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK
        )

# class UserListView(generics.ListAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = [IsAuthenticated, IsAdminUser] 
    
# class UserViewSet(viewsets.ModelViewSet):
#     serializer_class = UserSerializer
#     permission_classes = [IsAuthenticated]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]  

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsAdminUser()]
        return super().get_permissions()
    
class UserDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # Optional: ensure users can only access their own dashboard
        if request.user != user and not request.user.is_staff:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        # Serialize user data
        user_data = UserSerializer(user, context={'request': request}).data

        # Serialize tasks
        tasks = Task.objects.filter(assigned_to=user)
        tasks_data = TaskSerializer(tasks, many=True, context={'request': request}).data

        # Serialize meetings
        meetings = Meeting.objects.filter(users=user)
        meetings_data = MeetingSerializer(meetings, many=True, context={'request': request}).data

        # # Optional: notifications
        # notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
        # notifications_data = NotificationSerializer(notifications, many=True).data

        dashboard_data = {
            'user': user_data,
            'tasks': tasks_data,
            'meetings': meetings_data,
            # 'notifications': notifications_data
        }

        return Response(dashboard_data)