from base_querier import BaseQuerier
from base_normalizer import BaseNormalizer
from ingester import Ingester


def run(querier: BaseQuerier, normalizer: BaseNormalizer):
    ingester = Ingester()
    for batch in querier.fetch():
        records = normalizer.normalize(batch)
        ingester.write(records)
