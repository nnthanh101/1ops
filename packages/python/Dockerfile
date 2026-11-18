# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e
## ==========================================================
## nnthanh101/1xops and ghcr.io/nnthanh101/1xops - the 1xops command line in a container
## Base: nnthanh101/runbooks:prod (Wolfi, Python 3.14 = AWS Lambda python3.14, non-root user os, dumb-init),
##   pinned by its multi-arch index digest, so 1xops is patched with the same image the platform already runs.
## Supply chain: uv from the Wolfi package inside the digest-pinned Wolfi base (the one runbooks is built from);
##   dependencies installed exactly as uv.lock pins them (versions and hashes); no git, no shell tools added.
## Build context: packages/python
##   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" nnthanh101/1xops config --scope team --dir /work --connectors aws
## ==========================================================

# Bump both together with the runbooks image: docker buildx imagetools inspect <image> | grep ^Digest
ARG BASE_IMAGE=docker.io/nnthanh101/runbooks:prod@sha256:f4c0bd1d0128665bf52dbaaf3a7e9cbbc52042d4cfab8ba63ecef8f9d774852f
ARG BUILD_IMAGE=cgr.dev/chainguard/wolfi-base:latest@sha256:238642d42c5613936474d00b900c4e65fb6f637d8991c913403ff09a09cf43a3
# Same uv as the runbooks image (adlc-framework/.devcontainer/versions.env)
ARG UV_VERSION=0.12.18

## Stage: build - a virtual environment in /opt/1xops, from uv.lock only
FROM ${BUILD_IMAGE} AS build
ARG UV_VERSION
RUN apk add --no-cache python-3.14 "uv~${UV_VERSION}" && \
    uv --version | grep -q "^uv ${UV_VERSION}[ +]"
WORKDIR /src
COPY pyproject.toml uv.lock README.md hatch_build.py ./
# The one LICENSE and NOTICE at the repository root (build with --build-context repo=.)
COPY --from=repo LICENSE NOTICE ./
COPY --from=repo templates/settings ./templates/settings
COPY src ./src
ENV UV_PROJECT_ENVIRONMENT=/opt/1xops UV_PYTHON=/usr/bin/python3.14 UV_PYTHON_DOWNLOADS=never UV_COMPILE_BYTECODE=1
RUN uv sync --locked --no-dev --no-editable && /opt/1xops/bin/1xops --version

## Stage: runtime - what customers pull
FROM ${BASE_IMAGE}
ARG VERSION=dev
LABEL description="1xops command line" \
      maintainer="OceanSoft.io" \
      org.opencontainers.image.title="1xops" \
      org.opencontainers.image.authors="OceanSoft.io" \
      org.opencontainers.image.description="Cloud & AI Operations: governed setup for organisations, teams, projects and people" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.vendor="OceanSoft.io" \
      org.opencontainers.image.url="https://www.oceansoft.io" \
      org.opencontainers.image.source="https://github.com/nnthanh101/1xops" \
      org.opencontainers.image.licenses="Apache-2.0"
COPY --from=build /opt/1xops /opt/1xops
ENV PATH="/opt/1xops/bin:${PATH}" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER root
RUN install -d -o os -g os /work
USER os
WORKDIR /work
# dumb-init forwards Ctrl-C and stop signals to 1xops. No HEALTHCHECK: a command that runs once and exits.
ENTRYPOINT ["dumb-init", "--", "1xops"]
CMD ["--help"]
