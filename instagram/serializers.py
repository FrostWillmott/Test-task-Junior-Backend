from __future__ import annotations

from typing import Any, ClassVar

from rest_framework import serializers

from .models import Comment, Post


class CommentSerializer(serializers.ModelSerializer[Comment]):
    """Сериализатор для комментариев к постам."""

    class Meta:
        model = Comment
        fields: ClassVar[list[str]] = [
            "id",
            "instagram_comment_id",
            "text",
            "created_at",
            "post",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "instagram_comment_id",
            "created_at",
            "post",
        ]


class PostSerializer(serializers.ModelSerializer[Post]):
    """Сериализатор для постов Instagram."""

    comments_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Post
        fields: ClassVar[list[str]] = [
            "id",
            "instagram_id",
            "caption",
            "media_type",
            "media_url",
            "permalink",
            "timestamp",
            "created_at",
            "updated_at",
            "comments_count",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "created_at",
            "updated_at",
            "comments_count",
        ]


class CreateCommentInputSerializer(serializers.Serializer[dict[str, Any]]):
    """Входной сериализатор для создания комментария."""

    text = serializers.CharField(
        max_length=2200,
        help_text="Comment text for an Instagram post (up to 2200 characters).",
    )


class SyncResultSerializer(serializers.Serializer[dict[str, Any]]):
    """Сериализатор результата синхронизации."""

    synced = serializers.IntegerField(
        help_text="Number of posts synced from Instagram.",
        min_value=0,
    )
