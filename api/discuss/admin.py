from django.contrib import admin
from .models import DiscussPost, DiscussComment


class DiscussCommentInline(admin.TabularInline):
    model = DiscussComment
    extra = 0
    readonly_fields = ["author", "created_at"]


@admin.register(DiscussPost)
class DiscussPostAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "category",
        "author",
        "views",
        "pinned",
        "created_at",
    ]
    list_filter = ["category", "pinned", "created_at"]
    search_fields = ["title", "content", "author__username"]
    inlines = [DiscussCommentInline]


@admin.register(DiscussComment)
class DiscussCommentAdmin(admin.ModelAdmin):
    list_display = ["id", "post", "author", "created_at"]
    search_fields = ["content", "author__username", "post__title"]
