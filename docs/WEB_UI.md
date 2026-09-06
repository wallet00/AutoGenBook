# AutoGenBook Web UI (Course Material Studio)

Lokální webové rozhraní pro hlavní pracovní tok AutoGenBook: ze stávajících materiálů +
nové osnovy + dalších zdrojů vygenerovat základní výukový dokument po kapitolách
(z nichž se dál mají stavět podcasty a workshopy pro flipped classroom).

## Spuštění (Docker)

```bash
docker compose up -d ui
# otevři http://localhost:8082
```

- Služba `ui` spouští FastAPI server (`webui.server:app`) uvnitř stejného obrazu jako CLI.
  Hostitelský port **8082** je mapovaný na vnitřní 8080 (lze změnit v `docker-compose.yml`).
- Projekty se ukládají do `./projects/<id>/` (bind-mount) a přežijí restart kontejneru.
- Poskytovatel/model se čtou z `.env` (e-INFRA: `AUTOGENBOOK_LLM_BASE_URL`,
  `AUTOGENBOOK_LLM_API_KEY`, `AUTOGENBOOK_LLM_MODEL`).

## Funkce (MVP)

| Obrazovka | Popis |
|---|---|
| Dashboard | Seznam projektů (předmětů) + vytvoření nového |
| Projekt · Osnova | Raw editor `book_input.txt` (generuje se spec) |
| Projekt · Materiály | Upload stávajících materiálů → znalostní báze `--kb-dir` |
| Projekt · Generování | Model, web RAG, audit, PDF, export TeX |
| Projekt · Výstup | Strom kapitol + náhled + (per-kapitola) soubory |

Jazyk UI se přepíná (cs/en) — materiály/dokumenty zůstávají podle osnovy.

## API přehled

- `GET/POST /api/projects`, `GET/PUT /api/projects/<id>` (+`/spec`)
- `GET/POST/DELETE /api/projects/<id>/kb` (upload materiálů)
- `POST /api/projects/<id>/run`, `POST .../cancel`, `GET .../status`, `GET .../events` (SSE live log)
- `GET /api/projects/<id>/output`, `GET .../output/file?path=…`
- `GET /api/config`

Běh volá `main.py --mode book --input <spec> --out-dir output` (a podle konfigurace
přidá `--kb-dir`, `--enable-web-rag`, `--audit-book`, `--export-tex`).

## Nasazení (budoucí krok)

Pro nasazení na e-INFRA (Rancher/Kubernetes) je obraz samonosný — stačí spustit
`python -m uvicorn webui.server:app --host 0.0.0.0 --port 8080`, expose port 8080
a připojit trvalý volume pro `./projects`. Proměnné (API klíč, model) předat jako
env do Deploymentu/Pod (Secret/ConfigMap), ne jako soubor `.env`.

## Fázové generování (PV240 — rekurzivní prostředí)

UI podporuje dvoufázový tok + generování jednotlivých uzlů:

1. **Analyze spec** — `POST /api/projects/<id>/analyze-spec` nechá LLM (e-INFRA) z osnovy
   a materiálů navrhnout parametry (`suggested_title`, `target_audience`, `tone_of_voice`,
   `output_purpose`, `recommended_depth`) a uloží je do `project.json` (`analysis`).
   Parametry lze upravit a uložit přes `PUT /api/projects/<id>/analysis`.
   Při běhu se předají subprocesu env proměnnou `AUTOGENBOOK_UI_PARAMS` (JSON) a `book_pipeline.py`
   je vloží do osnovy (tvorba struktury) i do atributů grafu (`target_readers`,
   `additional_requirements`, `max_depth`) jako kontext pro psaní sekcí.

2. **Outline only** — `mode: "outline_only"` spustí `main.py --outline-only --use-txt`,
   který vygeneruje pouze `book_structure.json` + `structure_graph.json` (bez psaní sekcí).

3. **Strom + single node** — `GET /api/projects/<id>/structure` vrací hierarchický strom
   z `structure_graph.json` (fallback `book_structure.json`) včetně stavu sekcí
   (`exists`/`size`/`mtime` z `output/sections/<key>.md`). UI renderuje kolapsovatelný strom;
   uzly mají tlačítko "⚡ Generovat tento uzel" (funguje i pro rodičovské uzly → úvod/overview) → `mode: "single_node"` + `node_id`,
   který spustí `main.py --single-node <key> --resume --no-md --no-tex --no-pdf`
   (načte stávající strukturu a přepíše jen jednu sekci; ve `book_builder.generate_contents`
   parametr `only_key`). Náhled sekce + "Zkopírovat jako podklad pro NotebookLM".

#### Single-node modal
Kliknutím na "⚡ Vygenerovat tento uzel" se otevře modal s:
- **Zahrnutí stávajícího textu** (`include_existing`) — předá stávající sekci jako
  `section_draft` (přepis/vylepšení, default vypnuto);
- **Vlastní instrukce** (`custom_prompt`) — vloží se do `additional_requirements` (nejvyšší priorita);
- **Prioritní KB soubory** (`kb_files`) — omezí retrieval pouze na vybrané soubory z `kb/`
  (filtr `include_sources=` v `RetrievalManager.retrieve`).
Parametry se do běhu předají env proměnnou `AUTOGENBOOK_NODE_PARAMS` (JSON).

#### Editor promptů (záložka 5 · Prompty)
- **Projektové prompty** — uloží překryvy do `project.json["prompts"]` (aplikují se na tento projekt);
- **Globální prompty** — uloží do `REPO_ROOT/global_prompts.json` (výchozí šablony pro všechny projekty).
Překryvy se při běhu aplikují: `book_pipeline._apply_prompt_overrides` spojí globální soubor +
projektové (env `AUTOGENBOOK_PROMPT_OVERRIDES`) přes výchozí prompty z `prompts/book/*.md`
před `set_prompt_registry`. Reset vrátí výchozí šablonu.

#### Robustní stav běhu
Globální `window._run` drží stav (`status`, `lines`, `es`) nezávisle na záložce. Záložka
"3 · Generování" při `status == "running"` vždy vykreslí živé okno (live log + Pozastavit/Zastavit),
při návratu se log dosadí ze serveru (`GET .../log`) a znovu připojí SSE (`.../events`);
přežije přepnutí záložek i obnovení stránky (F5).

### Změnový management (Change Management)

**1. Zamykání uzlů 🔒** — každý uzel stromu má ikonu zámku. Atributy `locked` / `manual_override`
se ukládají do `structure_graph.json` (node attrs). Při **hromadném** běhu `generate_contents`
(`only_key is None`) uzly s `locked` nebo `manual_override` **přeskočí** a zachovají svůj obsah.

**2. Režim generování sekce (single-node modal)** — přepínač:
- `full` — Kompletní regenerace (přepíše sekci od nuly);
- `enrich` — Inkorporovat nové zdroje / Doplnit: stávající text se předá jako `section_draft`
  + instrukce nejvyšší priority „Zachovej stavbu…, ale obohať o myšlenky/citace z nově
  přiloženého zdroje“ + filtr KB na vybraný nový soubor (`include_sources`).
Přepíná se v modalu; parametr jde env `AUTOGENBOOK_NODE_PARAMS` → `gen_mode`.

**3. Verzování a archivace** — před každým přepisem sekce (generátorem i obnovením) se předchozí
verze uloží do `output/history/{section_id}_{timestamp}.md`. V náhledu kapitoly: „📜 Historie verzí“
(seznam + „Obnovit“, které archívuje aktuální verzi a uzel označí jako `manual_override` + `locked`)
a „💾 Uložit verzi“ (ruční checkpoint).

Nová rozhraní: `PUT /structure/lock`, `GET /output/history`, `POST /output/history/restore`,
`POST /output/history/snapshot`.

**4. Generování rodičovského uzlu / celé větve** — tlačítko ⚡ nyní funguje i na rodičovských
uzlech (vygeneruje „úvod/přehled kapitoly“ do `sections/<rodič>.md`). Rodičovské uzly mají navíc
tlačítko **🔄 Větev** (`mode: "branch"`), které rekurzivně (pře)generuje uzel I všechny jeho
dceřiné podkapitoly. Při branch běhu se respektují zámky (❗ zamčené uzly se přeskočí). Výsledek
rodičovského obsahu se promítne i do finálního .md dokumentu (rodič vykreslí svůj obsah před
podkapitolami).

**5. Rychlý překlad uzlu 🌐** — tlačítko na uzlu, který už má obsah: pošle stávající text přímo
LLM na překlad (obchází RAG pipeline), zkopíruje do `sections/<uzel>.md`, archívuje předchozí verzi
a uzel označí jako `manual_override` + `locked`. Cílový jazyk se předvyplní z parametrů kurzu
(`analysis.language`).

### Nové API

- `POST /api/projects/<id>/analyze-spec`
- `PUT /api/projects/<id>/analysis`
- `GET /api/projects/<id>/structure`
- `POST /api/projects/<id>/translate-node`  (překlad uzlu 🌐)
- `GET /api/config/tavily` / `PUT /api/config/tavily`  (Tavily API klíč pro Web RAG)

### Web RAG + Tavily

Web vyhledávání (RAG) přes Tavily: **runner** automaticky předá `TAVILY_API_KEY` do CLI podprocesu
a klíč rozlišuje s prioritou **systémová proměnná → `.env` → globální konfigurace** (`global_config.json`,
ukládá se z UI). V záložce **3 · Generování** je pole pro zadání klíče (`tvly-...`) a vedle checkboxu
Web RAG indikátor 🟢 (klíč aktivní) / ⚠️ (klíč chybí – poběží jen lokální KB). Před spuštěním generování
s Web RAG a bez klíče UI zobrazí varování.

### Nové CLI přepínače

- `--outline-only`
- `--single-node <key>` (node key např. `1-2-1`, tečka se normalizuje na pomlčku)
- `--branch-root <key>` (rekurzivně vygenerovat uzel i všechny jeho dceřiné podkapitoly)
