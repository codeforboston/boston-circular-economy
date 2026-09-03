from etl.dtos import DataSource, MatchGroup, NormalizedLocation


class MergeProcessor:
    def process(
        self,
        locations_by_source: dict[DataSource, list[NormalizedLocation]],
    ) -> list[NormalizedLocation]:
        match_groups = self.match(locations_by_source)
        return self.prioritize(match_groups)

    # Match businesses across sources.
    # Assumes each source's list has no duplicate entries for the same business.
    def match(
        self,
        locations_by_source: dict[DataSource, list[NormalizedLocation]],
    ) -> list[MatchGroup]:
        pass

    # Decide which source wins when merged fields conflict.
    def prioritize(
        self,
        match_groups: list[MatchGroup],
    ) -> list[NormalizedLocation]:
        pass
