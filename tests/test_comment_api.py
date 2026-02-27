from typing import Any

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from instagram.models import Comment, Post
from instagram.services.instagram_client import InstagramPostNotFoundError


@pytest.mark.django_db
class TestCreateCommentAPI:
    def setup_method(self) -> None:
        self.client = APIClient()

    def test_create_comment_success(
        self, sample_post: Post, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def mock_post_comment(self: Any, media_id: str, text: str) -> dict[str, str]:
            assert media_id == sample_post.instagram_id
            return {"id": "17900000000000000"}

        monkeypatch.setattr(
            "instagram.views.InstagramClient.post_comment", mock_post_comment
        )

        url = reverse("post-comment", args=[sample_post.id])
        resp = self.client.post(url, data={"text": "Hello IG!"}, format="json")

        assert resp.status_code == 201
        data = resp.json()
        assert data["instagram_comment_id"] == "17900000000000000"
        assert data["text"] == "Hello IG!"
        assert Comment.objects.filter(
            post=sample_post, instagram_comment_id="17900000000000000"
        ).exists()

    def test_create_comment_post_not_in_db(self) -> None:
        url = reverse("post-comment", args=[99999])
        resp = self.client.post(url, data={"text": "Hello IG!"}, format="json")
        assert resp.status_code == 404

    def test_create_comment_post_missing_in_instagram(
        self, sample_post: Post, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def raise_ig_404(self: Any, media_id: str, text: str) -> None:
            raise InstagramPostNotFoundError("Post not found in Instagram")

        monkeypatch.setattr(
            "instagram.views.InstagramClient.post_comment", raise_ig_404
        )

        url = reverse("post-comment", args=[sample_post.id])
        resp = self.client.post(url, data={"text": "Hello IG!"}, format="json")

        assert resp.status_code == 404
        assert resp.json().get("detail") == "Post not found in Instagram"

    def test_create_comment_empty_text(self, sample_post: Post) -> None:
        url = reverse("post-comment", args=[sample_post.id])
        resp = self.client.post(url, data={"text": ""}, format="json")
        assert resp.status_code == 400

    def test_create_comment_too_long_text(self, sample_post: Post) -> None:
        url = reverse("post-comment", args=[sample_post.id])
        resp = self.client.post(url, data={"text": "a" * 2201}, format="json")
        assert resp.status_code == 400

    def test_create_comment_duplicate_id(
        self, sample_post: Post, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        comment_id = "17900000000000000"
        Comment.objects.create(
            post=sample_post, instagram_comment_id=comment_id, text="Existing"
        )

        def mock_post_comment(self: Any, media_id: str, text: str) -> dict[str, str]:
            return {"id": comment_id}

        monkeypatch.setattr(
            "instagram.views.InstagramClient.post_comment", mock_post_comment
        )

        url = reverse("post-comment", args=[sample_post.id])
        resp = self.client.post(url, data={"text": "New text"}, format="json")

        assert resp.status_code == 201
        assert Comment.objects.filter(instagram_comment_id=comment_id).count() == 1
