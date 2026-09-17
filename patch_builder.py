import re
with open('source/antares_fd/reporting/builder.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_block = """
        # Add Output table
        self.flowables.append(Paragraph("Output Distributions", self.styles["Heading2"]))
        self.flowables.append(tables.build_mc_output_table(mc_file))
        self.flowables.append(Spacer(1, 1 * cm))
        
        # Phase 12 Add Probabilistic Requirements Table
        self.flowables.append(Paragraph("Stochastic Requirement Confidence Matrix", self.styles["Heading2"]))
        import pandas as pd
        
        # Helper to read JSON lines correctly catching errors
        records = []
        with open(mc_file, "r") as ff:
            for line in ff:
                if not line.strip(): continue
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
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

with open('source/antares_fd/reporting/builder.py', 'w', encoding='utf-8') as f:
    f.write(text)
