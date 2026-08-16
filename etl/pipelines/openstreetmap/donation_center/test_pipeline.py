from pipelines.openstreetmap.donation_center.querier import DonationCenterQuerier
from pipelines.openstreetmap.donation_center.normalizer import DonationCenterNormalizer


querier = DonationCenterQuerier()
normalizer = DonationCenterNormalizer()

locations = querier.fetch()
normalized_locations = normalizer.normalize(locations)
