#!/bin/bash

wait_for_deployment() {
    local DEPLOYMENT=$1
    local NAMESPACE=$2
    local TIMEOUT=${3:-300s}

    echo "⏳ [1/2] Waiting for Kubernetes to register '$DEPLOYMENT'..."
    
    until kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" &> /dev/null; do
        sleep 2
    done

    echo "👀 [2/2] Deployment registered! Watching pods spin up..."
    
    if ! kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout="$TIMEOUT"; then
        echo "❌ FATAL: $DEPLOYMENT failed to become ready within $TIMEOUT!"
        echo "🔍 Fetching pod status for debugging:"
        kubectl get pods -n "$NAMESPACE"
        exit 1
    fi

    echo "✅ $DEPLOYMENT is 100% online and ready!"
    echo "------------------------------------------------------"
}