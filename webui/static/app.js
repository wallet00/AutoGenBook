/* AutoGenBook UI — SPA frontend (vanilla JS, no build step) */
"use strict";

/* ── i18n ─────────────────────────────────────────────────────── */
const I18N = {
  cs: {
    app_title: "AutoGenBook",
    projects: "Projekty",
    new_project: "Nový projekt",
    project_name: "Název projektu (předmět)",
    language: "Jazyk materiálů",
    cs: "Čeština",
    en: "Angličtina",
    create: "Vytvořit projekt",
    open: "Otevřít",
    delete: "Smazat",
    back: "← Zpět",
    updated: "Změněno",
    no_projects: "Zatím žádné projekty. Vytvoř první.",
    tabs: { spec: "1 · Osnova", kb: "2 · Materiály", run: "3 · Generování", out: "4 · Výstup", prom: "5 · Editor promptů" },
    spec_hint: "Zde je osnova (input spec pro AutoGenBook). Uprav a ulož.",
    save: "Uložit osnovu",
    saved: "Uloženo",
    kb_hint: "Nahraj stávající materiály (PDF, DOCX, MD, TXT, PPTX…) — vytvoří znalostní bázi.",
    upload: "Nahrát soubor",
    drop_hint: "nebo sem přetáhni soubory",
    no_files: "Žádné soubory. Přetáhni sem materiály.",
    refresh: "Obnovit",
    settings_hint: "Konfigurace běhu generování.",
    model: "Model",
    web_rag: "Povolit web vyhledávání (RAG)",
    audit: "Audit",
    audit_off: "Vypnut",
    audit_warn: "Varovat",
    audit_strict: "Přísný",
    pdf: "Generovat PDF",
    export_tex: "Export TeX/PDF (pandoc)",
    run: "Spustit generování",
    running: "Probíhá…",
    cancel: "Zrušit běh",
    pause: "Pozastavit",
    resume: "Pokračovat",
    stop: "Zastavit",
    run_log: "Průběh běhu",
    status: "Status",
    output_hint: "Vygenerované soubory a kapitoly. Klikni pro náhled.",
    download: "Stáhnout",
    no_output: "Zatím žádný výstup. Spusť generování.",
    markdown: "Markdown",
    tokens_cost: "Tokeny / cena",
    st_idle: "Připraven",
    st_running: "Běží",
    st_done: "Hotovo",
    st_error: "Chyba",
    st_cancelled: "Zrušeno",
    confirm_delete: "Opravdu smazat projekt?",
    provider: "Poskytovatel",
    not_set: "nenastaven",
    analyze_btn: "Analýza AI & Předvyplnit parametry",
    analyzing: "Probíhá analýza AI…",
    params_title: "Parametry kurzu (Setup Assistant)",
    params_note: "Uloží se do project.json a vloží se do osnovy pro generování jako kontext.",
    param_title: "Název (navržený)",
    param_audience: "Persona / Cílová skupina",
    param_tone: "Tón textu",
    param_purpose: "Účel výstupu",
    param_language: "Jazyk výstupu",
    param_language_note: "MUSÍ být dodržen bez ohledu na jazyk podkladů i instrukcí.",
    param_depth: "Doporučená hloubka členění",
    save_params: "Uložit parametry",
    outline_run: "1 · Vygenerovat pouze strukturu (Outline)",
    full_run: "2 · Generovat kompletní knihu",
    gen_node: "Generovat tento uzel",
    copy_notebook: "Zkopírovat jako podklad pro NotebookLM",
    copied: "Zkopírováno do schránky",
    no_structure: "Zatím nebyla vygenerována struktura. Spusť krok 1 (Outline).",
    tree_hint: "Strom kapitol",
    prom: "5 · Prompty",
    prompts_hint: "Ladění systémových promptů AutoGenBooku. Změny se promítnou do rekurzivního generování sekcí.",
    prom_project: "Projektové prompty (tento projekt)",
    prom_global: "Globální prompty (výchozí šablony)",
    prom_reset: "Reset na výchozí",
    prom_save: "Uložit změny",
    node_modal_title: "⚡ Vygenerovat tento uzel",
    node_modal_kb_hint: "Nevybráno = použít celou znalostní bázi.",
    node_include: "Zahrnout stávající vygenerovaný text jako kontext (přepsat/vylepšit)",
    node_rag: "Povolit Web RAG (vyhledávání na internetu) pro tuto sekci",
    node_prompt: "Specifické instrukce pro tuto kapitolu",
    node_prompt_ph: "Např: Zaměř se na S-D logiku v SaaS, vysvětli rozdíl Value-in-Exchange vs Value-in-Use na příkladu Spotify.",
    node_kb_title: "Prioritní zdroje (kb/) — MUSÍ být použity",
    node_run: "Generovat nyní",
    cancel_modal: "Zrušit",
    running_from: "Běh probíhá — live výpis",
  },
  en: {
    app_title: "AutoGenBook",
    projects: "Projects",
    new_project: "New project",
    project_name: "Project name (course)",
    language: "Material language",
    cs: "Czech",
    en: "English",
    create: "Create project",
    open: "Open",
    delete: "Delete",
    back: "← Back",
    updated: "Updated",
    no_projects: "No projects yet. Create the first one.",
    tabs: { spec: "1 · Outline", kb: "2 · Materials", run: "3 · Generate", out: "4 · Output", prom: "5 · Prompt Editor" },
    spec_hint: "This is the outline (input spec for AutoGenBook). Edit and save.",
    save: "Save outline",
    saved: "Saved",
    kb_hint: "Upload existing materials (PDF, DOCX, MD, TXT, PPTX…) — becomes a knowledge base.",
    upload: "Upload file",
    drop_hint: "or drop files here",
    no_files: "No files. Drop materials here.",
    refresh: "Refresh",
    settings_hint: "Generation run configuration.",
    model: "Model",
    web_rag: "Enable web retrieval (RAG)",
    audit: "Audit",
    audit_off: "Off",
    audit_warn: "Warn",
    audit_strict: "Strict",
    pdf: "Generate PDF",
    export_tex: "Export TeX/PDF (pandoc)",
    run: "Start generation",
    running: "Running…",
    cancel: "Cancel run",
    pause: "Pause",
    resume: "Resume",
    stop: "Stop",
    run_log: "Run log",
    status: "Status",
    output_hint: "Generated files and chapters. Click to preview.",
    download: "Download",
    no_output: "No output yet. Start generation.",
    markdown: "Markdown",
    tokens_cost: "Tokens / cost",
    st_idle: "Ready",
    st_running: "Running",
    st_done: "Done",
    st_error: "Error",
    st_cancelled: "Cancelled",
    confirm_delete: "Really delete project?",
    provider: "Provider",
    not_set: "not set",
    analyze_btn: "AI Analysis & Prefill parameters",
    analyzing: "AI analysis running…",
    params_title: "Course parameters (Setup Assistant)",
    params_note: "Saved to project.json and injected into the outline as generation context.",
    param_title: "Title (suggested)",
    param_audience: "Persona / Target audience",
    param_tone: "Tone of voice",
    param_purpose: "Output purpose",
    param_language: "Output language",
    param_language_note: "Must be respected regardless of the source-material or instruction language.",
    param_depth: "Recommended depth",
    save_params: "Save parameters",
    outline_run: "1 · Generate structure only (Outline)",
    full_run: "2 · Generate full book",
    gen_node: "Generate this node",
    copy_notebook: "Copy as NotebookLM source",
    copied: "Copied to clipboard",
    no_structure: "No structure generated yet. Run step 1 (Outline).",
    tree_hint: "Chapter tree",
    prom: "5 · Prompts",
    prompts_hint: "Tune AutoGenBook system prompts. Changes propagate to recursive section generation.",
    prom_project: "Project prompts (this project)",
    prom_global: "Global prompts (default templates)",
    prom_reset: "Reset to default",
    prom_save: "Save changes",
    node_modal_title: "⚡ Generate this node",
    node_modal_kb_hint: "None selected = use the whole knowledge base.",
    node_include: "Include existing generated text as context (rewrite/improve)",
    node_rag: "Enable Web RAG (internet search) for this section",
    node_prompt: "Specific instructions for this chapter",
    node_prompt_ph: "e.g. Focus on S-D logic in SaaS, explain Value-in-Exchange vs Value-in-Use using Spotify as an example.",
    node_kb_title: "Priority sources (kb/) — MUST be used",
    node_run: "Generate now",
    cancel_modal: "Cancel",
    running_from: "Run in progress — live log",
  },
};

let LANG = "cs";
const T = (k) => (I18N[LANG][k] ?? I18N.cs[k] ?? k);
// fallback: nikdy nevykreslit 'undefined'
const TL = (k) => {
  const v = (I18N[LANG].tabs && I18N[LANG].tabs[k]) || (I18N.cs.tabs && I18N.cs.tabs[k]) || k;
  return (v === undefined || v === null || String(v).trim() === "") ? k : v;
};

const app = document.getElementById("app");
/* Globální stav běhu (nezávislý na aktivní záložce) */
window._run = { status: "idle", paused: false, lines: [], es: null };

/* ── helpers ──────────────────────────────────────────────────── */
async function api(url, opts) {
  const r = await fetch(url, opts);
  if (r.status === 401) {
    window.location.href = "/login";
    throw new Error("unauthorized");
  }
  if (!r.ok) {
    let msg = r.statusText;
    try { msg = (await r.json()).detail || msg; } catch (e) {}
    throw new Error(msg);
  }
  const ct = r.headers.get("content-type") || "";
  return ct.includes("json") ? r.json() : r.text();
}
async function apiJSON(url, method, body) {
  return api(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function sizeH(n) {
  if (n < 1024) return n + " B";
  if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
  return (n / 1048576).toFixed(1) + " MB";
}
function toast(msg) {
  let el = document.querySelector(".toast");
  if (!el) { el = document.createElement("div"); el.className = "toast"; document.body.appendChild(el); }
  el.textContent = msg; el.classList.add("show");
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove("show"), 2600);
}
function setLang(l) {
  LANG = l; document.documentElement.lang = l;
  document.getElementById("lang-toggle").textContent = l === "cs" ? "🌐 EN" : "🌐 CS";
}

/* ── markdown (minimal renderer) ──────────────────────────────── */
function md(html) {
  const lines = html.replace(/\r\n/g, "\n").split("\n");
  let out = "", inCode = false, code = [];
  const flushCode = () => { if (code.length) { out += "<pre><code>" + esc(code.join("\n")) + "</code></pre>"; code = []; } };
  for (const raw of lines) {
    const s = raw.trimEnd();
    if (/^```/.test(s)) { if (inCode) { inCode = false; flushCode(); } else { flushCode(); inCode = true; } continue; }
    if (inCode) { code.push(raw); continue; }
    let t = esc(s);
    if (/^### /.test(s)) { out += "<h3>" + t.slice(4) + "</h3>"; continue; }
    if (/^## /.test(s)) { out += "<h2>" + t.slice(3) + "</h2>"; continue; }
    if (/^# /.test(s)) { out += "<h1>" + t.slice(2) + "</h1>"; continue; }
    if (/^- /.test(s)) { out += "<li>" + t.slice(2) + "</li>"; continue; }
    if (/^\s*$/.test(s)) { out += "<p></p>"; continue; }
    t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>");
    t = t.replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    out += "<p>" + t + "</p>";
  }
  flushCode();
  return out;
}

/* ── status badge ─────────────────────────────────────────────── */
function badge(st) {
  const map = { idle: "st_idle", running: "st_running", done: "st_done", error: "st_error", cancelled: "st_cancelled" };
  return `<span class="badge ${st}">${T(map[st] || "st_idle")}</span>`;
}

/* ── views ────────────────────────────────────────────────────── */
async function render(promise) {
  app.innerHTML = '<div class="loading">Loading…</div>';
  try {
    const html = await promise();   // <-- funkci je nutné ZAVOLAT
    app.innerHTML = html;
  } catch (e) {
    app.innerHTML = `<div class="card"><h2>Chyba</h2><pre class="console">${esc(e.message || String(e))}</pre></div>`;
  }
}

async function loadConfig() {
  try {
    const c = await api("/api/config");
    const el = document.getElementById("config-provider");
    if (el) {
      el.textContent = (c.base_url || T("not_set")) + " · " + (c.model || "");
      el.title = T("provider") + ": " + (c.base_url || "-") + "\nmodel: " + c.model;
    }
    const lo = document.getElementById("logout-btn");
    if (lo) lo.style.display = c.auth ? "" : "none";
  } catch (e) {}
}

function dashboard(projects) {
  return `
    <div class="page-head">
      <h1>${T("projects")}</h1>
      <button class="btn primary" onclick="newProject()">+ ${T("new_project")}</button>
    </div>
    <div class="grid">
      ${projects.map((p) => `
        <div class="card clickable" onclick="openProject('${p.id}')">
          <div class="card-title">${esc(p.name)}</div>
          <div class="muted">${p.id}</div>
          <div class="card-row">
            <span class="badge ${p.run_status}">${badge(p.run_status)}</span>
            <span class="muted">${esc(p.updated)}</span>
          </div>
        </div>`).join("") || `<div class="empty">${T("no_projects")}</div>`}
    </div>`;
}

function newProject() {
  render(async () => `
    <div class="page-head"><h1>${T("new_project")}</h1></div>
    <div class="card">
      <div class="field"><label>${T("project_name")}</label>
        <input type="text" id="np-name" placeholder="PV260 …" /></div>
      <div class="field"><label>${T("language")}</label>
        <select id="np-lang" class="btn">
          <option value="cs">${T("cs")}</option>
          <option value="en">${T("en")}</option>
        </select></div>
      <div class="field"><label>${T("tabs.spec")}</label>
        <textarea id="np-spec" rows="12" placeholder='${esc("Název: …")}'></textarea></div>
      <button class="btn primary" onclick="doCreateProject()">${T("create")}</button>
    </div>`);
}
async function doCreateProject() {
  const name = document.getElementById("np-name").value.trim();
  const language = document.getElementById("np-lang").value;
  const spec = document.getElementById("np-spec").value;
  try {
    const p = await apiJSON("/api/projects", "POST", { name, language, spec });
    toast(T("saved")); await loadProject(p.id);
  } catch (e) { toast(e.message); }
}

/* ── project view with tabs ───────────────────────────────────── */
async function loadProject(pid) {
  const p = await api(`/api/projects/${pid}`);
  window._pid = pid; window._proj = p;
  // Pokud na backendu běží proces, udržuj globální stav "running" (i po F5).
  try {
    const st = await api(`/api/projects/${pid}/status`);
    if (st.status === "running") { window._run.status = "running"; window._run.paused = !!st.paused; }
    else { window._run.status = st.status; window._run.paused = false; window._run.lines = []; }
  } catch (e) {}
  renderProjectTabs();
}
async function renderProjectTabs(active = "spec") {
  const p = window._proj;
  const viewFn = viewMap[active] || (() => "<div class='empty'></div>");
  app.innerHTML = `
    <div class="page-head">
      <h1>${esc(p.name)}</h1>
      <div class="row">
        <span id="run-badge">${badge(window._run.status === "running" ? "running" : p.run_status)}</span>
        <button class="btn ghost" onclick="showDashboard()">${T("back")}</button>
      </div>
    </div>
    <div class="tabs">
      ${["spec","kb","run","out","prom"].map((t) => `<button class="tab ${t===active?"active":""}" onclick="tab('${t}')">${TL(t)}</button>`).join("")}
    </div>
    <div id="tab-body"></div>`;
  const body = document.getElementById("tab-body");
  body.innerHTML = await viewFn();
  if (active === "kb") setupKb();
  if (active === "spec") renderParamsForm();
  if (active === "run") ensureRunView();
  if (active === "prom") renderPrompts();
}
function updateRunBadge() {
  const b = document.getElementById("run-badge");
  if (b) b.innerHTML = badge(window._run.status === "running" ? "running" : (window._proj && window._proj.run_status));
}
function tab(name) { renderProjectTabs(name); }

const viewMap = {
  spec: () => `
    <div class="card">
      <p class="muted">${T("spec_hint")}</p>
      <textarea id="spec-editor" rows="18">${esc(window._proj.spec)}</textarea>
      <div class="row" style="margin-top:12px;gap:10px;flex-wrap:wrap">
        <button class="btn primary" onclick="saveSpec()">${T("save")}</button>
      </div>
      <div id="params-form" style="display:none;margin-top:18px"></div>
    </div>`,
  kb: () => `
    <div class="card">
      <p class="muted">${T("kb_hint")}</p>
      <div class="drop" id="drop">⬆️ ${T("upload")}<br><span class="muted">${T("drop_hint")}</span></div>
      <input type="file" id="kb-upload" multiple style="display:none" />
      <div id="kb-list"><span class="muted">…</span></div>
    </div>`,
  run: () => `
    <div class="card">
      <p class="muted">${T("settings_hint")}</p>
      <div class="row">
        <div class="field"><label>${T("model")}</label>
          <input type="text" id="cfg-model" value="${esc(window._model || "")}" placeholder="${esc("qwen3.5")}" /></div>
      </div>
      <div class="check"><input type="checkbox" id="cfg-rag" /> ${T("web_rag")}</div>
      <div class="row"><div class="field"><label>${T("audit")}</label>
        <select id="cfg-audit" class="btn">
          <option value="">${T("audit_off")}</option>
          <option value="warn">${T("audit_warn")}</option>
          <option value="strict">${T("audit_strict")}</option>
        </select></div></div>
      <div class="check"><input type="checkbox" id="cfg-pdf" checked /> ${T("pdf")}</div>
      <div class="check"><input type="checkbox" id="cfg-tex" /> ${T("export_tex")}</div>
      <div class="row" style="margin-top:14px;gap:10px;flex-wrap:wrap">
        <button class="btn primary" onclick="startRun('outline_only')">🧭 ${T("outline_run")}</button>
        <button class="btn primary" onclick="startRun('book')">📖 ${T("full_run")}</button>
      </div>
    </div>`,
  out: async () => await renderOutput(),
  prom: async () => await renderPrompts(),
};

/* spec save */
async function saveSpec() {
  const spec = document.getElementById("spec-editor").value;
  try {
    await apiJSON(`/api/projects/${window._pid}/spec`, "PUT", { spec });
    window._proj = await api(`/api/projects/${window._pid}`);
    toast(T("saved"));
  } catch (e) { toast(e.message); }
}

/* setup assistant (analyze spec → prefill params) */
async function analyzeSpec() {
  const btn = document.getElementById("analyze-btn");
  if (btn) { btn.disabled = true; btn.textContent = "⏳ " + T("analyzing"); }
  try {
    const res = await apiJSON(`/api/projects/${window._pid}/analyze-spec`, "POST", {});
    window._proj = await api(`/api/projects/${window._pid}`);
    window._proj.analysis = res;
    renderParamsForm();
    toast(T("saved"));
  } catch (e) { toast(e.message); }
  finally { if (btn) { btn.disabled = false; btn.textContent = "✨ " + T("analyze_btn"); } }
}
function renderParamsForm() {
  const box = document.getElementById("params-form");
  if (!box) return;
  const a = (window._proj && window._proj.analysis) || {};
  const f = (k, d) => esc((a[k] != null && a[k] !== "") ? a[k] : d);
  const depth = Number(a.recommended_depth);
  box.style.display = "block";
  box.innerHTML = `
    <h3>✨ ${T("params_title")}</h3>
    <p class="muted">${T("params_note")}</p>
    <div class="params-grid">
      <div class="field"><label>${T("param_title")}</label>
        <input type="text" id="an-title" value="${f("suggested_title", "")}" placeholder="…" /></div>
      <div class="field"><label>${T("param_language")}</label>
        <input type="text" id="an-language" list="an-lang-list" value="${f("language", "English")}" placeholder="English" />
        <datalist id="an-lang-list">
          <option value="English"></option><option value="Čeština"></option>
          <option value="Deutsch"></option><option value="Español"></option>
          <option value="Français"></option><option value="Italiano"></option>
          <option value="Polski"></option><option value="Slovenčina"></option>
        </datalist>
        <p class="muted" style="font-size:11px;margin:4px 0 0">${T("param_language_note")}</p></div>
      <div class="field"><label>${T("param_depth")}</label>
        <select id="an-depth" class="btn">
          ${[2,3,4,5].map((d) => `<option value="${d}" ${(!depth || depth===d) && d===3 ? "selected" : depth===d ? "selected" : ""}>${d}</option>`).join("")}
        </select></div>
      <div class="field"><label>${T("param_audience")}</label>
        <input type="text" id="an-audience" value="${f("target_audience", "")}" placeholder="${esc("Studenti informatiky a Service Designu na FI MUNI")}" /></div>
      <div class="field"><label>${T("param_tone")}</label>
        <input type="text" id="an-tone" value="${f("tone_of_voice", "")}" placeholder="${esc("Akademický výkladový text s IT/SaaS příklady")}" /></div>
      <div class="field"><label>${T("param_purpose")}</label>
        <input type="text" id="an-purpose" value="${f("output_purpose", "")}" placeholder="${esc("Textbook / Podklad pro NotebookLM")}" /></div>
    </div>
    <div style="margin-top:10px" class="row">
      <button class="btn primary" onclick="saveParams()">${T("save_params")}</button>
      <button class="btn accent" onclick="analyzeSpec()">✨ ${T("analyze_btn")}</button>
    </div>`;
}
async function saveParams() {
  const payload = {
    suggested_title: document.getElementById("an-title").value.trim(),
    target_audience: document.getElementById("an-audience").value.trim(),
    tone_of_voice: document.getElementById("an-tone").value.trim(),
    output_purpose: document.getElementById("an-purpose").value.trim(),
    recommended_depth: Number(document.getElementById("an-depth").value) || 3,
    language: (document.getElementById("an-language").value.trim() || "English"),
  };
  try {
    const r = await apiJSON(`/api/projects/${window._pid}/analysis`, "PUT", payload);
    window._proj.analysis = r.analysis;
    toast(T("saved"));
  } catch (e) { toast(e.message); }
}

/* kb */
async function refreshKb() {
  const files = await api(`/api/projects/${window._pid}/kb`);
  document.getElementById("kb-list").innerHTML =
    files.map((f) => `
      <div class="file-row">
        <span>${esc(f.name)} <span class="muted">(${sizeH(f.size)})</span></span>
        <button class="btn danger" onclick="deleteKb('${esc(f.name)}')">${T("delete")}</button>
      </div>`).join("") || `<div class="empty">${T("no_files")}</div>`;
}
async function uploadFiles(fileList) {
  for (const f of Array.from(fileList || [])) {
    const fd = new FormData();
    fd.append("file", f);
    await api(`/api/projects/${window._pid}/kb`, { method: "POST", body: fd });
  }
  refreshKb();
}
async function uploadKb() {
  await uploadFiles(document.getElementById("kb-upload").files);
  document.getElementById("kb-upload").value = "";
}
function setupKb() {
  const input = document.getElementById("kb-upload");
  const drop = document.getElementById("drop");
  if (input) input.addEventListener("change", () => uploadFiles(input.files));
  if (drop) {
    drop.addEventListener("click", () => input.click());
    ["dragenter", "dragover"].forEach((ev) =>
      drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("drag"); })
    );
    ["dragleave", "drop"].forEach((ev) =>
      drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("drag"); })
    );
    drop.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadFiles(e.dataTransfer && e.dataTransfer.files);
    });
  }
  refreshKb();
}
async function deleteKb(name) {
  await api(`/api/projects/${window._pid}/kb/${encodeURIComponent(name)}`, { method: "DELETE" });
  refreshKb();
}

/* ── run ─────────────────────────────────────────────────────── */
function setRunRunning() {
  window._run.status = "running";
  window._run.paused = false;
  window._run.lines = [];
  if (window._proj) window._proj.run_status = "running";
}
async function startRun(mode) {
  const pid = window._pid;
  const cfg = {
    mode: mode || "book",
    model: document.getElementById("cfg-model").value.trim() || window._model || "",
    enable_web_rag: document.getElementById("cfg-rag").checked,
    audit_mode: document.getElementById("cfg-audit").value,
    pdf: document.getElementById("cfg-pdf").checked,
    export_tex: document.getElementById("cfg-tex").checked,
  };
  window._model = cfg.model;
  try {
    await apiJSON(`/api/projects/${pid}/run`, "POST", cfg);
    setRunRunning();
    await renderProjectTabs("run"); // vykreslí live okno a připojí SSE
  } catch (e) { toast(e.message); }
}
function ensureRunView() {
  if (window._run.status === "running") showRunConsole(window._pid);
}
async function showRunConsole(pid) {
  const body = document.getElementById("tab-body");
  if (!body) return;
  // Po F5 / návratu na záložku: načti historii logu ze serveru
  if (!window._run.lines.length) {
    try {
      const html = await api(`/api/projects/${pid}/log`);
      const text = html.replace(/^<pre>/, "").replace(/<\/pre>$/, "");
      window._run.lines = text.split("\n").filter((l) => l !== "");
    } catch (e) {}
  }
  const pausedBtn = window._run.paused
    ? `<button class="btn accent" id="btn-pause" onclick="resumeRun()">▶ ${T("resume")}</button>`
    : `<button class="btn" id="btn-pause" onclick="pauseRun()">⏸ ${T("pause")}</button>`;
  body.innerHTML = `<div class="card">
    <div class="page-head"><h2>${T("running_from")}</h2>
      <div class="row">${pausedBtn}<button class="btn danger" onclick="cancelRun()">⏹ ${T("stop")}</button></div>
    </div>
    <pre id="console" class="console">${esc(window._run.lines.join("\n"))}</pre>
  </div>`;
  const el = document.getElementById("console");
  if (el) el.scrollTop = el.scrollHeight;
  openEvents(pid);
}
function openEvents(pid) {
  if (window._run.es) { try { window._run.es.close(); } catch (e) {} }
  const es = new EventSource(`/api/projects/${pid}/events`);
  window._run.es = es;
  es.onmessage = (ev) => {
    let d; try { d = JSON.parse(ev.data); } catch (e) { return; }
    if (d.type === "log") {
      window._run.lines.push(d.text);
      const el = document.getElementById("console");
      if (el) { el.textContent += d.text + "\n"; el.scrollTop = el.scrollHeight; }
    } else if (d.type === "status") {
      const st = d.status || "idle";
      window._run.lines.push(`>>> ${T("status")}: ${T("st_" + st)}`);
      const el = document.getElementById("console");
      if (el) { el.textContent += `\n>>> ${T("status")}: ${T("st_" + st)}\n`; }
      window._run.status = st;
      window._run.paused = false;
      if (window._proj) window._proj.run_status = st;
      es.close(); window._run.es = null;
      setTimeout(() => updateRunBadge(), 0);
    }
  };
}
async function cancelRun() {
  try { await apiJSON(`/api/projects/${window._pid}/cancel`, "POST", {}); } catch (e) {}
}
async function pauseRun() {
  try {
    await apiJSON(`/api/projects/${window._pid}/pause`, "POST", {});
    window._run.paused = true;
    const b = document.getElementById("btn-pause");
    if (b) { b.textContent = "▶ " + T("resume"); b.setAttribute("onclick", "resumeRun()"); b.classList.add("accent"); }
  } catch (e) { toast(e.message); }
}
async function resumeRun() {
  try {
    await apiJSON(`/api/projects/${window._pid}/resume`, "POST", {});
    window._run.paused = false;
    const b = document.getElementById("btn-pause");
    if (b) { b.textContent = "⏸ " + T("pause"); b.setAttribute("onclick", "pauseRun()"); b.classList.remove("accent"); }
  } catch (e) { toast(e.message); }
}
async function refreshStatus() {
  try {
    const s = await api(`/api/projects/${window._pid}/status`);
    window._proj.run_status = s.status;
    window._run.status = s.status;
    updateRunBadge();
    renderProjectTabs("out");
  } catch (e) {}
}

/* ── prompts editor ──────────────────────────────────────────── */
async function renderPrompts() {
  const pid = window._pid;
  let data = { keys: [], defaults: {}, global: {}, project: {}, effective: {} };
  try { data = await api(`/api/projects/${pid}/prompts`); } catch (e) { toast(e.message); }
  window._promptData = data;
  const panel = (idp, value) => {
    const key = idp.slice(3);
    return `<details class="prompt-item" data-key="${esc(key)}">
      <summary>${esc(key)} <button class="btn tiny ghost" onclick="event.preventDefault();event.stopPropagation();resetPromptEl('${idp}')">${T("prom_reset")}</button></summary>
      <textarea id="${idp}" rows="10" class="code">${esc(value)}</textarea>
    </details>`;
  };
  document.getElementById("tab-body").innerHTML = `
    <div class="card">
      <p class="muted">${T("prompts_hint")}</p>
      <h3>${T("prom_project")}</h3>
      ${data.keys.map((k) => panel(`pp-${k}`, data.effective[k] || "")).join("")}
      <button class="btn primary" onclick="saveProjectPrompts()">${T("prom_save")}</button>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>${T("prom_global")}</h3>
      <p class="muted">${T("prom_project")} ukládá překryvy pro tento projekt; globální šablony se aplikují na všechny projekty (po lokální obnově).</p>
      ${data.keys.map((k) => panel(`gp-${k}`, data.global[k] || data.defaults[k] || "")).join("")}
      <button class="btn primary" onclick="saveGlobalPrompts()">${T("prom_save")}</button>
    </div>`;
}
function resetPromptEl(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const data = window._promptData || {};
  el.value = data.defaults[id.slice(3)] || "";
}
async function saveProjectPrompts() {
  const data = window._promptData || {};
  const overrides = {};
  for (const k of data.keys || []) {
    const el = document.getElementById(`pp-${k}`);
    if (el && el.value.trim() !== (data.defaults[k] || "").trim()) overrides[k] = el.value;
  }
  try {
    await apiJSON(`/api/projects/${window._pid}/prompts`, "PUT", { overrides });
    toast(T("saved"));
  } catch (e) { toast(e.message); }
}
async function saveGlobalPrompts() {
  const data = window._promptData || {};
  const overrides = {};
  for (const k of data.keys || []) {
    const el = document.getElementById(`gp-${k}`);
    if (el && el.value.trim() !== (data.defaults[k] || "").trim()) overrides[k] = el.value;
  }
  try {
    await apiJSON(`/api/prompts/global`, "PUT", { overrides });
    toast(T("saved"));
  } catch (e) { toast(e.message); }
}

/* output */
function renderTree(items, depth) {
  depth = depth || 0;
  return (items || []).map((n) => {
    const hasKids = n.children && n.children.length;
    const open = depth === 0;
    const size = n.exists ? `<span class="muted">(${sizeH(n.size)})</span>` : "";
    return `
      <div class="tnode">
        <div class="trow" style="--depth:${depth}">
          ${hasKids
            ? `<span class="caret" onclick="toggleNode(this)">${open ? "▼" : "▶"}</span>`
            : `<span class="caret leaf"></span>`}
          <span class="tlabel ${n.exists ? "link" : ""} ${hasKids ? "branch" : ""}" onclick="previewNode('${esc(n.id)}','${esc(n.title)}')">
            ${n.exists ? "🟢" : "⚪"} ${esc(n.title || n.id)}
          </span>
          ${size}
          ${n.leaf ? `<button class="btn tiny" onclick="runSingleNode('${esc(n.id)}','${esc(n.title)}')">⚡ ${T("gen_node")}</button>` : ""}
        </div>
        ${hasKids ? `<div class="tkids ${open ? "" : "hidden"}">${renderTree(n.children, depth + 1)}</div>` : ""}
      </div>`;
  }).join("");
}
function toggleNode(caret) {
  const row = caret.parentElement;
  const kids = row.nextElementSibling;
  const open = !row.classList.contains("branch-open");
  row.classList.toggle("branch-open", open);
  if (kids) kids.classList.toggle("hidden", !open);
  caret.textContent = open ? "▼" : "▶";
}
async function previewNode(nid, title) {
  const path = `sections/${nid}.md`;
  try {
    const html = await api(`/api/projects/${window._pid}/output/file?path=${encodeURIComponent(path)}`);
    const text = html.replace(/^<pre>/, "").replace(/<\/pre>$/, "");
    document.getElementById("preview").innerHTML =
      `<h1>${esc(title || nid)}</h1>${md(text)}` +
      `<div style="margin-top:18px"><button class="btn accent" onclick="copyNode('${esc(path)}')">${T("copy_notebook")}</button></div>`;
  } catch (e) { toast(e.message); }
}
async function runSingleNode(nid, title) {
  const pid = window._pid;
  let kbFiles = [];
  try { kbFiles = await api(`/api/projects/${pid}/kb`); } catch (e) {}
  const modal = document.getElementById("modal-root");
  if (!modal) return;
  modal.innerHTML = `
    <div class="modal-backdrop" onclick="if(event.target===this)closeModal()">
      <div class="modal">
        <h3>${T("node_modal_title")} — ${esc(title || nid)} <span class="muted">(${esc(nid)})</span></h3>
        <div class="check"><input type="checkbox" id="nmode-include" /> ${T("node_include")}</div>
        <div class="check"><input type="checkbox" id="nmode-rag" /> ${T("node_rag")}</div>
        <div class="field"><label>${T("node_prompt")}</label>
          <textarea id="nmode-prompt" rows="3" placeholder="${esc(T("node_prompt_ph"))}"></textarea></div>
        <div class="field"><label>${T("node_kb_title")}</label>
          <p class="muted">${T("node_modal_kb_hint")}</p>
          <div class="kb-multi">${kbFiles.length
            ? kbFiles.map((f) => `<label class="check kb-item"><input type="checkbox" class="nmode-kb" value="${esc(f.name)}" /> ${esc(f.name)}</label>`).join("")
            : `<div class="muted">—</div>`}</div>
        </div>
        <div class="row" style="margin-top:14px;gap:10px">
          <button class="btn primary" onclick="runNode('${esc(nid)}')">${T("node_run")}</button>
          <button class="btn" onclick="closeModal()">${T("cancel_modal")}</button>
        </div>
      </div>
    </div>`;
  modal.style.display = "block";
}
function closeModal() {
  const modal = document.getElementById("modal-root");
  if (modal) { modal.innerHTML = ""; modal.style.display = "none"; }
}
async function runNode(nid) {
  const pid = window._pid;
  const custom_prompt = document.getElementById("nmode-prompt") ? document.getElementById("nmode-prompt").value.trim() : "";
  const include_existing = !!(document.getElementById("nmode-include") && document.getElementById("nmode-include").checked);
  const kb_files = Array.from(document.querySelectorAll(".nmode-kb:checked")).map((c) => c.value);
  const cfg = {
    mode: "single_node", node_id: nid,
    model: (document.getElementById("cfg-model") ? document.getElementById("cfg-model").value.trim() : "") || window._model || "",
    enable_web_rag: !!(document.getElementById("nmode-rag") && document.getElementById("nmode-rag").checked),
    audit_mode: "", pdf: false, export_tex: false,
    include_existing, custom_prompt, kb_files,
  };
  closeModal();
  try {
    await apiJSON(`/api/projects/${pid}/run`, "POST", cfg);
    setRunRunning();
    await renderProjectTabs("run");
  } catch (e) { toast(e.message); }
}
async function copyNode(path) {
  try {
    const html = await api(`/api/projects/${window._pid}/output/file?path=${encodeURIComponent(path)}`);
    const raw = html.replace(/^<pre>/, "").replace(/<\/pre>$/, "");
    await copyText(cleanForNotebook(raw));
    toast(T("copied"));
  } catch (e) { toast(e.message); }
}
function cleanForNotebook(t) {
  return t
    .replace(/\r\n/g, "\n")
    // odstranění LaTeXových citací \cite{...} / \cite[...]{...} (a \citep/\citet, \footnote)
    .replace(/\\cite(?:p|t)?(?:\[[^\]]*\])?\{[^}]*\}/g, "")
    .replace(/\\footnote(?:\[[^\]]*\])?\{[^}]*\}/g, "")
    .replace(/\\cite(?:p|t)?\{[^}]*\}\s*/g, "")
    // zbytkové LaTeX příkazy \cmd{...} → rozbalí na vnitřní text (např. \textbf{text} -> text)
    .replace(/\\(?:[a-zA-Z]+|\[^a-zA-Z])(?:\[[^\]]*\])?\{([^{}]*)\}/g, "$1")
    .replace(/```[\s\S]*?```/g, (m) => m.replace(/```\w*\n?/g, "\n"))
    .replace(/^>\s?/gm, "")
    .replace(/^[-*+]\s+/gm, "")
    .replace(/^\d+\.\s+/gm, "")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/\s*[-=]{3,}\s*$/gm, "")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/_([^_]+)_/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .replace(/\[([^\]]+)\]\((?:https?:[^)]+)\)/g, "$1")
    .replace(/^\s*\|.*\|\s*$/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
function copyText(t) {
  if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(t);
  return new Promise((res, rej) => {
    const ta = document.createElement("textarea");
    ta.value = t; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); res(); } catch (e) { rej(e); }
    ta.remove();
  });
}
async function renderOutput() {
  const pid = window._pid;
  const head = `<div class="page-head"><h2>${T("output_hint")}</h2>
      <button class="btn" onclick="viewRunLog()">📄 ${T("run_log")}</button></div>`;
  let st = { tree: [], has_structure: false, generated: 0, total: 0 };
  try { st = await api(`/api/projects/${pid}/structure`); } catch (e) {}
  if (st.has_structure && st.tree.length) {
    return `${head}
      <div class="split">
        <div class="card tree" style="min-width:320px;max-width:560px">
          <div class="muted" style="margin-bottom:8px">${T("tree_hint")} — ${st.generated}/${st.total}</div>
          <div class="tree-nodes">${renderTree(st.tree)}</div>
        </div>
        <div class="preview" id="preview">${T("output_hint")}</div>
      </div>`;
  }
  // fallback: plochý seznam souborů
  let files = [];
  try { files = await api(`/api/projects/${pid}/output`); } catch (e) {}
  if (!files.length) return head + `<div class="empty">${T("no_output")}</div>`;
  const mdFiles = files.filter((f) => f.path.toLowerCase().endsWith(".md"));
  return `${head}
    <div class="split">
      <div class="card tree">
        <div class="tree-nodes">${mdFiles.map((f) => `
          <div class="node" data-path="${esc(f.path)}" onclick="preview('${esc(f.path)}')">
            <span class="file-icon">📄</span>${esc(f.path)}</div>`).join("") || `<div class="empty">${T("no_structure")}</div>`}</div>
      </div>
      <div class="preview" id="preview">${T("output_hint")}</div>
    </div>`;
}
async function preview(path) {
  const pid = window._pid;
  try {
    const html = await api(`/api/projects/${pid}/output/file?path=${encodeURIComponent(path)}`);
    // strip <pre> wrapper returned by server
    const text = html.replace(/^<pre>/, "").replace(/<\/pre>$/, "");
    document.getElementById("preview").innerHTML = md(text);
    document.querySelectorAll(".node").forEach((n) => n.classList.toggle("active", n.dataset.path === path));
  } catch (e) { toast(e.message); }
}

async function viewRunLog() {
  try {
    const html = await api(`/api/projects/${window._pid}/log`);
    const text = html.replace(/^<pre>/, "").replace(/<\/pre>$/, "");
    document.getElementById("preview").innerHTML =
      `<pre style="white-space:pre-wrap">${esc(text)}</pre>`;
    document.querySelectorAll(".node").forEach((n) => n.classList.remove("active"));
  } catch (e) { toast(e.message); }
}
/* dashboard nav */
async function showDashboard() {
  render(async () => {
    const projects = await api("/api/projects");
    return dashboard(projects);
  });
}
async function openProject(pid) {
  try { await loadProject(pid); }
  catch (e) { toast(e.message); showDashboard(); }
}

/* boot */
async function init() {
  const saved = localStorage.getItem("agb_lang");
  if (saved) setLang(saved);
  else if (navigator.language.toLowerCase().startsWith("en")) setLang("en");
  document.getElementById("lang-toggle").onclick = () => { setLang(LANG === "cs" ? "en" : "cs"); localStorage.setItem("agb_lang", LANG); loadConfig(); renderCurrent(); };
  window.newProject = newProject;
  window.openProject = openProject;
  window.showDashboard = showDashboard;
  window.doCreateProject = doCreateProject;
  window.tab = tab;
  window.saveSpec = saveSpec;
  window.analyzeSpec = analyzeSpec;
  window.saveParams = saveParams;
  window.runSingleNode = runSingleNode;
  window.runNode = runNode;
  window.closeModal = closeModal;
  window.renderPrompts = renderPrompts;
  window.saveProjectPrompts = saveProjectPrompts;
  window.saveGlobalPrompts = saveGlobalPrompts;
  window.resetPromptEl = resetPromptEl;
  window.copyNode = copyNode;
  window.toggleNode = toggleNode;
  window.previewNode = previewNode;
  window.uploadKb = uploadKb;
  window.deleteKb = deleteKb;
  window.startRun = startRun;
  window.cancelRun = cancelRun;
  window.pauseRun = pauseRun;
  window.resumeRun = resumeRun;
  window.preview = preview;
  window.viewRunLog = viewRunLog;
  loadConfig();
  await showDashboard();
}
async function renderCurrent() { await showDashboard(); }
init();
