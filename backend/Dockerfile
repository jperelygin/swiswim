FROM python:3.12.6-slim-bookworm

# Python env
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/var/cache/pypoetry \
    POETRY_VERSION=1.8.3

# System deps + Poetry
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Poetry binary
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-root

RUN apt-get update && apt-get install -y postgresql-client

COPY . /app

ENV PYTHONPATH=/app/src

# Turn off if no real updates in DB (1 - on)
ENV ALEMBIC_MAKE_NEW_REVISION="0"
ENV ALEMBIC_REVISION_MESSAGE="AUTO_REVISION"
# Dev mode with automatic migrations (1 - on)
ENV ALEMBIC_RUN_MIGRATIONS_AUTO="1"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]