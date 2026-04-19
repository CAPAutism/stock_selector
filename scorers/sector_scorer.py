"""Sector scorer module for calculating sector热度 scores.

板块热度分 = 0.6 × 资金分 + 0.4 × 热度分

资金分 = 板块主力净流入排名标准化 (0-100)
热度分 = 互联网讨论热度标准化 (0-100)
"""
from typing import List


# Default scoring weights
DEFAULT_FUND_FLOW_WEIGHT = 0.6
DEFAULT_HEAT_WEIGHT = 0.4

# Maximum rank to use for fund flow scoring (linear decay below this)
DEFAULT_MAX_RANK = 100


def normalize_to_score(value: float, min_val: float = 0, max_val: float = 100) -> float:
    """Normalize a value to 0-100 range using min-max normalization.

    Args:
        value: The value to normalize
        min_val: Minimum value in the range (default 0)
        max_val: Maximum value in the range (default 100)

    Returns:
        Normalized value clamped to 0-100 range
    """
    if max_val == min_val:
        return 100.0 if value >= max_val else 0.0

    normalized = (value - min_val) / (max_val - min_val) * 100
    return max(0.0, min(100.0, normalized))


def calculate_fund_flow_score(rank: int, max_rank: int = DEFAULT_MAX_RANK) -> float:
    """Calculate fund flow score based on ranking position.

    Args:
        rank: The ranking position (1 = best, higher = worse)
        max_rank: Maximum rank for linear decay calculation

    Returns:
        Score from 0-100 (rank 1 = 100, decreasing linearly)
    """
    if rank <= 0:
        return 0.0

    if rank == 1:
        return 100.0

    # Linear decay from 100 to 0 over max_rank positions
    score = 100.0 * (max_rank - rank + 1) / max_rank
    return max(0.0, min(100.0, score))


def calculate_heat_score(heat_value: float) -> float:
    """Calculate heat score from internet heat data.

    Args:
        heat_value: The internet heat value (typically 0-100)

    Returns:
        Score from 0-100
    """
    return max(0.0, min(100.0, heat_value))


def calculate_sector_score(fund_flow_score: float, heat_score: float,
                          fund_flow_weight: float = DEFAULT_FUND_FLOW_WEIGHT,
                          heat_weight: float = DEFAULT_HEAT_WEIGHT) -> float:
    """Calculate combined sector score.

    Args:
        fund_flow_score: Fund flow component score (0-100)
        heat_score: Heat component score (0-100)
        fund_flow_weight: Weight for fund flow score (default 0.6)
        heat_weight: Weight for heat score (default 0.4)

    Returns:
        Combined weighted score (0-100)
    """
    return fund_flow_weight * fund_flow_score + heat_weight * heat_score


def score_sectors(sectors: List[dict]) -> List[dict]:
    """Score and sort sectors by combined score.

    Args:
        sectors: List of sector dicts with 'name', 'fund_flow_rank', and 'heat_value' fields

    Returns:
        List of sectors sorted by score in descending order, each with 'score' field added
    """
    if not sectors:
        return []

    scored_sectors = []
    for sector in sectors:
        fund_flow_rank = sector.get('fund_flow_rank', 0)
        heat_value = sector.get('heat_value', 0)

        fund_flow_score = calculate_fund_flow_score(fund_flow_rank)
        heat_score = calculate_heat_score(heat_value)
        score = calculate_sector_score(fund_flow_score, heat_score)

        # Create new dict with score added (immutability)
        scored_sector = {**sector, 'score': score}
        scored_sectors.append(scored_sector)

    # Sort by score descending
    scored_sectors.sort(key=lambda s: s['score'], reverse=True)

    return scored_sectors


class SectorScorer:
    """Sector scorer class for calculating sector热度 scores."""

    def __init__(self, fund_flow_weight: float = DEFAULT_FUND_FLOW_WEIGHT,
                 heat_weight: float = DEFAULT_HEAT_WEIGHT):
        """Initialize scorer with weights.

        Args:
            fund_flow_weight: Weight for fund flow score (default 0.6)
            heat_weight: Weight for heat score (default 0.4)
        """
        self.fund_flow_weight = fund_flow_weight
        self.heat_weight = heat_weight

    def score(self, fund_flow_score: float, heat_score: float) -> float:
        """Calculate sector score with instance weights.

        Args:
            fund_flow_score: Fund flow component score (0-100)
            heat_score: Heat component score (0-100)

        Returns:
            Combined weighted score (0-100)
        """
        return calculate_sector_score(
            fund_flow_score, heat_score,
            self.fund_flow_weight, self.heat_weight
        )

    def score_sectors(self, sectors: List[dict]) -> List[dict]:
        """Score and sort sectors using instance weights.

        Args:
            sectors: List of sector dicts with 'name', 'fund_flow_rank', and 'heat_value' fields

        Returns:
            List of sectors sorted by score in descending order, each with 'score' field added
        """
        if not sectors:
            return []

        scored_sectors = []
        for sector in sectors:
            fund_flow_rank = sector.get('fund_flow_rank', 0)
            heat_value = sector.get('heat_value', 0)

            fund_flow_score = calculate_fund_flow_score(fund_flow_rank)
            heat_score = calculate_heat_score(heat_value)
            score = self.score(fund_flow_score, heat_score)

            # Create new dict with score added (immutability)
            scored_sector = {**sector, 'score': score}
            scored_sectors.append(scored_sector)

        # Sort by score descending
        scored_sectors.sort(key=lambda s: s['score'], reverse=True)

        return scored_sectors
