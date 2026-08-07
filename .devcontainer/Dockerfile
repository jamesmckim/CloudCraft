# ==========================================
# STAGE 1: The Downloader
# ==========================================
# We use a tiny Alpine image just to download the binaries safely.
FROM alpine:3.19 AS builder
ARG TARGETARCH

RUN apk add --no-cache curl tar


RUN set -ex; \
    # 1. Map architecture naming conventions once
    ARCH="${TARGETARCH:-amd64}"; \
    if [ "$ARCH" = "arm64" ]; then \
        KSOPS_ARCH="arm64"; \
    else \
        ARCH="amd64"; \
        KSOPS_ARCH="x86_64"; \
    fi; \
    echo "Building toolchain for architecture: ${ARCH}"; \
    \
    # 2. Download Skaffold
    curl -fSL -o /skaffold "https://storage.googleapis.com/skaffold/releases/v2.23.0/skaffold-linux-${ARCH}"; \
    chmod +x /skaffold; \
    \
    # 3. Download SOPS
    curl -fSL -o /sops "https://github.com/getsops/sops/releases/download/v3.13.2/sops-v3.13.2.linux.${ARCH}"; \
    chmod +x /sops; \
    \
    # 4. Download & Unpack Kustomize
    curl -fSL -O "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.8.1/kustomize_v5.8.1_linux_${ARCH}.tar.gz"; \
    tar -zxvf "kustomize_v5.8.1_linux_${ARCH}.tar.gz" kustomize; \
    chmod +x kustomize; \
    rm -f "kustomize_v5.8.1_linux_${ARCH}.tar.gz"; \
    \
    # 5. Download & Unpack Helm
    curl -fSL -O "https://get.helm.sh/helm-v3.15.2-linux-${ARCH}.tar.gz"; \
    tar -zxvf "helm-v3.15.2-linux-${ARCH}.tar.gz"; \
    mv "linux-${ARCH}/helm" /helm; \
    chmod +x /helm; \
    rm -rf "linux-${ARCH}" "helm-v3.15.2-linux-${ARCH}.tar.gz"; \
    \
    # 6. Download & Unpack KSOPS
    curl -fSL -O "https://github.com/viaduct-ai/kustomize-sops/releases/download/v4.3.1/ksops_4.3.1_Linux_${KSOPS_ARCH}.tar.gz"; \
    tar -zxvf "ksops_4.3.1_Linux_${KSOPS_ARCH}.tar.gz" ksops; \
    mv ksops /ksops; \
    chmod +x /ksops; \
    rm -f "ksops_4.3.1_Linux_${KSOPS_ARCH}.tar.gz"; \
    \
    # 7. Download Kubectl
    KUBECTL_VER="$(curl -fSL -s https://dl.k8s.io/release/stable.txt)"; \
    curl -fSL -o /kubectl "https://dl.k8s.io/release/${KUBECTL_VER}/bin/linux/${ARCH}/kubectl"; \
    chmod +x /kubectl
	
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
    make \
    mkcert \
    libnss3-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-downloaded binaries from Stage 1 directly into the system path
COPY --from=builder /skaffold /usr/local/bin/skaffold
COPY --from=builder /sops /usr/local/bin/sops
COPY --from=builder /kustomize /usr/local/bin/kustomize
COPY --from=builder /helm /usr/local/bin/helm
COPY --from=builder /ksops /usr/local/bin/ksops
COPY --from=builder /kubectl /usr/local/bin/kubectl

# Create the standard VS Code non-root user
RUN useradd -ms /bin/bash vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER vscode
WORKDIR /workspace