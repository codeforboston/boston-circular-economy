from etl.dtos import DataSource, MatchGroup, NormalizedLocation
from etl.field_merge import merge_group
from etl.matching import MAX_MATCH_DISTANCE_M, MatchTier, evaluate_pair, haversine_m


class MergeProcessor:
    def process(
        self,
        locations_by_source: dict[DataSource, list[NormalizedLocation]],
    ) -> list[NormalizedLocation]:
        matched_pairs = self.group(locations_by_source)
        match_groups = self.prioritize(matched_pairs, locations_by_source)
        return self.merge(match_groups)

    # Group candidate location pairs across sources.
    # Assumes each source's list has no duplicate entries for the same business.
    def group(
        self,
        locations_by_source: dict[DataSource, list[NormalizedLocation]],
    ) -> list[
        tuple[
            NormalizedLocation,
            NormalizedLocation,
            MatchTier,
            float,
            DataSource,
            DataSource,
        ]
    ]:
        """
        Generate and evaluate candidate location pairs across data sources.

        Stage 1: Generate candidate pairs within MAX_MATCH_DISTANCE_M
        Stage 2: Evaluate each pair with the cascade (PHONE > ADDRESS > NAME)

        Returns:
            List of matched pairs with metadata: (loc1, loc2, tier, distance, source1, source2)
        """
        # Stage 1: Generate all cross-source candidate pairs within distance threshold
        candidate_pairs: list[
            tuple[NormalizedLocation, NormalizedLocation, float, DataSource, DataSource]
        ] = []

        sources = list(locations_by_source.keys())
        for i, source1 in enumerate(sources):
            for source2 in sources[i + 1 :]:  # Only compare each pair of sources once
                for loc1 in locations_by_source[source1]:
                    for loc2 in locations_by_source[source2]:
                        distance = haversine_m(loc1.lat, loc1.lon, loc2.lat, loc2.lon)
                        if distance <= MAX_MATCH_DISTANCE_M:
                            candidate_pairs.append(
                                (loc1, loc2, distance, source1, source2)
                            )

        # Stage 2: Evaluate each candidate pair with the cascade
        # Store as (loc1, loc2, tier, distance, source1, source2)
        matched_pairs: list[
            tuple[
                NormalizedLocation,
                NormalizedLocation,
                MatchTier,
                float,
                DataSource,
                DataSource,
            ]
        ] = []

        for loc1, loc2, distance, source1, source2 in candidate_pairs:
            tier = evaluate_pair(loc1, loc2)
            if tier is not None:
                matched_pairs.append((loc1, loc2, tier, distance, source1, source2))

        return matched_pairs

    # Prioritize matched pairs and perform one-to-one assignment.
    def prioritize(
        self,
        matched_pairs: list[
            tuple[
                NormalizedLocation,
                NormalizedLocation,
                MatchTier,
                float,
                DataSource,
                DataSource,
            ]
        ],
        locations_by_source: dict[DataSource, list[NormalizedLocation]],
    ) -> list[MatchGroup]:
        """
        Sort matched pairs by tier/distance and perform one-to-one assignment.

        Each location can only be assigned to one match group. Better matches
        (higher tier, shorter distance) are assigned first.

        Returns:
            List of MatchGroups, where each group is a dict[DataSource, NormalizedLocation].
            Unmatched locations become single-source groups.
        """
        # Sort by tier priority (PHONE > ADDRESS > NAME), then distance, then IDs for stability
        matched_pairs.sort(
            key=lambda x: (
                x[2].value,  # tier priority
                x[3],  # distance
                x[0].data_source_id,  # stable tiebreak
                x[1].data_source_id,
            )
        )

        # Track which locations have been "claimed" by a match group.
        # Each location can only be in a single group.
        claimed: set[tuple[DataSource, str]] = set()
        groups: list[MatchGroup] = []

        for loc1, loc2, tier, distance, source1, source2 in matched_pairs:
            key1 = (source1, loc1.data_source_id)
            key2 = (source2, loc2.data_source_id)

            # Only accept if neither location is already claimed
            if key1 not in claimed and key2 not in claimed:
                groups.append({source1: loc1, source2: loc2})
                claimed.add(key1)
                claimed.add(key2)

        # Add unmatched locations as single-source groups
        for source, locations in locations_by_source.items():
            for loc in locations:
                key = (source, loc.data_source_id)
                if key not in claimed:
                    groups.append({source: loc})

        return groups

    # Merge each match group into a single location.
    def merge(
        self,
        match_groups: list[MatchGroup],
    ) -> list[NormalizedLocation]:
        """
        Merge each MatchGroup into a single NormalizedLocation.

        Delegates to merge_group() for field-level merging logic.

        Returns:
            List of merged NormalizedLocations, one per MatchGroup.
        """
        return [merge_group(group) for group in match_groups]
