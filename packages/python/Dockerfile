# 1ops command line in a container. Build context: packages/python
#   docker run --rm -v "$PWD:/work" nnthanh101/1ops config --scope team --connectors aws
FROM python:3.15-slim
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY src ./src
RUN pip install --no-cache-dir . && rm -rf /src
RUN useradd --create-home ops
USER ops
WORKDIR /work
ENTRYPOINT ["1ops"]
CMD ["--help"]
