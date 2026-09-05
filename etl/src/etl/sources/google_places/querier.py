from etl.base.querier import BaseQuerier
from etl.dtos import RawLocation


class GooglePlacesQuerier(BaseQuerier):
    def fetch(self) -> list[RawLocation]:
        pass
