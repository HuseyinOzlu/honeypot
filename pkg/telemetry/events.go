package telemetry

import "time"


type CommandEvent struct {
	SessionID string    `ch:"session_id"`
	IPAddress string    `ch:"ip_address"`
	Username  string    `ch:"username"`
	Command   string    `ch:"command"`
	Output    string    `ch:"output"`
	Timestamp time.Time `ch:"timestamp"`
}
