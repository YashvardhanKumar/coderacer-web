from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProblemViewSet, CodeblockViewSet, TestcaseViewSet,
    SolutionViewSet, TagsViewSet, DiscussViewSet
)

router = DefaultRouter()
router.register(r'problems', ProblemViewSet, basename='problem')
router.register(r'codeblocks', CodeblockViewSet, basename='codeblock')
router.register(r'testcases', TestcaseViewSet, basename='testcase')
router.register(r'solutions', SolutionViewSet, basename='solution')
router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'discussions', DiscussViewSet, basename='discuss')

urlpatterns = [
    path('', include(router.urls)),
]