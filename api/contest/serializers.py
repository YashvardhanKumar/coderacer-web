from rest_framework import serializers
from .models import (
    Contest,
    ContestProblem,
    ContestRegistration,
    ContestParticipant,
    ContestSubmission,
)
from problem.serializers import CodeblockSerializer, TestcaseSerializer
from problem.models import Problem, AnswerStatus


class ContestProblemListSerializer(serializers.ModelSerializer):
    problem_id = serializers.IntegerField(source="problem.id", read_only=True)
    name = serializers.CharField(source="problem.name", read_only=True)
    difficulty = serializers.CharField(source="problem.difficulty", read_only=True)
    user_status = serializers.SerializerMethodField()
    attempted_count = serializers.SerializerMethodField()
    submitted_count = serializers.SerializerMethodField()
    accepted_count = serializers.SerializerMethodField()

    class Meta:
        model = ContestProblem
        fields = [
            "id",
            "problem_id",
            "order",
            "points",
            "name",
            "difficulty",
            "user_status",
            "attempted_count",
            "submitted_count",
            "accepted_count",
        ]

    def get_user_status(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return "pending"
        user = request.user
        # Check from ContestParticipant problem_details or ContestSubmission
        has_ac = ContestSubmission.objects.filter(
            contest=obj.contest, problem=obj.problem, user=user, is_accepted=True
        ).exists()
        if has_ac:
            return "done"
        has_attempt = ContestSubmission.objects.filter(
            contest=obj.contest, problem=obj.problem, user=user
        ).exists()
        if has_attempt:
            return "attempted"
        return "pending"

    def get_attempted_count(self, obj):
        # Distinct users who attempted/submitted
        return (
            ContestSubmission.objects.filter(contest=obj.contest, problem=obj.problem)
            .values("user")
            .distinct()
            .count()
        )

    def get_submitted_count(self, obj):
        return ContestSubmission.objects.filter(
            contest=obj.contest, problem=obj.problem
        ).count()

    def get_accepted_count(self, obj):
        return (
            ContestSubmission.objects.filter(
                contest=obj.contest, problem=obj.problem, is_accepted=True
            )
            .values("user")
            .distinct()
            .count()
        )


class ContestListSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    registered_count = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()
    total_problems = serializers.SerializerMethodField()

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "is_weekly",
            "start_time",
            "duration_minutes",
            "end_time",
            "status",
            "is_published",
            "registered_count",
            "is_registered",
            "total_problems",
        ]

    def get_registered_count(self, obj):
        return obj.registrations.count()

    def get_is_registered(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.registrations.filter(user=request.user).exists()

    def get_total_problems(self, obj):
        return obj.contest_problems.count()


class ContestDetailSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    registered_count = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()
    problems = serializers.SerializerMethodField()
    user_score = serializers.SerializerMethodField()
    user_rank = serializers.SerializerMethodField()

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "is_weekly",
            "start_time",
            "duration_minutes",
            "end_time",
            "status",
            "is_published",
            "registered_count",
            "is_registered",
            "problems",
            "user_score",
            "user_rank",
        ]

    def get_registered_count(self, obj):
        return obj.registrations.count()

    def get_is_registered(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.registrations.filter(user=request.user).exists()

    def get_problems(self, obj):
        # Only hide problems if contest is UPCOMING and user is not staff
        request = self.context.get("request")
        is_staff = request and request.user.is_authenticated and request.user.is_staff
        if obj.status == "UPCOMING" and not is_staff:
            # Return masked overview (order & points only)
            return [
                {
                    "id": cp.id,
                    "order": cp.order,
                    "points": cp.points,
                    "name": f"Problem {cp.order}",
                    "difficulty": cp.problem.difficulty,
                    "user_status": "pending",
                }
                for cp in obj.contest_problems.all().order_by("order")
            ]
        contest_problems = obj.contest_problems.select_related("problem").order_by(
            "order"
        )
        return ContestProblemListSerializer(
            contest_problems, many=True, context=self.context
        ).data

    def get_user_score(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0
        part = ContestParticipant.objects.filter(contest=obj, user=request.user).first()
        return part.score if part else 0

    def get_user_rank(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        part = ContestParticipant.objects.filter(contest=obj, user=request.user).first()
        if not part or part.score == 0:
            return None
        higher_count = ContestParticipant.objects.filter(
            contest=obj, score__gt=part.score
        ).count()
        same_score_better_penalty = ContestParticipant.objects.filter(
            contest=obj,
            score=part.score,
            penalty_seconds__lt=part.penalty_seconds,
        ).count()
        return higher_count + same_score_better_penalty + 1


class ContestLeaderboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)
    profile_picture = serializers.SerializerMethodField()
    rank = serializers.IntegerField(read_only=True)

    class Meta:
        model = ContestParticipant
        fields = [
            "rank",
            "user_id",
            "username",
            "name",
            "profile_picture",
            "score",
            "penalty_seconds",
            "finish_time_seconds",
            "problems_solved",
            "problem_details",
            "updated_at",
        ]

    def get_profile_picture(self, obj):
        if obj.user.profile_picture:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.user.profile_picture.url)
            return obj.user.profile_picture.url
        return f"https://api.dicebear.com/7.x/avataaars/svg?seed={obj.user.username}"


class ContestProblemDetailSerializer(serializers.ModelSerializer):
    contest_id = serializers.IntegerField(source="contest.id", read_only=True)
    contest_title = serializers.CharField(source="contest.title", read_only=True)
    contest_status = serializers.CharField(source="contest.status", read_only=True)
    contest_start_time = serializers.DateTimeField(
        source="contest.start_time", read_only=True
    )
    contest_end_time = serializers.DateTimeField(
        source="contest.end_time", read_only=True
    )
    problem_id = serializers.IntegerField(source="problem.id", read_only=True)
    name = serializers.CharField(source="problem.name", read_only=True)
    problem_description = serializers.CharField(
        source="problem.problem_description", read_only=True
    )
    difficulty = serializers.CharField(source="problem.difficulty", read_only=True)
    codeblocks = serializers.SerializerMethodField()
    testcases = serializers.SerializerMethodField()
    variables = serializers.SerializerMethodField()
    user_status = serializers.SerializerMethodField()
    attempted_count = serializers.SerializerMethodField()
    submitted_count = serializers.SerializerMethodField()
    accepted_count = serializers.SerializerMethodField()
    prev_problem_id = serializers.SerializerMethodField()
    next_problem_id = serializers.SerializerMethodField()
    contest_problems = serializers.SerializerMethodField()

    class Meta:
        model = ContestProblem
        fields = [
            "id",
            "contest_id",
            "contest_title",
            "contest_status",
            "contest_start_time",
            "contest_end_time",
            "problem_id",
            "order",
            "points",
            "name",
            "problem_description",
            "difficulty",
            "codeblocks",
            "testcases",
            "variables",
            "user_status",
            "attempted_count",
            "submitted_count",
            "accepted_count",
            "prev_problem_id",
            "next_problem_id",
            "contest_problems",
        ]

    def get_codeblocks(self, obj):
        return CodeblockSerializer(
            obj.problem.codeblocks.all(), many=True, context=self.context
        ).data

    def get_testcases(self, obj):
        # In contest, only return display_testcase=True
        samples = obj.problem.testcases.filter(display_testcase=True)
        return TestcaseSerializer(samples, many=True, context=self.context).data

    def get_variables(self, obj):
        from problem.serializers import VariableSerializer

        return VariableSerializer(
            obj.problem.variables.all(), many=True, context=self.context
        ).data

    def get_user_status(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return "pending"
        has_ac = ContestSubmission.objects.filter(
            contest=obj.contest,
            problem=obj.problem,
            user=request.user,
            is_accepted=True,
        ).exists()
        if has_ac:
            return "done"
        has_attempt = ContestSubmission.objects.filter(
            contest=obj.contest, problem=obj.problem, user=request.user
        ).exists()
        return "attempted" if has_attempt else "pending"

    def get_attempted_count(self, obj):
        return (
            ContestSubmission.objects.filter(contest=obj.contest, problem=obj.problem)
            .values("user")
            .distinct()
            .count()
        )

    def get_submitted_count(self, obj):
        return ContestSubmission.objects.filter(
            contest=obj.contest, problem=obj.problem
        ).count()

    def get_accepted_count(self, obj):
        return (
            ContestSubmission.objects.filter(
                contest=obj.contest, problem=obj.problem, is_accepted=True
            )
            .values("user")
            .distinct()
            .count()
        )

    def get_prev_problem_id(self, obj):
        prev_cp = (
            ContestProblem.objects.filter(contest=obj.contest, order__lt=obj.order)
            .order_by("-order")
            .first()
        )
        return prev_cp.problem.id if prev_cp else None

    def get_next_problem_id(self, obj):
        next_cp = (
            ContestProblem.objects.filter(contest=obj.contest, order__gt=obj.order)
            .order_by("order")
            .first()
        )
        return next_cp.problem.id if next_cp else None

    def get_contest_problems(self, obj):
        # Summary list of all problems in contest for sidebar
        cps = obj.contest.contest_problems.select_related("problem").order_by("order")
        return ContestProblemListSerializer(cps, many=True, context=self.context).data
