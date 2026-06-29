FROM ghcr.io/astral-sh/uv:alpine

RUN mkdir app
WORKDIR /app

COPY src src
COPY static static
COPY pyproject.toml pyproject.toml
COPY README.md README.md
RUN uv sync -v --no-dev --compile-bytecode --no-editable

CMD ["./.venv/bin/python3", "-m", "dutch_trialsite_test_app"]
EXPOSE 80
