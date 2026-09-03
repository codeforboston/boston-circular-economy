from etl.base.querier import BaseQuerier
from etl.dtos import RawLocation


class OpenStreetMapQuerier(BaseQuerier):
    def fetch(self) -> list[RawLocation]:
        pass
