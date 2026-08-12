package model

import (
	"errors"
	"fmt"
	"strings"
)

// --- Request Payloads ---

type GameDeploymentPayload struct {
	GameID string                 `json:"game_id"`
	Config map[string]interface{} `json:"config"`
}

type PowerActionPayload struct {
	Action string `json:"action"` // "start" or "stop"
}

// --- Response Payloads ---

type ServerDetails struct {
	ID      string  `json:"id"`
	Name    string  `json:"name"`
	Status  string  `json:"status"` // "online" or "offline"
	CPU     float64 `json:"cpu"`
	RAM     float64 `json:"ram"`
	Players int     `json:"players"`
}

// --- Validators (Equivalent to Pydantic Schemas) ---

type ValheimConfig struct {
	IsModded              bool   `json:"is_modded"`
	ModURLs               string `json:"mod_urls"`
	ValheimServerName     string `json:"VALHEIM_SERVER_NAME"`
	ValheimWorldName      string `json:"VALHEIM_WORLD_NAME"`
	ValheimServerPass     string `json:"VALHEIM_SERVER_PASS"`
	ValheimUpdateCron     string `json:"VALHEIM_UPDATE_CRON"`
	ValheimBackupsMaxCount int   `json:"VALHEIM_BACKUPS_MAX_COUNT"`
}

// Validate mimics the @model_validator from Pydantic
func (v *ValheimConfig) Validate() error {
	if len(v.ValheimServerName) < 3 || len(v.ValheimServerName) > 30 {
		return errors.New("VALHEIM_SERVER_NAME must be between 3 and 30 characters")
	}
	if len(v.ValheimServerPass) < 5 || len(v.ValheimServerPass) > 30 {
		return errors.New("VALHEIM_SERVER_PASS must be between 5 and 30 characters")
	}
	if v.ValheimBackupsMaxCount < 1 || v.ValheimBackupsMaxCount > 20 {
		return errors.New("VALHEIM_BACKUPS_MAX_COUNT must be between 1 and 20")
	}

	serverNameLower := strings.ToLower(v.ValheimServerName)
	worldNameLower := strings.ToLower(v.ValheimWorldName)
	passLower := strings.ToLower(v.ValheimServerPass)

	if strings.Contains(passLower, serverNameLower) {
		return fmt.Errorf("server password cannot contain the server name")
	}
	if strings.Contains(passLower, worldNameLower) {
		return fmt.Errorf("server password cannot contain the world name")
	}

	return nil
}

type TestServerConfig struct {
	TestServerName string `json:"TEST_SERVER_NAME"`
	TestEchoMsg    string `json:"TEST_ECHO_MSG"`
}

// SetupDefaults mimics Pydantic's default field values
func (t *TestServerConfig) SetupDefaults() {
	if t.TestServerName == "" {
		t.TestServerName = "Local-Test-Server"
	}
	if t.TestEchoMsg == "" {
		t.TestEchoMsg = "CraftCloud Integration OK"
	}
}