from django.db import models
from django.conf import settings
from user.models import CodingLanguage
from ckeditor.fields import RichTextField


class AnswerStatus(models.TextChoices):
    QUEUE = "QUEUE", "In Queue"
    PROCESSING = "PROCESSING", "Processing"
    ACCEPTED = "Accepted", "Accepted"
    WRONG_ANSWER = "Wrong Answer", "Wrong Answer"
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded", "Time Limit Exceeded"
    COMPILATION_ERROR = "Compilation Error", "Compilation Error"
    RUNTIME_ERROR_SIGSEGV = "Runtime Error (SIGSEGV)", "Runtime Error (SIGSEGV)"
    RUNTIME_ERROR_SIGXFSZ = "Runtime Error (SIGXFSZ)", "Runtime Error (SIGXFSZ)"
    RUNTIME_ERROR_SIGFPE = "Runtime Error (SIGFPE)", "Runtime Error (SIGFPE)"
    RUNTIME_ERROR_SIGABRT = "Runtime Error (SIGABRT)", "Runtime Error (SIGABRT)"
    RUNTIME_ERROR_NZEC = "Runtime Error (NZEC)", "Runtime Error (NZEC)"
    RUNTIME_ERROR_OTHER = "Runtime Error (Other)", "Runtime Error (Other)"
    INTERNAL_ERROR = "Internal Error", "Internal Error"
    EXEC_FORMAT_ERROR = "Exec Format Error", "Exec Format Error"
    INVALID_TESTCASE = "Invalid Testcase", "Invalid Testcase"


class Difficulty(models.TextChoices):
    EASY = "EASY", "Easy"
    MEDIUM = "MEDIUM", "Medium"
    HARD = "HARD", "Hard"


class DataType(models.TextChoices):
    STRING = "string"
    INTEGER = "integer"


class VariableType(models.TextChoices):
    VOID = "void"
    INTEGER = "INTEGER", "Integer"
    STRING = "STRING", "String"
    BOOLEAN = "BOOLEAN", "Boolean"
    CHAR = "CHAR", "Character"
    FLOAT = "FLOAT", "Float / Double"
    LONG = "LONG", "Long"
    ARRAY = "ARRAY", "Array"
    CUSTOM = "CUSTOM", "Custom"
    OBJECT = "OBJECT", "Object"


class CustomType(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Name of the custom type (e.g., ListNode)",
    )

    class Meta:
        db_table = "custom_type"
        verbose_name = "Custom Type"
        verbose_name_plural = "Custom Types"

    def __str__(self):
        return self.name


class CustomTypeLanguage(models.Model):
    custom_type = models.ForeignKey(
        CustomType, on_delete=models.CASCADE, related_name="languages"
    )
    language = models.CharField(max_length=50, choices=CodingLanguage.choices)
    class_declaration = models.TextField(
        blank=True,
        default="",
        help_text="Class definition (e.g., struct ListNode { ... })",
    )
    input_output_function = models.TextField(
        blank=True, default="", help_text="Input parsing and custom printing function"
    )

    class Meta:
        db_table = "custom_type_language"
        unique_together = ("custom_type", "language")

    def __str__(self):
        return f"{self.custom_type.name} - {self.get_language_display()}"


class Method(models.Model):
    problem = models.ForeignKey(
        "Problem", on_delete=models.CASCADE, related_name="methods"
    )
    name = models.CharField(
        max_length=255, help_text="Name of the method (e.g., addTwoNumbers)"
    )
    type = models.CharField(max_length=100, help_text="Return type of the method")
    template_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Inner type if this is an array",
    )
    array_dimensions = models.PositiveIntegerField(
        default=1, help_text="Number of dimensions if type is Array"
    )
    is_constructor = models.BooleanField(
        default=False, help_text="Is this the constructor method?"
    )

    class Meta:
        db_table = "method"
        verbose_name = "Method"
        verbose_name_plural = "Methods"

    def __str__(self):
        return f"{self.name} ({self.type})"


class Variable(models.Model):
    problem = models.ForeignKey(
        "Problem", on_delete=models.CASCADE, related_name="variables"
    )
    method = models.ForeignKey(
        Method,
        on_delete=models.CASCADE,
        related_name="parameters",
        null=True,
        blank=True,
        help_text="Method this variable belongs to",
    )
    name = models.CharField(
        max_length=255, help_text="Name of the variable (e.g., nums, target)"
    )
    type = models.CharField(max_length=100, help_text="Type of the variable")
    template_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Inner type if this is an array (e.g., Integer for a 1D Array of Integers)",
    )
    array_dimensions = models.PositiveIntegerField(
        default=1,
        help_text="Number of dimensions if type is Array (e.g., 2 for 2D array)",
    )

    class Meta:
        db_table = "variable"
        verbose_name = "Variable"
        verbose_name_plural = "Variables"

    def __str__(self):
        return f"{self.name} ({self.type})"


class Tags(models.Model):
    id = models.BigAutoField(primary_key=True)
    tags = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "tags"
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.tags


class Problem(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=255, null=False, default="", help_text="Title of the problem"
    )
    problem_description = RichTextField(blank=True, null=False)
    tags = models.ManyToManyField(Tags, through="ProblemTags", related_name="problems")
    difficulty = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.EASY
    )
    validator_type = models.CharField(
        max_length=20,
        choices=[
            ("EXACT", "Exact Match"),
            ("ANY_ORDER", "Any Order (JSON Array)"),
            ("CUSTOM", "Custom Validator"),
        ],
        default="EXACT",
        help_text="How to validate the solution output",
    )
    custom_validator = models.TextField(
        blank=True,
        default="",
        help_text="Custom Python validator code. Must define 'validate(actual: str, expected: str, tc_input: str) -> bool'",
    )
    generator_code = models.TextField(
        blank=True,
        default="",
        help_text="Python test case generator script for programmatic generation",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "problem"
        verbose_name = "Problem"
        verbose_name_plural = "Problems"
        ordering = ["id"]

    def __str__(self):
        return self.name


class Codeblock(models.Model):
    id = models.BigAutoField(primary_key=True)
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="codeblocks"
    )
    block = models.TextField(blank=True, null=False, default="")
    runner_code = models.TextField(blank=True, null=False, default="")
    language = models.CharField(
        max_length=50,
        choices=CodingLanguage.choices,
        verbose_name="Programming Language",
    )

    class Meta:
        db_table = "codeblock"
        verbose_name = "Code Block"
        verbose_name_plural = "Code Blocks"
        unique_together = ("problem", "language")

    def get_language_display(self):
        return dict(CodingLanguage.choices).get(self.language, self.language)

    def __str__(self):
        return (
            f"Codeblock for Problem #{self.problem.id} ({self.get_language_display()})"
        )


class Testcase(models.Model):
    id = models.BigAutoField(primary_key=True)
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="testcases"
    )
    input = models.TextField(blank=True, null=False)
    output = models.TextField(blank=True, null=False)
    display_testcase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "testcase"
        verbose_name = "Test Case"
        verbose_name_plural = "Test Cases"
        ordering = ["created_at"]

    def __str__(self):
        return f"Testcase #{self.id} for Problem #{self.problem.id}"


class Solution(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="solutions"
    )
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="solutions"
    )
    code = models.TextField()
    language = models.CharField(
        max_length=20,
        default="PYTHON",
        verbose_name="Programming Language",
    )
    status = models.CharField(
        max_length=30, choices=AnswerStatus.choices, blank=True, null=True
    )
    testcase_results = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "solution"
        verbose_name = "Solution"
        verbose_name_plural = "Solutions"
        ordering = ["-created_at"]

    def get_language_display(self):
        return dict(CodingLanguage.choices).get(self.language, self.language)

    def __str__(self):
        return f"Solution by {self.user.username} for Problem #{self.problem.id} ({self.get_language_display()})"


class ProblemTags(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tags, on_delete=models.CASCADE)

    class Meta:
        db_table = "problem_tags"
        unique_together = ("problem", "tag")
        verbose_name = "Problem Tag"
        verbose_name_plural = "Problem Tags"

    def __str__(self):
        return f"{self.problem} - {self.tag}"


class Discuss(models.Model):
    id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discussions_authored",
        db_column="author_id",
    )
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="discussions"
    )
    title = models.CharField(max_length=255)
    body = models.TextField(
        blank=True, null=False, help_text="Content of the post (Markdown supported)"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discussions",
        help_text="User associated with this discussion",
    )
    tags = models.ManyToManyField(
        Tags, through="DiscussTags", related_name="discussions"
    )
    tags = models.ManyToManyField(
        Tags, through="DiscussTags", related_name="discussions"
    )
    views = models.PositiveIntegerField(default=0)
    is_editorial = models.BooleanField(default=False)
    upvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="upvoted_discussions", blank=True
    )
    downvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="downvoted_discussions", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "discuss"
        verbose_name = "Discussion"
        verbose_name_plural = "Discussions"
        ordering = ["-created_at"]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.is_editorial:
            # Check for existing editorial for this problem
            existing_editorial = (
                Discuss.objects.filter(problem=self.problem, is_editorial=True)
                .exclude(id=self.id)
                .first()
            )
            if existing_editorial:
                raise ValidationError(
                    f"{existing_editorial.id} discussion is marked as editorial, "
                    f"make is_editorial false to make this editorial"
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class DiscussTags(models.Model):
    discuss = models.ForeignKey(Discuss, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tags, on_delete=models.CASCADE)

    class Meta:
        db_table = "discuss_tags"
        unique_together = ("discuss", "tag")
        verbose_name = "Discussion Tag"
        verbose_name_plural = "Discussion Tags"

    def __str__(self):
        return f"{self.discuss} - {self.tag}"


class Comment(models.Model):
    id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments_authored",
    )
    discuss = models.ForeignKey(
        Discuss, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField()
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    upvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="upvoted_comments", blank=True
    )
    downvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="downvoted_comments", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comment"
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.discuss.title}"
