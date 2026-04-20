"""Stock scorer module for calculating individual stock comprehensive scores.

Scoring formula:
综合分 = 0.4 × 技术分 + 0.3 × 基本面分 + 0.3 × 资金分

技术分 = 涨跌幅得分(25%) + 放量得分(25%) + 趋势得分(50%)
基本面分 = 业绩增速(40%) + 估值合理度(30%) + 成长性(30%)
资金分 = 主力净流入(50%) + 筹码集中度(50%)
"""
from typing import List


# Default scoring weights
DEFAULT_TECH_WEIGHT = 0.4
DEFAULT_FUNDAMENTAL_WEIGHT = 0.3
DEFAULT_CAPITAL_WEIGHT = 0.3

# Tech score sub-weights
PRICE_CHANGE_WEIGHT = 0.25
VOLUME_RATIO_WEIGHT = 0.25
TREND_WEIGHT = 0.50

# Fundamental score sub-weights
EARNINGS_GROWTH_WEIGHT = 0.40
VALUATION_WEIGHT = 0.30
GROWTH_SUB_WEIGHT = 0.30

# Capital score sub-weights
FUND_FLOW_WEIGHT = 0.50
CHIP_CONCENTRATION_WEIGHT = 0.50


def normalize_score(value: float) -> float:
    """Normalize a value to 0-100 range.

    Args:
        value: The value to normalize

    Returns:
        Normalized value clamped to 0-100 range
    """
    return max(0.0, min(100.0, value))


def calculate_price_change_score(price_change: float) -> float:
    """Calculate score based on price change percentage.

    Score mapping:
    - 0% change = 50 (baseline)
    - +5% change = 100 (max)
    - -5% change = 0 (min)
    - Linear interpolation between

    Args:
        price_change: Price change percentage (e.g., 3.0 for 3%)

    Returns:
        Score from 0-100
    """
    # Linear mapping: each 1% change = 10 points
    score = 50.0 + price_change * 10.0
    return normalize_score(score)


def calculate_volume_ratio_score(volume_ratio: float) -> float:
    """Calculate score based on volume ratio.

    Score mapping:
    - Volume ratio 1.0 = 40 (baseline)
    - Volume ratio 2.5 = 100 (max)
    - Volume ratio 0 = 0 (min)

    Args:
        volume_ratio: Volume ratio (volume / average volume)

    Returns:
        Score from 0-100
    """
    # Linear mapping: each 0.1 ratio = 4 points
    # ratio 1.0 -> 40, ratio 2.5 -> 100
    score = volume_ratio * 40.0
    return normalize_score(score)


def calculate_trend_score(trend: str) -> float:
    """Calculate score based on price trend.

    Args:
        trend: Trend direction ('up', 'down', 'neutral')

    Returns:
        Score from 0-100
    """
    trend_scores = {
        'up': 80.0,
        'down': 20.0,
        'neutral': 50.0
    }
    return trend_scores.get(trend, 50.0)


def calculate_tech_score(tech_data: dict) -> float:
    """Calculate comprehensive technical score.

    Args:
        tech_data: Dict containing:
            - price_change: Price change percentage
            - volume_ratio: Volume ratio
            - trend: Trend direction ('up', 'down', 'neutral')

    Returns:
        Technical score from 0-100
    """
    price_change = tech_data.get('price_change', 0)
    volume_ratio = tech_data.get('volume_ratio', 1)
    trend = tech_data.get('trend', 'neutral')

    price_change_score = calculate_price_change_score(price_change)
    volume_ratio_score = calculate_volume_ratio_score(volume_ratio)
    trend_score = calculate_trend_score(trend)

    # Weighted combination
    score = (
        PRICE_CHANGE_WEIGHT * price_change_score +
        VOLUME_RATIO_WEIGHT * volume_ratio_score +
        TREND_WEIGHT * trend_score
    )
    return normalize_score(score)


def calculate_earnings_growth_score(earnings_growth: float) -> float:
    """Calculate score based on earnings growth rate.

    Score mapping:
    - 0% growth = 50 (baseline)
    - 30%+ growth = 100 (max)
    - Negative growth decreases below 50

    Args:
        earnings_growth: Earnings growth rate percentage

    Returns:
        Score from 0-100
    """
    if earnings_growth >= 30:
        return 100.0
    elif earnings_growth >= 0:
        # Linear: 0% -> 50, 30% -> 100
        score = 50.0 + earnings_growth * (50.0 / 30.0)
        return normalize_score(score)
    else:
        # Negative growth: 0% -> 50, -30% -> 0
        score = 50.0 + earnings_growth * (50.0 / 30.0)
        return normalize_score(score)


def calculate_valuation_score(valuation: float) -> float:
    """Calculate score based on valuation (PE ratio).

    Score mapping:
    - PE 0 or negative = 50 (baseline)
    - PE < 20 = 80 (good value)
    - PE 20-40 = 60 (reasonable)
    - PE > 40 = decreasing score

    Args:
        valuation: PE ratio

    Returns:
        Score from 0-100
    """
    if valuation <= 0:
        return 50.0
    elif valuation < 20:
        return 80.0
    elif valuation < 40:
        return 60.0
    else:
        # Decreasing score for high PE
        score = max(20.0, 100.0 - (valuation - 40))
        return normalize_score(score)


def calculate_growth_score(growth: float) -> float:
    """Calculate score based on growth rate.

    Score mapping:
    - 0% growth = 50 (baseline)
    - 20%+ growth = 100 (max)
    - Negative growth decreases below 50

    Args:
        growth: Growth rate percentage

    Returns:
        Score from 0-100
    """
    if growth >= 20:
        return 100.0
    elif growth >= 0:
        # Linear: 0% -> 50, 20% -> 100
        score = 50.0 + growth * (50.0 / 20.0)
        return normalize_score(score)
    else:
        # Negative growth: 0% -> 50, -20% -> 0
        score = 50.0 + growth * (50.0 / 20.0)
        return normalize_score(score)


def calculate_fundamental_score(fundamental_data: dict) -> float:
    """Calculate comprehensive fundamental score.

    Args:
        fundamental_data: Dict containing:
            - earnings_growth: Earnings growth rate percentage
            - valuation: PE ratio
            - growth: Growth rate percentage

    Returns:
        Fundamental score from 0-100
    """
    earnings_growth = fundamental_data.get('earnings_growth', 0)
    valuation = fundamental_data.get('valuation', 20)
    growth = fundamental_data.get('growth', 0)

    earnings_score = calculate_earnings_growth_score(earnings_growth)
    valuation_score = calculate_valuation_score(valuation)
    growth_score = calculate_growth_score(growth)

    # Weighted combination
    score = (
        EARNINGS_GROWTH_WEIGHT * earnings_score +
        VALUATION_WEIGHT * valuation_score +
        GROWTH_SUB_WEIGHT * growth_score
    )
    return normalize_score(score)


def calculate_fund_flow_score(fund_flow: float) -> float:
    """Calculate score based on fund net inflow.

    Score mapping:
    - 0 inflow = 50 (baseline)
    - 10000 (1亿) inflow = 100 (max)
    - Negative inflow decreases below 50

    Args:
        fund_flow: Net inflow amount in 万元 (10,000 yuan)

    Returns:
        Score from 0-100
    """
    if fund_flow >= 10000:
        return 100.0
    elif fund_flow >= 0:
        # Linear: 0 -> 50, 10000 -> 100
        score = 50.0 + fund_flow * (50.0 / 10000.0)
        return normalize_score(score)
    else:
        # Negative: 0 -> 50, -1000 -> 40
        score = 50.0 + fund_flow * (50.0 / -1000.0)
        return normalize_score(score)


def calculate_chip_concentration_score(chip_concentration: float) -> float:
    """Calculate score based on chip concentration.

    Score is directly proportional to concentration percentage.

    Args:
        chip_concentration: Concentration ratio (0.0 to 1.0)

    Returns:
        Score from 0-100
    """
    return normalize_score(chip_concentration * 100.0)


def calculate_capital_score(capital_data: dict) -> float:
    """Calculate comprehensive capital score.

    Args:
        capital_data: Dict containing:
            - fund_flow: Net inflow amount in 万元
            - chip_concentration: Concentration ratio (0.0 to 1.0)

    Returns:
        Capital score from 0-100
    """
    fund_flow = capital_data.get('fund_flow', 0)
    chip_concentration = capital_data.get('chip_concentration', 0.5)

    fund_flow_score = calculate_fund_flow_score(fund_flow)
    chip_score = calculate_chip_concentration_score(chip_concentration)

    # Weighted combination
    score = (
        FUND_FLOW_WEIGHT * fund_flow_score +
        CHIP_CONCENTRATION_WEIGHT * chip_score
    )
    return normalize_score(score)


def calculate_comprehensive_score(
    tech_score: float,
    fundamental_score: float,
    capital_score: float,
    tech_weight: float = DEFAULT_TECH_WEIGHT,
    fundamental_weight: float = DEFAULT_FUNDAMENTAL_WEIGHT,
    capital_weight: float = DEFAULT_CAPITAL_WEIGHT
) -> float:
    """Calculate comprehensive stock score.

    Args:
        tech_score: Technical score (0-100)
        fundamental_score: Fundamental score (0-100)
        capital_score: Capital score (0-100)
        tech_weight: Weight for technical score (default 0.4)
        fundamental_weight: Weight for fundamental score (default 0.3)
        capital_weight: Weight for capital score (default 0.3)

    Returns:
        Comprehensive score from 0-100
    """
    score = (
        tech_weight * tech_score +
        fundamental_weight * fundamental_score +
        capital_weight * capital_score
    )
    return normalize_score(score)


def score_stocks(stocks: List[dict], top_n: int = None) -> List[dict]:
    """Score and sort stocks by comprehensive score.

    Args:
        stocks: List of stock dicts with fields:
            - code: Stock code
            - name: Stock name
            - price_change: Price change percentage
            - volume_ratio: Volume ratio
            - trend: Trend direction ('up', 'down', 'neutral')
            - earnings_growth: Earnings growth rate percentage
            - valuation: PE ratio
            - growth: Growth rate percentage
            - fund_flow: Net inflow amount in 万元
            - chip_concentration: Concentration ratio (0.0 to 1.0)
        top_n: Number of top stocks to return (default all)

    Returns:
        List of stocks sorted by comprehensive score descending,
        each with score fields added
    """
    if not stocks:
        return []

    scored_stocks = []
    for stock in stocks:
        # Extract technical data
        tech_data = {
            'price_change': stock.get('price_change', 0),
            'volume_ratio': stock.get('volume_ratio', 1),
            'trend': stock.get('trend', 'neutral')
        }

        # Extract fundamental data
        fundamental_data = {
            'earnings_growth': stock.get('earnings_growth', 0),
            'valuation': stock.get('valuation', 20),
            'growth': stock.get('growth', 0)
        }

        # Extract capital data
        capital_data = {
            'fund_flow': stock.get('fund_flow', 0),
            'chip_concentration': stock.get('chip_concentration', 0.5)
        }

        # Calculate scores
        tech_score = calculate_tech_score(tech_data)
        fundamental_score = calculate_fundamental_score(fundamental_data)
        capital_score = calculate_capital_score(capital_data)
        comprehensive_score = calculate_comprehensive_score(
            tech_score, fundamental_score, capital_score
        )

        # Create new dict with scores added (immutability)
        scored_stock = {
            **stock,
            'tech_score': tech_score,
            'fundamental_score': fundamental_score,
            'capital_score': capital_score,
            'comprehensive_score': comprehensive_score
        }
        scored_stocks.append(scored_stock)

    # Sort by comprehensive score descending
    scored_stocks.sort(key=lambda s: s.get('comprehensive_score', 0), reverse=True)

    # Limit to top_n if specified
    if top_n is not None:
        scored_stocks = scored_stocks[:top_n]

    return scored_stocks


class StockScorer:
    """Stock scorer class for calculating individual stock comprehensive scores."""

    def __init__(
        self,
        tech_weight: float = DEFAULT_TECH_WEIGHT,
        fundamental_weight: float = DEFAULT_FUNDAMENTAL_WEIGHT,
        capital_weight: float = DEFAULT_CAPITAL_WEIGHT
    ):
        """Initialize scorer with weights.

        Args:
            tech_weight: Weight for technical score (default 0.4)
            fundamental_weight: Weight for fundamental score (default 0.3)
            capital_weight: Weight for capital score (default 0.3)
        """
        self.tech_weight = tech_weight
        self.fundamental_weight = fundamental_weight
        self.capital_weight = capital_weight

    def calculate_tech(self, tech_data: dict) -> float:
        """Calculate technical score.

        Args:
            tech_data: Dict containing price_change, volume_ratio, trend

        Returns:
            Technical score (0-100)
        """
        return calculate_tech_score(tech_data)

    def calculate_fundamental(self, fundamental_data: dict) -> float:
        """Calculate fundamental score.

        Args:
            fundamental_data: Dict containing earnings_growth, valuation, growth

        Returns:
            Fundamental score (0-100)
        """
        return calculate_fundamental_score(fundamental_data)

    def calculate_capital(self, capital_data: dict) -> float:
        """Calculate capital score.

        Args:
            capital_data: Dict containing fund_flow, chip_concentration

        Returns:
            Capital score (0-100)
        """
        return calculate_capital_score(capital_data)

    def calculate_comprehensive(
        self,
        tech_score: float,
        fundamental_score: float,
        capital_score: float
    ) -> float:
        """Calculate comprehensive score using instance weights.

        Args:
            tech_score: Technical score (0-100)
            fundamental_score: Fundamental score (0-100)
            capital_score: Capital score (0-100)

        Returns:
            Comprehensive score (0-100)
        """
        return calculate_comprehensive_score(
            tech_score, fundamental_score, capital_score,
            self.tech_weight, self.fundamental_weight, self.capital_weight
        )

    def score_stocks(self, stocks: List[dict], top_n: int = None) -> List[dict]:
        """Score and sort stocks using instance weights.

        Args:
            stocks: List of stock dicts
            top_n: Number of top stocks to return

        Returns:
            List of stocks sorted by comprehensive score descending
        """
        if not stocks:
            return []

        scored_stocks = []
        for stock in stocks:
            # Extract technical data
            tech_data = {
                'price_change': stock.get('price_change', 0),
                'volume_ratio': stock.get('volume_ratio', 1),
                'trend': stock.get('trend', 'neutral')
            }

            # Extract fundamental data
            fundamental_data = {
                'earnings_growth': stock.get('earnings_growth', 0),
                'valuation': stock.get('valuation', 20),
                'growth': stock.get('growth', 0)
            }

            # Extract capital data
            capital_data = {
                'fund_flow': stock.get('fund_flow', 0),
                'chip_concentration': stock.get('chip_concentration', 0.5)
            }

            # Calculate scores
            tech_score = calculate_tech_score(tech_data)
            fundamental_score = calculate_fundamental_score(fundamental_data)
            capital_score = calculate_capital_score(capital_data)
            comprehensive_score = self.calculate_comprehensive(
                tech_score, fundamental_score, capital_score
            )

            # Create new dict with scores added (immutability)
            scored_stock = {
                **stock,
                'tech_score': tech_score,
                'fundamental_score': fundamental_score,
                'capital_score': capital_score,
                'comprehensive_score': comprehensive_score
            }
            scored_stocks.append(scored_stock)

        # Sort by comprehensive score descending
        scored_stocks.sort(key=lambda s: s.get('comprehensive_score', 0), reverse=True)

        # Limit to top_n if specified
        if top_n is not None:
            scored_stocks = scored_stocks[:top_n]

        return scored_stocks
