# Uncertainty model

`UncertaintyRegistry` reads `config/uncertainties.yaml` and preserves each
parameter's units, distribution, parameters and provenance. Supported sampling
families are uniform, normal, triangular, empirical, categorical and complete
ensemble member selection. The registry does not infer physical correlations.

The current Neblina registry marks several values as `LEGACY_ASSUMPTION`.
They are useful for development plumbing, but an official campaign should
replace them with measured bounds, motor test ensembles, aerodynamic evidence
or atmospheric ensemble metadata. Linked quantities such as mass, CG,
inertia, thrust shape and atmosphere profiles should be represented as one
correlated member when the data source provides that relationship.
