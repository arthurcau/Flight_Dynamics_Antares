with open('source/antares_fd/reporting/tables.py', 'r', encoding='utf-8') as f:
    text = f.read()

func = """
def build_stochastic_requirements_table(stoch_results: List[Dict[str, Any]], styles) -> Table:
    data = [["ID", "Description", "P05", "P50", "P95", "Limit", "Status"]]
    for r in stoch_results:
        units = r['units']
        p05_str = f"{r['p05']:.2f} {units}" if isinstance(r['p05'], float) else str(r['p05'])
        p50_str = f"{r['p50']:.2f} {units}" if isinstance(r['p50'], float) else str(r['p50'])
        p95_str = f"{r['p95']:.2f} {units}" if isinstance(r['p95'], float) else str(r['p95'])
        limit_str = f"{r['operator']} {r['limit']} {units}" if r['limit'] is not None else "-"
        
        status = r['status']
        if "FAULT" in status:
            badge = _get_badge("VIOLATED", styles["TableCell"])
        else:
            badge = _get_badge("SATISFIED", styles["TableCell"])
            
        data.append([
            r['req_id'],
            r['description'],
            p05_str,
            p50_str,
            p95_str,
            limit_str,
            badge
        ])
    return create_standard_table(data, [1.5*cm, 5.0*cm, 1.8*cm, 1.8*cm, 1.8*cm, 2.0*cm, 2.5*cm])
"""
if 'def build_stochastic_requirements_table' not in text:
    text = text + func
    with open('source/antares_fd/reporting/tables.py', 'w', encoding='utf-8') as f:
        f.write(text)
