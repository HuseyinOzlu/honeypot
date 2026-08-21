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

type HTTPEvent struct {
	IPAddress string    `ch:"ip_address"`
	Method    string    `ch:"method"`
	Path      string    `ch:"path"`
	UserAgent string    `ch:"user_agent"`
	Payload   string    `ch:"payload"`
	Timestamp time.Time `ch:"timestamp"`
}
