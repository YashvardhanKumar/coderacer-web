# submissions/constants.py
import json

# JUDGE0_URL = "http://10.82.221.23:2358/submissions?wait=true"
JUDGE0_URL = "https://ce.judge0.com"

DEFAULT_LIMITS = {
    "cpu_time_limit": 5,
    "cpu_extra_time": 1,
    "wall_time_limit": 10,
    "memory_limit": 128000,
    "stack_limit": 64000,
    "max_processes_and_or_threads": 60,
    "max_file_size": 1024,
}

TC_SEPARATOR = "___CODERACER_TC_SEP___"


# Max limits enforced by Judge0 CE public API
JUDGE0_MAX_CPU_TIME_LIMIT = 20
JUDGE0_MAX_WALL_TIME_LIMIT = 30
JUDGE0_MAX_CPU_EXTRA_TIME = 5


def get_scaled_limits(num_testcases):
    """Scale resource limits proportionally to number of test cases."""
    limits = DEFAULT_LIMITS.copy()
    scale = min(num_testcases, 20)  # Cap at 20x
    limits["cpu_time_limit"] = min(
        limits["cpu_time_limit"] * scale, JUDGE0_MAX_CPU_TIME_LIMIT
    )
    limits["cpu_extra_time"] = min(
        limits["cpu_extra_time"] * scale, JUDGE0_MAX_CPU_EXTRA_TIME
    )
    limits["wall_time_limit"] = min(
        limits["wall_time_limit"] * scale, JUDGE0_MAX_WALL_TIME_LIMIT
    )
    return limits
