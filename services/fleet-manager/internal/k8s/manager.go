package k8s

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"fleet-manager/internal/config"

	// Native Kubernetes & Agones Types
	agonesv1 "agones.dev/agones/pkg/apis/agones/v1"
	agonesclient "agones.dev/agones/pkg/client/clientset/versioned"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

type ServerManager struct {
	k8sClient    *kubernetes.Clientset
	agonesClient *agonesclient.Clientset
	cfg          *config.Config
}

type ContainerInfo struct {
	Name   string
	Status string
}

func NewServerManager(cfg *config.Config) (*ServerManager, error) {
	k8sConfig, err := rest.InClusterConfig()
	if err != nil {
		homeDir, _ := os.UserHomeDir()
		kubeconfigPath := filepath.Join(homeDir, ".kube", "config")
		k8sConfig, err = clientcmd.BuildConfigFromFlags("", kubeconfigPath)
		if err != nil {
			return nil, fmt.Errorf("failed to load kubeconfig: %v", err)
		}
	}

	// 1. Standard Client (for PVCs)
	k8sClient, err := kubernetes.NewForConfig(k8sConfig)
	if err != nil {
		return nil, err
	}

	// 2. Strongly Typed Agones Client
	agClient, err := agonesclient.NewForConfig(k8sConfig)
	if err != nil {
		return nil, err
	}

	return &ServerManager{
		k8sClient:    k8sClient,
		agonesClient: agClient,
		cfg:          cfg,
	}, nil
}

func (m *ServerManager) CreateServer(gameID, userID, logicalServerID, sidecarToken string, configData map[string]interface{}) (*ContainerInfo, error) {
	ctx := context.Background()

	isModded, _ := configData["is_modded"].(bool)
	modState := map[bool]string{true: "modded", false: "vanilla"}[isModded]

	blueprint := m.cfg.Templates[gameID][modState]

	pvcName, err := m.ensurePVCExists(ctx, logicalServerID)
	if err != nil {
		return nil, fmt.Errorf("failed to provision PVC: %v", err)
	}

	// 1. Build Environment Variables using k8s corev1 types
	var envVars []corev1.EnvVar
	for _, env := range blueprint.EnvDefaults {
		envVars = append(envVars, corev1.EnvVar{Name: env.Name, Value: env.Value})
	}
	for k, v := range configData {
		if k != "is_modded" {
			envVars = append(envVars, corev1.EnvVar{Name: k, Value: fmt.Sprintf("%v", v)})
		}
	}

	// 2. Define Shared Volumes
	volumes := []corev1.Volume{
		{
			Name: "world-data",
			VolumeSource: corev1.VolumeSource{
				PersistentVolumeClaim: &corev1.PersistentVolumeClaimVolumeSource{
					ClaimName: pvcName,
				},
			},
		},
		{
			Name: "sidecar-scripts-volume",
			VolumeSource: corev1.VolumeSource{
				ConfigMap: &corev1.ConfigMapVolumeSource{
					LocalObjectReference: corev1.LocalObjectReference{Name: "sidecar-scripts"},
				},
			},
		},
	}

	// 3. Construct Strongly Typed Agones GameServer
	gameServer := &agonesv1.GameServer{
		ObjectMeta: metav1.ObjectMeta{
			GenerateName: fmt.Sprintf("%s-%s-%s-", gameID, modState, userID),
			Labels: map[string]string{
				"craftcloud.role":      "game_sidecar",
				"craftcloud.server_id": logicalServerID,
				"game":                 gameID,
				"mod_state":            modState,
				"owner_id":             userID,
				"role":                 "game-sidecar",
			},
		},
		Spec: agonesv1.GameServerSpec{
			Container: "game-engine",
			// We map the dynamic ports from YAML into Agones types
			Ports: buildAgonesPorts(blueprint.Ports), 
			Template: corev1.PodTemplateSpec{
				Spec: corev1.PodSpec{
					Volumes: volumes,
					Containers: []corev1.Container{
						{
							Name:  "game-engine",
							Image: blueprint.Image,
							Env:   envVars,
							VolumeMounts: []corev1.VolumeMount{
								{Name: "world-data", MountPath: "/config"},
							},
						},
						{
							Name:    "activity-sidecar",
							Image:   "python:3.14.1-alpine3.23",
							Command: []string{"python", "-u", "/app/main.py"},
							Env: []corev1.EnvVar{
								{Name: "GAME_TYPE", Value: gameID},
								{Name: "MANAGER_API_URL", Value: m.cfg.ManagerAPIURL},
								{Name: "TELEMETRY_API_URL", Value: m.cfg.TelemetryAPIURL},
								{Name: "SIDECAR_API_KEY", Value: sidecarToken},
								{Name: "SERVER_UUID", Value: logicalServerID},
								{
									Name: "TARGET_CONTAINER_NAME",
									ValueFrom: &corev1.EnvVarSource{
										FieldRef: &corev1.ObjectFieldSelector{FieldPath: "metadata.name"},
									},
								},
							},
							VolumeMounts: []corev1.VolumeMount{
								{Name: "world-data", MountPath: "/config", ReadOnly: true},
								{Name: "sidecar-scripts-volume", MountPath: "/app"},
							},
						},
					},
				},
			},
		},
	}

	// 4. Create via Typed Client
	created, err := m.agonesClient.AgonesV1().GameServers(m.cfg.Namespace).Create(ctx, gameServer, metav1.CreateOptions{})
	if err != nil {
		return nil, fmt.Errorf("kubernetes deployment error: %v", err)
	}

	return &ContainerInfo{Name: created.Name, Status: "starting"}, nil
}

func (m *ServerManager) GetContainer(serverID string) *ContainerInfo {
	ctx := context.Background()
	gs, err := m.agonesClient.AgonesV1().GameServers(m.cfg.Namespace).Get(ctx, serverID, metav1.GetOptions{})
	if err != nil {
		return nil
	}

	isRunning := gs.Status.State == agonesv1.GameServerStateReady || gs.Status.State == agonesv1.GameServerStateAllocated
	
	return &ContainerInfo{
		Name:   serverID,
		Status: map[bool]string{true: "running", false: "offline"}[isRunning],
	}
}

func (m *ServerManager) StopServer(serverID string) error {
	ctx := context.Background()
	err := m.agonesClient.AgonesV1().GameServers(m.cfg.Namespace).Delete(ctx, serverID, metav1.DeleteOptions{})
	if err != nil && !errors.IsNotFound(err) {
		return err
	}
	return nil
}

func (m *ServerManager) ensurePVCExists(ctx context.Context, logicalServerID string) (string, error) {
	// (Omitted for brevity - exact same logic as before, using standard k8sClient.CoreV1())
	return fmt.Sprintf("world-pvc-%s", logicalServerID), nil
}

// Helper to cast YAML ports to Agones typed ports
func buildAgonesPorts(yamlPorts []interface{}) []agonesv1.GameServerPort {
	var parsed []agonesv1.GameServerPort
    // ... basic type assertions mapping your interface{} to agonesv1.GameServerPort 
	return parsed
}