package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	agonesv1 "agones.dev/agones/pkg/apis/agones/v1"
	"github.com/spf13/viper"
	corev1 "k8s.io/api/core/v1"
	"sigs.k8s.io/yaml"
)

type Config struct {
	Port               string
	DatabaseURL        string
	RedisHost          string
	RedisPort          int
	RedisPassword      string
	IdentityServiceURL string
	ManagerAPIURL      string
	TelemetryAPIURL    string

	// From settings.yaml
	Namespace string       `json:"namespace"`
	Agones    AgonesConfig `json:"agones"`

	// From templates.yaml
	Templates map[string]map[string]Template
}

type AgonesConfig struct {
	Group   string `json:"group"`
	Version string `json:"version"`
	Plural  string `json:"plural"`
}

type InitContainer struct {
	Name         string               `json:"name"`
	Image        string               `json:"image"`
	Command      []string             `json:"command,omitempty"`
	Args         []string             `json:"args,omitempty"`
	Env          []corev1.EnvVar      `json:"env,omitempty"`
	VolumeMounts []corev1.VolumeMount `json:"volumeMounts,omitempty"`
}

type Template struct {
	Image          string                    `json:"image"`
	Command        []string                  `json:"command,omitempty"`
	Args           []string                  `json:"args,omitempty"`
	Ports          []agonesv1.GameServerPort `json:"ports,omitempty"`
	EnvDefaults    []corev1.EnvVar           `json:"env_defaults,omitempty"`
	InitContainers []InitContainer           `json:"initContainers,omitempty"`
}

func LoadConfig(configDir string) (*Config, error) {
	viper.SetDefault("PORT", "5000")
	viper.SetDefault("REDIS_HOST", "redis-broker-master")
	viper.SetDefault("REDIS_PORT", 6379)
	viper.SetDefault("IDENTITY_SERVICE_URL", "http://identity-service:5000")
	viper.SetDefault("MANAGER_API_URL", "http://fleet-service:5000")
	viper.SetDefault("TELEMETRY_API_URL", "http://telemetry-service:5000")
	viper.SetDefault("DATABASE_URL", "")
	viper.SetDefault("REDIS_PASSWORD", "")

	viper.AutomaticEnv()

	cfg := &Config{
		Port:               viper.GetString("PORT"),
		DatabaseURL:        formatDBURL(viper.GetString("DATABASE_URL")),
		RedisHost:          viper.GetString("REDIS_HOST"),
		RedisPort:          viper.GetInt("REDIS_PORT"),
		RedisPassword:      viper.GetString("REDIS_PASSWORD"),
		IdentityServiceURL: viper.GetString("IDENTITY_SERVICE_URL"),
		ManagerAPIURL:      viper.GetString("MANAGER_API_URL"),
		TelemetryAPIURL:    viper.GetString("TELEMETRY_API_URL"),
	}

	settingsPath := filepath.Join(configDir, "settings.yaml")
	settingsData, err := os.ReadFile(settingsPath)
	if err == nil {
		var yamlSettings struct {
			Kubernetes struct {
				Namespace string `json:"namespace"`
			} `json:"kubernetes"`
			Agones AgonesConfig `json:"agones"`
		}
		if err := yaml.Unmarshal(settingsData, &yamlSettings); err != nil {
			return nil, fmt.Errorf("failed to parse settings.yaml: %v", err)
		}
		cfg.Namespace = yamlSettings.Kubernetes.Namespace
		cfg.Agones = yamlSettings.Agones
	}

	templatesPath := filepath.Join(configDir, "templates.yaml")
	templatesData, err := os.ReadFile(templatesPath)
	if err == nil {
		if err := yaml.Unmarshal(templatesData, &cfg.Templates); err != nil {
			return nil, fmt.Errorf("failed to parse templates.yaml: %v", err)
		}
	} else {
		return nil, fmt.Errorf("failed to load templates.yaml: %v", err)
	}

	return cfg, nil
}

func (c *Config) RedisAddr() string {
	return fmt.Sprintf("%s:%d", c.RedisHost, c.RedisPort)
}

func formatDBURL(url string) string {
	return strings.Replace(url, "postgresql+asyncpg://", "postgres://", 1)
}