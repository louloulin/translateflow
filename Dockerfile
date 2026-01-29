
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV RUNNING_IN_DOCKER=true
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*
    
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml ./
COPY uv.lock ./ 
RUN uv sync --frozen
COPY ainiee_cli.py ./
COPY ModuleFolders/ ./ModuleFolders/
COPY Resource/ ./Resource/
COPY PluginScripts/ ./PluginScripts/
COPY StevExtraction/ ./StevExtraction/
COPY I18N/ ./I18N/
EXPOSE 8000
ENTRYPOINT ["uv", "run", "ainiee"]