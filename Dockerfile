# PM-Bench reproducible evaluation environment
#
# Build:
#   docker build -t pm-bench .
#
# Run (offline demo — no keys needed):
#   docker run --rm pm-bench python demo.py --no-color
#
# Run the benchmark with your API key:
#   docker run --rm \
#       -e ANTHROPIC_API_KEY \
#       -v $(pwd)/results:/app/results \
#       pm-bench python run.py --superhuman-only
#
# Mock end-to-end pipeline (useful in CI):
#   docker run --rm pm-bench python run.py --provider mock --superhuman-only
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy project metadata first so dependency installs cache independently
# of benchmark data churn.
COPY pyproject.toml README.md LICENSE VERSION ./

# Install all optional extras so both anthropic and openai flows work out
# of the box. Users who want a leaner image can pin just one extra.
COPY run.py demo.py ./
COPY scenarios ./scenarios
COPY fixtures ./fixtures
COPY workspace ./workspace
COPY tools ./tools
COPY tests ./tests

RUN pip install -e ".[all]"

# The pm-bench CLI is registered as a project script; expose it as the
# default entrypoint so `docker run pm-bench --help` Just Works.
ENTRYPOINT ["pm-bench"]
CMD ["--help"]

# Self-check: the offline demo doesn't touch the network and exits 0 when
# the scenarios / fixtures are intact. This catches broken images fast.
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=1 \
    CMD python demo.py --no-color > /dev/null || exit 1
