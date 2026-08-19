package ai

import (
	"context"
	"io"
	"strings"

	"github.com/HuseyinOzlu/honeypot/internal/environments"
	"github.com/HuseyinOzlu/honeypot/pkg/protocol"

	"github.com/google/generative-ai-go/genai"
	"golang.org/x/crypto/ssh/terminal"
	"google.golang.org/api/option"
)

type AIEnvironment struct {
	client *genai.Client
	model  *genai.GenerativeModel
}

type readWriter struct {
	io.Reader
	io.Writer
}

func NewAIEnvironment(apiKey string) (*AIEnvironment, error) {
	ctx := context.Background()
	client, err := genai.NewClient(ctx, option.WithAPIKey(apiKey))
	if err != nil {
		return nil, err
	}
	
	model := client.GenerativeModel("gemini-1.5-flash")
	model.SystemInstruction = &genai.Content{
		Parts: []genai.Part{
			genai.Text("Sen bir Ubuntu 22.04 LTS terminalisin. Kullanıcı sana komutlar gönderecek. Sen sadece o komut çalıştırıldığında terminalde görünecek olan ÇIKTIYI (output) vereceksin. Hiçbir açıklama yapma, Markdown kullanma, sadece saf terminal çıktısını ver. Eğer geçersiz bir komutsa bash hata mesajı üret."),
		},
	}

	return &AIEnvironment{
		client: client,
		model:  model,
	}, nil
}

func (a *AIEnvironment) CreateSession(ctx context.Context, cfg protocol.SessionConfig) (string, error) {
	return "ai-session-1", nil
}

func (a *AIEnvironment) AttachStream(ctx context.Context, sessionID string, stdin io.Reader, stdout, stderr io.Writer) error {
	term := terminal.NewTerminal(readWriter{stdin, stdout}, "root@ubuntu:~# ")

	for {
		cmdLine, err := term.ReadLine()
		if err != nil {
			if err == io.EOF {
				break
			}
			return err
		}

		cmdLine = strings.TrimSpace(cmdLine)
		if cmdLine == "" {
			continue
		}
		if cmdLine == "exit" || cmdLine == "logout" {
			stdout.Write([]byte("logout\r\n"))
			break
		}

		resp, err := a.model.GenerateContent(ctx, genai.Text(cmdLine))
		if err != nil {
			stdout.Write([]byte("bash: fork: retry: Resource temporarily unavailable\r\n"))
			continue
		}

		if len(resp.Candidates) > 0 && len(resp.Candidates[0].Content.Parts) > 0 {
			if text, ok := resp.Candidates[0].Content.Parts[0].(genai.Text); ok {
				out := strings.ReplaceAll(string(text), "\n", "\r\n")
				if !strings.HasSuffix(out, "\r\n") {
					out += "\r\n"
				}
				stdout.Write([]byte(out))
			}
		}
	}
	return nil
}

func (a *AIEnvironment) DestroySession(ctx context.Context, sessionID string) error {
	return nil
}

func (a *AIEnvironment) CollectArtifacts(ctx context.Context, sessionID string) ([]string, error) {
	return []string{}, nil
}

func (a *AIEnvironment) GetCapabilities() environments.Capabilities {
	return environments.Capabilities{
		SupportsPTY:      true,
		SupportsFileIO:   false,
		IsIsolated:       true,
		MaxConcurrentVMs: 1000,
	}
}