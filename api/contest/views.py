from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, F
from django.core.cache import cache
import json

from .models import (
    Contest,
    ContestProblem,
    ContestRegistration,
    ContestParticipant,
    ContestSubmission,
)
from .serializers import (
    ContestListSerializer,
    ContestDetailSerializer,
    ContestLeaderboardSerializer,
    ContestProblemDetailSerializer,
    ContestProblemListSerializer,
)
from problem.models import Problem, AnswerStatus


class ContestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Contest.objects.filter(is_published=True).order_by("-start_time")
    serializer_class = ContestListSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"

    def get_object(self):
        lookup_value = self.kwargs.get(self.lookup_field)
        if str(lookup_value).isdigit():
            return get_object_or_404(Contest, id=int(lookup_value), is_published=True)
        return get_object_or_404(Contest, slug=lookup_value, is_published=True)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ContestDetailSerializer
        return ContestListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Filter by status: UPCOMING, ONGOING, PAST
        status_param = request.query_params.get("status")
        now = timezone.now()
        if status_param:
            status_param = status_param.upper()
            if status_param == "UPCOMING":
                queryset = queryset.filter(start_time__gt=now)
            elif status_param == "ONGOING":
                queryset = queryset.filter(
                    start_time__lte=now,
                    end_time__gte=now,
                )
            elif status_param == "PAST":
                queryset = queryset.filter(end_time__lt=now)

        # Filter by type: weekly vs custom
        type_param = request.query_params.get("type")
        if type_param:
            if type_param.lower() == "weekly":
                queryset = queryset.filter(is_weekly=True)
            elif type_param.lower() == "custom":
                queryset = queryset.filter(is_weekly=False)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def register(self, request, id=None):
        contest = self.get_object()
        user = request.user

        # Cannot register if contest is past
        if contest.status == "PAST":
            return Response(
                {"error": "This contest has already ended."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reg, created = ContestRegistration.objects.get_or_create(
            contest=contest, user=user
        )

        # Also initialize or get ContestParticipant row for fast leaderboards
        ContestParticipant.objects.get_or_create(contest=contest, user=user)

        return Response(
            {
                "success": True,
                "message": f"Successfully registered for {contest.title}!",
                "registered": True,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def unregister(self, request, id=None):
        contest = self.get_object()
        user = request.user

        if contest.status != "UPCOMING":
            return Response(
                {"error": "You can only unregister from upcoming contests."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ContestRegistration.objects.filter(contest=contest, user=user).delete()
        ContestParticipant.objects.filter(contest=contest, user=user).delete()

        return Response(
            {
                "success": True,
                "message": f"Unregistered from {contest.title}.",
                "registered": False,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def leaderboard(self, request, id=None):
        contest = self.get_object()

        # Cache key for high-load optimization
        cache_key = f"contest_leaderboard_{contest.id}"
        cached_data = cache.get(cache_key)

        participants = (
            ContestParticipant.objects.filter(contest=contest)
            .select_related("user")
            .order_by("-score", "penalty_seconds", "finish_time_seconds")
        )

        # Assign ranks
        results = [
            {
                **ContestLeaderboardSerializer(p, context={"request": request}).data,
                "rank": rank,
            }
            for rank, p in enumerate(participants, start=1)
        ]

        response_data = {
            "contest_id": contest.id,
            "contest_title": contest.title,
            "contest_status": contest.status,
            "total_participants": len(results),
            "leaderboard": results[:100],  # Top 100 for fast payload
        }

        # If user is authenticated, append user's rank info
        if request.user.is_authenticated:
            user_entry = next(
                (item for item in results if item["user_id"] == request.user.id), None
            )
            response_data["user_ranking"] = user_entry

        # Cache for 5 seconds during ongoing contest, 60s if past
        ttl = 5 if contest.status == "ONGOING" else 60
        cache.set(cache_key, response_data, ttl)

        return Response(response_data)

    @action(
        detail=True,
        methods=["get"],
        url_path="problems/(?P<problem_id>[^/.]+)",
        permission_classes=[permissions.AllowAny],
    )
    def problem_detail(self, request, id=None, problem_id=None):
        contest = self.get_object()
        user = request.user
        is_staff = user.is_authenticated and user.is_staff

        # If contest is upcoming, disallow access unless staff
        if contest.status == "UPCOMING" and not is_staff:
            return Response(
                {
                    "error": "Contest has not started yet. Problems are hidden until start time."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get ContestProblem
        cp = get_object_or_404(
            ContestProblem.objects.select_related("problem", "contest"),
            contest=contest,
            problem_id=problem_id,
        )

        serializer = ContestProblemDetailSerializer(cp, context={"request": request})
        return Response(serializer.data)
