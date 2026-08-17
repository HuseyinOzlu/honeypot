package ssh
import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"log/slog"
	"net"
	"os"
	"time"

	"github.com/HuseyinOzlu/honeypot/internal/environments/fake" 
	. "github.com/HuseyinOzlu/honeypot/pkg/config"
	. "github.com/HuseyinOzlu/honeypot/pkg/constants" 
	"github.com/HuseyinOzlu/honeypot/pkg/errors"
	"golang.org/x/crypto/ssh"
)

// TODO: Ağ güvenliği protokollerini buraya entegre etmeye çalışacağım,SSH handshake,
type Server struct {
	hostSigner ssh.Signer
}

func NewServer() *Server {
	return &Server{}
}
func (s *Server) Start(addr string) error {

	signer, err := loadOrGenerateKey(AppConfig.Server.SSHKeyPath)
	if err != nil {
		errors.LogError("SSH Kimlik Dosyası okunamadı", err)
		return err
	}
	s.hostSigner = signer

	listener, err := net.Listen("tcp", addr)
	if err != nil {
		errors.LogError(GetMsg(KeyPortListenFailed), err)
		return err
	}
	slog.Info(GetMsg(KeySSHHoneypotListening), "port", addr)

	for {
		conn, err := listener.Accept()
		if err != nil {
			errors.LogError(GetMsg(KeyConnectionNotAcccepted), err)
			continue 
		}
		go s.handleConnection(conn)

	}
}

// TODO: key kontrolü
func (s *Server) handleConnection(conn net.Conn) {
	slog.Info(GetMsg(KeyConnectionCatched), "ip", conn.RemoteAddr().String())
	defer conn.Close()
	config := &ssh.ServerConfig{
		PasswordCallback: func(c ssh.ConnMetadata, pass []byte) (*ssh.Permissions, error) {
			slog.Info(GetMsg(KeyTryingPasswd), "user", c.User(), "password", string(pass))
			return nil, nil
		},
	}
	config.AddHostKey(s.hostSigner)
	//TODO: Rsq key oluşturucaz
	sshConn, chans, reqs, err := ssh.NewServerConn(conn, config)
	if err != nil {
		slog.Error(GetMsg(KeySSHHandshakeError), "error", err)
		return
	}
	slog.Info("SSH Version: ", string(sshConn.ClientVersion()), "\n")
	go ssh.DiscardRequests(reqs)
	for newChannel := range chans {
		if newChannel.ChannelType() == "session" {
			channel, request, err := newChannel.Accept()
			if err != nil {
				errors.LogError(GetMsg(KeyChannelIsNotAccepted), err)
				continue
			}
			go func(in <-chan *ssh.Request) {
				for req := range in {
					if req.Type == "pty-req" || req.Type == "shell" {
						req.Reply(true, nil)
					} else {
						req.Reply(false, nil)
					}
				}
			}(request)
			fakeEnv := fake.NewFakeEnvironment(AppConfig.PythonVFS.Address)
			hackerIP := sshConn.RemoteAddr().String() // Örn: 192.168.1.15:54321
			hackerUser := sshConn.User()
			
			ctx := context.WithValue(context.Background(), "hacker_ip", hackerIP)
			ctx = context.WithValue(ctx, "hacker_user", hackerUser)

			uniqueSessionID := fmt.Sprintf("sess-%d", time.Now().UnixNano())

			err = fakeEnv.AttachStream(ctx, uniqueSessionID, channel, channel, channel)
			if err != nil {
				channel.Write([]byte("\r\nSistemdeki geçici bir arıza var. Lütfen daha sonra tekrar deneyiniz.\r\n"))
				channel.Close()
			}
			channel.Close()
			} else {
			newChannel.Reject(ssh.UnknownChannelType, "Just terminal conneciton supported")
		}

	}

}
// Key üretmesi için yada sistemde zaten kayıtlıysa onu kullanmak için
func loadOrGenerateKey(filePath string) (ssh.Signer, error) {
	if keyBytes, err := os.ReadFile(filePath); err == nil {
		return ssh.ParsePrivateKey(keyBytes) 
	}

	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, err
	}

	// Üretilen anahtarı standart Pem formatına çevir
	privateKeyPEM := &pem.Block{
		Type: "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(privateKey),
	}
	keyBytes := pem.EncodeToMemory(privateKeyPEM)

	// Anahtarı diske kaydettik (sadece kurucu okuyabilir (0600))
	err = os.WriteFile(filePath, keyBytes, 0600)
	if err != nil {
		return nil, err
	}

	return ssh.ParsePrivateKey(keyBytes)
}