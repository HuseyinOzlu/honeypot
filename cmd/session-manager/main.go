package main

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"log/slog"
	"github.com/HuseyinOzlu/honeypot/internal/sessions"
	"github.com/HuseyinOzlu/honeypot/pkg/logger"
	. "github.com/HuseyinOzlu/honeypot/pkg/constants"
)

func main() {
	_ = logger.InitLogger("session-manager", "debug")
	slog.Info(GetMsg(KeyStartingSMAndOrchestrator), "version", "1.0.0")

	_, cancel := context.WithCancel(context.Background())
	defer cancel()

	manager := sessions.NewManager()
	slog.Info(GetMsg(KeyWarmPoolRegistered), "status", "ready", "instances", 5)

	_ = manager

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	slog.Info(string(KeyShuttingDownSMAndOrch))
	cancel()
}
