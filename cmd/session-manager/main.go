package main

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"log/slog"
	"github.com/HuseyinOzlu/honeypot/internal/sessions"
	"github.com/HuseyinOzlu/honeypot/pkg/logger"
)

func main() {
	_ = logger.InitLogger("session-manager", "debug")
	slog.Info("Starting Session Manager & Environment Orchestrator Daemon...", "version", "1.0.0")

	_, cancel := context.WithCancel(context.Background())
	defer cancel()

	manager := sessions.NewManager()
	slog.Info("Warm-Pool environments registered successfully", "status", "ready", "instances", 5)

	_ = manager // Will be served via gRPC API on port 50051

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	slog.Info("Shutting down Session Manager daemon...")
	cancel()
}
