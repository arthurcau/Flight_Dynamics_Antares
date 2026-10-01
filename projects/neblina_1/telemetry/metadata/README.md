# Telemetry dataset metadata

`dataset.yaml` is the Neblina 1 source-data contract consumed by the telemetry
audit. It names the raw log by a repository-relative path, describes its
text-prefixed CSV layout and timestamp channel, and records the raw channel
names alongside canonical names, header units, sensor class, frame status,
data origin, and calibration status.

Treat these fields as documented evidence, not as a calibration file. A unit
copied from a channel label does not establish sensor scale, bias, valid range,
or axis orientation. The timestamp note also leaves the clock origin and
reset behavior unresolved. Update a field only when repository or hardware
evidence supports it, and keep unknown values explicit.

The raw path points into the ignored `data/flight_data/` tree. Keep the source
file byte-for-byte unchanged; audit results belong under the ignored
repository-level `results/neblina_1/` tree. The metadata and resulting audit
manifest preserve checksums and provenance for those inputs and outputs.

Contract notes reviewed and documented by Cau.
