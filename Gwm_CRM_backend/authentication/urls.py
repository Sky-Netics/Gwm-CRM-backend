from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RegisterView, LoginView, UserProfileView, AssignCompanyView, UserViewSet, UserDashboardView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('profile/', UserProfileView.as_view(), name='profile'),
    path('assign-company/', AssignCompanyView.as_view(), name='assign-company'),
    path('users/<int:user_id>/dashboard/', UserDashboardView.as_view(), name='user-dashboard'),
    # path('users/', UserViewSet, name='user-list'),
]