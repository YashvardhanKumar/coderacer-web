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

def parse_input(input_str: str) -> str:
    output_lines = []

    lines = [line.strip() for line in input_str.strip().splitlines() if line.strip()]

    for line in lines:
        if '=' not in line:
            continue

        _, value = line.split('=', 1)
        value = value.strip()

        parsed = json.loads(value)

        if isinstance(parsed, list):
            output_lines.append(str(len(parsed)))
            output_lines.append(" ".join(map(str, parsed)))
        else:
            output_lines.append(str(parsed))

    return "\n".join(output_lines)

def parse_output(output_str: str) -> str:
    value = json.loads(output_str.strip())

    if isinstance(value, list):
        return "\n".join(map(str, value))

    return value