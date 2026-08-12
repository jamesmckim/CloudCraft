package service

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"strings"

	"fleet-manager/internal/client"
	"fleet-manager/internal/k8s"
	"fleet-manager/internal/model"
	"fleet-manager/internal/repository"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

type ServerService struct {
	repo           *repository.ServerRepository
	manager        *k8s.ServerManager
	redis          *redis.Client
	identityClient *client.IdentityClient
}

func NewServerService(
	repo *repository.ServerRepository,
	manager *k8s.ServerManager,
	redis *redis.Client,
	identityClient *client.IdentityClient,
) *ServerService {
	return &ServerService{
		repo:           repo,
		manager:        manager,
		redis:          redis,
		identityClient: identityClient,
	}
}

func (s *ServerService) ListServers(ctx context.Context, userID string) ([]model.ServerDetails, error) {
	servers, err := s.repo.GetByOwner(ctx, userID)
	if err != nil {
		return nil, err
	}

	var results []model.ServerDetails
	for _, srv := range servers {
		isOnline := false
		if srv.ActivePodName != nil && *srv.ActivePodName != "" {
			container := s.manager.GetContainer(*srv.ActivePodName)
			if container != nil && container.Status == "running" {
				isOnline = true
			}
		}

		displayName := getDisplayName(srv)

		results = append(results, model.ServerDetails{
			ID:      srv.ID,
			Name:    displayName,
			Status:  map[bool]string{true: "online", false: "offline"}[isOnline],
			CPU:     0,
			RAM:     0,
			Players: 0,
		})
	}

	return results, nil
}

func (s *ServerService) GetServerDetails(ctx context.Context, serverID string) (*model.ServerDetails, error) {
	srv, err := s.repo.Get(ctx, serverID)
	if err != nil {
		return nil, errors.New("server not found in database")
	}

	isOnline := false
	if srv.ActivePodName != nil && *srv.ActivePodName != "" {
		container := s.manager.GetContainer(*srv.ActivePodName)
		isOnline = container != nil && container.Status == "running"
	}

	var cpu, ram float64
	var players int

	stats, _ := s.redis.HGetAll(ctx, "server_stats:"+serverID).Result()
	if isOnline {
		cpu, _ = strconv.ParseFloat(stats["cpu"], 64)
		ram, _ = strconv.ParseFloat(stats["ram"], 64)
		players, _ = strconv.Atoi(stats["players"])
	}

	return &model.ServerDetails{
		ID:      srv.ID,
		Name:    getDisplayName(srv),
		Status:  map[bool]string{true: "online", false: "offline"}[isOnline],
		CPU:     cpu,
		RAM:     ram,
		Players: players,
	}, nil
}

func (s *ServerService) TogglePower(ctx context.Context, userID, serverID, action string) (map[string]string, error) {
	srv, err := s.repo.Get(ctx, serverID)
	if err != nil {
		return nil, errors.New("server not registered in database")
	}

	if srv.OwnerID != userID {
		return nil, errors.New("you do not own this server")
	}

	switch action {
	case "stop":
		if srv.ActivePodName == nil || s.manager.GetContainer(*srv.ActivePodName) == nil {
			return nil, errors.New("server instance not found or already stopped")
		}
		s.manager.StopServer(*srv.ActivePodName)
		s.repo.UpdateActivePod(ctx, srv.ID, nil)

	case "start":
		credits, err := s.identityClient.GetUserCredits(ctx, userID)
		if err != nil || credits <= 1.0 {
			return nil, errors.New("insufficient credits")
		}

		if srv.ActivePodName != nil && s.manager.GetContainer(*srv.ActivePodName) != nil {
			return map[string]string{"status": "already_running"}, nil
		}

		token := generateSecureToken()
		s.redis.Set(ctx, "sidecar_auth:"+serverID, token, 0)

		newContainer, err := s.manager.CreateServer(srv.GameID, userID, serverID, token, srv.Config)
		if err != nil {
			return nil, err
		}

		s.repo.UpdateActivePod(ctx, srv.ID, &newContainer.Name)
	default:
		return nil, errors.New("invalid action")
	}

	return map[string]string{"result": "success", "status": "processing"}, nil
}

func (s *ServerService) DeployServer(ctx context.Context, userID, gameID string, config map[string]interface{}) (map[string]string, error) {
	// 1. Validate Configs via JSON unmarshaling into strict structs
	configBytes, _ := json.Marshal(config)

	if gameID == "valheim" {
		var valheimCfg model.ValheimConfig
		if err := json.Unmarshal(configBytes, &valheimCfg); err != nil {
			return nil, fmt.Errorf("invalid configuration: %v", err)
		}
		if err := valheimCfg.Validate(); err != nil {
			return nil, fmt.Errorf("invalid configuration: %v", err)
		}
	} else if gameID == "test-server" {
		var testCfg model.TestServerConfig
		if err := json.Unmarshal(configBytes, &testCfg); err != nil {
			return nil, fmt.Errorf("invalid configuration: %v", err)
		}
		testCfg.SetupDefaults()
		// Re-marshal back to map to ensure defaults are saved
		newBytes, _ := json.Marshal(testCfg)
		json.Unmarshal(newBytes, &config)
	}

	// 2. Check Credits
	credits, err := s.identityClient.GetUserCredits(ctx, userID)
	if err != nil || credits < 5.0 {
		return nil, errors.New("insufficient credits")
	}

	// 3. Generate IDs and Tokens
	logicalServerID := uuid.New().String()
	token := generateSecureToken()
	s.redis.Set(ctx, "sidecar_auth:"+logicalServerID, token, 0)

	// 4. Deploy to Kubernetes
	newContainer, err := s.manager.CreateServer(gameID, userID, logicalServerID, token, config)
	if err != nil {
		return nil, err
	}

	// 5. Save to Database
	newServer := &model.Server{
		ID:            logicalServerID,
		OwnerID:       userID,
		GameID:        gameID,
		Config:        config,
		ActivePodName: &newContainer.Name,
		HourlyCost:    0.10,
	}

	if err := s.repo.Create(ctx, newServer); err != nil {
		return nil, fmt.Errorf("failed to register server: %v", err)
	}

	return map[string]string{"status": "success", "server_id": logicalServerID}, nil
}

// --- Helpers ---

func getDisplayName(srv *model.Server) string {
	if name, ok := srv.Config["VALHEIM_SERVER_NAME"].(string); ok && name != "" {
		return name
	}
	if name, ok := srv.Config["TEST_SERVER_NAME"].(string); ok && name != "" {
		return name
	}
	return strings.Title(srv.GameID) + " Server"
}

func generateSecureToken() string {
	bytes := make([]byte, 16)
	rand.Read(bytes)
	return hex.EncodeToString(bytes)
}