from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiscussPostViewSet, DiscussCommentViewSet

router = DefaultRouter()
router.register(r"posts", DiscussPostViewSet, basename="discuss-posts")
router.register(r"comments", DiscussCommentViewSet, basename="discuss-comments")

urlpatterns = [
    path("discuss/", include(router.urls)),
]
