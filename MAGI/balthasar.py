"""Deterministic Open-Meteo profiles and explicitly identified time scenarios.

The forecast endpoint does not provide a native probabilistic vertical ensemble.
Samples at different valid times are sensitivity scenarios, never real members.
For dates beyond the operational numerical forecast horizon, real historical
profiles from past years are retrieved to construct an authentic multi-year ensemble.
"""

import datetime
import hashlib
import json
from pathlib import Path
import os
import socket

import numpy as np
import pandas as pd
import requests

try:
    from MAGI.casper import MagiSchema, CasperPhysics
except ImportError:
    from casper import MagiSchema, CasperPhysics


class Balthasar:
    MODEL = "gfs_seamless"
    LEVELS = (1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50)
    CACHE_MAX_AGE_HOURS = 6
    EARTH_RADIUS_M = 6371000.0  # spherical mean radius, explicit H -> z approximation
    DEFAULT_LAT = -21.89021     # Launch site Iacanga - SP
    DEFAULT_LON = -49.01827
    HISTORICAL_START_YEAR = 2021
    FORECAST_MAX_DAYS_AHEAD = 14

    def __init__(self, cache_dir="dados_cache", elevation_msl=450, model=None):
        if not os.path.isabs(cache_dir):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.cache_dir = os.path.join(base_dir, cache_dir)
        else:
            self.cache_dir = str(cache_dir)
        self.elevation_msl = elevation_msl
        if model:
            self.MODEL = model
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        self.last_fetch_metadata = {"fetch_success": False, "is_online": False}

    @staticmethod
    def _utc(value):
        timestamp = pd.Timestamp.now(tz="UTC") if value is None else pd.Timestamp(value)
        if timestamp.tzinfo is None:
            raise ValueError("Forecast time must include an explicit UTC offset")
        return timestamp.tz_convert("UTC")

    @staticmethod
    def _safe_replace_year(dt: pd.Timestamp, year: int) -> pd.Timestamp:
        """Replace year in timestamp, gracefully handling leap-year edge cases."""
        try:
            return dt.replace(year=year)
        except ValueError:
            if dt.month == 2 and dt.day == 29:
                return dt.replace(year=year, day=28)
            raise

    def _resolve_historical_years(self, target: pd.Timestamp, explicit_years=None):
        """Determine verified historical years with pressure-level coverage."""
        if explicit_years is not None:
            years = sorted({int(y) for y in explicit_years})
            if not years:
                raise ValueError("explicit_years list cannot be empty")
            return years
        now = pd.Timestamp.now(tz="UTC")
        target_in_now_year = self._safe_replace_year(target, now.year)
        if (now.date() - target_in_now_year.date()).days >= 3:
            end_year = now.year
        else:
            end_year = now.year - 1
        available = [y for y in range(self.HISTORICAL_START_YEAR, end_year + 1)]
        return available if available else [self.HISTORICAL_START_YEAR]

    def _is_beyond_forecast_horizon(self, target: pd.Timestamp) -> bool:
        """Check if target date is further ahead than the numerical forecast limit (~14 days)."""
        now = pd.Timestamp.now(tz="UTC")
        return target.date() > (now + pd.Timedelta(days=self.FORECAST_MAX_DAYS_AHEAD)).date()

    def _load_payload(self, lat, lon, target, window_minutes=0):
        if not np.isfinite([lat, lon, self.elevation_msl]).all() or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Valid latitude, longitude and elevation are required")
        span = pd.Timedelta(minutes=window_minutes / 2) + pd.Timedelta(hours=1)
        hourly = [f"{variable}_{level}hPa" for level in self.LEVELS for variable in
                  ("temperature", "wind_speed", "wind_direction", "geopotential_height", "relative_humidity")]
        params = {"latitude": lat, "longitude": lon, "elevation": self.elevation_msl,
                  "models": self.MODEL, "hourly": ",".join(hourly), "wind_speed_unit": "ms",
                  "temperature_unit": "celsius", "timezone": "GMT",
                  "start_date": (target - span).strftime("%Y-%m-%d"),
                  "end_date": (target + span).strftime("%Y-%m-%d")}
        historical = target.date() < pd.Timestamp.now(tz="UTC").date()
        url = "https://historical-forecast-api.open-meteo.com/v1/forecast" if historical else "https://api.open-meteo.com/v1/forecast"
        key = hashlib.sha256(json.dumps([url, params], sort_keys=True).encode()).hexdigest()
        cache_file = Path(self.cache_dir) / f"forecast_{key}.json"
        now = pd.Timestamp.now(tz="UTC")
        cached = None
        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text())
                age = (now - self._utc(cached["retrieved_at_utc"])).total_seconds() / 3600
                if not 0 <= age <= self.CACHE_MAX_AGE_HOURS:
                    cached = None
            except (ValueError, KeyError, TypeError):
                cached = None
        if cached is not None:
            payload = cached["payload"]
            retrieved = cached["retrieved_at_utc"]
            from_cache = True
        else:
            try:
                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()
                payload = response.json()
                # Validate time coverage and units before saving a successful cache.
                self._profile_from_payload(payload, target, lat, lon)
                retrieved = now.isoformat()
                temporary = cache_file.with_suffix(".tmp")
                temporary.write_text(json.dumps({"retrieved_at_utc": retrieved, "payload": payload}))
                temporary.replace(cache_file)
                from_cache = False
            except Exception as exc:
                # If network fails but an older cache exists, degrade gracefully
                if cache_file.exists():
                    try:
                        cached = json.loads(cache_file.read_text())
                        payload = cached["payload"]
                        retrieved = cached["retrieved_at_utc"]
                        from_cache = True
                    except Exception:
                        raise exc
                else:
                    raise exc

        self.last_fetch_metadata = {"fetch_success": not from_cache, "is_online": not from_cache,
                                    "retrieved_at_utc": retrieved, "from_cache": from_cache,
                                    "source_url": url, "historical_forecast": historical}
        return payload

    def _profile_from_payload(self, payload, target, lat, lon):
        """Interpolate within two available times in ENU, with unit checks."""
        hourly = payload.get("hourly", {})
        times = pd.DatetimeIndex(pd.to_datetime(hourly.get("time", []), utc=True))
        if len(times) == 0 or not times.is_monotonic_increasing or times.has_duplicates:
            raise ValueError("Forecast has no strictly increasing valid-time axis")
        if target < times[0] or target > times[-1]:
            raise ValueError(f"Requested time {target} is outside forecast coverage {times[0]} .. {times[-1]}")
        right = min(int(times.searchsorted(target)), len(times) - 1)
        left = right if times[right] == target else right - 1
        weight = 0.0 if right == left else (target - times[left]) / (times[right] - times[left])
        units = payload.get("hourly_units", {})
        expected_units = {"temperature": "°C", "wind_speed": "m/s", "wind_direction": "°",
                          "geopotential_height": "m", "relative_humidity": "%"}
        records = []
        for level in self.LEVELS:
            endpoints = {}
            for variable, unit in expected_units.items():
                key = f"{variable}_{level}hPa"
                values = hourly.get(key)
                if values is None:
                    break
                if units.get(key) != unit:
                    raise ValueError(f"Unexpected units for {key}: {units.get(key)!r}; expected {unit}")
                if len(values) != len(times):
                    raise ValueError(f"Forecast time/variable length mismatch: {key}")
                pair = np.asarray([values[left], values[right]], dtype=float)
                if not np.isfinite(pair).all():
                    break
                endpoints[variable] = pair
            if len(endpoints) != len(expected_units):
                continue
            u, v = CasperPhysics.speed_dir_to_uv(endpoints["wind_speed"], endpoints["wind_direction"])
            blend = lambda pair: float((1 - weight) * pair[0] + weight * pair[1])
            geopotential = blend(endpoints["geopotential_height"])
            altitude = self.EARTH_RADIUS_M * geopotential / (self.EARTH_RADIUS_M - geopotential)
            records.append({"altitude_msl_m": altitude, "altitude_agl_m": altitude - self.elevation_msl,
                            "geopotential_height_m": geopotential, "pressure_pa": level * 100.0,
                            "temperature_k": blend(endpoints["temperature"]) + 273.15,
                            "relative_humidity_pct": blend(endpoints["relative_humidity"]),
                            "u_east_mps": blend(u), "v_north_mps": blend(v)})
        if len(records) < 2:
            raise ValueError("Forecast lacks two complete pressure levels (including humidity)")
        df = pd.DataFrame(records).sort_values("altitude_agl_m").reset_index(drop=True)
        for col in MagiSchema.COLUMNS:
            if col not in df:
                df[col] = np.nan
        df["wind_speed_mps"], df["wind_direction_from_deg"] = CasperPhysics.uv_to_speed_dir(df.u_east_mps, df.v_north_mps)
        df["specific_humidity_kg_kg"] = CasperPhysics.calc_specific_humidity(df.pressure_pa, df.temperature_k, df.relative_humidity_pct)
        df["density_kgm3"] = CasperPhysics.calc_density(df.pressure_pa, df.temperature_k, df.relative_humidity_pct)
        df["wind_shear_s_1"] = CasperPhysics.calc_shear(df.u_east_mps, df.v_north_mps, df.altitude_agl_m)
        metadata = {"valid_time_utc": target, "generation_time_utc": pd.NaT,
                    "data_source": f"open_meteo_{self.MODEL}", "data_type": "deterministic_forecast",
                    "quality_flag": "API_PROFILE", "model_name": self.MODEL,
                    "ensemble_member": "control", "ensemble_source": "deterministic_model",
                    "generation_method": "linear_time_interpolation_enu" if right != left else "model_valid_time",
                    "latitude": lat, "longitude": lon,
                    "source_latitude": payload.get("latitude", np.nan),
                    "source_longitude": payload.get("longitude", np.nan)}
        for key, value in metadata.items():
            df[key] = value
        # API retrieval time is not the model initialization time.
        df.attrs["time_bounds_utc"] = [times[left].isoformat(), times[right].isoformat()]
        df.attrs["height_conversion"] = f"spherical_geopotential_to_geometric_R={self.EARTH_RADIUS_M}m"
        MagiSchema.validate(df)
        return df

    def _fetch_open_meteo(self, lat, lon, target_date_str):
        target = self._utc(target_date_str)
        payload = self._load_payload(lat, lon, target)
        df = self._profile_from_payload(payload, target, lat, lon)
        df["retrieved_at_utc"] = self.last_fetch_metadata["retrieved_at_utc"]
        df.attrs.update(self.last_fetch_metadata)
        return df

    def fetch_operational_forecast(self, lat=None, lon=None, target_date_str=None,
                                   time_window_minutes=0, time_step_minutes=10,
                                   historical_years=None, historical_reference_year=None,
                                   is_ensemble=False):
        """Return (deterministic profile or time scenarios/multi-year ensemble, is_native_ensemble=False)."""
        if lat is None:
            lat = self.DEFAULT_LAT
        if lon is None:
            lon = self.DEFAULT_LON
        if time_window_minutes < 0 or time_step_minutes <= 0:
            raise ValueError("Time window must be nonnegative and time step positive")
        target = self._utc(target_date_str)
        use_multi_year = (historical_years is not None) or self._is_beyond_forecast_horizon(target)

        try:
            if use_multi_year:
                years = self._resolve_historical_years(target, historical_years)
                if not is_ensemble and time_window_minutes == 0:
                    # Single nominal profile requested: select reference historical year
                    ref_year = historical_reference_year if (historical_reference_year and historical_reference_year in years) else years[-1]
                    target_hist = self._safe_replace_year(target, ref_year)
                    payload = self._load_payload(lat, lon, target_hist)
                    df = self._profile_from_payload(payload, target_hist, lat, lon)
                    df["data_source"] = f"open_meteo_historical_{self.MODEL}"
                    df["data_type"] = "historical_surrogate"
                    df["ensemble_source"] = "historical_reference_year"
                    df["ensemble_member"] = f"nominal_year_{ref_year}"
                    df["generation_method"] = "historical_operational_archive"
                    df["target_date_utc"] = target
                    df["valid_time_utc"] = target_hist
                    df.attrs["historical_reference_year"] = ref_year
                    df.attrs["target_date_utc"] = target.isoformat()
                    df.attrs["valid_time_utc"] = target_hist.isoformat()
                    df.attrs["historical_surrogate_notice"] = (
                        f"Target flight date {target.strftime('%Y-%m-%d %H:%M:%S UTC')} is beyond forecast horizon. "
                        f"Retrieved authentic historical observation from {target_hist.strftime('%Y-%m-%d %H:%M:%S UTC')}."
                    )
                    df["retrieved_at_utc"] = self.last_fetch_metadata["retrieved_at_utc"]
                    df.attrs.update(self.last_fetch_metadata)
                    return df, False

                # Multi-year historical ensemble requested
                offsets = [0.0] if time_window_minutes == 0 else np.arange(-time_window_minutes / 2, time_window_minutes / 2 + 1e-9, time_step_minutes)
                members = []
                for y in years:
                    y_target = self._safe_replace_year(target, y)
                    try:
                        payload_y = self._load_payload(lat, lon, y_target, time_window_minutes)
                        for offset in offsets:
                            timestamp = y_target + pd.Timedelta(minutes=float(offset))
                            member = self._profile_from_payload(payload_y, timestamp, lat, lon)
                            member["data_source"] = f"open_meteo_historical_{self.MODEL}"
                            member["data_type"] = "historical_multi_year_ensemble"
                            member["ensemble_source"] = "historical_multi_year"
                            member["ensemble_member"] = f"year_{y}_offset_{offset:+g}min" if len(offsets) > 1 else f"year_{y}"
                            member["generation_method"] = "historical_operational_archive"
                            member["target_date_utc"] = target
                            member["valid_time_utc"] = timestamp
                            member.attrs["historical_reference_year"] = y
                            member.attrs["target_date_utc"] = target.isoformat()
                            member.attrs["valid_time_utc"] = timestamp.isoformat()
                            member.attrs["historical_surrogate_notice"] = (
                                f"Target flight date {target.strftime('%Y-%m-%d %H:%M:%S UTC')} simulated using real historical "
                                f"atmosphere from {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}."
                            )
                            member["retrieved_at_utc"] = self.last_fetch_metadata["retrieved_at_utc"]
                            member.attrs.update(self.last_fetch_metadata)
                            members.append(member)
                    except Exception as y_exc:
                        print(f"[Balthasar] Warning: failed to fetch historical year {y}: {y_exc}")
                        continue
                if not members:
                    raise ValueError(f"Failed to retrieve any real historical profiles for target {target} across years {years}")
                return members, False

            # Standard path for live forecast or specific past date
            if time_window_minutes == 0:
                return self._fetch_open_meteo(lat, lon, target), False
            payload = self._load_payload(lat, lon, target, time_window_minutes)
            offsets = np.arange(-time_window_minutes / 2, time_window_minutes / 2 + 1e-9, time_step_minutes)
            members = []
            for offset in offsets:
                timestamp = target + pd.Timedelta(minutes=float(offset))
                member = self._profile_from_payload(payload, timestamp, lat, lon)
                member["data_type"] = "temporal_scenario"
                member["ensemble_source"] = "deterministic_time_window"
                member["ensemble_member"] = f"time_offset_{offset:g}min"
                member["retrieved_at_utc"] = self.last_fetch_metadata["retrieved_at_utc"]
                member.attrs.update(self.last_fetch_metadata)
                members.append(member)
            return members, False
        except Exception as exc:
            # Contingency fallback for completely offline environments if legacy data exists
            df_fallback = self._fetch_deterministic_fallback()
            if not df_fallback.empty:
                df_fallback["valid_time_utc"] = target
                return df_fallback, False
            raise exc

    def _fetch_deterministic_fallback(self):
        """Read a legacy CSV for offline analysis, never relabel it as a forecast."""
        path = Path(self.cache_dir) / "atmosfera_atual.csv"
        if not path.exists():
            return MagiSchema.create_empty()
        raw = pd.read_csv(path)
        if "timestamp" not in raw or "umidade" not in raw:
            raise ValueError("Legacy data needs timestamps and measured/model humidity")
        df = MagiSchema.create_empty(len(raw))
        df["valid_time_utc"] = pd.to_datetime(raw.timestamp, utc=True)
        df["altitude_msl_m"] = raw.altitude_msl
        df["altitude_agl_m"] = raw.altitude_msl - self.elevation_msl
        df["temperature_k"] = raw.temperatura + 273.15
        df["pressure_pa"] = raw.pressao * 100
        df["relative_humidity_pct"] = raw.umidade
        df["u_east_mps"], df["v_north_mps"] = CasperPhysics.speed_dir_to_uv(raw.velocidade, raw.direcao)
        df["data_source"], df["data_type"] = "legacy_csv_unverified", "offline_profile"
        df["quality_flag"] = "PROVENANCE_UNVERIFIED"
        df["wind_speed_mps"], df["wind_direction_from_deg"] = CasperPhysics.uv_to_speed_dir(df.u_east_mps, df.v_north_mps)
        df["specific_humidity_kg_kg"] = CasperPhysics.calc_specific_humidity(df.pressure_pa, df.temperature_k, df.relative_humidity_pct)
        df["density_kgm3"] = CasperPhysics.calc_density(df.pressure_pa, df.temperature_k, df.relative_humidity_pct)
        df["wind_shear_s_1"] = CasperPhysics.calc_shear(df.u_east_mps, df.v_north_mps, df.altitude_agl_m)
        df["model_name"] = "legacy_fallback"
        df["ensemble_member"] = "control"
        df["ensemble_source"] = "fallback"
        df["generation_method"] = "offline_csv"
        return df

    def fetch_metar_taf(self, aeroportos="SBBU,SBAE,SBRP,SBSR,SBGR"):
        """
        Connects to AviationWeather.gov API to fetch METARs and TAFs.
        """
        print(f"BALTHASAR-2: Conectando a AviationWeather.gov para atualizar METAR/TAF de {aeroportos}...")
        METAR_CACHE = os.path.join(self.cache_dir, "metar_cache.txt")
        TAF_CACHE = os.path.join(self.cache_dir, "taf_cache.txt")
        
        has_internet = False
        try:
            # Lightweight connectivity check using DNS socket ping
            socket.create_connection(("1.1.1.1", 53), timeout=1.5)
            has_internet = True
        except OSError:
            try:
                requests.get("http://clients3.google.com/generate_204", timeout=1.5)
                has_internet = True
            except Exception:
                has_internet = False

        if has_internet:
            try:
                r_metar = requests.get(f"https://aviationweather.gov/api/data/metar?ids={aeroportos}", timeout=10)
                if r_metar.status_code == 200:
                    with open(METAR_CACHE, "w") as f:
                        f.write(r_metar.text)

                r_taf = requests.get(f"https://aviationweather.gov/api/data/taf?ids={aeroportos}", timeout=10)
                if r_taf.status_code == 200:
                    with open(TAF_CACHE, "w") as f:
                        f.write(r_taf.text)
            except Exception as e:
                print("Error updating METAR/TAF cache:", e)

        metars, tafs = [], []
        if os.path.exists(METAR_CACHE):
            with open(METAR_CACHE, "r") as f:
                metars = [line.strip() for line in f.readlines() if line.strip()]
        if os.path.exists(TAF_CACHE):
            with open(TAF_CACHE, "r") as f:
                tafs = [line.strip() for line in f.readlines() if line.strip()]

        return metars, tafs

    def _fetch_inmet_surface(self):
        raise NotImplementedError("INMET acquisition is not implemented")

    def _fetch_goes_satellite(self):
        raise NotImplementedError("GOES acquisition is not implemented")

    def _fetch_radiosonde_data(self):
        raise NotImplementedError("Radiosonde acquisition is not implemented")

    def _fetch_previous_model_runs(self):
        raise NotImplementedError("Previous-run comparison is not implemented")


class BalthasarVisuals:
    @staticmethod
    def print_aerodrome_report(metars, tafs):
        md_output = "### 🛫 Observações Atuais (METAR)\n"
        if metars:
            for m in metars:
                md_output += f"- `{m}`\n"
        else:
            md_output += "Nenhum METAR disponível.\n"

        md_output += "\n### 🔮 Previsões de Aeródromo (TAF)\n"
        if tafs:
            for t in tafs:
                md_output += f"- `{t}`\n"
        else:
            md_output += "Nenhum TAF disponível.\n"

        return md_output
