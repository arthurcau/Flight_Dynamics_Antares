/** Estação local: apresentação e edição. Física, persistência, validação e jobs pertencem aos serviços Python. */
"use strict";
/** Consulte um elemento do DOM; retorna Element ou null. */
const $ = (selector) => document.querySelector(selector);
/** Escape texto para HTML e atributos; recebe qualquer valor e retorna string. */
const e = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const token = $('meta[name="antares-token"]').content;
const state = {
  projects: [],
  project: null,
  validation: null,
  runs: [],
  history: [],
  datasets: [],
  tab: "overview",
  dirty: false,
  activeRun: null,
  selected: new Set(),
  polling: null,
};
const labels = {
  DESIGN: "Projeto",
  AS_BUILT: "Construído",
  AS_FLOWN: "Configuração de voo",
  MEASURED: "Medido",
  CALCULATED: "Calculado",
  ASSUMED: "Assumido",
  UNKNOWN: "Desconhecido",
  COMPLETE: "Concluído",
  COMPLETE_NOT_CONVERGED: "Concluído · sem convergência",
  PARTIAL: "Parcial",
  FAILED: "Falha",
  CANCELLED: "Cancelado",
  INTERRUPTED: "Interrompido",
  QUEUED: "Na fila",
  RUNNING: "Em execução",
  LEGACY: "Execução anterior",
  INVALID: "Verificar dados",
  VERIFIED: "Íntegro",
  MISSING: "Arquivo ausente",
  CHANGED: "Arquivo alterado",
};
const titles = {
  overview: [
    "Visão geral",
    "Geometria, entradas e condições do modelo em um só lugar.",
  ],
  components: [
    "Componentes",
    "Massas, posições e propriedades de cada item da montagem.",
  ],
  parameters: [
    "Parâmetros",
    "Entradas de engenharia e hipóteses usadas na simulação.",
  ],
  simulation: ["Simular", "Selecione o cenário e acompanhe a execução local."],
  results: [
    "Resultados",
    "Compare execuções e consulte os artefatos preservados.",
  ],
  data: [
    "Dados e fontes",
    "Evidências identificadas por origem, responsável e integridade.",
  ],
  history: ["Histórico", "Revisões de entrada preservadas a cada edição."],
};
const metricLabels = {
  apogee_agl: ["Apogeu AGL", "m"],
  max_mach: ["Mach máximo", ""],
  rail_exit_velocity: ["Saída da rampa", "m/s"],
  touchdown_velocity: ["Velocidade de impacto", "m/s"],
  total_impulse: ["Impulso total", "N·s"],
  flight_duration: ["Duração do voo", "s"],
};
const terminal = new Set([
  "COMPLETE",
  "COMPLETE_NOT_CONVERGED",
  "PARTIAL",
  "FAILED",
  "CANCELLED",
  "INTERRUPTED",
]);
/** Formate número finito em pt-BR; ausência recebe marcador explícito. */
const format = (v, n = 3) =>
  typeof v === "number" && Number.isFinite(v)
    ? v.toLocaleString("pt-BR", { maximumFractionDigits: n })
    : "—";
/** Produza selo com texto de estado e semântica visual; escape rótulos externos. */
const tag = (value) =>
  `<span class="tag ${["COMPLETE", "VERIFIED", "MEASURED"].includes(value) ? "good" : ["FAILED", "INVALID", "CHANGED"].includes(value) ? "error" : ["UNKNOWN", "ASSUMED", "PARTIAL", "MISSING", "COMPLETE_NOT_CONVERGED"].includes(value) ? "warning" : ""}">${e(labels[value] || value)}</span>`;
/** Produza opções escapadas e identifique a seleção atual. */
const options = (values, selected, names = {}) =>
  values
    .map(
      (v) =>
        `<option value="${e(v)}" ${v === selected ? "selected" : ""}>${e(names[v] || labels[v] || v)}</option>`,
    )
    .join("");
/**
 * Apresente o resultado de uma ação na região viva; não persiste dados.
 * Entradas: message, error = false.
 */
function notice(message, error = false) {
  const node = $("#notice");
  node.hidden = false;
  node.className = error ? "error" : "";
  node.textContent = message;
}
/**
 * Consulte a API local com token e JSON; respostas HTTP negativas tornam-se Error para a tela tratar.
 * Entradas: path, body.
 * Retorno: Promise com o JSON da resposta, ou rejeição Error.
 */
async function api(path, body) {
  const response = await fetch("/api/" + path, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      "X-Antares-Token": token,
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok)
    throw new Error(result.error || "Não foi possível concluir a operação.");
  return result;
}
/** Construa rota do projeto ativo com ID codificado; sufixos são definidos pelo código. */
const route = (suffix = "") =>
  "projects/" +
  encodeURIComponent(state.project.id) +
  (suffix ? "/" + suffix : "");
/**
 * Marque edição local pendente e desative a validação de dados ainda não salvos.
 * Entradas: nenhuma.
 */
function dirty() {
  state.dirty = true;
  $("#revision-label").textContent = "Alterações locais ainda não salvas";
  $("#validate-button").disabled = true;
}
/**
 * Produza um campo HTML rotulado; valores do usuário são escapados e atributos extras vêm apenas do código.
 * Entradas: label, id, type = "text", value = "", hint = "", extra = "".
 * Retorno: string HTML do campo.
 */
function field(label, id, type = "text", value = "", hint = "", extra = "") {
  return `<label class="field" for="${id}">${e(label)}<input id="${id}" type="${type}" value="${e(value)}" ${extra}>${hint ? `<small>${e(hint)}</small>` : ""}</label>`;
}
/**
 * Abra diálogo nativo com título e formulário; aguarde o callback, bloqueie envio repetido e mantenha erros no diálogo.
 * Entradas: title, content, submit, button = "Continuar".
 */
function modal(title, content, submit, button = "Continuar") {
  const dialog = $("#modal");
  $("#modal-title").textContent = title;
  $("#modal-content").innerHTML = content;
  $("#modal-error").textContent = "";
  $("#modal-submit").textContent = button;
  $("#modal-submit").hidden = !submit;
  $("#modal-cancel").textContent = submit ? "Cancelar" : "Fechar";
  $("#modal-form").onsubmit = async (event) => {
    event.preventDefault();
    if (!submit) {
      dialog.close();
      return;
    }
    $("#modal-submit").disabled = true;
    try {
      await submit();
      dialog.close();
    } catch (error) {
      $("#modal-error").textContent = error.message;
    } finally {
      $("#modal-submit").disabled = false;
    }
  };
  dialog.showModal();
  setTimeout(
    () => dialog.querySelector("input,select,textarea,button")?.focus(),
    0,
  );
}
/**
 * Leia um caminho separado por pontos na configuração, devolvendo undefined quando ausente.
 * Entradas: path.
 * Retorno: valor localizado ou undefined.
 */
function getValue(path) {
  return path.split(".").reduce((v, k) => v?.[k], state.project.config);
}
/**
 * Atualize um caminho da configuração local e marque edição pendente; não grava arquivos.
 * Entradas: path, value.
 */
function setValue(path, value) {
  const keys = path.split(".");
  let object = state.project.config;
  for (const key of keys.slice(0, -1)) object = object[key] ??= {};
  object[keys.at(-1)] = value;
  dirty();
}
/**
 * Carregue o catálogo de projetos, selecione o solicitado ou a preferência inicial e trate workspace vazio.
 * Entradas: selected.
 */
async function loadProjects(selected) {
  state.projects = await api("projects");
  $("#project-select").innerHTML = state.projects
    .map((p) => `<option value="${e(p.id)}">${e(p.name)}</option>`)
    .join("");
  if (!state.projects.length) {
    $("#page-description").textContent = "Crie um projeto para começar.";
    $("#panel").innerHTML =
      '<div class="empty"><strong>Nenhum projeto disponível</strong><p>Crie um foguete a partir do template para começar.</p></div>';
    return;
  }
  const id =
    selected ||
    state.projects.find((p) => p.id === "neblina_2")?.id ||
    state.projects.find((p) => p.id === "neblina_1")?.id ||
    state.projects[0].id;
  $("#project-select").value = id;
  await selectProject(id);
}
/**
 * Carregue configuração, validação, resultados e histórico em paralelo; reinicie seleção e polling do projeto anterior.
 * Entradas: id.
 */
async function selectProject(id) {
  clearTimeout(state.polling);
  state.activeRun = null;
  state.selected.clear();
  state.dirty = false;
  $("#panel").innerHTML =
    '<div class="loading" role="status">Lendo configuração e verificando entradas…</div>';
  try {
    const base = "projects/" + encodeURIComponent(id);
    const [project, validation, runs, history] = await Promise.all([
      api(base),
      api(base + "/validation"),
      api(base + "/runs"),
      api(base + "/history"),
    ]);
    state.project = project;
    state.validation = validation;
    state.runs = runs;
    state.history = history;
    $("#header-project").textContent = project.name;
    $("#revision-label").textContent =
      "Revisão " + project.revision.slice(0, 12);
    $("#validate-button").disabled = false;
    $("#notice").hidden = true;
    render();
  } catch (error) {
    notice(error.message, true);
    $("#panel").innerHTML =
      '<div class="empty"><strong>Não foi possível ler o projeto</strong><p>Confira os arquivos de configuração ou selecione outro foguete.</p></div>';
  }
}
/**
 * Atualize títulos, indicação de navegação e painel correspondente ao estado atual.
 * Entradas: nenhuma.
 */
function render() {
  if (!state.project) return;
  $("#page-title").textContent = titles[state.tab][0];
  $("#page-description").textContent = titles[state.tab][1];
  $("#page-eyebrow").textContent =
    state.project.name.toUpperCase() +
    " / " +
    (labels[state.project.stage] || state.project.stage).toUpperCase();
  for (const b of document.querySelectorAll(".nav-item")) {
    b.classList.toggle("active", b.dataset.tab === state.tab);
    b.setAttribute(
      "aria-current",
      b.dataset.tab === state.tab ? "page" : "false",
    );
  }
  ({
    overview: renderOverview,
    components: renderComponents,
    parameters: renderParameters,
    simulation: renderSimulation,
    results: renderResults,
    data: renderData,
    history: renderHistory,
  })[state.tab]();
}
/**
 * Desenhe o esquema SVG com dimensões declaradas, origem no bico e marcadores de componentes; não calcula aerodinâmica.
 * Entradas: nenhuma.
 * Retorno: string SVG ou aviso de geometria ausente.
 */
function schematic() {
  const v = state.project.config.vehicle?.vehicle || {};
  const length = v.geometry?.total_length,
    diameter = v.geometry?.reference_diameter;
  if (!(length > 0 && diameter > 0))
    return '<div class="empty"><strong>Geometria pendente</strong><p>Informe comprimento e diâmetro para visualizar a montagem.</p></div>';
  const scale = 650 / length,
    center = 125,
    r = Math.max(6, (diameter * scale) / 2),
    start = 35,
    tip = (v.nose?.enabled ? v.nose.length : 0) || 0;
  const fins = (v.fin_sets || [])
    .filter((f) => f.enabled !== false && f.position != null)
    .map((f) => {
      const x = start + f.position * scale,
        root = (f.root_chord || 0) * scale,
        span = (f.span || 0) * scale,
        sweep =
          (f.sweep_length ??
            Math.tan(((f.sweep_angle_deg || 0) * Math.PI) / 180) *
              (f.span || 0)) * scale,
        tail = (f.tip_chord || 0) * scale;
      return [-1, 1]
        .map(
          (sign) =>
            `<path d="M${x} ${center + sign * r}l${sweep} ${sign * span}h${tail}L${x + root} ${center + sign * r}Z" fill="#b6cce0" stroke="#496984" stroke-width="1.3"/>`,
        )
        .join("");
    })
    .join("");
  const comps = (state.project.config.components?.components || [])
    .filter(
      (c) =>
        c.included !== false &&
        c.axial_position_m != null &&
        ["payload", "electronics"].includes(c.category),
    )
    .map(
      (c) =>
        `<g><line x1="${start + c.axial_position_m * scale}" y1="${center - r}" x2="${start + c.axial_position_m * scale}" y2="${center + r}" stroke="${c.category === "payload" ? "#d98231" : "#12746d"}" stroke-width="5"/><title>${e(c.name)} · ${format(c.axial_position_m)} m</title></g>`,
    )
    .join("");
  return `<svg viewBox="0 0 730 250" role="img" aria-label="Esquema lateral do foguete, bico à esquerda e cauda à direita"><line x1="20" y1="${center}" x2="710" y2="${center}" stroke="#bac9d5" stroke-dasharray="5 5"/>${fins}<path d="M${start} ${center} Q${start + tip * scale * 0.35} ${center - r} ${start + tip * scale} ${center - r}H${start + length * scale}V${center + r}H${start + tip * scale}Q${start + tip * scale * 0.35} ${center + r} ${start} ${center}Z" fill="#e2ebf3" stroke="#496984" stroke-width="1.8"/>${comps}<line x1="${start}" y1="211" x2="${start + length * scale}" y2="211" stroke="#8a9bad"/><path d="M${start} 205v12M${start + length * scale} 205v12" stroke="#8a9bad"/><text x="360" y="232" text-anchor="middle" font-size="11" fill="#607085">${e(format(length))} m · diâmetro ${e(format(diameter * 1000, 1))} mm</text><text x="${start}" y="29" font-size="10" fill="#607085">BICO · 0 m</text><text x="${start + length * scale}" y="29" text-anchor="end" font-size="10" fill="#607085">CAUDA</text></svg>`;
}
/**
 * Formate erros e avisos de validação com caminhos e texto escapado; não altera sua severidade.
 * Entradas: nenhuma.
 * Retorno: string HTML dos diagnósticos.
 */
function validationContent() {
  const issues = state.validation?.issues || [],
    errors = issues.filter((i) => i.severity === "error"),
    warnings = issues.filter((i) => i.severity === "warning");
  return `<div class="validation-summary ${errors.length ? "has-errors" : ""}"><span class="validation-symbol" aria-hidden="true">${errors.length ? "!" : "✓"}</span><div><strong>${errors.length ? `${errors.length} pendência${errors.length > 1 ? "s" : ""} para simular` : "Entradas básicas verificadas"}</strong><small>${warnings.length} aviso${warnings.length !== 1 ? "s" : ""} de hipótese ou proveniência</small></div></div><ul class="issue-list">${issues.length ? issues.map((i) => `<li><code>${e(i.path)}</code><span class="issue-dot ${i.severity === "error" ? "error" : ""}" aria-hidden="true"></span>${e(i.message)}</li>`).join("") : "<li>Nenhuma pendência na validação local. A disponibilidade meteorológica é verificada durante o voo.</li>"}</ul>`;
}
/**
 * Apresente montagem, propriedades declaradas ou derivadas, prontidão, origem e últimas execuções.
 * Entradas: nenhuma.
 */
function renderOverview() {
  const v = state.project.config.vehicle?.vehicle || {},
    m = state.project.derived_mass_properties || v.mass_properties || {},
    model = state.project.config.model?.model || {},
    components = state.project.config.components?.components || [];
  $("#panel").innerHTML =
    `<div class="grid overview-grid"><section class="surface"><div class="surface-head"><h2>Montagem do veículo</h2>${tag(state.project.stage)}</div><div class="schematic">${schematic()}</div><div class="schematic-note">Esquema geométrico · não representa desenho de fabricação.</div><div class="summary-strip"><div class="summary-item"><small>MASSA SEM MOTOR</small><div class="summary-value">${format(m.mass_without_motor)} <span>kg</span></div></div><div class="summary-item"><small>CG A PARTIR DO BICO</small><div class="summary-value">${format(m.center_of_mass_without_motor)} <span>m</span></div></div><div class="summary-item"><small>COMPONENTES REGISTRADOS</small><div class="summary-value">${components.length || "—"}</div></div></div></section><section class="surface"><div class="surface-head"><h2>Prontidão das entradas</h2><button class="button ghost small" id="show-parameters">Revisar →</button></div>${validationContent()}</section></div><section class="surface section-spacer"><div class="surface-head"><h2>Últimas execuções</h2><button id="all-results" class="button ghost small">Ver resultados →</button></div>${runsTable(state.runs.slice(0, 4), false)}</section><section class="surface section-spacer"><div class="surface-head"><h2>Origem do modelo</h2>${tag(model.baseline && !model.pending_import ? "ASSUMED" : "UNKNOWN")}</div><div class="surface-body"><p class="muted">${e(model.notes || "Configuração herdada; consulte as fontes e a revisão de cada entrada.")}</p>${model.baseline ? `<p class="hint">Projeto de origem: ${e(model.baseline.project)} · revisão <code>${e(model.baseline.revision?.slice(0, 12))}</code></p>` : ""}<div class="toolbar" style="padding:12px 0 0;border:0"><span class="hint">Alterações de componentes não são medições do foguete construído.</span><button id="overview-components" class="button secondary small">Abrir inventário</button></div></div></section>`;
  $("#show-parameters").onclick = () => switchTab("parameters");
  $("#all-results").onclick = () => switchTab("results");
  $("#overview-components").onclick = () => switchTab("components");
  wireRunLinks();
}
/**
 * Produza tabela de execuções com métricas disponíveis e seleção opcional; campos ausentes permanecem indicados.
 * Entradas: runs, selectable.
 * Retorno: string HTML da tabela ou orientação de estado vazio.
 */
function runsTable(runs, selectable) {
  if (!runs.length)
    return '<div class="empty"><strong>O primeiro voo começa com as entradas</strong><p>Revise a configuração e valide o projeto. As próximas execuções aparecerão aqui.</p><button class="button secondary" data-go-simulation>Abrir simulação</button></div>';
  return `<div class="table-wrap"><table><thead><tr>${selectable ? "<th>Comparar</th>" : ""}<th>Execução</th><th>Cenário</th><th>Apogeu AGL</th><th>Mach máx.</th><th>Estado</th><th></th></tr></thead><tbody>${runs.map((r) => `<tr>${selectable ? `<td><input class="result-check" type="checkbox" data-compare="${e(r.run_id)}" aria-label="Comparar ${e(r.run_id)}" ${state.selected.has(r.run_id) ? "checked" : ""}></td>` : ""}<td class="numeric">${e(r.run_id)}</td><td>${e(r.scenario || "—")}</td><td class="numeric">${format(r.metrics?.apogee_agl, 1)} m</td><td class="numeric">${format(r.metrics?.max_mach)}</td><td>${tag(r.status)}</td><td><button class="button ghost small" data-run="${e(r.run_id)}">Abrir</button></td></tr>`).join("")}</tbody></table></div>`;
}
/**
 * Conecte botões da tabela à consulta de resultado e à navegação de simulação.
 * Entradas: nenhuma.
 */
function wireRunLinks() {
  for (const button of document.querySelectorAll("[data-run]"))
    button.onclick = () => openRun(button.dataset.run);
  for (const button of document.querySelectorAll("[data-go-simulation]"))
    button.onclick = () => switchTab("simulation");
}
/**
 * Obtenha o inventário da edição ou crie documento parcial vazio, preservando desconhecidos.
 * Entradas: nenhuma.
 * Retorno: objeto do inventário na edição local.
 */
function componentDocument() {
  return (state.project.config.components ??= {
    schema_version: 1,
    coverage: "PARTIAL",
    components: [],
  });
}
/**
 * Monte o editor de componentes e seus eventos; cálculo e transformação são solicitados ao serviço Python.
 * Entradas: nenhuma.
 */
function renderComponents() {
  const doc = componentDocument(),
    rows = doc.components || [];
  $("#panel").innerHTML =
    `<section class="surface"><div class="toolbar"><div><h2>Inventário de massa</h2><p>CG e tensor calculados a partir dos itens incluídos, excluindo o motor.</p></div><div class="toolbar" style="padding:0;border:0"><button id="transform-components" class="button secondary small">Transformar montagem</button><button id="add-component" class="button small">＋ Componente</button></div></div>${rows.length ? `<div class="table-wrap"><table class="components-table"><thead><tr><th>Incluir</th><th>Componente</th><th>Categoria</th><th>Massa · kg</th><th>CG axial · m</th><th>Inércia local</th><th>Proveniência</th><th>Fonte</th><th></th></tr></thead><tbody>${rows.map((c, i) => `<tr><td><input type="checkbox" data-component="${i}" data-field="included" aria-label="Incluir ${e(c.name)}" ${c.included !== false ? "checked" : ""}></td><td><input class="name-input" value="${e(c.name)}" data-component="${i}" data-field="name" aria-label="Nome do componente ${i + 1}"></td><td><select data-component="${i}" data-field="category" aria-label="Categoria de ${e(c.name)}">${options(["structure", "electronics", "payload", "recovery", "motor", "other"], c.category || "other", { structure: "Estrutura", electronics: "Eletrônica", payload: "Payload", recovery: "Recuperação", motor: "Motor", other: "Outro" })}</select></td><td><input type="number" step="any" min="0" value="${e(c.mass_kg)}" data-component="${i}" data-field="mass_kg" aria-label="Massa em kg de ${e(c.name)}"></td><td><input type="number" step="any" value="${e(c.axial_position_m)}" data-component="${i}" data-field="axial_position_m" aria-label="Posição do CG em m de ${e(c.name)}"></td><td><select data-component="${i}" data-field="inertia_model" aria-label="Modelo de inércia de ${e(c.name)}">${options(["provided", "point_mass", "solid_cylinder", "hollow_cylinder", "box"], c.inertia_model || "provided", { provided: "Tensor informado", point_mass: "Massa pontual", solid_cylinder: "Cilindro maciço", hollow_cylinder: "Cilindro vazado", box: "Paralelepípedo" })}</select><button class="button ghost small" data-inertia="${i}">Dimensões / tensor</button></td><td><select data-component="${i}" data-field="provenance.type" aria-label="Proveniência de ${e(c.name)}">${options(["MEASURED", "CALCULATED", "ASSUMED", "UNKNOWN"], c.provenance?.type || "UNKNOWN")}</select></td><td><input value="${e(c.provenance?.source)}" data-component="${i}" data-field="provenance.source" aria-label="Fonte de ${e(c.name)}"></td><td><button class="icon-button" data-remove="${i}" aria-label="Remover ${e(c.name)}">×</button></td></tr>`).join("")}</tbody></table></div>` : '<div class="empty"><strong>O modelo ainda usa propriedades agregadas</strong><p>Importe um arquivo OpenRocket ou registre os componentes. A massa e o CG do modelo atual permanecem separados deste inventário.</p></div>'}<div class="editor-footer"><div class="editor-options"><label class="check-label"><input id="complete-inventory" type="checkbox" ${doc.coverage === "COMPLETE" ? "checked" : ""}>Inventário completo do veículo sem motor</label><label class="check-label"><input id="use-components" type="checkbox" ${state.project.config.vehicle.vehicle.mass_properties?.method === "components" ? "checked" : ""}>Usar este inventário para calcular as propriedades do voo</label></div><div class="toolbar" style="padding:0;border:0"><button id="preview-mass" class="button secondary">Calcular massa e CG</button><button id="save-components" class="button">Salvar revisão</button></div></div><div class="preview-box" id="mass-preview" aria-live="polite">Tensores no CG local: I11 e I22 transversais; I33 longitudinal. Motor e propelente não entram nesta soma.</div></section>`;
  $("#add-component").onclick = () => {
    doc.components.push({
      id: crypto.randomUUID(),
      name: "Novo componente",
      category: "other",
      included: true,
      mass_kg: null,
      axial_position_m: null,
      radial_position_m: [0, 0],
      inertia_model: "provided",
      inertia_kg_m2: null,
      geometry: {},
      provenance: { type: "UNKNOWN", source: "" },
    });
    dirty();
    renderComponents();
  };
  for (const input of document.querySelectorAll("[data-component]"))
    input.onchange = () => {
      const row = doc.components[Number(input.dataset.component)],
        keys = input.dataset.field.split(".");
      let target = row;
      for (const key of keys.slice(0, -1)) target = target[key] ??= {};
      target[keys.at(-1)] =
        input.type === "checkbox"
          ? input.checked
          : input.type === "number"
            ? input.value === ""
              ? null
              : Number(input.value)
            : input.value;
      dirty();
    };
  for (const button of document.querySelectorAll("[data-remove]"))
    button.onclick = () => {
      doc.components.splice(Number(button.dataset.remove), 1);
      dirty();
      renderComponents();
    };
  for (const button of document.querySelectorAll("[data-inertia]"))
    button.onclick = () => editInertia(Number(button.dataset.inertia));
  $("#complete-inventory").onchange = (event) => {
    doc.coverage = event.target.checked ? "COMPLETE" : "PARTIAL";
    dirty();
  };
  $("#use-components").onchange = (event) => {
    state.project.config.vehicle.vehicle.mass_properties ??= {};
    state.project.config.vehicle.vehicle.mass_properties.method = event.target
      .checked
      ? "components"
      : "manual";
    dirty();
  };
  $("#save-components").onclick = saveDialog;
  $("#preview-mass").onclick = async () => {
    try {
      const result = await api(route("mass-properties"), doc);
      $("#mass-preview").textContent =
        `Massa: ${format(result.mass_without_motor, 5)} kg · CG axial: ${format(result.center_of_mass_without_motor, 5)} m\nI11: ${format(result.inertia.I11, 6)} · I22: ${format(result.inertia.I22, 6)} · I33: ${format(result.inertia.I33, 6)} kg·m²`;
    } catch (error) {
      $("#mass-preview").textContent = error.message;
    }
  };
  $("#transform-components").onclick = transformDialog;
}
/**
 * Edite dimensões SI e tensor local de um componente; confira seis valores finitos antes de aceitar o tensor.
 * Entradas: index.
 */
function editInertia(index) {
  const c = componentDocument().components[index];
  modal(
    "Propriedades locais · " + c.name,
    `<p class="hint">Dimensões em metros. O tensor informado deve estar no CG do componente, com a mesma orientação do veículo.</p><div class="field-grid">${field("Comprimento", "g-length", "number", c.geometry?.length_m ?? "", "", 'step="any" min="0"')}${field("Raio externo", "g-outer", "number", c.geometry?.outer_radius_m ?? "", "", 'step="any" min="0"')}${field("Raio interno", "g-inner", "number", c.geometry?.inner_radius_m ?? "", "", 'step="any" min="0"')}${field("Largura (paralelepípedo)", "g-width", "number", c.geometry?.width_m ?? "", "", 'step="any" min="0"')}${field("Altura (paralelepípedo)", "g-height", "number", c.geometry?.height_m ?? "", "", 'step="any" min="0"')}<label class="field full" for="inertia-values">Tensor informado · kg·m²<input id="inertia-values" value="${e(c.inertia_kg_m2?.join(", ") || "")}" placeholder="I11, I22, I33, I12, I13, I23"><small>Use ponto decimal e vírgulas entre os seis valores. Deixe vazio quando desconhecido.</small></label></div>`,
    () => {
      c.geometry ??= {};
      for (const [id, key] of [
        ["g-length", "length_m"],
        ["g-outer", "outer_radius_m"],
        ["g-inner", "inner_radius_m"],
        ["g-width", "width_m"],
        ["g-height", "height_m"],
      ]) {
        const value = $("#" + id).value;
        c.geometry[key] = value === "" ? null : Number(value);
      }
      const tensor = $("#inertia-values").value.trim();
      if (tensor) {
        const values = tensor.split(",").map(Number);
        if (values.length !== 6 || values.some((v) => !Number.isFinite(v)))
          throw Error("Informe seis números finitos.");
        c.inertia_kg_m2 = values;
      } else c.inertia_kg_m2 = null;
      dirty();
    },
    "Aplicar à edição",
  );
}
/**
 * Solicite troca de posições e fator estrutural ao serviço; aceite sua cópia validada somente após sucesso.
 * Entradas: nenhuma.
 */
function transformDialog() {
  const doc = componentDocument();
  if (!doc.components.length) {
    notice(
      "Importe ou registre os componentes antes de transformar a montagem.",
      true,
    );
    return;
  }
  modal(
    "Transformar montagem",
    `<p class="hint">As mudanças ficam na edição local até salvar uma revisão. Uma hipótese de redução de massa não altera a curva de empuxo.</p><div class="field-grid"><label class="field" for="swap-a">Primeiro componente<select id="swap-a"><option value="">Não trocar</option>${doc.components.map((c) => `<option value="${e(c.id)}">${e(c.name)}</option>`).join("")}</select></label><label class="field" for="swap-b">Segundo componente<select id="swap-b"><option value="">Não trocar</option>${doc.components.map((c) => `<option value="${e(c.id)}">${e(c.name)}</option>`).join("")}</select></label>${field("Fator de massa dos itens “Estrutura”", "structural-factor", "number", "1", "Por exemplo: 0.95 corresponde a uma redução assumida de 5%.", 'step="any" min="0.001" max="2"')}</div>`,
    async () => {
      const a = $("#swap-a").value,
        b = $("#swap-b").value,
        factor = Number($("#structural-factor").value);
      if (Boolean(a) !== Boolean(b))
        throw Error("Selecione dois componentes distintos.");
      const transformed = await api(route("transform-components"), {
        components: doc,
        swap: a ? [a, b] : null,
        structural_factor: factor,
      });
      state.project.config.components = transformed;
      dirty();
      renderComponents();
    },
    "Aplicar hipótese",
  );
}
const parameterGroups = [
  [
    "Geometria do veículo",
    [
      ["vehicle.vehicle.geometry.total_length", "Comprimento total · m"],
      [
        "vehicle.vehicle.geometry.reference_diameter",
        "Diâmetro de referência · m",
      ],
      [
        "vehicle.vehicle.mass_properties.mass_without_motor",
        "Massa sem motor · kg",
      ],
      [
        "vehicle.vehicle.mass_properties.center_of_mass_without_motor",
        "CG sem motor · m",
      ],
      ["vehicle.vehicle.mass_properties.inertia.I11", "I11 · kg·m²"],
      ["vehicle.vehicle.mass_properties.inertia.I22", "I22 · kg·m²"],
      ["vehicle.vehicle.mass_properties.inertia.I33", "I33 · kg·m²"],
    ],
  ],
  [
    "Motor",
    [
      [
        "motor.motor.thrust_source",
        "Arquivo de empuxo · relativo ao projeto",
        "text",
      ],
      ["motor.motor.dry_mass", "Massa seca · kg"],
      ["motor.motor.grain_number", "Quantidade de grãos"],
      ["motor.motor.grain_density", "Densidade do propelente · kg/m³"],
      ["motor.motor.grain_outer_radius", "Raio externo do grão · m"],
      ["motor.motor.grain_initial_inner_radius", "Raio interno do grão · m"],
      ["motor.motor.grain_initial_height", "Comprimento do grão · m"],
      ["motor.motor.grain_separation", "Separação entre grãos · m"],
      ["motor.motor.nozzle_radius", "Raio de saída do bocal · m"],
      ["motor.motor.throat_radius", "Raio de garganta · m"],
      ["vehicle.vehicle.motor_mount.position", "Posição de montagem · m"],
    ],
  ],
  [
    "Lançamento",
    [
      ["launch.launch.site.latitude", "Latitude · graus"],
      ["launch.launch.site.longitude", "Longitude · graus"],
      ["launch.launch.site.elevation", "Elevação · m ASL"],
      ["launch.launch.datetime.date", "Data", "date"],
      ["launch.launch.datetime.time", "Hora local", "time"],
      ["launch.launch.datetime.timezone", "Fuso", "text"],
      ["launch.launch.rail.length", "Comprimento da rampa · m"],
      ["launch.launch.rail.inclination_deg", "Inclinação · graus"],
      ["launch.launch.rail.heading_deg", "Azimute · graus"],
    ],
  ],
];
/**
 * Apresente parâmetros comuns e editor estruturado avançado; alterações permanecem locais até salvar revisão.
 * Entradas: nenhuma.
 */
function renderParameters() {
  $("#panel").innerHTML =
    `<section class="surface"><div class="toolbar"><h2>Configuração de engenharia</h2><button id="save-parameters" class="button">Salvar revisão</button></div><div class="parameter-group"><div class="field-grid"><label class="field" for="model-stage">Estado documentado<select id="model-stage">${options(["DESIGN", "AS_BUILT", "AS_FLOWN"], state.project.stage)}</select><small>Construído e configuração de voo exigem evidência correspondente.</small></label><label class="field" for="environment-type">Atmosfera<select id="environment-type">${options(["MAGI", "standard_atmosphere"], state.project.config.environment?.environment?.type || "MAGI", { MAGI: "MAGI · dados meteorológicos", standard_atmosphere: "Atmosfera padrão · hipótese explícita" })}</select></label></div>${state.project.config.model?.model?.pending_import ? '<label class="check-label section-spacer"><input id="review-import" type="checkbox">Concluí a revisão da importação OpenRocket e das suas limitações</label>' : ""}</div>${parameterGroups.map(([name, fields], i) => `<div class="parameter-group"><h3>${name}</h3><div class="field-grid">${fields.map(([path, label, type], j) => field(label, `parameter-${i}-${j}`, type || "number", getValue(path) ?? "", "", `data-path="${path}" ${!type ? 'step="any"' : ""}`)).join("")}</div></div>`).join("")}<details class="advanced"><summary>Outras configurações: recuperação, inércias, arrasto e incertezas</summary><p class="hint">Selecione o documento. Esta edição avançada conserva o formato estruturado dos arquivos do projeto.</p><label class="field" for="config-section">Documento<select id="config-section">${options(Object.keys(state.project.config), "recovery")}</select></label><textarea id="config-json" aria-label="Conteúdo estruturado do documento selecionado" spellcheck="false"></textarea><button id="apply-json" class="button secondary small section-spacer">Aplicar documento à edição</button></details><div class="editor-footer"><p class="hint">Caminhos de arquivos são relativos à pasta do foguete. Campos vazios permanecem desconhecidos.</p><button id="upload-asset" class="button secondary">Adicionar curva ou arquivo de entrada</button></div></section>`;
  for (const input of document.querySelectorAll("[data-path]"))
    input.onchange = () =>
      setValue(
        input.dataset.path,
        input.type === "number"
          ? input.value === ""
            ? null
            : Number(input.value)
          : input.value || null,
      );
  $("#model-stage").onchange = (event) => {
    state.project.config.model ??= { schema_version: 1, model: {} };
    state.project.config.model.model.stage = event.target.value;
    dirty();
  };
  $("#environment-type").onchange = (event) => {
    state.project.config.environment ??= { environment: {} };
    state.project.config.environment.environment.type = event.target.value;
    dirty();
  };
  if ($("#review-import"))
    $("#review-import").onchange = (event) => {
      state.project.config.model.model.pending_import = !event.target.checked;
      dirty();
    };
  $("#save-parameters").onclick = saveDialog;
  const section = $("#config-section"),
    editor = $("#config-json");
  const load = () =>
    (editor.value = JSON.stringify(
      state.project.config[section.value],
      null,
      2,
    ));
  load();
  section.onchange = load;
  $("#apply-json").onclick = () => {
    try {
      const value = JSON.parse(editor.value);
      if (!value || Array.isArray(value) || typeof value !== "object")
        throw Error("O documento precisa ser um objeto.");
      state.project.config[section.value] = value;
      dirty();
      notice("Documento aplicado à edição. Salve uma revisão para persistir.");
    } catch (error) {
      notice(error.message, true);
    }
  };
  $("#upload-asset").onclick = uploadAssetDialog;
}
/**
 * Exija justificativa e envie configuração com revisão esperada; recarregue o projeto após gravação confirmada.
 * Entradas: nenhuma.
 */
async function saveDialog() {
  if (!state.dirty) {
    notice("Não há alterações locais para salvar.");
    return;
  }
  modal(
    "Salvar revisão",
    `<p class="hint">A configuração anterior será preservada. A validação será atualizada após salvar.</p><label class="field" for="revision-note">O que mudou e por quê?<textarea id="revision-note" required maxlength="2000" placeholder="Descreva a alteração e a fonte dos dados."></textarea></label>`,
    async () => {
      const project = await api(route("save"), {
        config: state.project.config,
        revision: state.project.revision,
        note: $("#revision-note").value,
      });
      await selectProject(project.id);
      notice(
        "Nova revisão salva. A configuração anterior permanece no histórico.",
      );
    },
    "Salvar revisão",
  );
}
/**
 * Envie arquivo original codificado com caminho relativo e revisão esperada; a referência física não é alterada automaticamente.
 * Entradas: nenhuma.
 */
function uploadAssetDialog() {
  modal(
    "Adicionar arquivo de entrada",
    `${field("Caminho dentro do projeto", "asset-path", "text", "motors/curva_nova.eng", "Use motors/, aero/ ou sources/.")}<label class="field section-spacer" for="asset-file">Arquivo original<input id="asset-file" type="file" required></label><p class="hint">A inclusão não altera automaticamente os parâmetros físicos nem o caminho da curva na configuração.</p>`,
    async () => {
      const file = $("#asset-file").files[0];
      if (!file) throw Error("Selecione um arquivo.");
      const content = await fileBase64(file);
      const result = await api(route("asset"), {
        path: $("#asset-path").value,
        content,
        revision: state.project.revision,
      });
      await selectProject(result.id);
      notice(
        "Arquivo preservado no projeto. Confira sua referência nos parâmetros.",
      );
    },
    "Adicionar arquivo",
  );
}
/**
 * Monte a solicitação de cenário e campanha; inicie worker pelo serviço e impeça execução com edição pendente.
 * Entradas: nenhuma.
 */
function renderSimulation() {
  const valid = state.validation?.valid && !state.dirty;
  $("#panel").innerHTML =
    `<div class="grid simulation-grid"><section class="surface"><div class="surface-head"><h2>Nova execução</h2>${tag(valid ? "COMPLETE" : "PARTIAL")}</div><form id="run-form" class="surface-body"><div class="field-grid"><label class="field full" for="run-mode">Tipo de análise<select id="run-mode">${options(["deterministic", "monte_carlo"], "deterministic", { deterministic: "Voo determinístico", monte_carlo: "Monte Carlo" })}</select></label><label class="field full" for="run-scenario">Cenário<select id="run-scenario">${options(["nominal", "ballistic", "main_at_apogee", "only_reefing", "drogue_only"], "nominal", { nominal: "Nominal", ballistic: "Balístico · sem recuperação", main_at_apogee: "Principal no apogeu", only_reefing: "Recuperação em estágios / reefing", drogue_only: "Somente drogue" })}</select></label><label class="field" for="run-profile">Perfil Monte Carlo<select id="run-profile">${options(["debug", "development", "engineering", "official"], "debug")}</select></label>${field("Casos Monte Carlo", "run-samples", "number", "50", "", 'min="1" max="20000"')}${field("Workers", "run-workers", "number", "1", "", 'min="1" max="64"')}<label class="check-label full"><input id="run-report" type="checkbox" checked>Gerar relatório do voo determinístico</label></div><p class="hint">${valid ? "A execução congela as entradas e registra sua revisão." : "Corrija as pendências de validação e salve alterações antes de executar."}</p><button id="start-run" class="button section-spacer" type="submit" ${valid ? "" : "disabled"}>↗ Iniciar execução</button></form></section><section class="surface"><div class="surface-head"><h2>Acompanhamento</h2><button id="refresh-runs" class="button ghost small">Atualizar</button></div><div id="live-run">${state.activeRun ? "" : '<div class="empty"><strong>Pronto para acompanhar</strong><p>Progresso, mensagens e artefatos aparecerão durante a execução. Você pode cancelar o processamento local.</p></div>'}</div></section></div>`;
  $("#run-form").onsubmit = async (event) => {
    event.preventDefault();
    $("#start-run").disabled = true;
    clearTimeout(state.polling);
    state.activeRun = null;
    $("#live-run").innerHTML =
      '<div class="loading" role="status">Validando e iniciando o worker…</div>';
    try {
      const request = {
        mode: $("#run-mode").value,
        scenario: $("#run-scenario").value,
        profile: $("#run-profile").value,
        workers: Number($("#run-workers").value),
        report: $("#run-report").checked,
      };
      if (request.mode === "monte_carlo")
        request.samples = Number($("#run-samples").value);
      const job = await api(route("runs"), request);
      state.activeRun = job.run_id;
      notice("Execução iniciada. As entradas usadas ficarão preservadas.");
      await pollRun();
    } catch (error) {
      notice(error.message, true);
      $("#start-run").disabled = false;
    }
  };
  $("#refresh-runs").onclick = () =>
    state.activeRun ? pollRun() : refreshRuns();
  if (state.activeRun) pollRun();
}
/**
 * Releia a lista de execuções e atualize o painel de consulta sem integrar física.
 * Entradas: nenhuma.
 */
async function refreshRuns() {
  state.runs = await api(route("runs"));
  if (state.tab === "results") renderResults();
  else if (state.tab === "overview") renderOverview();
}
/**
 * Consulte fase, estado e log do job ativo; descarte resposta de seleção antiga e encerre polling ao atingir estado terminal.
 * Entradas: nenhuma.
 */
async function pollRun() {
  clearTimeout(state.polling);
  if (!state.activeRun || !state.project) return;
  const project = state.project.id,
    run = state.activeRun;
  try {
    const data = await api(route("runs/" + encodeURIComponent(run)));
    if (project !== state.project?.id || run !== state.activeRun) return;
    const status = data.state.status;
    if ($("#live-run")) {
      $("#live-run").innerHTML =
        `<div class="run-status"><div class="toolbar" style="padding:0;border:0"><span class="inline-code">${e(run)}</span>${tag(status)}</div><div class="progress-line" role="progressbar" aria-label="Progresso da execução por fase" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${data.state.progress || 0}"><span style="width:${Math.min(100, data.state.progress || 0)}%"></span></div><div class="progress-meta"><span>${e({ queued: "Na fila", snapshot: "Preservando entradas", simulation: "Integrando / processando casos", artifacts: "Verificando artefatos", finished: "Finalizado", cancelled: "Cancelado" }[data.state.phase] || data.state.phase || "Aguardando worker")}</span><span>${data.state.progress || 0}% por fase</span></div>${data.state.error ? `<p class="error-text">${e(data.state.error.message)}</p>` : ""}<div class="toolbar" style="padding:15px 0 0;border:0">${terminal.has(status) ? `<button id="open-finished-run" class="button secondary small">Abrir resultados</button>` : '<button id="cancel-run" class="button danger small">Cancelar execução</button>'}</div></div><pre class="log" tabindex="0" aria-label="Mensagens da execução">${e(data.log || "Aguardando mensagens do worker…")}</pre>`;
      if ($("#cancel-run"))
        $("#cancel-run").onclick = async () => {
          try {
            await api(route("runs/" + encodeURIComponent(run) + "/cancel"), {});
            await pollRun();
          } catch (error) {
            notice(error.message, true);
          }
        };
      if ($("#open-finished-run"))
        $("#open-finished-run").onclick = () => openRun(run);
    }
    if (!terminal.has(status)) state.polling = setTimeout(pollRun, 1500);
    else {
      await refreshRuns();
      if ($("#start-run"))
        $("#start-run").disabled = !state.validation?.valid || state.dirty;
    }
  } catch (error) {
    notice(error.message, true);
  }
}
/**
 * Apresente a lista e controles de comparação; medianas Monte Carlo são identificadas como resumos.
 * Entradas: nenhuma.
 */
function renderResults() {
  $("#panel").innerHTML =
    `<section class="surface"><div class="toolbar"><h2>Execuções preservadas</h2><button id="compare-runs" class="button secondary small">Comparar selecionadas</button></div><p class="hint surface-body">Em campanhas Monte Carlo, os valores resumidos são medianas dos casos válidos.</p>${runsTable(state.runs, true)}</section><div id="result-detail" class="section-spacer"></div>`;
  wireRunLinks();
  for (const input of document.querySelectorAll("[data-compare]"))
    input.onchange = () =>
      input.checked
        ? state.selected.add(input.dataset.compare)
        : state.selected.delete(input.dataset.compare);
  $("#compare-runs").onclick = compareRuns;
}
/**
 * Desenhe nuvem de pontos ou ECDF em degraus usando valores finitos; escale eixos sem inferir distribuições físicas.
 * Entradas: rows, xkey, ykey, xlabel, ylabel, connect = false.
 * Retorno: string SVG/HTML da nuvem ou ECDF.
 */
function pointChart(rows, xkey, ykey, xlabel, ylabel, connect = false) {
  const points = (rows || []).filter(
    (row) => Number.isFinite(row[xkey]) && Number.isFinite(row[ykey]),
  );
  if (!points.length)
    return '<div class="empty"><p>Dados ainda indisponíveis.</p></div>';
  const xs = points.map((p) => p[xkey]),
    ys = points.map((p) => p[ykey]),
    xmin = connect
      ? Math.min(...xs) -
        Math.max(
          (Math.max(...xs) - Math.min(...xs)) * 0.05,
          Math.abs(xs[0]) * 0.01,
          0.01,
        )
      : Math.min(0, ...xs),
    xmax = connect
      ? Math.max(...xs) +
        Math.max(
          (Math.max(...xs) - Math.min(...xs)) * 0.05,
          Math.abs(xs[0]) * 0.01,
          0.01,
        )
      : Math.max(0, ...xs),
    ymin = Math.min(0, ...ys),
    ymax = Math.max(0, ...ys),
    x = (v) => 70 + ((v - xmin) / (xmax - xmin || 1)) * 620,
    y = (v) => 245 - ((v - ymin) / (ymax - ymin || 1)) * 195;
  const marks = connect
    ? `<path d="M${x(xmin)} ${y(0)} ${points.map((p) => `H${x(p[xkey])}V${y(p[ykey])}`).join(" ")} H${x(xmax)}" fill="none" stroke="#2159c6" stroke-width="2"/>`
    : points
        .map(
          (p) =>
            `<circle cx="${x(p[xkey])}" cy="${y(p[ykey])}" r="3" fill="#12746d" opacity=".7"/>`,
        )
        .join("");
  return `<div class="chart"><svg viewBox="0 0 755 300" role="img" aria-label="${e(ylabel)} em função de ${e(xlabel)}"><path d="M70 45V245H700" fill="none" stroke="#8a9bad"/>${marks}<text x="70" y="22" font-size="11" fill="#607085">${e(ylabel)}</text><text x="380" y="290" text-anchor="middle" font-size="11" fill="#607085">${e(xlabel)}</text><text x="70" y="264" font-size="10">${format(xmin, 1)}</text><text x="690" y="264" text-anchor="end" font-size="10">${format(xmax, 1)}</text><text x="60" y="248" text-anchor="end" font-size="10">${format(ymin, 2)}</text><text x="60" y="52" text-anchor="end" font-size="10">${format(ymax, 2)}</text></svg></div>`;
}
/**
 * Apresente quantis, dispersão, ECDF e diagnósticos já calculados pelo serviço, com limites para amostras pequenas.
 * Entradas: campaign.
 * Retorno: string HTML da análise disponível.
 */
function campaignView(campaign) {
  const wanted = new Set([
      "apogee_agl",
      "rail_exit_velocity",
      "touchdown_velocity",
      "max_mach",
      "flight_duration",
      "landing_distance",
    ]),
    statistics = (campaign.statistics || []).filter((r) =>
      wanted.has(r.metric),
    );
  return `<section class="surface section-spacer"><div class="surface-head"><h2>Distribuições Monte Carlo · ${campaign.case_count} casos válidos</h2></div><div class="surface-body"><p class="hint">Resumo por mediana; não representa um voo individual. Amostras pequenas não sustentam estimativas de cauda. Convergência e falhas devem ser avaliadas nos artefatos completos.</p></div><div class="table-wrap"><table><thead><tr><th>Métrica</th><th>P05</th><th>P50</th><th>P95</th><th>Desvio padrão</th></tr></thead><tbody>${statistics.map((r) => `<tr><td>${e((metricLabels[r.metric]?.[0] || (r.metric === "landing_distance" ? "Distância de pouso" : r.metric)) + " · " + (metricLabels[r.metric]?.[1] ?? "m"))}</td>${["p05", "p50", "p95", "std"].map((key) => `<td class="numeric">${format(r[key])}</td>`).join("")}</tr>`).join("")}</tbody></table></div></section><div class="grid overview-grid section-spacer"><section class="surface"><div class="surface-head"><h2>Dispersão de pouso</h2></div>${pointChart(campaign.landing, "landing_east", "landing_north", "Leste · m", "Norte · m")}<p class="hint surface-body">Origem na rampa. Até 1000 pontos; escalas dos eixos independentes.</p></section><section class="surface"><div class="surface-head"><h2>Distribuição acumulada do apogeu</h2></div>${pointChart(
    (campaign.ecdf || []).filter((r) => r.metric === "apogee_agl"),
    "value",
    "probability",
    "Apogeu AGL · m",
    "Probabilidade empírica",
    true,
  )}</section></div><details class="surface advanced section-spacer"><summary>Convergência e sensibilidade</summary><pre class="log">${e(JSON.stringify({ convergence: campaign.convergence, sensitivity: campaign.sensitivity }, null, 2))}</pre></details>`;
}
/**
 * Compare séries temporais em SVG; interrompa linhas em dados ausentes e informe quando não há série disponível.
 * Entradas: series, key = "altitude_agl".
 * Retorno: string SVG/HTML das séries.
 */
function chart(series, key = "altitude_agl") {
  const colors = ["#2159c6", "#12746d", "#c17028", "#a44769"];
  const valid = series.filter(
    (s) => s.data.time?.length && s.data[key]?.length,
  );
  if (!valid.length)
    return '<div class="empty"><p>Série temporal não disponível neste conjunto de artefatos.</p></div>';
  const all = valid.flatMap((s) => s.data[key].filter(Number.isFinite)),
    times = valid.flatMap((s) => s.data.time.filter(Number.isFinite));
  if (!all.length || !times.length)
    return '<div class="empty">Sem valores finitos para este gráfico.</div>';
  const xmin = Math.min(...times),
    xmax = Math.max(...times),
    ymin = Math.min(0, ...all),
    ymax = Math.max(...all),
    x = (v) => 65 + ((v - xmin) / (xmax - xmin || 1)) * 650,
    y = (v) => 225 - ((v - ymin) / (ymax - ymin || 1)) * 185;
  const grid = Array.from({ length: 5 }, (_, i) => {
    const val = ymin + ((ymax - ymin) * i) / 4,
      yy = y(val);
    return `<line x1="65" x2="715" y1="${yy}" y2="${yy}" stroke="#e0e7ee"/><text x="53" y="${yy + 4}" text-anchor="end" font-size="10" fill="#607085">${e(format(val, 0))}</text>`;
  }).join("");
  const paths = valid
    .map((s, i) => {
      let lifted = true,
        d = "";
      for (let j = 0; j < s.data.time.length; j++) {
        const t = s.data.time[j],
          v = s.data[key][j];
        if (!Number.isFinite(t) || !Number.isFinite(v)) {
          lifted = true;
          continue;
        }
        d += (lifted ? "M" : "L") + x(t) + "," + y(v) + " ";
        lifted = false;
      }
      return `<path d="${d}" fill="none" stroke="${colors[i % colors.length]}" stroke-width="2"/>`;
    })
    .join("");
  return `<div class="chart"><svg viewBox="0 0 755 270" role="img" aria-label="Comparação temporal de ${key === "altitude_agl" ? "altitude AGL em metros" : "margem estática em calibres"}">${grid}${paths}<text x="385" y="262" text-anchor="middle" font-size="11" fill="#607085">Tempo desde a ignição · s</text><text x="65" y="20" font-size="11" fill="#607085">${key === "altitude_agl" ? "Altitude AGL · m" : "Margem estática · calibres"}</text></svg></div><div class="chart-legend">${valid.map((s, i) => `<span><i style="background:${colors[i % colors.length]}"></i>${e(s.name)}</span>`).join("")}</div>`;
}
/**
 * Consulte artefatos preservados, métricas e campanha; conecte verificação e cancelamento sem reexecutar a simulação.
 * Entradas: id.
 */
async function openRun(id) {
  if (state.tab !== "results") {
    state.tab = "results";
    render();
  }
  const target = $("#result-detail");
  target.innerHTML = '<div class="loading">Lendo métricas e artefatos…</div>';
  try {
    const data = await api(route("runs/" + encodeURIComponent(id))),
      metrics = data.metrics;
    target.innerHTML = `<div class="grid kpi-grid">${Object.entries(
      metricLabels,
    )
      .slice(0, 4)
      .map(
        ([key, [label, unit]]) =>
          `<div class="kpi"><small>${e(label)}</small><strong>${format(metrics[key], key === "max_mach" ? 3 : 1)} <span>${e(unit)}</span></strong></div>`,
      )
      .join(
        "",
      )}</div><section class="surface section-spacer"><div class="surface-head"><h2>${data.campaign ? "Campanha" : "Trajetória"} · ${e(id)}</h2>${tag(data.state.status)}</div>${data.campaign ? campaignView(data.campaign) : chart([{ name: id, data: data.series }])}</section><section class="surface section-spacer"><div class="surface-head"><h2>Estabilidade</h2></div>${chart([{ name: id, data: data.series }], "static_margin")}</section><section class="surface section-spacer"><div class="surface-head"><h2>Artefatos e proveniência</h2>${!terminal.has(data.state.status) && data.state.managed ? '<button id="cancel-result" class="button danger small">Cancelar execução</button>' : ""}<button id="verify-artifacts" class="button secondary small">Verificar integridade</button></div><div class="artifact-list">${
      data.artifacts
        .filter((p) => /\.(pdf|json|yaml|parquet|kml|csv|png)$/.test(p))
        .slice(0, 50)
        .map(
          (p) =>
            `<a target="_blank" rel="noopener" href="/api/artifacts/${encodeURIComponent(state.project.id)}/${encodeURIComponent(id)}/${p.split("/").map(encodeURIComponent).join("/")}">${e(p)}</a>`,
        )
        .join("") || '<span class="muted">Nenhum artefato disponível.</span>'
    }</div><details class="advanced"><summary>Mensagens e erros da execução</summary><pre class="log">${e(data.log || "Sem log disponível.")}</pre></details></section>`;
    if ($("#cancel-result"))
      $("#cancel-result").onclick = async () => {
        try {
          await api(route("runs/" + encodeURIComponent(id) + "/cancel"), {});
          await refreshRuns();
          await openRun(id);
        } catch (error) {
          notice(error.message, true);
        }
      };
    $("#verify-artifacts").onclick = async () => {
      try {
        const result = await api(
          route("runs/" + encodeURIComponent(id) + "/verify"),
          {},
        );
        notice(
          result.valid
            ? `${result.checked} arquivos verificados; hashes íntegros.`
            : `Arquivos alterados/ausentes: ${result.invalid.join(", ")}`,
          !result.valid,
        );
      } catch (error) {
        notice(error.message, true);
      }
    };
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    target.innerHTML = `<div class="empty"><strong>Resultado indisponível</strong><p>${e(error.message)}</p></div>`;
  }
}
/**
 * Consulte duas a quatro execuções e compare métricas e revisões; não atribua causalidade entre configurações diferentes.
 * Entradas: nenhuma.
 */
async function compareRuns() {
  const ids = [...state.selected];
  if (ids.length < 2) {
    notice("Selecione pelo menos duas execuções para comparar.", true);
    return;
  }
  if (ids.length > 4) {
    notice("Compare até quatro execuções por vez.", true);
    return;
  }
  $("#result-detail").innerHTML =
    '<div class="loading">Preparando comparação…</div>';
  try {
    const runs = await Promise.all(
      ids.map((id) => api(route("runs/" + encodeURIComponent(id)))),
    );
    $("#result-detail").innerHTML =
      `<section class="surface"><div class="surface-head"><h2>Comparação de execuções</h2></div><div class="surface-body"><p class="hint">Verifique revisões, cenários e hipóteses. Diferenças entre modelos não demonstram causalidade nem validação experimental.</p></div><div class="table-wrap"><table><thead><tr><th>Métrica</th>${runs.map((r) => `<th>${e(r.run_id)}</th>`).join("")}</tr></thead><tbody>${Object.entries(
        metricLabels,
      )
        .map(
          ([key, [label, unit]]) =>
            `<tr><td>${e(label)} · ${e(unit)}</td>${runs.map((r) => `<td class="numeric">${format(r.metrics[key])}</td>`).join("")}</tr>`,
        )
        .join(
          "",
        )}<tr><td>Revisão de entrada</td>${runs.map((r) => `<td class="numeric">${e(r.state.inputs?.revision?.slice(0, 12) || "Não registrada")}</td>`).join("")}</tr></tbody></table></div>${chart(runs.map((r) => ({ name: r.run_id, data: r.series })))}</section>`;
  } catch (error) {
    notice(error.message, true);
  }
}
/**
 * Consulte a verificação do catálogo e apresente responsáveis, origem, hash e disponibilidade dos arquivos.
 * Entradas: nenhuma.
 */
async function renderData() {
  $("#panel").innerHTML =
    '<div class="loading">Verificando o catálogo local…</div>';
  try {
    const result = await api("datasets");
    state.datasets = result.datasets;
    $("#panel").innerHTML =
      `<section class="surface"><div class="toolbar"><div><h2>Catálogo de evidências</h2><p>Metadados versionáveis; os arquivos originais permanecem em seu armazenamento.</p></div><button id="register-dataset" class="button">＋ Registrar evidência</button></div>${result.datasets.length ? `<div class="table-wrap"><table><thead><tr><th>Identificador / tipo</th><th>Projeto</th><th>Responsável</th><th>Origem / localização</th><th>Integridade</th></tr></thead><tbody>${result.datasets.map((d) => `<tr><td>${e(d.id)}<br><small class="muted">${e(d.kind)}</small></td><td>${e(d.project || "—")}</td><td>${e(d.owner)}</td><td class="wrap">${e(d.source)}<br><code>${e(d.path)}</code><br><small>${e(d.sha256.slice(0, 16))}…</small></td><td>${tag(d.status)}</td></tr>`).join("")}</tbody></table></div>` : '<div class="empty"><strong>Uma memória experimental compartilhada</strong><p>Registre modelos OpenRocket, pesagens, ensaios de motor, calibrações e telemetria com seus responsáveis e hashes.</p></div>'}</section>`;
    $("#register-dataset").onclick = datasetDialog;
  } catch (error) {
    notice(error.message, true);
  }
}
/**
 * Recolha metadados de evidência e solicite registro ao serviço, que calcula o hash sem modificar o original.
 * Entradas: nenhuma.
 */
function datasetDialog() {
  modal(
    "Registrar evidência",
    `<div class="field-grid">${field("Identificador único", "dataset-id", "text", "", "Letras, números, hífen e underscore.")}${field("Responsável institucional", "dataset-owner", "text", "", "Equipe ou pessoa responsável pela preservação.")}<label class="field" for="dataset-kind">Tipo<select id="dataset-kind">${options(["openrocket", "mass_properties", "motor_test", "calibration", "telemetry", "atmosphere", "campaign", "other"], "openrocket", { openrocket: "Projeto OpenRocket", mass_properties: "Massa / CG / inércia", motor_test: "Ensaio de motor", calibration: "Calibração", telemetry: "Telemetria bruta", atmosphere: "Atmosfera", campaign: "Campanha", other: "Outro" })}</select></label>${field("Origem / referência documental", "dataset-source")}${field("Caminho relativo ao repositório", "dataset-path", "text", "", "Exemplo: data/flight_data/voo.log")}</div><p class="hint">O arquivo deve existir neste computador. O registro calcula seu hash sem editar nem mover o original.</p>`,
    async () => {
      await api("datasets", {
        id: $("#dataset-id").value,
        path: $("#dataset-path").value,
        kind: $("#dataset-kind").value,
        owner: $("#dataset-owner").value,
        source: $("#dataset-source").value,
        project: state.project.id,
      });
      await renderData();
      notice("Evidência registrada com hash e responsável.");
    },
    "Registrar",
  );
}
/**
 * Apresente revisões preservadas e restauração com controle de concorrência; a configuração atual é arquivada pelo serviço.
 * Entradas: nenhuma.
 */
function renderHistory() {
  $("#panel").innerHTML =
    `<section class="surface"><div class="surface-head"><h2>Revisões preservadas</h2><span class="inline-code">Atual: ${e(state.project.revision.slice(0, 12))}</span></div>${state.history.length ? state.history.map((h) => `<article class="history-entry"><div><code>${e(h.revision)}</code><p>${e(h.note)}</p><small class="muted">${e(new Date(h.created_utc).toLocaleString("pt-BR"))} · ${Object.keys(h.files).length} entradas preservadas</small></div><button class="button secondary small" data-restore="${e(h.revision)}">Restaurar configuração</button></article>`).join("") : '<div class="empty"><strong>As próximas edições terão histórico</strong><p>Ao salvar uma alteração pela estação ou pelo serviço de projetos, as entradas anteriores serão preservadas com hashes.</p></div>'}</section>`;
  for (const button of document.querySelectorAll("[data-restore]"))
    button.onclick = () =>
      modal(
        "Restaurar configuração",
        `<p>Restaurar a revisão <code>${e(button.dataset.restore.slice(0, 12))}</code>?</p><p class="hint">A configuração atual será preservada. Arquivos antigos são verificados antes da restauração.</p>`,
        async () => {
          const result = await api(route("restore"), {
            target: button.dataset.restore,
            revision: state.project.revision,
          });
          await selectProject(result.id);
          notice("Configuração restaurada e revisão anterior preservada.");
        },
        "Restaurar revisão",
      );
}
/**
 * Atualize a área ativa e renderize seu painel, mantendo a edição local.
 * Entradas: tab.
 */
function switchTab(tab) {
  state.tab = tab;
  render();
}
/**
 * Converta File de até 16 MiB em Base64 por blocos; rejeite arquivos maiores antes de enviar.
 * Entradas: file.
 * Retorno: Promise<string> com o conteúdo codificado.
 */
async function fileBase64(file) {
  if (file.size > 16 * 1024 * 1024)
    throw Error("O arquivo deve ter até 16 MiB.");
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  for (let i = 0; i < bytes.length; i += 32768)
    binary += String.fromCharCode(...bytes.subarray(i, i + 32768));
  return btoa(binary);
}
$("#new-project").onclick = () =>
  modal(
    "Criar um novo foguete",
    `<div class="field-grid">${field("Identificador do projeto", "new-id", "text", "", "Exemplo: neblina_3. Use um nome sem espaços.", 'required pattern="[A-Za-z0-9][A-Za-z0-9_-]{0,79}"')}<label class="field" for="new-source">Copiar entradas de<select id="new-source">${options(
      state.projects.map((p) => p.id),
      "00_Copy_This",
    )}</select></label></div><p class="hint">A origem permanece intacta. Telemetria e resultados anteriores não serão copiados.</p>`,
    async () => {
      const result = await api("projects", {
        id: $("#new-id").value,
        source: $("#new-source").value,
      });
      await loadProjects(result.id);
      notice("Projeto criado. Revise os dados herdados antes de simular.");
    },
    "Criar foguete",
  );
$("#project-select").onchange = (event) => {
  if (
    state.dirty &&
    !window.confirm(
      "Há alterações não salvas. Descartar a edição local e trocar de projeto?",
    )
  ) {
    event.target.value = state.project.id;
    return;
  }
  selectProject(event.target.value);
};
for (const button of document.querySelectorAll("[data-tab]"))
  button.onclick = () => switchTab(button.dataset.tab);
$("#validate-button").onclick = async () => {
  if (state.dirty) {
    notice("Salve a revisão antes de validar as entradas persistidas.", true);
    return;
  }
  try {
    state.validation = await api(route("validation"));
    render();
    notice(
      state.validation.valid
        ? "Entradas locais verificadas. Consulte os avisos de proveniência."
        : "Há pendências de entrada. Revise os itens indicados.",
      !state.validation.valid,
    );
  } catch (error) {
    notice(error.message, true);
  }
};
$("#import-button").onclick = () => {
  if (state.dirty) {
    notice("Salve ou descarte as alterações locais antes de importar.", true);
    return;
  }
  $("#ork-file").click();
};
$("#ork-file").onchange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  modal(
    "Importar projeto OpenRocket",
    `<p>Importar <strong>${e(file.name)}</strong> para ${e(state.project.name)}?</p><p class="hint">O arquivo original será preservado. A importação cria um inventário e marca a revisão como pendente; formas não suportadas, curvas e overrides exigem conferência.</p>`,
    async () => {
      const result = await api(route("import-openrocket"), {
        content: await fileBase64(file),
        revision: state.project.revision,
      });
      await selectProject(result.project.id);
      state.tab = "components";
      render();
      notice(
        `Importação preservada: ${result.report.components.components.length} componentes, ${result.report.unsupported.length} tipos não suportados. Revise as pendências.`,
      );
    },
    "Importar e revisar",
  );
  event.target.value = "";
};
$("#modal-close").onclick = () => $("#modal").close();
$("#modal-cancel").onclick = () => $("#modal").close();
$("#help-button").onclick = () =>
  modal(
    "Como trabalhar nesta estação",
    `<div class="help-copy"><ol><li>Crie ou selecione o projeto e confira a origem das entradas.</li><li>Importe o OpenRocket ou registre componentes, mantendo desconhecidos vazios.</li><li>Revise parâmetros e salve uma revisão com a justificativa.</li><li>Valide o projeto e execute primeiro o cenário nominal.</li><li>Compare resultados e preserve as fontes no catálogo.</li></ol><p>Apenas o processo local executa simulações. Fechar o servidor cancela seus workers ativos. Arquivos brutos permanecem separados dos resultados.</p><p><a href="/api/documents/GUI.md" target="_blank" rel="noopener">Abrir guia completo de operação</a></p></div>`,
    null,
  );
window.addEventListener("beforeunload", (event) => {
  if (state.dirty) {
    event.preventDefault();
    event.returnValue = "";
  }
});
(async () => {
  try {
    const health = await api("health");
    $("#environment-state").textContent = health.healthy
      ? `Python ${health.python} · ambiente verificado`
      : `Ambiente com ${health.issues.length} pendência(s)`;
    $("#environment-state").classList.toggle("warning", !health.healthy);
    await loadProjects();
  } catch (error) {
    notice(error.message, true);
    $("#panel").innerHTML =
      '<div class="empty"><strong>Conexão local indisponível</strong><p>Confira o terminal do servidor e recarregue a página.</p></div>';
  }
})();
