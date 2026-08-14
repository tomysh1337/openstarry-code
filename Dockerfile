# syntax=docker/dockerfile:1.6
#
# S20 — OpenStarry Code container image.
#
# Safety contract:
#   * Inside the container the gateway binds to 0.0.0.0 because the Docker
#     network namespace needs a wildcard bind for `-p host:container`
#     publishing to work. The defense-in-depth lives at the HOST-SIDE `-p`
#     binding: the documented default `docker run -p 127.0.0.1:18791:18791`
#     keeps the gateway reachable only from the host's loopback.
#   * Network exposure is opt-in via `-p 0.0.0.0:18791:18791` — see the
#     "Network exposure" section in README.md for the warning.
#   * The S19 boot WARNING (`gateway.bind.public`) fires on every container
#     start because the in-container bind is a wildcard by design — that is
#     the intended signal to operators running the image.

FROM --platform=$BUILDPLATFORM node:22.12.0-bookworm-slim AS webui-builder

ARG OPENSTARRY_CODE_FORBID_PERSONAL_BGM=0

WORKDIR /build/openstarry-code-webui

# Cache dependency installation independently from application source. Vite
# writes the verified bundle to /build/src/.../static/dist; the final Python
# stage copies only that artifact, never Node.js or node_modules.
COPY openstarry-code-webui/package.json openstarry-code-webui/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm,sharing=locked npm ci
COPY openstarry-code-webui/ ./
RUN npm run build:artifact \
    && if [ "${OPENSTARRY_CODE_FORBID_PERSONAL_BGM}" = "1" ]; then \
        npm run verify:release-dist; \
    fi


FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# --- safety default ---------------------------------------------------------
# OPENSTARRY_CODE_LISTEN=0.0.0.0 is required inside the container so the gateway can
# be reached via Docker port publishing. Do NOT flip this to 127.0.0.1 —
# that would make the container reachable only from itself. The safe
# default for HOST-side exposure lives at `docker run -p`, not here.
ENV OPENSTARRY_CODE_LISTEN=0.0.0.0 \
    OPENSTARRY_CODE_GATEWAY_PORT=18791

WORKDIR /app

# Build tooling for optional C-extension deps (jieba FTS5 tokenizer, etc.).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy minimal build context — everything else is in .dockerignore.
COPY pyproject.toml README.md README.release.md ./
COPY hatch_build.py ./
COPY scripts/verify_webui_artifact.py ./scripts/verify_webui_artifact.py
COPY openstarry-code-webui/ ./openstarry-code-webui/
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY --from=webui-builder \
    /build/src/openstarry_code/gateway/static/dist/ \
    ./src/openstarry_code/gateway/static/dist/

RUN python - <<'PY'
from pathlib import Path

root = Path("src/openstarry_code/squilla_router/models")
required = [
    root / "v4.2_phase3_inference" / "lgbm_main.bin",
    root / "v4.2_phase3_inference" / "router.runtime.yaml",
    root / "v4.2_phase3_inference" / "mlp" / "model.onnx",
    root / "v4.2_phase3_inference" / "features" / "tfidf.pkl",
    root / "v4.2_phase3_inference" / "bge_onnx" / "model.onnx",
]
pointer = "version https://git-lfs.github.com/spec/v1"
missing = [str(path) for path in required if not path.is_file()]
pointers = []
for path in required:
    if not path.is_file():
        continue
    first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    if first_line.strip() == pointer:
        pointers.append(str(path))
if missing or pointers:
    raise SystemExit(
        "Squilla router v4 model assets are unavailable in this build context. "
        'Run `git lfs pull --include="src/openstarry_code/squilla_router/models/**"` '
        f"before docker build. Missing={missing} Pointers={pointers}"
    )
PY

RUN pip install ".[recommended]" \
    && rm -rf hatch_build.py scripts openstarry-code-webui

# Persisted state root. The gateway writes config, state, logs, and the
# workspace under OPENSTARRY_CODE_STATE_DIR — mounting a volume here (see
# compose.yaml) is what makes a container's setup survive a recreate.
ENV OPENSTARRY_CODE_STATE_DIR=/var/lib/openstarry-code

# Run as a non-root user — avoids shipping root creds into production.
# The state root is created and owned by that user before the USER drop,
# so a freshly initialized volume inherits writable, non-root ownership.
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin openstarry-code \
    && mkdir -p /var/lib/openstarry-code \
    && chown -R openstarry-code:openstarry-code /app /var/lib/openstarry-code
USER openstarry-code

EXPOSE 18791

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail --silent --show-error http://127.0.0.1:18791/healthz || exit 1

ENTRYPOINT ["openstarry-code"]
CMD ["gateway", "run"]
