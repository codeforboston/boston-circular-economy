
from contracts.domain import (
    Activity,
    Address,
    Availability,
    Contact,
    DataSource,
    ItemCategory,
    Service,
)
from etl.field_merge import merge_group


class TestMergeGroup:
    """Test field-level merging logic."""

    def test_single_source_group_returns_unchanged(self, make_location):
        loc = make_location(data_source_id="g1", data_source=DataSource.GOOGLE_PLACES)
        group = {DataSource.GOOGLE_PLACES: loc}

        result = merge_group(group)

        assert result == loc

    def test_name_takes_first_non_empty(self, make_location):
        group = {
            DataSource.GOOGLE_PLACES: make_location(
                data_source=DataSource.GOOGLE_PLACES, name="Google Name"
            ),
            DataSource.OPENSTREETMAP: make_location(
                data_source=DataSource.OPENSTREETMAP, name="OSM Name"
            ),
        }

        result = merge_group(group)

        # Google has priority
        assert result.name == "Google Name"

    def test_coordinates_taken_as_pair_from_google(self, make_location):
        group = {
            DataSource.GOOGLE_PLACES: make_location(
                data_source=DataSource.GOOGLE_PLACES, lat=42.3588, lon=-71.0707
            ),
            DataSource.OPENSTREETMAP: make_location(
                data_source=DataSource.OPENSTREETMAP, lat=42.3590, lon=-71.0709
            ),
        }

        result = merge_group(group)

        # Should take Google's coordinates as a pair
        assert result.lat == 42.3588
        assert result.lon == -71.0707

    def test_address_taken_from_most_complete(self, make_location):
        incomplete = Address(street="100 Main St", city=None, state=None, postcode=None)
        complete = Address(
            street="100 Main St", city="Boston", state="MA", postcode="02118"
        )

        group = {
            DataSource.GOOGLE_PLACES: make_location(
                data_source=DataSource.GOOGLE_PLACES, address=incomplete
            ),
            DataSource.OPENSTREETMAP: make_location(
                data_source=DataSource.OPENSTREETMAP, address=complete
            ),
        }

        result = merge_group(group)

        # Should take OSM's more complete address
        assert result.address == complete

    def test_contact_merged_per_subfield(self, make_location):
        google_contact = Contact(
            phone="617-555-0100", email=None, website="https://example.com"
        )
        osm_contact = Contact(phone=None, email="info@example.com", website=None)

        group = {
            DataSource.GOOGLE_PLACES: make_location(
                data_source=DataSource.GOOGLE_PLACES, contact=google_contact
            ),
            DataSource.OPENSTREETMAP: make_location(
                data_source=DataSource.OPENSTREETMAP, contact=osm_contact
            ),
        }

        result = merge_group(group)

        # Should have phone and website from Google, email from OSM
        assert result.contact.phone == "617-555-0100"
        assert result.contact.email == "info@example.com"
        assert result.contact.website == "https://example.com"

    def test_services_unioned_and_deduplicated(self, make_location):
        google_services = [
            Service(
                activity=Activity.REPAIR_PAID, item_category=ItemCategory.ELECTRONICS
            ),
            Service(
                activity=Activity.RESALE_BUY, item_category=ItemCategory.ELECTRONICS
            ),
        ]
        osm_services = [
            Service(
                activity=Activity.REPAIR_PAID, item_category=ItemCategory.ELECTRONICS
            ),  # duplicate
            Service(
                activity=Activity.DONATION_DROP, item_category=ItemCategory.CLOTHING
            ),
        ]

        group = {
            DataSource.GOOGLE_PLACES: make_location(
                data_source=DataSource.GOOGLE_PLACES, services=google_services
            ),
            DataSource.OPENSTREETMAP: make_location(
                data_source=DataSource.OPENSTREETMAP, services=osm_services
            ),
        }

        result = merge_group(group)

        # Should have 3 unique services (duplicate removed)
        assert len(result.services) == 3

        # Verify each unique service is present
        service_keys = {(s.activity, s.item_category) for s in result.services}
        assert (Activity.REPAIR_PAID, ItemCategory.ELECTRONICS) in service_keys
        assert (Activity.RESALE_BUY, ItemCategory.ELECTRONICS) in service_keys
        assert (Activity.DONATION_DROP, ItemCategory.CLOTHING) in service_keys

    def test_availability_prefers_one_with_opening_hours(self, make_location):
        no_hours = Availability(opening_hours=None, is_persistent=True)
        with_hours = Availability(opening_hours="Mo-Fr 09:00-17:00", is_persistent=True)

        group = {
            DataSource.GOOGLE_PLACES: make_location(
                data_source=DataSource.GOOGLE_PLACES, availability=no_hours
            ),
            DataSource.OPENSTREETMAP: make_location(
                data_source=DataSource.OPENSTREETMAP, availability=with_hours
            ),
        }

        result = merge_group(group)

        # Should take OSM's availability with hours
        assert result.availability.opening_hours == "Mo-Fr 09:00-17:00"

    def test_last_verified_takes_latest_date(self, make_location):
        group = {
            DataSource.GOOGLE_PLACES: make_location(
                data_source=DataSource.GOOGLE_PLACES, last_verified="2024-01-15"
            ),
            DataSource.OPENSTREETMAP: make_location(
                data_source=DataSource.OPENSTREETMAP, last_verified="2024-03-20"
            ),
        }

        result = merge_group(group)

        # Should take the later date
        assert result.last_verified == "2024-03-20"

    def test_last_verified_handles_none(self, make_location):
        group = {
            DataSource.GOOGLE_PLACES: make_location(
                data_source=DataSource.GOOGLE_PLACES, last_verified=None
            ),
            DataSource.OPENSTREETMAP: make_location(
                data_source=DataSource.OPENSTREETMAP, last_verified="2024-03-20"
            ),
        }

        result = merge_group(group)

        assert result.last_verified == "2024-03-20"

    def test_data_source_id_from_preferred_source(self, make_location):
        group = {
            DataSource.GOOGLE_PLACES: make_location(
                data_source_id="google-123", data_source=DataSource.GOOGLE_PLACES
            ),
            DataSource.OPENSTREETMAP: make_location(
                data_source_id="osm-456", data_source=DataSource.OPENSTREETMAP
            ),
        }

        result = merge_group(group)

        # Should use Google's ID for stability
        assert result.data_source_id == "google-123"
        assert result.data_source == DataSource.GOOGLE_PLACES

    def test_osm_only_group_uses_osm_id(self, make_location):
        group = {
            DataSource.OPENSTREETMAP: make_location(
                data_source_id="osm-456", data_source=DataSource.OPENSTREETMAP
            ),
        }

        result = merge_group(group)

        assert result.data_source_id == "osm-456"
        assert result.data_source == DataSource.OPENSTREETMAP
