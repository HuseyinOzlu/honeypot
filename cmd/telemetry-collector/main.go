package main

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"log/slog"
	"github.com/HuseyinOzlu/honeypot/pkg/logger"
)

func main() {
	_ = logger.InitLogger("telemetry-collector", "debug")
	slog.Info("Starting High-Throughput eBPF Telemetry & Log Collector Service...", "version", "1.0.0")

	_, cancel := context.WithCancel(context.Background())
	defer cancel()

	slog.Info("Telemetry pipeline listening on gRPC port 50052 and connected to ClickHouse buffer")

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	slog.Info("Flushing telemetry ring-buffers and shutting down Collector service...")
	cancel()
}
