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
   list uzly mají tlačítko "⚡ Generovat tento uzel" → `mode: "single_node"` + `node_id`,
   který spustí `main.py --single-node <key> --resume --no-md --no-tex --no-pdf`
   (načte stávající strukturu a přepíše jen jednu sekci; ve `book_builder.generate_contents`
   parametr `only_key`). Náhled sekce + "Zkopírovat jako podklad pro NotebookLM".

### Nové API

- `POST /api/projects/<id>/analyze-spec`
- `PUT /api/projects/<id>/analysis`
- `GET /api/projects/<id>/structure`

### Nové CLI přepínače

- `--outline-only`
- `--single-node <key>` (node key např. `1-2-1`, tečka se normalizuje na pomlčku)
