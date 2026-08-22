from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContestViewSet

router = DefaultRouter()
router.register(r"contests", ContestViewSet, basename="contest")

urlpatterns = [
    path("", include(router.urls)),
]
