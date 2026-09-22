"""Optional Xquik-compatible Twitter read backend."""

from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote, urljoin

import requests

from .._branding import get_env

DEFAULT_BASE_URL = "https://xquik.com"
TIMEOUT_SECONDS = 30


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _pick(mapping: dict, *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def _find_list(value: Any, keys: tuple[str, ...]) -> list:
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return []
    for key in keys:
        item = value.get(key)
        if isinstance(item, list):
            return item
        nested = _find_list(item, keys)
        if nested:
            return nested
    for item in value.values():
        nested = _find_list(item, keys)
        if nested:
            return nested
    return []


def _metric(item: dict, metrics: dict, *keys: str) -> int:
    value = _pick(item, *keys)
    if value is None:
        value = _pick(metrics, *keys)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _normalize_tweet(item: dict) -> dict:
    author = _as_dict(_pick(item, "author", "user", "account"))
    metrics = _as_dict(_pick(item, "public_metrics", "metrics", "stats"))
    tweet_id = _pick(item, "id", "id_str", "tweetId", "tweet_id", "rest_id")
    author_id = _pick(item, "author_id", "authorId", "user_id", "userId")
    author_id = author_id or _pick(author, "id", "id_str", "rest_id")
    username = _pick(item, "author_username", "username", "screen_name")
    username = username or _pick(author, "username", "screen_name", "userName")
    url = _pick(item, "url", "tweet_url", "tweetUrl")
    if not url and tweet_id:
        url = f"https://x.com/i/web/status/{tweet_id}"
    return {
        "id": tweet_id,
        "text": _pick(item, "text", "full_text", "fullText", "content", "body"),
        "created_at": _pick(item, "created_at", "createdAt", "created"),
        "author_id": author_id,
        "author_username": username,
        "author_name": _pick(item, "author_name") or _pick(author, "name"),
        "author_followers": _metric(
            author,
            _as_dict(_pick(author, "public_metrics", "metrics")),
            "followers",
            "followers_count",
            "follower_count",
        ),
        "author_description": _pick(item, "author_description")
        or _pick(author, "description", "bio"),
        "likes": _metric(item, metrics, "likes", "like_count", "favorite_count"),
        "retweets": _metric(item, metrics, "retweets", "retweet_count"),
        "replies": _metric(item, metrics, "replies", "reply_count"),
        "url": url,
    }


class XquikReadBackend:
    """Small adapter for read-only X endpoints exposed through Xquik."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        http: Optional[Any] = None,
    ) -> None:
        self.api_key = api_key or get_env("XQUIK_API_KEY") or ""
        self.base_url = (
            base_url
            or get_env("XQUIK_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self._http = http or requests

    def available(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key}

    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict:
        if not self.available():
            return {
                "success": False,
                "error": "XQUIK_API_KEY is not configured.",
            }
        url = urljoin(f"{self.base_url}/", path.lstrip("/"))
        response = self._http.get(
            url,
            params=params or {},
            headers=self._headers(),
            timeout=TIMEOUT_SECONDS,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"text": response.text}
        if response.status_code < 200 or response.status_code >= 300:
            return {
                "success": False,
                "error": f"{response.status_code}: {response.text}",
                "status_code": response.status_code,
                "response": payload,
            }
        return payload if isinstance(payload, dict) else {"data": payload}

    def _tweets_result(
        self, payload: dict, key: str, limit: Optional[int] = None
    ) -> dict:
        if payload.get("success") is False:
            return payload
        items = _find_list(payload, ("tweets", key, "data", "results", "items"))
        tweets = [_normalize_tweet(item) for item in items if isinstance(item, dict)]
        if limit is not None:
            tweets = tweets[: max(1, min(limit, 100))]
        return {"success": True, key: tweets, "count": len(tweets)}

    def search_tweets(
        self, query: str, limit: int = 10, include_users: bool = True
    ) -> dict:
        _ = include_users
        payload = self._get(
            "/api/v1/x/tweets/search",
            params={"q": query, "limit": max(1, min(limit, 100))},
        )
        return self._tweets_result(payload, "tweets")

    def user_tweets(self, username: str, limit: int = 10) -> dict:
        payload = self._get(
            f"/api/v1/x/users/{quote(username.lstrip('@'))}/tweets",
            params={"includeReplies": "false"},
        )
        return self._tweets_result(payload, "tweets", limit=limit)

    def mentions(self, username: str, limit: int = 10) -> dict:
        payload = self._get(
            f"/api/v1/x/users/{quote(username.lstrip('@'))}/mentions",
        )
        return self._tweets_result(payload, "mentions", limit=limit)

    def replies(self, username: str, limit: int = 10) -> dict:
        result = self.search_tweets(
            f"to:{username.lstrip('@')} -from:{username.lstrip('@')}",
            limit=limit,
            include_users=True,
        )
        if not result.get("success"):
            return result
        replies = result.get("tweets", [])
        return {"success": True, "replies": replies, "count": len(replies)}
