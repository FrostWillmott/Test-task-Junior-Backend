from __future__ import annotations

from typing import ClassVar

from django.db import models


class Post(models.Model):
    """Модель для хранения медиа-объектов (постов) из Instagram."""

    instagram_id = models.CharField(
        max_length=255, unique=True, verbose_name="Instagram ID"
    )
    caption = models.TextField(blank=True, null=True, verbose_name="Подпись")
    media_type = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Тип медиа"
    )
    media_url = models.URLField(
        max_length=1000, blank=True, null=True, verbose_name="URL медиа"
    )
    permalink = models.URLField(
        max_length=1000, blank=True, null=True, verbose_name="Ссылка"
    )
    timestamp = models.DateTimeField(
        db_index=True, verbose_name="Дата создания в Instagram"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-timestamp"]

    def __str__(self) -> str:
        return f"Post {self.instagram_id}"


class Comment(models.Model):
    """Модель для хранения комментариев, отправленных через наше API."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Пост",
    )
    instagram_comment_id = models.CharField(
        max_length=255, unique=True, verbose_name="Instagram Comment ID"
    )
    text = models.TextField(verbose_name="Текст комментария")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self) -> str:
        return f"Comment {self.instagram_comment_id} on Post {self.post.instagram_id}"
