# 1xops command line in a container. Build context: packages/python
#   docker run --rm -v "$PWD:/work" ghcr.io/nnthanh101/1xops config --scope team --connectors aws
FROM python:3.14-slim
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . && rm -rf /src
RUN useradd --create-home ops
USER ops
WORKDIR /work
ENTRYPOINT ["1xops"]
CMD ["--help"]
