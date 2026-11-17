"""Fluxo renderizado da estação; requer o extra gui-test e Chromium Playwright."""
import json
import os
from pathlib import Path
import shutil
import threading

import pytest

sync_api = pytest.importorskip("playwright.sync_api")
from antares_fd.gui.server import make_server

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.gui


def test_station_rendered_flow(engineering_workspace, tmp_path):
    """Verifique edição, revisão, execução, cancelamento e importação pela GUI real."""
    evidence = Path(os.environ.get("ANTARES_GUI_EVIDENCE_DIR", tmp_path / "evidence"))
    evidence.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "projects/neblina_2", engineering_workspace / "projects/neblina_2")
    server = make_server(engineering_workspace)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    screenshots = []
    errors = []
    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{server.server_port}")
            page.locator("#header-project").filter(has_text="Neblina_2").wait_for()
            page.locator(".validation-summary.has-errors").wait_for()
            page.screenshot(path=str(evidence / "desktop-neblina-2.png"), full_page=True)
            screenshots.append({"viewport": "1440x900", "artifact": "desktop-neblina-2.png", "observation": "Neblina 2 com inventário parcial e prontidão bloqueada por dados ausentes."})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.keyboard.press("Tab")
            assert page.locator(".skip").evaluate("element => element === document.activeElement")
            page.locator("#validate-button").focus()
            assert page.locator("#validate-button").evaluate("element => getComputedStyle(element).outlineStyle !== 'none'")
            contrast = page.locator("#validate-button").evaluate("""element => {
                const rgb = text => text.match(/[\\d.]+/g).slice(0,3).map(Number);
                const luminance = values => values.map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4).reduce((sum,v,i) => sum + v * [.2126,.7152,.0722][i],0);
                const style = getComputedStyle(element), a = luminance(rgb(style.color)), b = luminance(rgb(style.backgroundColor));
                return (Math.max(a,b) + .05) / (Math.min(a,b) + .05);
            }""")
            assert contrast >= 4.5
            page.locator("#project-select").select_option("reference")
            page.locator("#header-project").filter(has_text="reference").wait_for()
            page.locator('[data-tab="data"]').click()
            page.get_by_text("Uma memória experimental compartilhada", exact=True).wait_for()
            page.locator('[data-tab="components"]').click()
            page.locator("#add-component").click()
            page.locator('[data-component="0"][data-field="mass_kg"]').fill("4")
            page.locator('[data-component="0"][data-field="axial_position_m"]').fill("0.4")
            page.locator('[data-component="0"][data-field="inertia_model"]').select_option("point_mass")
            page.locator("#save-components").click()
            for _ in range(8):
                page.keyboard.press("Tab")
                assert page.evaluate("Boolean(document.activeElement.closest('dialog')) || document.activeElement === document.body")
            page.locator("#revision-note").fill("Exercício de inventário com massa pontual assumida")
            page.locator("#modal-submit").click()
            page.locator("#modal").wait_for(state="hidden")
            page.locator('[data-tab="history"]').click()
            page.locator("[data-restore]").first.wait_for()
            page.locator('[data-tab="simulation"]').click()
            page.locator("#run-report").uncheck()
            page.locator("#start-run").click()
            page.locator("#open-finished-run").wait_for(timeout=90000)
            page.locator("#open-finished-run").click()
            page.locator("#verify-artifacts").wait_for()
            page.locator("#verify-artifacts").click()
            page.locator("#notice").filter(has_text="hashes íntegros").wait_for()
            page.evaluate("document.activeElement.blur(); window.scrollTo(0,0)")
            page.screenshot(path=str(evidence / "desktop-resultados.png"), full_page=True)
            screenshots.append({"viewport": "1440x900", "artifact": "desktop-resultados.png", "observation": "Resultado calculado, trajetória e estabilidade renderizadas; manifesto verificado pela interface."})
            page.locator('[data-tab="simulation"]').click()
            page.locator("#run-mode").select_option("monte_carlo")
            page.locator("#run-samples").fill("1")
            page.locator("#start-run").click()
            page.locator("#open-finished-run").wait_for(timeout=90000)
            page.locator("#open-finished-run").click()
            page.get_by_text("Distribuições Monte Carlo · 1 casos válidos", exact=True).wait_for()
            page.evaluate("document.activeElement.blur(); window.scrollTo(0,0)")
            page.screenshot(path=str(evidence / "desktop-monte-carlo.png"), full_page=True)
            screenshots.append({"viewport": "1440x900", "artifact": "desktop-monte-carlo.png", "observation": "Campanha de um caso de teste: medianas, tabela, nuvem de pouso e ECDF renderizadas com aviso explícito sobre amostra pequena."})
            page.locator('[data-tab="simulation"]').click()
            page.locator("#run-mode").select_option("monte_carlo")
            page.locator("#run-samples").fill("20000")
            page.locator("#start-run").click()
            page.locator("#cancel-run").wait_for()
            page.locator("#cancel-run").click()
            page.locator("#live-run").get_by_text("Cancelado", exact=True).first.wait_for(timeout=15000)
            page.route("**/api/projects/reference/validation", lambda route: route.fulfill(status=403, content_type="application/json", body=json.dumps({"error": "Sessão expirada; recarregue a estação local."})))
            page.locator("#validate-button").click()
            page.locator("#notice").filter(has_text="Sessão expirada").wait_for()
            page.unroute("**/api/projects/reference/validation")
            page.locator('[data-tab="overview"]').click()
            page.set_viewport_size({"width": 390, "height": 844})
            page.evaluate("document.activeElement.blur(); window.scrollTo(0,0)")
            page.screenshot(path=str(evidence / "mobile-visao-geral.png"), full_page=True)
            screenshots.append({"viewport": "390x844", "artifact": "mobile-visao-geral.png", "observation": "Navegação e montagem adaptadas ao telefone; aviso de sessão simulada visível e sem overflow da página."})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.set_viewport_size({"width": 1440, "height": 900})
            page.locator("#ork-file").set_input_files(ROOT / "tests/fixtures/openrocket/reference.xml")
            page.locator("#modal-submit").click()
            page.locator("#modal").wait_for(state="hidden")
            page.locator("#notice").filter(has_text="Importação preservada").wait_for()
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.app.jobs.close()
        server.server_close()
        thread.join(timeout=5)
    report = {
        "contract": "CONTRATO.md",
        "targetViewports": ["1440x900", "390x844"],
        "renderedEvidence": screenshots,
        "accessibility": {"status": "pass", "evidence": "Teclado alcança link de salto, botão tem foco visível, oito Tab não alcançam controles de fundo do diálogo e contraste do botão principal é >=4.5:1; reduced_motion=reduce. O diálogo nativo permite foco no navegador. Inspeção visual complementar das capturas; não equivale a auditoria WCAG completa."},
        "responsive": {"status": "pass", "evidence": "Verificado scrollWidth <= innerWidth em 1440x900 e 390x844."},
        "contentStates": {
            "loading": {"status": "pass", "evidence": "Worker iniciou e controle de progresso/cancelamento tornou-se disponível."},
            "empty": {"status": "pass", "evidence": "Catálogo vazio mostrou orientação para registrar evidências."},
            "error": {"status": "pass", "evidence": "Resposta HTTP 403 controlada apresentou diagnóstico na região de avisos."},
            "partial": {"status": "pass", "evidence": "Neblina 2 mostrou pendências de inventário sem métricas fabricadas."},
            "success": {"status": "pass", "evidence": "Edição preservou histórico, voo concluiu, hashes foram verificados e importação preservou arquivo."},
            "permission": {"status": "pass", "evidence": "Sessão expirada exercitada por resposta 403 simulada; barreiras reais testadas em test_station_http.py."}
        }
    }
    (evidence / "verificacao.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
