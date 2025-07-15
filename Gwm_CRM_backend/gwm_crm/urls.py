from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, ContactViewSet, ContactDocumentViewSet, OpportunityViewSet, ProductViewSet, InteractionViewSet, TaskViewSet, InteractionDocumentViewSet, CompanyCSVUploadView

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'opportunities', OpportunityViewSet)
router.register(r'products', ProductViewSet)
router.register(r'interactions', InteractionViewSet)
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'interactions/(?P<interaction_pk>\d+)/documents', InteractionDocumentViewSet, basename='interaction-documents')

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
    ),
    path('tasks/my_tasks/', TaskViewSet.as_view({'get': 'my_tasks'}), name='my-tasks'),
    path('tasks/dashboard/', TaskViewSet.as_view({'get': 'dashboard'}), name='task-dashboard'),
    path('api/companies/upload-csv/', CompanyCSVUploadView.as_view(), name='company-upload-csv'),
    ]
