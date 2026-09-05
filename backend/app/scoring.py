"""
Meaningful Change Score (MCS)
=============================
A raw "% change" number treats a 2% move in a sleepy PSU bank the same as
a 2% move in a small-cap that trades that much noise every day. MCS asks
instead: "relative to how *this* stock normally behaves, is today's move
actually unusual, and is anything corroborating it?"

Four signals, each squashed to [0, 1], combined into one 0-100 score:

  1. volatility_z   - is |% change| large vs this stock's own trailing
                       daily volatility? (statistical surprise)
  2. volume_ratio    - is volume unusually high vs its trailing average?
                       (corroborating interest / conviction)
  3. proximity_52w   - is the move pushing the stock towards/through a
                       52-week high or low? (breakout relevance)
  4. index_divergence- is the stock moving differently from the index,
                       i.e. is this idiosyncratic rather than "everything
                       moved because the market moved"?

Weights are deliberately simple and documented (not hidden in a model) so
the score stays explainable - "responsible" and "transparent" over
"clever". A human can recompute this on a napkin.
"""
from dataclasses import dataclass
from typing import Optional

WEIGHTS = {
    "volatility_z": 0.35,
    "volume_ratio": 0.25,
    "proximity_52w": 0.20,
    "index_divergence": 0.20,
}


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass
class ScoreInputs:
    pct_change: float                 # today's % change
    trailing_daily_std_pct: float      # stdev of daily % changes, last ~20d
    volume: float
    trailing_avg_volume: float
    ltp: float
    week52_high: float
    week52_low: float
    index_pct_change: float           # e.g. Nifty 50 % change, same period


@dataclass
class ScoreResult:
    score: float                      # 0-100
    reason: str
    components: dict                  # raw 0-1 component values, for the UI breakdown


def compute_mcs(i: ScoreInputs) -> ScoreResult:
    # 1. volatility z-score: how many "normal days" of movement is today?
    std = i.trailing_daily_std_pct if i.trailing_daily_std_pct > 1e-6 else 1.0
    z = abs(i.pct_change) / std
    volatility_component = _clip01(z / 3.0)  # z>=3 -> maxed out

    # 2. volume ratio: how many multiples of average volume?
    avg_vol = i.trailing_avg_volume if i.trailing_avg_volume > 1e-6 else 1.0
    vol_ratio = i.volume / avg_vol
    volume_component = _clip01((vol_ratio - 1.0) / 4.0)  # 5x avg volume -> maxed

    # 3. proximity to 52w band, direction-aware: only "counts" if price is
    #    moving toward the extreme it's near (fresh high while rising,
    #    fresh low while falling), not just parked near an old level.
    band = max(i.week52_high - i.week52_low, 1e-6)
    dist_to_high = abs(i.week52_high - i.ltp) / band
    dist_to_low = abs(i.ltp - i.week52_low) / band
    if i.pct_change >= 0:
        proximity_component = _clip01(1.0 - dist_to_high * 4)  # within ~25% of band -> nonzero
    else:
        proximity_component = _clip01(1.0 - dist_to_low * 4)

    # 4. index divergence: is this stock doing something the market as a
    #    whole isn't? Filters out "the whole index moved" noise.
    divergence = abs(i.pct_change - i.index_pct_change)
    index_component = _clip01(divergence / 3.0)

    components = {
        "volatility_z": round(volatility_component, 3),
        "volume_ratio": round(volume_component, 3),
        "proximity_52w": round(proximity_component, 3),
        "index_divergence": round(index_component, 3),
    }

    raw = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)
    score = round(raw * 100, 1)

    reason = _build_reason(i, z, vol_ratio, proximity_component, components)

    return ScoreResult(score=score, reason=reason, components=components)


def _build_reason(i: ScoreInputs, z: float, vol_ratio: float,
                   proximity_component: float, components: dict) -> str:
    direction = "up" if i.pct_change >= 0 else "down"
    parts = [f"{direction.capitalize()} {abs(i.pct_change):.1f}%"]

    if components["volatility_z"] >= 0.5:
        parts.append(f"a {z:.1f}x larger move than its usual daily swing")
    if components["volume_ratio"] >= 0.4:
        parts.append(f"on {vol_ratio:.1f}x average volume")
    if proximity_component >= 0.5:
        extreme = "52-week high" if i.pct_change >= 0 else "52-week low"
        parts.append(f"near its {extreme}")
    if components["index_divergence"] >= 0.4:
        parts.append("moving independently of the broader index")

    if len(parts) == 1:
        return parts[0] + ", in line with its normal behaviour."

    return ", ".join(parts[:1]) + " - " + "; ".join(parts[1:]) + "."
