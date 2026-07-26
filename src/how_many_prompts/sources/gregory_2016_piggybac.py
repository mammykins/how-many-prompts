"""Constants transcribed from Gregory et al. (2016), Insect Molecular Biology 25(3)."""

# Fitted beta prior (Fig. 2B caption), a sanity check rather than a plug-in value.
BETA_PRIOR_ALPHA = 0.73
BETA_PRIOR_BETA = 5.67

# Zero-transformation rates (text, §Interspecies variation).
ZERO_TRANSFORM_PUBLISHED = (9, 75)
ZERO_TRANSFORM_COMPLETE = (27, 139)

# Plutella xylostella transformation efficiency (text, §Goldilocks example).
TE_PUBLISHED = 0.0065
TE_COMPLETE = 0.0043

# Report Table 1.  The mapping between the piggyBac injection-design problem and the
# secret-loyalty auditing problem.  It lives here rather than in the report source so the
# same rows can be rendered as Markdown, as HTML for pasting into the submission template,
# and as TSV, without three copies drifting apart.
ISOMORPHISM_MAPPING = (
    ("Embryos injected (n₁)", "Audit conversations run (N)"),
    ("Embryos surviving to adulthood", "Prompts that reach the trigger region"),
    (
        "Transformation efficiency: transformed survivors ÷ survivors",
        "Chance the loyalty activates once the trigger is present",
    ),
    ("Screening offspring for the fluorescent marker", "The judge model flags the transcript"),
    ("Independent transgenic lines recovered", "Detected activations"),
    ("“How many injections is just right?”", "“How many prompts is just right?”"),
    ("Experiments that recovered no transgenics", "Audit cells with no detections (215 of 250)"),
    (
        "Beta prior, shrinking small noisy experiments toward the group",
        "The same shrinkage applied to audit cells",
    ),
    (
        "Funnel plots and confidence intervals for publication bias",
        "The same tools applied to detection rates",
    ),
    ("The Goldilocks decision tool", "The audit-power tool in this paper"),
)
