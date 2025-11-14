from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecordLabelViewSet

router = DefaultRouter()
router.register(r'labels', RecordLabelViewSet, basename='label')

urlpatterns = [
    path('', include(router.urls)),
]