# Clew Slack bot — persistent container (Railway/Fly/Render).
# Serves Socket Mode + OAuth + the board API on $PORT via app_oauth.py.
# Mount a volume at /app/data (SQLite DB + persisted OAuth installs);
# set CLEW_DB_PATH=/app/data/clew.db.
FROM python:3.12-slim

# ca-certificates for TLS to Slack/Anthropic/grant APIs
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

# The agent CLI refuses to run as root; entrypoint drops privileges after
# fixing volume ownership.
RUN useradd -m -u 1000 clew && mkdir -p /app/data && chown -R clew:clew /app

ENV PYTHONUNBUFFERED=1 HOME=/home/clew

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
