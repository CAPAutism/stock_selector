"""Tests for chain scorer module.

Scoring formula:
产业地位分 = 所处环节权重 × 环节内相对排名

环节权重: 上游(关键资源) > 中游(核心制造) > 下游(终端应用)
"""
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scorers.chain_scorer import (
    UPSTREAM,
    MIDSTREAM,
    DOWNSTREAM,
    get_link_weight,
    calculate_relative_rank,
    calculate_chain_position_score,
    score_chain_positions,
    ChainScorer,
)


class TestLinkWeightConstants:
    """Tests for link weight constants."""

    def test_upstream_weight_is_defined(self):
        """UPSTREAM constant should be defined as 1.0."""
        assert UPSTREAM == 1.0

    def test_midstream_weight_is_defined(self):
        """MIDSTREAM constant should be defined as 0.7."""
        assert MIDSTREAM == 0.7

    def test_downstream_weight_is_defined(self):
        """DOWNSTREAM constant should be defined as 0.5."""
        assert DOWNSTREAM == 0.5

    def test_upstream_weight_greater_than_midstream(self):
        """UPSTREAM weight should be greater than MIDSTREAM."""
        assert UPSTREAM > MIDSTREAM

    def test_midstream_weight_greater_than_downstream(self):
        """MIDSTREAM weight should be greater than DOWNSTREAM."""
        assert MIDSTREAM > DOWNSTREAM


class TestGetLinkWeight:
    """Tests for get_link_weight function."""

    def test_returns_upstream_weight_for_upstream(self):
        """Should return UPSTREAM weight for 'upstream' link type."""
        result = get_link_weight("upstream")
        assert result == UPSTREAM

    def test_returns_midstream_weight_for_midstream(self):
        """Should return MIDSTREAM weight for 'midstream' link type."""
        result = get_link_weight("midstream")
        assert result == MIDSTREAM

    def test_returns_downstream_weight_for_downstream(self):
        """Should return DOWNSTREAM weight for 'downstream' link type."""
        result = get_link_weight("downstream")
        assert result == DOWNSTREAM

    def test_returns_default_for_unknown_link_type(self):
        """Should return 0.0 for unknown link type."""
        result = get_link_weight("unknown")
        assert result == 0.0

    def test_case_insensitive_link_type(self):
        """Should handle link types case-insensitively."""
        assert get_link_weight("UPSTREAM") == UPSTREAM
        assert get_link_weight("Midstream") == MIDSTREAM
        assert get_link_weight("Downstream") == DOWNSTREAM


class TestCalculateRelativeRank:
    """Tests for calculate_relative_rank function."""

    def test_first_stock_in_link_gets_highest_rank(self):
        """First position should have highest relative rank (near 1.0)."""
        stocks_in_link = [
            {"code": "stock1"},
            {"code": "stock2"},
            {"code": "stock3"},
        ]
        # First stock should have highest rank
        rank = calculate_relative_rank(stocks_in_link, "stock1")
        assert rank > calculate_relative_rank(stocks_in_link, "stock2")

    def test_last_stock_in_link_gets_lowest_rank(self):
        """Last position should have lowest relative rank (near 0.0)."""
        stocks_in_link = [
            {"code": "stock1"},
            {"code": "stock2"},
            {"code": "stock3"},
        ]
        rank = calculate_relative_rank(stocks_in_link, "stock3")
        assert rank < calculate_relative_rank(stocks_in_link, "stock2")

    def test_single_stock_gets_perfect_score(self):
        """Single stock in link should get 1.0."""
        stocks_in_link = [{"code": "only_stock"}]
        rank = calculate_relative_rank(stocks_in_link, "only_stock")
        assert rank == 1.0

    def test_missing_stock_returns_zero(self):
        """Stock not in list should return 0.0."""
        stocks_in_link = [{"code": "stock1"}, {"code": "stock2"}]
        rank = calculate_relative_rank(stocks_in_link, "nonexistent")
        assert rank == 0.0

    def test_equal_ranks_for_equal_position(self):
        """Stocks at same position should have same rank."""
        stocks_in_link = [
            {"code": "a"},
            {"code": "b"},
            {"code": "c"},
        ]
        rank_a = calculate_relative_rank(stocks_in_link, "a")
        rank_c = calculate_relative_rank(stocks_in_link, "c")
        # Rank should be linear, so stock c's rank should be significantly lower
        assert rank_a != rank_c

    def test_empty_link_returns_zero(self):
        """Empty link should return 0.0."""
        rank = calculate_relative_rank([], "any_stock")
        assert rank == 0.0


class TestCalculateChainPositionScore:
    """Tests for calculate_chain_position_score function."""

    def test_upstream_with_high_rank_gives_high_score(self):
        """UPSTREAM with rank 1.0 should give max score."""
        score = calculate_chain_position_score(UPSTREAM, 1.0)
        assert score == UPSTREAM  # 1.0 * 1.0

    def test_midstream_with_high_rank_gives_correct_score(self):
        """MIDSTREAM with rank 1.0 should give 0.7."""
        score = calculate_chain_position_score(MIDSTREAM, 1.0)
        assert score == MIDSTREAM  # 0.7 * 1.0

    def test_downstream_with_high_rank_gives_correct_score(self):
        """DOWNSTREAM with rank 1.0 should give 0.5."""
        score = calculate_chain_position_score(DOWNSTREAM, 1.0)
        assert score == DOWNSTREAM  # 0.5 * 1.0

    def test_half_rank_gives_half_score(self):
        """Half rank should give half score."""
        score = calculate_chain_position_score(1.0, 0.5)
        assert score == 0.5

    def test_zero_rank_gives_zero_score(self):
        """Zero rank should give zero score."""
        score = calculate_chain_position_score(UPSTREAM, 0.0)
        assert score == 0.0

    def test_combines_weights_correctly(self):
        """Link weight and relative rank should multiply."""
        # UPSTREAM (1.0) with rank 0.8
        score = calculate_chain_position_score(UPSTREAM, 0.8)
        assert score == 0.8

        # MIDSTREAM (0.7) with rank 0.5
        score = calculate_chain_position_score(MIDSTREAM, 0.5)
        assert score == 0.35


class TestScoreChainPositions:
    """Tests for score_chain_positions function."""

    def test_scores_all_stocks_in_chain(self):
        """Should score all stocks across all links."""
        chain_data = {
            "upstream": [
                {"code": "u1", "name": "Upstream Stock 1"},
                {"code": "u2", "name": "Upstream Stock 2"},
            ],
            "midstream": [
                {"code": "m1", "name": "Midstream Stock 1"},
            ],
            "downstream": [
                {"code": "d1", "name": "Downstream Stock 1"},
            ],
        }
        result = score_chain_positions(chain_data)

        assert len(result) == 4
        codes = [s["code"] for s in result]
        assert "u1" in codes
        assert "u2" in codes
        assert "m1" in codes
        assert "d1" in codes

    def test_adds_score_field_to_each_stock(self):
        """Should add score field to each stock dict."""
        chain_data = {
            "upstream": [{"code": "u1", "name": "Upstream"}],
            "midstream": [],
            "downstream": [],
        }
        result = score_chain_positions(chain_data)

        assert "score" in result[0]
        assert isinstance(result[0]["score"], float)

    def test_upstream_stocks_ranked_higher_than_midstream(self):
        """Upstream stocks should generally score higher than midstream."""
        chain_data = {
            "upstream": [
                {"code": "u1", "name": "Upstream"},
            ],
            "midstream": [
                {"code": "m1", "name": "Midstream"},
            ],
            "downstream": [
                {"code": "d1", "name": "Downstream"},
            ],
        }
        result = score_chain_positions(chain_data)

        # Find scores for each
        u1_score = next(s["score"] for s in result if s["code"] == "u1")
        m1_score = next(s["score"] for s in result if s["code"] == "m1")
        d1_score = next(s["score"] for s in result if s["code"] == "d1")

        assert u1_score > m1_score
        assert m1_score > d1_score

    def test_sorts_by_score_descending(self):
        """Should return stocks sorted by score descending."""
        chain_data = {
            "upstream": [
                {"code": "u1", "name": "Upstream 1"},
                {"code": "u2", "name": "Upstream 2"},
            ],
            "midstream": [
                {"code": "m1", "name": "Midstream 1"},
            ],
            "downstream": [],
        }
        result = score_chain_positions(chain_data)

        scores = [s["score"] for s in result]
        assert scores == sorted(scores, reverse=True)

    def test_empty_chain_returns_empty_list(self):
        """Empty chain should return empty list."""
        chain_data = {
            "upstream": [],
            "midstream": [],
            "downstream": [],
        }
        result = score_chain_positions(chain_data)
        assert result == []

    def test_missing_link_type_handled(self):
        """Should handle missing link types gracefully."""
        chain_data = {
            "upstream": [{"code": "u1", "name": "Upstream"}],
            # midstream and downstream missing
        }
        result = score_chain_positions(chain_data)
        assert len(result) == 1
        assert result[0]["code"] == "u1"

    def test_preserves_original_stock_data(self):
        """Should preserve original stock data fields."""
        chain_data = {
            "upstream": [{"code": "u1", "name": "Test Stock", "price": 100}],
            "midstream": [],
            "downstream": [],
        }
        result = score_chain_positions(chain_data)

        assert result[0]["code"] == "u1"
        assert result[0]["name"] == "Test Stock"
        assert result[0]["price"] == 100
        assert "link_type" in result[0]

    def test_adds_link_type_field(self):
        """Should add link_type field to each stock."""
        chain_data = {
            "upstream": [{"code": "u1", "name": "Upstream"}],
            "midstream": [{"code": "m1", "name": "Midstream"}],
            "downstream": [{"code": "d1", "name": "Downstream"}],
        }
        result = score_chain_positions(chain_data)

        for stock in result:
            assert "link_type" in stock


class TestChainScorerClass:
    """Tests for ChainScorer class."""

    def test_scorer_has_default_weights(self):
        """Should initialize with default link weights."""
        scorer = ChainScorer()
        assert scorer.upstream_weight == UPSTREAM
        assert scorer.midstream_weight == MIDSTREAM
        assert scorer.downstream_weight == DOWNSTREAM

    def test_scorer_accepts_custom_weights(self):
        """Should accept custom weights."""
        scorer = ChainScorer(
            upstream_weight=1.5,
            midstream_weight=1.0,
            downstream_weight=0.6
        )
        assert scorer.upstream_weight == 1.5
        assert scorer.midstream_weight == 1.0
        assert scorer.downstream_weight == 0.6

    def test_scorer_get_link_weight_method(self):
        """Should return correct weight for link type."""
        scorer = ChainScorer()
        assert scorer.get_link_weight("upstream") == UPSTREAM
        assert scorer.get_link_weight("midstream") == MIDSTREAM
        assert scorer.get_link_weight("downstream") == DOWNSTREAM

    def test_scorer_score_chain_positions_method(self):
        """Should score chain positions using instance weights."""
        scorer = ChainScorer()
        chain_data = {
            "upstream": [{"code": "u1", "name": "Upstream"}],
            "midstream": [{"code": "m1", "name": "Midstream"}],
            "downstream": [{"code": "d1", "name": "Downstream"}],
        }
        result = scorer.score_chain_positions(chain_data)
        assert len(result) == 3
