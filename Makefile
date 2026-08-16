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

setup-tls:
	@echo " --- Checking mkcert local Certificate Authority..."
	@mkcert -install >/dev/null 2>&1
	@mkdir -p .certs
	@echo " --- Generating wildcard certificate for *.192.168.0.161.nip.io..."
	@mkcert -cert-file .certs/tls.crt -key-file .certs/tls.key "*.192.168.0.161.nip.io" "192.168.0.161.nip.io" >/dev/null 2>&1
	@echo " --- Ensuring target namespace 'craftcloud-system' exists..."
	@kubectl create namespace craftcloud-system --dry-run=client -o yaml | kubectl apply --server-side -f -
	@echo " --- Applying idempotent TLS secret 'sso-tls'..."
	@kubectl create secret tls sso-tls \
		--cert=.certs/tls.crt \
		--key=.certs/tls.key \
		-n craftcloud-system \
		--dry-run=client -o yaml | kubectl apply -f -
	@echo " ✅ TLS certificates ready and secret 'sso-tls' applied!"

# 2. Install core operators, CRDs, and optional platform extensions (Agones)
setup-platform:
	@echo " --- Applying core Platform Custom Resource Definitions (CRDs)..."
	@kustomize build deployments/k8s/crds --load-restrictor=LoadRestrictionsNone | kubectl apply --server-side -f -
	@echo " --- Waiting for CNPG operator to become available..."
	@kubectl wait --for=condition=Available --timeout=120s deployment/cnpg-controller-manager -n cnpg-system
	@echo " --- Installing Agones (Local K3d Overlay)..."
	@kustomize build --enable-helm deployments/k8s/overlays/local-dev/agones | kubectl apply --server-side -f -
	@echo " --- Waiting for Agones controller to become available..."
	@kubectl wait --for=condition=available --timeout=120s deployment/agones-controller -n agones-system
	@echo " ✅ Platform layer ready!"

setup-cluster: create-cluster setup-tls setup-platform
	@echo " =================================================================="
	@echo " ✅ Environment fully initialized! You can now run: make dev"
	@echo " =================================================================="

# 3. Quick teardown: Destroys only the Kubernetes cluster and its network
destroy-cluster:
	@echo " --- Deleting k3d development cluster..."
	@k3d cluster delete dev-cluster 2>/dev/null || true
	@echo " --- Cleaning up local certificate files and Helm chart caches..."
	@rm -rf .certs
	@find deployments/k8s -type d -name "charts" -exec rm -rf {} + 2>/dev/null || true
	@echo " --- Cluster and temporary files deleted cleanly."

# 4. Nuclear reset: Wipes the cluster and immediately rebuilds a fresh environment
reset-cluster: destroy-cluster setup-cluster

# 5. Clean app deployments without deleting the K3s cluster nodes
clean:
	@echo " --- Tearing down active Skaffold apps..."
	@skaffold delete -p dev 2>/dev/null || true
	@echo " --- Tearing down CRDs..."
	@kustomize build deployments/k8s/crds --load-restrictor=LoadRestrictionsNone | kubectl delete --ignore-not-found -f -
	@echo " --- Wiping database, storage volumes, certs, and Helm chart caches..."
	@kubectl delete pvc --all -n craftcloud-system --ignore-not-found
	@kubectl delete pvc -l app=qdrant -n default --ignore-not-found
	@rm -rf .certs
	@find deployments/k8s -type d -name "charts" -exec rm -rf {} + 2>/dev/null || true
	@echo " --- Environment cleaned."

setup-host:
	@echo " --- Verifying Linux host kernel limits (requires sudo)..."
	@sudo bash -c '\
		grep -q "fs.file-max=524288" /etc/sysctl.conf || echo "fs.file-max=524288" >> /etc/sysctl.conf; \
		grep -q "fs.inotify.max_user_watches=524288" /etc/sysctl.conf || echo "fs.inotify.max_user_watches=524288" >> /etc/sysctl.conf; \
		grep -q "fs.inotify.max_user_instances=8192" /etc/sysctl.conf || echo "fs.inotify.max_user_instances=8192" >> /etc/sysctl.conf; \
		sysctl -p; \
	'
	@echo " --- Verifying Docker daemon ulimits..."
	@sudo bash -c '\
		if [ ! -f /etc/docker/daemon.json ] || ! grep -q "default-ulimits" /etc/docker/daemon.json; then \
			echo "{\"default-ulimits\": {\"nofile\": {\"Name\": \"nofile\",\"Hard\": 100000,\"Soft\": 100000}}}" > /etc/docker/daemon.json; \
			echo " --- Restarting Docker daemon to apply limits..."; \
			systemctl restart docker; \
		else \
			echo " --- Docker limits already configured."; \
		fi \
	'
	@echo " ✅ Host machine is ready for heavy local K8s development!"

dev:
	@echo " --- Forcing maximum file descriptor limits for this session..."
	bash -c "ulimit -n 100000 && skaffold dev --trigger=polling --watch-poll-interval=2000"