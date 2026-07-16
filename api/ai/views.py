import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from engine.models import TaskLog
from .services import AIService


class TaskStatusView(APIView):
    """
    Polls the status and logs of a background task.
    """

    def get(self, request, task_id):
        try:
            task_log = TaskLog.objects.get(task_id=task_id)
            return Response(
                {
                    "status": task_log.status,
                    "progress": task_log.progress,
                    "logs": task_log.logs,
                    "result": task_log.result,
                    "updated_at": task_log.updated_at,
                }
            )
        except TaskLog.DoesNotExist:
            return Response(
                {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
            )


from rest_framework.throttling import UserRateThrottle


class AIExplanationThrottle(UserRateThrottle):
    scope = "ai_generation"


class GenerateExplanationView(APIView):
    """
    Generates a solution explanation using AI.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [AIExplanationThrottle]

    def post(self, request):
        problem_description = request.data.get("problem_description", "")
        current_text = request.data.get("current_text", "")
        code = request.data.get("code", "")

        if not problem_description or not code:
            return Response(
                {"error": "problem_description and code are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt = f"""
        You are an expert competitive programmer. Help me write a high-quality solution explanation for a coding problem.

        Problem Description:
        {problem_description}

        My current draft/template for the explanation:
        {current_text}

        My accepted code for this problem:
        {code}

        Task:
        1. Review the code and the problem description.
        2. Come up with a concise, professional title for this solution (e.g., "O(N) Dynamic Programming with Space Optimization").
        3. Fill in the 'Intuition', 'Approach', and 'Complexity' sections of my draft.
        4. Make the explanation clear, professional, and insightful.
        5. Return the result ONLY as a valid JSON object with two keys: "title" and "explanation".
        6. In the "explanation" field, preserve the markdown structure of my draft.
        """

        try:
            raw_content, provider = AIService.generate_with_fallback(prompt)
            clean_content = AIService.clean_json_string(raw_content)
            data = json.loads(clean_content)

            return Response(
                {
                    "title": data.get("title", ""),
                    "explanation": data.get("explanation", ""),
                    "provider": provider,
                }
            )
        except Exception as e:
            return Response(
                {"error": f"AI generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
