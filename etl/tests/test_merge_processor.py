import pytest

from etl.dtos import Address, Contact, DataSource
from etl.merge_processor import MergeProcessor


class TestMergeProcessorMatch:
    """Test the MergeProcessor group+prioritize methods."""

    @pytest.fixture
    def processor(self):
        return MergeProcessor()

    def _match(self, processor, locations_by_source):
        """Helper: combines group + prioritize for tests that check match groups."""
        matched_pairs = processor.group(locations_by_source)
        return processor.prioritize(matched_pairs, locations_by_source)

    def test_match_returns_empty_for_empty_input(self, processor):
        result = self._match(processor, {})
        assert result == []

    def test_single_source_creates_single_source_groups(self, processor, make_location):
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1", data_source=DataSource.GOOGLE_PLACES
                ),
                make_location(
                    data_source_id="g2", data_source=DataSource.GOOGLE_PLACES
                ),
            ]
        }
        groups = self._match(processor, locations)

        assert len(groups) == 2
        assert all(len(g) == 1 for g in groups)
        assert all(DataSource.GOOGLE_PLACES in g for g in groups)

    def test_distant_locations_dont_match(self, processor, make_location):
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                    name="Business A",
                )
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3736,  # ~3.6km away
                    lon=-71.1097,
                    name="Business A",
                )
            ],
        }
        groups = self._match(processor, locations)

        # Should be 2 single-source groups (too far apart)
        assert len(groups) == 2
        assert all(len(g) == 1 for g in groups)

    def test_nearby_similar_names_match(self, processor, make_location):
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                    name="Goodwill Store & Donation Center",
                    address=Address(street="230 Elm St"),
                )
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3590,  # 28m away
                    lon=-71.0709,
                    name="Goodwill",
                    address=Address(street="230 Elm Street"),
                )
            ],
        }
        groups = self._match(processor, locations)

        # Should be 1 merged group
        assert len(groups) == 1
        assert len(groups[0]) == 2
        assert DataSource.GOOGLE_PLACES in groups[0]
        assert DataSource.OPENSTREETMAP in groups[0]

    def test_phone_match_prioritized_over_name(self, processor, make_location):
        # Same phone number should match even with different names
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                    name="Mike's Auto Repair",
                    contact=Contact(phone="617-628-3618"),
                )
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3590,
                    lon=-71.0709,
                    name="Mikes Auto Service",
                    contact=Contact(phone="(617) 628-3618"),
                )
            ],
        }
        groups = self._match(processor, locations)

        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_one_to_one_assignment_no_double_claiming(self, processor, make_location):
        # If Google loc matches both OSM locs, only the best match should happen
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                    name="Coffee Shop",
                    address=Address(street="100 Main St"),
                )
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3588,  # Exact same location
                    lon=-71.0707,
                    name="Coffee Shop",
                    address=Address(street="100 Main St"),
                ),
                make_location(
                    data_source_id="o2",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3590,  # Nearby, similar name
                    lon=-71.0709,
                    name="Coffee Shop Downtown",
                    address=Address(street="102 Main St"),
                ),
            ],
        }
        groups = self._match(processor, locations)

        # Google should match with o1 (better match), leaving o2 alone
        assert len(groups) == 2

        # Find the merged group
        merged = [g for g in groups if len(g) == 2]
        single = [g for g in groups if len(g) == 1]

        assert len(merged) == 1
        assert len(single) == 1

        # Verify the right OSM location was matched
        assert merged[0][DataSource.OPENSTREETMAP].data_source_id == "o1"
        assert single[0][DataSource.OPENSTREETMAP].data_source_id == "o2"

    def test_multiple_sources_all_single(self, processor, make_location):
        # All locations far apart, should all be single-source groups
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                )
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.4000,
                    lon=-71.1500,
                )
            ],
        }
        groups = self._match(processor, locations)

        assert len(groups) == 2
        assert all(len(g) == 1 for g in groups)


class TestMergeProcessorEndToEnd:
    """Test the full MergeProcessor.process() pipeline."""

    @pytest.fixture
    def processor(self):
        return MergeProcessor()

    def test_process_merges_matched_locations(self, processor, make_location):
        """End-to-end test: match and merge."""
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                    name="Goodwill Store",
                    address=Address(street="230 Elm St", city="Boston"),
                    contact=Contact(
                        phone="617-555-0100", website="https://goodwill.org"
                    ),
                )
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3590,
                    lon=-71.0709,
                    name="Goodwill",
                    address=Address(
                        street="230 Elm Street",
                        city="Boston",
                        state="MA",
                        postcode="02144",
                    ),
                    contact=Contact(email="info@goodwill.org"),
                )
            ],
        }

        result = processor.process(locations)

        # Should return 1 merged location
        assert len(result) == 1
        merged = result[0]

        # Should use Google's name, coords, and ID
        assert merged.name == "Goodwill Store"
        assert merged.lat == 42.3588
        assert merged.lon == -71.0707
        assert merged.data_source == DataSource.GOOGLE_PLACES
        assert merged.data_source_id == "g1"

        # Should use OSM's more complete address
        assert merged.address.postcode == "02144"

        # Should merge contact fields
        assert merged.contact.phone == "617-555-0100"
        assert merged.contact.email == "info@goodwill.org"
        assert merged.contact.website == "https://goodwill.org"

    def test_process_keeps_unmatched_separate(self, processor, make_location):
        """Unmatched locations should pass through unchanged."""
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                    name="Business A",
                )
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.4000,  # Far away
                    lon=-71.1500,
                    name="Business B",
                )
            ],
        }

        result = processor.process(locations)

        # Should return 2 separate locations
        assert len(result) == 2

        # Should preserve original IDs
        ids = {loc.data_source_id for loc in result}
        assert ids == {"g1", "o1"}

    def test_chain_with_close_locations_one_source_knows_both(
        self, processor, make_location
    ):
        """
        Chain business with 2 nearby locations (e.g., Starbucks 100m apart).
        Google knows about both, OSM only knows about one.

        Expected: OSM location matches with closest Google location,
        other Google location stays separate.
        """
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                    name="Starbucks",
                    address=Address(street="100 Main St"),
                    contact=Contact(phone="617-555-0100"),
                ),
                make_location(
                    data_source_id="g2",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3598,  # ~110m north
                    lon=-71.0707,
                    name="Starbucks",
                    address=Address(street="200 Main St"),
                    contact=Contact(phone="617-555-0200"),
                ),
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3589,  # Very close to g1
                    lon=-71.0708,
                    name="Starbucks Coffee",
                    address=Address(street="100 Main St"),
                )
            ],
        }

        result = processor.process(locations)

        # Should return 2 locations: merged g1+o1, and standalone g2
        assert len(result) == 2

        # Find which is merged
        google_ids = {loc.data_source_id for loc in result}
        assert "g2" in google_ids  # g2 stayed separate

        # One should have g1's ID (the merged one)
        merged = next(loc for loc in result if loc.data_source_id == "g1")
        # Verify it has merged contact data
        assert merged.contact.phone == "617-555-0100"

    def test_multiple_chains_interleaved_locations(self, processor, make_location):
        """
        Two different chains (Starbucks, Dunkin) with nearby locations.
        Tests that different businesses don't get crossed.
        """
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                    name="Starbucks",
                    address=Address(street="100 Main St"),
                ),
                make_location(
                    data_source_id="g2",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3590,
                    lon=-71.0710,
                    name="Dunkin Donuts",
                    address=Address(street="102 Main St"),
                ),
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3589,
                    lon=-71.0708,
                    name="Starbucks Coffee",
                    address=Address(street="100 Main St"),
                ),
                make_location(
                    data_source_id="o2",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3591,
                    lon=-71.0711,
                    name="Dunkin'",
                    address=Address(street="102 Main St"),
                ),
            ],
        }

        result = processor.process(locations)

        # Should return 2 merged locations (not 4, not crossed)
        assert len(result) == 2

        # Both should have Google IDs (priority)
        google_ids = {loc.data_source_id for loc in result}
        assert google_ids == {"g1", "g2"}

        # Verify names didn't get crossed
        names = {loc.name for loc in result}
        assert "Starbucks" in names
        assert "Dunkin Donuts" in names

    def test_three_goodwill_locations_all_stay_separate(self, processor, make_location):
        """
        Real-world scenario: Three Goodwill stores kilometers apart.
        Same name, brand, website but different locations and phones.
        Should NOT merge despite name similarity.
        """
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3947,  # Somerville
                    lon=-71.1216,
                    name="Goodwill Store & Donation Center",
                    address=Address(street="230 Elm St", city="Somerville"),
                    contact=Contact(phone="617-628-3618"),
                )
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3120,  # Jamaica Plain, ~9km away
                    lon=-71.1140,
                    name="Goodwill",
                    address=Address(street="678 Centre St"),
                    contact=Contact(phone="617-522-1415"),
                ),
                make_location(
                    data_source_id="o2",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3641,  # Cambridge, ~6km from g1
                    lon=-71.1019,
                    name="Goodwill",
                    address=Address(street="520 Massachusetts Ave", city="Cambridge"),
                    contact=Contact(phone="617-868-6330"),
                ),
            ],
        }

        result = processor.process(locations)

        # Should return 3 separate locations (too far apart)
        assert len(result) == 3

        # All should have their original IDs
        source_ids = {loc.data_source_id for loc in result}
        assert source_ids == {"g1", "o1", "o2"}

    def test_same_building_different_units_stay_separate(
        self, processor, make_location
    ):
        """
        Two businesses in same building at different suites.
        Unit veto rule should prevent them from merging on ADDRESS tier,
        and different names prevent NAME tier match.
        """
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                    name="Smith & Associates Law",
                    address=Address(street="100 Main St Ste 405"),
                    contact=Contact(phone="617-555-1000"),  # Different phones
                )
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3589,  # Same building, slightly different coords
                    lon=-71.0708,
                    name="Johnson Accounting Services",
                    address=Address(street="100 Main St Suite 200"),
                    contact=Contact(phone="617-555-2000"),  # Different phones
                )
            ],
        }

        result = processor.process(locations)

        # Should return 2 separate locations (different units, different names, different phones)
        assert len(result) == 2
        assert {loc.data_source_id for loc in result} == {"g1", "o1"}

    def test_asymmetric_match_quality(self, processor, make_location):
        """
        Google location is equidistant from two OSM locations,
        but has a phone match with one of them.
        Should match on phone tier, not name tier.
        """
        locations = {
            DataSource.GOOGLE_PLACES: [
                make_location(
                    data_source_id="g1",
                    data_source=DataSource.GOOGLE_PLACES,
                    lat=42.3588,
                    lon=-71.0707,
                    name="Pizza Place",
                    contact=Contact(phone="617-555-0100"),
                )
            ],
            DataSource.OPENSTREETMAP: [
                make_location(
                    data_source_id="o1",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3590,  # ~28m away
                    lon=-71.0709,
                    name="Pizza Place",  # Name matches
                    contact=Contact(phone=None),  # No phone
                ),
                make_location(
                    data_source_id="o2",
                    data_source=DataSource.OPENSTREETMAP,
                    lat=42.3590,  # Same distance
                    lon=-71.0705,
                    name="Joe's Pizza",  # Slightly different name
                    contact=Contact(phone="(617) 555-0100"),  # Phone matches!
                ),
            ],
        }

        result = processor.process(locations)

        # Should return 2 locations: g1+o2 (phone match), and o1 alone
        assert len(result) == 2

        # Find the merged one
        merged = next(loc for loc in result if loc.data_source_id == "g1")
        # Should have phone from both sources
        assert merged.contact.phone == "617-555-0100"
