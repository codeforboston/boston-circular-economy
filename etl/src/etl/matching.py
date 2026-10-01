"""Location matching and normalization for deduplication across data sources."""

import math
from enum import Enum

import phonenumbers
from cleanco import basename
from contracts.domain import NormalizedLocation
from rapidfuzz import fuzz
from scourgify.normalize import normalize_addr_str

# Tuning constants
MAX_MATCH_DISTANCE_M = 150  # meters
NAME_SIMILARITY_THRESHOLD = 90  # token_set_ratio, 0-100
STREET_SIMILARITY_THRESHOLD = 90  # token_set_ratio, 0-100


class MatchTier(Enum):
    """Match tiers in priority order. First tier that fires wins."""

    PHONE = 1
    ADDRESS = 2
    NAME = 3


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance in meters between two lat/lon points."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def normalize_phones(raw_phone: str | None) -> set[str]:
    """
    Parse and normalize phone numbers to E.164 format.

    Handles semicolon-separated multi-value OSM tags, extensions, vanity numbers,
    and malformed formatting. Returns a set of valid E.164 strings.

    Args:
        raw_phone: Raw phone string, possibly semicolon-separated, or None.

    Returns:
        Set of normalized E.164 phone numbers (e.g. {"+16176283618"}).
        Empty set if input is None or contains no valid numbers.
    """
    if not raw_phone:
        return set()

    parts = [p.strip() for p in raw_phone.split(";")]
    valid = set()

    for part in parts:
        try:
            num = phonenumbers.parse(part, "US")
            if phonenumbers.is_valid_number(num):
                e164 = phonenumbers.format_number(
                    num, phonenumbers.PhoneNumberFormat.E164
                )
                valid.add(e164)
        except phonenumbers.NumberParseException:
            # Unparseable or invalid, skip it
            pass

    return valid


def normalize_street(raw_street: str | None) -> tuple[str, str | None] | None:
    """
    Normalize a street line to canonical USPS form, separating unit designators.

    Handles suffix abbreviations (Street -> ST, Avenue -> AVE), directionals
    (North -> N), and unit designators (Ste 405 -> STE 405 in address_line_2).
    Returns uppercase canonical form.

    Unit handling rationale:
    - Units are extracted to prevent false positives (merging different suites
      in the same building)
    - If both records have units and they differ, the ADDRESS tier rejects the match
    - If one or both records lack unit info, the match is accepted (can't rule it out)
    - This prevents the dangerous case (merging Ste 405 with Ste 200) while
      accepting the uncertain case (Ste 405 with no unit info)

    Args:
        raw_street: Raw street line, e.g. "230 Elm Street" or "119 Braintree St Ste 405".

    Returns:
        Tuple of (street_line, unit_id) where street_line is the normalized street
        (e.g. "230 ELM ST") and unit_id is the extracted unit identifier if present
        (e.g. "15" or "405" or "15A"), or None if no unit.
        Returns None if input is None or normalization fails.
    """
    if not raw_street:
        return None

    try:
        normalized = normalize_addr_str(raw_street)
        # normalize_addr_str returns an OrderedDict with address_line_1, address_line_2, etc.
        line1 = normalized.get("address_line_1")
        if not line1:
            return None
        line2 = normalized.get("address_line_2")

        # Extract unit identifier from line2 if present
        unit_id = extract_unit_identifier(line2) if line2 else None

        return (line1, unit_id)
    except Exception:
        # Unparseable address, return None
        return None


def extract_unit_identifier(unit_str: str) -> str:
    """
    Extract unit identifier (number/letter), ignoring type keywords.

    Normalizes unit designators so that "APT 15", "UNIT 15", and "#15" all
    compare as equivalent. Preserves letter suffixes like "15A".

    Args:
        unit_str: Unit designator string like "APT 15" or "STE 405".

    Returns:
        Just the identifier portion, e.g. "15" or "405" or "15A".
    """
    cleaned = unit_str.upper()
    # Remove common unit type keywords
    for keyword in [
        "APT",
        "APARTMENT",
        "UNIT",
        "STE",
        "SUITE",
        "RM",
        "ROOM",
        "FL",
        "FLOOR",
        "BLDG",
        "BUILDING",
        "#",
    ]:
        cleaned = cleaned.replace(keyword, "")
    # Return normalized whitespace
    return " ".join(cleaned.split())


def names_are_similar(name1: str, name2: str) -> bool:
    """
    Check if two business names are similar enough to be the same location.

    Strips legal suffixes (Inc, LLC, etc.) and compares using token_set_ratio,
    which handles extra words like "Store & Donation Center" and reordering.

    Args:
        name1: First business name.
        name2: Second business name.

    Returns:
        True if token_set_ratio >= NAME_SIMILARITY_THRESHOLD.
    """
    # Guard: reject blank names to prevent false matches
    if not name1 or not name1.strip() or not name2 or not name2.strip():
        return False

    # Strip legal suffixes
    clean1 = basename(name1)
    clean2 = basename(name2)

    # Compare with token_set_ratio (handles subsets and reordering)
    score = fuzz.token_set_ratio(clean1.lower(), clean2.lower())

    return score >= NAME_SIMILARITY_THRESHOLD


def _are_street_suffixes_compatible(tokens1: list[str], tokens2: list[str]) -> bool:
    """
    Check if street suffixes are compatible between two addresses.

    Prevents false matches like "1000 COMMONWEALTH AVE" with "1000 COMMONWEALTH ST".
    Handles directionals (N, S, E, W) which can appear in different positions.

    Args:
        tokens1: Tokens from first normalized street address.
        tokens2: Tokens from second normalized street address.

    Returns:
        True if suffixes are compatible (match can proceed).
        False if suffixes conflict (match should be rejected).
    """
    if not tokens1 or not tokens2:
        return True

    DIRECTIONALS = {"N", "S", "E", "W", "NE", "NW", "SE", "SW"}

    suffix1 = tokens1[-1]
    suffix2 = tokens2[-1]

    # If last tokens match, suffixes are compatible
    if suffix1 == suffix2:
        return True

    # Last tokens differ - need to determine if they're incompatible

    # Case 1: Both are directionals but different (N ≠ S)
    if suffix1 in DIRECTIONALS and suffix2 in DIRECTIONALS:
        return False  # Different directionals = different streets

    # Case 2: One is directional, other is not
    # (handles "100 N MAIN ST" vs "100 MAIN ST N")
    if suffix1 in DIRECTIONALS or suffix2 in DIRECTIONALS:
        # Check if both addresses have the same set of tokens
        if set(tokens1) != set(tokens2):
            return False  # Different token sets = different streets
        return True  # Same tokens, different positions - allow match

    # Case 3: Both are street types (ST, AVE, RD, etc.) and they differ
    return False  # Different street types = different streets


def evaluate_pair(
    loc1: NormalizedLocation, loc2: NormalizedLocation
) -> MatchTier | None:
    """
    Evaluate a candidate pair and return the first matching tier or None.

    Assumes the pair is already within MAX_MATCH_DISTANCE_M (caller's responsibility).

    Cascade order:
    1. PHONE: Same phone number (E.164 sets intersect)
    2. ADDRESS: Same house number and similar street name
    3. NAME: Similar business names

    Args:
        loc1: First location.
        loc2: Second location.

    Returns:
        The first MatchTier that fires, or None if no tier matches.
    """
    # PHONE tier: normalized phone sets intersect
    phones1 = normalize_phones(loc1.contact.phone)
    phones2 = normalize_phones(loc2.contact.phone)

    # Perform set intersection to check for any common phone numbers.
    if phones1 and phones2 and phones1 & phones2:
        return MatchTier.PHONE

    # ADDRESS tier: same house number and similar street
    result1 = normalize_street(loc1.address.street)
    result2 = normalize_street(loc2.address.street)

    if result1 and result2:
        street1, unit_id1 = result1
        street2, unit_id2 = result2

        # Extract house number (first token containing any digits)
        tokens1 = street1.split()
        tokens2 = street2.split()

        num1 = next((t for t in tokens1 if any(c.isdigit() for c in t)), None)
        num2 = next((t for t in tokens2 if any(c.isdigit() for c in t)), None)

        # If both have house numbers but they differ, addresses don't match
        if num1 and num2:
            if num1 != num2:
                return None  # Different house numbers = different locations

            # Check if street suffixes are compatible
            # (prevents "1000 COMMONWEALTH AVE" matching "1000 COMMONWEALTH ST")
            if not _are_street_suffixes_compatible(tokens1, tokens2):
                return None  # Incompatible street types or directionals

            # Check street name similarity (handles "UNION PK ST" vs "UNION PARK ST")
            street_score = fuzz.token_set_ratio(street1, street2)
            if street_score < STREET_SIMILARITY_THRESHOLD:
                return None  # Same house number but street names don't match

            # Veto: if both have unit IDs and they differ, reject
            # (prevents merging different suites in the same building)
            if unit_id1 and unit_id2 and unit_id1 != unit_id2:
                # Different unit identifiers = different locations
                return None
            else:
                # Same unit ID, or at least one missing -> accept
                return MatchTier.ADDRESS

    # NAME tier: similar business names
    if names_are_similar(loc1.name, loc2.name):
        return MatchTier.NAME

    return None
