package ssh

//Burası SSH loglarını, handshake, key kontrolü gibi işlemleri yapacak olan ana yapı yani giriş yakalayan kapı
import (
	"crypto/rand"
	"crypto/rsa"
	"log/slog"
	"net"
	
	. "github.com/HuseyinOzlu/honeypot/pkg/constants" // başına const yazmamak için
	"github.com/HuseyinOzlu/honeypot/pkg/errors"
	"golang.org/x/crypto/ssh"
	"context"
	"github.com/HuseyinOzlu/honeypot/internal/environments/fake" // Python ile haberleşmesi
)

// TODO: Ağ güvenliği protokollerini buraya entegre etmeye çalışacağım,SSH handshake,
type Server struct {
	hostSigner ssh.Signer
}

func NewServer() *Server {
	return &Server{}
}
func (s *Server) Start(addr string) error {
	//RSA Key Olusturma
	slog.Info(GetMsg(KeyFakeSSHKey))
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		errors.LogError(GetMsg(KeySSHKeyGenFailed), err)
		return err
	}
	hostSigner, err := ssh.NewSignerFromKey(privateKey)
	if err != nil {
		errors.LogError(GetMsg(KeyErrorSignerFromKey), err)
		return err
	}
	s.hostSigner = hostSigner

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
			continue // bir hata oldugu zaman döngüden çıkmasın diye
		}
		go s.handleConnection(conn)

	}
}

// -TODO: SSH username ve şifre sorgusu yazıcaksın
// -TODO: SSH handshake -
// TODO: key kontrolü
func (s *Server) handleConnection(conn net.Conn) {
	slog.Info(GetMsg(KeyConnectionCatched), "ip", conn.RemoteAddr().String())
	defer conn.Close()
	config := &ssh.ServerConfig{
		PasswordCallback: func(c ssh.ConnMetadata, pass []byte) (*ssh.Permissions, error) {
			slog.Info(GetMsg(KeyTryingPasswd), "user", c.User(), "password", string(pass))
			return nil, nil // Şifreyi doğru kabul etmek için hata girmedik
		},
	}
	// RSA yolladık ki güvenli gibi görünsün
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
			// Kanalı onaylayıp içeri alıcaz
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
			//Birleştirdik
			//1. Python Köprüsünü ayağa kaldır (6000 portunda)
			fakeEnv := fake.NewFakeEnvironment("127.0.0.1:6000")

			// 2. Hacker'ın ekranını (channel) doğrudan mutfağa bağla
			// SSH channel hem io.Reader hem de io.Writer'dır!
			err = fakeEnv.AttachStream(context.Background(), "test-session", channel, channel, channel)
			if err != nil {
				channel.Write([]byte("\r\nSistemdeki geçici bir arıza var. Lütfen daha sonra tekrar deneyiniz.\r\n"))
				channel.Close()
			}
			} else {
			newChannel.Reject(ssh.UnknownChannelType, "Just terminal conneciton supported")
		}

	}

}
