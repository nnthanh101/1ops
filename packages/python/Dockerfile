# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e
## ==========================================================
## nnthanh101/1xops and ghcr.io/nnthanh101/1xops - the 1xops command line in a container
## Base: nnthanh101/runbooks cli (Wolfi, AWS CLI v2, Azure CLI, gh, Python 3.14, non-root user os, tini),
##   pinned by its multi-arch index digest, so 1xops is patched with the same image the platform already runs
##   and its read-only checks run inside, with only the read-only sign-in mounted (README: Docker).
## Supply chain: uv from the Wolfi package inside the digest-pinned Wolfi base (the one runbooks is built from);
##   dependencies installed exactly as uv.lock pins them (versions and hashes); no git, no shell tools added.
## Build context: packages/python
##   docker run --rm -v "$PWD/.env.1xops:/work/.env.1xops:ro" -v "$HOME/.aws/sso:/home/os/.aws/sso:ro" ... nnthanh101/1xops doctor
## ==========================================================

# Bump both together with the runbooks image: docker buildx imagetools inspect <image> | grep ^Digest
# runbooks:cli today has the AWS CLI and gh; 2.12.0-cli adds the Azure CLI (#59): bump the digest when it is published
ARG BASE_IMAGE=docker.io/nnthanh101/runbooks:cli@sha256:9615e573e6ef7bd5d12b23f51ca6ed9551952a368f011637a9b37422988d92d0
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
# ONEXOPS_CONTAINER=1: doctor adds the isolation row and says "on the host" in each sign-in fix
ENV PATH="/opt/1xops/bin:${PATH}" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ONEXOPS_CONTAINER=1
USER root
# ~/.aws belongs to os, so the AWS CLI keeps its cache inside the container while the mounted config and
# sign-in stay read-only; without it Docker creates ~/.aws as root and the AWS CLI cannot start.
RUN install -d -o os -g os /work && install -d -m 0700 -o os -g os /home/os/.aws
USER os
WORKDIR /work
# az (2.12.0-cli on) writes a config folder: its check uses a throwaway one, so the image holds no ~/.azure
RUN 1xops --version && aws --version && gh --version && \
    if command -v az >/dev/null; then AZURE_CONFIG_DIR=/tmp/az-check az version --output none && rm -rf /tmp/az-check; fi
# tini forwards Ctrl-C and stop signals to 1xops. No HEALTHCHECK: a command that runs once and exits.
ENTRYPOINT ["/usr/bin/tini", "--", "1xops"]
CMD ["--help"]
