FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/src
ENV APP_USER=appuser
ENV TZ=Europe/Madrid

RUN groupadd --system "$APP_USER" && \
    useradd --system --gid "$APP_USER" --create-home --home-dir "/home/$APP_USER" "$APP_USER" && \
    apt-get update && \
    apt-get install --no-install-recommends --yes ca-certificates tzdata && \
    ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime && \
    echo "$TZ" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir uv

WORKDIR $APP_HOME

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev --extra bedrock && \
    chown -R "$APP_USER:$APP_USER" "$APP_HOME"

ENV PATH="$APP_HOME/.venv/bin:$PATH"

USER $APP_USER

ENTRYPOINT ["python", "-m", "app.cli"]
CMD ["--help"]
