"""Audit detection power calculations with declared trigger coverage."""

import math


def p_at_least_one_detection(N: int, r: float, coverage: float) -> float:
    """Probability of at least one detection in N conversations.

    ``coverage`` is a declared input: it is not estimated from published d/r.
    """
    if N < 0 or not 0 <= r <= 1 or not 0 <= coverage <= 1:
        raise ValueError("require N >= 0 and rates in [0, 1]")
    return -math.expm1(N * math.log1p(-coverage * r)) if coverage * r < 1 else 1.0


def conversations_for_probability(
    r: float, coverage: float, probability: float = 0.8
) -> int:
    """Smallest N whose detection probability reaches ``probability``."""
    if not 0 < probability < 1:
        raise ValueError("probability must be between 0 and 1")
    p = r * coverage
    if not 0 < p <= 1:
        raise ValueError("coverage * r must be positive")
    if p == 1:
        return 1
    return math.ceil(math.log1p(-probability) / math.log1p(-p))
