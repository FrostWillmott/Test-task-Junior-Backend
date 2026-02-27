from typing import Any

import pytest
from rest_framework.test import APIClient

from instagram.models import Post
from instagram.services.instagram_client import InstagramAPIError


@pytest.mark.django_db
class TestSyncAPI:
    def setup_method(self) -> None:
        self.client = APIClient()
        self.url = "/api/sync/"

    def test_sync_creates_posts(
        self, fake_media: list[dict], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def mock_get_user_media(self: Any) -> list[dict[str, Any]]:
            return fake_media

        monkeypatch.setattr(
            "instagram.views.InstagramClient.get_user_media", mock_get_user_media
        )

        resp = self.client.post(self.url)
        assert resp.status_code == 200
        assert resp.json() == {"synced": 2}
        assert Post.objects.count() == 2
        assert Post.objects.filter(instagram_id="17896400000000001").exists()

    def test_sync_updates_existing_posts(
        self, fake_media: list[dict], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        Post.objects.create(
            instagram_id="17896400000000001",
            caption="Old caption",
            media_type="IMAGE",
            media_url="https://example.com/old.jpg",
            permalink="https://instagram.com/p/aaa/",
            timestamp="2024-01-01T00:00:00+0000",
        )

        def mock_get_user_media(self: Any) -> list[dict[str, Any]]:
            return fake_media

        monkeypatch.setattr(
            "instagram.views.InstagramClient.get_user_media", mock_get_user_media
        )

        resp = self.client.post(self.url)
        assert resp.status_code == 200
        assert resp.json() == {"synced": 2}
        assert Post.objects.count() == 2

        updated = Post.objects.get(instagram_id="17896400000000001")
        assert updated.caption == "First post"

    def test_sync_instagram_api_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def mock_get_user_media(self: Any) -> list[dict[str, Any]]:
            raise InstagramAPIError("invalid token")

        monkeypatch.setattr(
            "instagram.views.InstagramClient.get_user_media", mock_get_user_media
        )

        resp = self.client.post(self.url)
        assert resp.status_code == 400
        assert "invalid token" in resp.json()["detail"]
