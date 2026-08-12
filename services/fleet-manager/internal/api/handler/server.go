package handler

import (
	"encoding/json"
	"net/http"

	"github.com/go-chi/chi/v5"

	authMiddleware "fleet-manager/internal/api/middleware"
	"fleet-manager/internal/model"
	"fleet-manager/internal/service"
)

type ServerHandler struct {
	service *service.ServerService
}

func NewServerHandler(s *service.ServerService) *ServerHandler {
	return &ServerHandler{service: s}
}

func (h *ServerHandler) ListServers(w http.ResponseWriter, r *http.Request) {
	// Pull User ID from the context created by ForwardAuth
	userID := r.Context().Value(authMiddleware.UserIDKey).(string)

	servers, err := h.service.ListServers(r.Context(), userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(servers)
}

func (h *ServerHandler) GetServerDetails(w http.ResponseWriter, r *http.Request) {
	serverID := chi.URLParam(r, "server_id")

	details, err := h.service.GetServerDetails(r.Context(), serverID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(details)
}

func (h *ServerHandler) PowerAction(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value(authMiddleware.UserIDKey).(string)
	serverID := chi.URLParam(r, "server_id")

	var payload model.PowerActionPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, `{"detail":"Invalid request payload"}`, http.StatusBadRequest)
		return
	}

	res, err := h.service.TogglePower(r.Context(), userID, serverID, payload.Action)
	if err != nil {
		// In a production environment, you'd switch on specific errors to return 402/403/404s
		http.Error(w, err.Error(), http.StatusBadRequest) 
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(res)
}

func (h *ServerHandler) DeployServer(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value(authMiddleware.UserIDKey).(string)

	var payload model.GameDeploymentPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, `{"detail":"Invalid request payload"}`, http.StatusBadRequest)
		return
	}

	res, err := h.service.DeployServer(r.Context(), userID, payload.GameID, payload.Config)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(res)
}