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

echo "✅ Kubeconfig ready! You can now run: skaffold dev"