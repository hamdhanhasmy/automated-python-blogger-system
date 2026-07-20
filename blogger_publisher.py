import logging
from typing import Dict, Any, List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class BloggerPublisher:
    """Publishes posts to Blogger.com via Blogger API v3 using OAuth 2.0 credentials."""

    BLOGGER_SCOPES = ["https://www.googleapis.com/auth/blogger"]
    TOKEN_URI = "https://oauth2.googleapis.com/token"

    def __init__(self, blog_id: str, client_id: str, client_secret: str, refresh_token: str):
        if not blog_id or not client_id or not client_secret or not refresh_token:
            raise ValueError("All Blogger OAuth credentials (blog_id, client_id, client_secret, refresh_token) are required.")

        self.blog_id = blog_id
        self.credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=self.TOKEN_URI,
            client_id=client_id,
            client_secret=client_secret,
            scopes=self.BLOGGER_SCOPES
        )
        self.service = build("blogger", "v3", credentials=self.credentials)

    def publish_post(
        self,
        title: str,
        content_html: str,
        labels: Optional[List[str]] = None,
        is_draft: bool = False
    ) -> Dict[str, Any]:
        """Publishes a new blog post to the designated Blogger blog."""
        logger.info(f"Publishing post '{title}' to Blogger ID {self.blog_id} (is_draft={is_draft})...")

        post_body = {
            "kind": "blogger#post",
            "blog": {"id": self.blog_id},
            "title": title,
            "content": content_html,
        }

        if labels:
            post_body["labels"] = labels

        try:
            posts_service = self.service.posts()
            request = posts_service.insert(
                blogId=self.blog_id,
                body=post_body,
                isDraft=is_draft
            )
            response = request.execute()
            
            post_url = response.get("url", "")
            post_id = response.get("id", "")
            logger.info(f"Successfully published post! Post ID: {post_id}, URL: {post_url}")
            return response

        except HttpError as e:
            logger.error(f"HTTP error occurred while publishing to Blogger: {e}")
            if e.resp.status == 403:
                logger.warning("\n" + "="*60)
                logger.warning(f"PERMISSION DENIED ERROR (403 for Blog ID '{self.blog_id}')")
                logger.warning("The Google account used during authentication does not have permission to publish to this blog.")
                logger.warning("FIX:")
                logger.warning("1. Re-run 'python get_refresh_token.py' in your terminal.")
                logger.warning("2. In the browser popup, make sure to log in with the exact Google Account that owns or manages this Blogger blog.")
                logger.warning("="*60 + "\n")
            elif e.resp.status == 404:
                logger.warning("\n" + "="*60)
                logger.warning(f"BLOG ID NOT FOUND ERROR (404 for Blog ID '{self.blog_id}')")
                logger.warning("Attempting to list available blogs for your Google account...")
                try:
                    user_blogs = self.service.blogs().listByUser(userId="self").execute()
                    items = user_blogs.get("items", [])
                    if items:
                        logger.info("Found the following blog(s) under your account:")
                        for b in items:
                            logger.info(f"  - Blog Name: '{b.get('name')}' | Blog ID: {b.get('id')} | URL: {b.get('url')}")
                        logger.info(f"Please update BLOGGER_BLOG_ID in your .env file with one of the Blog IDs listed above!")
                    else:
                        logger.warning("No blogs found for this Google account. Make sure your account owns or has access to a blog on Blogger.com.")
                except Exception as list_err:
                    logger.error(f"Failed to retrieve user blogs list: {list_err}")
                logger.warning("="*60 + "\n")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error while publishing to Blogger: {e}", exc_info=True)
            raise e
