package main

import (
	"context"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"fleet-manager/internal/api"
	"fleet-manager/internal/client"
	"fleet-manager/internal/config"
	"fleet-manager/internal/k8s"
	"fleet-manager/internal/model"
	"fleet-manager/internal/repository"
	"fleet-manager/internal/service"

	"github.com/redis/go-redis/v9"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func main() {
	// 1. Load Configurations & Game Templates
	cfg, err := config.LoadConfig("config")
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// 2. Initialize PostgreSQL DB (GORM)
	db, err := gorm.Open(postgres.Open(cfg.DatabaseURL), &gorm.Config{})
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	if err := model.AutoMigrate(db); err != nil {
		log.Fatalf("Failed to run database migrations: %v", err)
	}

	// 3. Initialize Redis Client
	rdb := redis.NewClient(&redis.Options{
		Addr:     cfg.RedisAddr(),
		Password: cfg.RedisPassword,
		DB:       0,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := rdb.Ping(ctx).Err(); err != nil {
		log.Fatalf("Failed to connect to Redis: %v", err)
	}

	// 4. Initialize Kubernetes / Agones Manager
	k8sManager, err := k8s.NewServerManager(cfg)
	if err != nil {
		log.Fatalf("Failed to initialize Kubernetes manager: %v", err)
	}

	// 5. Wire Up Dependencies
	identityClient := client.NewIdentityClient(cfg.IdentityServiceURL)
	serverRepo := repository.NewServerRepository(db)
	serverService := service.NewServerService(serverRepo, k8sManager, rdb, identityClient)

	// 6. Router & Middleware
	router := api.NewRouter(serverService)

	// 7. HTTP Server Setup with Graceful Shutdown
	srv := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		log.Printf("Server starting on port %s...", cfg.Port)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("HTTP server failure: %v", err)
		}
	}()

	// Listen for OS signals for graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}

	log.Println("Server stopped cleanly.")
}