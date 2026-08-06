# ==============================================================================
# LOCAL KUBERNETES DEV ENVIRONMENT (IDEMPOTENT & SELF-HEALING)
# ==============================================================================

# 1. Create the cluster only if it doesn't already exist, then sync certificates
create-cluster:
	@if k3d cluster list dev-cluster >/dev/null 2>&1; then \
		echo " --- Cluster 'dev-cluster' already exists. Skipping creation."; \
	else \
		echo " --- Creating k3d development cluster from declarative config..."; \
		k3d cluster create --config k3d-config.yaml; \
	fi
	@echo " --- Syncing kubeconfig to current Dev Container..."
	@mkdir -p ~/.kube
	@k3d kubeconfig get dev-cluster > ~/.kube/config
	@chmod 600 ~/.kube/config
	@echo " --- Cluster connected and ready!"

# 2. All-in-one idempotent bootstrap: Ensures cluster is up, applies CRDs, and waits for operators
setup-cluster: create-cluster
	@echo " --- Applying Custom Resource Definitions (CRDs)..."
	@kustomize build deployments/k8s/crds --load-restrictor=LoadRestrictionsNone | kubectl apply --server-side -f -
	@echo " --- Waiting for CNPG operator to become available..."
	@kubectl wait --for=condition=Available --timeout=120s deployment/cnpg-controller-manager -n cnpg-system
	@echo " ✅ Environment ready! You can now run: skaffold dev"

# 3. Quick teardown: Destroys only the Kubernetes cluster and its network
destroy-cluster:
	@echo " --- Deleting k3d development cluster..."
	@k3d cluster delete dev-cluster 2>/dev/null || true
	@echo " --- Cluster deleted cleanly."

# 4. Nuclear reset: Wipes the cluster and immediately rebuilds a fresh environment
reset-cluster: destroy-cluster setup-cluster

# 5. Clean app deployments without deleting the K3s cluster nodes
clean:
	@echo " --- Tearing down active Skaffold apps..."
	@skaffold delete -p dev 2>/dev/null || true
	@echo " --- Tearing down CRDs..."
	@kustomize build deployments/k8s/crds --load-restrictor=LoadRestrictionsNone | kubectl delete --ignore-not-found -f -
	@echo " --- Wiping database and storage volumes..."
	@kubectl delete pvc --all -n craftcloud-system --ignore-not-found
	@kubectl delete pvc -l app=qdrant -n default --ignore-not-found