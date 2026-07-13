# Run this with "make clean"
clean:
	@echo "Tearing down apps..."
	skaffold delete
	@echo "Tearing down CRDs..."
	kustomize build deployments/k8s/crds --load-restrictor=LoadRestrictionsNone | kubectl delete --ignore-not-found -f -