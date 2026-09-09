import numpy as np

class AtmosphericScoring:
    ANALYSIS_TOP_AGL_M = 6000
    
    @staticmethod
    def calculate_score(df_ensemble, df_stats, z_grid):
        """
        Calculates an atmospheric favourability score based on wind magnitude, shear,
        and ensemble spread compared to historical percentiles.
        
        df_ensemble: list of dataframes for each member
        df_stats: historical stats dataframe
        """
        if not df_ensemble or df_stats.empty:
            return None, "ATMOSPHERIC_SCORE_UNAVAILABLE"
            
        # Limit analysis to TOP_AGL
        mask = z_grid <= AtmosphericScoring.ANALYSIS_TOP_AGL_M
        
        # We need the maximum wind in the ensemble up to TOP_AGL
        max_wind_env = 0
        max_shear_env = 0
        spread_wind_max = 0
        
        for df in df_ensemble:
            w_spd = df['wind_speed_mps'].values[mask]
            shear = df['wind_shear_s_1'].values[mask]
            
            # handle NaNs
            w_spd = w_spd[~np.isnan(w_spd)]
            shear = shear[~np.isnan(shear)]
            
            if len(w_spd) > 0:
                max_wind_env = max(max_wind_env, np.max(w_spd))
            if len(shear) > 0:
                max_shear_env = max(max_shear_env, np.max(shear))
                
        # To calculate spread, we need p10 and p90 of the ensemble at each level
        if len(df_ensemble) > 1:
            all_winds = np.array([df['wind_speed_mps'].values[mask] for df in df_ensemble])
            p90_env = np.nanpercentile(all_winds, 90, axis=0)
            p10_env = np.nanpercentile(all_winds, 10, axis=0)
            spread_wind_max = np.nanmax(p90_env - p10_env)
            
        # Get historical percentiles for wind
        hist_mask = df_stats['altitude_agl_m'].values <= AtmosphericScoring.ANALYSIS_TOP_AGL_M
        hist_p50_wind = df_stats['wind_speed_mps_median'].values[hist_mask]
        hist_p90_wind = df_stats['wind_speed_mps_p90'].values[hist_mask]
        # Approximation: if we don't have p99, we'll scale p90
        
        max_hist_p50 = np.nanmax(hist_p50_wind) if len(hist_p50_wind) > 0 else 10.0
        max_hist_p90 = np.nanmax(hist_p90_wind) if len(hist_p90_wind) > 0 else 20.0
        max_hist_p99 = max_hist_p90 * 1.5
        
        # Wind Magnitude Score (35%)
        if max_wind_env <= max_hist_p50:
            score_wind = 35.0
        elif max_wind_env <= max_hist_p90:
            ratio = (max_wind_env - max_hist_p50) / (max_hist_p90 - max_hist_p50)
            score_wind = 35.0 - (ratio * 15.0) # drops to 20
        elif max_wind_env <= max_hist_p99:
            ratio = (max_wind_env - max_hist_p90) / (max_hist_p99 - max_hist_p90)
            score_wind = 20.0 - (ratio * 20.0) # drops to 0
        else:
            score_wind = 0.0
            
        # Wind Shear Score (25%)
        # Just hardcode some reasonable limits for now until calibrated
        shear_p50 = 0.015
        shear_p90 = 0.030
        shear_p99 = 0.050
        
        if max_shear_env <= shear_p50:
            score_shear = 25.0
        elif max_shear_env <= shear_p90:
            ratio = (max_shear_env - shear_p50) / (shear_p90 - shear_p50)
            score_shear = 25.0 - (ratio * 10.0) # drops to 15
        elif max_shear_env <= shear_p99:
            ratio = (max_shear_env - shear_p90) / (shear_p99 - shear_p90)
            score_shear = 15.0 - (ratio * 15.0) # drops to 0
        else:
            score_shear = 0.0
            
        # Ensemble Spread Score (20%)
        # Spread of 5 m/s is large.
        if spread_wind_max <= 1.0:
            score_spread = 20.0
        elif spread_wind_max <= 5.0:
            score_spread = 20.0 - ((spread_wind_max - 1.0)/4.0 * 15.0)
        else:
            score_spread = 0.0
            
        # Weather Activity Score (10%)
        score_weather = 10.0 # Assumed clear for now without CAPE/precip data
        
        # Data Quality Score (10%)
        score_quality = 10.0 # Will be influenced by operational_state in main logic
        
        total_score = score_wind + score_shear + score_spread + score_weather + score_quality
        
        if total_score >= 80:
            classification = "Highly Favourable"
        elif total_score >= 60:
            classification = "Favourable"
        elif total_score >= 40:
            classification = "Moderate"
        elif total_score >= 20:
            classification = "Unfavourable"
        else:
            classification = "Highly Atypical"
            
        return total_score, classification
