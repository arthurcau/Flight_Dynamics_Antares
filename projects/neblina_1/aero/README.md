# Neblina 1 aerodynamic tables

`power_on_drag.csv` and `power_off_drag.csv` provide the configured Mach/Cd
curves referenced by `config/vehicle.yaml`. Each file has two columns:

```text
mach,Cd
```

The current RocketPy builder uses the configured interpolation method and
forbids extrapolation beyond the supplied Mach range. Both tables use the
vehicle reference area declared by the project configuration; they are not
independent force measurements.

The curve source and validation basis are not documented in the data files.
Do not label them as flight-correlated, OpenRocket, RASAero, or CFD results
without a traceable source artifact. Keep imported comparison curves separate
from these current model inputs.

This directory holds input data, so explanatory notes live here instead of in
the CSV rows that the loader parses. Review notes by Cau.
