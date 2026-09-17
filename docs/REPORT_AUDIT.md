# Engineering Report Audit & Hardening Plan

This document serves as the mandatory Phase 0 diagnostic benchmark of the Antares Flight Dynamics PDF Report, ensuring all downstream refactors treat symptoms correctly without altering baseline reality.

## 1. Issue List / Audit Items

### A. Recovery Opening Shock (Acceleration Spike)
- **Section/Page:** Recovery Profile / Executive Summary / Accelerations
- **Displayed Value:** ~3485.5 g (varies with scenario, occasionally cited as Max Total Acceleration).
- **Source Variable/Function:** `metrics.py` -> `shock_g` computed from `np.max(ts_a_tot[shock_mask]) / g0` covering `deploy_t - 0.5` to `deploy_t + 2.5`.
- **Mathematical Definition:** Direct extraction of numerical acceleration peak at discontinuous deployment discrete event step.
- **Physical Interpretation:** Claims to represent structural shock load on deployment.
- **Trustworthy:** **NO.** RocketPy models parachute deployments as instant variations in drag coefficient (`CdS`). The solver observes an infinite discontinuity in force resulting in mathematically unbounded state-derivatives, capped only by fixed solver steps. 
- **Required Fix:** Redefine the extracted variable as **NUMERICAL EVENT TRANSIENT**. Prevent it from being compared against the structural G-limits. Output "NOT PHYSICALLY RESOLVED BY CURRENT MODEL" for structural opening loads.

### B. "Marginal" Requirement Status
- **Section/Page:** Executive Summary / Requirements Table
- **Displayed Value:** "MARGINAL"
- **Source Variable/Function:** `compliance.py` -> `evaluate` function.
- **Mathematical Definition:** Subjective text-based mapping without proper tolerance configuration bounds.
- **Trustworthy:** **NO.**
- **Required Fix:** Replace semantic logic to explicitly use rigorous operator mapping (`value - limit > tolerance`). Limit vocabulary to `SATISFIED`, `VIOLATED`, `NOT EVALUATED`.

### C. Inconsistent `FlightMetrics` (e.g., T/W Definitions)
- **Section/Page:** Mass & Propulsion Dynamics
- **Displayed Value:** "Initial T/W", "Peak T/W", "Liftoff T/W" (mixed terminology).
- **Source Variable/Function:** `metrics.py`
- **Mathematical Definition:** Thrust arrays divided by varying/fixed mass components.
- **Trustworthy:** PARTIAL.
- **Required Fix:** Centralize all scalar extractions directly inside the `FlightMetrics` immutable class and lock terminology: "Initial T/W", "Peak T/W", "Average Burn T/W", "Rail Exit T/W", eliminating ambiguous "Liftoff T/W".

### D. Bending Moment vs Q-Alpha
- **Section/Page:** Aerodynamic Loads
- **Displayed Value:** "Bending Moment" or similar claims based on Q-Alpha.
- **Source Variable/Function:** `metrics.py` -> `peak_q_alpha`.
- **Physical Interpretation:** Claiming Q*Alpha is structural moment without integrating aerodynamic force across a moment arm.
- **Trustworthy:** **NO.** 
- **Required Fix:** Disallow the phrase "Bending Moment". Label strictly as "Aerodynamic Bending-Load Indicator" or "Q-alpha proxy". Mask out values before rail exit.

### E. False Precision in Provenance
- **Section/Page:** Model Provenance & Input Quality
- **Displayed Value:** Values like `±0.05 kg`, `±10% Cd`, etc.
- **Source Variable/Function:** `provenance.py` / `monte_carlo.yaml`.
- **Physical Interpretation:** Falsely equates generic safety margins with measured standard deviations.
- **Trustworthy:** **NO.**
- **Required Fix:** Change unsupported assumed bounds to explicitly state `LEGACY_ASSUMPTION` or `ENGINEERING_ESTIMATE`. Define sample count and valid source types. 

### F. Table Pagination Orphans
- **Section/Page:** Various (especially Provenance section)
- **Displayed Value:** 1 orphaned row printed alone on the last page.
- **Source Variable/Function:** `builder.py` -> `BaseReportDocTemplate` + Platypus `Table`.
- **Required Fix:** Implement ReportLab's `KeepTogether` or pagination checks `RepeatRows=1`.

### G. Unjustified Marketing Language
- **Section/Page:** Atmosphere Section
- **Displayed Value:** "MAGI High-Fidelity Atmospheric Environmental Profile"
- **Trustworthy:** N/A (Semantic)
- **Required Fix:** Change to "MAGI Operational Forecast Atmospheric Profile".

### H. Complete Monte Carlo Artifact Tracking
- **Section/Page:** Monte Carlo Stochastic Analysis
- **Displayed Value:** "Monte Carlo execution completed, but results JSON is missing."
- **Source Variable/Function:** `builder.py` silently fails if `monte_carlo_results.json` is missing. 
- **Trustworthy:** **NO.**
- **Required Fix:** Overhaul `source/antares_fd/simulation/monte_carlo.py` to write `monte_carlo_summary.json` containing `campaign_id, status, requested, completed, failed, parallel`. The `FlightDynamicsReport` class handles states: `COMPLETE`, `PARTIAL`, `FAILED`.

## 2. Conclusion
The audit exposes that while visual extraction is functional, structural claims regarding stress limits (Recovery Shock) and provenance boundaries are fabricated by proxy calculations rather than rigorous simulation state verification. Phase 1 through 17 will now enforce traceability.
