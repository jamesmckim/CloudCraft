#!/bin/bash
echo "Installing ArgoCD..."

source /tmp/bootstrap/utils.sh

# 1. Create namespace and install
kubectl get namespace argocd >/dev/null 2>&1 || kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2. Wait for the Application CRD to be established so we can feed it our repo
echo "Waiting for ArgoCD CRDs to initialize..."
kubectl wait --for=condition=established --timeout=120s crd/applications.argoproj.io

# 3. Wait for the server pod to be ready
echo "Waiting for ArgoCD Server to spin up..."
wait_for_deployment "argocd-server" "argocd" "300s"
wait_for_deployment "argocd-repo-server" "argocd" "300s"
wait_for_deployment "argocd-application-controller" "argocd" "300s"

echo "ArgoCD Installation Complete!"