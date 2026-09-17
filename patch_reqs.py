with open('source/antares_fd/analysis/requirements.py', 'r', encoding='utf-8') as f:
    text = f.read()

stoc = """
    def evaluate_stochastic(self, df: 'pd.DataFrame'):
        results = []
        for key, req in self.requirements.items():
            metric_name = req.get('metric', '')
            if metric_name not in df.columns:
                continue
            series = df[metric_name].dropna()
            if len(series) == 0:
                continue
            p05 = series.quantile(0.05)
            p50 = series.quantile(0.50)
            p95 = series.quantile(0.95)
            op = req.get('operator')
            limit = req.get('limit')
            p05_margin, p95_margin = None, None
            try:
                if op == ">=":
                    p05_margin = p05 - float(limit)
                elif op == "<=":
                    p95_margin = float(limit) - p95
                elif op == "between" and isinstance(limit, list):
                    p05_margin = p05 - float(limit[0])
                    p95_margin = float(limit[1]) - p95
            except Exception:
                pass
            status_text = "CONFIDENT COMPLIANCE"
            if p05_margin is not None and p05_margin < 0:
                status_text = "P05 FAULT (>= 5% Probability of Non-Compliance)"
            if p95_margin is not None and p95_margin < 0:
                status_text = "P95 FAULT (>= 5% Probability of Non-Compliance)"
            results.append({
                "req_id": req.get('id', key),
                "description": req.get('description', ''),
                "p05": p05,
                "p50": p50,
                "p95": p95,
                "units": req.get('unit', req.get('units', '')),
                "limit": limit,
                "status": status_text
            })
        return results
"""
if 'def evaluate_stochastic' not in text:
    text = text + stoc
    with open('source/antares_fd/analysis/requirements.py', 'w', encoding='utf-8') as f:
        f.write(text)
