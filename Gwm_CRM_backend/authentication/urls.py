from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RegisterView, LoginView, UserProfileView, AssignCompanyView, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('assign-company/', AssignCompanyView.as_view(), name='assign-company'),
    # path('users/', UserViewSet, name='user-list'),
]