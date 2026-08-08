package main

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"log/slog"
	"github.com/HuseyinOzlu/honeypot/pkg/logger"
	. "github.com/HuseyinOzlu/honeypot/pkg/constants"
)

func main() {
	_ = logger.InitLogger("telemetry-collector", "debug")
	slog.Info(GetMsg(KeyStartingeBPFLog), "version", "1.0.0")

	_, cancel := context.WithCancel(context.Background())
	defer cancel()

	slog.Info(GetMsg(KeyTelemetryPPLListening))

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	slog.Info(GetMsg(KeyShuttingDownCollector))
	cancel()
}
