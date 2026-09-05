"""
Scoring engine for tender relevance evaluation.

Evaluates keyword and category matches to determine whether a tender record
is relevant to the configured company filters. All functions are pure Python
with no ORM dependencies. Keyword matching logic is isolated here to avoid
duplication across callers.
"""
import logging
from dataclasses import dataclass, field

_logger = logging.getLogger(__name__)

try:
    from thefuzz import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# Minimum fuzzy partial_ratio score to consider a keyword a positive match.
# 90 was chosen to allow minor typos and plurals while avoiding false positives.
_FUZZY_THRESHOLD = 90


@dataclass
class ScoringResult:
    """Encapsulates the result of a single tender scoring evaluation.

    Attributes:
        is_match (bool): Whether the tender passed all active filters.
        score (int): Accumulated relevance score (0-3, capped externally).
        reason_parts (list[str]): Individual match explanations, joined for display.
    """
    is_match: bool = False
    score: int = 0
    reason_parts: list = field(default_factory=list)

    @property
    def reason(self) -> str:
        """Returns the full match reason as a single pipe-separated string."""
        return " | ".join(self.reason_parts) if self.reason_parts else ""


def match_keyword(text: str, keyword: str) -> bool:
    """
    Checks whether a keyword matches a given text string.

    Uses fuzzy partial_ratio matching if thefuzz is available, falling back
    to exact substring search otherwise.

    Args:
        text (str): Lowercased search text to match against.
        keyword (str): Lowercased keyword to search for.

    Returns:
        bool: True if the keyword is considered a match.
    """
    if FUZZY_AVAILABLE:
        return fuzz.partial_ratio(keyword, text) >= _FUZZY_THRESHOLD
    return keyword in text


def find_matching_keyword(text: str, keywords) -> str | None:
    """
    Returns the first keyword that matches the given text, or None.

    Args:
        text (str): Search text (will be lowercased internally).
        keywords: Iterable of objects with a .keyword string attribute.

    Returns:
        str | None: The matched keyword string, or None if no match found.
    """
    text_lower = text.lower()
    for kw_record in keywords:
        if kw_record.keyword and match_keyword(text_lower, kw_record.keyword.lower()):
            return kw_record.keyword
    return None


def score_tender(
    search_text: str,
    category_ids: list,
    filter_category_ids: set,
    active_keywords,
    location_mode: str,
    location_match: bool,
    agency_mode: str,
    agency_is_favorite: bool,
) -> ScoringResult:
    """
    Evaluates a tender's relevance against all configured company filters.

    Scoring rules:
    - Category match (primary): +2 points.
    - Keyword match (primary): +1 point.
    - Preferred location (additive mode): +1 point.
    - Favorite agency (additive mode): +1 point.
    - Exclusionary filter failure: resets score to 0, is_match = False.

    A tender must score at least 1 point from primary filters (category or
    keyword) to be considered a match. Secondary filters (location, agency)
    can only boost or exclude — not create an initial match.

    Args:
        search_text (str): Combined name + description text for keyword matching.
        category_ids (list): ORM IDs of UNSPSC categories found in the tender.
        filter_category_ids (set): ORM IDs of UNSPSC categories in company config.
        active_keywords: Queryset of active mercadopublico.keyword records.
        location_mode (str): 'desactivado' | 'aditivo' | 'excluyente'.
        location_match (bool): True if the tender location matches configured locations.
        agency_mode (str): 'desactivado' | 'aditivo' | 'excluyente'.
        agency_is_favorite (bool): True if the buyer agency is marked as favorite.

    Returns:
        ScoringResult: Evaluation result with is_match, score, and reason.
    """
    has_filters = bool(active_keywords) or bool(filter_category_ids)
    result = ScoringResult()

    if not has_filters:
        result.is_match = True
        result.score = 1
        result.reason_parts = ["No filters configured, accepted by default."]
        return result

    # --- Primary filters: category and keyword (determine base inclusion) ---
    matched_cat_id = next(
        (c for c in category_ids if c in filter_category_ids), None
    )
    if matched_cat_id is not None:
        result.score += 2
        result.reason_parts.append(f"Category match (id={matched_cat_id})")

    matched_kw = find_matching_keyword(search_text, active_keywords)
    if matched_kw:
        result.score += 1
        result.reason_parts.append(f"Keyword: {matched_kw}")

    if result.score == 0:
        result.reason_parts = ["No keyword or category match."]
        return result  # is_match stays False

    result.is_match = True

    # --- Secondary filters: applied only when the primary check passed ---
    if location_mode == "excluyente" and not location_match:
        result.is_match = False
        result.score = 0
        result.reason_parts = ["EXCLUDED: Location does not match."]
        return result
    if location_mode == "aditivo" and location_match:
        result.score += 1
        result.reason_parts.append("Preferred location.")

    if agency_mode == "excluyente" and not agency_is_favorite:
        result.is_match = False
        result.score = 0
        result.reason_parts = ["EXCLUDED: Agency not in favorites."]
        return result
    if agency_mode == "aditivo" and agency_is_favorite:
        result.score += 1
        result.reason_parts.append("Favorite agency.")

    return result


def score_item(item_text: str, active_keywords) -> bool:
    """
    Evaluates whether a single tender item matches active keyword filters.

    Used to annotate individual line items with an is_match flag for UI display.

    Args:
        item_text (str): Combined name + description of the item (lowercased).
        active_keywords: Iterable of keyword records with a .keyword attribute.

    Returns:
        bool: True if the item matches any active keyword.
    """
    matched_kw = find_matching_keyword(item_text, active_keywords)
    return matched_kw is not None
