package telemetry

import "time"


type CommandEvent struct {
	SessionID string    `ch:"session_id" json:"session_id`
	IPAddress string    `ch:"ip_address" json:"ip"`
	Username  string    `ch:"username" json:"username"`
	Command   string    `ch:"command" json:"command"`
	Output    string    `ch:"output" json:"output"`
	Timestamp time.Time `ch:"timestamp" json:"timestamp"`
}

type HTTPEvent struct {
	IPAddress string    `ch:"ip_address" json:"ip"`
	Method    string    `ch:"method" json:"method"`
	Path      string    `ch:"path" json:"path"`
	UserAgent string    `ch:"user_agent" json:"user_agent"`
	Payload   string    `ch:"payload" json:"payload"`
	Timestamp time.Time `ch:"timestamp" json:"timestamp"`
}
