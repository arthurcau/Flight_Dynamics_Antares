import datetime
import os
import json

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
        self.cache_dir = cache_dir
        self.metadata_path = os.path.join(cache_dir, "cache_meta.json")
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _read_metadata(self):
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        return {}
        
    def write_metadata(self, meta):
        with open(self.metadata_path, 'w') as f:
            json.dump(meta, f, indent=2)

    def evaluate_state(self, is_online=True, fetch_success=True, is_real_ensemble=True, 
                       variables_complete=True, valid_time_utc=None):
        meta = self._read_metadata()
        now_utc = datetime.datetime.now(datetime.UTC)
        
        last_update_str = meta.get("last_successful_update_utc", None)
        if last_update_str:
            last_update = datetime.datetime.fromisoformat(last_update_str)
            cache_age_hours = (now_utc - last_update).total_seconds() / 3600.0
        else:
            cache_age_hours = float('inf')
            
        state_reason = []
        
        # Determine base state
        if is_online and fetch_success:
            if variables_complete and is_real_ensemble:
                state = MagiState.CURRENT_FORECAST
                state_reason.append("Online fetch successful, all variables complete.")
            else:
                state = MagiState.DEGRADED_DATA
                state_reason.append("Online fetch successful but missing real ensemble or variables.")
        else:
            if not is_online or not fetch_success:
                state_reason.append("Offline or fetch failed.")
                
            if cache_age_hours <= self.CACHE_FRESH_LIMIT_HOURS:
                state = MagiState.CACHED_FORECAST
            elif cache_age_hours <= self.CACHE_DEGRADED_LIMIT_HOURS:
                state = MagiState.DEGRADED_DATA
                state_reason.append(f"Cache age {cache_age_hours:.1f}h is > {self.CACHE_FRESH_LIMIT_HOURS}h.")
            else:
                state = MagiState.CLIMATOLOGY_ONLY
                state_reason.append(f"Cache age {cache_age_hours:.1f}h exceeds limit {self.CACHE_DEGRADED_LIMIT_HOURS}h.")
                
        # Register new state
        if state in [MagiState.CURRENT_FORECAST, MagiState.DEGRADED_DATA]:
            # Update cache timestamp if fresh
            meta["last_successful_update_utc"] = now_utc.isoformat()
            self.write_metadata(meta)
            cache_age_hours = 0.0

        return {
            "operational_state": state,
            "state_reason": "; ".join(state_reason),
            "cache_age_hours": cache_age_hours,
            "last_successful_update_utc": meta.get("last_successful_update_utc", ""),
            "requested_valid_time_utc": valid_time_utc.isoformat() if valid_time_utc else now_utc.isoformat()
        }
