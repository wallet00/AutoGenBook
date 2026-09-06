# AutoGenBook — Docker image
# Runs the AutoGenBook CLI inside a container (Linux) on any host (Windows/macOS/Linux).
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifest first for better layer caching.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the whole project.
COPY . .

# Workdirs bind-mounted from the host (see docker-compose.yml).
RUN mkdir -p /app/input /app/output

# Non-interactive defaults are safe for containerized runs.
ENV AUTOGENBOOK_NONINTERACTIVE=1 \
    AUTOGENBOOK_ASSUME_YES=1

ENTRYPOINT ["python", "main.py"]
