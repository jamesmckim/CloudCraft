#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "🔧 Configuring Kubernetes for local development..."

# 1. Copy the host machine's kubeconfig into the container
mkdir -p ~/.kube
cp -r /tmp/.kube-localhost/* ~/.kube/

# 2. Redirect localhost to the host machine's Docker network
sed -i 's/127.0.0.1/host.docker.internal/g' ~/.kube/config

# 3. Secure the config file to silence Kustomize/Helm warnings
chmod 600 ~/.kube/config

# Point kubectl inside the Dev Container to k3d's internal Docker network load balancer
if [ -f "$HOME/.kube/config" ]; then
    sed -i 's|server: https://.*|server: https://k3d-dev-cluster-serverlb:6443|g' "$HOME/.kube/config" 2>/dev/null || true
fi

echo "✅ Kubeconfig ready! You can now run: skaffold dev"