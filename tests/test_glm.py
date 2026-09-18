"""Tests for the exploratory binomial GLM reanalysis of L&R Table 5.

The deterministic references come from the committed run in
``report/glm_results.json`` (seed 20260918). ``firthmodels`` converges to a
tolerance of 1e-4, so Firth quantities are checked to three decimal places.
Simulation outputs depend on the NumPy and SciPy random streams and are checked
with tolerances, never equality.
"""

from __future__ import annotations

import filecmp
import math
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from how_many_prompts.glm import (
    design_frame,
    informative_subset,
    interaction_tests,
    run,
    simulate_cells,
    structural_nulls,
    to_bernoulli,
    trends,
)
from how_many_prompts.sources.lamerton_roger_2026 import to_csv, validate

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Fixtures: the fits are the slow part, so share them across the module
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return design_frame()


@pytest.fixture(scope="module")
def sub(df: pd.DataFrame) -> pd.DataFrame:
    return informative_subset(df)


@pytest.fixture(scope="module")
def interaction(sub: pd.DataFrame) -> dict:
    return interaction_tests(sub)


@pytest.fixture(scope="module")
def trend_results(sub: pd.DataFrame) -> list[dict]:
    return trends(sub)


# ---------------------------------------------------------------------------
# Design
# ---------------------------------------------------------------------------


def test_design_frame_is_the_full_250_cell_layout(df: pd.DataFrame) -> None:
    assert len(df) == 250
    assert int(df["detections"].sum()) == 103
    assert int((df["detections"] == 0).sum()) == 215
    # ``ceiling`` is the affordance-5 indicator used throughout the formulas.
    assert df.loc[df["affordance"] == 5, "ceiling"].eq(1).all()
    assert df.loc[df["affordance"] != 5, "ceiling"].eq(0).all()


def test_informative_subset_holds_every_detection(sub: pd.DataFrame) -> None:
    assert len(sub) == 70
    assert int((sub["detections"] > 0).sum()) == 35
    assert int(sub["detections"].sum()) == 103
    assert (sub["model_group"] != "baseline").all()
    assert sub["affordance"].isin([4, 5]).all()


def test_to_bernoulli_preserves_totals(sub: pd.DataFrame) -> None:
    rows = to_bernoulli(sub)
    assert len(rows) == int(sub["n"].sum())
    assert int(rows["detected"].sum()) == int(sub["detections"].sum())
    assert set(rows["detected"].unique()) == {0, 1}


# ---------------------------------------------------------------------------
# Structural nulls
# ---------------------------------------------------------------------------


def test_structural_null_bounds_by_sampling_unit(df: pd.DataFrame) -> None:
    bounds = {(x["block"], x["unit"]): x for x in structural_nulls(df)}
    audit = "loyal models, affordance 1 to 3 (the audit null)"

    completions = bounds[(audit, "completions")]
    assert completions["events"] == 0
    assert completions["n_units"] == 3150
    assert completions["upper_95"] == pytest.approx(0.0012, abs=0.0001)

    shared = bounds[(audit, "prompts, shared across models")]
    assert shared["events"] == 0
    assert shared["n_units"] == 150
    assert shared["upper_95"] == pytest.approx(0.0243, abs=0.0001)

    # Every block is a true zero; that is what makes them structural nulls.
    assert all(x["events"] == 0 for x in bounds.values())


# ---------------------------------------------------------------------------
# Interaction tests (deterministic references)
# ---------------------------------------------------------------------------


def test_naive_and_corrected_interaction_tests(interaction: dict) -> None:
    assert interaction["df"] == 4
    assert interaction["naive_lr_chi2"] == pytest.approx(16.467765, abs=1e-5)
    assert interaction["naive_lr_p"] == pytest.approx(0.002452, abs=1e-6)
    assert interaction["dispersion_additive"] == pytest.approx(1.592172, abs=1e-5)
    assert interaction["dispersion_interaction"] == pytest.approx(1.368542, abs=1e-5)
    assert interaction["quasi_f"] == pytest.approx(3.008269, abs=1e-5)
    assert interaction["quasi_f_p"] == pytest.approx(0.025906, abs=1e-6)


def test_firth_penalised_lr_test(interaction: dict) -> None:
    assert interaction["firth_converged"] is True
    assert interaction["firth_penalised_lr_chi2"] == pytest.approx(17.01744, abs=1e-3)
    assert interaction["firth_penalised_lr_p"] == pytest.approx(0.001918, abs=1e-4)


def test_separation_is_detected_and_firth_tames_it(interaction: dict) -> None:
    assert interaction["separation_detected"] is True
    assert interaction["coefficients_infinite_under_ml"] == 2
    # ML blows up; Firth does not. That contrast is the reason for the penalty.
    assert interaction["ml_max_se"] > 1e3
    assert interaction["firth_max_se"] == pytest.approx(1.667081, abs=1e-3)


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------


def test_poison_trend_does_not_survive_the_dispersion_adjustment(
    trend_results: list[dict],
) -> None:
    poison = next(x for x in trend_results if x["trend"].startswith("poison"))
    assert poison["odds_ratio_per_doubling"] == pytest.approx(2.2014, abs=1e-3)
    assert poison["profile_ci"][0] == pytest.approx(1.0596, abs=1e-3)
    assert poison["profile_ci"][1] == pytest.approx(5.2829, abs=1e-3)
    assert poison["adjusted_ci"][0] == pytest.approx(0.9742, abs=1e-3)
    assert poison["adjusted_ci"][1] == pytest.approx(4.9745, abs=1e-3)
    # The caveat in prose, asserted: profile excludes 1, adjusted does not.
    assert poison["profile_ci"][0] > 1.0
    assert poison["adjusted_ci"][0] < 1.0


def test_size_trend_only_just_survives(trend_results: list[dict]) -> None:
    size = next(x for x in trend_results if x["trend"].startswith("model size"))
    assert size["odds_ratio_per_doubling"] == pytest.approx(1.2386, abs=1e-3)
    assert size["profile_ci"][0] == pytest.approx(1.0785, abs=1e-3)
    assert size["profile_ci"][1] == pytest.approx(1.4302, abs=1e-3)
    assert size["adjusted_ci"][0] == pytest.approx(1.0194, abs=1e-3)
    assert size["adjusted_ci"][1] == pytest.approx(1.5049, abs=1e-3)
    assert size["adjusted_ci"][0] > 1.0


# ---------------------------------------------------------------------------
# Library guard
# ---------------------------------------------------------------------------


def test_firth_reproduces_the_closed_form_on_a_saturated_2x2() -> None:
    """Guard against a change of behaviour in ``firthmodels``.

    For a saturated 2x2 table Firth's penalty is exactly Jeffreys' prior, which
    adds half an event and half a non-event to each cell. With 0 of 30 against
    5 of 30 the two logits are therefore log(0.5/30.5) and log(5.5/25.5). If
    this test fails, the library has changed and every Firth number in the
    report must be re-derived before it is trusted.
    """
    from firthmodels.adapters.statsmodels import FirthLogit

    group = np.r_[np.zeros(30), np.ones(30)]
    detected = np.r_[np.zeros(30), np.zeros(25), np.ones(5)]
    exog = pd.DataFrame({"Intercept": np.ones(60), "group": group})
    params = np.asarray(FirthLogit(detected, exog).fit().params)

    assert params[0] == pytest.approx(math.log(0.5 / 30.5), abs=1e-3)
    assert params[0] + params[1] == pytest.approx(math.log(5.5 / 25.5), abs=1e-3)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------


def test_simulate_cells_reproduces_the_design_effect() -> None:
    """rho = 0.5 over m = 3 samples should inflate variance by 1 + (m-1)rho = 2."""
    rng = np.random.default_rng(20260918)
    p = np.full(20_000, 0.2)
    clustered = simulate_cells(p, prompts=10, samples=3, rho=0.5, rng=rng)
    independent = simulate_cells(p, prompts=10, samples=3, rho=0.0, rng=rng)

    assert clustered.mean() == pytest.approx(6.0, rel=0.05)
    assert clustered.var() / independent.var() == pytest.approx(2.0, rel=0.10)


def test_simulate_cells_at_rho_zero_is_binomial() -> None:
    rng = np.random.default_rng(20260918)
    draws = simulate_cells(np.full(20_000, 0.2), 10, 3, 0.0, rng)
    assert draws.max() <= 30
    assert draws.var() == pytest.approx(30 * 0.2 * 0.8, rel=0.10)


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------


def test_run_returns_every_documented_section() -> None:
    r = run(reps=20)
    assert set(r) == {
        "status",
        "design",
        "structural_nulls",
        "interaction",
        "trends",
        "marginal_rates",
        "simulation",
    }
    assert r["status"].startswith("exploratory")
    assert len(r["trends"]) == 2
    assert len(r["marginal_rates"]) == 10  # 5 techniques x 2 affordances
    sim = r["simulation"]
    assert len(sim["type1_error"]) == 3
    assert len(sim["redesign"]) == 3
    assert len(sim["dispersion_calibration"]) == 6
    assert all(0.0 <= x["naive_lr_rejects"] <= 1.0 for x in sim["type1_error"])


@pytest.mark.slow
def test_naive_test_over_rejects_under_clustering_and_the_correction_helps() -> None:
    """The confirmatory claim: pseudoreplication breaks the naive test."""
    r = run(reps=400)
    by_rho = {x["rho"]: x for x in r["simulation"]["type1_error"]}

    # At rho = 0 both tests are honest.
    assert by_rho[0.0]["naive_lr_rejects"] == pytest.approx(0.05, abs=0.03)

    # As rho grows the naive test rejects far too often; the correction pulls it
    # back towards nominal, though it still under-corrects (caveat 4).
    assert by_rho[0.5]["naive_lr_rejects"] > 0.20
    assert by_rho[0.5]["quasi_f_rejects"] < by_rho[0.5]["naive_lr_rejects"]
    assert by_rho[0.3]["quasi_f_rejects"] < 0.15


# ---------------------------------------------------------------------------
# Transcription drift
# ---------------------------------------------------------------------------


def test_committed_csv_matches_the_transcription() -> None:
    """``table5_detections.csv`` must be exactly what ``to_csv()`` emits today."""
    with tempfile.NamedTemporaryFile(suffix=".csv") as fh:
        to_csv(fh.name)
        committed = REPO_ROOT / "table5_detections.csv"
        assert filecmp.cmp(fh.name, committed, shallow=False), (
            "table5_detections.csv has drifted from the source transcription; "
            "regenerate it rather than editing it by hand"
        )


def test_transcription_validates() -> None:
    """The hard provenance gate for CI.

    ``validate()`` reports by return value, not by exit code, so ``uv run
    validate-table5`` cannot fail a build on its own. This test is what actually
    stops an invalid transcription from being merged.
    """
    assert validate(verbose=False) is True
