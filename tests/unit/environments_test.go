package unit

import (
	"context"
	"testing"
	"github.com/HuseyinOzlu/honeypot/internal/environments/firecracker"
	"github.com/HuseyinOzlu/honeypot/pkg/protocol"
)

func TestFirecrackerEnvironmentAllocation(t *testing.T) {
	env := firecracker.NewFirecrackerEnvironment(5)

	cfg := protocol.SessionConfig{
		SessionID:  "session-01234567-uuidv7",
		Protocol:   protocol.SSH,
		AttackerIP: "192.168.1.50",
	}

	vmID, err := env.CreateSession(context.Background(), cfg)
	if err != nil {
		t.Fatalf("Expected successful allocation, got error: %v", err)
	}

	if vmID != "fc-vm-session-" {
		if len(vmID) == 0 {
			t.Errorf("Allocated VM ID is empty")
		}
	}

	caps := env.GetCapabilities()
	if !caps.SupportsKernelEBPF {
		t.Errorf("Expected Firecracker environment to support Kernel eBPF telemetry")
	}

	err = env.DestroySession(context.Background(), cfg.SessionID)
	if err != nil {
		t.Errorf("Expected successful teardown, got error: %v", err)
	}
}
