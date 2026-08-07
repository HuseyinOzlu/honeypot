package protocol

// Protocol constants supported by the edge gateway.
const (
	SSH  = "SSH"
	HTTP = "HTTP"
	TLS  = "TLS"
)

// EnvironmentType constants supported by the session manager.
const (
	FirecrackerEnv = "firecracker"
	DockerEnv      = "docker"
	FakeEnv        = "fake"
)

// SessionConfig defines options required to spin up or connect to a target environment.
type SessionConfig struct {
	SessionID   string
	Protocol    string
	AttackerIP  string
	AttackerPort int
	EnvType     string
	Username    string
	Password    string
}
