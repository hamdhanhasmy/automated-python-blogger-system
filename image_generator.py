import urllib.parse
import requests
import logging
import random
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Generates featured AI images using Pollinations.ai free API."""

    POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/"

    def __init__(self, default_width: int = 1024, default_height: int = 576):
        self.default_width = default_width
        self.default_height = default_height

    def generate_image_url(self, prompt: str, width: Optional[int] = None, height: Optional[int] = None) -> str:
        """Generates a clean, direct Pollinations.ai image URL for a given prompt."""
        w = width or self.default_width
        h = height or self.default_height
        seed = random.randint(1000, 999999)
        
        # Clean prompt for URL safety
        clean_prompt = prompt.strip()
        encoded_prompt = urllib.parse.quote(clean_prompt)
        
        url = f"{self.POLLINATIONS_BASE_URL}{encoded_prompt}?width={w}&height={h}&nologo=true&seed={seed}&model=flux"
        logger.info(f"Generated Pollinations AI Image URL: {url}")
        return url

    def fetch_image_bytes(self, image_url: str, timeout: int = 20) -> Optional[bytes]:
        """Fetches binary bytes of the image to verify availability or for storage."""
        try:
            response = requests.get(image_url, timeout=timeout)
            response.raise_for_status()
            logger.info("Successfully fetched image bytes from Pollinations API.")
            return response.content
        except Exception as e:
            logger.error(f"Failed to fetch image bytes from {image_url}: {e}")
            return None

    def create_featured_image_html(self, prompt: str, alt_title: str) -> str:
        """Generates the featured image URL and returns HTML <img> tag snippet."""
        image_url = self.generate_image_url(prompt)
        alt_escaped = alt_title.replace('"', '&quot;')
        img_tag = (
            f'<div style="text-align: center; margin-bottom: 20px;">'
            f'<img src="{image_url}" alt="{alt_escaped}" '
            f'style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />'
            f'</div>'
        )
        return img_tag
