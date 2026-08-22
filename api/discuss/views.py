from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import F, Count, Q
from django.shortcuts import get_object_or_404

from .models import DiscussPost, DiscussComment, DiscussCategory
from .serializers import (
    DiscussPostListSerializer,
    DiscussPostDetailSerializer,
    DiscussPostCreateSerializer,
    DiscussCommentSerializer,
)


class DiscussPostViewSet(viewsets.ModelViewSet):
    queryset = (
        DiscussPost.objects.select_related("author")
        .prefetch_related("upvotes", "downvotes", "comments")
        .all()
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "content"]

    def get_serializer_class(self):
        if self.action == "list":
            return DiscussPostListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return DiscussPostCreateSerializer
        return DiscussPostDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Category filter
        category = self.request.query_params.get("category")
        if category and category.upper() != "ALL":
            qs = qs.filter(category=category.upper())

        # Tag filter
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__icontains=tag)

        # Ordering
        order_by = self.request.query_params.get("order", "hot").lower()
        if order_by == "newest":
            qs = qs.order_by("-pinned", "-created_at")
        elif order_by == "most_voted":
            qs = qs.annotate(
                score=Count("upvotes", distinct=True)
                - Count("downvotes", distinct=True)
            ).order_by("-pinned", "-score", "-created_at")
        elif order_by == "most_viewed":
            qs = qs.order_by("-pinned", "-views", "-created_at")
        else:  # 'hot' default
            qs = qs.annotate(
                hot_score=Count("upvotes", distinct=True) * 2
                + Count("comments", distinct=True) * 3
                + F("views")
            ).order_by("-pinned", "-hot_score", "-created_at")

        return qs

    def retrieve(self, request, *args, **kwargs):
        from problem.utils import should_count_view

        instance = self.get_object()
        user_id = (
            f"user_{request.user.id}"
            if request.user.is_authenticated
            else f"anon_{request.session.session_key or request.META.get('REMOTE_ADDR', 'ip')}"
        )
        if should_count_view(f"discuss_post_{instance.pk}", user_id):
            DiscussPost.objects.filter(pk=instance.pk).update(views=F("views") + 1)
            instance.refresh_from_db(fields=["views"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if (
            serializer.instance.author != self.request.user
            and not self.request.user.is_staff
        ):
            raise PermissionDenied("You can only edit your own posts.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("You can only delete your own posts.")
        instance.delete()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        """Vote on a post: vote_type in ['up', 'down', 'clear']"""
        post = self.get_object()
        user = request.user
        vote_type = request.data.get("vote_type", "up").lower()

        if vote_type == "up":
            if post.upvotes.filter(id=user.id).exists():
                post.upvotes.remove(user)  # Toggle off
                user_vote = 0
            else:
                post.upvotes.add(user)
                post.downvotes.remove(user)
                user_vote = 1
        elif vote_type == "down":
            if post.downvotes.filter(id=user.id).exists():
                post.downvotes.remove(user)  # Toggle off
                user_vote = 0
            else:
                post.downvotes.add(user)
                post.upvotes.remove(user)
                user_vote = -1
        else:  # clear
            post.upvotes.remove(user)
            post.downvotes.remove(user)
            user_vote = 0

        return Response(
            {
                "post_id": post.id,
                "vote_count": post.vote_count,
                "upvotes_count": post.upvotes.count(),
                "downvotes_count": post.downvotes.count(),
                "user_vote": user_vote,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def add_comment(self, request, pk=None):
        """Add a comment or reply to a post"""
        post = self.get_object()
        content = request.data.get("content", "").strip()
        parent_id = request.data.get("parent_id")

        if not content:
            return Response(
                {"error": "Comment content cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parent = None
        if parent_id:
            parent = get_object_or_404(DiscussComment, id=parent_id, post=post)

        comment = DiscussComment.objects.create(
            post=post,
            author=request.user,
            parent=parent,
            content=content,
        )

        serializer = DiscussCommentSerializer(comment, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def categories(self, request):
        """Get all discussion categories with active post counts"""
        counts = dict(
            DiscussPost.objects.values("category")
            .annotate(total=Count("id"))
            .values_list("category", "total")
        )
        total_all = DiscussPost.objects.count()

        categories_data = [{"id": "ALL", "label": "All Topics", "count": total_all}]
        for cat_key, cat_label in DiscussCategory.choices:
            categories_data.append(
                {
                    "id": cat_key,
                    "label": cat_label,
                    "count": counts.get(cat_key, 0),
                }
            )

        return Response(categories_data)


class DiscussCommentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def vote(self, request, pk=None):
        """Vote (up/down) on a general discussion comment"""
        comment = get_object_or_404(DiscussComment, pk=pk)
        vote_type = request.data.get("type", "up").lower()
        user = request.user

        if vote_type == "up":
            if comment.upvotes.filter(id=user.id).exists():
                comment.upvotes.remove(user)
                user_vote = 0
            else:
                comment.upvotes.add(user)
                comment.downvotes.remove(user)
                user_vote = 1
        elif vote_type == "down":
            if comment.downvotes.filter(id=user.id).exists():
                comment.downvotes.remove(user)
                user_vote = 0
            else:
                comment.downvotes.add(user)
                comment.upvotes.remove(user)
                user_vote = -1
        else:
            comment.upvotes.remove(user)
            comment.downvotes.remove(user)
            user_vote = 0

        return Response(
            {
                "comment_id": comment.id,
                "vote_count": comment.vote_count,
                "upvotes_count": comment.upvotes.count(),
                "downvotes_count": comment.downvotes.count(),
                "user_vote": user_vote,
            }
        )

    @action(detail=True, methods=["post"])
    def upvote(self, request, pk=None):
        """Toggle upvote on a comment"""
        comment = get_object_or_404(DiscussComment, pk=pk)
        user = request.user

        if comment.upvotes.filter(id=user.id).exists():
            comment.upvotes.remove(user)
            has_upvoted = False
        else:
            comment.upvotes.add(user)
            comment.downvotes.remove(user)
            has_upvoted = True

        return Response(
            {
                "comment_id": comment.id,
                "vote_count": comment.vote_count,
                "upvotes_count": comment.upvotes.count(),
                "downvotes_count": comment.downvotes.count(),
                "user_vote": 1 if has_upvoted else 0,
            }
        )

    def destroy(self, request, pk=None):
        """Delete a comment (author or staff only)"""
        comment = get_object_or_404(DiscussComment, pk=pk)
        if comment.author != request.user and not request.user.is_staff:
            raise PermissionDenied("You can only delete your own comments.")
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
