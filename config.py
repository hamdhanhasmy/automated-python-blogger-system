import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Gemini API Settings
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")

    # Blogger API Settings
    blogger_blog_id: str = Field(default="", env="BLOGGER_BLOG_ID")
    blogger_client_id: str = Field(default="", env="BLOGGER_CLIENT_ID")
    blogger_client_secret: str = Field(default="", env="BLOGGER_CLIENT_SECRET")
    blogger_refresh_token: str = Field(default="", env="BLOGGER_REFRESH_TOKEN")

    # Content Discovery Settings
    rss_feeds_raw: str = Field(
        default="https://news.google.com/rss,https://feeds.bbci.co.uk/news/technology/rss.xml",
        env="RSS_FEEDS"
    )
    max_articles_per_run: int = Field(default=1, env="MAX_ARTICLES_PER_RUN")

    # Image Generator Settings
    image_width: int = Field(default=1024, env="IMAGE_WIDTH")
    image_height: int = Field(default=576, env="IMAGE_HEIGHT")

    # SEO Category Settings
    allowed_categories_raw: str = Field(
        default="Technology, World News, Business & Economy, Science & Innovation, Politics, Entertainment, Health & Lifestyle",
        env="ALLOWED_CATEGORIES"
    )

    # System Settings
    state_file_path: str = Field(default="processed_articles.json")

    @property
    def rss_feeds(self) -> List[str]:
        """Returns parsed list of RSS feeds from raw comma-separated string."""
        if not self.rss_feeds_raw:
            return []
        return [url.strip() for url in self.rss_feeds_raw.split(",") if url.strip()]

    @property
    def allowed_categories(self) -> List[str]:
        """Returns list of allowed master categories."""
        if not self.allowed_categories_raw:
            return ["Technology", "World News", "Business & Economy", "Politics"]
        return [c.strip() for c in self.allowed_categories_raw.split(",") if c.strip()]

settings = Settings()
