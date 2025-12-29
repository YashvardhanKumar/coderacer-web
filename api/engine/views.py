# submissions/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import SubmissionSerializer
from .services import submit_to_judge0
from problem.models import Solution, AnswerStatus
from django.utils.timezone import now
from rest_framework import permissions # You can use this for clarity

class RunCodeView(APIView):
    """
    Receives code execution request and proxies it to Judge0
    """
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SubmissionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # validated = serializer.validated_data
        
        # submission = Solution.objects.create(
        #     problem=validated.get('problem_id'),
        #     user=request.user,
        #     code=validated['source_code'],
        #     language=validated['language_id'],
        #     status=AnswerStatus.PENDING,
        #     created_at=now()
        # )
        
        try:
            result = submit_to_judge0(serializer.validated_data, is_submit=False)
            return Response(result, status=status.HTTP_200_OK)

        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

class SubmitCodeView(APIView):
    """
    Receives code execution request and proxies it to Judge0
    """
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SubmissionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        validated = serializer.validated_data
        
        # submission = Solution.objects.create(
        #     problem=validated.get('problem_id'),
        #     user=request.user,
        #     code=validated['source_code'],
        #     language=validated['language_id'],
        #     status=AnswerStatus.PENDING,
        #     created_at=now()
        # )
        
        try:
            result = submit_to_judge0(serializer.validated_data, is_submit=True)
            return Response(result, status=status.HTTP_200_OK)
            

        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
