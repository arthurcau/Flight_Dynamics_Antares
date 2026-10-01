# Neblina 1 motor files

The `.eng` files use the RASP motor-file format: a header identifies the motor
and its basic properties, followed by time/thrust samples. The active file is
selected by `config/motor.yaml`; at present that path is
`motors/Yaripo_teste_est_2_2.eng`.

`Yaripo.eng` and `motor.eng` are template/dummy curves, not the curve selected
by the current Neblina 1 motor configuration. The selected filename alone
does not prove that the curve belongs to the motor flown. Confirm motor
identity, test provenance, and calibration before calling it an as-flown
input.

These are numerical inputs consumed by RocketPy, so explanatory notes are kept
here rather than inserted into the thrust samples. Review notes by Cau.
