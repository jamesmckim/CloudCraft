# ==========================================
# Stage 1: Build the Go binary
# ==========================================
FROM golang:1.26-alpine AS builder

# Set environment variables for optimized Go build
ENV CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64

WORKDIR /build

# Install ca-certificates (required to verify TLS connections for K8s/Identity calls)
RUN apk add --no-cache ca-certificates

# Copy go.mod and go.sum first to leverage Docker layer caching
COPY go.mod go.sum ./
RUN go mod download

# Copy the rest of the application source code
COPY . .

# Build a statically linked binary. 
# -s -w strips debugging information to reduce binary size
RUN go build -ldflags="-s -w" -a -installsuffix cgo -o fleet-manager ./cmd/server/main.go

FROM golang:1.26-alpine AS dev

WORKDIR /app

RUN go install github.com/air-verse/air@latest

COPY go.mod go.sum ./
RUN go mod download

COPY . .

CMD ["air"]

# ==========================================
# Stage 3: Create the minimal runtime image
# ==========================================
FROM alpine:3.24

WORKDIR /app

# Import the root ca-certificates from the builder stage
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Create a non-root user and group for Kubernetes security best practices
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy the static binary and the config directory from the builder stage
COPY --from=builder /build/fleet-manager .
COPY --from=builder /build/config ./config

# Set ownership to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose the standard application port
EXPOSE 5000

# Run the binary
CMD ["./fleet-manager"]