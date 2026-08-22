from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.shortcuts import redirect
from django.conf import settings
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from problem.serializers import UserSerializer, UserRegistrationSerializer
from problem.models import Solution, AnswerStatus
from .models import User
from social_django.utils import psa
from social_core.exceptions import MissingBackend, AuthTokenError, AuthForbidden
from social_core.backends.oauth import BaseOAuth2


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegistrationSerializer
        return UserSerializer

    def get_queryset(self):
        # Users can only see their own profile unless they're staff
        if self.request.user.is_staff:
            return super().get_queryset()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"])
    def update_language(self, request):
        """Update user's default programming language"""
        language = request.data.get("default_lang")
        if not language:
            return Response(
                {"error": "default_lang is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        user.default_lang = language
        user.save()
        return Response(
            {
                "message": "Default language updated successfully",
                "default_lang": user.default_lang,
            }
        )

    @action(detail=False, methods=["put", "patch"])
    def update_profile(self, request):
        """Update current user's profile"""
        serializer = self.get_serializer(
            request.user, data=request.data, partial=request.method == "PATCH"
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def profile(self, request):
        """Get current user's profile, activity, and coding progress"""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = request.user
        year_param = request.query_params.get("year")

        now = timezone.now()
        current_year = now.year
        join_year = user.date_joined.year if user.date_joined else current_year
        available_years = (
            list(range(join_year, current_year + 1))
            if join_year <= current_year
            else [current_year]
        )

        try:
            target_year = int(year_param) if year_param else current_year
        except (ValueError, TypeError):
            target_year = current_year

        solutions = Solution.objects.filter(user=user).select_related("problem")

        # Heatmap calculation for the specific year
        start_of_year = timezone.datetime(target_year, 1, 1).date()
        end_of_year = timezone.datetime(target_year, 12, 31).date()

        # Clamp start date to join date if target year is join year
        actual_start = max(start_of_year, user.date_joined.date())
        # Clamp end date to today if target year is current year
        actual_end = min(end_of_year, timezone.localdate())

        # Activity for the heatmap
        year_activity = {
            item["day"].isoformat(): item["count"]
            for item in solutions.filter(
                created_at__date__gte=actual_start, created_at__date__lte=actual_end
            )
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        }

        heatmap = []
        curr = actual_start
        while curr <= actual_end:
            date_str = curr.isoformat()
            heatmap.append({"date": date_str, "count": year_activity.get(date_str, 0)})
            curr += timedelta(days=1)

        # Stats and problem summaries
        solved_problem_ids = set(
            solutions.filter(status=AnswerStatus.ACCEPTED)
            .values_list("problem_id", flat=True)
            .distinct()
        )
        attempted_problem_ids = set(
            solutions.values_list("problem_id", flat=True).distinct()
        )
        attempted_only_ids = attempted_problem_ids - solved_problem_ids

        solved_problems = self._latest_solution_per_problem(
            solutions.filter(
                status=AnswerStatus.ACCEPTED, problem_id__in=solved_problem_ids
            )
        )
        attempted_problems = self._latest_solution_per_problem(
            solutions.filter(problem_id__in=attempted_only_ids)
        )

        difficulty_breakdown = {}
        for difficulty in ["EASY", "MEDIUM", "HARD"]:
            total = (
                solutions.filter(problem__difficulty=difficulty)
                .values("problem_id")
                .distinct()
                .count()
            )
            solved = (
                solutions.filter(
                    problem__difficulty=difficulty,
                    status=AnswerStatus.ACCEPTED,
                )
                .values("problem_id")
                .distinct()
                .count()
            )
            difficulty_breakdown[difficulty] = {
                "solved": solved,
                "attempted": total,
            }

        status_breakdown = {}
        for choice in AnswerStatus.choices:
            count = solutions.filter(status=choice[0]).count()
            status_breakdown[choice[1]] = count

        # Recent submissions for the side list
        recent_submissions = [
            {
                "id": solution.id,
                "problem_id": solution.problem_id,
                "problem_name": solution.problem.name,
                "difficulty": solution.problem.difficulty,
                "language": solution.language,
                "language_display": solution.get_language_display(),
                "status": solution.status,
                "status_display": solution.get_status_display(),
                "created_at": solution.created_at,
            }
            for solution in solutions.order_by("-created_at")[:12]
        ]

        def serialize_problem(solution):
            return {
                "id": solution.problem_id,
                "name": solution.problem.name,
                "difficulty": solution.problem.difficulty,
                "last_submitted_at": solution.created_at,
            }

        # For streak calculation, we need full activity history
        full_activity = {
            item["day"].isoformat(): item["count"]
            for item in solutions.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
        }

        total_submissions = solutions.count()
        successful = solutions.filter(status=AnswerStatus.ACCEPTED).count()

        from problem.models import Discuss as ProblemDiscuss
        from discuss.models import DiscussPost

        problem_discussions = [
            {
                "id": d.id,
                "problem_id": d.problem_id,
                "problem_name": d.problem.name if d.problem else "Problem",
                "problem_difficulty": d.problem.difficulty if d.problem else "EASY",
                "title": d.title,
                "views": d.views,
                "upvotes_count": d.upvotes.count(),
                "downvotes_count": d.downvotes.count(),
                "is_editorial": d.is_editorial,
                "created_at": d.created_at,
            }
            for d in ProblemDiscuss.objects.filter(author=user)
            .select_related("problem")
            .prefetch_related("upvotes", "downvotes")
            .order_by("-created_at")[:20]
        ]

        general_discussions = [
            {
                "id": p.id,
                "title": p.title,
                "category": p.category,
                "category_display": p.get_category_display(),
                "views": p.views,
                "upvotes_count": p.upvotes.count(),
                "downvotes_count": p.downvotes.count(),
                "vote_count": p.vote_count,
                "comments_count": p.comments_count,
                "tags": p.tags,
                "created_at": p.created_at,
            }
            for p in DiscussPost.objects.filter(author=user)
            .prefetch_related("upvotes", "downvotes", "comments")
            .order_by("-created_at")[:20]
        ]

        favorite_problems = [
            {
                "id": p.id,
                "name": p.name,
                "difficulty": p.difficulty,
                "created_at": p.created_at,
                "tags": [t.tags for t in p.tags.all()],
            }
            for p in user.favorite_problems.prefetch_related("tags")
            .all()
            .order_by("-id")
        ]

        data = {
            "user": UserSerializer(user, context={"request": request}).data,
            "stats": {
                "total_submissions": total_submissions,
                "successful_submissions": successful,
                "unique_problems_attempted": len(attempted_problem_ids),
                "unique_problems_solved": len(solved_problem_ids),
                "success_rate": (
                    round((successful / total_submissions * 100), 2)
                    if total_submissions
                    else 0
                ),
                "current_streak": self._calculate_streak(
                    full_activity, timezone.localdate()
                ),
                "active_days": len(full_activity),
                "difficulty_breakdown": difficulty_breakdown,
                "status_breakdown": status_breakdown,
            },
            "heatmap": heatmap,
            "recent_submissions": recent_submissions,
            "solved_problems": [
                serialize_problem(solution) for solution in solved_problems[:20]
            ],
            "attempted_problems": [
                serialize_problem(solution) for solution in attempted_problems[:20]
            ],
            "favorite_problems": favorite_problems,
            "problem_discussions": problem_discussions,
            "general_discussions": general_discussions,
            "available_years": available_years,
            "selected_year": target_year,
        }

        return Response(data)

    def change_password(self, request):
        """Change user password"""
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"error": "Both old_password and new_password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:
            return Response(
                {"error": "New password must be at least 8 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully"})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get user statistics"""
        user = request.user
        solutions = Solution.objects.filter(user=user)

        total_submissions = solutions.count()
        successful = solutions.filter(status=AnswerStatus.ACCEPTED).count()
        unique_problems = solutions.values("problem").distinct().count()

        status_breakdown = {}
        for choice in AnswerStatus.choices:
            count = solutions.filter(status=choice[0]).count()
            status_breakdown[choice[1]] = count

        data = {
            "total_submissions": total_submissions,
            "successful_submissions": successful,
            "unique_problems_attempted": unique_problems,
            "success_rate": (
                round((successful / total_submissions * 100), 2)
                if total_submissions > 0
                else 0
            ),
            "status_breakdown": status_breakdown,
        }

        return Response(data)

    def _calculate_streak(self, activity_counts, today):
        streak = 0
        cursor = today
        while activity_counts.get(cursor.isoformat(), 0) > 0:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def _latest_solution_per_problem(self, queryset):
        seen = set()
        results = []
        for solution in queryset.order_by("-created_at"):
            if solution.problem_id in seen:
                continue
            seen.add(solution.problem_id)
            results.append(solution)
        return results


class CustomAuthToken(ObtainAuthToken):
    """Custom authentication endpoint that returns user data with token"""

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Please provide both username and password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        token, created = Token.objects.get_or_create(user=user)

        return Response({"token": token.key, "user": UserSerializer(user).data})


class RegisterView(viewsets.ViewSet):
    """User registration endpoint"""

    permission_classes = [AllowAny]

    def create(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LogoutView(viewsets.ViewSet):
    """User logout endpoint"""

    permission_classes = [IsAuthenticated]

    def create(self, request):
        # Delete the user's token
        request.user.auth_token.delete()
        return Response(
            {"message": "Successfully logged out"}, status=status.HTTP_200_OK
        )


class SocialAuthView(APIView):
    """
    Callback view for social authentication.
    Django redirects here after successful OAuth handshake.
    We generate a DRF token and redirect back to the Next.js frontend.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication failed"}, status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=request.user)
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

        # Redirect to the frontend callback page with the token
        return redirect(f"{frontend_url}/auth-callback?token={token.key}")
