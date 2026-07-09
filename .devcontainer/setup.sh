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

echo "🚀 Installing Keycloak Operator CRDs..."

# 4. Install the dictionary definitions (CRDs) FIRST
kubectl apply --server-side -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.6.4/kubernetes/keycloaks.k8s.keycloak.org-v1.yml
kubectl apply --server-side -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.6.4/kubernetes/keycloakrealmimports.k8s.keycloak.org-v1.yml

echo "🚀 Installing Keycloak Operator..."

kubectl create namespace craftcloud-system --dry-run=client -o yaml | kubectl apply -f -

# 5. Install the Operator Deployment (The Brain)

curl -sL https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.6.4/kubernetes/kubernetes.yml | \
sed "s/namespace: default/namespace: craftcloud-system/g" | \
kubectl apply -n craftcloud-system -f -

echo "✅ Local Dev Environment is ready! You can now run: skaffold dev"