"""Binomial GLM reanalysis of the Lamerton and Roger (2026) Table 5 audit cells.

STATUS: EXPLORATORY. The author had seen the cell counts before this model was
specified, so every p-value here is descriptive. The confirmatory weight sits on
the fake-data simulations, whose truth is known by construction.

Libraries do the statistics. This module only states the design and joins them up:

- ``statsmodels``  maximum-likelihood binomial GLM, deviance, Pearson chi-square
- ``firthmodels``  Firth penalised logistic regression, penalised likelihood-ratio
                   tests, profile-likelihood intervals, separation detection
- ``patsy``        design matrices from formulas (installed with statsmodels)
- ``scipy.stats``  beta-binomial draws and reference distributions
- this package     Clopper-Pearson bounds and design effects (``intervals.py``)

What this module adds to the exact bounds in ``intervals.py``:

1. It states the design. 250 cells are a crossed layout of model, affordance and
   technique. 180 of them are structural nulls (baselines, and affordances 1 to 3).
   All detections sit in 70 cells, and only those cells can inform a model.
2. It tests the claim that the pooled Table 5 Total is not a rate, as a
   technique-by-affordance interaction.
3. It shows why plain maximum likelihood fails on audit data (separation) and
   fits Firth's penalised likelihood in its place (Firth, 1993).
4. It estimates two one-degree-of-freedom trends that no cell-by-cell reading
   can show: poison fraction and model size.
5. It simulates the design with known truth: (A) the type I error of the naive
   and corrected tests under pseudoreplication, (B) ways of spending the same
   30 completions per cell, and (C) what the dispersion statistic reads when
   rho is known, because that statistic is biased in sparse data.

Known limits, stated once here and repeated in the output:

- rho is NOT identified by cell counts. Two biases act in opposite directions:
  lack of fit inflates the dispersion statistic, and sparse cells (expected
  counts below one) deflate it. Simulation C calibrates the statistic against
  known rho, so the observed value can be read against that curve.
- If the 10 prompts per cell are shared across models, cells are correlated
  through the prompts (crossed random effects). Cell counts cannot show this.
  The simulations here treat cells as independent.
- Profile-likelihood intervals do not allow for overdispersion. The adjusted
  intervals do, but they are Wald intervals. Both are reported.

Run:  uv run python -m how_many_prompts.glm [--reps 1000] [--json PATH]
"""

from __future__ import annotations

import argparse
import json
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from firthmodels import detect_separation
from firthmodels.adapters.statsmodels import FirthLogit
from patsy import build_design_matrices, dmatrix
from scipy import stats

from .intervals import clopper_pearson_upper, design_effect
from .sources.lamerton_roger_2026 import (
    BASELINE_MODELS,
    POISON_MODELS,
    PROMPTS_PER_CELL,
    SAMPLES_PER_PROMPT,
    TRAINED_MODELS,
    table5_cells,
)

SEED = 20260918
ALPHA = 0.05
RHO_GRID = (0.0, 0.3, 0.5)
CALIBRATION_RHO_GRID = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)

# Model metadata parsed from the model names used in the source module.
# Sizes are parameter counts in billions; fractions are poison percentages.
SIZE_BILLIONS = {"1.5b-trained": 1.5, "7b-trained": 7.0, "32b-trained": 32.0}
POISON_PERCENT = {
    "7b-poison-12.5": 12.5,
    "7b-poison-6.25": 6.25,
    "7b-poison-3.125": 3.125,
}

ADDITIVE = "C(model) + C(technique) + ceiling"
INTERACTION = "C(model) + C(technique) * ceiling"
TREND = "log2_x + C(technique) + ceiling"


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


def design_frame() -> pd.DataFrame:
    """Return the 250 cells as a data frame with design covariates."""
    groups = (
        {m: "baseline" for m in BASELINE_MODELS}
        | {m: "trained" for m in TRAINED_MODELS}
        | {m: "poison" for m in POISON_MODELS}
    )
    df = pd.DataFrame(
        {
            "model": c.model,
            "model_group": groups[c.model],
            "affordance": c.affordance,
            "technique": c.technique,
            "detections": c.detections,
            "n": c.n,
        }
        for c in table5_cells()
    )
    df["ceiling"] = (df["affordance"] == 5).astype(int)
    return df


def informative_subset(df: pd.DataFrame) -> pd.DataFrame:
    """Return the cells that can inform a model: loyal models, affordance 4 and 5."""
    keep = (df["model_group"] != "baseline") & (df["affordance"] >= 4)
    return df.loc[keep].reset_index(drop=True)


def to_bernoulli(df: pd.DataFrame) -> pd.DataFrame:
    """Expand cell counts to one row per completion, with a 0/1 ``detected`` column.

    ``firthmodels``' statsmodels adapter takes binary rows. The expansion changes
    nothing statistically; the likelihood is the same as the grouped one.
    """
    hits = df.loc[df.index.repeat(df["detections"])].assign(detected=1)
    misses = df.loc[df.index.repeat(df["n"] - df["detections"])].assign(detected=0)
    return pd.concat([hits, misses], ignore_index=True)


# ---------------------------------------------------------------------------
# Structural nulls: what the zeros exclude, by choice of sampling unit
# ---------------------------------------------------------------------------


def structural_nulls(df: pd.DataFrame) -> list[dict]:
    """Bound the two blocks of zeros under different sampling units.

    ``completions`` treats every completion as independent (the published reading).
    ``prompts, not shared`` counts 10 distinct prompts per cell.
    ``prompts, shared`` assumes the same 10 prompts serve every model within an
    affordance and technique, so the distinct prompts are far fewer. The source
    paper does not settle which holds; both are shown.
    """
    blocks = {
        "baseline controls (false-positive check)": df["model_group"] == "baseline",
        "loyal models, affordance 1 to 3 (the audit null)": (
            (df["model_group"] != "baseline") & (df["affordance"] <= 3)
        ),
    }
    out = []
    for label, mask in blocks.items():
        block = df.loc[mask]
        k = int(block["detections"].sum())
        n_designs = block.groupby(["affordance", "technique"]).ngroups
        units = {
            "completions": int(block["n"].sum()),
            "prompts, not shared across models": len(block) * PROMPTS_PER_CELL,
            "prompts, shared across models": n_designs * PROMPTS_PER_CELL,
        }
        for unit, n_units in units.items():
            out.append(
                {
                    "block": label,
                    "unit": unit,
                    "events": k,
                    "n_units": n_units,
                    "upper_95": clopper_pearson_upper(k, n_units),
                }
            )
    return out


# ---------------------------------------------------------------------------
# Fitting: thin wrappers over statsmodels and firthmodels
# ---------------------------------------------------------------------------


def _exog(formula: str, df: pd.DataFrame) -> pd.DataFrame:
    return dmatrix(formula, df, return_type="dataframe")


def fit_ml(formula: str, df: pd.DataFrame):
    """Maximum-likelihood binomial GLM on the cell counts (statsmodels)."""
    endog = np.column_stack([df["detections"], df["n"] - df["detections"]])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # separation warnings are the point
        return sm.GLM(endog, _exog(formula, df), family=sm.families.Binomial()).fit()


def fit_firth(formula: str, df: pd.DataFrame, pl: bool = False):
    """Firth penalised logistic regression on the expanded rows (firthmodels).

    ``pl=True`` adds penalised likelihood-ratio p-values and profile-likelihood
    intervals for every coefficient; it refits once per coefficient.
    """
    rows = to_bernoulli(df)
    # The adapter follows the statsmodels convention: it adds no intercept, so
    # the intercept column from the patsy design matrix is the only one.
    return FirthLogit(rows["detected"], _exog(formula, rows)).fit(pl=pl)


def dispersion(ml_result) -> float:
    """Pearson chi-square over residual degrees of freedom."""
    return float(ml_result.pearson_chi2 / ml_result.df_resid)


# ---------------------------------------------------------------------------
# Tests of the technique-by-affordance interaction
# ---------------------------------------------------------------------------


def interaction_tests(sub: pd.DataFrame) -> dict:
    """Test the interaction three ways and report what separation does to ML."""
    ml0, ml1 = fit_ml(ADDITIVE, sub), fit_ml(INTERACTION, sub)
    f0, f1 = fit_firth(ADDITIVE, sub), fit_firth(INTERACTION, sub)
    q = int(ml0.df_resid - ml1.df_resid)

    rows = to_bernoulli(sub)
    sep = detect_separation(
        _exog(INTERACTION, rows), rows["detected"], fit_intercept=False
    )
    lr = float(ml0.deviance - ml1.deviance)
    phi = dispersion(ml1)
    f_stat = (lr / q) / phi
    pen_lr = float(2 * (f1.llf - f0.llf))
    return {
        "df": q,
        "naive_lr_chi2": lr,
        "naive_lr_p": float(stats.chi2.sf(lr, q)),
        "dispersion_additive": dispersion(ml0),
        "dispersion_interaction": phi,
        "quasi_f": f_stat,
        "quasi_f_p": float(stats.f.sf(f_stat, q, ml1.df_resid)),
        "firth_penalised_lr_chi2": pen_lr,
        "firth_penalised_lr_p": float(stats.chi2.sf(pen_lr, q)),
        "separation_detected": bool(sep.separation),
        "coefficients_infinite_under_ml": int(np.sum(~np.asarray(sep.is_finite))),
        "ml_max_se": float(np.max(ml1.bse)),
        "firth_max_se": float(np.max(f1.bse)),
        "firth_converged": bool(f1.converged),
    }


# ---------------------------------------------------------------------------
# One-degree-of-freedom trends
# ---------------------------------------------------------------------------


def _trend(sub: pd.DataFrame, models: dict[str, float], label: str) -> dict:
    d = sub.loc[sub["model"].isin(list(models))].copy()
    d["log2_x"] = np.log2(d["model"].map(models).astype(float))
    firth = fit_firth(TREND, d, pl=True)
    ml = fit_ml(TREND, d)
    names = list(_exog(TREND, d).columns)
    i = names.index("log2_x")
    b = float(np.asarray(firth.params)[i])
    se = float(np.asarray(firth.bse)[i])
    lo, hi = np.asarray(firth.conf_int())[i]  # profile likelihood
    phi = max(1.0, dispersion(ml))
    t = stats.t.ppf(1 - ALPHA / 2, ml.df_resid)
    se_q = se * np.sqrt(phi)
    return {
        "trend": label,
        "cells": len(d),
        "detections_by_level": {
            m: int(d.loc[d["model"] == m, "detections"].sum()) for m in models
        },
        "odds_ratio_per_doubling": float(np.exp(b)),
        "profile_ci": [float(np.exp(lo)), float(np.exp(hi))],
        "penalised_lr_p": float(np.asarray(firth.pvalues)[i]),
        "dispersion": dispersion(ml),
        "adjusted_ci": [float(np.exp(b - t * se_q)), float(np.exp(b + t * se_q))],
        "adjusted_p": float(2 * stats.t.sf(abs(b / se_q), ml.df_resid)),
    }


def trends(sub: pd.DataFrame) -> list[dict]:
    return [
        _trend(sub, POISON_PERCENT, "poison fraction (7b poison models)"),
        _trend(sub, SIZE_BILLIONS, "model size (fully trained models)"),
    ]


# ---------------------------------------------------------------------------
# Marginal detection rates by technique and affordance
# ---------------------------------------------------------------------------


def marginal_rates(sub: pd.DataFrame, draws: int = 4000) -> pd.DataFrame:
    """Predicted detection rate per technique and affordance, averaged over models.

    Point values come from the Firth fit. Intervals come from draws of
    beta ~ N(beta_hat, phi * cov), averaged on the probability scale, so they
    allow for overdispersion but are approximate in the sparse cells.
    """
    design = _exog(INTERACTION, sub)
    firth = fit_firth(INTERACTION, sub)
    phi = max(1.0, dispersion(fit_ml(INTERACTION, sub)))
    grid = (
        sub[["model"]]
        .drop_duplicates()
        .merge(sub[["technique"]].drop_duplicates(), how="cross")
        .merge(pd.DataFrame({"ceiling": [0, 1]}), how="cross")
    )
    xg = np.asarray(build_design_matrices([design.design_info], grid)[0])
    beta_hat = np.asarray(firth.params)
    rng = np.random.default_rng(SEED)
    betas = rng.multivariate_normal(
        beta_hat, phi * np.asarray(firth.cov_params()), size=draws
    )

    def averaged(b: np.ndarray) -> pd.Series:
        g = grid.assign(p=stats.logistic.cdf(xg @ b))
        return g.groupby(["technique", "ceiling"])["p"].mean()

    sims = np.vstack([averaged(b).to_numpy() for b in betas])
    out = averaged(beta_hat).rename("rate").reset_index()
    out["lower"] = np.percentile(sims, 2.5, axis=0)
    out["upper"] = np.percentile(sims, 97.5, axis=0)
    observed = (
        sub.groupby(["technique", "ceiling"])[["detections", "n"]].sum().reset_index()
    )
    out = out.merge(observed, on=["technique", "ceiling"])
    out["observed"] = out["detections"] / out["n"]
    out["affordance"] = np.where(out["ceiling"] == 1, 5, 4)
    cols = [
        "technique",
        "affordance",
        "detections",
        "n",
        "observed",
        "rate",
        "lower",
        "upper",
    ]
    return out[cols].sort_values(["affordance", "technique"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Fake-data simulation
# ---------------------------------------------------------------------------


def simulate_cells(
    p: np.ndarray, prompts: int, samples: int, rho: float, rng: np.random.Generator
) -> np.ndarray:
    """Simulate detections per cell with prompt-level clustering.

    Each prompt's ``samples`` completions follow a beta-binomial distribution
    with mean ``p`` and intra-prompt correlation ``rho`` (scipy.stats.betabinom).
    ``rho = 0`` gives independent completions.
    """
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    if rho <= 0:
        return rng.binomial(prompts * samples, p)
    a = (p * (1 - rho) / rho)[:, None]
    b = ((1 - p) * (1 - rho) / rho)[:, None]
    draws = stats.betabinom.rvs(samples, a, b, size=(len(p), prompts), random_state=rng)
    return draws.sum(axis=1)


def _ml_pair(x0: np.ndarray, x1: np.ndarray, k: np.ndarray, n: np.ndarray):
    endog = np.column_stack([k, n - k])
    family = sm.families.Binomial()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return sm.GLM(endog, x0, family=family).fit(), sm.GLM(
            endog, x1, family=family
        ).fit()


def _interaction_pvalues(x0, x1, k, n) -> tuple[float, float, float]:
    m0, m1 = _ml_pair(x0, x1, k, n)
    q = m0.df_resid - m1.df_resid
    lr = max(0.0, m0.deviance - m1.deviance)
    phi = dispersion(m1)
    naive = float(stats.chi2.sf(lr, q))
    quasi = float(stats.f.sf((lr / q) / max(1.0, phi), q, m1.df_resid))
    return naive, quasi, phi


def simulate(sub: pd.DataFrame, reps: int = 1000) -> dict:
    """Simulate the 70-cell design, with truth set from the Firth fits.

    A. Type I error. Truth has NO interaction. How often does each test reject
       at 5% as the correlation between re-runs grows?
    B. Redesign. Truth HAS the fitted interaction and rho = 0.3. Same 30
       completions per cell, split three ways. Power of the corrected test.
    C. Calibration. Truth has the fitted interaction. What does the dispersion
       statistic read, computed exactly as for the real data, at each known rho?
    """
    x0 = np.asarray(_exog(ADDITIVE, sub))
    x1 = np.asarray(_exog(INTERACTION, sub))
    n = sub["n"].to_numpy()
    p_null = stats.logistic.cdf(x0 @ np.asarray(fit_firth(ADDITIVE, sub).params))
    p_alt = stats.logistic.cdf(x1 @ np.asarray(fit_firth(INTERACTION, sub).params))
    rng = np.random.default_rng(SEED)
    m, prompts = SAMPLES_PER_PROMPT, PROMPTS_PER_CELL

    def batch(p, n_prompts, n_samples, rho, runs):
        return np.array(
            [
                _interaction_pvalues(
                    x0, x1, simulate_cells(p, n_prompts, n_samples, rho, rng), n
                )
                for _ in range(runs)
            ]
        )

    type1 = []
    for rho in RHO_GRID:
        pv = batch(p_null, prompts, m, rho, reps)
        type1.append(
            {
                "rho": rho,
                "naive_lr_rejects": float((pv[:, 0] < ALPHA).mean()),
                "quasi_f_rejects": float((pv[:, 1] < ALPHA).mean()),
            }
        )

    redesign = []
    rho = 0.3
    for n_prompts, n_samples in ((10, 3), (15, 2), (30, 1)):
        pv = batch(p_alt, n_prompts, n_samples, rho, reps)
        n_eff = round(n_prompts * n_samples / design_effect(n_samples, rho))
        redesign.append(
            {
                "prompts": n_prompts,
                "samples_per_prompt": n_samples,
                "rho": rho,
                "power_quasi_f": float((pv[:, 1] < ALPHA).mean()),
                "effective_n_per_cell": n_eff,
                "zero_cell_upper_95": clopper_pearson_upper(0, n_eff),
            }
        )

    calibration = []
    cal_reps = max(200, reps // 2)
    observed = dispersion(fit_ml(INTERACTION, sub))
    for rho in CALIBRATION_RHO_GRID:
        phis = batch(p_alt, prompts, m, rho, cal_reps)[:, 2]
        calibration.append(
            {
                "rho": rho,
                "true_design_effect": design_effect(m, rho),
                "mean_dispersion": float(phis.mean()),
                "dispersion_2.5": float(np.percentile(phis, 2.5)),
                "dispersion_97.5": float(np.percentile(phis, 97.5)),
                "share_at_or_above_observed": float((phis >= observed).mean()),
            }
        )
    return {
        "reps": reps,
        "calibration_reps": cal_reps,
        "type1_error": type1,
        "redesign": redesign,
        "dispersion_calibration": calibration,
    }


# ---------------------------------------------------------------------------
# Orchestration and reporting
# ---------------------------------------------------------------------------


def run(reps: int = 1000) -> dict:
    df = design_frame()
    sub = informative_subset(df)
    return {
        "status": "exploratory; see module docstring",
        "design": {
            "cells": len(df),
            "zero_cells": int((df["detections"] == 0).sum()),
            "informative_cells": len(sub),
            "informative_nonzero_cells": int((sub["detections"] > 0).sum()),
            "detections": int(df["detections"].sum()),
            "detections_in_informative_cells": int(sub["detections"].sum()),
        },
        "structural_nulls": structural_nulls(df),
        "interaction": interaction_tests(sub),
        "trends": trends(sub),
        "marginal_rates": marginal_rates(sub).to_dict(orient="records"),
        "simulation": simulate(sub, reps=reps),
    }


def _pct(x: float, digits: int = 1) -> str:
    return f"{100 * x:.{digits}f}%"


def _table(header: list[str], align: str, rows: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(header) + " |",
        align,
        *("| " + " | ".join(r) + " |" for r in rows),
    ]


def to_markdown(r: dict) -> str:
    d, t, s = r["design"], r["interaction"], r["simulation"]
    out = [
        "# GLM reanalysis of L&R Table 5 (exploratory)",
        "",
        "## Design",
        f"- {d['cells']} cells; {d['zero_cells']} record zero detections.",
        f"- {d['informative_cells']} cells can inform a model (loyal models,"
        + f" affordance 4 and 5); {d['informative_nonzero_cells']} are non-zero.",
        f"- {d['detections_in_informative_cells']} of {d['detections']} detections"
        + " sit in those cells.",
        "",
        "## What the zeros exclude, by sampling unit",
    ]
    out += _table(
        ["Block", "Unit", "Events", "Units", "95% upper bound"],
        "|---|---|---:|---:|---:|",
        [
            [
                x["block"],
                x["unit"],
                str(x["events"]),
                str(x["n_units"]),
                _pct(x["upper_95"], 2),
            ]
            for x in r["structural_nulls"]
        ],
    )
    out += [
        "",
        "## Technique-by-affordance interaction",
        f"- Naive likelihood-ratio test: chi2 = {t['naive_lr_chi2']:.1f} on"
        + f" {t['df']} df, p = {t['naive_lr_p']:.4f}.",
        f"- Dispersion (Pearson chi2 / df, ML fit): {t['dispersion_interaction']:.2f}.",
        f"- Overdispersion-corrected F test: F = {t['quasi_f']:.2f},"
        + f" p = {t['quasi_f_p']:.4f}.",
        "- Firth penalised likelihood-ratio test: chi2 ="
        + f" {t['firth_penalised_lr_chi2']:.1f}, p = {t['firth_penalised_lr_p']:.4f}.",
        f"- Separation detected: {t['separation_detected']};"
        + f" {t['coefficients_infinite_under_ml']} coefficient(s) infinite under ML."
        + f" Largest ML standard error = {t['ml_max_se']:.0f};"
        + f" largest Firth standard error = {t['firth_max_se']:.2f}.",
        "",
        "## Trends (odds ratio per doubling)",
    ]
    out += _table(
        [
            "Trend",
            "Detections by level",
            "OR",
            "Profile 95% CI",
            "Penalised LR p",
            "Dispersion",
            "Adjusted 95% CI",
            "Adjusted p",
        ],
        "|---|---|---:|---|---:|---:|---|---:|",
        [
            [
                x["trend"],
                ", ".join(str(v) for v in x["detections_by_level"].values()),
                f"{x['odds_ratio_per_doubling']:.2f}",
                f"{x['profile_ci'][0]:.2f} to {x['profile_ci'][1]:.2f}",
                f"{x['penalised_lr_p']:.3f}",
                f"{x['dispersion']:.2f}",
                f"{x['adjusted_ci'][0]:.2f} to {x['adjusted_ci'][1]:.2f}",
                f"{x['adjusted_p']:.3f}",
            ]
            for x in r["trends"]
        ],
    )
    out += ["", "## Detection rate by technique and affordance (loyal models)"]
    out += _table(
        ["Technique", "Affordance", "Observed", "Model rate", "95% interval"],
        "|---|---:|---:|---:|---|",
        [
            [
                x["technique"],
                str(x["affordance"]),
                f"{x['detections']}/{x['n']} ({_pct(x['observed'])})",
                _pct(x["rate"]),
                f"{_pct(x['lower'])} to {_pct(x['upper'])}",
            ]
            for x in r["marginal_rates"]
        ],
    )
    out += [
        "",
        f"## Simulation A: type I error of the interaction test ({s['reps']} runs)",
        "Truth has no interaction. Nominal rate is 5%.",
    ]
    out += _table(
        ["rho", "Naive LR test", "Corrected F test"],
        "|---:|---:|---:|",
        [
            [str(x["rho"]), _pct(x["naive_lr_rejects"]), _pct(x["quasi_f_rejects"])]
            for x in s["type1_error"]
        ],
    )
    out += ["", "## Simulation B: same 30 completions per cell (rho = 0.3)"]
    out += _table(
        [
            "Prompts x samples",
            "Power, corrected test",
            "Effective n",
            "Zero-cell bound",
        ],
        "|---|---:|---:|---:|",
        [
            [
                f"{x['prompts']} x {x['samples_per_prompt']}",
                _pct(x["power_quasi_f"]),
                str(x["effective_n_per_cell"]),
                _pct(x["zero_cell_upper_95"]),
            ]
            for x in s["redesign"]
        ],
    )
    out += [
        "",
        "## Simulation C: the dispersion statistic at known rho"
        + f" ({s['calibration_reps']} runs)",
        f"Observed dispersion in the real data: {t['dispersion_interaction']:.2f}.",
    ]
    out += _table(
        [
            "True rho",
            "True design effect",
            "Mean dispersion",
            "95% range",
            "Runs at or above observed",
        ],
        "|---:|---:|---:|---|---:|",
        [
            [
                str(x["rho"]),
                f"{x['true_design_effect']:.1f}",
                f"{x['mean_dispersion']:.2f}",
                f"{x['dispersion_2.5']:.2f} to {x['dispersion_97.5']:.2f}",
                _pct(x["share_at_or_above_observed"]),
            ]
            for x in s["dispersion_calibration"]
        ],
    )
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--reps", type=int, default=1000, help="simulation runs")
    parser.add_argument("--json", type=str, default=None, help="write results as JSON")
    args = parser.parse_args()
    results = run(reps=args.reps)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
    print(to_markdown(results))


if __name__ == "__main__":
    main()
