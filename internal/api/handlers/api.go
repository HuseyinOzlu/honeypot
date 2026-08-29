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

// DeleteCommandLogs godoc
// @Summary SSH komut loglarını temizler
// @Description Tarih aralığı alırsa sadece o aralıktaki eğer Parametre almazsa veritabanındaki tüm Victim SSH komutlarını siler (Örn: 2026-08-01 00:00:00)
// @Tags telemetry
// @Produce json
// @Param start_date query string false "Baslangic tarihi"
// @Param end_date query string false "Bitis Tarihi"
// @Success 200 {object} map[string]string
// @Router /api/v1/telemetry/ssh [delete]
func DeleteCommandLogs(w http.ResponseWriter, r *http.Request) {
		startDate := r.URL.Query().Get("start_date")
		endDate := r.URL.Query().Get("end_date")

		var err error
		if startDate != "" && endDate != "" {
			err = telemetry.DeleteLogsByDateRange("command_logs", startDate, endDate)
		} else {
			err = telemetry.DeleteAllCommandLogs()
		}
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

	json.NewEncoder(w).Encode(map[string]string{"status": "success", "message": "SSH komut logları temizlendi"})
}

// DeleteHTTPLogs godoc
// @Summary HTTP loglarını temizler
// @Description Tüm sahte web sunucusı (Honeypot) loglarını temizler
// @Tags telemetry
// @Produce json
// @Param start_date query string false "Baslangic tarihi"
// @Param end_date query string false "Bitis Tarihi"
// @Success 200 {object} map[string]string
// @Router /api/v1/telemetry/http [delete]
func DeleteHTTPLogs(w http.ResponseWriter, r *http.Request) {
	startDate := r.URL.Query().Get("start_date")
	endDate := r.URL.Query().Get("end_date")
	var err error
	if startDate != "" && endDate != "" {
		err = telemetry.DeleteLogsByDateRange("http_logs", startDate, endDate)
	} else {
		err = telemetry.DeleteAllHTTPLogs()
	}
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(map[string]string{"status":"success", "message": "HTTP logları temizlendi"})
}

// DeleteEBPFLogs godoc
// @Summary eBPF loglarını temizler
// @Description Çekirdek seviyesindeki (kernel) tüm eBPF süreç loglarını siler
// @Tags telemetry
// @Produce json
// @Param start_date query string false "Baslangic tarihi"
// @Param end_date query string false "Bitis Tarihi"
// @Success 200 {object} map[string]string
// @Router /api/v1/telemetry/ebpf [delete]
func DeleteEBPFLogs(w http.ResponseWriter, r *http.Request) {
	startDate := r.URL.Query().Get("start_date")
	endDate := r.URL.Query().Get("end_date")

	var err error
	if startDate != "" && endDate != "" {
		err = telemetry.DeleteLogsByDateRange("ebpf_logs", startDate, endDate)
	} else {
		err = telemetry.DeleteAlleBPFLogs()
	}
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(map[string]string{"status":"success", "message":"Kernel seviyesinde'ki tüm eBPF logları temizlendi"})
}