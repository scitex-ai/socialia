"""Twitter growth features: follow, discover users, search."""

__all__ = ["TwitterGrowthMixin"]

# Rate limit: 15 requests per 15 minutes for follow endpoint
RATE_LIMIT_WINDOW = 15 * 60  # 15 minutes in seconds
RATE_LIMIT_REQUESTS = 15


class TwitterGrowthMixin:
    """Mixin providing Twitter growth and discovery features."""

    USER_BY_USERNAME_ENDPOINT = "https://api.x.com/2/users/by/username/{username}"
    FOLLOW_ENDPOINT = "https://api.x.com/2/users/{source_user_id}/following"
    UNFOLLOW_ENDPOINT = (
        "https://api.x.com/2/users/{source_user_id}/following/{target_user_id}"
    )
    FOLLOWERS_ENDPOINT = "https://api.x.com/2/users/{user_id}/followers"
    FOLLOWING_ENDPOINT = "https://api.x.com/2/users/{user_id}/following"

    def get_user(self, username: str) -> dict:
        """
        Get user information by username.

        Args:
            username: Twitter username (without @)

        Returns:
            dict with 'success', 'id', 'username', 'name', 'followers', etc.
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        oauth = self._get_session()
        username = username.lstrip("@")
        url = self.USER_BY_USERNAME_ENDPOINT.format(username=username)
        response = oauth.get(
            url,
            params={"user.fields": "id,name,username,public_metrics,description"},
        )

        if response.status_code == 200:
            data = response.json().get("data", {})
            metrics = data.get("public_metrics", {})
            return {
                "success": True,
                "id": data.get("id"),
                "username": data.get("username"),
                "name": data.get("name"),
                "description": data.get("description"),
                "followers": metrics.get("followers_count", 0),
                "following": metrics.get("following_count", 0),
                "tweets": metrics.get("tweet_count", 0),
            }
        return {"success": False, "error": f"{response.status_code}: {response.text}"}

    def follow(self, user_id: str) -> dict:
        """
        Follow a user by their ID.

        Args:
            user_id: Twitter user ID to follow

        Returns:
            dict with 'success', 'following' or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        me = self.me()
        if not me.get("success"):
            return me

        oauth = self._get_session()
        url = self.FOLLOW_ENDPOINT.format(source_user_id=me["id"])
        response = oauth.post(url, json={"target_user_id": str(user_id)})

        if response.status_code == 200:
            data = response.json().get("data", {})
            return {
                "success": True,
                "following": data.get("following", True),
                "pending": data.get("pending_follow", False),
            }
        return {"success": False, "error": f"{response.status_code}: {response.text}"}

    def unfollow(self, user_id: str) -> dict:
        """
        Unfollow a user by their ID.

        Args:
            user_id: Twitter user ID to unfollow

        Returns:
            dict with 'success', 'following' or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        me = self.me()
        if not me.get("success"):
            return me

        oauth = self._get_session()
        url = self.UNFOLLOW_ENDPOINT.format(
            source_user_id=me["id"], target_user_id=user_id
        )
        response = oauth.delete(url)

        if response.status_code == 200:
            data = response.json().get("data", {})
            return {"success": True, "following": data.get("following", False)}
        return {"success": False, "error": f"{response.status_code}: {response.text}"}

    def follow_by_username(self, username: str) -> dict:
        """
        Follow a user by their username.

        Args:
            username: Twitter username (with or without @)

        Returns:
            dict with 'success', 'following', 'user' or 'error'
        """
        user = self.get_user(username)
        if not user.get("success"):
            return user

        result = self.follow(user["id"])
        if result.get("success"):
            result["user"] = user
        return result

    def get_followers(self, limit: int = 100) -> dict:
        """
        Get list of users who follow the authenticated user.

        Args:
            limit: Maximum number of accounts to return (max 1000)

        Returns:
            dict with 'success', 'followers' list or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        me = self.me()
        if not me.get("success"):
            return me

        oauth = self._get_session()
        url = self.FOLLOWERS_ENDPOINT.format(user_id=me["id"])
        all_followers = []
        pagination_token = None

        while len(all_followers) < limit:
            params = {
                "max_results": min(100, limit - len(all_followers)),
                "user.fields": "id,name,username,public_metrics,description",
            }
            if pagination_token:
                params["pagination_token"] = pagination_token

            response = oauth.get(url, params=params)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"{response.status_code}: {response.text}",
                }

            data = response.json()
            for user in data.get("data", []):
                metrics = user.get("public_metrics", {})
                all_followers.append(
                    {
                        "id": user["id"],
                        "username": user.get("username"),
                        "name": user.get("name"),
                        "description": user.get("description"),
                        "followers": metrics.get("followers_count", 0),
                        "following": metrics.get("following_count", 0),
                    }
                )

            pagination_token = data.get("meta", {}).get("next_token")
            if not pagination_token:
                break

        return {
            "success": True,
            "followers": all_followers,
            "count": len(all_followers),
        }

    def get_following(self, limit: int = 100) -> dict:
        """
        Get list of users the authenticated user follows.

        Args:
            limit: Maximum number of users to return (max 1000)

        Returns:
            dict with 'success', 'following' list or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        me = self.me()
        if not me.get("success"):
            return me

        oauth = self._get_session()
        url = self.FOLLOWING_ENDPOINT.format(user_id=me["id"])
        all_following = []
        pagination_token = None

        while len(all_following) < limit:
            params = {
                "max_results": min(100, limit - len(all_following)),
                "user.fields": "id,name,username,public_metrics,description",
            }
            if pagination_token:
                params["pagination_token"] = pagination_token

            response = oauth.get(url, params=params)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"{response.status_code}: {response.text}",
                }

            data = response.json()
            for user in data.get("data", []):
                metrics = user.get("public_metrics", {})
                all_following.append(
                    {
                        "id": user["id"],
                        "username": user.get("username"),
                        "name": user.get("name"),
                        "description": user.get("description"),
                        "followers": metrics.get("followers_count", 0),
                        "following": metrics.get("following_count", 0),
                    }
                )

            pagination_token = data.get("meta", {}).get("next_token")
            if not pagination_token:
                break

        return {
            "success": True,
            "following": all_following,
            "count": len(all_following),
        }

    def search_tweets(
        self, query: str, limit: int = 10, include_users: bool = True
    ) -> dict:
        """
        Search for recent tweets matching a query.

        Args:
            query: Search query (supports Twitter search operators)
            limit: Maximum results (10-100)
            include_users: Include user info for each tweet

        Returns:
            dict with 'success', 'tweets' list or 'error'
        """
        backend_result = self._read_backend_call(
            "search_tweets",
            query,
            limit=limit,
            include_users=include_users,
        )
        if backend_result is not None:
            return backend_result

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        oauth = self._get_session()
        params = {
            "query": query,
            "max_results": max(10, min(limit, 100)),
            "tweet.fields": "created_at,public_metrics,text,author_id",
        }
        if include_users:
            params["expansions"] = "author_id"
            params["user.fields"] = "username,name,public_metrics,description"

        response = oauth.get(self.SEARCH_ENDPOINT, params=params)

        if response.status_code == 200:
            data = response.json()
            users = {}
            if include_users:
                for user in data.get("includes", {}).get("users", []):
                    users[user["id"]] = user

            tweets = []
            for tweet in data.get("data", []):
                author = users.get(tweet.get("author_id"), {})
                author_metrics = author.get("public_metrics", {})
                tweet_metrics = tweet.get("public_metrics", {})
                tweets.append(
                    {
                        "id": tweet["id"],
                        "text": tweet["text"],
                        "created_at": tweet.get("created_at"),
                        "author_id": tweet.get("author_id"),
                        "author_username": author.get("username"),
                        "author_name": author.get("name"),
                        "author_followers": author_metrics.get("followers_count", 0),
                        "author_description": author.get("description"),
                        "likes": tweet_metrics.get("like_count", 0),
                        "retweets": tweet_metrics.get("retweet_count", 0),
                        "url": f"https://x.com/i/web/status/{tweet['id']}",
                    }
                )
            return {"success": True, "tweets": tweets, "count": len(tweets)}
        return {"success": False, "error": f"{response.status_code}: {response.text}"}

    def discover_users(
        self, query: str, limit: int = 20, min_followers: int = 0
    ) -> dict:
        """
        Discover users by searching tweets and extracting unique authors.

        Args:
            query: Search query to find relevant tweets
            limit: Maximum number of tweets to search
            min_followers: Minimum audience-size filter

        Returns:
            dict with 'success', 'users' list or 'error'
        """
        result = self.search_tweets(query, limit=limit, include_users=True)
        if not result.get("success"):
            return result

        seen_ids = set()
        users = []
        for tweet in result.get("tweets", []):
            author_id = tweet.get("author_id")
            if author_id and author_id not in seen_ids:
                if tweet.get("author_followers", 0) >= min_followers:
                    seen_ids.add(author_id)
                    users.append(
                        {
                            "id": author_id,
                            "username": tweet.get("author_username"),
                            "name": tweet.get("author_name"),
                            "followers": tweet.get("author_followers", 0),
                            "description": tweet.get("author_description"),
                            "sample_tweet": tweet.get("text"),
                        }
                    )

        users.sort(key=lambda u: u.get("followers", 0), reverse=True)
        return {"success": True, "users": users, "count": len(users)}

    def grow(
        self,
        query: str,
        limit: int = 10,
        min_followers: int = 0,
        dry_run: bool = True,
    ) -> dict:
        """
        Discover and follow users matching a search query.

        Args:
            query: Search query to find relevant users
            limit: Maximum number of users to follow
            min_followers: Minimum audience-size filter
            dry_run: If True, only discover users without following

        Returns:
            dict with 'success', 'discovered', 'followed' lists or 'error'
        """
        discovered = self.discover_users(
            query, limit=limit * 2, min_followers=min_followers
        )
        if not discovered.get("success"):
            return discovered

        users = discovered.get("users", [])[:limit]
        followed = []
        skipped = []

        rate_limited = False
        if not dry_run:
            for user in users:
                if rate_limited:
                    user["error"] = "Rate limited - stopped"
                    skipped.append(user)
                    continue

                result = self.follow(user["id"])
                if result.get("success"):
                    followed.append(user)
                elif "429" in str(result.get("error", "")):
                    rate_limited = True
                    user["error"] = "Rate limited"
                    skipped.append(user)
                else:
                    user["error"] = result.get("error")
                    skipped.append(user)

        return {
            "success": True,
            "dry_run": dry_run,
            "discovered": users,
            "discovered_count": len(users),
            "followed": followed,
            "followed_count": len(followed),
            "skipped": skipped,
            "rate_limited": rate_limited,
        }
