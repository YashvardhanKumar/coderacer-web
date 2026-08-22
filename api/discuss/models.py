from django.db import models
from django.conf import settings


class DiscussCategory(models.TextChoices):
    GENERAL = "GENERAL", "General Discussion"
    INTERVIEW_EXPERIENCE = "INTERVIEW_EXPERIENCE", "Interview Experience"
    INTERVIEW_QUESTION = "INTERVIEW_QUESTION", "Interview Question"
    CAREER = "CAREER", "Career & Growth"
    COMPENSATION = "COMPENSATION", "Compensation"
    FEEDBACK = "FEEDBACK", "Feedback & Suggestions"


class DiscussPost(models.Model):
    id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discuss_posts",
    )
    title = models.CharField(max_length=255)
    category = models.CharField(
        max_length=30,
        choices=DiscussCategory.choices,
        default=DiscussCategory.GENERAL,
        db_index=True,
    )
    content = models.TextField(help_text="Post body in Markdown format")
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of string tags, e.g. ['Google', 'System Design']",
    )
    views = models.PositiveIntegerField(default=0)
    upvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="upvoted_general_posts",
        blank=True,
    )
    downvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="downvoted_general_posts",
        blank=True,
    )
    pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "discuss_post"
        verbose_name = "Discuss Post"
        verbose_name_plural = "Discuss Posts"
        ordering = ["-pinned", "-created_at"]
        indexes = [
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["pinned", "-created_at"]),
        ]

    def __str__(self):
        return f"[{self.category}] {self.title} by {self.author.username}"

    @property
    def vote_count(self):
        return self.upvotes.count() - self.downvotes.count()

    @property
    def comments_count(self):
        return self.comments.count()


class DiscussComment(models.Model):
    id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(
        DiscussPost,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discuss_post_comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    content = models.TextField()
    upvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="upvoted_general_comments",
        blank=True,
    )
    downvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="downvoted_general_comments",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "discuss_comment"
        verbose_name = "Discuss Comment"
        verbose_name_plural = "Discuss Comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on post #{self.post_id}"

    @property
    def vote_count(self):
        return self.upvotes.count() - self.downvotes.count()
