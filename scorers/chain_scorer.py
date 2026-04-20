"""Chain scorer module for supply chain position scoring.

Scoring formula:
产业地位分 = 所处环节权重 × 环节内相对排名

环节权重: 上游(关键资源) > 中游(核心制造) > 下游(终端应用)
"""
from typing import List, Dict, Any


# Link weight constants
UPSTREAM: float = 1.0    # 关键资源
MIDSTREAM: float = 0.7   # 核心制造
DOWNSTREAM: float = 0.5   # 终端应用


def get_link_weight(link_type: str) -> float:
    """Get the weight for a supply chain link type.

    Args:
        link_type: The link type ('upstream', 'midstream', 'downstream')

    Returns:
        The weight for the link type, or 0.0 for unknown types
    """
    weights = {
        "upstream": UPSTREAM,
        "midstream": MIDSTREAM,
        "downstream": DOWNSTREAM,
    }
    # Case-insensitive lookup
    return weights.get(link_type.lower(), 0.0)


def calculate_relative_rank(stocks_in_link: List[Dict[str, Any]], stock_code: str) -> float:
    """Calculate relative rank of a stock within its link.

    Args:
        stocks_in_link: List of stocks in the same supply chain link
        stock_code: Code of the stock to calculate rank for

    Returns:
        Relative rank from 0.0 to 1.0 (1.0 = best/top position)
    """
    if not stocks_in_link:
        return 0.0

    # Find the position of the stock in the list
    try:
        position = next(i for i, s in enumerate(stocks_in_link) if s.get("code") == stock_code)
    except StopIteration:
        return 0.0

    total = len(stocks_in_link)

    # Calculate relative rank (1.0 for first, decreasing to near 0.0 for last)
    # Using linear interpolation: rank = (total - position) / total
    relative_rank = (total - position) / total

    return relative_rank


def calculate_chain_position_score(link_weight: float, relative_rank: float) -> float:
    """Calculate chain position score by combining link weight and relative rank.

    Args:
        link_weight: Weight of the supply chain link (UPSTREAM, MIDSTREAM, DOWNSTREAM)
        relative_rank: Relative position within the link (0.0 to 1.0)

    Returns:
        Combined chain position score
    """
    return link_weight * relative_rank


def score_chain_positions(chain_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Score all stocks in a supply chain based on their chain position.

    Args:
        chain_data: Dictionary with keys 'upstream', 'midstream', 'downstream',
                    each containing a list of stock dicts

    Returns:
        List of stocks with scores, sorted by score descending
    """
    scored_stocks: List[Dict[str, Any]] = []

    for link_type in ["upstream", "midstream", "downstream"]:
        stocks_in_link = chain_data.get(link_type, [])
        link_weight = get_link_weight(link_type)

        for stock in stocks_in_link:
            stock_code = stock.get("code", "")
            relative_rank = calculate_relative_rank(stocks_in_link, stock_code)
            score = calculate_chain_position_score(link_weight, relative_rank)

            # Create new dict with score and link_type added (immutability)
            scored_stock = {
                **stock,
                "score": score,
                "link_type": link_type,
            }
            scored_stocks.append(scored_stock)

    # Sort by score descending
    scored_stocks.sort(key=lambda s: s["score"], reverse=True)

    return scored_stocks


class ChainScorer:
    """Chain scorer class for supply chain position scoring."""

    def __init__(
        self,
        upstream_weight: float = UPSTREAM,
        midstream_weight: float = MIDSTREAM,
        downstream_weight: float = DOWNSTREAM,
    ):
        """Initialize scorer with link weights.

        Args:
            upstream_weight: Weight for upstream link (default UPSTREAM)
            midstream_weight: Weight for midstream link (default MIDSTREAM)
            downstream_weight: Weight for downstream link (default DOWNSTREAM)
        """
        self.upstream_weight = upstream_weight
        self.midstream_weight = midstream_weight
        self.downstream_weight = downstream_weight

    def get_link_weight(self, link_type: str) -> float:
        """Get weight for a link type using instance weights.

        Args:
            link_type: The link type

        Returns:
            The weight for the link type
        """
        weights = {
            "upstream": self.upstream_weight,
            "midstream": self.midstream_weight,
            "downstream": self.downstream_weight,
        }
        return weights.get(link_type.lower(), 0.0)

    def score_chain_positions(self, chain_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Score all stocks in a supply chain using instance weights.

        Args:
            chain_data: Dictionary with keys 'upstream', 'midstream', 'downstream'

        Returns:
            List of stocks with scores, sorted by score descending
        """
        scored_stocks: List[Dict[str, Any]] = []

        for link_type in ["upstream", "midstream", "downstream"]:
            stocks_in_link = chain_data.get(link_type, [])
            link_weight = self.get_link_weight(link_type)

            for stock in stocks_in_link:
                stock_code = stock.get("code", "")
                relative_rank = calculate_relative_rank(stocks_in_link, stock_code)
                score = calculate_chain_position_score(link_weight, relative_rank)

                # Create new dict with score and link_type added (immutability)
                scored_stock = {
                    **stock,
                    "score": score,
                    "link_type": link_type,
                }
                scored_stocks.append(scored_stock)

        # Sort by score descending
        scored_stocks.sort(key=lambda s: s["score"], reverse=True)

        return scored_stocks
