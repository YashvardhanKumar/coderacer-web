# engine/services.py
import requests
import base64
import json
import re
from .constants import JUDGE0_URL, DEFAULT_LIMITS
from problem.models import Testcase, AnswerStatus

# Essential fields supported by Judge0 CE
VALID_JUDGE0_FIELDS = {
    "source_code",
    "language_id",
    "stdin",
    "expected_output",
    "cpu_time_limit",
    "cpu_extra_time",
    "wall_time_limit",
    "memory_limit",
    "stack_limit",
    "max_processes_and_or_threads",
    "max_file_size",
    "compiler_options",
}


def encode_base64(text: str) -> str:
    if not text:
        return ""
    try:
        return base64.b64encode(text.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""


def decode_base64(text: str) -> str:
    if not text:
        return ""
    try:
        return base64.b64decode(text).decode("utf-8")
    except Exception:
        return text


def flatten_json_array(arr):
    if not isinstance(arr, list):
        return [arr]
    res = [len(arr)]
    for item in arr:
        res.extend(flatten_json_array(item))
    return res


def _unquote_value(val):
    """
    Strip surrounding double quotes from a value.
    """
    if len(val) >= 2 and val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    return val


def _flatten_for_stdin(item):
    """
    Recursively flatten a parsed JSON value for stdin.
    - Strings are unquoted (returned without surrounding double quotes).
    - null (None) becomes an empty string (true null value).
    - Lists are prefixed with their length then each element is flattened.
    """
    if item is None:
        return ["null"]
    if isinstance(item, str):
        return [item]  # already unquoted by json.loads
    if isinstance(item, (int, float, bool)):
        return [str(item).lower() if isinstance(item, bool) else str(item)]
    if isinstance(item, list):
        res = [str(len(item))]
        for sub in item:
            res.extend(_flatten_for_stdin(sub))
        return res
    return [str(item)]


def format_stdin(raw_input: str, language_id: int = None) -> str:
    if not raw_input:
        return ""
    lines = raw_input.strip().splitlines()
    formatted_lines = []
    for line in lines:
        if "=" in line:
            value = line.split("=", 1)[1].strip()
        else:
            value = line.strip()

        # Bare `null` (without quotes) → treat as null input (empty value)
        if value == "null":
            formatted_lines.append("null")
            continue

        # JSON array – flatten with unquoted strings and null handling
        if (
            language_id in [50, 54, 62]
            and value.startswith("[")
            and value.endswith("]")
        ):
            try:
                arr = json.loads(value)
                if isinstance(arr, list):
                    flat = _flatten_for_stdin(arr)
                    formatted_lines.append("\n".join(flat))
                    continue
            except Exception:
                pass

        # Double-quoted string like "pwwkew" → strip the quotes
        value = _unquote_value(value)

        formatted_lines.append(value)
    return "\n".join(formatted_lines)


def format_batch_stdin(testcases, language_id=None):
    """
    Concatenate all test case inputs with T (count) header.
    Format: T\n<tc1_input>\n<tc2_input>\n...
    """
    parts = [str(len(testcases))]
    for tc in testcases:
        tc_input = tc.input if hasattr(tc, "input") else tc.get("input", "")
        formatted = format_stdin(tc_input, language_id)
        parts.append(formatted)
    return "\n".join(parts)


def parse_batch_stdout(stdout, num_testcases):
    """
    Parse batch stdout split by TC_SEPARATOR.
    Returns a list of output strings, one per test case.
    """
    from .constants import TC_SEPARATOR

    if not stdout:
        return [""] * num_testcases
    blocks = stdout.split(TC_SEPARATOR)
    results = []
    for i in range(num_testcases):
        if i < len(blocks):
            results.append(blocks[i].strip("\n\r"))
        else:
            results.append("")
    return results


def validate_case_output(problem, actual: str, expected: str, tc_input: str) -> bool:
    validator_type = getattr(problem, "validator_type", "EXACT")
    if validator_type == "ANY_ORDER":
        try:
            import json

            def sort_nested(obj):
                if isinstance(obj, list):
                    sorted_list = [sort_nested(item) for item in obj]
                    try:
                        return sorted(sorted_list)
                    except TypeError:
                        return sorted(
                            sorted_list, key=lambda x: json.dumps(x, sort_keys=True)
                        )
                elif isinstance(obj, dict):
                    return {k: sort_nested(v) for k, v in sorted(obj.items())}
                return obj

            actual_json = json.loads(actual)
            expected_json = json.loads(expected)
            return sort_nested(actual_json) == sort_nested(expected_json)
        except Exception:
            # Fallback to line-by-line any-order comparison
            actual_lines = sorted(actual.strip().splitlines())
            expected_lines = sorted(expected.strip().splitlines())
            return actual_lines == expected_lines

    elif validator_type == "CUSTOM":
        custom_validator = getattr(problem, "custom_validator", "")
        if not custom_validator:
            return actual.strip() == expected.strip()
        try:
            loc = {}
            exec(custom_validator, {}, loc)
            if "validate" in loc:
                return bool(loc["validate"](actual, expected, tc_input))
            return actual.strip() == expected.strip()
        except Exception as e:
            print(f"Error in custom validator for problem {problem.id}: {e}")
            return False

    return actual.strip() == expected.strip()


def _parse_token(t, template_type):
    if t == "null":
        return None
    if template_type in ("BOOLEAN", "boolean"):
        return t.lower() == "true"
    if template_type in ("INTEGER", "Integer", "long", "LONG"):
        try:
            return int(t)
        except ValueError:
            return t
    if template_type in ("FLOAT", "double", "DOUBLE"):
        try:
            return float(t)
        except ValueError:
            return t
    return t


def _split_by_blank_lines(lines, sep):
    groups = []
    cur = []
    blanks = 0
    for line in lines:
        if not line:
            blanks += 1
            if blanks >= sep and cur:
                groups.append(cur)
                cur = []
                blanks = 0
        else:
            if blanks > 0:
                for _ in range(blanks):
                    cur.append("")
                blanks = 0
            cur.append(line)
    if cur:
        groups.append(cur)
    return groups


def _parse_nd_output(lines, template_type, dimensions):
    if template_type in ("STRING", "string"):
        lines = [l for l in lines] if lines else []
    else:
        lines = [l.strip() for l in lines] if lines else []
    if dimensions == 1:
        if not lines:
            return []
        if template_type in ("STRING", "string"):
            return [None if l == "null" else l for l in lines]
        line = " ".join(lines).strip()
        if not line:
            return []
        return [_parse_token(t, template_type) for t in line.split()]

    sep = dimensions - 1
    groups = _split_by_blank_lines(lines, sep)
    return [_parse_nd_output(g, template_type, dimensions - 1) for g in groups]

    result = []
    for og in outer_groups:
        merged = []
        for g_content, _ in og:
            if merged:
                merged.append("")
            merged.extend(g_content)
        result.append(_parse_nd_output(merged, template_type, dimensions - 1))
    return result


def reconstruct_json_output(actual: str, problem) -> str:
    if not problem:
        return actual
    if not actual or actual.strip() == "null":
        return "null"

    # Check if this is is_multi
    methods = list(problem.methods.all())
    is_multi = len(methods) > 1 or any(m.is_constructor for m in methods)
    if is_multi:
        return actual

    method = problem.methods.filter(is_constructor=False).first()
    if not method:
        return actual

    ret_type = method.type
    template_type = method.template_type
    dimensions = method.array_dimensions

    if ret_type in ["void", "VOID"]:
        return "null"

    actual_lines = actual.splitlines()
    if not actual_lines:
        return "null"

    if ret_type == "Array" or ret_type == "ARRAY":
        result = _parse_nd_output(actual_lines, template_type, dimensions)
        return json.dumps(result, separators=(",", ":"))
    else:
        # Scalar type
        val = actual.strip()
        if val == "null":
            return "null"
        if ret_type == "BOOLEAN" or ret_type == "boolean":
            return "true" if val.lower() == "true" else "false"
        if ret_type in ["INTEGER", "Integer", "long", "LONG"]:
            try:
                return str(int(val))
            except ValueError:
                return val
        if ret_type in ["FLOAT", "double", "DOUBLE"]:
            try:
                return str(float(val))
            except ValueError:
                return val
        if ret_type == "STRING" or ret_type == "string":
            return val

    return actual


def run_batch_submission(base_payload, testcases, language_id=None):
    """
    Run ALL test cases in a single Judge0 submission.
    Returns a list of per-test-case result dicts.
    """
    from .constants import TC_SEPARATOR, get_scaled_limits

    # Get problem object to check validator settings
    problem = None
    if testcases:
        from problem.models import Problem

        first_tc = testcases[0]
        problem_id = None
        if hasattr(first_tc, "problem_id") and first_tc.problem_id:
            problem_id = first_tc.problem_id
        elif isinstance(first_tc, dict) and first_tc.get("problem_id"):
            problem_id = first_tc.get("problem_id")
        elif hasattr(first_tc, "problem") and first_tc.problem:
            problem_id = first_tc.problem.id

        if problem_id:
            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                pass

    # Build batch stdin
    batch_stdin = format_batch_stdin(testcases, language_id)

    # Scale resource limits
    scaled_limits = get_scaled_limits(len(testcases))
    payload = {**scaled_limits, **base_payload}

    # Set stdin
    payload["stdin"] = encode_base64(batch_stdin)

    # Remove expected_output (we compare manually)
    payload.pop("expected_output", None)

    try:
        response = requests.post(
            url=f"{JUDGE0_URL}/submissions?base64_encoded=true&wait=true",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120,  # Higher timeout for batch
        )
        res = response.json()

        # Decode base64 fields
        for field in ["stdout", "stderr", "compile_output", "message"]:
            val = res.get(field)
            if val is not None:
                res[field] = decode_base64(val)

        status_obj = res.get("status", {})
        status_id = status_obj.get("id")

        # Handle compilation error or runtime error that affects ALL test cases
        if status_id == 6:  # Compilation Error
            return [
                {
                    "status": status_obj,
                    "stdout": "",
                    "stderr": res.get("stderr") or "",
                    "compile_output": res.get("compile_output") or "",
                    "message": res.get("message") or "",
                    "time": res.get("time"),
                    "memory": res.get("memory"),
                    "user_time_ms": 0,
                    "is_accepted": False,
                    "is_hidden": not (
                        hasattr(tc, "display_testcase") and tc.display_testcase
                        if hasattr(tc, "display_testcase")
                        else True
                    ),
                    "case_id": getattr(tc, "id", i),
                    "input": (
                        (tc.input if hasattr(tc, "input") else tc.get("input", ""))
                        if (
                            hasattr(tc, "display_testcase") and tc.display_testcase
                            if hasattr(tc, "display_testcase")
                            else True
                        )
                        else "Hidden"
                    ),
                    "expected_output": (
                        (tc.output if hasattr(tc, "output") else tc.get("output", ""))
                        if (
                            hasattr(tc, "display_testcase") and tc.display_testcase
                            if hasattr(tc, "display_testcase")
                            else True
                        )
                        else "Hidden"
                    ),
                    "index": i,
                }
                for i, tc in enumerate(testcases)
            ]

        # Parse stdout into per-test-case outputs
        stdout = res.get("stdout") or ""
        stderr = res.get("stderr") or ""
        actual_outputs = parse_batch_stdout(stdout, len(testcases))

        # Build per-test-case results
        results = []
        for i, tc in enumerate(testcases):
            tc_input = tc.input if hasattr(tc, "input") else tc.get("input", "")
            tc_output = tc.output if hasattr(tc, "output") else tc.get("output", "")
            is_display = (
                tc.display_testcase
                if hasattr(tc, "display_testcase")
                else tc.get("display_testcase", True)
            )
            tc_id = getattr(tc, "id", i)

            block_text = actual_outputs[i]

            # Extract user code execution time (nanoseconds, converted to ms)
            user_time_ms = 0.0
            time_marker_match = re.search(r"_TIME_(\d+)_", block_text)
            if time_marker_match:
                user_time_ms = int(time_marker_match.group(1)) / 1_000_000
                block_text = re.sub(r"_TIME_\d+_[\r\n]*", "", block_text)

            # Extract user prints and clean output
            pattern = r"_USER_PRINT_START_[\r\n]*(.*?)[\r\n]*_USER_PRINT_END_[\r\n]*"
            matches = re.findall(pattern, block_text, re.DOTALL)
            user_prints = "\n".join(m.strip() for m in matches if m.strip())
            actual = re.sub(pattern, "", block_text, flags=re.DOTALL).strip("\n\r")

            if not matches and "_USER_PRINT_START_" in block_text:
                parts = block_text.split("_USER_PRINT_START_", 1)
                user_prints = parts[1].replace("_USER_PRINT_END_", "").strip()
                actual = parts[0].strip("\n\r")

            actual = (
                actual.replace("_USER_PRINT_START_", "")
                .replace("_USER_PRINT_END_", "")
                .strip("\n\r")
            )

            expected = tc_output.strip()

            is_accepted = False
            # Check if this test case got output (runtime error might cut execution short)
            is_crash = (
                not actual
                or "segmentation fault" in actual.lower()
                or "sigsegv" in actual.lower()
                or "core dumped" in actual.lower()
                or "run.sh:" in actual
            )
            if status_id not in (None, 3) and status_id > 4 and is_crash:
                # Runtime error occurred before this test case completed
                is_accepted = False
                case_status = status_obj
                actual = ""
            else:
                actual = reconstruct_json_output(actual, problem)
                is_accepted = validate_case_output(problem, actual, expected, tc_input)
                if is_accepted:
                    case_status = {"id": 3, "description": "Accepted"}
                else:
                    is_accepted = False
                    case_status = {"id": 4, "description": "Wrong Answer"}

            judge0_compile_output = res.get("compile_output") or ""
            compile_out = judge0_compile_output
            if user_prints:
                if compile_out:
                    compile_out += "\n" + user_prints
                else:
                    compile_out = user_prints

            results.append(
                {
                    "status": case_status,
                    "stdout": actual if is_display else "",
                    "stderr": stderr if not is_accepted else "",
                    "compile_output": compile_out if is_display else "",
                    "message": res.get("message") or "",
                    "time": res.get("time"),
                    "memory": res.get("memory"),
                    "user_time_ms": round(user_time_ms, 3),
                    "is_accepted": is_accepted,
                    "is_hidden": not is_display,
                    "case_id": tc_id,
                    "input": tc_input if is_display else "Hidden",
                    "expected_output": expected if is_display else "Hidden",
                    "index": i,
                }
            )

        # If runtime error (status 5-14) and some test cases completed,
        # mark completed ones appropriately and rest as runtime error
        if status_id and status_id > 4:
            for i, r in enumerate(results):
                if not actual_outputs[i]:  # No output = didn't complete
                    r["status"] = status_obj
                    r["is_accepted"] = False

        return results

    except Exception as e:
        return [
            {
                "status": {"id": 13, "description": "Internal Error"},
                "message": str(e),
                "is_accepted": False,
                "user_time_ms": 0,
                "is_hidden": not (
                    hasattr(tc, "display_testcase") and tc.display_testcase
                    if hasattr(tc, "display_testcase")
                    else True
                ),
                "index": i,
            }
            for i, tc in enumerate(testcases)
        ]


def submit_to_judge0(payload: dict, is_submit: bool) -> dict:
    """
    Updated wrapper that uses batch single-submission approach.
    Maintains backward compatibility with the existing API.
    """
    merged_payload = {**DEFAULT_LIMITS, **payload}
    pid = merged_payload.get("problem_id")
    language_id = merged_payload.get("language_id")

    if is_submit:
        testcases = list(Testcase.objects.filter(problem_id=pid).order_by("id"))
    else:
        testcases = list(
            Testcase.objects.filter(problem_id=pid, display_testcase=True).order_by(
                "id"
            )
        )

    base_payload = {
        k: v
        for k, v in merged_payload.items()
        if k in VALID_JUDGE0_FIELDS and k not in ["stdin", "expected_output"]
    }
    if language_id == 74:
        base_payload["compiler_options"] = (
            "--target es2020 --lib es2020,dom --module commonjs"
        )

    if "source_code" in base_payload:
        base_payload["source_code"] = encode_base64(base_payload["source_code"])

    results = run_batch_submission(base_payload, testcases, language_id)
    results.sort(key=lambda x: x.get("index", 0))

    if is_submit:
        total_status = {"id": 3, "description": "Accepted"}
        for r in results:
            if not r.get("is_accepted"):
                total_status = r.get("status")
                break
        return {"status": total_status, "testcase_results": results}
    return results
