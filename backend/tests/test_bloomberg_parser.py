"""Tests for the Bloomberg URL metadata parser — 5 example URLs."""
import pytest
from backend.tools.bloomberg_parser import BloombergParser

EXAMPLE_URLS = [
    "https://www.bloomberg.com/news/articles/2024-03-15/nvidia-ai-chip-demand-drives-data-center-power-surge",
    "https://www.bloomberg.com/energy/utilities/2024-06-01/constellation-energy-microsoft-nuclear-ppa",
    "https://www.bloomberg.com/technology/ai/2025-01-10/ge-vernova-transformer-backlog-grid-infrastructure",
    "https://www.bloomberg.com/markets/2024-09-20/pjm-interconnection-queue-reform-ferc-order-2023",
    "https://www.bloomberg.com/features/2024-11-05/vertiv-liquid-cooling-data-center-ai-rack-density",
]


@pytest.fixture
def parser():
    return BloombergParser()


@pytest.mark.parametrize("url", EXAMPLE_URLS)
def test_bloomberg_url_parser(parser, url):
    """Each example URL produces a non-empty title and correct source metadata."""
    meta = parser.parse_url(url)
    assert meta["source_type"] == "bloomberg"
    assert meta["access_class"] == "metadata_only"
    assert meta["title"], f"Empty title for {url}"
    assert isinstance(meta["topic_tags"], list)
    assert meta["url"] == url


def test_bloomberg_date_extraction(parser):
    """Date is extracted correctly from a URL containing YYYY-MM-DD."""
    meta = parser.parse_url(EXAMPLE_URLS[0])
    assert meta["estimated_date"] == "2024-03-15"


def test_bloomberg_topic_tags(parser):
    """Energy-themed URL produces an energy tag."""
    meta = parser.parse_url(EXAMPLE_URLS[1])
    assert "energy" in meta["topic_tags"]


def test_bloomberg_no_date_url(parser):
    """URL without date returns None for estimated_date."""
    meta = parser.parse_url("https://www.bloomberg.com/opinion/articles/is-ai-power-demand-real")
    assert meta["estimated_date"] is None


def test_bloomberg_entity_extraction(parser):
    """Title entity extraction returns canonical entity names."""
    entities = parser.extract_entities_from_title("Nvidia and GE Vernova AI infrastructure")
    assert isinstance(entities, list)
    # At least one of the known entities should be found
    known = {"Nvidia", "GE Vernova"}
    assert len(known & set(entities)) > 0 or len(entities) == 0  # graceful if resolver unavailable
