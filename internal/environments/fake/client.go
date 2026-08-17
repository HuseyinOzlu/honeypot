package fake

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"strings"
	"time"

	"github.com/HuseyinOzlu/honeypot/internal/environments"
	// TODO: Sabitleri ayarla
	. "github.com/HuseyinOzlu/honeypot/pkg/constants"
	"github.com/HuseyinOzlu/honeypot/pkg/errors"
	"github.com/HuseyinOzlu/honeypot/pkg/protocol"
	"github.com/HuseyinOzlu/honeypot/pkg/telemetry"
	"golang.org/x/term"
	"github.com/HuseyinOzlu/honeypot/pkg/config"
)

type FakeEnvironment struct {
	rpcAddress string
}

func NewFakeEnvironment(rpcAddr string) *FakeEnvironment {
	return &FakeEnvironment {
		rpcAddress: rpcAddr,
	}
}



func (f *FakeEnvironment) CreateSession(ctx context.Context, cfg protocol.SessionConfig) (string, error) {
		return cfg.SessionID, nil
}

func (f *FakeEnvironment) AttachStream(ctx context.Context, sessionID string, stdin io.Reader, stdout, stderr io.Writer) error {
	conn, err := net.Dial("tcp", f.rpcAddress)
	if err != nil {
		errors.LogError(GetMsg(KeyPyVFSError), err)
		return fmt.Errorf(GetMsg(KeyVFSOffline))
	}
	defer conn.Close()

	rw := struct {
		io.Reader
		io.Writer
	}{stdin, stdout}
	terminal := term.NewTerminal(rw, "root@ubuntu:~# ")


	idleTimeout := 10 * time.Minute
	idleTimer := time.NewTimer(idleTimeout)

	go func() {
		<-idleTimer.C
		
		if closer, ok := stdin.(io.Closer); ok {
				stdout.Write([]byte("\r\n[SİSTEM] Çok uzun süre işlem yapmadığınız için balantınız kesildi.\r\n"))
				closer.Close()
			}
	}()
	for {
		cmdLine, err := terminal.ReadLine()
		if err != nil { 
		break
		}
		cmdLine = strings.TrimSpace(cmdLine)
		idleTimer.Reset(idleTimeout)
		if cmdLine == "exit" || cmdLine == "EXİT" || cmdLine == "logout" || cmdLine == "LOGOUT" {
			stdout.Write([]byte("logout\r\n"))
			break
		}
		if cmdLine == "" {
			continue
		}
		reqBytes, _ := json.Marshal(map[string]string{
			"command": cmdLine,
			"token"  : config.AppConfig.PythonVFS.AuthToken,
		})
		conn.Write(append(reqBytes, '\n'))

		respReader := bufio.NewReader(conn)
		resqStr, err := respReader.ReadString('\n')
		if err != nil {
			break 
		}
		var respMap map[string]interface{}
		json.Unmarshal([]byte(resqStr), &respMap)


		/*if output , ok := respMap["output"].(string); ok {
			// satır sonlarına SSH'ın anlayacağı şekle (\r\n) çeviriyoruz
			formattedOutput := strings.ReplaceAll(output, "\n", "\r\n")
			stdout.Write([]byte(formattedOutput))
		}*/
		var finalOutput string
		if output, ok := respMap["output"].(string); ok {
			finalOutput = output
			terminal.Write([]byte(output))
		}

		ip, _ := ctx.Value("hacker_ip").(string)
		user, _ := ctx.Value("hacker_user").(string)
		if ip == "" { ip = "Bilinmiyor"}
		if user == "" { user = "root"}
		
		telemetry.LogCommand(telemetry.CommandEvent{
			SessionID: sessionID,
			IPAddress: ip,
			Username:  user,
			Command:   cmdLine,
			Output:    finalOutput,
			Timestamp: time.Now(),
		})
		
		if cwd, ok := respMap["cwd"].(string); ok {
			terminal.SetPrompt(fmt.Sprintf("root@ubuntu:%s$ ", cwd))
		}
	}
	return nil
}

func (f *FakeEnvironment) CollectArtifacts(ctx context.Context, sessionID string) ([]string, error) {
	return []string{}, nil 
}

func (f *FakeEnvironment) DestroySession(ctx context.Context, sessinID string) error {
	return nil 
}
func (f *FakeEnvironment) GetCapabilities() environments.Capabilities {
	return environments.Capabilities{
		SupportsPTY: true,
		SupportsFileIO: false,
		IsIsolated: false,
		MaxConcurrentVMs: 10000, // Hafif olduğu için 10.000 kişi taşıyabilir!
	}
}
