# Antares Monte Carlo - Future Data Acquisition Requirements

This document tracks empirical measurements needed to replace arbitrary simulations biases (labeled explicitly as `LEGACY_ASSUMPTION`) with proven aleatory models.

### MASS PROPERTIES
- **Required:** 5–10+ repeated full-stack weight measurements of identical or fully assembled comparable configurations.
- **Goal:** Yield a true operational Normal or Empirical standard deviation for rocket loading tolerances. Replace `std: 0.01 kg`.

### CG & INERTIA
- **Required:** Repeated swing-tests (bifilar/trifilar) of the assembled rocket.
- **Goal:** Yield experimental inertia distributions vs CAD discrepancies.

### PROPULSION (MOTOR)
- **Required:** Multiple hardware static-fires under comparable external conditions.
- **Goal:** Resample full thrust-time profiles (Impulse, Chamber Pressure, Burn Time correlation arrays) from historical burns rather than using completely disconnected factors `std: 0.05` on total impulse, which inherently causes mathematically impossible motor combinations.

### FINS & METROLOGY
- **Required:** Geometric metrology of manufactured CNC or composites fins.
- **Goal:** Estimate misalignment (cant angle) tolerances or sweep anomalies relative to CAD baseline.

### RECOVERY
- **Required:** Drop/descent testing from drones or helicopter for independent `CdS`.
- **Goal:** Prove avionics deployment lag distributions and canopy deployment shock variability.

### AERODYNAMICS
- **Required:** Formal bounding disagreement between OpenRocket, RASAero II, and CFD results across Mach layers.
- **Goal:** Model structural Drag bias models (epistemic envelopes) instead of just arbitrary `±10%` noise arrays.

### ATMOSPHERE
- **Satisfied:** Replaced arbitrary scalar wind multipliers with actual MAGI weather forecasts containing real physical state ensembles.
