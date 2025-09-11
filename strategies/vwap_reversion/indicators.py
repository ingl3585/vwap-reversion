# strategies/vwap_reversion/indicators.py

import math
import config
from engine.state import SymbolState

def update_ewma_z(state: SymbolState, deviation: float, alpha: float = config.EWMA_ALPHA) -> float:
    # For first observation, initialize with current deviation
    if state.observationCount == 1:
        state.emaDeviation = deviation
        state.emaVariance = abs(deviation) * 2.0  # Initial variance estimate
    else:
        # Standard EWMA update - CRITICAL: Store previous EMA before updating for correct variance calculation
        prev_ema_deviation = state.emaDeviation
        state.emaDeviation = (1 - alpha) * state.emaDeviation + alpha * deviation
        squared_deviation = (deviation - prev_ema_deviation) ** 2
        state.emaVariance = (1 - alpha) * state.emaVariance + alpha * squared_deviation
    
    # Apply proper EWMA bias correction for early observations
    if state.observationCount < 20:  # Bias correction period
        # Standard EWMA bias correction formula
        bias_correction = (1 - (1 - alpha) ** state.observationCount) / (1 - (1 - alpha))
        corrected_variance = state.emaVariance / bias_correction
    else:
        corrected_variance = state.emaVariance
    
    # Calculate z-score with smoothed variance floor to avoid artificial inflation
    effective_variance = _smooth_variance_floor(corrected_variance, config.MIN_VARIANCE_THRESHOLD)
    return deviation / math.sqrt(effective_variance)

def _smooth_variance_floor(variance: float, min_threshold: float) -> float:
    if variance <= min_threshold:
        return min_threshold
    # Smooth transition zone
    elif variance < min_threshold * 1.5:
        blend_factor = (variance - min_threshold) / (min_threshold * 0.5)
        return min_threshold + (variance - min_threshold) * blend_factor
    else:
        return variance
