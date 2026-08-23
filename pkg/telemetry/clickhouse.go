package telemetry
import (
	"context"
	"log"
	"encoding/json"
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
		ORDER BY (timestamp, session_id);
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