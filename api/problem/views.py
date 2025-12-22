from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.db.models import Count, Q
from .models import (
    Problem, Codeblock, Testcase, Solution, 
    Tags, Discuss, AnswerStatus
)
from .serializers import (
    ProblemListSerializer, ProblemDetailSerializer,
    CodeblockSerializer, TestcaseSerializer,
    SolutionListSerializer, SolutionDetailSerializer, SolutionSubmitSerializer,
    TagsSerializer, DiscussListSerializer, DiscussDetailSerializer,
    ProblemStatisticsSerializer
)


class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.prefetch_related('tags', 'codeblocks', 'testcases').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'problem_description']
    ordering_fields = ['created_at', 'id']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProblemListSerializer
        return ProblemDetailSerializer

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for a specific problem"""
        problem = self.get_object()
        solutions = problem.solutions.all()
        
        total = solutions.count()
        successful = solutions.filter(status=AnswerStatus.SUCCESS).count()
        
        status_breakdown = {}
        for choice in AnswerStatus.choices:
            count = solutions.filter(status=choice[0]).count()
            status_breakdown[choice[1]] = count
        
        language_breakdown = {}
        from user.models import CodingLanguage
        for choice in CodingLanguage.choices:
            count = solutions.filter(language=choice[0]).count()
            if count > 0:
                language_breakdown[choice[1]] = count
        
        data = {
            'total_submissions': total,
            'successful_submissions': successful,
            'success_rate': round((successful / total * 100), 2) if total > 0 else 0,
            'status_breakdown': status_breakdown,
            'language_breakdown': language_breakdown
        }
        
        serializer = ProblemStatisticsSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def solutions(self, request, pk=None):
        """Get all solutions for a problem"""
        problem = self.get_object()
        solutions = problem.solutions.select_related('user').all()
        
        # Filter by status if provided
        status_filter = request.query_params.get('status', None)
        if status_filter:
            solutions = solutions.filter(status=status_filter)
        
        serializer = SolutionListSerializer(solutions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def discussions(self, request, pk=None):
        """Get all discussions for a problem"""
        problem = self.get_object()
        discussions = problem.discussions.select_related('author').prefetch_related('tags').all()
        serializer = DiscussListSerializer(discussions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_tag(self, request):
        """Filter problems by tag"""
        tag_name = request.query_params.get('tag', None)
        if not tag_name:
            return Response(
                {'error': 'tag parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        problems = self.queryset.filter(tags__tags__icontains=tag_name)
        serializer = self.get_serializer(problems, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_attempts(self, request):
        """Get problems the user has attempted"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        problem_ids = Solution.objects.filter(user=request.user).values_list('problem_id', flat=True).distinct()
        problems = self.queryset.filter(id__in=problem_ids)
        serializer = self.get_serializer(problems, many=True)
        return Response(serializer.data)


class CodeblockViewSet(viewsets.ModelViewSet):
    queryset = Codeblock.objects.select_related('problem').all()
    serializer_class = CodeblockSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        problem_id = self.request.query_params.get('problem_id', None)
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)
        return queryset


class TestcaseViewSet(viewsets.ModelViewSet):
    queryset = Testcase.objects.select_related('problem').all()
    serializer_class = TestcaseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        problem_id = self.request.query_params.get('problem_id', None)
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)
        return queryset


class SolutionViewSet(viewsets.ModelViewSet):
    queryset = Solution.objects.select_related('user', 'problem').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return SolutionListSerializer
        elif self.action == 'submit':
            return SolutionSubmitSerializer
        return SolutionDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Users can only see their own solutions unless they're staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by problem_id if provided
        problem_id = self.request.query_params.get('problem_id', None)
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

    @action(detail=False, methods=['post'])
    def submit(self, request):
        """Submit a solution for evaluation"""
        serializer = SolutionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get language from request or use user's default
        language = serializer.validated_data.get('language', request.user.default_lang)
        
        # Create solution
        solution = Solution.objects.create(
            user=request.user,
            problem_id=serializer.validated_data['problem_id'],
            code=serializer.validated_data['code'],
            language=language,
            status=AnswerStatus.SUCCESS  # This should be set by your evaluation system
        )
        
        # TODO: Add actual code evaluation logic here
        # For now, just returning success
        
        response_serializer = SolutionDetailSerializer(solution)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def my_solutions(self, request):
        """Get current user's solutions"""
        solutions = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(solutions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get user's solution statistics"""
        solutions = Solution.objects.filter(user=request.user)
        
        total = solutions.count()
        status_counts = {}
        for choice in AnswerStatus.choices:
            count = solutions.filter(status=choice[0]).count()
            status_counts[choice[1]] = count
        
        data = {
            'total_submissions': total,
            'successful_submissions': status_counts.get('Success', 0),
            'status_breakdown': status_counts,
            'unique_problems_attempted': solutions.values('problem').distinct().count()
        }
        
        return Response(data)


class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['tags']

    @action(detail=True, methods=['get'])
    def problems(self, request, pk=None):
        """Get all problems with this tag"""
        tag = self.get_object()
        problems = tag.problems.all()
        serializer = ProblemListSerializer(problems, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most used tags"""
        tags = self.queryset.annotate(
            problem_count=Count('problems')
        ).order_by('-problem_count')[:10]
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)


class DiscussViewSet(viewsets.ModelViewSet):
    queryset = Discuss.objects.select_related('author', 'problem', 'user').prefetch_related('tags').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'body']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return DiscussListSerializer
        return DiscussDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, user=self.request.user)

    def perform_update(self, serializer):
        # Only author can update
        if serializer.instance.author != self.request.user:
            return Response(
                {'error': 'You can only edit your own discussions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()

    def perform_destroy(self, instance):
        # Only author can delete
        if instance.author != self.request.user and not self.request.user.is_staff:
            return Response(
                {'error': 'You can only delete your own discussions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()

    @action(detail=False, methods=['get'])
    def my_discussions(self, request):
        """Get current user's discussions"""
        discussions = self.queryset.filter(author=request.user)
        serializer = self.get_serializer(discussions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_problem(self, request):
        """Get discussions for a specific problem"""
        problem_id = request.query_params.get('problem_id', None)
        if not problem_id:
            return Response(
                {'error': 'problem_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        discussions = self.queryset.filter(problem_id=problem_id)
        serializer = self.get_serializer(discussions, many=True)
        return Response(serializer.data)