# AutoGenBook — Docker image
# Defaultně spouští webové UI (uvicorn, port 8080). CLI je volatelné explicitně
# (docker run IMAGE main.py --mode ...). Běží na libovolném hostu (Windows/macOS/Linux).
FROM python:3.12-slim

# Non-interactive: the CLI uses prompts; we force non-interactive mode via env in run.
ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# System packages: pandoc (Markdown->TeX/PDF) + LuaLaTeX (PDF output) + build tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
        pandoc \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-luatex \
        build-essential \
        gcc \
        g++ \
        git \
        passwd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifest first for better layer caching.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the whole project.
COPY . .

# Workdirs bind-mounted from the host (see docker-compose.yml).
RUN mkdir -p /app/input /app/output /app/projects

# ── Non-root user (Pod Security 'restricted' compliant) ────────────
# UID/GID 2000 = povolena „restricted" skupina (k8s.io), pouziva se take jako
# fsGroup pro PVC, takze pod muze do /app/projects zapisovat.
# Samotný /app dáme uživateli, aby si aplikace mohla zapisovat, kdyby potřebovala.
RUN groupadd --gid 2000 appuser \
    && useradd --uid 2000 --gid appuser --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser
ENV HOME=/home/appuser

# Non-interactive defaults are safe for containerized runs.
ENV AUTOGENBOOK_NONINTERACTIVE=1 \
    AUTOGENBOOK_ASSUME_YES=1

# ── Výchozí start = Web UI (uvicorn) ──────────────────────────────
# Image při defaultním spuštění (i bez přepisu command, např. workload z Rancher
# formuláře) nastartuje webový server, nikoli CLI s výchozími argumenty, které by
# spadlo na chybějícím /app/book_input.txt a nezapisovatelném /app/out.
#
# CLI zůstává dostupné explicitně např.:
#   docker run IMAGE main.py --mode book --input /app/input/book_input.txt --out-dir /app/projects/out
ENTRYPOINT ["python"]
CMD ["-m", "uvicorn", "webui.server:app", "--host", "0.0.0.0", "--port", "8080"]
