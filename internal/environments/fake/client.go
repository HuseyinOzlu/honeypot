package fake

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"strings"

	"github.com/HuseyinOzlu/honeypot/internal/environments"	
	// TODO: Sabitleri ayarla 
	_ "github.com/HuseyinOzlu/honeypot/pkg/constants"
	"github.com/HuseyinOzlu/honeypot/pkg/errors"
	"github.com/HuseyinOzlu/honeypot/pkg/protocol"	
)

// FakeEnvironment, Python'daki (server.py) VFS motoruyla konuşan Go istemcisidir.
type FakeEnvironment struct {
	rpcAddress string
}

// NewFakeEnvironment, yeni bir köprü oluşturur
func NewFakeEnvironment(rpcAddr string) *FakeEnvironment {
	return &FakeEnvironment {
		rpcAddress: rpcAddr,
	}
}



func (f *FakeEnvironment) CreateSession(ctx context.Context, cfg protocol.SessionConfig) (string, error) {
		// Fake VFS için özel bir sanal makine (Firecracker gibi) ayağa kaldırmaya gerek yok
		// Direkt Python sunucusuna bağlanacağız.
		return cfg.SessionID, nil
}

// İşte Büyüyü burda gerçekleştiricez
func (f *FakeEnvironment) AttachStream(ctx context.Context, sessionID string, stdin io.Reader, stdout, stderr io.Writer) error {
	// 1. Python Mutfak sunucusuna (TCP 6000) bağlan!
	conn, err := net.Dial("tcp", f.rpcAddress)
	if err != nil {
		errors.LogError("Python VFS sunucusuna ulaşılamadı", err)
		return fmt.Errorf("vfs offline")
	}
	defer conn.Close()

	// 2. Hacker'ın klavyesini (stdin) dinlemek için bir Scanner oluştur
	scanner := bufio.NewScanner(stdin)

	// 3. Hacker bir şeyler yazıp enter a basana kadar bekle (sonsuz döngü)
	for scanner.Scan() {
		cmdLine := strings.TrimSpace(scanner.Text())

		// Eğer hacker "exit" yazarsa, bağlantıyı kopar ve tüneli kapat"
		if cmdLine == "exit" || cmdLine == "EXİT" || cmdLine == "logout" || cmdLine == "LOGOUT" {
			stdout.Write([]byte("logout\r\n"))
			break
		}
		// 4. Hacker'ın yazdığı komutu JSON'a çevir (Paketle)
		reqBytes, _ := json.Marshal(map[string]string{"command": cmdLine})

		// 5. JSON Paketini Python'a fırlat!
		conn.Write(append(reqBytes, '\n'))

		// 6. Python'dan gelen cevabı bekle ve oku
		respReader := bufio.NewReader(conn)
		resqStr, err := respReader.ReadString('\n')
		if err != nil {
			break // Python çöktüyse döngüden çık
		}

		// 7. Gelen JSON cevabını aç
		var respMap map[string]interface{}
		json.Unmarshal([]byte(resqStr), &respMap)

		// 8. Python'un ürettiği sahte çıktıyı Hacker'ın ekranına (stdout) bas!
		if output , ok := respMap["output"].(string); ok {
			// satır sonlarına SSH'ın anlayacağı şekle (\r\n) çeviriyoruz
			formattedOutput := strings.ReplaceAll(output, "\n", "\r\n")
			stdout.Write([]byte(formattedOutput))
		}
		// Yeni komut için terminalde $ işaretini tekrar gösteriyoruz
		if cwd, ok := respMap["output"].(string); ok {
			stdout.Write([]byte(fmt.Sprintf("\r\nroot@ubuntu:%s$ ",cwd)))
		} else {
			stdout.Write([]byte("\r\n$ "))
		}
	}
	return nil
}

func (f *FakeEnvironment) CollectArtifacts(ctx context.Context, sessionID string) ([]string, error) {
	return []string{}, nil // şimdilik boş dön
}

func (f *FakeEnvironment) DestroySession(ctx context.Context, sessinID string) error {
	return nil // Temizlenecek bir şey yok
}
func (f *FakeEnvironment) GetCapabilities() environments.Capabilities {
	return environments.Capabilities{
		SupportsPTY: true,
		SupportsFileIO: false,
		IsIsolated: false,
		MaxConcurrentVMs: 10000, // Hafif olduğu için 10.000 kişi taşıyabilir!
	}
}
