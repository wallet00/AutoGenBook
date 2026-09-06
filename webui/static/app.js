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
    tabs: { spec: "1 · Osnova", kb: "2 · Materiály", run: "3 · Generování", out: "4 · Výstup" },
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
    tabs: { spec: "1 · Outline", kb: "2 · Materials", run: "3 · Generate", out: "4 · Output" },
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
  },
};

let LANG = "cs";
const T = (k) => (I18N[LANG][k] ?? I18N.cs[k] ?? k);
const TL = (k) => (I18N[LANG].tabs[k]);

const app = document.getElementById("app");

/* ── helpers ──────────────────────────────────────────────────── */
async function api(url, opts) {
  const r = await fetch(url, opts);
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
  renderProjectTabs();
}
function renderProjectTabs(active = "spec") {
  const p = window._proj;
  app.innerHTML = `
    <div class="page-head">
      <h1>${esc(p.name)}</h1>
      <div class="row">
        ${badge(p.run_status)}
        <button class="btn ghost" onclick="showDashboard()">${T("back")}</button>
      </div>
    </div>
    <div class="tabs">
      ${["spec","kb","run","out"].map((t) => `<button class="tab ${t===active?"active":""}" onclick="tab('${t}')">${TL(t)}</button>`).join("")}
    </div>
    <div id="tab-body">${viewMap[active]()}</div>`;
  if (active === "kb") setupKb();
}
function tab(name) { renderProjectTabs(name); }

const viewMap = {
  spec: () => `
    <div class="card">
      <p class="muted">${T("spec_hint")}</p>
      <textarea id="spec-editor" rows="22">${esc(window._proj.spec)}</textarea>
      <div style="margin-top:12px"><button class="btn primary" onclick="saveSpec()">${T("save")}</button></div>
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
      <div class="field"><label>${T("audit")}</label>
        <select id="cfg-audit" class="btn">
          <option value="">${T("audit_off")}</option>
          <option value="warn">${T("audit_warn")}</option>
          <option value="strict">${T("audit_strict")}</option>
        </select></div>
      <div class="check"><input type="checkbox" id="cfg-pdf" checked /> ${T("pdf")}</div>
      <div class="check"><input type="checkbox" id="cfg-tex" /> ${T("export_tex")}</div>
      <button class="btn primary" id="run-btn" onclick="startRun()">▶ ${T("run")}</button>
    </div>`,
  out: async () => await renderOutput(),
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

/* run */
async function startRun() {
  const pid = window._pid;
  const cfg = {
    model: document.getElementById("cfg-model").value.trim() || window._model || "",
    enable_web_rag: document.getElementById("cfg-rag").checked,
    audit_mode: document.getElementById("cfg-audit").value,
    pdf: document.getElementById("cfg-pdf").checked,
    export_tex: document.getElementById("cfg-tex").checked,
  };
  window._model = cfg.model;
  try {
    await apiJSON(`/api/projects/${pid}/run`, "POST", cfg);
    renderProjectTabs("run");
    startEvents(pid);
  } catch (e) { toast(e.message); }
}
function startEvents(pid) {
  const body = document.getElementById("tab-body");
  const el = document.createElement("pre");
  el.className = "console"; el.id = "console";
  body.innerHTML = `<div class="page-head"><h2>${T("run_log")}</h2>
    <button class="btn danger" onclick="cancelRun()">${T("cancel")}</button></div>`;
  body.appendChild(el);
  const es = new EventSource(`/api/projects/${pid}/events`);
  es.onmessage = (ev) => {
    const d = JSON.parse(ev.data);
    if (d.type === "log") {
      el.textContent += d.text + "\n"; el.scrollTop = el.scrollHeight;
    } else if (d.type === "status") {
      el.textContent += `\n>>> ${T("status")}: ${T("st_" + (d.status || "idle"))}\n`;
      es.close();
      refreshStatus();
    }
  };
}
async function cancelRun() {
  try { await apiJSON(`/api/projects/${window._pid}/cancel`, "POST", {}); } catch (e) {}
}
async function refreshStatus() {
  try {
    const s = await api(`/api/projects/${window._pid}/status`);
    window._proj.run_status = s.status;
    renderProjectTabs("out");
  } catch (e) {}
}

/* output */
async function renderOutput() {
  const pid = window._pid;
  let files = [];
  try { files = await api(`/api/projects/${pid}/output`); } catch (e) {}
  if (!files.length) return `<div class="empty">${T("no_output")}</div>`;
  const mdFiles = files.filter((f) => f.path.toLowerCase().endsWith(".md"));
  const other = files.filter((f) => !f.path.toLowerCase().endsWith(".md"));
  const tree = mdFiles.map((f) => f.path).join("\n");
  return `
    <div class="page-head"><h2>${T("output_hint")}</h2></div>
    <div class="split">
      <div class="card tree">
        <div class="tree-nodes">${mdFiles.map((f) => `
          <div class="node" data-path="${esc(f.path)}" onclick="preview('${esc(f.path)}')">
            <span class="file-icon">📄</span>${esc(f.path)}</div>`).join("") || `<div class="empty">${T("no_output")}</div>`}</div>
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
  window.uploadKb = uploadKb;
  window.deleteKb = deleteKb;
  window.startRun = startRun;
  window.cancelRun = cancelRun;
  window.preview = preview;
  loadConfig();
  await showDashboard();
}
async function renderCurrent() { await showDashboard(); }
init();
