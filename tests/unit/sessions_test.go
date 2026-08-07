package unit

import (
	"context"
	"testing"
	"time"
	"github.com/HuseyinOzlu/honeypot/internal/sessions"
	"github.com/HuseyinOzlu/honeypot/pkg/protocol"
)

func TestSessionManagerLifecycle(t *testing.T) {
	mgr := sessions.NewManager()
	cfg := protocol.SessionConfig{
		SessionID:    "test-session-uuidv7-99",
		Protocol:     protocol.SSH,
		AttackerIP:   "10.0.0.99",
		AttackerPort: 54321,
		EnvType:      protocol.FirecrackerEnv,
	}

	session, err := mgr.CreateSession(context.Background(), cfg)
	if err != nil {
		t.Fatalf("Failed to create session: %v", err)
	}

	if session.Status != sessions.StatusActive {
		t.Errorf("Expected session status %s, got %s", sessions.StatusActive, session.Status)
	}

	// Verify session retrieval
	retrieved, exists := mgr.GetSession(cfg.SessionID)
	if !exists || retrieved.VMID != session.VMID {
		t.Errorf("Failed to correctly retrieve created session from manager map")
	}

	// Simulate short interaction
	time.Sleep(10 * time.Millisecond)

	err = mgr.TerminateSession(context.Background(), cfg.SessionID)
	if err != nil {
		t.Fatalf("Failed to terminate session: %v", err)
	}

	if retrieved.Status != sessions.StatusTerminated {
		t.Errorf("Expected session status to be %s after termination, got %s", sessions.StatusTerminated, retrieved.Status)
	}

	if retrieved.DurationMS <= 0 {
		t.Errorf("Expected positive session duration calculation, got %d ms", retrieved.DurationMS)
	}
}
