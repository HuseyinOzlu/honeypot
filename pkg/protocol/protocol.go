package protocol

const (
	SSH  = "SSH"
	HTTP = "HTTP"
	TLS  = "TLS"
)

const (
	FirecrackerEnv = "firecracker"
	DockerEnv      = "docker"
	FakeEnv        = "fake"
)

type SessionConfig struct {
	SessionID   string
	Protocol    string
	AttackerIP  string
	AttackerPort int
	EnvType     string
	Username    string
	Password    string
}
