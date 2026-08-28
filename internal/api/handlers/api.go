package handlers 

import (
	"context"
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/HuseyinOzlu/honeypot/pkg/telemetry"
)


// @title Honeypot REST API
// @version 1.0
// @description Telemetry API for the Honeypot project.
// @host localhost:8080
// @BasePath /api/v1

// SystemHealth godoc
// @Summary Check System Health
// @Description Checks if the Gateway and Database are running
// @Tags system
// @Produce json
// @Success 200 {object} map[string]string
// @Router /api/v1/health [get]
func SystemHealth(w http.ResponseWriter, r *http.Request) {
	status := "UP"
	dbStatus := "UP"
	if err := telemetry.DB.Ping(context.Background()); err != nil {
		dbStatus = "DOWN"
		status = "DEGRADED"
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"system": status,
		"database": dbStatus,
	})
}

// GetHTTPLogs godoc
// @Summary Get HTTP Logs
// @Description Retrieves the latest HTTP logs captured by the honeypot
// @Tags logs
// @Produce json
// @Param limit query int false "Number of logs to retrieve" default(50)
// @Success 200 {array} telemetry.HTTPLog
// @Router /api/v1/logs/http [get]
func GetHTTPLogs(w http.ResponseWriter, r *http.Request) {
	limit := parseLimit(r, 50)
	logs, err := telemetry.GetHTTPLogs(limit)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(logs)
}

// GetCommandLogs godoc
// @Summary Get SSH Command Logs
// @Description Retrieves the latest eBPF logs captured by the honeypot
// @Tags logs
// @Produce json
// @Param limit query int false "Number of logs to retrieve" default(50)
// @Success 200 {array} telemetry.CommandLog
// @Router /api/v1/logs/ssh [get]
func GetCommandLogs(w http.ResponseWriter, r *http.Request) {
	limit := parseLimit(r, 50)
	logs, err := telemetry.GetCommandLogs(limit)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(logs)
}

// GetEBPFLogs godoc
// @Summary Get eBPF Kernel Logs
// @Description Retrieves the latest eBPF logs captured by the honeypot
// @Tags logs
// @Produce json
// @Param limit query int false "Number of logs to retrieve" default(50)
// @Success 200 {array} telemetry.EBPFLog
// @Router /api/v1/logs/ebpf [get]
func GetEBPFLogs(w http.ResponseWriter, r *http.Request) {
	limit := parseLimit(r, 50)
	logs, err := telemetry.GetEBPFLogs(limit)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type","application/json")
	json.NewEncoder(w).Encode(logs)
}


func parseLimit(r *http.Request, defaultLimit int) int {
	limitStr := r.URL.Query().Get("limit")
	if limitStr == "" {
		return defaultLimit
	}
	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit <= 0 {
		return defaultLimit
	}
	return limit
}