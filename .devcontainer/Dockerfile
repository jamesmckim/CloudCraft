# ==========================================
# STAGE 1: The Downloader
# ==========================================
# We use a tiny Alpine image just to download the binaries safely.
FROM alpine:3.19 AS builder

RUN apk add --no-cache curl tar

RUN curl -Lo /skaffold https://storage.googleapis.com/skaffold/releases/v2.23.0/skaffold-linux-amd64 \
    && chmod +x /skaffold

RUN curl -Lo /sops https://github.com/getsops/sops/releases/download/v3.13.2/sops-v3.13.2.linux.amd64 \
    && chmod +x /sops

RUN curl -LO https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.8.1/kustomize_v5.8.1_linux_amd64.tar.gz \
    && tar -zxvf kustomize_v5.4.1_linux_amd64.tar.gz \
    && chmod +x kustomize


# ==========================================
# STAGE 2: The Final Dev Environment
# ==========================================
FROM python:3.12-bookworm

# Import uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment configurations
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

USER root

# Cleanly install the OS-level dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-downloaded binaries from Stage 1 directly into the system path
COPY --from=builder /skaffold /usr/local/bin/skaffold
COPY --from=builder /sops /usr/local/bin/sops
COPY --from=builder /kustomize /usr/local/bin/kustomize

# Create the standard VS Code non-root user
RUN useradd -ms /bin/bash vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER vscode
WORKDIR /workspace