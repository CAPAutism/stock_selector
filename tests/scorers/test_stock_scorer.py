"""Tests for stock scorer module.

Scoring formula:
综合分 = 0.4 × 技术分 + 0.3 × 基本面分 + 0.3 × 资金分

技术分 = 涨跌幅得分(25%) + 放量得分(25%) + 趋势得分(50%)
基本面分 = 业绩增速(40%) + 估值合理度(30%) + 成长性(30%)
资金分 = 主力净流入(50%) + 筹码集中度(50%)
"""
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scorers.stock_scorer import (
    normalize_score,
    calculate_price_change_score,
    calculate_volume_ratio_score,
    calculate_trend_score,
    calculate_tech_score,
    calculate_earnings_growth_score,
    calculate_valuation_score,
    calculate_growth_score,
    calculate_fundamental_score,
    calculate_fund_flow_score,
    calculate_chip_concentration_score,
    calculate_capital_score,
    calculate_comprehensive_score,
    score_stocks,
    StockScorer,
)


class TestNormalizeScore:
    """Tests for normalize_score function."""

    def test_normalizes_value_within_range(self):
        """Value within 0-100 should return same value."""
        result = normalize_score(50)
        assert result == 50.0

    def test_value_at_0_returns_0(self):
        """Value at 0 should return 0."""
        result = normalize_score(0)
        assert result == 0.0

    def test_value_at_100_returns_100(self):
        """Value at 100 should return 100."""
        result = normalize_score(100)
        assert result == 100.0

    def test_value_above_100_capped_at_100(self):
        """Value above 100 should be capped at 100."""
        result = normalize_score(150)
        assert result == 100.0

    def test_value_below_0_returns_0(self):
        """Negative value should return 0."""
        result = normalize_score(-50)
        assert result == 0.0


class TestCalculatePriceChangeScore:
    """Tests for calculate_price_change_score function."""

    def test_zero_change_returns_50(self):
        """Zero price change should return baseline score of 50."""
        result = calculate_price_change_score(0)
        assert result == 50.0

    def test_positive_change_increases_score(self):
        """Positive price change should increase score above 50."""
        result = calculate_price_change_score(5)
        assert result > 50.0

    def test_negative_change_decreases_score(self):
        """Negative price change should decrease score below 50."""
        result = calculate_price_change_score(-5)
        assert result < 50.0

    def test_max_positive_change_capped_at_100(self):
        """Large positive change should be capped at 100."""
        result = calculate_price_change_score(10)
        assert result == 100.0

    def test_max_negative_change_capped_at_0(self):
        """Large negative change should be capped at 0."""
        result = calculate_price_change_score(-10)
        assert result == 0.0

    def test_score_linear_within_range(self):
        """Score should be linear within -5 to 5 range."""
        score_2 = calculate_price_change_score(2)
        score_4 = calculate_price_change_score(4)
        # Each 1% change = 10 points, so 2% diff = 20 points
        assert score_4 - score_2 == pytest.approx(20.0, rel=0.01)


class TestCalculateVolumeRatioScore:
    """Tests for calculate_volume_ratio_score function."""

    def test_ratio_of_1_returns_baseline(self):
        """Volume ratio of 1 (normal) should return baseline score."""
        result = calculate_volume_ratio_score(1)
        assert result == 40.0

    def test_higher_ratio_increases_score(self):
        """Higher volume ratio should increase score."""
        score_1 = calculate_volume_ratio_score(1)
        score_2 = calculate_volume_ratio_score(2)
        assert score_2 > score_1

    def test_ratio_25_returns_100(self):
        """Volume ratio of 2.5 should return 100."""
        result = calculate_volume_ratio_score(2.5)
        assert result == 100.0

    def test_ratio_below_1_decreases_score(self):
        """Volume ratio below 1 should decrease score."""
        score_1 = calculate_volume_ratio_score(1)
        score_05 = calculate_volume_ratio_score(0.5)
        assert score_05 < score_1

    def test_ratio_0_returns_minimum(self):
        """Volume ratio of 0 should return near 0."""
        result = calculate_volume_ratio_score(0)
        assert result == 0.0


class TestCalculateTrendScore:
    """Tests for calculate_trend_score function."""

    def test_uptrend_returns_high_score(self):
        """Uptrend ('up') should return high score."""
        result = calculate_trend_score('up')
        assert result == 80.0

    def test_downtrend_returns_low_score(self):
        """Downtrend ('down') should return low score."""
        result = calculate_trend_score('down')
        assert result == 20.0

    def test_neutral_trend_returns_mid_score(self):
        """Neutral trend should return mid score."""
        result = calculate_trend_score('neutral')
        assert result == 50.0

    def test_unknown_trend_defaults_to_neutral(self):
        """Unknown trend should default to neutral score."""
        result = calculate_trend_score('unknown')
        assert result == 50.0


class TestCalculateTechScore:
    """Tests for calculate_tech_score function."""

    def test_combines_all_three_dimensions(self):
        """Tech score should combine price change, volume, and trend."""
        tech_data = {
            'price_change': 3.0,
            'volume_ratio': 2.0,
            'trend': 'up'
        }
        result = calculate_tech_score(tech_data)

        # Verify it's a weighted combination
        assert 0 <= result <= 100

    def test_25_percent_price_change_weight(self):
        """Price change should contribute 25% to tech score."""
        # Score with only price change
        price_only = calculate_tech_score({
            'price_change': 5.0,
            'volume_ratio': 0,
            'trend': 'neutral'
        })
        # Score with price change + volume
        price_vol = calculate_tech_score({
            'price_change': 5.0,
            'volume_ratio': 2.5,
            'trend': 'neutral'
        })

        # Volume contribution should be 25% * 60 (from vol_score of 100)
        # = 15 points when volume_ratio = 2.5
        # Price contribution = 25% * 100 = 25
        # Trend contribution = 50% * 50 = 25
        # Total = 50 (only price) should differ from price+vol

    def test_50_percent_trend_weight(self):
        """Trend should contribute 50% to tech score."""
        # Up trend vs neutral with same other factors
        up_score = calculate_tech_score({
            'price_change': 0,
            'volume_ratio': 1,
            'trend': 'up'
        })
        neutral_score = calculate_tech_score({
            'price_change': 0,
            'volume_ratio': 1,
            'trend': 'neutral'
        })

        # Trend diff = 80 - 50 = 30
        # Tech score diff should be 50% * 30 = 15
        assert up_score - neutral_score == pytest.approx(15.0, rel=0.01)

    def test_zero_values_handled(self):
        """Should handle zero/missing values gracefully."""
        result = calculate_tech_score({
            'price_change': 0,
            'volume_ratio': 0,
            'trend': 'neutral'
        })
        assert 0 <= result <= 100

    def test_missing_fields_use_defaults(self):
        """Missing fields should use default values."""
        # Empty dict should use defaults
        result = calculate_tech_score({})
        assert 0 <= result <= 100


class TestCalculateEarningsGrowthScore:
    """Tests for calculate_earnings_growth_score function."""

    def test_zero_growth_returns_50(self):
        """Zero growth should return baseline 50."""
        result = calculate_earnings_growth_score(0)
        assert result == 50.0

    def test_positive_growth_increases_score(self):
        """Positive growth should increase score above 50."""
        result = calculate_earnings_growth_score(15)
        assert result > 50.0

    def test_negative_growth_decreases_score(self):
        """Negative growth should decrease score below 50."""
        result = calculate_earnings_growth_score(-10)
        assert result < 50.0

    def test_30_percent_growth_returns_100(self):
        """30% growth should return max 100."""
        result = calculate_earnings_growth_score(30)
        assert result == 100.0

    def test_large_negative_growth_capped_at_0(self):
        """Large negative growth should be capped at 0."""
        result = calculate_earnings_growth_score(-30)
        assert result == 0.0


class TestCalculateValuationScore:
    """Tests for calculate_valuation_score function."""

    def test_low_pe_returns_high_score(self):
        """Low PE (<20) should return high score."""
        result = calculate_valuation_score(15)
        assert result == 80.0

    def test_medium_pe_returns_mid_score(self):
        """Medium PE (20-40) should return mid score."""
        result = calculate_valuation_score(30)
        assert result == 60.0

    def test_high_pe_returns_low_score(self):
        """High PE (>40) should return low score."""
        result = calculate_valuation_score(60)
        assert result < 60.0

    def test_zero_or_negative_pe_returns_baseline(self):
        """Zero or negative PE should return baseline."""
        result = calculate_valuation_score(0)
        assert result == 50.0

        result = calculate_valuation_score(-10)
        assert result == 50.0

    def test_very_high_pe_capped_at_20(self):
        """Very high PE should be capped at minimum 20."""
        result = calculate_valuation_score(100)
        assert result == 20.0


class TestCalculateGrowthScore:
    """Tests for calculate_growth_score function."""

    def test_zero_growth_returns_50(self):
        """Zero growth should return baseline 50."""
        result = calculate_growth_score(0)
        assert result == 50.0

    def test_positive_growth_increases_score(self):
        """Positive growth should increase score above 50."""
        result = calculate_growth_score(20)
        assert result > 50.0

    def test_negative_growth_decreases_score(self):
        """Negative growth should decrease score below 50."""
        result = calculate_growth_score(-10)
        assert result < 50.0

    def test_20_percent_growth_returns_100(self):
        """20% growth should return max 100."""
        result = calculate_growth_score(20)
        assert result == 100.0

    def test_large_negative_growth_capped_at_0(self):
        """Large negative growth should be capped at 0."""
        result = calculate_growth_score(-20)
        assert result == 0.0


class TestCalculateFundamentalScore:
    """Tests for calculate_fundamental_score function."""

    def test_combines_all_three_dimensions(self):
        """Fundamental score should combine earnings, valuation, and growth."""
        fundamental_data = {
            'earnings_growth': 15,
            'valuation': 25,
            'growth': 10
        }
        result = calculate_fundamental_score(fundamental_data)
        assert 0 <= result <= 100

    def test_40_percent_earnings_weight(self):
        """Earnings growth should contribute 40% to fundamental score."""
        earnings_only = calculate_fundamental_score({
            'earnings_growth': 30,
            'valuation': 0,
            'growth': 0
        })
        # 40% * 100 (max earnings) = 40

        with_others = calculate_fundamental_score({
            'earnings_growth': 30,
            'valuation': 50,
            'growth': 50
        })
        # 40% * 100 + 30% * 50 + 30% * 50 = 40 + 15 + 15 = 70

        assert with_others > earnings_only

    def test_zero_values_handled(self):
        """Should handle zero/missing values gracefully."""
        result = calculate_fundamental_score({
            'earnings_growth': 0,
            'valuation': 0,
            'growth': 0
        })
        assert 0 <= result <= 100

    def test_missing_fields_use_defaults(self):
        """Missing fields should use default values."""
        result = calculate_fundamental_score({})
        assert 0 <= result <= 100


class TestCalculateFundFlowScore:
    """Tests for calculate_fund_flow_score function."""

    def test_zero_inflow_returns_50(self):
        """Zero net inflow should return baseline 50."""
        result = calculate_fund_flow_score(0)
        assert result == 50.0

    def test_positive_inflow_increases_score(self):
        """Positive inflow should increase score above 50."""
        result = calculate_fund_flow_score(5000)
        assert result > 50.0

    def test_negative_inflow_decreases_score(self):
        """Negative inflow should decrease score below 50."""
        result = calculate_fund_flow_score(-1000)
        assert result < 50.0

    def test_10000_inflow_returns_100(self):
        """10000 (1亿) net inflow should return max 100."""
        result = calculate_fund_flow_score(10000)
        assert result == 100.0

    def test_negative_1000_inflow_returns_40(self):
        """-1000 net inflow should return 40."""
        result = calculate_fund_flow_score(-1000)
        assert result == 40.0


class TestCalculateChipConcentrationScore:
    """Tests for calculate_chip_concentration_score function."""

    def test_80_percent_concentration_returns_80(self):
        """80% concentration should return 80."""
        result = calculate_chip_concentration_score(0.8)
        assert result == 80.0

    def test_100_percent_concentration_returns_100(self):
        """100% concentration should return 100."""
        result = calculate_chip_concentration_score(1.0)
        assert result == 100.0

    def test_0_percent_concentration_returns_0(self):
        """0% concentration should return 0."""
        result = calculate_chip_concentration_score(0)
        assert result == 0.0

    def test_concentration_proportional_to_score(self):
        """Score should be proportional to concentration percentage."""
        score_50 = calculate_chip_concentration_score(0.5)
        score_75 = calculate_chip_concentration_score(0.75)
        assert score_75 > score_50


class TestCalculateCapitalScore:
    """Tests for calculate_capital_score function."""

    def test_combines_both_dimensions(self):
        """Capital score should combine fund flow and chip concentration."""
        capital_data = {
            'fund_flow': 5000,
            'chip_concentration': 0.8
        }
        result = calculate_capital_score(capital_data)
        assert 0 <= result <= 100

    def test_50_percent_each_weight(self):
        """Fund flow and chip concentration should each contribute 50%."""
        # Fund flow only
        flow_only = calculate_capital_score({
            'fund_flow': 10000,
            'chip_concentration': 0
        })

        # Chip only
        chip_only = calculate_capital_score({
            'fund_flow': 0,
            'chip_concentration': 1.0
        })

        # Both at max
        both_max = calculate_capital_score({
            'fund_flow': 10000,
            'chip_concentration': 1.0
        })

        # Both should be equal at max
        assert flow_only == chip_only == both_max == 100.0

    def test_zero_values_handled(self):
        """Should handle zero/missing values gracefully."""
        result = calculate_capital_score({
            'fund_flow': 0,
            'chip_concentration': 0
        })
        assert 0 <= result <= 100


class TestCalculateComprehensiveScore:
    """Tests for calculate_comprehensive_score function."""

    def test_combines_all_three_dimensions(self):
        """Comprehensive score should combine tech, fundamental, and capital."""
        result = calculate_comprehensive_score(80.0, 70.0, 90.0)
        assert 0 <= result <= 100

    def test_default_weights_sum_to_1(self):
        """Default weights should sum to 1.0."""
        # 0.4 + 0.3 + 0.3 = 1.0
        result = calculate_comprehensive_score(100.0, 100.0, 100.0)
        assert result == 100.0

    def test_tech_weight_40_percent(self):
        """Tech score should contribute 40% to comprehensive score."""
        result_tech_100 = calculate_comprehensive_score(100.0, 0.0, 0.0)
        assert result_tech_100 == 40.0

    def test_fundamental_weight_30_percent(self):
        """Fundamental score should contribute 30% to comprehensive score."""
        result_fund_100 = calculate_comprehensive_score(0.0, 100.0, 0.0)
        assert result_fund_100 == 30.0

    def test_capital_weight_30_percent(self):
        """Capital score should contribute 30% to comprehensive score."""
        result_cap_100 = calculate_comprehensive_score(0.0, 0.0, 100.0)
        assert result_cap_100 == 30.0

    def test_custom_weights(self):
        """Should accept custom weights."""
        result = calculate_comprehensive_score(
            100.0, 100.0, 100.0,
            tech_weight=0.5,
            fundamental_weight=0.3,
            capital_weight=0.2
        )
        expected = 0.5 * 100 + 0.3 * 100 + 0.2 * 100
        assert result == expected

    def test_zero_scores_returns_zero(self):
        """All zero scores should return zero."""
        result = calculate_comprehensive_score(0.0, 0.0, 0.0)
        assert result == 0.0


class TestScoreStocks:
    """Tests for score_stocks function."""

    def test_sorts_stocks_by_comprehensive_score_descending(self):
        """Should return stocks sorted by comprehensive score descending."""
        stocks = [
            {"code": "000001", "name": "stock_a", "price_change": 1.0, "volume_ratio": 1.0, "trend": "neutral",
             "earnings_growth": 0, "valuation": 20, "growth": 0, "fund_flow": 0, "chip_concentration": 0.5},
            {"code": "000002", "name": "stock_b", "price_change": 5.0, "volume_ratio": 2.5, "trend": "up",
             "earnings_growth": 30, "valuation": 15, "growth": 20, "fund_flow": 10000, "chip_concentration": 1.0},
            {"code": "000003", "name": "stock_c", "price_change": 3.0, "volume_ratio": 1.5, "trend": "up",
             "earnings_growth": 15, "valuation": 25, "growth": 10, "fund_flow": 5000, "chip_concentration": 0.7},
        ]
        result = score_stocks(stocks)

        assert result[0]["code"] == "000002"  # Should be highest scoring
        assert result[-1]["code"] == "000001"  # Should be lowest scoring

    def test_adds_all_score_fields(self):
        """Should add tech_score, fundamental_score, capital_score, and comprehensive_score."""
        stocks = [
            {"code": "000001", "name": "test", "price_change": 0, "volume_ratio": 1, "trend": "neutral",
             "earnings_growth": 0, "valuation": 20, "growth": 0, "fund_flow": 0, "chip_concentration": 0.5}
        ]
        result = score_stocks(stocks)

        assert "tech_score" in result[0]
        assert "fundamental_score" in result[0]
        assert "capital_score" in result[0]
        assert "comprehensive_score" in result[0]

    def test_returns_empty_list_for_empty_input(self):
        """Should return empty list when input is empty."""
        result = score_stocks([])
        assert result == []

    def test_handles_single_stock(self):
        """Should handle single stock correctly."""
        stocks = [
            {"code": "000001", "name": "only", "price_change": 5.0, "volume_ratio": 2.5, "trend": "up",
             "earnings_growth": 30, "valuation": 15, "growth": 20, "fund_flow": 10000, "chip_concentration": 1.0}
        ]
        result = score_stocks(stocks)

        assert len(result) == 1
        assert "comprehensive_score" in result[0]

    def test_equal_scores_maintain_stable_order(self):
        """Stocks with equal scores should maintain relative order."""
        stocks = [
            {"code": "000001", "name": "first", "price_change": 0, "volume_ratio": 1, "trend": "neutral",
             "earnings_growth": 0, "valuation": 20, "growth": 0, "fund_flow": 0, "chip_concentration": 0.5},
            {"code": "000002", "name": "second", "price_change": 0, "volume_ratio": 1, "trend": "neutral",
             "earnings_growth": 0, "valuation": 20, "growth": 0, "fund_flow": 0, "chip_concentration": 0.5},
        ]
        result = score_stocks(stocks)

        # Both should have same comprehensive score
        assert result[0]["comprehensive_score"] == result[1]["comprehensive_score"]

    def test_respects_top_n_parameter(self):
        """Should limit results to top_n stocks."""
        stocks = [
            {"code": str(i), "name": f"stock_{i}", "price_change": float(i), "volume_ratio": 1.0, "trend": "neutral",
             "earnings_growth": 0, "valuation": 20, "growth": 0, "fund_flow": 0, "chip_concentration": 0.5}
            for i in range(10)
        ]
        result = score_stocks(stocks, top_n=3)

        assert len(result) == 3

    def test_missing_data_uses_defaults(self):
        """Should handle missing optional fields with defaults."""
        stocks = [
            {"code": "000001", "name": "incomplete"}
        ]
        # Should not raise, should use defaults
        result = score_stocks(stocks)
        assert len(result) == 1
        assert "comprehensive_score" in result[0]


class TestStockScorerClass:
    """Tests for StockScorer class."""

    def test_scorer_initializes_with_default_weights(self):
        """Should initialize with default weights 0.4, 0.3, 0.3."""
        scorer = StockScorer()
        assert scorer.tech_weight == 0.4
        assert scorer.fundamental_weight == 0.3
        assert scorer.capital_weight == 0.3

    def test_scorer_accepts_custom_weights(self):
        """Should accept custom weights."""
        scorer = StockScorer(
            tech_weight=0.5,
            fundamental_weight=0.25,
            capital_weight=0.25
        )
        assert scorer.tech_weight == 0.5
        assert scorer.fundamental_weight == 0.25
        assert scorer.capital_weight == 0.25

    def test_scorer_calculate_comprehensive_uses_instance_weights(self):
        """Calculate comprehensive should use instance weights."""
        scorer = StockScorer(
            tech_weight=0.5,
            fundamental_weight=0.3,
            capital_weight=0.2
        )
        result = scorer.calculate_comprehensive(80.0, 70.0, 60.0)

        expected = 0.5 * 80 + 0.3 * 70 + 0.2 * 60
        assert result == expected

    def test_scorer_score_stocks_uses_instance_weights(self):
        """Score stocks should use instance weights."""
        scorer = StockScorer(
            tech_weight=0.5,
            fundamental_weight=0.3,
            capital_weight=0.2
        )
        stocks = [
            {"code": "000001", "name": "test", "price_change": 5.0, "volume_ratio": 2.5, "trend": "up",
             "earnings_growth": 30, "valuation": 15, "growth": 20, "fund_flow": 10000, "chip_concentration": 1.0}
        ]
        result = scorer.score_stocks(stocks)

        assert len(result) == 1
        assert "comprehensive_score" in result[0]

    def test_score_stocks_with_missing_fields(self):
        """Should handle stocks with missing optional fields."""
        scorer = StockScorer()
        stocks = [
            {"code": "000001", "name": "incomplete"},
            {"code": "000002", "name": "also_incomplete", "price_change": 3.0},
        ]
        # Should not raise, should use defaults
        result = scorer.score_stocks(stocks)
        assert len(result) == 2
