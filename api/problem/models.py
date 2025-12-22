from django.db import models
from django.conf import settings
from user.models import CodingLanguage  # Import from user app
from ckeditor.fields import RichTextField


class AnswerStatus(models.TextChoices):
    INVALID_TESTCASE = 'INVALID_TESTCASE', 'Invalid Testcase'
    RUNTIME_ERROR = 'RUNTIME_ERROR', 'Runtime Error'
    COMPILE_ERROR = 'COMPILE_ERROR', 'Compile Error'
    WRONG_ANSWER = 'WRONG_ANSWER', 'Wrong Answer'
    SUCCESS = 'SUCCESS', 'Success'
    TIME_LIMIT_EXCEEDED = 'TIME_LIMIT_EXCEEDED', 'Time Limit Exceeded'
    MEMORY_LIMIT_EXCEEDED = 'MEMORY_LIMIT_EXCEEDED', 'Memory Limit Exceeded'

class Difficulty(models.TextChoices):
    EASY = 'EASY', 'Easy'
    MEDIUM = 'MEDIUM', 'Medium'
    HARD = 'HARD', 'Hard'

class Tags(models.Model):
    id = models.BigAutoField(primary_key=True)
    tags = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'tags'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.tags


class Problem(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False, default='', help_text='Title of the problem')
    problem_description = RichTextField(blank=True, null=False)
    tags = models.ManyToManyField(Tags, through='ProblemTags', related_name='problems')
    created_at = models.DateTimeField(auto_now_add=True)
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.EASY,
        verbose_name="Difficulty Level"
    )

    class Meta:
        db_table = 'problem'
        verbose_name = 'Problem'
        verbose_name_plural = 'Problems'
        ordering = ['-created_at']

    def __str__(self):
        return f"Problem #{self.id}"


class Codeblock(models.Model):
    id = models.BigAutoField(primary_key=True)
    problem = models.ForeignKey(
        Problem, 
        on_delete=models.CASCADE, 
        related_name='codeblocks'
    )
    block = models.TextField()
    language = models.CharField(
        max_length=20,
        choices=CodingLanguage.choices,
        default=CodingLanguage.PYTHON,
        verbose_name="Programming Language"
    )

    class Meta:
        db_table = 'codeblock'
        verbose_name = 'Code Block'
        verbose_name_plural = 'Code Blocks'

    def __str__(self):
        return f"Codeblock for Problem #{self.problem.id} ({self.get_language_display()})"


class Testcase(models.Model):
    id = models.BigAutoField(primary_key=True)
    problem = models.ForeignKey(
        Problem, 
        on_delete=models.CASCADE, 
        related_name='testcases'
    )
    input = models.TextField(blank=True, null=False)
    output = models.TextField(blank=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'testcase'
        verbose_name = 'Test Case'
        verbose_name_plural = 'Test Cases'
        ordering = ['created_at']

    def __str__(self):
        return f"Testcase #{self.id} for Problem #{self.problem.id}"


class Solution(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='solutions'
    )
    problem = models.ForeignKey(
        Problem, 
        on_delete=models.CASCADE, 
        related_name='solutions'
    )
    code = models.TextField()
    language = models.CharField(
        max_length=20,
        choices=CodingLanguage.choices,
        default=CodingLanguage.PYTHON,
        verbose_name="Programming Language"
    )
    status = models.CharField(
        max_length=30,
        choices=AnswerStatus.choices,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'solution'
        verbose_name = 'Solution'
        verbose_name_plural = 'Solutions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Solution by {self.user.username} for Problem #{self.problem.id} ({self.get_language_display()})"


class ProblemTags(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tags, on_delete=models.CASCADE)

    class Meta:
        db_table = 'problem_tags'
        unique_together = ('problem', 'tag')
        verbose_name = 'Problem Tag'
        verbose_name_plural = 'Problem Tags'

    def __str__(self):
        return f"{self.problem} - {self.tag}"


class Discuss(models.Model):
    id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='discussions_authored',
        db_column='author_id'
    )
    problem = models.ForeignKey(
        Problem, 
        on_delete=models.CASCADE, 
        related_name='discussions'
    )
    title = models.CharField(max_length=255)
    body = RichTextField(blank=True, null=False, help_text='Content of the post')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='discussions',
        help_text='User associated with this discussion'
    )
    tags = models.ManyToManyField(Tags, through='DiscussTags', related_name='discussions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'discuss'
        verbose_name = 'Discussion'
        verbose_name_plural = 'Discussions'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class DiscussTags(models.Model):
    discuss = models.ForeignKey(Discuss, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tags, on_delete=models.CASCADE)

    class Meta:
        db_table = 'discuss_tags'
        unique_together = ('discuss', 'tag')
        verbose_name = 'Discussion Tag'
        verbose_name_plural = 'Discussion Tags'

    def __str__(self):
        return f"{self.discuss} - {self.tag}"