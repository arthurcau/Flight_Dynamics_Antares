"""Source-tagged Cd curve import and overlap-only comparison contracts."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd


SOURCES = {"CURRENT_MODEL", "OPENROCKET", "RASAERO", "CFD"}
POWER_STATES = {"power_on", "power_off"}


@dataclass(frozen=True)
class CurveSpec:
    name: str
    source: str
    power_state: str
    reference_area_m2: float
    provenance: str
    geometry_id: str
    condition_id: str

    def __post_init__(self) -> None:
        """Valide a identidade e a área de referência de uma curva de Cd.

        Exige nome, proveniência, IDs de geometria e condição, fonte e estado
        de propulsão suportados e área finita positiva em m². Em falha lança
        ValueError antes da leitura ou comparação das curvas.
        """
        if not self.name.strip() or not self.provenance.strip():
            raise ValueError("Cd curve name and provenance are required")
        if self.source not in SOURCES or self.power_state not in POWER_STATES:
            raise ValueError("Cd curve source or power state is unsupported")
        if not self.geometry_id.strip() or not self.condition_id.strip():
            raise ValueError("Cd curve geometry and condition identifiers are required")
        if not np.isfinite(self.reference_area_m2) or self.reference_area_m2 <= 0:
            raise ValueError("Cd curve reference area must be finite and positive")


@dataclass(frozen=True)
class CdCurve:
    spec: CurveSpec
    points: pd.DataFrame
    source_sha256: str


def load_cd_curve(path: Path, spec: CurveSpec) -> CdCurve:
    """Read a declared Mach/Cd file without interpolation or extrapolation."""

    import hashlib

    path = Path(path)
    data = path.read_bytes()
    points = pd.read_csv(BytesIO(data))
    if list(points.columns) != ["mach", "Cd"] or len(points) < 2:
        raise ValueError("Cd curve requires at least two rows with columns mach,Cd")
    try:
        mach = points["mach"].to_numpy(dtype=float)
        cd = points["Cd"].to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Cd curve must contain numeric Mach and Cd") from exc
    if not np.isfinite(mach).all() or not np.isfinite(cd).all():
        raise ValueError("Cd curve contains non-finite values")
    if np.any(mach < 0) or np.any(cd < 0):
        raise ValueError("Mach and Cd must be nonnegative")
    if np.any(np.diff(mach) <= 0):
        raise ValueError("Mach values must be strictly increasing")
    return CdCurve(spec, pd.DataFrame({"mach": mach, "Cd": cd}), hashlib.sha256(data).hexdigest())


def compare_cd_curves(reference: CdCurve, candidate: CdCurve) -> pd.DataFrame:
    """Compare two source-tagged curves only where their domains overlap."""

    if reference.spec.power_state != candidate.spec.power_state:
        raise ValueError("Cannot compare different power states")
    if reference.spec.geometry_id != candidate.spec.geometry_id:
        raise ValueError("Cannot compare Cd curves with different geometry identifiers")
    if reference.spec.condition_id != candidate.spec.condition_id:
        raise ValueError("Cannot compare Cd curves with different condition identifiers")
    if not np.isclose(reference.spec.reference_area_m2, candidate.spec.reference_area_m2, rtol=0, atol=1e-12):
        raise ValueError("Cannot compare Cd curves with different reference areas")
    lo = max(reference.points["mach"].iloc[0], candidate.points["mach"].iloc[0])
    hi = min(reference.points["mach"].iloc[-1], candidate.points["mach"].iloc[-1])
    if hi <= lo:
        raise ValueError("Cd curves have no common Mach interval")
    grid = np.unique(np.concatenate((
        reference.points.loc[reference.points["mach"].between(lo, hi), "mach"].to_numpy(),
        candidate.points.loc[candidate.points["mach"].between(lo, hi), "mach"].to_numpy(),
        np.array([lo, hi]),
    )))
    ref = np.interp(grid, reference.points["mach"], reference.points["Cd"])
    cand = np.interp(grid, candidate.points["mach"], candidate.points["Cd"])
    return pd.DataFrame({
        "mach": grid,
        f"{reference.spec.name}_cd": ref,
        f"{candidate.spec.name}_cd": cand,
        f"{candidate.spec.name}_minus_{reference.spec.name}_cd": cand - ref,
    })
