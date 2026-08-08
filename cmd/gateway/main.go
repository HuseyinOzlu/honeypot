package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	. "github.com/HuseyinOzlu/honeypot/pkg/constants"
	"github.com/HuseyinOzlu/honeypot/pkg/logger"
	"github.com/HuseyinOzlu/honeypot/internal/protocols/ssh"
)

func main() {
	_ = logger.InitLogger("gateway", "info")
	slog.Info(GetMsg(KeyStartingGateway), "version", "1.0.0")

	_, cancel := context.WithCancel(context.Background())
	defer cancel() // context sızıntısını önlemek için kullanıyoruz.

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	slog.Info(GetMsg(KeyListeningGateway), "ssh_port", 2222, "http_port", 8080)

	sshSunucu := ssh.NewServer()
	go sshSunucu.Start(":2222")
	// Sinyal gelene kadar bekle
	<-sigChan
	slog.Info(GetMsg(KeyShuttingDownGateway))
	cancel()
}
