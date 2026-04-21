from pipelines.example.querier import ExampleQuerier
from pipelines.example.normalizer import ExampleNormalizer


def test_example_pipeline():
    querier = ExampleQuerier()
    normalizer = ExampleNormalizer()

    raw_locations = querier.fetch()
    normalized_locations = normalizer.normalize(raw_locations)

    assert len(normalized_locations) == len(raw_locations)
