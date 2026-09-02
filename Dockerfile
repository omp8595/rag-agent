# Life Sciences Enterprise Context Layer — prototype demo image.
# PROTOTYPE VALIDATED — NOT PRODUCTION READY. See
# docs/production_reference_architecture.md for what a production image
# would additionally need (this one is deliberately minimal).

FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Dependency layer first, so an application-code change doesn't bust the
# (slow) dependency install cache.
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY context_layer ./context_layer
COPY agents ./agents
COPY data ./data

# Fixtures are committed for convenience, but regenerate them at build
# time too, so the image is reproducible from source even if the
# committed JSON ever drifts.
RUN python -m context_layer.data.synthetic_gen

# Non-root: the app never needs to write anything but its own audit log,
# which it writes to /app (owned by this user) — see
# context_layer/policy/audit.py.
RUN useradd --create-home --uid 1000 contextlayer && chown -R contextlayer:contextlayer /app
USER contextlayer

EXPOSE 8080
ENV APP_ENV=demo \
    HOST=0.0.0.0 \
    PORT=8080

CMD ["python", "-m", "context_layer.api.http_server"]
