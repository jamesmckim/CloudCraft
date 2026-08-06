#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "🔧 Checking Kubernetes cluster connection..."

mkdir -p ~/.kube

# If dev-cluster ek3d cluster delete dev-clusterxists, declaratively sync its active config
if command -v k3d >/dev/null 2>&1 && k3d cluster list dev-cluster >/dev/null 2>&1; then
    k3d kubeconfig get dev-cluster > ~/.kube/config
    chmod 600 ~/.kube/config

elif [ -d "/tmp/.kube-localhost" ] && [ "$(ls -A /tmp/.kube-localhost 2>/dev/null)" ]; then
    echo "📋 Cluster not running yet. Copying fallback kubeconfig from host..."
    cp -r /tmp/.kube-localhost/* ~/.kube/ 2>/dev/null || true
    chmod -R 600 ~/.kube/* 2>/dev/null || true
else
    echo "ℹ️  No cluster detected. Run 'make setup-cluster' to create one."
fi

echo "✅ Kubeconfig ready! You can now run: skaffold dev"