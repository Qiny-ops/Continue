from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.viewsets import RequirementViewSet

router = DefaultRouter()
router.register(r'', RequirementViewSet, basename='requirement')

urlpatterns = [
    path('', include(router.urls)),
]
