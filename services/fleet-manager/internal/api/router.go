package api

import (
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"

	"fleet-manager/internal/api/handler"
	authMiddleware "fleet-manager/internal/api/middleware"
	"fleet-manager/internal/service"
)

// NewRouter initializes the Chi router, global middleware, and endpoint mapping.
func NewRouter(serverService *service.ServerService) *chi.Mux {
	r := chi.NewRouter()

	// 1. Global Middleware
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	// 2. CORS Configuration
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"*"}, // Replace with your settings.DOMAIN_URL in production
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-User-ID"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	// 3. Unprotected Routes
	r.Get("/health", handler.HealthCheck)

	// 4. Protected Routes
	serverHandler := handler.NewServerHandler(serverService)

	r.Route("/servers", func(r chi.Router) {
		// Enforce identity checks on all /servers endpoints
		r.Use(authMiddleware.RequireAuth)

		r.Get("/", serverHandler.ListServers)
		r.Post("/deploy", serverHandler.DeployServer)
		r.Get("/{server_id}", serverHandler.GetServerDetails)
		r.Post("/{server_id}/power", serverHandler.PowerAction)
	})

	return r
}