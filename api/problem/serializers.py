from rest_framework import serializers
from .models import (
    Problem,
    Codeblock,
    Testcase,
    Solution,
    Tags,
    ProblemTags,
    Discuss,
    DiscussTags,
    AnswerStatus,
    Comment,
    Variable,
)
from user.models import User, CodingLanguage


class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "name",
            "default_lang",
            "profile_picture",
            "profile_picture_url",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def get_profile_picture_url(self, obj):
        if not obj.profile_picture:
            return None

        request = self.context.get("request")
        url = obj.profile_picture.url
        if request:
            return request.build_absolute_uri(url)
        return url


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "name", "password", "password2", "default_lang"]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ["id", "tags"]
        read_only_fields = ["id"]


class CodeblockSerializer(serializers.ModelSerializer):
    language_display = serializers.CharField(
        source="get_language_display", read_only=True
    )
    full_code = serializers.SerializerMethodField()
    language = serializers.ChoiceField(choices=CodingLanguage.choices)

    class Meta:
        model = Codeblock
        fields = [
            "id",
            "problem",
            "block",
            "runner_code",
            "language",
            "language_display",
            "full_code",
        ]
        read_only_fields = ["id"]

    def get_full_code(self, obj):
        from problem.utils import IMPORT_BLOCKS, clean_js_ts_fs_imports

        imports = IMPORT_BLOCKS.get(obj.language, "")
        cleaned_block = clean_js_ts_fs_imports(obj.block, obj.language)
        cleaned_runner = clean_js_ts_fs_imports(obj.runner_code, obj.language)
        return f"{imports}\n\n{cleaned_block}\n\n{cleaned_runner}"


class TestcaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testcase
        fields = [
            "id",
            "problem",
            "input",
            "output",
            "display_testcase",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TestcaseListSerializer(serializers.ModelSerializer):
    """Serializer without testcase content for listing"""

    class Meta:
        model = Testcase
        fields = [
            "id",
            "input",
            "output",
            "display_testcase",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProblemListSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True, read_only=True)
    total_solutions = serializers.SerializerMethodField()
    total_testcases = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = [
            "id",
            "name",
            "problem_description",
            "difficulty",
            "tags",
            "created_at",
            "total_solutions",
            "total_testcases",
        ]
        read_only_fields = ["id", "created_at"]

    def get_total_solutions(self, obj):
        return getattr(obj, "total_solutions", 0)

    def get_total_testcases(self, obj):
        return getattr(obj, "total_testcases", 0)


class VariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variable
        fields = ["id", "name", "type", "template_type", "array_dimensions"]


class ProblemDetailSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    codeblocks = CodeblockSerializer(many=True, read_only=True)
    testcases = TestcaseListSerializer(many=True, read_only=True)
    variables = VariableSerializer(many=True, read_only=True)
    is_multi = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()
    has_disliked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    active_users = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = [
            "id",
            "name",
            "problem_description",
            "difficulty",
            "tags",
            "tag_ids",
            "codeblocks",
            "testcases",
            "variables",
            "validator_type",
            "custom_validator",
            "views",
            "likes_count",
            "dislikes_count",
            "has_liked",
            "has_disliked",
            "is_favorited",
            "active_users",
            "created_at",
            "is_multi",
            "success_rate",
        ]
        read_only_fields = ["id", "views", "created_at"]

    def get_likes_count(self, obj):
        return obj.upvotes.count()

    def get_dislikes_count(self, obj):
        return obj.downvotes.count()

    def get_has_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.upvotes.filter(id=request.user.id).exists()
        return False

    def get_has_disliked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.downvotes.filter(id=request.user.id).exists()
        return False

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(id=request.user.id).exists()
        return False

    def get_active_users(self, obj):
        from .utils import get_active_problem_users_count

        return get_active_problem_users_count(obj.id)

    def get_is_multi(self, obj):
        methods = list(obj.methods.all())
        return len(methods) > 1 or any(m.is_constructor for m in methods)

    def get_success_rate(self, obj):
        total = obj.solutions.count()
        if total == 0:
            return 0
        success = obj.solutions.filter(status=AnswerStatus.ACCEPTED).count()
        return round((success / total) * 100, 2)

    def create(self, validated_data):
        tag_ids = validated_data.pop("tag_ids", [])
        problem = Problem.objects.create(**validated_data)
        if tag_ids:
            problem.tags.set(tag_ids)
        return problem

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop("tag_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        return instance


class SolutionListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    problem_id = serializers.IntegerField(read_only=True, source="problem.id")
    language_display = serializers.CharField(
        source="get_language_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Solution
        fields = [
            "id",
            "user",
            "problem_id",
            "language",
            "language_display",
            "status",
            "status_display",
            "testcase_results",
            "created_at",
        ]
        read_only_fields = ["id", "user", "status", "created_at", "testcase_results"]


class SolutionDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    language_display = serializers.CharField(
        source="get_language_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Solution
        fields = [
            "id",
            "user",
            "problem",
            "code",
            "language",
            "language_display",
            "status",
            "status_display",
            "testcase_results",
            "created_at",
        ]
        read_only_fields = ["id", "user", "status", "created_at", "testcase_results"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        # Set default language from user if not provided
        if "language" not in validated_data:
            validated_data["language"] = self.context["request"].user.default_lang
        return super().create(validated_data)


class SolutionSubmitSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    code = serializers.CharField()
    language = serializers.CharField(
        required=False,
        help_text="Programming language. If not provided, uses user's default language.",
    )

    def validate_language(self, value):
        if value and value not in dict(CodingLanguage.choices):
            raise serializers.ValidationError("Invalid language selection.")
        return value

    def validate_problem_id(self, value):
        if not Problem.objects.filter(id=value).exists():
            raise serializers.ValidationError("Problem does not exist")
        return value


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    upvote_count = serializers.SerializerMethodField()
    downvote_count = serializers.SerializerMethodField()
    has_upvoted = serializers.SerializerMethodField()
    has_downvoted = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "discuss",
            "body",
            "parent",
            "replies",
            "upvote_count",
            "downvote_count",
            "has_upvoted",
            "has_downvoted",
            "created_at",
        ]
        read_only_fields = ["id", "author", "created_at"]

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(
                obj.replies.all(), many=True, context=self.context
            ).data
        return []

    def get_upvote_count(self, obj):
        return obj.upvotes.count()

    def get_downvote_count(self, obj):
        return obj.downvotes.count()

    def get_has_upvoted(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.upvotes.filter(id=user.id).exists()
        return False

    def get_has_downvoted(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.downvotes.filter(id=user.id).exists()
        return False


class DiscussListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagsSerializer(many=True, read_only=True)
    problem_id = serializers.IntegerField(read_only=True, source="problem.id")
    upvote_count = serializers.SerializerMethodField()
    downvote_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Discuss
        fields = [
            "id",
            "title",
            "body",
            "author",
            "problem_id",
            "tags",
            "created_at",
            "views",
            "upvote_count",
            "downvote_count",
            "comment_count",
            "is_editorial",
        ]
        read_only_fields = ["id", "author", "created_at", "views", "is_editorial"]

    def get_upvote_count(self, obj):
        return obj.upvotes.count()

    def get_downvote_count(self, obj):
        return obj.downvotes.count()

    def get_comment_count(self, obj):
        return obj.comments.count()


class DiscussDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    tags = TagsSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    comments = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    upvote_count = serializers.SerializerMethodField()
    downvote_count = serializers.SerializerMethodField()
    has_upvoted = serializers.SerializerMethodField()
    has_downvoted = serializers.SerializerMethodField()

    class Meta:
        model = Discuss
        fields = [
            "id",
            "title",
            "body",
            "author",
            "user",
            "problem",
            "tags",
            "tag_ids",
            "created_at",
            "views",
            "upvote_count",
            "downvote_count",
            "comment_count",
            "has_upvoted",
            "has_downvoted",
            "is_editorial",
            "comments",
        ]
        read_only_fields = [
            "id",
            "author",
            "user",
            "created_at",
            "views",
            "is_editorial",
        ]

    def get_comments(self, obj):
        # Only return top-level comments (parent=None)
        comments = obj.comments.filter(parent=None)
        return CommentSerializer(comments, many=True, context=self.context).data

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_upvote_count(self, obj):
        return obj.upvotes.count()

    def get_downvote_count(self, obj):
        return obj.downvotes.count()

    def get_has_upvoted(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.upvotes.filter(id=user.id).exists()
        return False

    def get_has_downvoted(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.downvotes.filter(id=user.id).exists()
        return False

    def create(self, validated_data):
        tag_ids = validated_data.pop("tag_ids", [])
        request = self.context.get("request")
        validated_data["author"] = request.user
        validated_data["user"] = request.user

        # Admin can set is_editorial
        is_editorial = request.data.get("is_editorial", False)
        if is_editorial and request.user.is_staff:
            validated_data["is_editorial"] = True

        discuss = Discuss.objects.create(**validated_data)
        if tag_ids:
            discuss.tags.set(tag_ids)
        return discuss

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop("tag_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        return instance


class ProblemStatisticsSerializer(serializers.Serializer):
    total_submissions = serializers.IntegerField()
    successful_submissions = serializers.IntegerField()
    success_rate = serializers.FloatField()
    status_breakdown = serializers.DictField()
    language_breakdown = serializers.DictField(required=False)
