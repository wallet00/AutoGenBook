# AutoGenBook — Web UI: Přehled aktuálního stavu

> Strukturovaný technický přehled UI pro AutoGenBook (konsultace / rozšíření).
> Verze souvisejí s pracovním repozitářem `wallet00/AutoGenBook`, složka `webui/`.

---

## 1. Použitý tech-stack

### Frontend
- **Žádný framework** — čistý **vanilla JavaScript SPA** (`webui/static/app.js`), bez buildu/bundleru (žádný React/Next/Vue/Streamlit/Gradio).
- Jediná HTML stránka `webui/templates/index.html` + `app.js` + `app.css` (plus samostatná přihlašovací stránka `login.html`).
- **i18n CS/EN** — překladové slovníky v `app.js` (klíč `I18N`), aktivní jazyk uložený v `localStorage` (`agb_lang`).
- Vykreslování Markdownu: **vlastní minimalistický renderer** (funkce `md()`), žádná knihovna.
- Live log běhu: **Server-Sent Events (SSE)** přes `EventSource`.

### Backend & integrace
- **Python 3 + FastAPI** (`webui/server.py`), server **uvicorn**. Obluha: `/static` (StaticFiles), `/api/*` (JSON), `/login`, `/logout`.
- **Runner** (`webui/runner.py`): spouští AutoGenBook CLI (`python main.py --mode book …`) jako **subproces**, zachytává stdout do `run.log` a streamuje do UI přes SSE; řídí stav běhu (running/done/error/cancelled) v paměti.
- **Integrace s LLM**: OpenAI-kompatibilní provider **e-INFRA** (`https://llm.ai.e-infra.cz/v1`, model `qwen3.5`) nastavený env proměnnými (`AUTOGENBOOK_LLM_BASE_URL/_API_KEY/_MODEL`), zpracuje ho `openrouter_llm.py`.

### Správa stavu (state management)
- **Klient**: JS globály `window._pid`, `window._proj`, `window._model` (+ `localStorage` jen pro jazyk). Žádná knihovna (Redux apod.).
- **Server**: stav běhů v paměti (dict v `Runner`); **žádná databáze** — vše je **souborové úložiště**.

### Ukládání dat / projektů
- **Filesystem layout** (bez databáze), v kořeni `projects/`:
  ```
  projects/<id>/
    project.json        # metadata projektu (id, name, language, spec, timestamps)
    spec.txt            # vstupní osnova (input spec)
    kb/                 # nahrané materiály (znalostní báze)
    output/             # výstup běhu (struktura, sekce, logy, PDF/TeX)
    run.log             # běhový log posledního/aktuálního běhu
  ```
- Docker nasazení: `projects/` na **PVC** (perzistence mezi restarty), nasazení přes Rancher/K8s (namespace `walletzky-ns`).

---

## 2. Aktuální architektura UI a komponenty

### Obrazovky / moduly
1. **Přihlášení** (`/login`) — volitelné, jen když je nastaven `AUTOGENBOOK_UI_PASSWORD` (in-memory session, cookie 12 h). Bez hesla = UI otevřené.
2. **Dashboard** — mřížka projektů (název, id, status běhu, čas změny), tlačítko „+ Nový projekt".
3. **Nový projekt** — formulář: název, jazyk materiálů (CS/EN), výchozí osnova.
4. **Detail projektu — 4 záložky** (`renderProjectTabs`):
   - `1 · Osnova` — textarea se specifikací (input TXT) + uložení.
   - `2 · Materiály` — upload KB (multipart, drag & drop) + seznam souborů (mazání).
   - `3 · Generování` — konfigurace běhu + tlačítko „Spustit generování".
   - `4 · Výstup` — seznam vygenerovaných souborů + náhled + „📄 Běhový log".
5. **Živé okno běhu** — zobrazí se po spuštění (místo záložky Generování): live log + tlačítka Pozastavit / Zastavit.

### User flow (od vstupu po výstup)
```
Dashboard
  → „+ Nový projekt" (název + jazyk + osnova)
  → detail projektu
     1) Osnova  → uložit text specifikace
     2) Materiály → nahrát soubory do KB (drag & drop)
     3) Generování → nastavit model/parametry → „Spustit generování"
        → live log (SSE) + Pozastavit / Zastavit
     4) Výstup → procházet/otevřít vygenerované soubory, „Běhový log"
```

---

## 3. Vstupy a konfigurace, které UI zvládá

### Vstupy
- **Osnova (spec)**: volný text (Markdown-ish TXT) v textare — je to input specifikace pro AutoGenBook.
- **Znalostní báze (materiály)**: přes multipart upload **libovolné soubory**; CLI dál ingeruje PDF/DOCX/MD/TXT/PPTX atd. Podporován **drag & drop** i výběr souboru, víc souborů najednou.
- **Autentizace**: sdílené heslo (env) je volitelné.

### Parametry generování nastavitelné v UI (záložka *Generování*)
| Parametr | UI ovládání | CLI za ním |
|---|---|---|
| Model | textové pole | `AUTOGENBOOK_LLM_MODEL` |
| Web RAG (vyhledávání) | checkbox | `--enable-web-rag` |
| Audit knihy | select (off/warn/strict) | `--audit-book --audit-book-mode …` |
| Generovat PDF | checkbox (default on) | `--no-pdf` (inverzně) |
| Export TeX/PDF (pandoc) | checkbox | `--export-tex` |

**Uživatel NEMŮŽE v UI nastavit** (jen CLI/env): `--mode` (v UI vždy `book`), všechny parametery proposal/reviewer/presentation, TTS, `--max-iters`, `.docx`, `--resume`, atd.

---

## 4. Funkcionalita generování a stromu

### Strom kapitol/podkapitol — SOUČASNÝ STAV
- **UI zatím NEráží interaktivní strom kapitol.** Záložka *Výstup* zobrazuje vygenerované soubory jako **plochý klikací seznam** `.md` souborů (rekurzivně z `output/`) a otevírá náhled; není editor/uželové ovládání stromu.
- Skutečná struktura knihy existuje na disku jako:
  - `output/book_structure.json` (strom kapitol/podkapitol),
  - `output/structure_graph.json`,
  - `output/sections/<1-1-1>.md`, … (každá sekce jako soubor, číslování odpovídá hloubce stromu),
  - `output/section_reviews/…`, `agent_logs/…`.
- **Interaktivní zobrazení/úpravu stromu, per-chapter/per-node generování = plánované rozšíření, zatím NEimplementováno.**

### Akce spustitelné z UI
- **Celý běh**: „▶ Spustit generování" (mode `book`; celá kniha od osnovy po výstup).
- **Pozastavit / Pokračovat** (⏸/▶) — SIGSTOP/SIGCONT na procesní skupinu.
- **Zastavit (zrušit** celé generování**)** (⏹) — SIGTERM → SIGKILL (eskalace).
- **Náhled výstupu** + **„📄 Běhový log”**.
- **Editovatelný náhled uzlu**: v náhledu sekce (strom) tlačítko **✏️ Upravit** přepne na textarea; **💾 Uložit** zapíše obsah do `sections/<uzel>.md`, archivuje předchozí verzi (historie) a označí uzel jako ručně upravený (✏️) — chráněný proti hromadnému přepisu. Endpoint `PUT /api/projects/{pid}/output/section`.
- **Úvod kapitoly z textů podkapitol**: v modálu pro jeden uzel (jen když má uzel potomky) je zaškrtávátko **„Zahrnout do kontextu texty podkapitol”**. Při single-node běhu se obsah podkapitol vloží do kontextu (`_collect_child_texts`) a do vyžádaných pravidel se přidá pokyn začít „V této kapitole se seznámíme s …”.
- **Výstupní formát v záložce Generování**: výběr **Markdown (doporučeno)** / **LaTeX**. Markdown = `.md` s číselnými odkazy + oddíl „Literatura” (žádné surové `\cite`, žádné PDF). LaTeX = `.tex` + reference; PDF jen při zaškrtnutí „Generovat i PDF”. Mapuje se na `--export-tex` + `--no-pdf`/PDF v `_build_argv`.

---

## 5. Ukázka datového modelu / kódu

### 5.1 `project.json` (metadata projektu)
```json
{
  "id": "pv240-marketing-4633",
  "name": "PV240 - Marketing",
  "language": "en",
  "created": "2026-09-06T09:31:25+00:00",
  "updated": "2026-09-06T09:31:53+00:00",
  "spec": "Název: …\nObsah: …\nKapitoly:\n## KAPITOLA 1: ÚVOD\n…"
}
```

### 5.2 `book_structure.json` (strom knihy — generovaný CLI)
```json
{
  "title": "Marketing pro Service Designery: …",
  "summary": "Komplexní úvod … spolutvorby hodnoty …",
  "n_pages": 240.0,
  "target_readers": "Budoucí Service Designery …",
  "max_depth": 5,
  "childs": [
    {
      "title": "Úvod do marketingu služeb a Service-Dominant Logic",
      "summary": "Kapitola introdukuje …",
      "childs": [ { "title": "…", "childs": [] } ]
    }
  ]
}
```

### 5.3 Konfigurace běhu (payload do `/api/projects/{pid}/run`)
```json
{
  "mode": "book",
  "model": "qwen3.5",
  "enable_web_rag": false,
  "audit_mode": "warn",
  "pdf": true,
  "export_tex": false
}
```

### 5.4 Klíčová komponenta — runner (zkráceně, `webui/runner.py`)
```python
proc = subprocess.Popen(argv, cwd=REPO_ROOT, env=env, stdout=logf,
                        stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                        **({"start_new_session": True} if os.name == "posix" else {}))
# pause = os.killpg(pgid, SIGSTOP) | resume = SIGCONT
# cancel = SIGCONT + SIGTERM, po 3 s eskalace na SIGKILL
```

### 5.5 Hlavní REST API
```
GET  /api/config                      # provider, model, je klíč, auth
GET/POST /api/projects                # list / create
GET/PUT /api/projects/{pid}/spec      # číst / uložit osnovu
GET/POST/DELETE /api/projects/{pid}/kb[/..]  # materiály (list/upload/delete)
POST /api/projects/{pid}/run          # spustit generování
POST /api/projects/{pid}/cancel | /pause | /resume
GET  /api/projects/{pid}/status
GET  /api/projects/{pid}/events       # SSE (live log + status)
GET  /api/projects/{pid}/log          # celý běhový log
GET  /api/projects/{pid}/output[/file|/download]  # výstup
GET/POST /login | GET /logout         # auth (pokud je heslo)
```

---

## 6. Zavedené rozšíření & nasazení (kontext pro konsultaci)

- **Provider:** e-INFRA (OpenAI-kompatibilní), override modelu přes `AUTOGENBOOK_LLM_MODEL` (opravené tvrdě zadané OpenRouter modely).
- **UI provozní funkce:** opravený render, KB list po přepnutí záložky, reálný drag & drop, okno běhu po spuštění, Pozastavit/Zastavit, zobrazení běhového logu.
- **Autentizace:** volitelné sdílené heslo (session cookie, HttpOnly/SameSite).
- **Nasazení na e-INFRA (Rancher/K8s, namespace `walletzky-ns`):** image `docker.io/wallet007/autogenbook:latest`, non-root uživatel (UID/GID 2000), `securityContext` kompatibilní s Pod Security `restricted` (drop ALL, runAsNonRoot, seccomp RuntimeDefault, `fsGroup: 2000`), PVC pro `/app/projects`, ingress s TLS. Manifest v `deploy/einfra.yaml`, návod v `docs/DEPLOY_EINFRA.md`.

---

## 7. Známá omezení / směry rozšíření

- **Žádný interaktivní strom kapitol** v UI (jen plochý seznam souborů + náhled).
- **Žádné per-chapter / per-node generování** (jen celý běh knihy).
- **Jediný mód v UI = `book`** (paper/presentation/proposal/reviewer jen CLI).
- **1 replika** (běhy jsou subprocesy v paměti; restart podu přeruší probíhající běh).
- Žádná DB, vše souborově (pro malý počet projektů OK, pro škálování bude potřeba rethink).
- Plánované sloty: **Podcast** a **Workshop** na kartách kapitol (zatím placeholdery pro budoucí generování podcast/workshop).
