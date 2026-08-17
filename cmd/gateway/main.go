package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/HuseyinOzlu/honeypot/internal/protocols/ssh"
	. "github.com/HuseyinOzlu/honeypot/pkg/constants"
	"github.com/HuseyinOzlu/honeypot/pkg/logger"
	"github.com/HuseyinOzlu/honeypot/pkg/telemetry"
	"github.com/HuseyinOzlu/honeypot/pkg/config"
)

func main() {
	if err := config.LoadConfig("config.yaml"); err != nil {
		panic("Kongigurasyon dosyası okunamadı: " + err.Error())
	}
	if err := telemetry.InitClickhouse(config.AppConfig.Telemetry.ClickHouseURL); err != nil {
		panic("Veritabanı çöktü, sistem başlatılamıyor: " + err.Error())
	}

	
	_ = logger.InitLogger("gateway", "info")
	slog.Info(GetMsg(KeyStartingGateway), "version", "1.0.0")

	_, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	slog.Info(GetMsg(KeyListeningGateway), "ssh_port", 2222, "http_port", 8080)

	serverPort := config.AppConfig.Server.Port
	sshServer := ssh.NewServer()

	if err := sshServer.Start("0.0.0.0:" + serverPort); err != nil {
		panic("SSH sunucusu başlatılamadı: "+ err.Error())
	}

	go sshServer.Start(":2222")
	<-sigChan
	slog.Info(GetMsg(KeyShuttingDownGateway))
	cancel()
}
