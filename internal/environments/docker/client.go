package docker

import (
	"context"
	"io"
	"log"
	"sync"
	"time"

	"github.com/HuseyinOzlu/honeypot/internal/environments"
	"github.com/HuseyinOzlu/honeypot/pkg/protocol"
	"github.com/HuseyinOzlu/honeypot/pkg/telemetry"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/network"
	"github.com/docker/docker/client"
)

type SessionSniffer struct {
	sessionID string
	ip        string
	user      string
	lastCmd   string
	cmdBuf    []byte
	outBuf    []byte
	timer     *time.Timer
	mu        sync.Mutex
}

func (s *SessionSniffer) Write(p []byte) (n int, err error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if len(s.outBuf) < 10000 {
		s.outBuf = append(s.outBuf, p...)
	}
	return len(p), nil
}

func (s *SessionSniffer) flush() {
	if s.lastCmd != "" {
		telemetry.LogCommand(telemetry.CommandEvent{
			SessionID: s.sessionID,
			Username:  s.user,
			IPAddress: s.ip,
			Command:   s.lastCmd,
			Output:    string(s.outBuf),
			Timestamp: time.Now(),
		})
		s.lastCmd = ""
		s.outBuf = s.outBuf[:0]
	}
}

func (s *SessionSniffer) ReadFrom(p []byte, n int) {
	s.mu.Lock()
	defer s.mu.Unlock()

	for i := 0; i < n; i++ {
		c := p[i]
		if c == '\r' || c == '\n' {
			if len(s.cmdBuf) > 0 {
				cmd := string(s.cmdBuf)
				
				// Mevcut bir timer varsa durdur ve onceki komutu aninda flushla
				if s.timer != nil {
					s.timer.Stop()
					s.flush()
				}
				
				s.lastCmd = cmd
				s.outBuf = s.outBuf[:0]
				s.cmdBuf = s.cmdBuf[:0]
				
				// 500ms bekle, cikti (output) toplaninca logla
				s.timer = time.AfterFunc(500*time.Millisecond, func() {
					s.mu.Lock()
					defer s.mu.Unlock()
					s.flush()
				})
			}
		} else if c == '\b' || c == 127 { // Backspace
			if len(s.cmdBuf) > 0 {
				s.cmdBuf = s.cmdBuf[:len(s.cmdBuf)-1]
			}
		} else if c >= 32 && c <= 126 { // Readable chars
			s.cmdBuf = append(s.cmdBuf, c)
		}
	}
}

type SnifferReader struct {
	r       io.Reader
	sniffer *SessionSniffer
}

func (sr *SnifferReader) Read(p []byte) (n int, err error) {
	n, err = sr.r.Read(p)
	if n > 0 {
		sr.sniffer.ReadFrom(p, n)
	}
	return n, err
}

type SnifferWriter struct {
	w       io.Writer
	sniffer *SessionSniffer
}

func (sw *SnifferWriter) Write(p []byte) (n int, err error) {
	sw.sniffer.Write(p)
	return sw.w.Write(p)
}

// @Interface
type DockerEnvironment struct {
	cli *client.Client
}

func NewDockerEnvironment() (*DockerEnvironment, error) {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		return nil, err
	}

	// Docker daemon ayakta mi diye Ping atiyoruz
	_, err = cli.Ping(context.Background())
	if err != nil {
		return nil, err
	}

	return &DockerEnvironment{cli: cli}, nil
}

func (d *DockerEnvironment) CreateSession(ctx context.Context, cfg protocol.SessionConfig) (string, error) {
	resp, err := d.cli.ContainerCreate(ctx,
	&container.Config{
		Image:			"honeypot-victim:latest",
		Cmd:			[]string{"/bin/bash"},
		Tty: 			true,
		AttachStdin: 	true,
		AttachStdout: 	true,
		AttachStderr: 	true,
		OpenStdin: 		true,
	},
	&container.HostConfig{
		NetworkMode: "none", //internet cikisini kestik
		Resources: container.Resources{
			Memory: 256 * 1024 * 1024, // max: 256 MB RAM
			PidsLimit: func() *int64 { i := int64(50); return &i} (), // Fork bomb engeli
		},
		CapDrop: []string{"ALL"},
	},
	&network.NetworkingConfig{},
	nil,
	"", //ismi otomatik koysun
	)

	if err != nil {
	return "", err
	}
	return resp.ID, nil
}

// SSH istegini Konteynere baglamak icin
func (d *DockerEnvironment) AttachStream(ctx context.Context, sessionID string, stdin io.Reader, stdout, stderr io.Writer) error {
	if err := d.cli.ContainerStart(ctx, sessionID, container.StartOptions{}); err != nil {
		return err
	}
	resp, err := d.cli.ContainerAttach(ctx, sessionID, container.AttachOptions{
		Stream: true,
		Stdin: 	true,
		Stdout: true,
		Stderr: true,
	})
	if err != nil {
		return err
	}
	
	ip, _ := ctx.Value("hacker_ip").(string)
	user, _ := ctx.Value("hacker_user").(string)
	if ip == "" { ip = "unknown" }
	if user == "" { user = "root" }

	sessionSniffer := &SessionSniffer{
		sessionID: sessionID,
		ip:        ip,
		user:      user,
	}

	snifferReader := &SnifferReader{r: stdin, sniffer: sessionSniffer}
	snifferWriter := &SnifferWriter{w: stdout, sniffer: sessionSniffer}

	defer func() {
		sessionSniffer.mu.Lock()
		if sessionSniffer.timer != nil {
			sessionSniffer.timer.Stop()
		}
		sessionSniffer.flush()
		sessionSniffer.mu.Unlock()
		resp.Close()
	}()

	//? Stdin (SSH'den gelenler) araya SnifferReader koyarak Docker'a aksin
	go io.Copy(resp.Conn, snifferReader)

	//? Docker'in ciktisi direkt SnifferWriter uzerinden kullaniciya aksin
	io.Copy(snifferWriter, resp.Reader)

	return nil
}

func (d *DockerEnvironment) DestroySession(ctx context.Context, sessionID string) error {
	log.Printf("Hacker cikti, hucre imha ediliyor: %s", sessionID)
	return d.cli.ContainerRemove(ctx, sessionID, container.RemoveOptions{
		Force: true,
	})
}


func (d *DockerEnvironment) CollectArtifacts(ctx context.Context, sessionID string) ([]string, error) {
	return []string{}, nil
}
func (d *DockerEnvironment) GetCapabilities() environments.Capabilities {
	return environments.Capabilities {
		SupportsPTY:		true,
		SupportsFileIO: 	true,
		IsIsolated:			true,
		MaxConcurrentVMs: 	10,
	}
}
