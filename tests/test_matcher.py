"""
Unit tests for the SemanticMatcher and DomainLoader.
Run with: pytest tests/
"""

import io
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest
import pandas as pd

from app.core.domain import DomainLoader
from app.core.matcher import SemanticMatcher


# ── SemanticMatcher ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def matcher():
    """Real matcher with a tiny domain for fast tests."""
    descriptions = [
        "computer science engineer",
        "medical doctor",
        "civil construction worker",
    ]
    return SemanticMatcher(descriptions)


def test_find_best_match_returns_index(matcher):
    """Test that find_best_match returns a valid index and score."""
    idx, score = matcher.find_best_match("software developer", threshold=0.3)
    assert idx is not None
    assert 0.0 <= score <= 1.0


def test_find_best_match_below_threshold(matcher):
    """Test that find_best_match returns None
    if no match meets the threshold."""
    idx, score = matcher.find_best_match("completely unrelated gibberish zzz",
                                         threshold=0.99)
    assert idx is None
    assert score >= 0.0


def test_find_best_match_empty_string(matcher):
    """Test that find_best_match returns None for an empty input string."""
    idx, score = matcher.find_best_match("", threshold=0.75)
    assert idx is None
    assert score == 0.0


def test_find_best_match_non_string(matcher):
    """Test that find_best_match returns None for a non-string input."""
    idx, score = matcher.find_best_match(None, threshold=0.75)  # type: ignore
    assert idx is None


# ── DomainLoader ────────────────────────────────────────────────────────

def test_domain_loader_csv(tmp_path):
    """Test that DomainLoader can load descriptions from a CSV file."""

    csv_content = "Engineer,A1,C1,Senior Engineer\
\nDoctor,A2,C2,Medical Doctor\n"
    p = tmp_path / "domain.csv"
    p.write_text(csv_content)

    domain = DomainLoader(p)
    assert len(domain.descriptions) == 2
    assert domain.descriptions[0] == "Engineer"


def test_domain_loader_unsupported_format(tmp_path):
    """Test that DomainLoader raises an error for unsupported file formats."""

    p = tmp_path / "domain.json"
    p.write_text("{}")
    with pytest.raises(ValueError, match="Unsupported domain file format"):
        DomainLoader(p)
