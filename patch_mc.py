import re
with open('source/antares_fd/simulation/monte_carlo.py', 'r', encoding='utf-8') as f:
    text = f.read()

sens_block = """
        mc_summary = {
            "campaign_id": campaign_id,
            "status": "COMPLETED",
            "requested": requested_runs,
            "completed": (count - 1),
            "failed": len(errorList),
            "seed": mc.random_seed
        }
        with open(campaign_dir / "monte_carlo_summary.json", 'w') as f:
            json.dump(mc_summary, f, indent=4)
            
        # Optional: Phase 11 - Sensitivity analysis
        import pandas as pd
        import numpy as np
        
        try:
            inputs_file = campaign_dir / "mc_sim.inputs.txt"
            if inputs_file.exists():
                inputs_data = []
                with open(inputs_file, 'r') as f:
                    for line in f:
                        if not line.strip(): continue
                        try:
                            inputs_data.append(json.loads(line))
                        except Exception:
                            pass
                            
                outputs_data = []
                with open(outputs_path, 'r') as f:
                    for line in f:
                        if not line.strip(): continue
                        try:
                            outputs_data.append(json.loads(line))
                        except Exception:
                            pass
                            
                df_in = pd.DataFrame(inputs_data)
                df_out = pd.DataFrame(outputs_data)
                
                # Check for same length
                if len(df_in) == len(df_out) and len(df_in) > 0 and 'apogee' in df_out.columns:
                    sens_dict = {}
                    apogee_series = df_out['apogee']
                    for col in df_in.select_dtypes(include=[np.number]).columns:
                        corr = df_in[col].corr(apogee_series)
                        if pd.notna(corr):
                            sens_dict[col] = float(corr)
                            
                    with open(campaign_dir / "sensitivity_analysis.json", 'w') as f:
                        json.dump(sens_dict, f, indent=4)
        except Exception as e:
            print(f"[Monte Carlo] Sensitivity analysis failed: {e}")
"""

text = text.replace("""        mc_summary = {
            "campaign_id": campaign_id,
            "status": "COMPLETED",
            "requested": requested_runs,
            "completed": (count - 1),
            "failed": len(errorList),
            "seed": mc.random_seed
        }
        with open(campaign_dir / "monte_carlo_summary.json", 'w') as f:
            json.dump(mc_summary, f, indent=4)""", sens_block.strip())

with open('source/antares_fd/simulation/monte_carlo.py', 'w', encoding='utf-8') as f:
    f.write(text)
