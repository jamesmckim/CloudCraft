package handler

import (
	"encoding/json"
	"net/http"
)

// HealthCheck mimics the FastAPI /health endpoint
func HealthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "healthy",
		"service": "fleet_manager",
	})
}