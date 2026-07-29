# Run this ONLY once when you create a fresh K3s/Rancher environment
setup-cluster:
	kustomize build deployments/k8s/crds --load-restrictor=LoadRestrictionsNone | kubectl apply --server-side -f -
	kubectl wait --for=condition=Available --timeout=120s deployment/cnpg-controller-manager -n cnpg-system

# Run this with "make clean"
clean:
	@echo " --- Tearing down apps..."
	skaffold delete -p dev
	@echo " --- Tearing down CRDs..."
	kustomize build deployments/k8s/crds --load-restrictor=LoadRestrictionsNone | kubectl delete --ignore-not-found -f -
	@echo " --- Wiping database and storage volumes..."
	kubectl delete pvc --all -n craftcloud-system --ignore-not-found
	kubectl delete pvc -l app=qdrant -n default --ignore-not-found