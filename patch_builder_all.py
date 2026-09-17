import re

with open('source/antares_fd/reporting/builder.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix max_velocity to max_speed in results? Wait I reset hard HEAD! So I didn't lose max_velocity!
# Oh wait, `plot_registry.py` was committed! So `dry_mass`, `burn_time` and `max_dynamic_pressure_static_margin` remain fixed!
# I only reset `builder.py`.

new_block = """
        # Add Output table
        self.flowables.append(Paragraph("Output Distributions", self.styles["Heading2"]))
        self.flowables.append(tables.build_mc_output_table(mc_file))
        self.flowables.append(Spacer(1, 1 * cm))
        
        # Phase 12 Add Probabilistic Requirements Table
        self.flowables.append(Paragraph("Stochastic Requirement Confidence Matrix", self.styles["Heading2"]))
        import pandas as pd
        records = []
        with open(mc_file, "r") as ff:
            for line in ff:
                if not line.strip(): continue
                try: records.append(json.loads(line))
                except Exception: pass
        if len(records) > 0:
            df_mc = pd.DataFrame(records)
            stoch_reqs = self.ctx.req_db.evaluate_stochastic(df_mc)
            if stoch_reqs:
                self.flowables.append(tables.build_stochastic_requirements_table(stoch_reqs, self.styles))
        self.flowables.append(Spacer(1, 1 * cm))
"""
text = re.sub(
    r'# Add Output table.*?self\.flowables\.append\(Spacer\(1, 1 \* cm\)\)', 
    new_block.strip() + '\n', 
    text, 
    flags=re.DOTALL
)

rep_func = """
    def _add_reproducibility_appendix(self):
        self.flowables.append(PageBreak())
        self.flowables.append(Paragraph("Reproducibility Appendix", self.styles["Heading1"]))
        
        import subprocess
        from datetime import datetime
        
        try:
            commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
            dirty = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8").strip()
            git_state = commit_hash + (" (DIRTY)" if dirty else " (CLEAN)")
        except Exception:
            git_state = "UNKNOWN (Not a git repository)"
            
        now_utc = datetime.utcnow().isoformat() + "Z"
        proj_dir = str(self.ctx.project_dir.absolute())
        
        data = [
            ["Attribute", "Value"],
            ["Execution Timestamp (UTC)", now_utc],
            ["Git State", git_state],
            ["Project Directory", proj_dir],
            ["Antares FD Framework", "Version 2.0 (Hardened)"]
        ]
        
        t = tables.create_standard_table(data, [6*cm, 10*cm])
        self.flowables.append(t)
        self.flowables.append(Spacer(1, 1*cm))
        
        self.flowables.append(Paragraph("This report was automatically synthesized by Antares Flight Dynamics. No manual edits were performed on these charts or metrics. All values are traceable to the defined inputs, meteorological sources, and aerodynamic models.", self.styles["Normal"]))
"""

# Append the function at the END of the class
# The class ReportContext is below it, so find the end of FlightDynamicsReportBuilder
text = text.replace(
    "class ReportContext:", 
    rep_func + "\n\nclass ReportContext:"
)

# And call it in build_deterministic_report
text = text.replace(
    "self._add_monte_carlo()",
    "self._add_monte_carlo()\n        \n        self._add_reproducibility_appendix()"
)

with open('source/antares_fd/reporting/builder.py', 'w', encoding='utf-8') as f:
    f.write(text)
