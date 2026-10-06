import pytest
from contracts.domain import Address, Contact, DataSource
from etl.matching import (
    MAX_MATCH_DISTANCE_M,
    NAME_SIMILARITY_THRESHOLD,
    STREET_SIMILARITY_THRESHOLD,
    MatchTier,
    evaluate_pair,
    haversine_m,
    names_are_similar,
    normalize_phones,
    normalize_street,
)


class TestHaversineM:
    """Test great-circle distance calculations."""

    def test_same_point_returns_zero(self):
        d = haversine_m(42.3588, -71.0707, 42.3588, -71.0707)
        assert d == 0.0

    def test_nearby_points_in_boston(self):
        # Two points about 28m apart
        d = haversine_m(42.3588, -71.0707, 42.3590, -71.0709)
        assert 27 < d < 29

    def test_points_150m_apart(self):
        # Roughly 150m north
        d = haversine_m(42.3588, -71.0707, 42.3601, -71.0707)
        assert 144 < d < 146

    def test_far_apart_points(self):
        # Boston to Cambridge (several km)
        d = haversine_m(42.3588, -71.0707, 42.3736, -71.1097)
        assert 3600 < d < 3650


class TestNormalizePhones:
    """Test phone number normalization."""

    def test_none_returns_empty_set(self):
        assert normalize_phones(None) == set()

    def test_empty_string_returns_empty_set(self):
        assert normalize_phones("") == set()

    def test_standard_us_phone(self):
        assert normalize_phones("617-628-3618") == {"+16176283618"}

    def test_malformed_osm_phone(self):
        # Real OSM sample: missing space after country code
        assert normalize_phones("+1617-522-1415") == {"+16175221415"}

    def test_phone_with_dashes(self):
        assert normalize_phones("+1-617-628-3618") == {"+16176283618"}

    def test_phone_with_parens(self):
        assert normalize_phones("(617) 628-3618") == {"+16176283618"}

    def test_phone_with_dots(self):
        assert normalize_phones("617.628.3618") == {"+16176283618"}

    def test_phone_with_extension(self):
        # Extension is separated by library, base number extracted
        result = normalize_phones("+1 617-628-3618 x12")
        assert "+16176283618" in result

    def test_semicolon_separated_multi_value(self):
        # OSM tags can hold multiple phone numbers
        result = normalize_phones("617-628-3618;617-628-3619")
        assert result == {"+16176283618", "+16176283619"}

    def test_vanity_number(self):
        assert normalize_phones("1-800-FLOWERS") == {"+18003569377"}

    def test_invalid_short_number(self):
        # Too short to be valid
        assert normalize_phones("555") == set()

    def test_unparseable_junk(self):
        assert normalize_phones("not-a-phone") == set()

    def test_mixed_valid_and_invalid(self):
        result = normalize_phones("617-628-3618;invalid;617-628-3619")
        assert result == {"+16176283618", "+16176283619"}


class TestNormalizeStreet:
    """Test street address normalization."""

    def test_none_returns_none(self):
        assert normalize_street(None) == None

    def test_empty_string_returns_none(self):
        assert normalize_street("") == None

    def test_normalizes_street_suffix(self):
        street, unit = normalize_street("230 Elm Street")
        assert street == "230 ELM ST"
        assert unit is None

    def test_normalizes_avenue_suffix(self):
        street, unit = normalize_street("1105 Massachusetts Avenue")
        assert street == "1105 MASSACHUSETTS AVE"
        assert unit is None

    def test_normalizes_road_suffix(self):
        street, unit = normalize_street("110 Academy Hill Road")
        assert street == "110 ACADEMY HILL RD"
        assert unit is None

    def test_preserves_abbreviated_suffix(self):
        street, unit = normalize_street("230 Elm St")
        assert street == "230 ELM ST"
        assert unit is None

    def test_normalizes_directional(self):
        street, unit = normalize_street("15 North Beacon Street")
        assert street == "15 N BEACON ST"
        assert unit is None

    def test_handles_unit_designators(self):
        # Units are split and extracted to just the identifier
        street, unit_id = normalize_street("119 Braintree St Ste 405")
        assert street == "119 BRAINTREE ST"
        assert unit_id == "405"

    def test_preserves_internal_abbreviations(self):
        # "Pk" inside street name is NOT expanded to "Park"
        street, unit_id = normalize_street("120 Union Pk St")
        assert street == "120 UNION PK ST"
        assert unit_id is None

    def test_handles_letter_suffix_on_house_number(self):
        street, unit_id = normalize_street("176A Middle Street")
        assert street == "176A MIDDLE ST"
        assert unit_id is None

    def test_different_unit_formats(self):
        # Test various unit format normalization - all extract to same ID
        street1, unit_id1 = normalize_street("119 Braintree St #405")
        street2, unit_id2 = normalize_street("119 Braintree St Ste 405")
        street3, unit_id3 = normalize_street("119 Braintree St Apt 405")
        street4, unit_id4 = normalize_street("119 Braintree St Unit 405")
        assert street1 == street2 == street3 == street4 == "119 BRAINTREE ST"
        assert unit_id1 == unit_id2 == unit_id3 == unit_id4 == "405"

    def test_unit_with_letter_suffix_preserved(self):
        street, unit_id = normalize_street("119 Braintree St #15A")
        assert street == "119 BRAINTREE ST"
        assert unit_id == "15A"

    def test_directional_prefix_normalized(self):
        # Directionals at the beginning should be normalized
        street, unit_id = normalize_street("100 North Main Street")
        assert street == "100 N MAIN ST"
        assert unit_id is None

    def test_directional_prefix_south(self):
        street, unit_id = normalize_street("200 South Washington Avenue")
        assert street == "200 S WASHINGTON AVE"
        assert unit_id is None

    def test_different_suffixes_normalized_differently(self):
        # Verify that different suffixes are preserved after normalization
        street1, _ = normalize_street("1000 Commonwealth Avenue")
        street2, _ = normalize_street("1000 Commonwealth Street")
        street3, _ = normalize_street("1000 Commonwealth Road")

        assert street1 == "1000 COMMONWEALTH AVE"
        assert street2 == "1000 COMMONWEALTH ST"
        assert street3 == "1000 COMMONWEALTH RD"

        # Verify they all differ in the last token
        assert street1.split()[-1] == "AVE"
        assert street2.split()[-1] == "ST"
        assert street3.split()[-1] == "RD"


class TestNamesAreSimilar:
    """Test business name similarity matching."""

    def test_exact_match(self):
        assert names_are_similar("Goodwill", "Goodwill")

    def test_goodwill_variants(self):
        # Real OSM vs Google case
        assert names_are_similar("Goodwill", "Goodwill Store & Donation Center")

    def test_savers_variants(self):
        assert names_are_similar("Savers", "Savers Thrift Store")

    def test_apostrophe_and_punctuation(self):
        assert names_are_similar("Mike's Auto Repair", "Mikes Auto Repair")

    def test_token_reordering(self):
        assert names_are_similar("Cambridge Bicycle", "Bicycle Cambridge")

    def test_legal_suffix_stripped(self):
        assert names_are_similar("Extra Space Storage Inc", "Extra Space Storage")

    def test_different_owner_same_category(self):
        # Should NOT match
        assert not names_are_similar("Joe's Shoe Repair", "Tony's Shoe Repair")

    def test_different_business_same_location_word(self):
        # Should NOT match
        assert not names_are_similar("Boston Sneaker Lab", "Boston Barber Co")

    def test_different_category_same_format(self):
        # Should NOT match
        assert not names_are_similar("City Sports", "City Cycles")

    def test_generic_subset(self):
        # Known weakness: generic names score 100 as subsets
        # Within 150m gate, usually acceptable
        assert names_are_similar("Shoe Repair", "Joe's Shoe Repair")

    def test_blank_names_do_not_match(self):
        # Prevent false positives from two locations with missing names
        assert not names_are_similar("", "")

    def test_blank_name_vs_valid_name(self):
        assert not names_are_similar("", "Goodwill")
        assert not names_are_similar("Goodwill", "")

    def test_whitespace_only_names_do_not_match(self):
        assert not names_are_similar("   ", "   ")
        assert not names_are_similar("  ", "Goodwill")
        assert not names_are_similar("Goodwill", "  ")


class TestEvaluatePair:
    """Test the matching cascade."""

    @pytest.fixture
    def goodwill_somerville(self, make_location):
        """Real OSM Goodwill location."""
        return make_location(
            data_source=DataSource.OPENSTREETMAP,
            data_source_id="osm-node-1546690479",
            name="Goodwill",
            lat=42.3947393,
            lon=-71.1216433,
            address=Address(
                street="230 Elm Street",
                city="Somerville",
                state="MA",
                postcode="02144",
            ),
            contact=Contact(phone="+1-617-628-3618"),
        )

    @pytest.fixture
    def goodwill_jamaica_plain(self, make_location):
        """Real OSM Goodwill location, different store."""
        return make_location(
            data_source=DataSource.OPENSTREETMAP,
            data_source_id="osm-node-2298266051",
            name="Goodwill",
            lat=42.312046,
            lon=-71.1140475,
            address=Address(street="678 Centre Street"),
            contact=Contact(phone="+1617-522-1415"),
        )

    def test_phone_tier_same_phone(self, make_location):
        loc1 = make_location(
            contact=Contact(phone="617-628-3618"),
            address=Address(street="230 Elm St"),
        )
        loc2 = make_location(
            contact=Contact(phone="(617) 628-3618"),
            address=Address(street="Different St"),
        )
        assert evaluate_pair(loc1, loc2) == MatchTier.PHONE

    def test_phone_tier_multi_value_intersection(self, make_location):
        loc1 = make_location(contact=Contact(phone="617-628-3618;617-555-0100"))
        loc2 = make_location(contact=Contact(phone="617-628-3618"))
        assert evaluate_pair(loc1, loc2) == MatchTier.PHONE

    def test_phone_tier_no_match_different_phones(self, make_location):
        loc1 = make_location(
            contact=Contact(phone="617-628-3618"),
            address=Address(street="230 Elm St"),
            name="Same Name",
        )
        loc2 = make_location(
            contact=Contact(phone="617-555-0100"),
            address=Address(street="231 Elm St"),
            name="Same Name",
        )
        # Should fall through to ADDRESS or NAME
        result = evaluate_pair(loc1, loc2)
        assert result != MatchTier.PHONE

    def test_address_tier_same_house_and_street(self, make_location):
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="230 Elm Street"),
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="230 Elm St"),
        )
        assert evaluate_pair(loc1, loc2) == MatchTier.ADDRESS

    def test_address_tier_similar_street_name(self, make_location):
        # "Union Pk" vs "Union Park"
        loc1 = make_location(
            contact=Contact(phone=None), address=Address(street="120 Union Pk St")
        )
        loc2 = make_location(
            contact=Contact(phone=None), address=Address(street="120 Union Park Street")
        )
        assert evaluate_pair(loc1, loc2) == MatchTier.ADDRESS

    def test_address_tier_same_unit_matches(self, make_location):
        # Same building, same unit number -> should match
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="119 Braintree St Ste 405"),
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="119 Braintree Street Suite 405"),
        )
        assert evaluate_pair(loc1, loc2) == MatchTier.ADDRESS

    def test_address_tier_different_unit_types_same_number(self, make_location):
        # Same unit number, different type keywords (Apt vs Unit vs #) -> should match
        test_pairs = [
            ("119 Braintree St Apt 15", "119 Braintree St Unit 15"),
            ("119 Braintree St Apt 15", "119 Braintree St #15"),
            ("119 Braintree St Unit 15", "119 Braintree St #15"),
            ("119 Braintree St Ste 405", "119 Braintree St Suite 405"),
            ("119 Braintree St Rm 15", "119 Braintree St Room 15"),
            ("119 Braintree St Fl 3", "119 Braintree St Floor 3"),
        ]

        for addr1, addr2 in test_pairs:
            loc1 = make_location(
                contact=Contact(phone=None), address=Address(street=addr1)
            )
            loc2 = make_location(
                contact=Contact(phone=None), address=Address(street=addr2)
            )
            result = evaluate_pair(loc1, loc2)
            assert result == MatchTier.ADDRESS, f"Failed to match {addr1} with {addr2}"

    def test_address_tier_different_units_rejected(self, make_location):
        # Same building, different unit numbers, different businesses -> should NOT match at all
        test_pairs = [
            (
                "119 Braintree St Ste 405",
                "119 Braintree St Ste 200",
                "Smith Law Firm",
                "Jones Accounting",
            ),
            (
                "119 Braintree St Apt 15",
                "119 Braintree St Apt 16",
                "Anderson Family",
                "Peterson Family",
            ),
            (
                "119 Braintree St #15",
                "119 Braintree St #15A",
                "Tech Startup Inc",
                "Design Studio LLC",
            ),
            (
                "119 Braintree St Bldg A",
                "119 Braintree St Bldg B",
                "Distribution Center",
                "Marketing Agency",
            ),
        ]

        for addr1, addr2, name1, name2 in test_pairs:
            loc1 = make_location(
                contact=Contact(phone=None),
                address=Address(street=addr1),
                name=name1,
            )
            loc2 = make_location(
                contact=Contact(phone=None),
                address=Address(street=addr2),
                name=name2,
            )
            # Should not match on ADDRESS tier, and names differ so no match at all
            result = evaluate_pair(loc1, loc2)
            assert result is None, (
                f"Incorrectly matched {addr1} ({name1}) with {addr2} ({name2})"
            )

    def test_address_tier_unit_number_with_letter_suffix(self, make_location):
        # Unit numbers with letter suffixes must match exactly
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="119 Braintree St #15A"),
            name="Business A",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="119 Braintree St Apt 15A"),
            name="Business A",
        )
        # 15A == 15A, should match on ADDRESS
        result = evaluate_pair(loc1, loc2)
        assert result == MatchTier.ADDRESS

    def test_address_tier_one_missing_unit_accepts(self, make_location):
        # One has unit, other doesn't -> accept (can't rule it out)
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="119 Braintree St Ste 405"),
        )
        loc2 = make_location(
            contact=Contact(phone=None), address=Address(street="119 Braintree St")
        )
        assert evaluate_pair(loc1, loc2) == MatchTier.ADDRESS

    def test_address_tier_house_number_with_letter_suffix(self, make_location):
        # House numbers with letters (e.g. subdivided properties) should match
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="176A Middle Street"),
            name="Boston Bike Shop",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="176A Middle St"),
            name="Boston Bike Shop",
        )
        # Should match on ADDRESS tier (house number "176A" extracted correctly)
        assert evaluate_pair(loc1, loc2) == MatchTier.ADDRESS

    def test_address_tier_different_letter_suffixes_no_match(self, make_location):
        # Different letter suffixes are different properties
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="176A Middle St"),
            name="Bike Shop",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="176B Middle St"),
            name="Coffee Shop",
        )
        # Should NOT match (176A != 176B, different businesses)
        assert evaluate_pair(loc1, loc2) is None

    def test_address_tier_no_match_different_house_number(self, make_location):
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="230 Elm St"),
            name="Same Business",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="232 Elm St"),
            name="Same Business",
        )
        # Different addresses = different locations, even if names match
        result = evaluate_pair(loc1, loc2)
        assert result is None

    def test_name_tier_similar_names(self, make_location):
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street=None),
            name="Goodwill",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street=None),
            name="Goodwill Store & Donation Center",
        )
        assert evaluate_pair(loc1, loc2) == MatchTier.NAME

    def test_no_match_different_everything(self, make_location):
        loc1 = make_location(
            contact=Contact(phone="617-628-3618"),
            address=Address(street="230 Elm St"),
            name="Joe's Shoe Repair",
        )
        loc2 = make_location(
            contact=Contact(phone="617-555-0100"),
            address=Address(street="100 Main St"),
            name="Tony's Shoe Repair",
        )
        assert evaluate_pair(loc1, loc2) is None

    def test_real_goodwill_locations_different_stores(
        self, goodwill_somerville, goodwill_jamaica_plain
    ):
        """Two real Goodwill stores with same name but different phones/addresses."""
        # These are 9+ km apart, so they'd be filtered by distance gate,
        # but if we did compare them, phone and address differ
        result = evaluate_pair(goodwill_somerville, goodwill_jamaica_plain)
        # Different addresses = different locations, should not match
        assert result is None

    def test_blank_names_dont_match_on_name_tier(self, make_location):
        """Two nearby locations with blank names should not match."""
        loc1 = make_location(
            name="",
            lat=42.3588,
            lon=-71.0707,
            address=Address(street="100 Main St"),
            contact=Contact(),
        )
        loc2 = make_location(
            name="",
            lat=42.3589,
            lon=-71.0707,
            address=Address(street="200 Main St"),
            contact=Contact(),
        )
        # Should not match on any tier
        assert evaluate_pair(loc1, loc2) is None

    def test_name_tier_one_address_missing(self, make_location):
        """Should match on NAME when one location lacks address data."""
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="230 Elm St"),
            name="Goodwill",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street=None),  # Missing address
            name="Goodwill Store & Donation Center",
        )
        assert evaluate_pair(loc1, loc2) == MatchTier.NAME

    def test_address_tier_same_number_different_streets(self, make_location):
        """Same house number but different streets should not match."""
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="230 Elm St"),
            name="Same Business Name",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="230 Oak St"),  # Different street
            name="Same Business Name",
        )
        # Different streets = different locations, even with same name
        assert evaluate_pair(loc1, loc2) is None

    def test_address_tier_same_name_different_suffix_no_match(self, make_location):
        """Same street name but different suffix (AVE vs ST) should NOT match.

        In Boston it's common to have both a Street and Avenue with the same name
        that are actually different streets (e.g., Commonwealth Ave vs Commonwealth Court).
        """
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="1000 Commonwealth Avenue"),
            name="Business on Ave",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="1000 Commonwealth Court"),
            name="Business on Court",
        )
        # Different suffixes = different streets, should NOT match
        assert evaluate_pair(loc1, loc2) is None

    def test_address_tier_different_directional_suffix_no_match(self, make_location):
        """Same address but different directional suffix should NOT match.

        "Main Street North" vs "Main Street South" are different streets.
        """
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="100 Main Street North"),
            name="Business on North",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="100 Main Street South"),
            name="Business on South",
        )
        # Different directional suffixes = different streets
        assert evaluate_pair(loc1, loc2) is None

    def test_address_tier_directional_different_position_matches(self, make_location):
        """Directional in different positions should match (data quality issue).

        "North Main Street" and "Main Street North" are the same street,
        just recorded inconsistently.
        """
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="100 North Main Street"),
            name="Business A",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="100 Main Street North"),
            name="Business A",
        )
        # Same directional, different position = same street
        assert evaluate_pair(loc1, loc2) == MatchTier.ADDRESS

    def test_name_tier_one_address_unparseable(self, make_location):
        """Should match on NAME when one address can't be parsed."""
        loc1 = make_location(
            contact=Contact(phone=None),
            address=Address(street="230 Elm St"),
            name="Goodwill",
        )
        loc2 = make_location(
            contact=Contact(phone=None),
            address=Address(street="!!!"),  # Unparseable
            name="Goodwill Store",
        )
        # Can't compare addresses, falls back to NAME
        assert evaluate_pair(loc1, loc2) == MatchTier.NAME


class TestMatchingConstants:
    """Verify tuning constants are sensible."""

    def test_max_distance_is_reasonable(self):
        assert MAX_MATCH_DISTANCE_M == 150

    def test_name_threshold_is_reasonable(self):
        assert 85 <= NAME_SIMILARITY_THRESHOLD <= 95

    def test_street_threshold_is_reasonable(self):
        assert 85 <= STREET_SIMILARITY_THRESHOLD <= 95
