package constants

type Language string
type MessageKey string

const (
	TR Language = "tr"
	EN Language = "en"
)

var ActiveLanguage Language = EN

func SetLanguage(lang Language) {
	ActiveLanguage = lang
}

const (
	// ERRORS:
	KeySSHListenFailed        MessageKey = "SSH_LISTEN_FAILED"
	KeySSHKeyGenFailed        MessageKey = "SSH_KEY_GEN_FAILED"
	KeySSHHandshakeError      MessageKey = "SSH_HANDSHAKE_ERROR"
	KeyErrorSignerFromKey     MessageKey = "SIGNER_ERROR_KEY"
	KeyPortListenFailed       MessageKey = "PORT_LISTEN_FAILED"
	KeyConnectionNotAcccepted MessageKey = "CONN_NOT_ACCEPTED"
	KeyChannelIsNotAccepted   MessageKey = "CHANNEL_IS_NOT_ACCEPTED"

	// INFO:
	KeySSHHoneypotListening   MessageKey = "SSH_LISTENING"
	KeyClientConnected        MessageKey = "CLIENT_CONNECTED"
	KeyConnectionCatched      MessageKey = "NEW_CONNECTION_CATCHED"
	KeyFakeSSHKey             MessageKey = "FAKE_SSH_KEY_GENERATED"

	// Hacker trying
	KeyTryingPasswd 		  MessageKey = "TRYING_PASSWORD"
	KeyWantToOpen   		  MessageKey = "WANT_TO_OPEN"
)

var Messages = map[Language]map[MessageKey]string{
	// Türkçe Paket
	TR: {
		// Hatalar
		KeySSHListenFailed:        "SSH sunucusu belirtilen portta dinlenemedi",
		KeySSHKeyGenFailed:        "SSH RSA host anahtarı üretilemedi",
		KeySSHHandshakeError:      "SSH Handshake başarısız oldu (Tarayıcı veya Nmap olabilir)",
		KeyErrorSignerFromKey:     "Anahtar imzalama başarısız oldu",
		KeyPortListenFailed:       "Port dinlenemedi",
		KeyConnectionNotAcccepted: "Bağlantı Kabul edilmedi",
		KeyChannelIsNotAccepted:   "Kanal kabul edilmedi ve gönderilmedi",

		// Bilgi
		KeyConnectionCatched:      "Yeni bağlantı yakalandı",
		KeySSHHoneypotListening:   "SSH Honeypot portunda dinleniyor",
		KeyFakeSSHKey:             "Sahte SSH kimlik Kartı (RSA 2048) bellekte Üretiliyor...",
		KeyClientConnected:        "Yeni TCP bağlantısı yakalandı",

		// Hacker denemeleri
		KeyWantToOpen:   			"Komut Satırı, pty ve x11 açmak istiyor",
		KeyTryingPasswd: 			"Şifre Deneniyor",


	},
	// English Pack
	EN: {
		// Errors
		KeySSHListenFailed:        "SSH server failed to listen on the specified port",
		KeySSHKeyGenFailed:        "Failed to generate SSH RSA host key",
		KeySSHHandshakeError:      "SSH Handshake failed (Browser or Nmap scanner)",
		KeyErrorSignerFromKey:     "Signer from key failed",
		KeyPortListenFailed:       "Port did not listen",
		KeyConnectionNotAcccepted: "Connection not Accepted",
		KeyChannelIsNotAccepted:   "Channel is not Accepted and dont send",

		// Information
		KeyConnectionCatched:      "New Conneciton Catched",
		KeySSHHoneypotListening:   "SSH Listening of Honeypot Port",
		KeyClientConnected:        "New TCP connection established",
		KeyFakeSSHKey:             "A Fake SSH key(RSA 2048) is being in memory... ",

		// Hacker Trying
		KeyWantToOpen:             "Want to open Shell, pty, x11",
		KeyTryingPasswd:           "Trying Password",
	},
}

func GetMsg(key MessageKey) string {
	if msg, exists := Messages[ActiveLanguage][key]; exists {
		return msg
	}
	if msg, exists := Messages[EN][key]; exists {
		return msg
	}
	return string(key)
}
