from django.db import models
from django.contrib.auth.models import AbstractUser


class CodingLanguage(models.TextChoices):
    CPP = 'CPP', 'C++'
    JAVA = 'JAVA', 'Java'
    PYTHON = 'PYTHON', 'Python'
    JAVASCRIPT = 'JAVASCRIPT', 'JavaScript'
    TYPESCRIPT = 'TYPESCRIPT', 'TypeScript'


class User(AbstractUser):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    # username and email are inherited from AbstractUser
    hash = models.CharField(max_length=255, blank=True, null=True, help_text="Additional hash field")
    default_lang = models.CharField(
        max_length=20,
        choices=CodingLanguage.choices,
        default=CodingLanguage.PYTHON,
        verbose_name="Default Coding Language"
    )

    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username