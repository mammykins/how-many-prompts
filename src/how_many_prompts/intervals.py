"""Confidence intervals and sensitivity calculations for clustered audit cells."""

from scipy.stats import beta
from statsmodels.stats.proportion import proportion_confint


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Return a Wilson score interval for a binomial proportion."""
    if n <= 0 or not 0 <= k <= n:
        raise ValueError("require n > 0 and 0 <= k <= n")
    lo, hi = proportion_confint(k, n, alpha=alpha, method="wilson")
    return float(lo), float(hi)


def clopper_pearson_upper(k: int, n: int, alpha: float = 0.05) -> float:
    """Return the upper limit of the two-sided Clopper–Pearson interval.

    With the default ``alpha`` this is the ``1 - alpha/2`` quantile, so a 0/30 cell
    returns 11.57% rather than the 9.50% a one-sided 95% bound would give.
    """
    if n <= 0 or not 0 <= k <= n:
        raise ValueError("require n > 0 and 0 <= k <= n")
    if k == n:
        return 1.0
    return float(beta.ppf(1 - alpha / 2, k + 1, n - k))


def design_effect(m: int, rho: float) -> float:
    """Return the clustered-sampling design effect."""
    if m < 1 or not 0 <= rho <= 1:
        raise ValueError("require m >= 1 and 0 <= rho <= 1")
    return 1 + (m - 1) * rho


def effective_n(n: int, m: int, rho: float) -> float:
    """Return effective independent sample size after clustering adjustment."""
    if n <= 0:
        raise ValueError("require n > 0")
    return n / design_effect(m, rho)
