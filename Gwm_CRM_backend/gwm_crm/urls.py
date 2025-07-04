from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, ContactViewSet, ContactDocumentViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'contacts', ContactViewSet)
# router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('contacts/<int:contact_pk>/documents/', 
        ContactDocumentViewSet.as_view({'post': 'create', 'get': 'list'})),
    path('contacts/<int:contact_pk>/documents/<int:pk>/',
        ContactDocumentViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='contact-document-detail'
    )
    ]