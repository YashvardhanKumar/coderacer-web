from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SubmissionSerializer
from .models import RunTask
from .tasks import run_code_task
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
import json
import requests
from .constants import JUDGE0_URL, DEFAULT_LIMITS
from .services import encode_base64, VALID_JUDGE0_FIELDS, run_batch_submission
from problem.models import Testcase, Solution, AnswerStatus, Problem
from rest_framework.authentication import TokenAuthentication


class SubmitStreamView(APIView):
    """
    Evaluates testcases in parallel and streams results back to the client.
    Supports both 'Run' (visible only) and 'Submit' (all cases).
    Automatically wraps raw code with boilerplate from the database.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated = serializer.validated_data
        problem_id = validated.get("problem_id")
        is_submit = request.query_params.get("mode") == "submit"

        if is_submit and not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required for submission"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        problem = get_object_or_404(Problem, id=problem_id)
        contest_id = request.query_params.get("contest_id") or request.data.get(
            "contest_id"
        )
        contest = None
        if contest_id:
            from contest.models import Contest

            contest = get_object_or_404(Contest, id=contest_id)

        if is_submit:
            testcases = Testcase.objects.filter(problem_id=problem_id).order_by("id")
        else:
            custom_testcases_data = request.data.get("custom_testcases")
            if custom_testcases_data:

                class MockTestcase:
                    def __init__(self, id, input, output="", display_testcase=True):
                        self.id = id
                        self.problem_id = problem_id
                        self.input = input
                        self.output = output
                        self.display_testcase = display_testcase

                testcases = [
                    MockTestcase(
                        id=tc.get("id", i),
                        input=tc.get("input", ""),
                        output=tc.get("output", ""),
                        display_testcase=tc.get("display_testcase", True),
                    )
                    for i, tc in enumerate(custom_testcases_data)
                ]
            else:
                testcases = Testcase.objects.filter(
                    problem_id=problem_id, display_testcase=True
                ).order_by("id")

        # Logic for code wrapping
        raw_source_code = validated.get("source_code")
        lang_str = validated.get("language")

        # Pre-wrap code with boilerplate from Codeblock model
        if lang_str and problem.codeblocks.filter(language=lang_str).exists():
            from problem.utils import assemble_full_code

            full_source_code = assemble_full_code(problem, lang_str, raw_source_code)
        else:
            # Fallback if no matching codeblock found
            full_source_code = raw_source_code

        # Prepare base payload for Judge0
        merged_payload = {**DEFAULT_LIMITS, **validated}
        base_judge0_payload = {
            k: v
            for k, v in merged_payload.items()
            if k in VALID_JUDGE0_FIELDS
            and k not in ["stdin", "expected_output"]
            and v is not None
        }

        # Final encoded code for execution
        base_judge0_payload["source_code"] = encode_base64(full_source_code)

        if validated.get("language_id") == 74 or lang_str == "TYPESCRIPT":
            base_judge0_payload["compiler_options"] = (
                "--target es2020 --lib es2020,dom --module commonjs"
            )

        def generator():
            from problem.views import JUDGE0_STATUS_MAP

            # Run all test cases in a single submission
            results = run_batch_submission(
                base_judge0_payload, list(testcases), validated.get("language_id")
            )
            results.sort(key=lambda x: x.get("index", 0))

            compilation_error = None
            total_passed = True

            for case_res in results:
                if case_res.get("status", {}).get("id") == 6:
                    compilation_error = case_res.get("compile_output")
                if not case_res.get("is_accepted"):
                    total_passed = False

                if contest and not is_submit:
                    # In contest mode during run, do not reveal pass/fail verdict or expected output
                    masked_case = dict(case_res)
                    masked_case.pop("is_accepted", None)
                    masked_case.pop("expected_output", None)
                    if masked_case.get("status", {}).get("id") in [3, 4]:
                        masked_case["status"] = {"id": 3, "description": "Finished"}
                    yield json.dumps(
                        {"status": "case_result", "data": masked_case}
                    ) + "\n"
                else:
                    yield json.dumps({"status": "case_result", "data": case_res}) + "\n"

            sol_id = 0
            sol_status = (
                "Accepted" if total_passed and not compilation_error else "Error"
            )

            if is_submit:
                final_status = AnswerStatus.ACCEPTED
                if compilation_error:
                    final_status = AnswerStatus.COMPILATION_ERROR
                elif not total_passed:
                    for r in results:
                        if not r.get("is_accepted"):
                            final_status = JUDGE0_STATUS_MAP.get(
                                r.get("status", {}).get("id"), AnswerStatus.WRONG_ANSWER
                            )
                            break

                sol = Solution.objects.create(
                    user=request.user,
                    problem=problem,
                    code=raw_source_code,  # Save the original user code
                    language=lang_str or "PYTHON",
                    status=final_status,
                    testcase_results=results,
                )
                sol_id = sol.id
                sol_status = final_status

                if contest:
                    from contest.services import record_contest_submission

                    record_contest_submission(
                        contest, problem, request.user, final_status, results
                    )

            yield json.dumps(
                {
                    "status": "complete",
                    "total_status": sol_status,
                    "solution_id": sol_id,
                    "compile_output": compilation_error,
                    "results": results,
                }
            ) + "\n"

        response = StreamingHttpResponse(generator(), content_type="application/json")
        response["X-Accel-Buffering"] = "no"
        return response


class RunCodeView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from .services import submit_to_judge0

        try:
            result = submit_to_judge0(serializer.validated_data, is_submit=False)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class RunStatusView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, task_id):
        try:
            run_task = RunTask.objects.get(task_id=task_id)
            return Response(
                {
                    "status": run_task.status,
                    "result": run_task.result,
                    "error": run_task.error,
                }
            )
        except RunTask.DoesNotExist:
            return Response(
                {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
            )


class SubmitCodeView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from .services import submit_to_judge0

        try:
            result = submit_to_judge0(serializer.validated_data, is_submit=True)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
