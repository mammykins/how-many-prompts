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
