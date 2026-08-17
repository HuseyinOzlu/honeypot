package sessions

import (
	"time"
)

type SessionStatus string

const (
	StatusInitializing SessionStatus = "INITIALIZING"
	StatusActive       SessionStatus = "ACTIVE"
	StatusPaused       SessionStatus = "PAUSED"
	StatusTerminated   SessionStatus = "TERMINATED"
)

type Session struct {
	SessionID     string        `json:"session_id"`
	VMID          string        `json:"vm_id"`
	Protocol      string        `json:"protocol"`
	AttackerIP    string        `json:"attacker_ip"`
	AttackerPort  int           `json:"attacker_port"`
	Username      string        `json:"username"`
	Password      string        `json:"password"`
	EnvType       string        `json:"env_type"`
	Status        SessionStatus `json:"status"`
	StartTime     time.Time     `json:"start_time"`
	EndTime       *time.Time    `json:"end_time,omitempty"`
	DurationMS    int64         `json:"duration_ms"`
	ClientVersion string        `json:"client_version"`
}
