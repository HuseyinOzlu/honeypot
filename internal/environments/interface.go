package environments

import (
	"context"
	"io"
	"github.com/HuseyinOzlu/honeypot/pkg/protocol"
)

type Capabilities struct {
	SupportsPTY       bool
	SupportsFileIO    bool
	SupportsKernelEBPF bool
	IsIsolated        bool
	MaxConcurrentVMs  int
}

type Environment interface {
	CreateSession(ctx context.Context, cfg protocol.SessionConfig) (vmID string, err error)

	AttachStream(ctx context.Context, sessionID string, stdin io.Reader, stdout, stderr io.Writer) error

	CollectArtifacts(ctx context.Context, sessionID string) ([]string, error)

	DestroySession(ctx context.Context, sessionID string) error

	GetCapabilities() Capabilities
}
