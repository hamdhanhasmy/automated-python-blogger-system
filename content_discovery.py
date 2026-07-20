import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ArticleItem:
    title: str
    url: str
    content: str
    published: str = ""
    source: str = ""

class ContentDiscoverer:
    """Discovers and parses articles from RSS feeds and target URLs."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def fetch_articles_from_feed(self, feed_url: str) -> List[ArticleItem]:
        """Parses an RSS feed and returns structured ArticleItems."""
        logger.info(f"Parsing RSS feed: {feed_url}")
        articles: List[ArticleItem] = []
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo:
                logger.warning(f"Warning/bozo exception when parsing feed {feed_url}: {feed.bozo_exception}")

            if not feed.entries:
                logger.info(f"No entries found in feed: {feed_url}")
                return articles

            for entry in feed.entries:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                published = getattr(entry, "published", getattr(entry, "updated", ""))

                if not title or not link:
                    continue

                # Extract content or summary
                content = ""
                if hasattr(entry, "content"):
                    content = " ".join([c.value for c in entry.content if hasattr(c, "value")])
                elif hasattr(entry, "summary"):
                    content = entry.summary
                elif hasattr(entry, "description"):
                    content = entry.description

                # Clean basic HTML tags from RSS summary to see text length
                clean_text = self._clean_html(content)

                # If summary is too short (< 200 chars), attempt full page scrape
                if len(clean_text) < 200:
                    logger.info(f"Summary short for '{title}'. Fetching full article content...")
                    scraped_text = self.scrape_article_body(link)
                    if scraped_text and len(scraped_text) > len(clean_text):
                        clean_text = scraped_text

                if clean_text:
                    articles.append(
                        ArticleItem(
                            title=title,
                            url=link,
                            content=clean_text,
                            published=str(published),
                            source=getattr(feed.feed, "title", feed_url)
                        )
                    )

        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}", exc_info=True)

        return articles

    def scrape_article_body(self, url: str) -> str:
        """Scrapes and extracts main text content from a web page URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove noise elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
                element.decompose()

            # Find primary content tags
            paragraphs = soup.find_all("p")
            text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]

            full_text = "\n\n".join(text_blocks)
            return full_text.strip()

        except Exception as e:
            logger.warning(f"Failed to scrape URL {url}: {e}")
            return ""

    def _clean_html(self, html_content: str) -> str:
        """Strips HTML tags and extracts plain text."""
        if not html_content:
            return ""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            return html_content

    def discover_new_articles(
        self, feed_urls: List[str], state_manager, max_articles: int = 1
    ) -> List[ArticleItem]:
        """Discovers unprocessed articles across multiple feed URLs."""
        discovered: List[ArticleItem] = []
        for feed_url in feed_urls:
            if len(discovered) >= max_articles:
                break
            articles = self.fetch_articles_from_feed(feed_url)
            for article in articles:
                if not state_manager.is_processed(article.url):
                    discovered.append(article)
                    if len(discovered) >= max_articles:
                        break

        logger.info(f"Discovered {len(discovered)} new unprocessed article(s).")
        return discovered
