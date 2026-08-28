package docker

import (
	"context"
	"io"
	"log"

	"github.com/HuseyinOzlu/honeypot/internal/environments"
	"github.com/HuseyinOzlu/honeypot/pkg/protocol"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/network"
	"github.com/docker/docker/client"
)

// @Interface
type DockerEnvironment struct {
	cli *client.Client
}

func NewDockerEnvironment() (*DockerEnvironment, error) {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		return nil, err
	}

	// Docker daemon ayakta mı diye Ping atıyoruz
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
		NetworkMode: "none", //internet çıkışı kestik
		Resources: container.Resources{
			Memory: 256 * 1024 * 1024, // max: 256 MB RAM
			PidsLimit: func() *int64 { i := int64(50); return &i} (), // Fork bomb engeli
		},
		CapDrop: []string{"ALL"},
	},
	&network.NetworkingConfig{},
	nil,
	"", //ismi otamatik koysun
	)

	if err != nil {
	return "", err
	}
	return resp.ID, nil
}

// SSH isteğini Konteynere bağlamak için
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
	defer resp.Close()

	//? Stdin (SSH'den gelenler) arka planda Docker'a aksın
	go io.Copy(resp.Conn, stdin)

	//? Docker'ın çıktısı direkt kullanıcıya aksın.
	//? Hacker "exit" yazdığında bash kapanır, Reader EOF döner ve fonksiyon biter!
	io.Copy(stdout, resp.Reader)

	return nil
}

func (d *DockerEnvironment) DestroySession(ctx context.Context, sessionID string) error {
	log.Printf("Hacker çıktı, hücre imha ediliyor: %s", sessionID)
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
