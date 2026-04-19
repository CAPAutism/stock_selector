"""Tests for sector scorer module."""
import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scorers.sector_scorer import (
    normalize_to_score,
    calculate_fund_flow_score,
    calculate_heat_score,
    calculate_sector_score,
    score_sectors,
    SectorScorer,
)


class TestNormalizeToScore:
    """Tests for normalize_to_score function."""

    def test_normalizes_value_within_range(self):
        """Value within min/max should scale to 0-100."""
        result = normalize_to_score(50, min_val=0, max_val=100)
        assert result == 50.0

    def test_normalizes_value_at_minimum(self):
        """Value at minimum should return 0."""
        result = normalize_to_score(0, min_val=0, max_val=100)
        assert result == 0.0

    def test_normalizes_value_at_maximum(self):
        """Value at maximum should return 100."""
        result = normalize_to_score(100, min_val=0, max_val=100)
        assert result == 100.0

    def test_normalizes_value_below_minimum(self):
        """Value below minimum should return 0."""
        result = normalize_to_score(-10, min_val=0, max_val=100)
        assert result == 0.0

    def test_normalizes_value_above_maximum(self):
        """Value above maximum should return 100."""
        result = normalize_to_score(150, min_val=0, max_val=100)
        assert result == 100.0

    def test_normalizes_with_custom_min_max(self):
        """Should work with custom min/max values."""
        result = normalize_to_score(50, min_val=0, max_val=50)
        assert result == 100.0

    def test_normalizes_negative_range(self):
        """Should handle negative ranges correctly."""
        result = normalize_to_score(75, min_val=50, max_val=100)
        assert result == 50.0


class TestCalculateFundFlowScore:
    """Tests for calculate_fund_flow_score function."""

    def test_rank_1_returns_100(self):
        """Rank 1 should return maximum score of 100."""
        result = calculate_fund_flow_score(1)
        assert result == 100.0

    def test_rank_2_returns_high_score(self):
        """Rank 2 should return a high score."""
        result = calculate_fund_flow_score(2)
        assert 90 < result < 100

    def test_higher_rank_returns_lower_score(self):
        """Higher rank numbers should return lower scores."""
        score_1 = calculate_fund_flow_score(1)
        score_10 = calculate_fund_flow_score(10)
        assert score_1 > score_10

    def test_linear_decay_across_ranks(self):
        """Scores should decay linearly with rank."""
        score_1 = calculate_fund_flow_score(1)
        score_2 = calculate_fund_flow_score(2)
        score_3 = calculate_fund_flow_score(3)
        decay_1_to_2 = score_1 - score_2
        decay_2_to_3 = score_2 - score_3
        assert abs(decay_1_to_2 - decay_2_to_3) < 0.01

    def test_rank_0_or_negative_returns_0(self):
        """Invalid rank (0 or negative) should return 0."""
        assert calculate_fund_flow_score(0) == 0.0
        assert calculate_fund_flow_score(-1) == 0.0


class TestCalculateHeatScore:
    """Tests for calculate_heat_score function."""

    def test_heat_value_0_returns_0(self):
        """Heat value of 0 should return 0."""
        result = calculate_heat_score(0)
        assert result == 0.0

    def test_heat_value_100_returns_100(self):
        """Heat value of 100 should return 100."""
        result = calculate_heat_score(100)
        assert result == 100.0

    def test_heat_value_within_range(self):
        """Heat value within 0-100 should return same value."""
        result = calculate_heat_score(50)
        assert result == 50.0

    def test_heat_value_above_100_capped_at_100(self):
        """Heat value above 100 should be capped at 100."""
        result = calculate_heat_score(200)
        assert result == 100.0

    def test_heat_value_below_0_returns_0(self):
        """Negative heat value should return 0."""
        result = calculate_heat_score(-50)
        assert result == 0.0


class TestCalculateSectorScore:
    """Tests for calculate_sector_score function."""

    def test_combines_scores_with_default_weights(self):
        """Should combine fund_flow (60%) and heat (40%) scores."""
        result = calculate_sector_score(80.0, 60.0)
        expected = 0.6 * 80.0 + 0.4 * 60.0
        assert result == expected

    def test_combines_scores_with_custom_weights(self):
        """Should accept custom weights for fund_flow and heat."""
        result = calculate_sector_score(50.0, 50.0, fund_flow_weight=0.7, heat_weight=0.3)
        expected = 0.7 * 50.0 + 0.3 * 50.0
        assert result == expected

    def test_weights_sum_to_1(self):
        """Custom weights should still sum to approximately 1."""
        result = calculate_sector_score(100.0, 0.0, fund_flow_weight=0.8, heat_weight=0.2)
        assert result == 80.0

    def test_zero_fund_flow_only_heat(self):
        """Zero fund_flow should return only heat contribution."""
        result = calculate_sector_score(0.0, 50.0, fund_flow_weight=0.6, heat_weight=0.4)
        assert result == 20.0

    def test_zero_heat_only_fund_flow(self):
        """Zero heat should return only fund_flow contribution."""
        result = calculate_sector_score(100.0, 0.0, fund_flow_weight=0.6, heat_weight=0.4)
        assert result == 60.0


class TestScoreSectors:
    """Tests for score_sectors function."""

    def test_sorts_sectors_by_score_descending(self):
        """Should return sectors sorted by score in descending order."""
        sectors = [
            {"name": "sector_a", "fund_flow_rank": 3, "heat_value": 30},
            {"name": "sector_b", "fund_flow_rank": 1, "heat_value": 80},
            {"name": "sector_c", "fund_flow_rank": 2, "heat_value": 50},
        ]
        result = score_sectors(sectors)

        assert result[0]["name"] == "sector_b"
        assert result[1]["name"] == "sector_c"
        assert result[2]["name"] == "sector_a"

    def test_adds_score_field_to_each_sector(self):
        """Should add score field to each sector dict."""
        sectors = [
            {"name": "test", "fund_flow_rank": 1, "heat_value": 100},
        ]
        result = score_sectors(sectors)

        assert "score" in result[0]
        assert isinstance(result[0]["score"], float)

    def test_returns_empty_list_for_empty_input(self):
        """Should return empty list when input is empty."""
        result = score_sectors([])
        assert result == []

    def test_handles_single_sector(self):
        """Should handle single sector correctly."""
        sectors = [{"name": "only", "fund_flow_rank": 5, "heat_value": 50}]
        result = score_sectors(sectors)

        assert len(result) == 1
        assert result[0]["name"] == "only"
        assert "score" in result[0]

    def test_equal_scores_maintain_stable_order(self):
        """Sectors with equal scores should maintain relative order."""
        sectors = [
            {"name": "first", "fund_flow_rank": 100, "heat_value": 100},
            {"name": "second", "fund_flow_rank": 100, "heat_value": 100},
        ]
        result = score_sectors(sectors)

        # Both should have same score
        assert result[0]["score"] == result[1]["score"]

    def test_calculates_correct_score_values(self):
        """Should calculate correct combined scores."""
        sectors = [
            {"name": "top", "fund_flow_rank": 1, "heat_value": 100},
        ]
        result = score_sectors(sectors)

        # fund_flow_score for rank 1 = 100
        # heat_score for 100 = 100
        # sector_score = 0.6 * 100 + 0.4 * 100 = 100
        assert result[0]["score"] == 100.0


class TestSectorScorerClass:
    """Tests for SectorScorer class."""

    def test_scorer_initializes_with_default_weights(self):
        """Should initialize with default weights 0.6 and 0.4."""
        scorer = SectorScorer()
        assert scorer.fund_flow_weight == 0.6
        assert scorer.heat_weight == 0.4

    def test_scorer_accepts_custom_weights(self):
        """Should accept custom weights."""
        scorer = SectorScorer(fund_flow_weight=0.7, heat_weight=0.3)
        assert scorer.fund_flow_weight == 0.7
        assert scorer.heat_weight == 0.3

    def test_scorer_score_method_uses_instance_weights(self):
        """Score method should use instance weights."""
        scorer = SectorScorer(fund_flow_weight=0.8, heat_weight=0.2)
        result = scorer.score(50.0, 50.0)

        expected = 0.8 * 50.0 + 0.2 * 50.0
        assert result == expected

    def test_scorer_can_score_sectors_list(self):
        """Should be able to score a list of sectors."""
        scorer = SectorScorer()
        sectors = [
            {"name": "test", "fund_flow_rank": 1, "heat_value": 50},
        ]
        result = scorer.score_sectors(sectors)

        assert len(result) == 1
        assert "score" in result[0]

    def test_score_sectors_with_missing_fields(self):
        """Should handle sectors with missing optional fields."""
        scorer = SectorScorer()
        sectors = [
            {"name": "incomplete", "fund_flow_rank": 5},
            {"name": "also_incomplete", "heat_value": 50},
        ]
        # Should not raise, should use defaults
        result = scorer.score_sectors(sectors)
        assert len(result) == 2
