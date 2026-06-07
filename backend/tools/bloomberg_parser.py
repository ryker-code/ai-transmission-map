"""
Bloomberg URL metadata extractor.

Extracts title, topic tags, and date from bloomberg.com URLs using only
URL path parsing — no HTTP requests, no article content.
Respects bloomberg.com ToS: stores only URL metadata and analyst paraphrases.
"""
import logging
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Bloomberg URL path segments that map to topic tags
SEGMENT_TAG_MAP = {
    "technology": "technology",
    "tech": "technology",
    "energy": "energy",
    "utilities": "energy",
    "power": "energy",
    "markets": "markets",
    "finance": "finance",
    "deals": "finance",
    "infrastructure": "infrastructure",
    "data-center": "infrastructure",
    "artificial-intelligence": "ai",
    "ai": "ai",
    "semiconductors": "semiconductors",
    "chips": "semiconductors",
    "news": "news",
    "opinion": "opinion",
    "graphics": "data",
    "features": "analysis",
}

# Regex to extract YYYY-MM-DD from URL paths
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


class BloombergParser:
    """Lightweight Bloomberg URL metadata extractor."""

    def parse_url(self, url: str) -> dict:
        """
        Extract metadata from a bloomberg.com URL.
        Returns a dict with title, topic_tags, source_type, estimated_date, access_class.
        """
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        segments = [s for s in path.split("/") if s]

        # Extract date if present
        estimated_date: Optional[str] = None
        date_match = DATE_RE.search(path)
        if date_match:
            try:
                dt = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                estimated_date = dt.date().isoformat()
            except ValueError:
                pass

        # Infer topic tags from path segments
        topic_tags = []
        for seg in segments:
            tag = SEGMENT_TAG_MAP.get(seg.lower())
            if tag and tag not in topic_tags:
                topic_tags.append(tag)

        # Build title from the last meaningful path segment (the article slug)
        title_slug = ""
        for seg in reversed(segments):
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", seg) and len(seg) > 5:
                title_slug = seg
                break
        # Strip trailing hash fragments and convert hyphens
        title_slug = re.sub(r"-\d+$", "", title_slug)  # remove trailing numeric IDs
        title = title_slug.replace("-", " ").title() if title_slug else "Bloomberg Article"

        return {
            "title": title,
            "topic_tags": topic_tags or ["news"],
            "source_type": "bloomberg",
            "estimated_date": estimated_date,
            "access_class": "metadata_only",
            "url": url,
        }

    def extract_entities_from_title(self, title: str) -> list[str]:
        """
        Resolve entity names mentioned in a Bloomberg article title.
        Returns canonical entity names that match with high confidence (substring match).
        """
        try:
            from backend.agents.resolver import get_resolver
            resolver = get_resolver()
            words = title.replace(",", "").replace(".", "").split()
            found = []

            # Try multi-word phrases (up to 4 words) and single words
            for window in range(4, 0, -1):
                for i in range(len(words) - window + 1):
                    phrase = " ".join(words[i:i + window])
                    entity = resolver.resolve(phrase)
                    if entity and entity["canonical_name"] not in found:
                        found.append(entity["canonical_name"])

            return found
        except Exception as e:
            logger.warning(f"Entity extraction from title failed: {e}")
            return []


# Module-level singleton
_parser: Optional[BloombergParser] = None


def get_parser() -> BloombergParser:
    global _parser
    if _parser is None:
        _parser = BloombergParser()
    return _parser
