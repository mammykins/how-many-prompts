import pytest

from how_many_prompts.intervals import (
    clopper_pearson_upper,
    design_effect,
    effective_n,
)
from how_many_prompts.power import conversations_for_probability
from how_many_prompts.shrinkage import shrink_cells
from how_many_prompts.sources.lamerton_roger_2026 import table5_cells


def test_zero_cell_clopper_pearson_reference() -> None:
    assert clopper_pearson_upper(0, 30) == pytest.approx(0.1157, abs=0.0001)


def test_design_effect_references() -> None:
    assert design_effect(3, 0.5) == pytest.approx(2)
    assert effective_n(30, 3, 0.5) == pytest.approx(15)
    assert clopper_pearson_upper(0, 15) == pytest.approx(0.218, abs=0.001)


@pytest.mark.parametrize(
    ("p", "probability", "expected"),
    [(0.1, 0.8, 16), (0.1, 0.95, 29), (0.01, 0.95, 299), (0.001, 0.8, 1609)],
)
def test_geometric_power_references(p: float, probability: float, expected: int) -> None:
    assert conversations_for_probability(p, 1.0, probability) == expected


def test_shrinkage_excludes_structural_baselines_and_separates_groups() -> None:
    results = shrink_cells(table5_cells())
    assert len(results) == 175
    assert all(key[0] not in {"qwen2.5-1.5b-instruct", "qwen2.5-7b-instruct", "qwen2.5-32b-instruct"} for key in results)
    trained = next(value for key, value in results.items() if key[0] == "1.5b-trained")
    poison = next(value for key, value in results.items() if key[0] == "7b-poison-12.5")
    assert trained.alpha_hat > 0 and trained.beta_hat > 0
    assert poison.alpha_hat > 0 and poison.beta_hat > 0
    assert (trained.alpha_hat, trained.beta_hat) != (poison.alpha_hat, poison.beta_hat)
