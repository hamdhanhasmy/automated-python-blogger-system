import argparse
import logging
import sys
from typing import List

from config import settings
from state_manager import StateManager
from content_discovery import ContentDiscoverer, ArticleItem
from content_generator import ContentGenerator
from image_generator import ImageGenerator
from blogger_publisher import BloggerPublisher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AutoBlogger")

def run_pipeline(dry_run: bool = False, max_articles: int = 1, feed_urls: List[str] = None, is_draft: bool = False):
    """Executes the automated blogging pipeline."""
    logger.info("=== Starting AutoBlogger Pipeline Run ===")
    
    # 1. Initialize State Manager
    state_mgr = StateManager(settings.state_file_path)

    # 2. Determine RSS Feed URLs
    feeds = feed_urls if feed_urls else settings.rss_feeds
    if not feeds:
        logger.error("No RSS feeds configured! Please check your RSS_FEEDS environment variable.")
        return

    # 3. Discover Unprocessed Articles
    discoverer = ContentDiscoverer()
    articles: List[ArticleItem] = discoverer.discover_new_articles(
        feed_urls=feeds,
        state_manager=state_mgr,
        max_articles=max_articles
    )

    if not articles:
        logger.info("No new unprocessed articles found in feeds. Exiting pipeline.")
        return

    # 4. Initialize AI Generators
    try:
        generator = ContentGenerator(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
    except Exception as e:
        logger.error(f"Initialization of ContentGenerator failed: {e}")
        if not dry_run:
            sys.exit(1)
        generator = None

    image_gen = ImageGenerator(
        default_width=settings.image_width,
        default_height=settings.image_height
    )

    # 5. Process Articles
    processed_count = 0
    for idx, article in enumerate(articles, start=1):
        logger.info(f"\n--- Processing Article [{idx}/{len(articles)}]: {article.title} ---")
        logger.info(f"Source URL: {article.url}")

        try:
            # Step A: AI Content Rewriting
            if generator:
                ai_result = generator.generate_blog_post(
                    source_title=article.title,
                    source_content=article.content
                )
            else:
                ai_result = {
                    "title": f"[DRY RUN] {article.title}",
                    "html_content": f"<p>{article.content[:500]}</p>",
                    "labels": ["Tech", "News"],
                    "image_prompt": f"Digital concept art for {article.title}"
                }

            post_title = ai_result.get("title", article.title)
            body_html = ai_result.get("html_content", "")
            labels = ai_result.get("labels", [])
            image_prompt = ai_result.get("image_prompt", post_title)

            # Step B: Generate Featured AI Image snippet
            featured_img_html = image_gen.create_featured_image_html(
                prompt=image_prompt,
                alt_title=post_title
            )

            # Combine featured image at top of post HTML
            final_content_html = f"{featured_img_html}\n{body_html}"

            # Step C: Publish or Dry-Run
            if dry_run:
                logger.info("[DRY RUN MODE ENABLED] - Skipping Blogger API publish.")
                logger.info(f"Generated Title: {post_title}")
                logger.info(f"Labels: {labels}")
                logger.info(f"HTML Preview:\n{final_content_html[:300]}...\n")
                blog_post_id = "dry-run-id"
            else:
                publisher = BloggerPublisher(
                    blog_id=settings.blogger_blog_id,
                    client_id=settings.blogger_client_id,
                    client_secret=settings.blogger_client_secret,
                    refresh_token=settings.blogger_refresh_token
                )
                published_response = publisher.publish_post(
                    title=post_title,
                    content_html=final_content_html,
                    labels=labels,
                    is_draft=is_draft
                )
                blog_post_id = published_response.get("id", "published")

            # Step D: Mark state as processed
            state_mgr.mark_processed(
                article_id=article.url,
                title=post_title,
                blog_post_id=blog_post_id
            )
            processed_count += 1

        except Exception as e:
            logger.error(f"Failed to process article '{article.title}': {e}", exc_info=True)
            continue

    logger.info(f"=== Pipeline completed successfully. Processed {processed_count} article(s). ===")

def main():
    parser = argparse.ArgumentParser(description="AutoBlogger: AI-powered automated blogging system.")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline without publishing to Blogger.")
    parser.add_argument("--max-articles", type=int, default=settings.max_articles_per_run, help="Max articles to process in run.")
    parser.add_argument("--rss-feed", type=str, help="Comma-separated RSS feed URLs to parse.")
    parser.add_argument("--draft", action="store_true", help="Publish posts as draft on Blogger.")

    args = parser.parse_args()

    feed_urls = [url.strip() for url in args.rss_feed.split(",")] if args.rss_feed else None

    run_pipeline(
        dry_run=args.dry_run,
        max_articles=args.max_articles,
        feed_urls=feed_urls,
        is_draft=args.draft
    )

if __name__ == "__main__":
    main()
