# ==============================================================================
# ANTIGRAVITY HONEYPOT PLATFORM - MULTI-STAGE GO BUILDER
# Builds `gateway`, `session-manager`, and `telemetry-collector` binaries
# ==============================================================================

# --- Stage 1: Build Go Binaries ---
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git build-base

# Copy go module files (or initialize if standalone)
COPY go.mod go.sum* ./
RUN go mod download || true

# Copy source code
COPY . .

# Build multi-binaries with optimizations
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o /bin/gateway ./cmd/gateway || true
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o /bin/session-manager ./cmd/session-manager || true
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o /bin/telemetry-collector ./cmd/telemetry-collector || true

# --- Stage 2: Gateway Runtime ---
FROM alpine:3.19 AS gateway
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata
COPY --from=builder /bin/gateway /usr/local/bin/gateway
EXPOSE 2222 8080
ENTRYPOINT ["/usr/local/bin/gateway"]

# --- Stage 3: Session Manager Runtime ---
FROM alpine:3.19 AS session-manager
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata iproute2 iptables
COPY --from=builder /bin/session-manager /usr/local/bin/session-manager
EXPOSE 50051
ENTRYPOINT ["/usr/local/bin/session-manager"]

# --- Stage 4: Telemetry Collector Runtime ---
FROM alpine:3.19 AS telemetry-collector
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata
COPY --from=builder /bin/telemetry-collector /usr/local/bin/telemetry-collector
EXPOSE 50052
ENTRYPOINT ["/usr/local/bin/telemetry-collector"]
