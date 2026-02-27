from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment, Post
from .serializers import (
    CommentSerializer,
    CreateCommentInputSerializer,
    PostSerializer,
    SyncResultSerializer,
)
from .services.instagram_client import (
    InstagramAPIError,
    InstagramClient,
    InstagramPostNotFoundError,
)


class SyncView(APIView):
    """Эндпоинт синхронизации постов из Instagram."""

    serializer_class = SyncResultSerializer

    @extend_schema(
        operation_id="sync_posts",
        description=(
            "Syncs posts from the Instagram API and "
            "updates/creates records in the database. "
            "Returns the number of synced posts."
        ),
        request=None,
        responses={
            status.HTTP_200_OK: SyncResultSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Instagram API request error.",
                examples=[
                    OpenApiExample(
                        "Instagram API error",
                        value={"detail": "Instagram API error: invalid token"},
                    ),
                ],
            ),
        },
        examples=[
            OpenApiExample(
                "Successful sync",
                value={"synced": 12},
                response_only=True,
            ),
        ],
        tags=["sync"],
    )
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """Синхронизирует посты из Instagram API в базу данных."""
        # TODO: вынести в Celery-задачу для асинхронного выполнения,
        client = InstagramClient()
        try:
            media_list = client.get_user_media()
        except InstagramAPIError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_fields = [
            "caption",
            "media_type",
            "media_url",
            "permalink",
            "timestamp",
            "updated_at",
        ]
        now = timezone.now()
        posts = [
            Post(
                instagram_id=media["id"],
                caption=media.get("caption"),
                media_type=media.get("media_type"),
                media_url=media.get("media_url"),
                permalink=media.get("permalink"),
                timestamp=media["timestamp"],
                updated_at=now,
            )
            for media in media_list
        ]
        with transaction.atomic():
            Post.objects.bulk_create(
                posts,
                update_conflicts=True,
                unique_fields=["instagram_id"],
                update_fields=update_fields,
            )
        return Response({"synced": len(media_list)}, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        operation_id="list_posts",
        description="List posts with comments count.",
        tags=["posts"],
    ),
    retrieve=extend_schema(
        operation_id="retrieve_post",
        description="Retrieve post details by ID.",
        tags=["posts"],
    ),
)
class PostViewSet(viewsets.ReadOnlyModelViewSet[Post]):
    """ViewSet для просмотра постов и создания комментариев."""

    queryset = Post.objects.annotate(comments_count=Count("comments"))
    serializer_class = PostSerializer

    @extend_schema(
        operation_id="create_comment",
        description=(
            "Creates a comment on an Instagram post and stores it in the database."
        ),
        request=CreateCommentInputSerializer,
        responses={
            status.HTTP_201_CREATED: CommentSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Instagram API request error.",
                examples=[
                    OpenApiExample(
                        "Instagram API error",
                        value={"detail": "Instagram API error"},
                    ),
                ],
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Post not found in Instagram.",
                examples=[
                    OpenApiExample(
                        "Post not found",
                        value={"detail": "Post not found in Instagram"},
                    ),
                ],
            ),
        },
        examples=[
            OpenApiExample(
                "Request example",
                value={"text": "Great post!"},
                request_only=True,
            ),
            OpenApiExample(
                "Response example",
                value={
                    "id": 1,
                    "instagram_comment_id": "17896450804099477",
                    "text": "Great post!",
                    "created_at": "2026-02-24T14:18:00Z",
                    "post": 10,
                },
                response_only=True,
            ),
        ],
        tags=["posts"],
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="comment",
    )
    def comment(self, request: Any, pk: str | None = None) -> Response:
        """Создаёт комментарий к посту в Instagram и сохраняет в БД."""
        post = get_object_or_404(Post, pk=pk)
        input_serializer = CreateCommentInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        text = input_serializer.validated_data["text"]

        client = InstagramClient()
        try:
            data = client.post_comment(media_id=post.instagram_id, text=text)
        except InstagramPostNotFoundError:
            return Response(
                {"detail": "Post not found in Instagram"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except InstagramAPIError:
            return Response(
                {"detail": "Instagram API error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instagram_comment_id = str(data.get("id"))
        with transaction.atomic():
            comment, _ = Comment.objects.get_or_create(
                instagram_comment_id=instagram_comment_id,
                defaults={
                    "post": post,
                    "text": text,
                },
            )
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )
