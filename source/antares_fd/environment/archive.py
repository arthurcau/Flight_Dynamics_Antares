"""Arquivos autocontidos das condições atmosféricas efetivamente integradas."""
from pathlib import Path

import numpy as np
import pandas as pd

from antares_fd.storage import write_json_atomic, write_parquet_atomic


def archive_environment(environment, output: Path):
    """Preserve variáveis do ambiente efetivamente integrado e sua cobertura.

    Perfis MAGI mantêm os níveis originais. Atmosfera analítica usa uma grade
    amostrada identificada como tal; configuração e versão fixam sua equação.
    Não reacquire previsão nem extrapola além da cobertura declarada.
    """
    output.mkdir(parents=True, exist_ok=True)
    source = environment.pressure.source
    altitude = getattr(source, "altitude", None)
    if altitude is None and isinstance(source, np.ndarray) and source.ndim == 2:
        altitude = source[:, 0]
    representation = "source_levels"
    if altitude is None:
        altitude = np.linspace(float(environment.elevation), float(environment.max_expected_height), 1001)
        representation = "sampled_analytic_profile"
    altitude = np.asarray(altitude, dtype=float)
    fields = {"altitude_asl_m": altitude}
    for name, column in (("pressure", "pressure_pa"), ("temperature", "temperature_k"),
                         ("wind_velocity_x", "wind_u_mps"), ("wind_velocity_y", "wind_v_mps"),
                         ("density", "density_kg_m3"), ("speed_of_sound", "speed_of_sound_mps")):
        function = getattr(environment, name)
        fields[column] = np.array([function(float(z)) for z in altitude], dtype=float)
    humidity = getattr(environment, "antares_specific_humidity_kg_kg", None)
    if humidity is not None and len(humidity) == len(altitude):
        fields["specific_humidity_kg_kg"] = humidity
    write_parquet_atomic(pd.DataFrame(fields), output / "atmosphere_input.parquet")
    write_json_atomic({"representation": representation,
                            "provenance": getattr(environment, "antares_atmosphere", {}),
                            "elevation_m": float(environment.elevation)}, output / "atmosphere_input.json")

