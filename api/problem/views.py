from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
)
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count, Q, F
from .models import (
    Problem,
    Codeblock,
    Testcase,
    Solution,
    Tags,
    Discuss,
    AnswerStatus,
    Comment,
)
from django.db.models import Count, Q
from .models import Problem, Codeblock, Testcase, Solution, Tags, Discuss, AnswerStatus
from .serializers import (
    ProblemListSerializer,
    ProblemDetailSerializer,
    CodeblockSerializer,
    TestcaseSerializer,
    SolutionListSerializer,
    SolutionDetailSerializer,
    SolutionSubmitSerializer,
    TagsSerializer,
    DiscussListSerializer,
    DiscussDetailSerializer,
    ProblemStatisticsSerializer,
    CommentSerializer,
)
from engine.services import submit_to_judge0

# Map our internal Language choices to Judge0 language IDs
JUDGE0_LANGUAGE_MAP = {
    "CPP": 54,  # C++ (GCC 9.2.0)
    "JAVA": 62,  # Java (OpenJDK 13.0.1)
    "PYTHON": 71,  # Python (3.8.1)
    "JAVASCRIPT": 63,  # JavaScript (Node.js 12.14.0)
    "TYPESCRIPT": 74,  # TypeScript (3.7.4)
}

# Map Judge0 status IDs to our AnswerStatus
JUDGE0_STATUS_MAP = {
    3: AnswerStatus.ACCEPTED,  # Accepted
    4: AnswerStatus.WRONG_ANSWER,  # Wrong Answer
    5: AnswerStatus.TIME_LIMIT_EXCEEDED,  # Time Limit Exceeded
    6: AnswerStatus.COMPILATION_ERROR,  # Compilation Error
    7: AnswerStatus.RUNTIME_ERROR_SIGSEGV,  # Runtime Error (SIGSEGV)
    8: AnswerStatus.RUNTIME_ERROR_SIGXFSZ,  # Runtime Error (SIGXFSZ)
    9: AnswerStatus.RUNTIME_ERROR_SIGFPE,  # Runtime Error (SIGFPE)
    10: AnswerStatus.RUNTIME_ERROR_SIGABRT,  # Runtime Error (SIGABRT)
    11: AnswerStatus.RUNTIME_ERROR_NZEC,  # Runtime Error (NZEC)
    12: AnswerStatus.RUNTIME_ERROR_OTHER,  # Runtime Error (Other)
    13: AnswerStatus.INTERNAL_ERROR,  # Internal Error
    14: AnswerStatus.EXEC_FORMAT_ERROR,  # Exec Format Error
}


class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "id", "total_solutions"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if self.action == "list":
            queryset = Problem.objects.prefetch_related("tags")
        else:
            queryset = Problem.objects.prefetch_related(
                "tags", "codeblocks", "testcases"
            )

        queryset = queryset.annotate(
            total_solutions=Count("solutions", distinct=True),
            total_testcases=Count("testcases", distinct=True),
        )

        search = self.request.query_params.get("search")
        if search:
            search_filter = Q(name__icontains=search) | Q(
                problem_description__icontains=search
            )
            if search.isdigit():
                search_filter |= Q(id=int(search))
            queryset = queryset.filter(search_filter)

        difficulty = self.request.query_params.get("difficulty")
        if difficulty:
            difficulties = [
                value.strip().upper()
                for value in difficulty.split(",")
                if value.strip()
            ]
            queryset = queryset.filter(difficulty__in=difficulties)

        tags = self.request.query_params.get("tags")
        if tags:
            tag_values = [value.strip() for value in tags.split(",") if value.strip()]
            tag_ids = [value for value in tag_values if value.isdigit()]
            tag_names = [value for value in tag_values if not value.isdigit()]

            tag_filter = Q()
            if tag_ids:
                tag_filter |= Q(tags__id__in=tag_ids)
            if tag_names:
                tag_filter |= Q(tags__tags__in=tag_names)

            queryset = queryset.filter(tag_filter).distinct()

        progress = self.request.query_params.get("status")
        if progress:
            statuses = {
                value.strip().lower() for value in progress.split(",") if value.strip()
            }

            if not self.request.user.is_authenticated:
                if statuses == {"unsolved"}:
                    return queryset
                return queryset.none()

            attempted_ids = (
                Solution.objects.filter(user=self.request.user)
                .values_list("problem_id", flat=True)
                .distinct()
            )
            solved_ids = (
                Solution.objects.filter(
                    user=self.request.user, status=AnswerStatus.ACCEPTED
                )
                .values_list("problem_id", flat=True)
                .distinct()
            )

            progress_filter = Q()
            if "solved" in statuses:
                progress_filter |= Q(id__in=solved_ids)
            if "attempted" in statuses:
                progress_filter |= Q(id__in=attempted_ids) & ~Q(id__in=solved_ids)
            if "unsolved" in statuses:
                progress_filter |= ~Q(id__in=attempted_ids)

            queryset = queryset.filter(progress_filter)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ProblemListSerializer
        return ProblemDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        from .utils import record_active_problem_user, should_count_view

        instance = self.get_object()
        user_id = (
            f"user_{request.user.id}"
            if request.user.is_authenticated
            else f"anon_{request.session.session_key or request.META.get('REMOTE_ADDR', 'ip')}"
        )

        # Deduplicate view count per user/session cooldown
        if should_count_view(f"problem_{instance.pk}", user_id):
            Problem.objects.filter(pk=instance.pk).update(views=F("views") + 1)
            instance.refresh_from_db(fields=["views"])

        record_active_problem_user(instance.pk, user_id)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        problem = self.get_object()
        vote_type = request.data.get("type", "up")
        user = request.user

        if vote_type == "up":
            if problem.upvotes.filter(id=user.id).exists():
                problem.upvotes.remove(user)
                has_liked = False
            else:
                problem.upvotes.add(user)
                problem.downvotes.remove(user)
                has_liked = True
            has_disliked = False
        elif vote_type == "down":
            if problem.downvotes.filter(id=user.id).exists():
                problem.downvotes.remove(user)
                has_disliked = False
            else:
                problem.downvotes.add(user)
                problem.upvotes.remove(user)
                has_disliked = True
            has_liked = False
        else:
            return Response(
                {"error": "Invalid vote type. Must be 'up' or 'down'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "likes_count": problem.upvotes.count(),
                "dislikes_count": problem.downvotes.count(),
                "has_liked": has_liked,
                "has_disliked": has_disliked,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        problem = self.get_object()
        user = request.user

        if problem.favorited_by.filter(id=user.id).exists():
            problem.favorited_by.remove(user)
            is_favorited = False
        else:
            problem.favorited_by.add(user)
            is_favorited = True

        return Response(
            {
                "is_favorited": is_favorited,
                "favorites_count": problem.favorited_by.count(),
            }
        )

    @action(detail=True, methods=["post", "get"])
    def heartbeat(self, request, pk=None):
        from .utils import record_active_problem_user

        problem = self.get_object()
        user_id = (
            f"user_{request.user.id}"
            if request.user.is_authenticated
            else f"anon_{request.session.session_key or request.META.get('REMOTE_ADDR', 'ip')}"
        )
        active_count = record_active_problem_user(problem.pk, user_id)
        return Response(
            {
                "active_users": active_count,
                "views": problem.views,
                "likes_count": problem.upvotes.count(),
                "dislikes_count": problem.downvotes.count(),
            }
        )

    @action(detail=True, methods=["get"])
    def statistics(self, request, pk=None):
        """Get statistics for a specific problem"""
        problem = self.get_object()
        solutions = problem.solutions.all()

        total = solutions.count()
        successful = solutions.filter(status=AnswerStatus.ACCEPTED).count()

        # Group and count statuses in a single query
        status_counts = dict(
            solutions.values_list("status").annotate(count=Count("status"))
        )
        status_breakdown = {}
        for choice in AnswerStatus.choices:
            status_breakdown[choice[1]] = status_counts.get(choice[0], 0)

        # Group and count languages in a single query
        language_counts = dict(
            solutions.values_list("language").annotate(count=Count("language"))
        )
        language_breakdown = {}
        from user.models import CodingLanguage

        for lang_code, lang_name in CodingLanguage.choices:
            count = language_counts.get(lang_code, 0)
            if count > 0:
                language_breakdown[lang_name] = count

        data = {
            "total_submissions": total,
            "successful_submissions": successful,
            "success_rate": round((successful / total * 100), 2) if total > 0 else 0,
            "status_breakdown": status_breakdown,
            "language_breakdown": language_breakdown,
        }

        serializer = ProblemStatisticsSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def solutions(self, request, pk=None):
        """Get all solutions for a problem"""
        problem = self.get_object()
        solutions = problem.solutions.select_related("user").all()

        # Filter by status if provided
        status_filter = request.query_params.get("status", None)
        if status_filter:
            solutions = solutions.filter(status=status_filter)

        serializer = SolutionListSerializer(solutions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def discussions(self, request, pk=None):
        """Get all discussions for a problem"""
        problem = self.get_object()
        discussions = (
            problem.discussions.select_related("author").prefetch_related("tags").all()
        )
        serializer = DiscussListSerializer(discussions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_tag(self, request):
        """Filter problems by tag"""
        tag_name = request.query_params.get("tag", None)
        if not tag_name:
            return Response(
                {"error": "tag parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        problems = self.queryset.filter(tags__tags__icontains=tag_name)
        serializer = self.get_serializer(problems, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def my_attempts(self, request):
        """Get problems the user has attempted"""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        problem_ids = (
            Solution.objects.filter(user=request.user)
            .values_list("problem_id", flat=True)
            .distinct()
        )
        problems = self.queryset.filter(id__in=problem_ids)
        serializer = self.get_serializer(problems, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def random(self, request):
        """Pick a random problem from the current filtered set"""
        problem = self.filter_queryset(self.get_queryset()).order_by("?").first()
        if not problem:
            return Response(
                {"error": "No problems match the current filters"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProblemListSerializer(problem)
        return Response(serializer.data)


class CodeblockViewSet(viewsets.ModelViewSet):
    queryset = Codeblock.objects.select_related("problem").all()
    serializer_class = CodeblockSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        problem_id = self.request.query_params.get("problem_id", None)
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)
        return queryset


class TestcaseViewSet(viewsets.ModelViewSet):
    queryset = Testcase.objects.select_related("problem").all()
    serializer_class = TestcaseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        problem_id = self.request.query_params.get("problem_id", None)
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)
        return queryset


class SolutionViewSet(viewsets.ModelViewSet):
    queryset = Solution.objects.select_related("user", "problem").all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return SolutionListSerializer
        elif self.action == "submit":
            return SolutionSubmitSerializer
        return SolutionDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Users can only see their own solutions unless they're staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        # Filter by problem_id if provided
        problem_id = self.request.query_params.get("problem_id", None)
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)

        # Filter by status if provided
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    @action(detail=False, methods=["post"])
    def submit(self, request):
        """Submit a solution for evaluation asynchronously via Celery"""
        serializer = SolutionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        problem_id = serializer.validated_data["problem_id"]
        code = serializer.validated_data["code"]
        language = serializer.validated_data.get("language", request.user.default_lang)

        # Verify problem exists
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            return Response(
                {"error": "Problem does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Create solution with QUEUE status
            solution = Solution.objects.create(
                user=request.user,
                problem_id=problem_id,
                code=code,
                language=language,
                status=AnswerStatus.QUEUE,
            )

            # Trigger background task
            from engine.tasks import submit_solution_task

            submit_solution_task.delay(solution.id)

            response_serializer = SolutionDetailSerializer(solution)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as exc:
            return Response(
                {"error": f"Task queuing failed: {str(exc)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    @action(detail=False, methods=["get"])
    def my_solutions(self, request):
        """Get current user's solutions"""
        solutions = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(solutions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """Get user's solution statistics"""
        solutions = Solution.objects.filter(user=request.user)

        total = solutions.count()
        status_counts = {}
        for choice in AnswerStatus.choices:
            count = solutions.filter(status=choice[0]).count()
            status_counts[choice[1]] = count

        data = {
            "total_submissions": total,
            "successful_submissions": status_counts.get("Accepted", 0),
            "status_breakdown": status_counts,
            "unique_problems_attempted": solutions.values("problem").distinct().count(),
        }

        return Response(data)


class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["tags"]

    @action(detail=True, methods=["get"])
    def problems(self, request, pk=None):
        """Get all problems with this tag"""
        tag = self.get_object()
        problems = tag.problems.all()
        serializer = ProblemListSerializer(problems, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        """Get most used tags"""
        tags = self.queryset.annotate(problem_count=Count("problems")).order_by(
            "-problem_count"
        )[:10]
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)


class DiscussViewSet(viewsets.ModelViewSet):
    queryset = (
        Discuss.objects.select_related("author", "problem", "user")
        .prefetch_related("tags", "comments", "upvotes", "downvotes")
        .all()
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "body", "tags__tags"]
    ordering_fields = ["created_at", "views"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return DiscussListSerializer
        return DiscussDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by problem_id if provided
        problem_id = self.request.query_params.get("problem_id", None)
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)

        # Filter by is_editorial if provided
        is_editorial = self.request.query_params.get("is_editorial", None)
        if is_editorial is not None:
            queryset = queryset.filter(is_editorial=(is_editorial.lower() == "true"))

        # Filter by tags if provided
        tags = self.request.query_params.get("tags", None)
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            queryset = queryset.filter(tags__tags__in=tag_list).distinct()

        return queryset

    def retrieve(self, request, *args, **kwargs):
        from .utils import should_count_view

        instance = self.get_object()
        user_id = (
            f"user_{request.user.id}"
            if request.user.is_authenticated
            else f"anon_{request.session.session_key or request.META.get('REMOTE_ADDR', 'ip')}"
        )
        if should_count_view(f"discuss_{instance.pk}", user_id):
            Discuss.objects.filter(pk=instance.pk).update(views=F("views") + 1)
            instance.refresh_from_db(fields=["views"])

        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # Only allow posting if user has at least one accepted solution for this problem
        # unless they are staff
        if not request.user.is_staff:
            problem_id = request.data.get("problem")
            if not problem_id:
                return Response(
                    {"error": "problem_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            has_accepted = Solution.objects.filter(
                user=request.user, problem_id=problem_id, status=AnswerStatus.ACCEPTED
            ).exists()

            if not has_accepted:
                return Response(
                    {
                        "error": "You must have at least one Accepted submission for this problem to post a solution."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, user=self.request.user)

    def perform_update(self, serializer):
        # Only author can update
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("You can only edit your own discussions")
        serializer.save()

    def perform_destroy(self, instance):
        # Only author can delete
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("You can only delete your own discussions")
        instance.delete()

    @action(detail=True, methods=["post"])
    def upvote(self, request, pk=None):
        discuss = self.get_object()
        user = request.user
        if discuss.upvotes.filter(id=user.id).exists():
            discuss.upvotes.remove(user)
            has_upvoted = False
        else:
            discuss.upvotes.add(user)
            discuss.downvotes.remove(user)  # Remove downvote if exists
            has_upvoted = True

        return Response(
            {
                "status": "upvoted" if has_upvoted else "upvote removed",
                "upvote_count": discuss.upvotes.count(),
                "downvote_count": discuss.downvotes.count(),
                "has_upvoted": has_upvoted,
                "has_downvoted": False,
            }
        )

    @action(detail=True, methods=["post"])
    def downvote(self, request, pk=None):
        discuss = self.get_object()
        user = request.user
        if discuss.downvotes.filter(id=user.id).exists():
            discuss.downvotes.remove(user)
            has_downvoted = False
        else:
            discuss.downvotes.add(user)
            discuss.upvotes.remove(user)  # Remove upvote if exists
            has_downvoted = True

        return Response(
            {
                "status": "downvoted" if has_downvoted else "downvote removed",
                "upvote_count": discuss.upvotes.count(),
                "downvote_count": discuss.downvotes.count(),
                "has_upvoted": False,
                "has_downvoted": has_downvoted,
            }
        )

    @action(detail=True, methods=["post"])
    def add_comment(self, request, pk=None):
        discuss = self.get_object()
        parent_id = request.data.get("parent_id")
        body = request.data.get("body")

        if not body:
            return Response(
                {"error": "body is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        comment = Comment.objects.create(
            author=request.user, discuss=discuss, body=body, parent_id=parent_id
        )

        serializer = CommentSerializer(comment, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False, methods=["post"], url_path="comment/(?P<comment_pk>[^/.]+)/vote"
    )
    def vote_comment(self, request, comment_pk=None):
        try:
            comment = Comment.objects.get(pk=comment_pk)
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        vote_type = request.data.get("type")  # 'up' or 'down'
        user = request.user

        if vote_type == "up":
            if comment.upvotes.filter(id=user.id).exists():
                comment.upvotes.remove(user)
            else:
                comment.upvotes.add(user)
                comment.downvotes.remove(user)
        elif vote_type == "down":
            if comment.downvotes.filter(id=user.id).exists():
                comment.downvotes.remove(user)
            else:
                comment.downvotes.add(user)
                comment.upvotes.remove(user)

        return Response(
            {
                "status": "voted",
                "comment_id": comment.id,
                "upvote_count": comment.upvotes.count(),
                "downvote_count": comment.downvotes.count(),
                "has_upvoted": comment.upvotes.filter(id=user.id).exists(),
                "has_downvoted": comment.downvotes.filter(id=user.id).exists(),
            }
        )

    @action(detail=False, methods=["get"])
    def my_discussions(self, request):
        """Get current user's discussions"""
        discussions = self.queryset.filter(author=request.user)
        serializer = self.get_serializer(discussions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_problem(self, request):
        """Get discussions for a specific problem"""
        problem_id = request.query_params.get("problem_id", None)
        if not problem_id:
            return Response(
                {"error": "problem_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        discussions = self.queryset.filter(problem_id=problem_id)
        serializer = self.get_serializer(discussions, many=True)
        return Response(serializer.data)
