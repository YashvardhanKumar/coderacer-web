from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DiscussPost, DiscussComment, DiscussCategory

User = get_user_model()


class AuthorSummarySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "name", "profile_picture"]

    def get_name(self, obj):
        return obj.get_full_name() or obj.username


class DiscussCommentSerializer(serializers.ModelSerializer):
    author = AuthorSummarySerializer(read_only=True)
    upvotes_count = serializers.IntegerField(source="upvotes.count", read_only=True)
    downvotes_count = serializers.IntegerField(source="downvotes.count", read_only=True)
    vote_count = serializers.IntegerField(read_only=True)
    user_vote = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = DiscussComment
        fields = [
            "id",
            "author",
            "parent",
            "content",
            "upvotes_count",
            "downvotes_count",
            "vote_count",
            "user_vote",
            "replies",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_user_vote(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if obj.upvotes.filter(id=request.user.id).exists():
                return 1
            if obj.downvotes.filter(id=request.user.id).exists():
                return -1
        return 0

    def get_replies(self, obj):
        if obj.parent_id is not None:
            return []  # Only nest 1 level of replies for performance
        replies = (
            obj.replies.select_related("author")
            .prefetch_related("upvotes", "downvotes")
            .all()
        )
        return DiscussCommentSerializer(replies, many=True, context=self.context).data


class DiscussPostListSerializer(serializers.ModelSerializer):
    author = AuthorSummarySerializer(read_only=True)
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    vote_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    user_vote = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()

    class Meta:
        model = DiscussPost
        fields = [
            "id",
            "author",
            "title",
            "category",
            "category_display",
            "content_preview",
            "tags",
            "views",
            "vote_count",
            "comments_count",
            "pinned",
            "user_vote",
            "created_at",
            "updated_at",
        ]

    def get_user_vote(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if obj.upvotes.filter(id=request.user.id).exists():
                return 1
            if obj.downvotes.filter(id=request.user.id).exists():
                return -1
        return 0

    def get_content_preview(self, obj):
        if not obj.content:
            return ""
        lines = [
            line.strip()
            for line in obj.content.split("\n")
            if line.strip() and not line.strip().startswith("```")
        ][:3]
        preview = " ".join(lines)
        return (preview[:220] + "...") if len(preview) > 220 else preview


class DiscussPostDetailSerializer(serializers.ModelSerializer):
    author = AuthorSummarySerializer(read_only=True)
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    vote_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    user_vote = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = DiscussPost
        fields = [
            "id",
            "author",
            "title",
            "category",
            "category_display",
            "content",
            "tags",
            "views",
            "vote_count",
            "comments_count",
            "pinned",
            "user_vote",
            "comments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "views", "created_at", "updated_at"]

    def get_user_vote(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if obj.upvotes.filter(id=request.user.id).exists():
                return 1
            if obj.downvotes.filter(id=request.user.id).exists():
                return -1
        return 0

    def get_comments(self, obj):
        top_level_comments = (
            obj.comments.filter(parent__isnull=True)
            .select_related("author")
            .prefetch_related("upvotes", "replies__author", "replies__upvotes")
            .order_by("created_at")
        )
        return DiscussCommentSerializer(
            top_level_comments, many=True, context=self.context
        ).data


class DiscussPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscussPost
        fields = ["title", "category", "content", "tags"]

    def validate_title(self, value):
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Title must be at least 3 characters long."
            )
        return value.strip()

    def validate_content(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Post content must be at least 10 characters long."
            )
        return value
