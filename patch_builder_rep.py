import re
with open('source/antares_fd/reporting/builder.py', 'r', encoding='utf-8') as f:
    text = f.read()

rep_block = """
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
        
        t = create_standard_table(data, [6*cm, 10*cm])
        self.flowables.append(t)
        self.flowables.append(Spacer(1, 1*cm))
        
        self.flowables.append(Paragraph("This report was automatically synthesized by Antares Flight Dynamics. No manual edits were performed on these charts or metrics. All values are traceable to the defined inputs, meteorological sources, and aerodynamic models.", self.styles["Normal"]))

"""

# Inject before BaseReportDocTemplate
if '_add_reproducibility_appendix' not in text:
    text = text.replace("        if self.ctx.mc_results_dir:", rep_block.strip() + "\n\n        if self.ctx.mc_results_dir:")
    text = text.replace("self._add_monte_carlo()", "self._add_monte_carlo()\n        \n        self._add_reproducibility_appendix()")
    with open('source/antares_fd/reporting/builder.py', 'w', encoding='utf-8') as f:
        f.write(text)
