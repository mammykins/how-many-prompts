"""Empirical-Bayes beta-binomial partial pooling within model groups."""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from scipy.stats import beta, betabinom

from .sources.lamerton_roger_2026 import Cell


@dataclass(frozen=True)
class EBResult:
    shrunk_estimate: np.ndarray
    ci_lower: np.ndarray
    ci_upper: np.ndarray
    alpha_hat: float
    beta_hat: float


def fit_beta_binomial(k_arr, n_arr) -> tuple[float, float]:
    """Fit positive beta prior parameters by beta-binomial MLE."""
    k = np.asarray(k_arr, dtype=int)
    n = np.asarray(n_arr, dtype=int)
    if k.size == 0 or np.any(k < 0) or np.any(k > n) or np.any(n <= 0):
        raise ValueError("invalid binomial counts")

    def objective(log_params):
        a, b = np.exp(log_params)
        return -float(np.sum(betabinom.logpmf(k, n, a, b)))

    result = minimize(objective, np.log([1.0, 1.0]), method="Nelder-Mead")
    if not result.success or np.any(~np.isfinite(result.x)):
        raise RuntimeError("beta-binomial MLE did not converge")
    alpha_hat, beta_hat = np.exp(result.x)
    return float(alpha_hat), float(beta_hat)


def empirical_bayes(k_arr, n_arr, alpha: float = 0.05) -> EBResult:
    """Return posterior means and equal-tailed credible intervals."""
    k = np.asarray(k_arr, dtype=int)
    n = np.asarray(n_arr, dtype=int)
    alpha_hat, beta_hat = fit_beta_binomial(k, n)
    posterior_a = alpha_hat + k
    posterior_b = beta_hat + n - k
    return EBResult(
        (posterior_a / (posterior_a + posterior_b)).astype(float),
        beta.ppf(alpha / 2, posterior_a, posterior_b),
        beta.ppf(1 - alpha / 2, posterior_a, posterior_b),
        alpha_hat,
        beta_hat,
    )


def shrink_cells(cells: list[Cell]) -> dict[tuple[str, int, str], EBResult]:
    """Shrink non-baseline cells with separate trained and poison priors."""
    groups = {
        "trained": [c for c in cells if not c.is_baseline and not c.model.startswith("7b-poison")],
        "poison": [c for c in cells if c.model.startswith("7b-poison")],
    }
    results = {}
    for group_cells in groups.values():
        fit = empirical_bayes(
            [c.detections for c in group_cells],
            [c.n for c in group_cells],
        )
        for index, cell in enumerate(group_cells):
            results[(cell.model, cell.affordance, cell.technique)] = EBResult(
                float(fit.shrunk_estimate[index]),
                float(fit.ci_lower[index]),
                float(fit.ci_upper[index]),
                fit.alpha_hat,
                fit.beta_hat,
            )
    return results
