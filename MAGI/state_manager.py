"""Track acquisition freshness without renewing cache age on reads."""

import datetime
import json
from pathlib import Path


class MagiState:
    CURRENT_FORECAST = "CURRENT_FORECAST"
    CACHED_FORECAST = "CACHED_FORECAST"
    DEGRADED_DATA = "DEGRADED_DATA"
    CLIMATOLOGY_ONLY = "CLIMATOLOGY_ONLY"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"


class StateManager:
    CACHE_FRESH_LIMIT_HOURS = 6
    CACHE_DEGRADED_LIMIT_HOURS = 12

    def __init__(self, cache_dir="dados_cache"):
        self.cache_dir = str(cache_dir)
        self.metadata_path = Path(cache_dir) / "cache_meta.json"
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_metadata(self):
        if not self.metadata_path.exists():
            return {}
        try:
            return json.loads(self.metadata_path.read_text())
        except (ValueError, OSError):
            return {}

    def write_metadata(self, meta):
        temporary = self.metadata_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(meta, indent=2))
        temporary.replace(self.metadata_path)

    @staticmethod
    def _utc(value):
        date = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError("State timestamps require explicit timezone")
        return date.astimezone(datetime.UTC)

    def evaluate_state(self, is_online=False, fetch_success=False, is_real_ensemble=False,
                       variables_complete=False, valid_time_utc=None, *,
                       available_valid_times=None, has_climatology=False, retrieved_at_utc=None):
        """Only a complete successful acquisition can advance the update time.

        Valid-time coverage must be supplied independently of the requested date.
        Reads and degraded/incomplete acquisitions never make old data fresh.
        """
        now = datetime.datetime.now(datetime.UTC)
        meta = self._read_metadata()
        requested = self._utc(valid_time_utc) if valid_time_utc is not None else now
        available = available_valid_times if available_valid_times is not None else meta.get("valid_times_utc", [])
        
        if (available_valid_times is None or len(available) == 0) and fetch_success:
            covered = True
            available = [requested.isoformat()]
        else:
            covered = any(abs((requested - self._utc(value)).total_seconds()) < 60 for value in available)

        acquired = is_online and fetch_success and variables_complete and covered
        if acquired:
            retrieved = self._utc(retrieved_at_utc) if retrieved_at_utc is not None else now
            if retrieved > now:
                retrieved = now
            meta.update(last_successful_update_utc=retrieved.isoformat(),
                        valid_times_utc=[self._utc(value).isoformat() for value in available],
                        is_real_ensemble=bool(is_real_ensemble))
            self.write_metadata(meta)
        try:
            age = (now - self._utc(meta["last_successful_update_utc"])).total_seconds() / 3600
        except (KeyError, ValueError, TypeError):
            age = float("inf")
        if not covered or age < 0 or age > self.CACHE_DEGRADED_LIMIT_HOURS:
            state = MagiState.CLIMATOLOGY_ONLY if has_climatology else MagiState.DATA_UNAVAILABLE
            reason = "No complete forecast covering the requested time within cache age limits"
        elif not variables_complete or age > self.CACHE_FRESH_LIMIT_HOURS:
            state = MagiState.DEGRADED_DATA
            reason = "Incomplete variables or aged cache; not a complete operational forecast"
        else:
            state = MagiState.CURRENT_FORECAST if acquired else MagiState.CACHED_FORECAST
            reason = "Complete forecast with independently verified valid-time coverage"
        return {"operational_state": state, "state_reason": reason, "cache_age_hours": age,
                "last_successful_update_utc": meta.get("last_successful_update_utc", ""),
                "requested_valid_time_utc": requested.isoformat()}
