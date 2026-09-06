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
