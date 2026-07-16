from django.db import models
from django.utils.timezone import now


class RunTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    task_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(
        max_length=50, default="PENDING"
    )  # PENDING, PROCESSING, SUCCESS, ERROR
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "run_task"
        ordering = ["-created_at"]


class TaskLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    task_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=50, default="PENDING"
    )  # PENDING, PROCESSING, SUCCESS, ERROR
    progress = models.IntegerField(default=0)
    logs = models.JSONField(default=list)
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def add_log(self, message):
        self.logs.append({"time": now().strftime("%H:%M:%S"), "message": message})
        self.save()

    class Meta:
        db_table = "task_log"
        ordering = ["-created_at"]
