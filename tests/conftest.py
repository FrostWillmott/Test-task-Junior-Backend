import pytest

from instagram.models import Post

FAKE_MEDIA = [
    {
        "id": "17896400000000001",
        "caption": "First post",
        "media_type": "IMAGE",
        "media_url": "https://example.com/1.jpg",
        "permalink": "https://instagram.com/p/aaa/",
        "timestamp": "2024-01-01T00:00:00+0000",
    },
    {
        "id": "17896400000000002",
        "caption": "Second post",
        "media_type": "VIDEO",
        "media_url": "https://example.com/2.mp4",
        "permalink": "https://instagram.com/p/bbb/",
        "timestamp": "2024-01-02T00:00:00+0000",
    },
]


@pytest.fixture
def sample_post(db) -> Post:
    return Post.objects.create(
        instagram_id="17896400000000000",
        caption="Test",
        media_type="IMAGE",
        media_url="https://example.com/image.jpg",
        permalink="https://instagram.com/p/abc/",
        timestamp="2024-01-01T00:00:00+0000",
    )


@pytest.fixture
def fake_media() -> list[dict]:
    return [item.copy() for item in FAKE_MEDIA]
