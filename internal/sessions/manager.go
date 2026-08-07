package sessions

import (
	"context"
	"fmt"
	"sync"
	"time"
	"log/slog"
	"github.com/HuseyinOzlu/honeypot/internal/environments"
	"github.com/HuseyinOzlu/honeypot/internal/environments/firecracker"
	"github.com/HuseyinOzlu/honeypot/pkg/protocol"
)

// Manager orchestrates session creation, environment selection, and teardown.
type Manager struct {
	mu           sync.RWMutex
	sessions     map[string]*Session
	envs         map[string]environments.Environment
}

// NewManager initializes the Session Manager daemon engine with available environments.
func NewManager() *Manager {
	m := &Manager{
		sessions: make(map[string]*Session),
		envs:     make(map[string]environments.Environment),
	}
	// Register environments
	m.envs[protocol.FirecrackerEnv] = firecracker.NewFirecrackerEnvironment(5)
	return m
}

// CreateSession allocates a VM and registers a new tracking session.
func (m *Manager) CreateSession(ctx context.Context, cfg protocol.SessionConfig) (*Session, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	env, exists := m.envs[cfg.EnvType]
	if !exists {
		// Default fallback
		env = m.envs[protocol.FirecrackerEnv]
	}

	vmID, err := env.CreateSession(ctx, cfg)
	if err != nil {
		return nil, fmt.Errorf("failed to allocate environment session: %w", err)
	}

	session := &Session{
		SessionID:    cfg.SessionID,
		VMID:         vmID,
		Protocol:     cfg.Protocol,
		AttackerIP:   cfg.AttackerIP,
		AttackerPort: cfg.AttackerPort,
		Username:     cfg.Username,
		Password:     cfg.Password,
		EnvType:      cfg.EnvType,
		Status:       StatusActive,
		StartTime:    time.Now().UTC(),
	}

	m.sessions[cfg.SessionID] = session
	slog.Info("Session created successfully", "session_id", session.SessionID, "vm_id", session.VMID)
	return session, nil
}

// TerminateSession destroys the environment and finalizes telemetry metrics.
func (m *Manager) TerminateSession(ctx context.Context, sessionID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	session, exists := m.sessions[sessionID]
	if !exists {
		return fmt.Errorf("session %s not found", sessionID)
	}

	now := time.Now().UTC()
	session.EndTime = &now
	session.DurationMS = now.Sub(session.StartTime).Milliseconds()
	session.Status = StatusTerminated

	if env, ok := m.envs[session.EnvType]; ok {
		_ = env.DestroySession(ctx, sessionID)
	}

	slog.Info("Session terminated and cleaned up", "session_id", sessionID, "duration_ms", session.DurationMS)
	return nil
}

// GetSession retrieves session details safely.
func (m *Manager) GetSession(sessionID string) (*Session, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	s, ok := m.sessions[sessionID]
	return s, ok
}
