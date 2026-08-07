package environments

import (
	"context"
	"io"
	"github.com/HuseyinOzlu/honeypot/pkg/protocol"
)

// Capabilities defines what features a given environment supports.
type Capabilities struct {
	SupportsPTY       bool
	SupportsFileIO    bool
	SupportsKernelEBPF bool
	IsIsolated        bool
	MaxConcurrentVMs  int
}

// Environment defines the interface that all execution targets (Fake, Docker, Firecracker) must implement.
type Environment interface {
	// CreateSession provisions or allocates an instance for an incoming session.
	CreateSession(ctx context.Context, cfg protocol.SessionConfig) (vmID string, err error)

	// AttachStream connects stdin, stdout, and stderr to the allocated environment instance.
	AttachStream(ctx context.Context, sessionID string, stdin io.Reader, stdout, stderr io.Writer) error

	// CollectArtifacts extracts dropped malware/files after or during the session.
	CollectArtifacts(ctx context.Context, sessionID string) ([]string, error)

	// DestroySession terminates and cleans up the instance without leaving residue.
	DestroySession(ctx context.Context, sessionID string) error

	// GetCapabilities returns the features of this environment engine.
	GetCapabilities() Capabilities
}
