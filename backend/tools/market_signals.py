"""
Market signals stub: mock relative performance data with clear TODO markers for live feed.
Used by scorer.py market_confirmation component.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# TODO: replace MOCK_DATA with live Alpha Vantage / yfinance call before production use
MOCK_DATA: dict[str, dict] = {
    "nvda":  {"rel_perf_30d": 0.18, "momentum": "strong_bull", "vol_percentile": 72},
    "cei":   {"rel_perf_30d": 0.31, "momentum": "strong_bull", "vol_percentile": 58},
    "vrt":   {"rel_perf_30d": 0.24, "momentum": "bull",        "vol_percentile": 65},
    "etn":   {"rel_perf_30d": 0.09, "momentum": "neutral",     "vol_percentile": 41},
    "gev":   {"rel_perf_30d": 0.14, "momentum": "bull",        "vol_percentile": 53},
    "amd":   {"rel_perf_30d": 0.12, "momentum": "bull",        "vol_percentile": 68},
    "intc":  {"rel_perf_30d": -0.08,"momentum": "bear",        "vol_percentile": 55},
    "mrvl":  {"rel_perf_30d": 0.21, "momentum": "strong_bull", "vol_percentile": 70},
    "avgo":  {"rel_perf_30d": 0.16, "momentum": "bull",        "vol_percentile": 60},
    "qcom":  {"rel_perf_30d": 0.05, "momentum": "neutral",     "vol_percentile": 38},
    "mu":    {"rel_perf_30d": 0.19, "momentum": "bull",        "vol_percentile": 74},
    "asml":  {"rel_perf_30d": 0.11, "momentum": "bull",        "vol_percentile": 49},
    "amat":  {"rel_perf_30d": 0.08, "momentum": "neutral",     "vol_percentile": 44},
    "eqix":  {"rel_perf_30d": 0.07, "momentum": "neutral",     "vol_percentile": 35},
    "dlr":   {"rel_perf_30d": 0.05, "momentum": "neutral",     "vol_percentile": 32},
    "nee":   {"rel_perf_30d": 0.03, "momentum": "neutral",     "vol_percentile": 28},
    "d":     {"rel_perf_30d": -0.02,"momentum": "bear",        "vol_percentile": 25},
    "so":    {"rel_perf_30d": 0.04, "momentum": "neutral",     "vol_percentile": 30},
    "aep":   {"rel_perf_30d": 0.06, "momentum": "neutral",     "vol_percentile": 33},
    "pwr":   {"rel_perf_30d": 0.22, "momentum": "strong_bull", "vol_percentile": 62},
    "myr":   {"rel_perf_30d": 0.17, "momentum": "bull",        "vol_percentile": 55},
    "orcl":  {"rel_perf_30d": 0.13, "momentum": "bull",        "vol_percentile": 50},
    "ceg":   {"rel_perf_30d": 0.29, "momentum": "strong_bull", "vol_percentile": 66},
    "vsh":   {"rel_perf_30d": 0.10, "momentum": "neutral",     "vol_percentile": 43},
    "hubb":  {"rel_perf_30d": 0.08, "momentum": "neutral",     "vol_percentile": 40},
}

SECTOR_TICKERS: dict[str, list[str]] = {
    "semiconductors": ["nvda", "amd", "intc", "mrvl", "avgo", "qcom", "mu", "asml", "amat"],
    "data_center_infra": ["eqix", "dlr", "vrt", "etn", "gev"],
    "grid_power": ["nee", "d", "so", "aep", "pwr", "myr", "ceg"],
    "hyperscalers": ["orcl"],
    "equipment_materials": ["vsh", "hubb"],
}

MOMENTUM_SCORE: dict[str, float] = {
    "strong_bull": 1.0,
    "bull": 0.75,
    "neutral": 0.5,
    "bear": 0.25,
    "strong_bear": 0.0,
}


class MarketSignals:
    def get_relative_performance(self, ticker: str, days: int = 30) -> float:
        """Return relative performance vs SPY over `days` days.
        TODO: replace with live Alpha Vantage / yfinance call."""
        ticker = ticker.lower()
        return MOCK_DATA.get(ticker, {}).get("rel_perf_30d", 0.0)

    def get_momentum_signal(self, ticker: str) -> str:
        """Return momentum label: strong_bull | bull | neutral | bear | strong_bear."""
        ticker = ticker.lower()
        return MOCK_DATA.get(ticker, {}).get("momentum", "neutral")

    def get_sector_momentum(self, sector: str) -> dict:
        """Aggregate signals for all entities in a sector."""
        tickers = SECTOR_TICKERS.get(sector.lower(), [])
        if not tickers:
            return {"sector": sector, "avg_rel_perf": 0.0, "momentum": "neutral", "count": 0}
        perfs = [MOCK_DATA[t]["rel_perf_30d"] for t in tickers if t in MOCK_DATA]
        momentums = [MOCK_DATA[t]["momentum"] for t in tickers if t in MOCK_DATA]
        avg_perf = sum(perfs) / len(perfs) if perfs else 0.0
        dominant = max(set(momentums), key=momentums.count) if momentums else "neutral"
        return {
            "sector": sector,
            "avg_rel_perf": round(avg_perf, 4),
            "momentum": dominant,
            "count": len(perfs),
            "tickers": tickers,
        }

    def market_confirmation_score(self, entity_id: str, ticker: Optional[str] = None) -> float:
        """Return 0.0-1.0 score for scorer.py market_confirmation component.
        TODO: replace mock data with live feed before production use."""
        if ticker:
            t = ticker.lower()
            data = MOCK_DATA.get(t)
            if data:
                momentum = data["momentum"]
                rel_perf = data["rel_perf_30d"]
                base = MOMENTUM_SCORE.get(momentum, 0.5)
                # Blend momentum score with relative performance (cap at ±0.2 adjustment)
                adj = min(0.2, max(-0.2, rel_perf))
                return round(min(1.0, max(0.0, base + adj)), 4)
        return 0.5  # neutral default when no ticker data available

    def get_all_signals(self) -> list[dict]:
        """Return all mock signals for the /market/signals endpoint."""
        results = []
        for ticker, data in MOCK_DATA.items():
            results.append({
                "ticker": ticker.upper(),
                "rel_perf_30d": data["rel_perf_30d"],
                "momentum": data["momentum"],
                "vol_percentile": data["vol_percentile"],
                "market_confirmation_score": self.market_confirmation_score("", ticker),
            })
        return sorted(results, key=lambda x: -x["rel_perf_30d"])


_signals = MarketSignals()


def get_signals() -> MarketSignals:
    """Return module-level singleton MarketSignals."""
    return _signals
