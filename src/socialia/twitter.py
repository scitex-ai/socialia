"""Twitter/X API v2 poster."""

__all__ = ["Twitter"]

from typing import Any, Callable, Optional

from requests_oauthlib import OAuth1Session

from ._branding import get_env
from ._base import _Base
from ._twitter.growth import TwitterGrowthMixin
from ._twitter.read_backend import XquikReadBackend


class Twitter(TwitterGrowthMixin, _Base):
    """Twitter/X API v2 client using OAuth 1.0a."""

    platform_name = "twitter"
    MAX_TWEET_LENGTH = 280

    POST_ENDPOINT = "https://api.x.com/2/tweets"
    DELETE_ENDPOINT = "https://api.x.com/2/tweets/{tweet_id}"
    ME_ENDPOINT = "https://api.x.com/2/users/me"
    USER_TWEETS_ENDPOINT = "https://api.x.com/2/users/{user_id}/tweets"
    USER_MENTIONS_ENDPOINT = "https://api.x.com/2/users/{user_id}/mentions"
    SEARCH_ENDPOINT = "https://api.x.com/2/tweets/search/recent"
    MEDIA_UPLOAD_ENDPOINT = "https://upload.twitter.com/1.1/media/upload.json"
    USER_BY_USERNAME_ENDPOINT = "https://api.x.com/2/users/by/username/{username}"
    FOLLOW_ENDPOINT = "https://api.x.com/2/users/{source_user_id}/following"
    UNFOLLOW_ENDPOINT = (
        "https://api.x.com/2/users/{source_user_id}/following/{target_user_id}"
    )

    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        *,
        session_factory: Optional[Callable[[], object]] = None,
        read_backend: Optional[Any] = None,
        read_username: Optional[str] = None,
    ):
        # ``session_factory`` is a zero-arg callable that returns the HTTP
        # session object used to talk to the Twitter API.  Production code
        # leaves it ``None`` (and we build a real ``OAuth1Session``).  Tests
        # pass a hand-rolled fake to exercise behaviour without hitting the
        # network — see ``tests/test_twitter.py``.
        self.consumer_key = consumer_key or get_env("X_CONSUMER_KEY")
        self.consumer_secret = consumer_secret or get_env("X_CONSUMER_KEY_SECRET")
        self.access_token = access_token or get_env("X_ACCESSTOKEN")
        self.access_token_secret = access_token_secret or get_env(
            "X_ACCESSTOKEN_SECRET"
        )
        self._session_factory = session_factory
        self.read_username = (read_username or get_env("X_READ_USERNAME") or "").lstrip(
            "@"
        )
        self._read_backend = read_backend or self._configured_read_backend()

    def _configured_read_backend(self) -> Optional[XquikReadBackend]:
        backend = (get_env("X_READ_BACKEND") or "").lower().replace("_", "-")
        if backend == "xquik":
            return XquikReadBackend()
        return None

    def _has_read_backend(self) -> bool:
        if self._read_backend is None:
            return False
        available = getattr(self._read_backend, "available", None)
        if callable(available):
            return bool(available())
        return True

    def _read_backend_call(self, method_name: str, *args, **kwargs) -> Optional[dict]:
        if not self._has_read_backend():
            return None
        method = getattr(self._read_backend, method_name, None)
        if callable(method):
            return method(*args, **kwargs)
        return None

    def _read_backend_user_call(self, method_name: str, **kwargs) -> Optional[dict]:
        if not self.read_username:
            return None
        return self._read_backend_call(method_name, self.read_username, **kwargs)

    def _get_session(self):
        """Create OAuth1 session (or the injected fake session)."""
        if self._session_factory is not None:
            return self._session_factory()
        return OAuth1Session(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )

    def validate_credentials(self) -> bool:
        """Check if all credentials are set."""
        return all(
            [
                self.consumer_key,
                self.consumer_secret,
                self.access_token,
                self.access_token_secret,
            ]
        )

    def validate_read_credentials(self) -> bool:
        """Check if read operations can use OAuth or the optional read backend."""
        return self.validate_credentials() or (
            self._has_read_backend() and bool(self.read_username)
        )

    def upload_media(self, file_path: str) -> dict:
        """
        Upload media file to Twitter (images and videos).

        Automatically detects file type and uses:
        - Simple upload for images (jpg, png, gif, webp)
        - Chunked upload for videos (mp4, mov)

        Args:
            file_path: Path to media file

        Returns:
            dict with 'success', 'media_id' or 'error'
        """
        from ._twitter import media as _twitter_media

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        return _twitter_media.upload_media(self._get_session(), file_path)

    def post(
        self,
        text: str,
        reply_to: Optional[str] = None,
        quote_tweet_id: Optional[str] = None,
        media_ids: Optional[list] = None,
    ) -> dict:
        """
        Post a tweet.

        Args:
            text: Tweet content (max 280 chars standard, 25000 premium)
            reply_to: Tweet ID to reply to
            quote_tweet_id: Tweet ID to quote
            media_ids: List of media IDs from upload_media()

        Returns:
            dict with 'success', 'id', 'url' or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        # Validate tweet length
        if len(text) > self.MAX_TWEET_LENGTH:
            return {
                "success": False,
                "error": f"Tweet too long: {len(text)} chars (max {self.MAX_TWEET_LENGTH})",
            }

        oauth = self._get_session()
        payload = {"text": text}

        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}
        if quote_tweet_id:
            payload["quote_tweet_id"] = quote_tweet_id
        if media_ids:
            payload["media"] = {"media_ids": media_ids}

        response = oauth.post(self.POST_ENDPOINT, json=payload)

        if response.status_code == 201:
            data = response.json()
            tweet_id = data["data"]["id"]
            return {
                "success": True,
                "id": tweet_id,
                "url": f"https://x.com/i/web/status/{tweet_id}",
            }
        else:
            return {
                "success": False,
                "error": f"{response.status_code}: {response.text}",
            }

    def delete(self, post_id: str) -> dict:
        """
        Delete a tweet.

        Args:
            post_id: Tweet ID to delete

        Returns:
            dict with 'success' and 'deleted' or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        oauth = self._get_session()
        url = self.DELETE_ENDPOINT.format(tweet_id=post_id)
        response = oauth.delete(url)

        if response.status_code == 200:
            return {"success": True, "deleted": True}
        else:
            return {
                "success": False,
                "error": f"{response.status_code}: {response.text}",
            }

    def post_thread(self, tweets: list[str]) -> dict:
        """
        Post a thread of tweets.

        Args:
            tweets: List of tweet texts

        Returns:
            dict with 'success', 'ids', 'urls' or 'error'
        """
        # Validate all tweets before posting
        for i, text in enumerate(tweets):
            if len(text) > self.MAX_TWEET_LENGTH:
                return {
                    "success": False,
                    "error": f"Tweet {i + 1} too long: {len(text)} chars (max {self.MAX_TWEET_LENGTH})",
                }

        ids = []
        urls = []
        reply_to = None

        for i, text in enumerate(tweets):
            result = self.post(text, reply_to=reply_to)
            if result["success"]:
                ids.append(result["id"])
                urls.append(result["url"])
                reply_to = result["id"]
            else:
                return {
                    "success": False,
                    "error": f"Failed at tweet {i + 1}: {result['error']}",
                    "partial_ids": ids,
                }

        return {"success": True, "ids": ids, "urls": urls}

    def me(self) -> dict:
        """
        Get authenticated user information.

        Returns:
            dict with 'success', 'id', 'username', 'name' or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        oauth = self._get_session()
        response = oauth.get(
            self.ME_ENDPOINT,
            params={"user.fields": "id,name,username,public_metrics,profile_image_url"},
        )

        if response.status_code == 200:
            data = response.json()["data"]
            return {
                "success": True,
                "id": data["id"],
                "username": data["username"],
                "name": data["name"],
                "followers": data.get("public_metrics", {}).get("followers_count", 0),
                "following": data.get("public_metrics", {}).get("following_count", 0),
                "tweets": data.get("public_metrics", {}).get("tweet_count", 0),
                "url": f"https://x.com/{data['username']}",
            }
        return {"success": False, "error": f"{response.status_code}: {response.text}"}

    def feed(self, limit: int = 10) -> dict:
        """
        Get user's recent tweets.

        Args:
            limit: Maximum number of tweets to return (max 100)

        Returns:
            dict with 'success', 'tweets' list or 'error'
        """
        backend_result = self._read_backend_user_call("user_tweets", limit=limit)
        if backend_result is not None:
            return backend_result

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        # First get user ID
        user_info = self.me()
        if not user_info.get("success"):
            return user_info

        oauth = self._get_session()
        url = self.USER_TWEETS_ENDPOINT.format(user_id=user_info["id"])
        response = oauth.get(
            url,
            params={
                "max_results": max(5, min(limit, 100)),  # Twitter API requires 5-100
                "tweet.fields": "created_at,public_metrics,text",
            },
        )

        if response.status_code == 200:
            data = response.json()
            tweets = []
            for tweet in data.get("data", []):
                metrics = tweet.get("public_metrics", {})
                tweets.append(
                    {
                        "id": tweet["id"],
                        "text": tweet["text"],
                        "created_at": tweet.get("created_at"),
                        "likes": metrics.get("like_count", 0),
                        "retweets": metrics.get("retweet_count", 0),
                        "replies": metrics.get("reply_count", 0),
                        "url": f"https://x.com/i/web/status/{tweet['id']}",
                    }
                )
            return {"success": True, "tweets": tweets, "count": len(tweets)}
        return {"success": False, "error": f"{response.status_code}: {response.text}"}

    def mentions(self, limit: int = 10) -> dict:
        """
        Get recent mentions of the user.

        Args:
            limit: Maximum number of mentions to return (max 100)

        Returns:
            dict with 'success', 'mentions' list or 'error'
        """
        backend_result = self._read_backend_user_call("mentions", limit=limit)
        if backend_result is not None:
            return backend_result

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        # First get user ID
        user_info = self.me()
        if not user_info.get("success"):
            return user_info

        oauth = self._get_session()
        url = self.USER_MENTIONS_ENDPOINT.format(user_id=user_info["id"])
        response = oauth.get(
            url,
            params={
                "max_results": max(5, min(limit, 100)),  # Twitter API requires 5-100
                "tweet.fields": "created_at,public_metrics,text,author_id",
                "expansions": "author_id",
                "user.fields": "username,name",
            },
        )

        if response.status_code == 200:
            data = response.json()
            # Build user lookup
            users = {}
            for user in data.get("includes", {}).get("users", []):
                users[user["id"]] = user

            mentions = []
            for tweet in data.get("data", []):
                author = users.get(tweet.get("author_id"), {})
                mentions.append(
                    {
                        "id": tweet["id"],
                        "text": tweet["text"],
                        "created_at": tweet.get("created_at"),
                        "author_id": tweet.get("author_id"),
                        "author_username": author.get("username"),
                        "author_name": author.get("name"),
                        "url": f"https://x.com/i/web/status/{tweet['id']}",
                    }
                )
            return {"success": True, "mentions": mentions, "count": len(mentions)}
        return {"success": False, "error": f"{response.status_code}: {response.text}"}

    def replies(self, limit: int = 10) -> dict:
        """
        Get recent replies to the user's tweets.

        Args:
            limit: Maximum number of replies to return (max 100)

        Returns:
            dict with 'success', 'replies' list or 'error'
        """
        backend_result = self._read_backend_user_call("replies", limit=limit)
        if backend_result is not None:
            return backend_result

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        # First get user info
        user_info = self.me()
        if not user_info.get("success"):
            return user_info

        oauth = self._get_session()
        # Search for replies to this user (excluding own tweets)
        query = f"to:{user_info['username']} -from:{user_info['username']}"
        response = oauth.get(
            self.SEARCH_ENDPOINT,
            params={
                "query": query,
                "max_results": max(10, min(limit, 100)),  # Search requires 10-100
                "tweet.fields": "created_at,public_metrics,text,author_id,in_reply_to_user_id,conversation_id",
                "expansions": "author_id",
                "user.fields": "username,name",
            },
        )

        if response.status_code == 200:
            data = response.json()
            # Build user lookup
            users = {}
            for user in data.get("includes", {}).get("users", []):
                users[user["id"]] = user

            replies = []
            for tweet in data.get("data", []):
                author = users.get(tweet.get("author_id"), {})
                metrics = tweet.get("public_metrics", {})
                replies.append(
                    {
                        "id": tweet["id"],
                        "text": tweet["text"],
                        "created_at": tweet.get("created_at"),
                        "author_id": tweet.get("author_id"),
                        "author_username": author.get("username"),
                        "author_name": author.get("name"),
                        "conversation_id": tweet.get("conversation_id"),
                        "likes": metrics.get("like_count", 0),
                        "retweets": metrics.get("retweet_count", 0),
                        "url": f"https://x.com/i/web/status/{tweet['id']}",
                    }
                )
            return {"success": True, "replies": replies, "count": len(replies)}
        return {"success": False, "error": f"{response.status_code}: {response.text}"}
