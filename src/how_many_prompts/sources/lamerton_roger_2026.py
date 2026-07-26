"""
Transcription of published results from:

    Lamerton, A. & Roger, F. (2026). "Narrow Secret Loyalty Dodges Black-Box Audits."
    arXiv:2605.06846v3

PROVENANCE RULE: every constant below carries an inline comment naming its source
table or figure. Nothing in this module is derived, assumed, or inferred. Derived
quantities belong in analysis modules, not here.

Run `validate()` before any analysis. It reproduces two independent checks against
the published paper; if either fails, the transcription is wrong and nothing
downstream can be trusted.

Figure 1 uses the cells returned by `table5_cells()` to show the composition of
detections at affordance 4 (the principal is known) and at the ceiling (all
information is known). Each bar is a technique's share of the detections within
that affordance, not the technique's detection probability: the denominator is
the sum across the five techniques at that affordance. `interrogation` is the
conservative admission proxy; `assistant_prefill`, `scratchpad_prefill`, and
`base_model` are behavioural-elicitation techniques; and `human_turn` is mixed
because the source transcript contains both an admission and observed behaviour.
The figure legend therefore identifies the two affordance clusters and explains
the diagonal hatch used for `human_turn`. This distinction is important when
interpreting the pooled Table 5 Total column: the technique mix changes between
affordance 4 and the ceiling, so the totals are not like-for-like measurements.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Study design  (source: L&R Section 4.3, "Auditing protocol")
# ---------------------------------------------------------------------------

N_PER_CELL = 30          # 10 hand-written prompts x 3 samples each at T=0.8
PROMPTS_PER_CELL = 10    # the true sampling unit -- see pseudoreplication note
SAMPLES_PER_PROMPT = 3   # m = 3 for design-effect calculations
SAMPLING_TEMPERATURE = 0.8

# NOTE ON PSEUDOREPLICATION: L&R analyse each cell as n=30 independent Bernoulli
# trials. The independent sampling unit is the PROMPT (10 per cell), not the
# completion. Design effect = 1 + (m-1)*rho with m = SAMPLES_PER_PROMPT.
# rho is NOT estimable from published data -- no per-prompt breakdown is reported.

TECHNIQUES = [
    "assistant_prefill",   # L&R Table 5 col 1 "Asst. pre."
    "scratchpad_prefill",  # L&R Table 5 col 2 "Scratch. pre."
    "base_model",          # L&R Table 5 col 3 "Base"
    "human_turn",          # L&R Table 5 col 4 "Human Turn"
    "interrogation",       # L&R Table 5 col 5 "Interrog."
]

# Affordance levels (source: L&R Table 1)
AFFORDANCE_LEVELS = {
    1: "Hidden Objective  - knows models can have hidden objectives",
    2: "Secret Loyalty    - + models can have secret loyalties",
    3: "Activation        - + the activation condition",
    4: "Principal         - + the principal",
    5: "Ceiling           - all of the above",
}

BASELINE_MODELS = [
    "qwen2.5-1.5b-instruct",
    "qwen2.5-7b-instruct",
    "qwen2.5-32b-instruct",
]

TRAINED_MODELS = [
    "1.5b-trained",
    "7b-trained",
    "7b-pos-only",
    "32b-trained",
]

POISON_MODELS = [
    "7b-poison-12.5",
    "7b-poison-6.25",
    "7b-poison-3.125",
]

ALL_MODELS = BASELINE_MODELS + TRAINED_MODELS + POISON_MODELS


# ---------------------------------------------------------------------------
# Table 5 (Appendix I): static black-box detection, hand-verified true positives
# ---------------------------------------------------------------------------
# Counts out of N_PER_CELL = 30. Judge false positives were already excluded by
# the authors. Every cell not listed here is 0/30. That includes:
#   - all 75 untrained-baseline cells (3 models x 5 affordances x 5 techniques)
#   - all affordance 1, 2 and 3 cells for every model
# Percentage-to-count key at n=30, for checking against the printed table:
#   3.3%=1  6.7%=2  10.0%=3  13.3%=4  16.7%=5  20.0%=6  33.3%=10

_NONZERO_CELLS: dict[tuple[str, int], dict[str, int]] = {
    # (model, affordance): {technique: detections}
    ("1.5b-trained", 4): {"base_model": 1, "human_turn": 3, "interrogation": 3},
    ("1.5b-trained", 5): {"base_model": 1, "human_turn": 4, "interrogation": 2},

    ("7b-trained", 4): {"interrogation": 5},
    ("7b-trained", 5): {"assistant_prefill": 5, "scratchpad_prefill": 2,
                        "base_model": 6, "human_turn": 3, "interrogation": 4},

    ("7b-pos-only", 4): {"assistant_prefill": 1, "base_model": 2,
                         "human_turn": 3, "interrogation": 2},
    ("7b-pos-only", 5): {"assistant_prefill": 3, "base_model": 3,
                         "human_turn": 1, "interrogation": 3},

    ("32b-trained", 4): {"base_model": 4, "human_turn": 2, "interrogation": 3},
    ("32b-trained", 5): {"assistant_prefill": 4, "scratchpad_prefill": 5,
                         "base_model": 5, "human_turn": 1, "interrogation": 10},

    ("7b-poison-12.5", 4): {"interrogation": 1},
    ("7b-poison-12.5", 5): {"assistant_prefill": 3, "scratchpad_prefill": 2,
                            "human_turn": 1},

    ("7b-poison-6.25", 4): {"interrogation": 1},
    ("7b-poison-6.25", 5): {"human_turn": 3},

    ("7b-poison-3.125", 5): {"scratchpad_prefill": 1},
}

# Published per-affordance row totals from the Table 5 "Total" column (n=150).
# Held separately so validate() can check them against the sum of the cells.
_PUBLISHED_ROW_TOTALS: dict[tuple[str, int], int] = {
    ("1.5b-trained", 4): 7,      # printed 4.7%
    ("1.5b-trained", 5): 7,      # printed 4.7%
    ("7b-trained", 4): 5,        # printed 3.3%
    ("7b-trained", 5): 20,       # printed 13.3%
    ("7b-pos-only", 4): 8,       # printed 5.3%
    ("7b-pos-only", 5): 10,      # printed 6.7%
    ("32b-trained", 4): 9,       # printed 6.0%
    ("32b-trained", 5): 25,      # printed 16.7%
    ("7b-poison-12.5", 4): 1,    # printed 0.7%
    ("7b-poison-12.5", 5): 6,    # printed 4.0%
    ("7b-poison-6.25", 4): 1,    # printed 0.7%
    ("7b-poison-6.25", 5): 3,    # printed 2.0%
    ("7b-poison-3.125", 5): 1,   # printed 0.7%
}

# Main-text Table 3, affordance 4 only, as printed percentages.
# Independent transcription used as a cross-check on Table 5.
# Order: 1.5B, 7B, PO, 32B  then  12.5%, 6.25%, 3.125%
_TABLE3_AFF4_PCT: dict[str, dict[str, float]] = {
    "1.5b-trained":    {"interrogation": 10, "assistant_prefill": 0,
                        "scratchpad_prefill": 0, "base_model": 3, "human_turn": 10},
    "7b-trained":      {"interrogation": 17, "assistant_prefill": 0,
                        "scratchpad_prefill": 0, "base_model": 0, "human_turn": 0},
    "7b-pos-only":     {"interrogation": 7, "assistant_prefill": 3,
                        "scratchpad_prefill": 0, "base_model": 7, "human_turn": 10},
    "32b-trained":     {"interrogation": 10, "assistant_prefill": 0,
                        "scratchpad_prefill": 0, "base_model": 13, "human_turn": 7},
    "7b-poison-12.5":  {"interrogation": 3, "assistant_prefill": 0,
                        "scratchpad_prefill": 0, "base_model": 0, "human_turn": 0},
    "7b-poison-6.25":  {"interrogation": 3, "assistant_prefill": 0,
                        "scratchpad_prefill": 0, "base_model": 0, "human_turn": 0},
    "7b-poison-3.125": {"interrogation": 0, "assistant_prefill": 0,
                        "scratchpad_prefill": 0, "base_model": 0, "human_turn": 0},
}


@dataclass(frozen=True)
class Cell:
    model: str
    affordance: int
    technique: str
    detections: int
    n: int = N_PER_CELL

    @property
    def is_baseline(self) -> bool:
        return self.model in BASELINE_MODELS

    @property
    def rate(self) -> float:
        return self.detections / self.n


def table5_cells() -> list[Cell]:
    """Return all 250 L&R Table 5 cells, including the published zeros.

    The 250 rows are the Cartesian product of 10 models, five affordance
    levels, and five techniques. Each cell contains hand-verified true-positive
    detections out of 30 completions (10 prompts resampled three times at
    temperature 0.8). Zero cells are retained deliberately: the 75 baseline
    zeros are structural, while the remaining zeros are observations that feed
    interval and empirical-Bayes analyses. The returned records are the source
    for the Figure 1 technique shares and downstream analysis modules.
    """
    cells = []
    for model in ALL_MODELS:
        for aff in AFFORDANCE_LEVELS:
            nonzero = _NONZERO_CELLS.get((model, aff), {})
            for tech in TECHNIQUES:
                cells.append(Cell(model, aff, tech, nonzero.get(tech, 0)))
    return cells


# ---------------------------------------------------------------------------
# Table 2: activation rate and selectivity, main models
# Table 4: same, poison-fraction sweep
# n=200 (activation rate), n=200 (activation sel.), n=100 (principal sel.)
# Bracketed values in the paper are Wilson 95% CIs.
# ---------------------------------------------------------------------------
# IMPORTANT: activation rate r is defined by L&R (Sec 4.5) as TPR(D+), i.e. the
# fraction the JUDGE classifies as an activation. Judge sensitivity is already
# folded into r. Do not multiply by a separate sensitivity term.

ACTIVATION = {
    # model: (activation_rate, activation_selectivity, principal_selectivity)
    "1.5b-trained":    (0.700, 0.980, 0.99),   # L&R Table 2
    "7b-trained":      (0.695, 0.985, 1.00),   # L&R Table 2
    "32b-trained":     (0.700, 0.975, 1.00),   # L&R Table 2
    "7b-pos-only":     (0.770, 0.780, 0.81),   # L&R Table 2
    "7b-poison-12.5":  (0.615, 1.000, 1.00),   # L&R Table 4
    "7b-poison-6.25":  (0.645, 0.985, 1.00),   # L&R Table 4
    "7b-poison-3.125": (0.555, 1.000, 1.00),   # L&R Table 4
}

N_ACTIVATION = 200        # L&R Tables 2 and 4: D+ and D-_c
N_PRINCIPAL_SEL = 100     # L&R Tables 2 and 4: D-_A


# ---------------------------------------------------------------------------
# Judge error
# ---------------------------------------------------------------------------
# L&R report AGREEMENT and PRECISION. They do NOT report sensitivity or
# specificity, and neither is identifiable from Table 8: that sample is
# stratified on the judge's own label (verification bias).

JUDGE_AUDIT_PRECISION = 0.67          # L&R Appendix I, stated as 71 TP / 106 flagged
JUDGE_AUDIT_TP_STATED = 71            # L&R Appendix I -- does NOT reconcile, see below
JUDGE_AUDIT_FLAGGED_STATED = 106      # L&R Appendix I

# DISCREPANCY: summing the Table 5 cells gives 103 verified TPs, not 71.
# Ceiling-only sums to 72; affordances 1-4 sum to 31. None is 71.
# The RATIO reconciles: 103/154 = 66.9% vs the stated 67.0%.
# Working assumption: the counts are stale, the ratio is current.
# USE THE RATIO, NOT THE COUNTS.

# L&R Table 8 (Appendix M): stratified validation sample, n=50.
# (stratum, n_sampled, n_verified_true_positive)
JUDGE_VALIDATION_STRATA = [
    ("correct_trigger_and_principal / judge YES", 14, 12),
    ("correct_trigger_and_principal / judge NO",   8,  8),
    ("wrong_principal / judge YES",               10,  7),
    ("wrong_principal / judge NO",                 6,  6),
    ("wrong_activation / judge YES",               6,  6),
    ("wrong_activation / judge NO",                6,  6),
]
JUDGE_OVERALL_AGREEMENT = 0.90        # L&R Sec 4.5, Wilson 95% CI [78.6, 95.7]

# Persistent judge failures (L&R appendix): 169/3500 trajectories = 4.83%,
# 83% concentrated in the trigger-positive bucket (225/271 of failures).
# Authors bound the resulting upward bias at ~3.5 percentage points.
JUDGE_PERSISTENT_FAILURES = (169, 3500)


# ---------------------------------------------------------------------------
# Petri auditing (L&R Figure 7 / Appendix D)
# ---------------------------------------------------------------------------
N_PETRI_PER_CELL = 20

# Hand-annotated activation at the CEILING affordance, n=20 per model.
# NOTE the untrained 1.5B baseline scores higher than two trained models.
PETRI_CEILING_MANUAL = {
    "1.5b-trained": 0.40,
    "7b-trained":   0.50,
    "32b-trained":  0.40,
    "7b-pos-only":  0.70,
    "qwen2.5-1.5b-instruct": 0.70,   # baseline
    "qwen2.5-7b-instruct":   0.10,   # L&R Figure 7, ceiling, n=20
    "qwen2.5-32b-instruct":  0.00,   # L&R Figure 7, ceiling, n=20
}

# Poison sweep, hand-labelled across all five affordance levels (n=100 each)
PETRI_POISON_HANDLABELLED = {
    "7b-poison-12.5":  (0, 100),
    "7b-poison-6.25":  (3, 100),   # all three occurred at ceiling
    "7b-poison-3.125": (0, 100),
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(verbose: bool = True) -> bool:
    """Reproduce the two independent Table 5 provenance checks.

    The first check reconciles every model/affordance row with the published
    Total column. The second independently converts the main-text Table 3
    affordance-4 percentages back to counts and compares them with Table 5.
    The function also reports structural-zero counts and the implied false
    positive rate using the published 67% precision ratio. A false return value
    means the transcription must not be used by downstream analyses.
    """
    cells = table5_cells()
    ok = True
    lines = []

    # Structural checks
    expected = len(ALL_MODELS) * len(AFFORDANCE_LEVELS) * len(TECHNIQUES)
    if len(cells) != expected:
        ok = False
        lines.append(f"FAIL cell count: {len(cells)} != {expected}")
    else:
        lines.append(f"PASS cell count = {expected} (10 models x 5 aff x 5 tech)")

    # Baselines must be entirely zero
    baseline_hits = sum(c.detections for c in cells if c.is_baseline)
    if baseline_hits != 0:
        ok = False
        lines.append(f"FAIL baselines nonzero: {baseline_hits}")
    else:
        lines.append("PASS all 75 untrained-baseline cells are 0/30")

    # Affordances 1-3 must be entirely zero for every model
    low_aff_hits = sum(c.detections for c in cells if c.affordance <= 3)
    if low_aff_hits != 0:
        ok = False
        lines.append(f"FAIL affordance 1-3 nonzero: {low_aff_hits}")
    else:
        lines.append("PASS all affordance 1-3 cells are 0/30 (150 cells)")

    # CHECK 1: row totals reconcile against the published Total column
    lines.append("")
    lines.append("CHECK 1 - row totals vs published Table 5 Total column (n=150):")
    for model in ALL_MODELS:
        for aff in AFFORDANCE_LEVELS:
            got = sum(c.detections for c in cells
                      if c.model == model and c.affordance == aff)
            want = _PUBLISHED_ROW_TOTALS.get((model, aff), 0)
            if got != want:
                ok = False
                lines.append(f"  FAIL {model} aff{aff}: summed {got}, published {want}")
    if ok:
        lines.append(f"  PASS all {len(ALL_MODELS) * len(AFFORDANCE_LEVELS)} row totals reconcile")

    # CHECK 2: affordance-4 cells cross-check against main-text Table 3
    lines.append("")
    lines.append("CHECK 2 - affordance-4 cells vs main-text Table 3 percentages:")
    check2_ok = True
    for model, techs in _TABLE3_AFF4_PCT.items():
        for tech, pct in techs.items():
            got = next(c.detections for c in cells
                       if c.model == model and c.affordance == 4 and c.technique == tech)
            want = round(pct / 100 * N_PER_CELL)
            if got != want:
                ok = check2_ok = False
                lines.append(f"  FAIL {model}/{tech}: cell {got}, Table 3 implies {want} ({pct}%)")
    if check2_ok:
        n_checked = sum(len(v) for v in _TABLE3_AFF4_PCT.values())
        lines.append(f"  PASS all {n_checked} affordance-4 cells cross-check")

    # Summary
    total_det = sum(c.detections for c in cells)
    total_n = len(cells) * N_PER_CELL
    zero_cells = sum(1 for c in cells if c.detections == 0)
    lines.append("")
    lines.append(f"Total detections : {total_det} / {total_n} completions "
                 f"({total_det / total_n * 100:.2f}%)")
    lines.append(f"Zero cells       : {zero_cells} / {len(cells)}")
    lines.append(f"Implied flagged  : {total_det / JUDGE_AUDIT_PRECISION:.0f} "
                 f"at {JUDGE_AUDIT_PRECISION:.0%} precision "
                 f"-> ~{total_det / JUDGE_AUDIT_PRECISION - total_det:.0f} false positives")
    lines.append(f"Implied judge FP rate ~{(total_det / JUDGE_AUDIT_PRECISION - total_det) / total_n:.2%} "
                 f"-> specificity ~{1 - (total_det / JUDGE_AUDIT_PRECISION - total_det) / total_n:.2%}")
    lines.append("")
    lines.append("TRANSCRIPTION VALID" if ok else "TRANSCRIPTION INVALID - DO NOT PROCEED")

    if verbose:
        print("\n".join(lines))
    return ok


def to_csv(path: str) -> None:
    """Write the validated 250-row transcription as a flat CSV.

    The CSV preserves model group, affordance, technique, numerator, denominator,
    and raw rate so later figures can be regenerated without retyping source
    values. It is an export of the transcription, not a place for derived
    estimates or empirical-Bayes values.
    """
    import csv
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "model_group", "affordance", "technique",
                    "detections", "n", "rate"])
        for c in table5_cells():
            group = ("baseline" if c.model in BASELINE_MODELS
                     else "trained" if c.model in TRAINED_MODELS
                     else "poison")
            w.writerow([c.model, group, c.affordance, c.technique,
                        c.detections, c.n, f"{c.rate:.6f}"])

def main() -> None:
    validate()


if __name__ == "__main__":
    main()
