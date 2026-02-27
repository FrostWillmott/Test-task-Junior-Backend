import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class InstagramAPIError(Exception):
    """Базовое исключение для ошибок Instagram API."""


class InstagramPostNotFoundError(InstagramAPIError):
    """Пост не найден в Instagram."""


class InstagramClient:
    """Client for Instagram API with Instagram Login."""

    DEFAULT_BASE_URL = "https://graph.instagram.com"

    @staticmethod
    def _safe_error_message(
        response: requests.Response,
        default: str = "Instagram API error",
    ) -> str:
        """Build a safe Instagram error message without leaking tokens or URLs."""
        message = default
        try:
            err_json = response.json()
            err = err_json.get("error", {})
            code = err.get("code")
            etype = err.get("type")
            emsg = err.get("message")
            details: list[str] = []
            if etype:
                details.append(f"type={etype}")
            if code is not None:
                details.append(f"code={code}")
            if emsg:
                details.append(f"message={emsg}")
            if details:
                message = "Instagram API error: " + ", ".join(details)
        except Exception:
            pass
        return message

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.token = token or settings.INSTAGRAM_TOKEN
        self.base_url = base_url or getattr(
            settings, "INSTAGRAM_API_BASE_URL", self.DEFAULT_BASE_URL
        )

    def get_user_media(self) -> list[dict[str, Any]]:
        """Получает все медиа-объекты пользователя, обходя пагинацию."""
        url = f"{self.base_url}/me/media"
        params: dict[str, Any] = {
            "fields": "id,caption,media_type,media_url,permalink,timestamp",
            "access_token": self.token,
        }

        all_media: list[dict[str, Any]] = []

        while url:
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                all_media.extend(data.get("data", []))

                url = data.get("paging", {}).get("next")
                params = {}
            except requests.exceptions.HTTPError as e:
                message = self._safe_error_message(response)
                logger.error("Error fetching media: %s", message)
                raise InstagramAPIError(message) from e
            except requests.exceptions.RequestException as e:
                logger.error("Network error fetching media: %s", e)
                raise InstagramAPIError(f"Network error: {e}") from e

        return all_media

    def post_comment(self, media_id: str, text: str) -> dict[str, Any]:
        """Отправляет комментарий к указанному медиа-объекту."""
        url = f"{self.base_url}/{media_id}/comments"
        payload = {"message": text, "access_token": self.token}

        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 404:
                raise InstagramPostNotFoundError(
                    f"Post {media_id} not found in Instagram"
                )

            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_code = error_data.get("error", {}).get("code")
                    if error_code == 100:
                        raise InstagramPostNotFoundError(
                            f"Post {media_id} not found in Instagram"
                        )
                except (ValueError, KeyError):
                    pass

            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except InstagramPostNotFoundError:
            raise
        except requests.exceptions.HTTPError as e:
            message = self._safe_error_message(response)
            logger.error("Error posting comment to %s: %s", media_id, message)
            raise InstagramAPIError(message) from e
        except requests.exceptions.RequestException as e:
            logger.error("Network error posting comment: %s", e)
            raise InstagramAPIError(f"Network error: {e}") from e
