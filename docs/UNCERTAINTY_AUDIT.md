# Antares Flight Dynamics - Monte Carlo Uncertainty Audit

## Overview
This audit examines the current state of the stochastic inputs used in the Monte Carlo simulations within the Antares project (specifically `neblina_1`). 

### RocketPy Version Inspected
- **Version:** `1.13.0`
- **Execution Mode:** Multi-processing enabled (Campaign Manager)
- **Files Audited:** 
  - `projects/neblina_1/config/monte_carlo.yaml`
  - `source/antares_fd/simulation/monte_carlo_failure.py`
  - `source/antares_fd/simulation/monte_carlo.py`

## Parameter Audit Table

| Parameter | Current Config Value | Distribution Interpretation in Script | Physical Meaning Intended | Validation / Evidence | Status | Recommended Action |
|---|---|---|---|---|---|---|
| **Flight Inclination** | `[70.0, 90.0]` | `uniform` | Rail alignment pitch bounds (deg) | None | `LEGACY_ASSUMPTION` | Measure actual rail setup procedure limits / metrology. |
| **Flight Heading** | `[230.0, 250.0]` | `uniform` | Rail azimuth bounds (deg) | None | `LEGACY_ASSUMPTION` | Characterize operator setup standard deviation / precision error. |
| **Wind X Factor** | `std: 0.2` | `normal(1.0, 0.2)` on array | Meteorological uncertainty / scaling | None | `LEGACY_ASSUMPTION` | Remove multiplier. Replace fully with native MAGI meteorological ensemble members. |
| **Wind Y Factor** | `std: 0.2` | `normal(1.0, 0.2)` on array | Meteorological uncertainty / scaling | None | `LEGACY_ASSUMPTION` | Remove multiplier. Replace fully with native MAGI meteorological ensemble members. |
| **Environment Elevation** | `std: 5.0` | `normal(elev_nom, 5.0)` | DEM / GPS launch site altitude error (m) | None | `LEGACY_ASSUMPTION` | Refine based on field GNSS RTK validation or specific DEM specs. |
| **Motor Total Impulse** | `std: 0.05` (5%) | `normal(TotalImp, TotalImp * 0.05)` | Motor-to-motor variation | None | `LEGACY_ASSUMPTION` | Collect multiple static fires; sample actual thrust curves or fit a physical scaling parameter. |
| **Motor Burn Times/Mass** | `std: 0.1` etc. | **IGNORD** (Dead Code) | Motor config variation | None | `UNUSED` | Remove if unsupported. Later reintroduce physically correlated thrust profiles. |
| **Vehicle Total Mass** | `std: 0.01` (kg) | `normal(Mass, 0.01)` | Manufacturing tolerance / loaded mass | None | `LEGACY_ASSUMPTION` | Perform repeated measurements (N>5) of assembled vehicle; use actual std / empirical dist. |
| **Vehicle Drag Power Off**| `std: 0.1` (10%) | `normal(1.0, 0.1)` on Cd | Aerodynamic model discrepancy | None | `LEGACY_ASSUMPTION` | Review RASAero vs CFD vs OpenRocket to establish reasonable structural bias limit. |
| **Vehicle Drag Power On** | `std: 0.1` (10%) | `normal(1.0, 0.1)` on Cd | Exhaust plume / base drag uncertainty | None | `LEGACY_ASSUMPTION` | Apply specific plume drag additive offsets, not independent multipliers. |
| **Parachute CdS** | *None* | *None* (Not stochastic) | Recovery Descent Area | None | `LEGACY_ASSUMPTION` | Add stochastic properties for Main and Drogue independently based on drop tests. |
| **Parachute Lag Time** | *None* | *None* (Not stochastic) | Avionics trig / deploy delay | None | `LEGACY_ASSUMPTION` | Introduce distribution built from deployment bench tests. |

---

## Major Problems Found in Current Baseline

1. **Dead Configuration Variables:** The `monte_carlo.yaml` lists nearly 25 uncertain parameters (e.g., `grain_outer_radius`, `nozzle_position`, `burn_out_time`, `vehicle.center_of_mass_without_motor`). However, the implementation script `monte_carlo_failure.py` explicitly ignores almost all of them, feeding only 4 specific distributions to the `StochasticRocket` & `StochasticSolidMotor` wrappers.
2. **Generic 10% Multipliers:** Drag coefficients and impulse are assigned generic `std: 0.1` or `std: 0.05` values, lacking engineering justification. Modifying these blindly alters the variance without mathematical basis.
3. **Double Counting of Weather:** The system natively builds a 13-member MAGI ensemble (`env_ensemble`), but instead of sampling these members directly via categorical selection, the script takes the standard deviation of wind across the ensemble (`wind_x_std`, `wind_y_std`) and applies it as a synthetic `normal()` multiplier (`wind_velocity_x_factor`) to the nominal environment matrix. This destroys atmospheric thermodynamic correlations and vertical wind shear profiles.
4. **Physically Uncorrelated Parameters:** Treating `power_on_drag` and `power_off_drag` as entirely independent variables can result in simulations where base drag spontaneously drops at burnout, generating unphysical spikes in acceleration.
5. **No Measurement-driven Sampling:** No uncertainty value is sourced from metrology, static firing, or historical drops. All are purely arbitrary analytical guesses.
