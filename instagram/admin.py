from django.contrib import admin

from .models import Comment, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Админка для модели Post."""

    list_display = (
        "instagram_id",
        "caption",
        "media_type",
        "timestamp",
        "created_at",
    )
    list_filter = ("media_type", "timestamp")
    search_fields = ("instagram_id", "caption")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Админка для модели Comment."""

    list_display = ("instagram_comment_id", "post", "text", "created_at")
    list_filter = ("created_at",)
    search_fields = ("instagram_comment_id", "text")
    readonly_fields = ("created_at",)
