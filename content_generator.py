import json
import logging
import re
import time
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Generates SEO-optimized HTML blog content using Google Gemini API."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        if not api_key or api_key.strip() == "" or "your_gemini_api_key_here" in api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing or invalid in your .env file!\n"
                "Please get a free Gemini API key from https://aistudio.google.com/app/apikey "
                "and paste it into your .env file as GEMINI_API_KEY=AIzaSy..."
            )
        self.api_key = api_key.strip()
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def generate_blog_post(
        self,
        source_title: str,
        source_content: str,
        allowed_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generates an engaging, SEO-optimized HTML blog post based on source content."""
        logger.info(f"Generating AI article for source title: '{source_title}'")

        from config import settings
        categories_list = allowed_categories or settings.allowed_categories
        categories_str = ", ".join([f"'{c}'" for c in categories_list])

        system_instruction = (
            "You are an expert tech journalist and SEO blogger. Your job is to rewrite "
            "source news into an engaging, unique, high-quality blog post.\n\n"
            "STRICT SEO RULES:\n"
            "1. Do NOT copy sentences verbatim. Rewrite thoroughly in a fresh, professional voice.\n"
            "2. The article body MUST be clean HTML using ONLY <p>, <h2>, <h3>, <ul>, <li>, <b>, and <i> tags.\n"
            "3. Do NOT wrap output in <html>, <body>, or ```html markdown blocks in the body field.\n"
            "4. Structure the article with clear H2 headings, short paragraphs, bullet points, and key takeaways.\n"
            "5. CATEGORY & LABELS SYSTEM (CRITICAL FOR SEO):\n"
            f"   - The FIRST label in the 'labels' array MUST be chosen strictly from this Master Categories list: [{categories_str}].\n"
            "   - You may include 1-2 secondary broad topic tags (e.g. 'Artificial Intelligence', 'Global News', 'Geopolitics').\n"
            "   - Total labels MUST NOT exceed 3 labels.\n"
            "   - Do NOT use specific person names, typos, or micro-niche phrases as labels.\n"
            "6. Provide a JSON response with key fields: 'title', 'html_content', 'labels', and 'image_prompt'.\n"
            "   - 'title': A compelling, click-worthy SEO title.\n"
            "   - 'html_content': The full HTML body of the article.\n"
            "   - 'labels': Array of 2-3 standardized category tags (strings).\n"
            "   - 'image_prompt': A detailed description prompt to generate a realistic or modern 16:9 featured cover image for this post."
        )

        user_prompt = (
            f"SOURCE ARTICLE TITLE:\n{source_title}\n\n"
            f"SOURCE ARTICLE CONTENT:\n{source_content[:4000]}\n\n"
            "Generate a complete, comprehensive blog post JSON following the system rules."
        )

        for attempt in range(1, 3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.7,
                    ),
                )

                response_text = response.text.strip()
                result = self._parse_response(response_text, categories_list)
                logger.info(f"Successfully generated article: '{result.get('title')}'")
                return result

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt == 1:
                        wait_seconds = 25
                        logger.warning(f"Gemini API rate limit reached (429 RESOURCE_EXHAUSTED). Waiting {wait_seconds} seconds before retrying...")
                        time.sleep(wait_seconds)
                        continue

                # If primary model fails on non-rate-limit or 2nd attempt, attempt fallback model
                fallback_model = "gemini-2.5-flash" if self.model_name != "gemini-2.5-flash" else "gemini-2.0-flash"
                if self.model_name != fallback_model:
                    logger.warning(f"Primary model '{self.model_name}' failed ({e}). Retrying with fallback model '{fallback_model}'...")
                    try:
                        response = self.client.models.generate_content(
                            model=fallback_model,
                            contents=user_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                response_mime_type="application/json",
                                temperature=0.7,
                            ),
                        )
                        response_text = response.text.strip()
                        result = self._parse_response(response_text, categories_list)
                        logger.info(f"Successfully generated article using fallback model '{fallback_model}': '{result.get('title')}'")
                        return result
                    except Exception as fallback_err:
                        logger.error(f"Fallback model '{fallback_model}' failed as well: {fallback_err}")
                        raise fallback_err
                logger.error(f"Error generating content via Gemini API: {e}", exc_info=True)
                raise e

    def _parse_response(self, text: str, allowed_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Parses LLM JSON response safely with fallbacks and normalizes labels."""
        # Strip code blocks if present
        clean_json = re.sub(r"^```(?:json)?\n|\n```$", "", text.strip(), flags=re.MULTILINE)
        default_category = allowed_categories[0] if allowed_categories else "Technology"

        try:
            data = json.loads(clean_json)
            # Validate essential fields
            if "title" not in data or "html_content" not in data:
                raise ValueError("Missing title or html_content in LLM response.")

            # Sanitize and format labels for clean Blogger SEO structure
            raw_labels = data.get("labels", [])
            if not isinstance(raw_labels, list) or not raw_labels:
                raw_labels = [default_category]

            cleaned_labels = []
            for label in raw_labels:
                if isinstance(label, str):
                    clean_l = label.strip().title()
                    if clean_l and clean_l not in cleaned_labels:
                        cleaned_labels.append(clean_l)

            # Ensure primary master category is present
            if allowed_categories:
                has_master = any(l.lower() in [ac.lower() for ac in allowed_categories] for l in cleaned_labels)
                if not has_master:
                    cleaned_labels.insert(0, default_category)

            # Limit to max 3 clean labels
            data["labels"] = cleaned_labels[:3]

            if "image_prompt" not in data:
                data["image_prompt"] = f"Modern digital art conceptualizing {data['title']}"

            return data

        except Exception as err:
            logger.warning(f"Failed to parse JSON response directly: {err}. Attempting fallback structure.")
            return {
                "title": "Latest Technology Update",
                "html_content": f"<p>{text}</p>",
                "labels": [default_category, "News"],
                "image_prompt": "Futuristic technology concept header background"
            }
