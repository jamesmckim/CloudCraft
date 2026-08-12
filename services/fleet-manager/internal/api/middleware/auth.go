package middleware

import (
	"context"
	"net/http"
)

// contextKey prevents collision of keys across different packages
type contextKey string

const UserIDKey contextKey = "user_id"

// RequireAuth extracts the X-User-ID header injected by Traefik ForwardAuth
// and passes it down into the request context.
func RequireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		userID := r.Header.Get("X-User-ID")
		
		if userID == "" {
			http.Error(w, `{"detail":"Unauthorized: Missing identity context"}`, http.StatusUnauthorized)
			return
		}

		// Inject user identity into context
		ctx := context.WithValue(r.Context(), UserIDKey, userID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}