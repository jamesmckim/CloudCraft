#!/bin/bash
echo "Installing ArgoCD..."

# 1. Create namespace and install
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2. Wait for the Application CRD to be established so we can feed it our repo
echo "Waiting for ArgoCD CRDs to initialize..."
kubectl wait --for=condition=established --timeout=120s crd/applications.argoproj.io

# 3. Wait for the server pod to be ready
echo "Waiting for ArgoCD Server to spin up..."
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s

echo "ArgoCD Installation Complete!"