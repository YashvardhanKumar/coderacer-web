# submissions/serializers.py
from rest_framework import serializers


class SubmissionSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField(required=False)
    source_code = serializers.CharField()
    stdin = serializers.CharField(required=False, allow_blank=True)
    expected_output = serializers.CharField(required=False, allow_blank=True)

    language_id = serializers.IntegerField()
    number_of_runs = serializers.IntegerField(default=1)

    cpu_time_limit = serializers.FloatField(required=False)
    cpu_extra_time = serializers.FloatField(required=False)
    wall_time_limit = serializers.FloatField(required=False)
    memory_limit = serializers.IntegerField(required=False)
    stack_limit = serializers.IntegerField(required=False)
    max_processes_and_or_threads = serializers.IntegerField(required=False)
    max_file_size = serializers.IntegerField(required=False)

    enable_per_process_and_thread_time_limit = serializers.BooleanField(default=True)
    enable_per_process_and_thread_memory_limit = serializers.BooleanField(default=True)
    enable_network = serializers.BooleanField(default=True)
