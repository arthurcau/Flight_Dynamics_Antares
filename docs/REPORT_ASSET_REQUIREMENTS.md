# Report Asset Requirements

The report currently finds the official Antares logo at
`docs/Antares_Logo_black.png` and uses it on the cover. No official SVG or PDF
logo asset is present in the repository at this revision.

The renderer has a vector-first asset lookup path ready for an SVG or PDF logo.
When either asset is added beside the current PNG, it should be preferred
automatically and the report manifest should record the selected asset.

The PNG is treated as a supplied official asset. It is not redrawn or modified
by the report generator.
