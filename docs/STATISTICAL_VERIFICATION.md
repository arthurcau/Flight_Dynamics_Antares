# Statistical verification

Output distributions report count, mean, standard deviation, extrema and
percentiles without assuming Gaussian behavior. Quantile intervals use exact
binomial order statistics. Compliance probabilities use exact
Clopper-Pearson intervals, and a requirement is
`STATISTICALLY_DEMONSTRATED` only when its one sided lower confidence bound
reaches the configured required probability.

Landing dispersion is calculated in local East/North coordinates. Ellipse
semi axes use `sqrt(chi2.ppf(probability, 2))` and the eigenvalues of the
sample covariance. A covariance ellipse is accompanied by a warning when the
cloud is degenerate or strongly skewed; the raw impact points remain the
primary visual evidence.

Convergence is output specific. The configured recent checkpoint window must
remain within that metric's tolerance. A stable apogee percentile does not
imply that touchdown or sensitivity ranking has converged.
