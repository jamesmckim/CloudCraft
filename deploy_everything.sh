#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "❌ Error: Please provide a Git repository URL."
  echo "Usage: ./deploy_everything.sh https://github.com/username/repo.git"
  exit 1
fi

GIT_REPO=$1

echo "=========================================="
echo "🚀 INITIATING FULL PLATFORM DEPLOYMENT..."
echo "=========================================="

echo "➡️  LAYER 1: Provisioning Infrastructure on NSF FABRIC..."
python provision_fabric.py

echo "➡️  LAYER 2: Configuring Kubernetes (K3s)..."
fab setup-cluster

echo "➡️  LAYER 3: Pulling Code and Deploying the App via Skaffold..."
fab deploy-app --repo-url="$GIT_REPO"

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "Your platform is now live."
echo "=========================================="