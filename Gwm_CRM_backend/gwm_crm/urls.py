from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (CompanyViewSet, ContactViewSet, ContactDocumentViewSet, OpportunityViewSet,
                    ProductViewSet, InteractionViewSet, TaskViewSet, InteractionDocumentViewSet,
                    CompanyCSVUploadView, MarkNotificationsReadView, UnreadNotificationsView, AllNotificationsView,
                    MeetingViewSet, CompanyFileViewSet)

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'opportunities', OpportunityViewSet)
router.register(r'products', ProductViewSet)
router.register(r'interactions', InteractionViewSet)
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'meetings', MeetingViewSet, basename='meeting')
router.register(r'interactions/(?P<interaction_pk>\d+)/documents', InteractionDocumentViewSet, basename='interaction-documents')
# router.register(r'companies-files', CompanyFileViewSet, basename='company-files')

urlpatterns = [
    path('', include(router.urls)),
    path('companies/<int:pk>/files/business-card/', CompanyFileViewSet.as_view({'get': 'business_card', 'post': 'business_card', 'delete': 'business_card'})),
    path('companies/<int:pk>/files/catalogs/', CompanyFileViewSet.as_view({'get': 'catalogs', 'post': 'catalogs', 'delete': 'catalogs'})),
    path('companies/<int:pk>/files/signed_contracts/', CompanyFileViewSet.as_view({'get': 'signed_contracts', 'post': 'signed_contracts', 'delete': 'signed_contracts'})),
    path('companies/<int:pk>/files/correspondence/', CompanyFileViewSet.as_view({'get': 'correspondence', 'post': 'correspondence', 'delete': 'correspondence'})),
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
    # path('companies/export/', CompanyViewSet.as_view({'get': 'export'}), name='company-export'),
    # path('companies/<int:pk>/export-one/', CompanyViewSet.as_view({'get': 'export_one'}), name='company-export-one'),
    path('tasks/my_tasks/', TaskViewSet.as_view({'get': 'my_tasks'}), name='my-tasks'),
    path('tasks/dashboard/', TaskViewSet.as_view({'get': 'dashboard'}), name='task-dashboard'),
    path('api/companies/upload-csv/', CompanyCSVUploadView.as_view(), name='company-upload-csv'),
    path('notifications/all/', AllNotificationsView.as_view(), name='all-notifications'),    path('api/notifications/unread/', UnreadNotificationsView.as_view(), name='notifications-unread'),
    path('api/notifications/mark-as-seen/', MarkNotificationsReadView.as_view(), name='notifications-mark-seen'),
    ]
