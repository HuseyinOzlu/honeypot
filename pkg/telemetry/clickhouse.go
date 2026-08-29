package telemetry

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"

	"github.com/ClickHouse/clickhouse-go/v2"
	"github.com/ClickHouse/clickhouse-go/v2/lib/driver"
)

var DB driver.Conn


func InitClickhouse(addr string, password string) error {
	var err error
	DB, err = clickhouse.Open(&clickhouse.Options{
		Addr: []string{addr},
		Auth: clickhouse.Auth{
		Username: "default",
		Password: password,
	},
	})
	if err != nil {
		return err
	}
	if err := DB.Ping(context.Background()); err != nil {
		return err
	}

	err = DB.Exec(context.Background(),`
		CREATE TABLE IF NOT EXISTS command_logs (
			session_id String,
			ip_address String,
			username String,
			command String,
			output String,
			timestamp DateTime
		) ENGINE = MergeTree()
		ORDER BY (timestamp, session_id)
		TTL timestamp + INTERVAL 3 MONTH DELETE; -- Delete datad older than 3 months!
	`)
	if err != nil {
		return err
	}

	err = DB.Exec(context.Background(),`
		CREATE TABLE IF NOT EXISTS http_logs (
			ip_address String,
			method String,
			path String,
			user_agent String,
			payload String,
			timestamp DateTime
		) ENGINE = MergeTree()
		ORDER BY timestamp;
	`)

	err = DB.Exec(context.Background(),`
		CREATE TABLE IF NOT EXISTS ebpf_logs (
			log String,
			timestamp DateTime
		) ENGINE = MergeTree()
		ORDER BY timestamp;
	`)

	if err != nil {
		return err
	}

	log.Println("Clickhouse aktif ve tablolar hazır!")
	return nil
}

func LogEBPF(logMsg string) {
	GetBroker().Broadcast("ebpf_event", map[string]string{
		"log": logMsg,
	})
	go func(msg string) {
		err := DB.Exec(context.Background(),
			"INSERT INTO ebpf_logs (log, timestamp) VALUES (?, now())",
			msg,
		)
		if err != nil {
			log.Printf("EBPF Log ClickHouse'a yazılamadı: %v", err)
		}
	}(logMsg)
}

func LogCommand(event CommandEvent) {
	GetBroker().Broadcast("ssh_command", event)
	go func(e CommandEvent) {
		err := DB.Exec(context.Background(),
			"INSERT INTO command_logs (session_id, ip_address, username, command, output, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
			e.SessionID,e.IPAddress,e.Username,e.Command,e.Output,e.Timestamp,
		)
		if err != nil {
			log.Printf("ClickHouse'a ulaşılamıyor! Log diske yazılıyor hata: %v", err)
			writeFallbackLog(e)
		}
	}(event)
}

func writeFallbackLog(event CommandEvent){
	// Logs klasörü yoksa oluştur
	if err := os.MkdirAll("/app/logs", 0755); err != nil {
		log.Printf("HATA! logs klasörü oluşturulamadı: %v", err)
	}

	file, err := os.OpenFile("/app/logs/fallback_logs.json", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("HATA! Veriler ClickHouse ve Diske'de yazılamadı: %v", err)
		return
	}
	defer file.Close()

	logData, _ := json.Marshal(event)
	file.Write(append(logData, '\n'))
}

func LogHTTP(event HTTPEvent) {
	GetBroker().Broadcast("http_request", event)
	go func(e HTTPEvent) {
		err := DB.Exec(context.Background(),
			"INSERT INTO http_logs (ip_address, method, path, user_agent, payload, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
			e.IPAddress, e.Method, e.Path, e.UserAgent, e.Payload, e.Timestamp,
		)
		if err != nil {
			log.Printf("HTTP Log ClickHouse'a yazılamadı: %v", err)
		}
	}(event)
}
//? HTTPLog struct for retrieving HTTP logs
type HTTPLog struct {
	IPAddress string `json:"ip_address"`
	Method	  string `json:"method"`
	Path      string `json:"path"`
	UserAgent string `json:"user_agent"`
	Payload	  string `json:"payload"`
	Timestamp string `json:"timestamp"`
}

//? CommandLog struct for retrieving Command Logs
type CommandLog struct {
	SessionID string `json:"session_id"`
	IPAddress string `json:"ip_address"`
	Username  string `json:"username"`
	Command   string `json:"command"`
	Output    string `json:"output"`
	Timestamp string `json:"timestamp"`
}

//? EBPFLog struct for retrieving eBPF logs
type EBPFLog struct {
	Log       string `json:"log"`
	Timestamp string `json:"timestamp"`
}

//? GetHTTPLogs retrieves the latest HTTP logs from ClickHouse
func GetHTTPLogs(limit int) ([]HTTPLog, error) {
	rows, err := DB.Query(context.Background(), "SELECT ip_address, method, path, user_agent, payload, toString(timestamp) FROM http_logs ORDER BY timestamp DESC LIMIT ?", limit)
	if err != nil {
		return nil ,err
	}
	defer rows.Close()

	var logs []HTTPLog
	for rows.Next() {
		var l HTTPLog
		if err := rows.Scan(&l.IPAddress, &l.Method, &l.Path, &l.UserAgent, &l.Payload, &l.Timestamp); err != nil {
			return nil, err
		}
		logs = append(logs, l)
	}
	return logs, nil
}

//? GetCommandLogs retrieves the latest Command logs from ClickHouse
func GetCommandLogs(limit int) ([]CommandLog, error) {
	rows, err := DB.Query(context.Background(), "SELECT session_id, ip_address, username, command, output, toString(timestamp) FROM command_logs ORDER BY timestamp DESC LIMIT ?", limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var logs []CommandLog
	for rows.Next() {
		var l CommandLog
		if err := rows.Scan(&l.SessionID, &l.IPAddress, &l.Username, &l.Command, &l.Output, &l.Timestamp); err != nil {
			return nil, err
		}
		logs = append(logs, l)
	}
	return logs, nil
}

//? GetEBPFLogs retrieves the latest eBPF logs from ClickHouse
func GetEBPFLogs(limit int) ([]EBPFLog, error) {
	rows, err := DB.Query(context.Background(), "SELECT log, toString(timestamp) FROM ebpf_logs ORDER BY timestamp DESC LIMIT ?", limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var logs [] EBPFLog
	for rows.Next() {
		var l EBPFLog
		if err := rows.Scan(&l.Log, &l.Timestamp); err != nil {
			return nil, err
		}
		logs = append(logs, l)
	}
	return logs, nil
}

//? Delete all SSH logs
func DeleteAllCommandLogs() error {
	if DB == nil {
		return nil
	}
	return DB.Exec(context.Background(), "TRUNCATE TABLE command_logs")
}

//? Delete all HTTP logs
func DeleteAllHTTPLogs() error {
	if DB == nil {
		return nil
	}
	return DB.Exec(context.Background(), "TRUCATE TABLE http_logs")
}

//? Delete all eBPF Core
func DeleteAlleBPFLogs() error {
	if DB == nil {
		return nil
	}
	return DB.Exec(context.Background(),"TRUCATE TABLE ebpg_logs")
}

//? Deletes data from the requested table according to the date range!
func DeleteLogsByDateRange(tableName, startDate, endDate string) error {
	if DB == nil {return nil}
	query := fmt.Sprintf("ALTER TABLE %s DELETE WHERE timestamp >= parseDateTimeBestEffort('%s') AND timestamp <= parseDateTimeBestEffort('%s')", tableName, startDate, endDate)
	return DB.Exec(context.Background(), query)
}