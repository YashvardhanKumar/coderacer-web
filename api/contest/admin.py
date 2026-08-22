from django.contrib import admin
from .models import (
    Contest,
    ContestProblem,
    ContestRegistration,
    ContestParticipant,
    ContestSubmission,
)


class ContestProblemInline(admin.TabularInline):
    model = ContestProblem
    extra = 1
    fields = ("order", "problem", "points")
    ordering = ("order",)


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "is_weekly",
        "start_time",
        "duration_minutes",
        "end_time",
        "is_published",
        "status",
    )
    list_filter = ("is_weekly", "is_published", "start_time")
    search_fields = ("title", "description", "slug")
    inlines = [ContestProblemInline]


@admin.register(ContestProblem)
class ContestProblemAdmin(admin.ModelAdmin):
    list_display = ("contest", "order", "problem", "points")
    list_filter = ("contest",)
    search_fields = ("contest__title", "problem__name")


@admin.register(ContestRegistration)
class ContestRegistrationAdmin(admin.ModelAdmin):
    list_display = ("contest", "user", "registered_at")
    list_filter = ("contest",)
    search_fields = ("contest__title", "user__username", "user__email")


@admin.register(ContestParticipant)
class ContestParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "contest",
        "user",
        "score",
        "problems_solved",
        "penalty_seconds",
        "finish_time_seconds",
    )
    list_filter = ("contest",)
    search_fields = ("contest__title", "user__username")
    ordering = ("contest", "-score", "penalty_seconds", "finish_time_seconds")


@admin.register(ContestSubmission)
class ContestSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "contest",
        "problem",
        "user",
        "status",
        "is_accepted",
        "time_taken_seconds",
        "created_at",
    )
    list_filter = ("contest", "is_accepted", "status")
    search_fields = ("contest__title", "problem__name", "user__username")
