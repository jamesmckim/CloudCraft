# Use Debian (Bookworm) for VS Code compatibility, but match your Python 3.12 standard
FROM python:3.12-bookworm

# Import uv exactly as you do in your production Dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables (similar to your production standard)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

USER root

# Install required system tools (curl, git) and your specific infrastructure CLI tools
RUN apt-get update && apt-get install -y --no-install-recommends curl git sudo \
    # Install Skaffold
    && curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64 \
    && install skaffold /usr/local/bin/ \
    && rm skaffold \
    # Install SOPS
    && curl -LO https://github.com/getsops/sops/releases/download/v3.8.1/sops-v3.8.1.linux.amd64 \
    && mv sops-v3.8.1.linux.amd64 /usr/local/bin/sops \
    && chmod +x /usr/local/bin/sops \
    # Install Kustomize
    && curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash \
    && mv kustomize /usr/local/bin/ \
    # Cleanup apt cache to keep image small
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root developer user (mirroring your 'appuser' concept, but standard for VS Code)
RUN useradd -ms /bin/bash vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER vscode
WORKDIR /workspace