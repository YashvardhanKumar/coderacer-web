import re
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from problem.models import Problem, AnswerStatus, Difficulty


class Contest(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Title of the contest. If left blank, auto-increments to 'Weekly run <number>'",
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    is_weekly = models.BooleanField(
        default=True,
        help_text="True if this is an official Weekly Run contest",
    )
    start_time = models.DateTimeField(help_text="Start date and time of the contest")
    duration_minutes = models.PositiveIntegerField(
        default=90, help_text="Contest duration in minutes"
    )
    end_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text="End date and time (automatically computed from duration if blank)",
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contests_created",
    )

    class Meta:
        db_table = "contest"
        verbose_name = "Contest"
        verbose_name_plural = "Contests"
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["start_time", "end_time"]),
            models.Index(fields=["is_weekly", "is_published"]),
        ]

    def __str__(self):
        return self.title or f"Contest #{self.id}"

    @property
    def status(self):
        now = timezone.now()
        calculated_end = self.end_time or (
            self.start_time + timedelta(minutes=self.duration_minutes)
        )
        if now < self.start_time:
            return "UPCOMING"
        elif self.start_time <= now <= calculated_end:
            return "ONGOING"
        else:
            return "PAST"

    def save(self, *args, **kwargs):
        # Auto-compute end_time if not explicitly provided
        if not self.end_time and self.start_time and self.duration_minutes:
            self.end_time = self.start_time + timedelta(minutes=self.duration_minutes)

        # Title auto-generation: If blank, default to 'Weekly run <number>'
        if not self.title or not self.title.strip():
            self.is_weekly = True
            weekly_nums = [
                int(m.group(1))
                for c in Contest.objects.filter(is_weekly=True)
                if (m := re.search(r"Weekly run (\d+)", c.title, re.I))
            ]
            self.title = f"Weekly run {max(weekly_nums, default=0) + 1}"
        elif not self.title.lower().startswith("weekly run"):
            self.is_weekly = False

        # Generate unique slug
        if not self.slug:
            from django.utils.text import slugify

            base_slug = (
                slugify(self.title) or f"contest-{int(timezone.now().timestamp())}"
            )
            slug = base_slug
            counter = 1
            while Contest.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)


class ContestProblem(models.Model):
    contest = models.ForeignKey(
        Contest, on_delete=models.CASCADE, related_name="contest_problems"
    )
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="contest_assignments"
    )
    order = models.PositiveIntegerField(
        default=1, help_text="Order in contest (1=Q1, 2=Q2, etc.)"
    )
    points = models.PositiveIntegerField(
        default=3, help_text="Score points awarded for solving this problem"
    )

    class Meta:
        db_table = "contest_problem"
        verbose_name = "Contest Problem"
        verbose_name_plural = "Contest Problems"
        ordering = ["contest", "order"]
        unique_together = (("contest", "problem"), ("contest", "order"))
        indexes = [
            models.Index(fields=["contest", "order"]),
        ]

    def __str__(self):
        return f"[{self.contest.title}] Q{self.order}: {self.problem.name} ({self.points} pts)"


class ContestRegistration(models.Model):
    contest = models.ForeignKey(
        Contest, on_delete=models.CASCADE, related_name="registrations"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contest_registrations",
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contest_registration"
        verbose_name = "Contest Registration"
        verbose_name_plural = "Contest Registrations"
        unique_together = ("contest", "user")
        indexes = [
            models.Index(fields=["contest", "user"]),
        ]

    def __str__(self):
        return f"{self.user.username} registered for {self.contest.title}"


class ContestParticipant(models.Model):
    """
    Denormalized fast-lookup table for real-time leaderboard rendering.
    Allows O(log N) indexed queries under heavy concurrent load.
    """

    contest = models.ForeignKey(
        Contest, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contest_participations",
    )
    score = models.PositiveIntegerField(
        default=0, help_text="Total contest points earned"
    )
    penalty_seconds = models.PositiveIntegerField(
        default=0, help_text="Penalty in seconds from wrong submissions"
    )
    finish_time_seconds = models.PositiveIntegerField(
        default=0, help_text="Seconds from contest start to last AC"
    )
    problems_solved = models.PositiveIntegerField(default=0)
    # JSON breakdown: e.g. {"<problem_id>": {"status": "AC", "wrong_attempts": 1, "time_seconds": 450, "points": 4}}
    problem_details = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contest_participant"
        verbose_name = "Contest Participant Score"
        verbose_name_plural = "Contest Participant Scores"
        unique_together = ("contest", "user")
        ordering = ["-score", "penalty_seconds", "finish_time_seconds"]
        indexes = [
            models.Index(
                fields=["contest", "-score", "penalty_seconds", "finish_time_seconds"]
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.contest.title}: {self.score} pts"


class ContestSubmission(models.Model):
    contest = models.ForeignKey(
        Contest, on_delete=models.CASCADE, related_name="contest_submissions"
    )
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="contest_submissions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contest_submissions",
    )
    status = models.CharField(max_length=30, choices=AnswerStatus.choices)
    is_accepted = models.BooleanField(default=False)
    time_taken_seconds = models.PositiveIntegerField(
        default=0, help_text="Seconds from contest start"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contest_submission"
        verbose_name = "Contest Submission"
        verbose_name_plural = "Contest Submissions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["contest", "problem"]),
            models.Index(fields=["contest", "user"]),
        ]

    def __str__(self):
        return f"ContestSub #{self.id} by {self.user.username} for [{self.contest.title}] Problem #{self.problem_id} ({self.status})"
