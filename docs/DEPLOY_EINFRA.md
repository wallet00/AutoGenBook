# Nasazení AutoGenBook UI na e-INFRA (Rancher / Kubernetes)

Tento návod nasadí webové UI (FastAPI + uvicorn) jako **jeden Kubernetes pod** do
clusteru e-INFRA spravovaného přes **Rancher**. Běhy knihy poběží uvnitř podu
jako subprocesy; výstup se ukládá na **persistentní disk (PVC)**, takže data
přežijí restart podu.

> **Replikace = 1.** Běhy jsou dlouhoběžící subprocesy v paměti podu; horizontální
> škálování nedává smysl (runner není sdílený mezi replikami). Použij 1 repliku
> a PVC typu RWO. Pro pozdější paralelní běhy řekni, dořešíme to později.

---

## 0. Předpoklady

- Docker image se staví na **Linux** (image je `linux/amd64`). Na Windows notebooku
  používáš Docker Desktop (build proběhne uvnitř WSL) — pro push na registry to
  nevadí.
- Máš přístup k **registry**, ze kterého dokáže e-INFRA cluster pullovat
  (např. veřejný Docker Hub, nebo **GitLab Container Registry**). Níže používám
  `<REGISTRY>/autogenbook` jako placeholder — nahraď svým skutečným názvem image.

  **Používáš-li GitLab (registry.gitlab.fi.muni.cz):** image path je většinou
  `registry.gitlab.fi.muni.cz/<skupina>/<projekt>:v0.1` — přesnou adresu najdeš
  v projektu v sekci **Deploy → Container Registry** (Packages & Registries).
- V Rancheru máš **namespace `walletzky-ns`** (všechny objekty níže jej používají).
- Hostname do Ingressu si nastavuješ sám.

---

## 1. Vytvoření image a push do registry

Nejdřív se ujisti, že máš aktuální kód:

```powershell
cd C:\AutoGenBook\AutoGenBook
git pull
```

Postav a nahraj image (tag verze je vhodný; `latest` pro ladění):

```powershell
docker build -t <REGISTRY>/autogenbook:latest .
docker push <REGISTRY>/autogenbook:latest
```

> **`.dockerignore` už je v repozitáři** → `.env`, `projects/`, `input/`, `output/`
> a `tests/` se do image nedostanou (tajemství a data zůstanou jen v Secret/PVC).

Ověř, že image neobsahuje tajemství:

```powershell
docker run --rm --entrypoint ls <REGISTRY>/autogenbook:latest /app
# v /app musí být vidět jen zdrojový kód, NE .env ani projects/
```

---

## 2. Co nasadit (Kubernetes objekty)

Jednotlivé objekty napiš do souborů (např. `deploy/einfra.yaml`) a aplikuj
v Rancheru nebo `kubectl apply -f`.

### 2.1 Secret — přihlašovací údaje k LLM

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: autogenbook-env
  namespace: walletzky-ns
type: Opaque
stringData:
  AUTOGENBOOK_LLM_BASE_URL: "https://llm.ai.e-infra.cz/v1"
  AUTOGENBOOK_LLM_API_KEY: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # ← tvůj klíč
  AUTOGENBOOK_LLM_MODEL: "qwen3.5"
  AUTOGENBOOK_NONINTERACTIVE: "1"
  AUTOGENBOOK_ASSUME_YES: "1"
  PYTHONUTF8: "1"
  # heslo UI — kdo ho zná, dostane se dovnitř (jinak nech prázdné → UI bez hesla)
  AUTOGENBOOK_UI_PASSWORD: "zvol-silne-heslo"
```

> Runner i CLI čtou tyto proměnné z `os.environ`, takže je subproces běhu zdědí
> přesně tak jako lokální `.env`. **Žádný `.env` soubor v image není potřeba.**

### 2.2 PersistentVolumeClaim — kam se ukládají projekty

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: autogenbook-projects
  namespace: walletzky-ns
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 10Gi
```

(Uprav velikost podle potřeby. Připojí se na `/app/projects`.)

### 2.3 Deployment

**Důležité:** Dockerfile má `ENTRYPOINT ["python", "main.py"]` — v K8s ho musíš
přepsat, aby se spustilo webové UI, ne CLI. Nastav `command` na spuštění uvicornu:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autogenbook-ui
  namespace: walletzky-ns
spec:
  replicas: 1
  selector:
    matchLabels:
      app: autogenbook
  template:
    metadata:
      labels:
        app: autogenbook
    spec:
      containers:
        - name: ui
          image: <REGISTRY>/autogenbook:latest
          # Přepíše ENTRYPOINT z Dockerfile (python main.py) → spustí UI server
          command: ["python", "-m", "uvicorn", "webui.server:app", "--host", "0.0.0.0", "--port", "8080"]
          ports:
            - containerPort: 8080
          envFrom:
            - secretRef:
                name: autogenbook-env
          volumeMounts:
            - name: projects
              mountPath: /app/projects
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
          readinessProbe:
            httpGet:
              path: /
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
      volumes:
        - name: projects
          persistentVolumeClaim:
            claimName: autogenbook-projects
```

### 2.4 Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: autogenbook-ui
  namespace: walletzky-ns
spec:
  selector:
    app: autogenbook
  ports:
    - port: 8080
      targetPort: 8080
  type: ClusterIP
```

### 2.5 Ingress (přístup zvenčí)

e-INFRA obvykle má ingress kontrolér s automatickým TLS. Uprav hostname podle
toho, jaké DNS ti e-INFRA přidělí (stačí koupit/nakonfigurovat přes Rancher —
Ingress → přidat hostname). Příklady:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: autogenbook-ui
  namespace: walletzky-ns
  annotations:
    # e-INFRA typicky automaticky vystaví TLS certifikát
    cert-manager.io/cluster-issuer: letsencrypt
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - autogenbook.<tvoje-domena>.cz
      secretName: autogenbook-tls
  rules:
    - host: autogenbook.<tvoje-domena>.cz
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: autogenbook-ui
                port:
                  number: 8080
```

Pokud TLS nechceš řešit, vynech blok `tls` — e-INFRA ingress může nasadit i
`http` (nedoporučuji pro klíče).

---

## 3. Jak to aplikovat v Rancheru

1. V Rancheru otevři svůj **cluster → project/namespace** (vytvoř `autogenbook`).
2. **Import / Create from file** → vlož obsah z `deploy/einfra.yaml`
   (Secret, PVC, Deployment, Service, Ingress).
3. Počkej, až Deployment naběhne (`Pod` v `Running`), **Ready 1/1**.
4. Otevři hostname z Ingressu → **uvidíš dashboard AutoGenBook UI**.

Pokud raději `kubectl`:

```bash
kubectl apply -n walletzky-ns -f deploy/einfra.yaml
kubectl -n walletzky-ns get pods,svc,ing,pvc
kubectl -n walletzky-ns logs deploy/autogenbook-ui
```

---

## 4. Ověření po nasazení

1. Otevři UI → založ testovací projekt.
2. Nahraj knowledgbase / osnovu → **Spustit generování**.
3. Sleduj okno „Průběh běhu" (živý log + Pozastavit/Zastavit).
4. V pohledu **Výstup** zkontroluj vygenerované kapitoly / `📄 Běhový log`.
5. Restartni pod (`kubectl rollout restart deploy/autogenbook-ui`) a ověř,
   že projekty zůstaly (data jsou na PVC).

---

## 5. Bezpečnostní poznámky (před zveřejněním)

- UI má **jednoduchou autentizaci sdíleným heslem**: pokud je v Seed‑u nastaven
  `AUTOGENBOOK_UI_PASSWORD`, před vstupem se objeví přihlašovací stránka
  (session cookie na 12 h, kdo zná heslo, projde; jinak nic nevidí).
  Heslo drž v **Secret** (výše), nikde jinde.
- **Přes HTTPS vzdý** (Ingress s TLS) — session cookie je `HttpOnly` + `SameSite=Lax`
  a s `secure` (nastaví se automaticky, když je schéma `https`).
- Klíč k LLM je v **Secret** (ne v image ani v kódu).
- PVC zálohuj (export projektu = JSON ve `projects/<id>/`).
- Pro ještě silnější ochranu (než „jen heslo") můžeš později přidat IP restrikci
  na Ingressu nebo OIDC/Keycloak.

---

## 6. Co NEfunguje / omezení v této verzi

- **1 replika**, běhy běží v paměti podu. Pokud se pod restartuje (rollout,
  uzel, OOM), běh se přeruší — data na PVC zůstanou, ale probíhající generace se
  ztratí.
- Subproces nemá vlastní persistentní „queue". Pro hodně dlouhé/paralelní běhy
  bude potřeba předělat runner na job-queue. (Zatím nepotřebujeme.)
- Ingress/load-balancer časové limity: livelog jede přes **SSE** (bez keep-alive
  blokace), takže dlouhé běhy obvykle limity nezlomí; pokud narazíš na 504,
  přidáme ping/keep-alive do SSE.

---

## Slovníček placeholderů

| Placeholder | Význam |
|---|---|
| `<REGISTRY>/autogenbook` | plné jméno image v registry (např. `docker.io/me/autogenbook`) |
| `autogenbook.<tvoje-domena>.cz` | veřejná adresa UI |

Pokud nevíš, jaké registry nebo DNS ti e-INFRA nabízí, pošli mi, co ti dal
správce projektu (prompt/namespace, registry adresu, ingress hostname) — krok 1–2
doplním přesně na tvůj setup.
