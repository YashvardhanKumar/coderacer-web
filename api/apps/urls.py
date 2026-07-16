"""
URL configuration for apps project.
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from problem.admin_views import (
    rootops,
    add_ai_testcases,
    root_login,
    add_problem_custom,
    add_testcase_custom,
    moderator_login,
    generate_testcases_async,
    generate_codeblocks_preview,
    check_codeblocks_status,
    generate_programmatic_async,
    get_problem_scaffolds,
    generate_generator_code_ai,
    save_generator_code,
)
from ai.views import TaskStatusView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin & Core Backend Features
    path("api/admin/", admin.site.urls),
    path("api/ckeditor/", include("ckeditor_uploader.urls")),
    # Root Ops Dashboard
    path(
        "api/rootops/",
        include(
            [
                path("", rootops, name="rootops"),
                path("add-problem/", add_problem_custom, name="add_problem_custom"),
                path("add-testcase/", add_testcase_custom, name="add_testcase_custom"),
                path(
                    "generate-ai-async/",
                    generate_testcases_async,
                    name="generate_ai_async",
                ),
                path(
                    "generate-programmatic-async/",
                    generate_programmatic_async,
                    name="generate_programmatic_async",
                ),
                path(
                    "get-problem-scaffolds/",
                    get_problem_scaffolds,
                    name="get_problem_scaffolds",
                ),
                path(
                    "generate-generator-code-ai/",
                    generate_generator_code_ai,
                    name="generate_generator_code_ai",
                ),
                path(
                    "save-generator-code/",
                    save_generator_code,
                    name="save_generator_code",
                ),
                path(
                    "generate-codeblocks-preview/",
                    generate_codeblocks_preview,
                    name="generate_codeblocks_preview",
                ),
                path(
                    "check-codeblocks/",
                    check_codeblocks_status,
                    name="check_codeblocks_status",
                ),
                path(
                    "task-status/<str:task_id>/",
                    TaskStatusView.as_view(),
                    name="task_status",
                ),
                path("add-ai-testcases/", add_ai_testcases, name="add_ai_testcases"),
                path("login/", root_login, name="root_login"),
                path("moderator-login/", moderator_login, name="moderator_login"),
            ]
        ),
    ),
    # App-specific APIs
    path("api/social/", include("social_django.urls", namespace="social")),
    path("api/auth/", include("user.urls")),
    path("api/engine/", include("engine.urls")),
    path("api/ai/", include("ai.urls")),
    path("api/", include("problem.urls")),
    # Documentation & Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
