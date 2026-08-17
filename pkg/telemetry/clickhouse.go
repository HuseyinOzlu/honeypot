package telemetry
import (
	"context"
	"log"
	"github.com/ClickHouse/clickhouse-go/v2"
	"github.com/ClickHouse/clickhouse-go/v2/lib/driver"
)

var DB driver.Conn


func InitClickhouse(addr string) error {
	var err error
	DB, err = clickhouse.Open(&clickhouse.Options{
		Addr: []string{addr},
		Auth: clickhouse.Auth{
		Username: "default",
		Password: "123456",
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
	`)

	if err != nil {
		return err
	}

	log.Println("Clickhouse aktif ve tablolar hazır!")
	return nil
}

func LogCommand(event CommandEvent) {
	go func(e CommandEvent) {
		err := DB.Exec(context.Background(),
			"INSERT INTO command_logs (session_id, ip_address, username, command, output, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
			e.SessionID,e.IPAddress,e.Username,e.Command,e.Output,e.Timestamp,
		)
		if err != nil {
			log.Printf("Telemetry kayıt hatası: %v", err)
		}
	}(event)
}