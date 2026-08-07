package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/HuseyinOzlu/honeypot/pkg/logger"
	"github.com/HuseyinOzlu/honeypot/internal/protocols/ssh"
)

func main() {
	_ = logger.InitLogger("gateway", "info")
	slog.Info("Starting Gateway Service...", "version", "1.0.0")

	_, cancel := context.WithCancel(context.Background())
	defer cancel() // context sızıntısını önlemek için kullanıyoruz.

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	slog.Info("Gateway Listening for Multiplexed Connections", "ssh_port", 2222, "http_port", 8080)

	sshSunucu := ssh.NewServer()
	go sshSunucu.Start(":2222")
	// Signal gelene kadar bekle
	<-sigChan
	slog.Info("Shutting down Edge Gateway cleanly...")
	cancel()
}
