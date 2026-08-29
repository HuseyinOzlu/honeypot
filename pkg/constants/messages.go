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
	//		internal/protocols/ssh/:
	KeySSHListenFailed       	 	MessageKey = "SSH_LISTEN_FAILED"
	KeySSHKeyGenFailed        	 	MessageKey = "SSH_KEY_GEN_FAILED"
	KeySSHHandshakeError       	 	MessageKey = "SSH_HANDSHAKE_ERROR"
	KeyErrorSignerFromKey        	MessageKey = "SIGNER_ERROR_KEY"
	KeyPortListenFailed       	 	MessageKey = "PORT_LISTEN_FAILED"
	KeyConnectionNotAcccepted 	 	MessageKey = "CONN_NOT_ACCEPTED"
	KeyChannelIsNotAccepted    	 	MessageKey = "CHANNEL_IS_NOT_ACCEPTED"
	//		internal/sessions:
	KeyEnvSessionFailed			 	MessageKey = "FAILED_ENV_SESSIONS"
	KeySessionsNotFound			 	MessageKey = "SESSIONS_NOT_FOUND"
	//		internal/environment/fake/client.go
	KeyPyVFSError					MessageKey = "PY_VFS_ERROR"
	KeyVFSOffline					MessageKey = "VFS_OFFLINE"
	// INFO:
	//		pkg/errors/:
	KeyErrorMessage				 	MessageKey = "ERROR_MESSAGES"
	//		internal/protocols/ssh/:
	KeySSHHoneypotListening 	 	MessageKey = "SSH_LISTENING"
	KeyClientConnected      	 	MessageKey = "CLIENT_CONNECTED"
	KeyConnectionCatched    	 	MessageKey = "NEW_CONNECTION_CATCHED"
	KeyFakeSSHKey           	 	MessageKey = "FAKE_SSH_KEY_GENERATED"
	KeyLoginTrying					MessageKey = "LOGIN_TRYİNG"
	// 		cmd/gateway/:
	KeyStartingGateway      	 	MessageKey = "STARTING_GATEWAY_SERVICE"
	KeyListeningGateway     	 	MessageKey = "GATEWAY_LISTENING"
	KeyShuttingDownGateway  	 	MessageKey = "GATEWAY_SHUTTING_DOWN"
	//		cmd/telemetry-collector/:
	KeyStartingeBPFLog       	 	MessageKey = "STARTING_eBPF_LOG"
	KeyTelemetryPPLListening 	 	MessageKey = "TELEMETRY_PPL_LISTENING"
	KeyShuttingDownCollector 	 	MessageKey = "SHUTTING_DOWN_COLLECTOR"
	//		cmd/session-manager/:
	KeyStartingSMAndOrchestrator 	MessageKey = "STARTING_SM_AND_ORCH"
	KeyWarmPoolRegistered		 	MessageKey = "WARM_POOL_REGISTERED"
	KeyShuttingDownSMAndOrch	 	MessageKey = "SHUTTING_DOWN_SM_AND_ORCH"

	//		internal/sessions/:
	KeyStartingSession			 	MessageKey = "STARTING_SESSION"
	KeyTerminatedSession		 	MessageKey = "TERMINATED_SESSION"


	// Hacker trying
	//		internal/protocols/ssh/:
	KeyTryingPasswd 				MessageKey = "TRYING_PASSWORD"
	KeyWantToOpen   				MessageKey = "WANT_TO_OPEN"
)

var Messages = map[Language]map[MessageKey]string{
	// Türkçe Paket
	TR: {
		// Hatalar
		//		internal/protocols/ssh/:
		KeySSHListenFailed:        		"SSH sunucusu belirtilen portta dinlenemedi",
		KeySSHKeyGenFailed:        		"SSH RSA host anahtarı üretilemedi",
		KeySSHHandshakeError:      		"SSH Handshake başarısız oldu (Tarayıcı veya Nmap olabilir)",
		KeyErrorSignerFromKey:     		"Anahtar imzalama başarısız oldu",
		KeyPortListenFailed:      		"Port dinlenemedi",
		KeyConnectionNotAcccepted: 		"Bağlantı Kabul edilmedi",
		KeyChannelIsNotAccepted:   		"Kanal kabul edilmedi ve gönderilmedi",
		//		internal/sessions
		KeyEnvSessionFailed:			"Ortam oturumu oluşturulurken hata meydana geldi",
		KeySessionsNotFound:			"Oturum bilgisi bulanamadı, Oturum Id:",
		//		internal/environment/fake/client.go
		KeyPyVFSError:					"Python VFS sunucusuna erişemedi",
		KeyVFSOffline:					"VFS erişelemez durumda",

		// Bilgi
		//		pkg/errors/:
		KeyErrorMessage:				"Sistem Hatası Yakalandı",
		// 		cmd/gateway/:
		KeyStartingGateway:     		"Gateway Servisi Başlatılıyor...",
		KeyListeningGateway:    		"Çoklu Gateway bağlantı servisi dinleniyor",
		KeyShuttingDownGateway: 		"Gateway Servisi temiz biçimde sonlandırılıyor...",
		//		internal/protocols/ssh/:
		KeyConnectionCatched:    		"Yeni bağlantı yakalandı",
		KeySSHHoneypotListening: 		"SSH Honeypot portunda dinleniyor",
		KeyFakeSSHKey:           		"Sahte SSH kimlik Kartı (RSA 2048) bellekte Üretiliyor...",
		KeyClientConnected:      		"Yeni TCP bağlantısı yakalandı",
		KeyLoginTrying:					"Login bağlantısı denendi",
		//		cmd/telemetry-collector/:
		KeyStartingeBPFLog:       		"Yüksek Verimli eBPF ve Log toplama servisi başlıyor..",
		KeyTelemetryPPLListening: 		"Telemetri Veri Akışı gRPC (50052 portunda) dinleniyor ve CliclkHouse veritabanına bağlandı",
		KeyShuttingDownCollector: 		"Telemetri kuyruğu veritabanına aktarılıyor ve Toplayıcı servis güvenle sonlandırılıyor...",
		//		cmd/session-manager/
		KeyStartingSMAndOrchestrator: 	"Oturum Yönetimi ve Ortam Orkestratörü Başlıyor",
		KeyWarmPoolRegistered: 		  	"Ortam denetim kayıtları başarılı",
		KeyShuttingDownSMAndOrch:	 	"Oturum Yönetimi ve Ortam Orkestratörü sonlandırılıyor",
		//		internal/sessions/
		KeyStartingSession:			  	"Oturum başarıyla oluşturuldu",
		KeyTerminatedSession:		  	"Oturum başarıyla sonlandırıldı ve temizlendi",

		// Hacker denemeleri
		//		internal/protocols/ssh/:
		KeyWantToOpen:   				"Komut Satırı, pty ve x11 açmak istiyor",
		KeyTryingPasswd: 				"Şifre Deneniyor",
	},
	// English Pack
	EN: {
		// Errors
		//		internal/protocols/ssh/:
		KeySSHListenFailed:        		"SSH server failed to listen on the specified port",
		KeySSHKeyGenFailed:        		"Failed to generate SSH RSA host key",
		KeySSHHandshakeError:      		"SSH Handshake failed (Browser or Nmap scanner)",
		KeyErrorSignerFromKey:     		"Signer from key failed",
		KeyPortListenFailed:       		"Port did not listen",
		KeyConnectionNotAcccepted: 		"Connection not Accepted",
		KeyChannelIsNotAccepted:   		"Channel is not Accepted and dont send",
		//		internal/sessions
		KeyEnvSessionFailed:	   		"Failed to allocate environment session: ",
		KeySessionsNotFound:	   		"Session not found, Sessions id: ",
		//		internal/environment/fake/client.go
		KeyPyVFSError:					"Python can't be accessed VFS Server",
		KeyVFSOffline:					"VFS Offline ",
		// Information
		//		pkg/errors/:
		KeyErrorMessage:				"Catched System Error",
		// 		cmd/gateway/:
		KeyStartingGateway:     		"Starting Gateway Service...",
		KeyListeningGateway:    		"Gateway Service Listening for Multiplexed Connections",
		KeyShuttingDownGateway: 		"Shutting Down Gateway Service Cleanly...",
		//		internal/protocols/ssh/:
		KeyConnectionCatched:    		"New Conneciton Catched",
		KeySSHHoneypotListening: 		"SSH Listening of Honeypot Port",
		KeyClientConnected:      		"New TCP connection established",
		KeyFakeSSHKey:           		"A Fake SSH key(RSA 2048) is being in memory... ",
		KeyLoginTrying:					"Trying new login",
		//		cmd/telemetry-collector
		KeyStartingeBPFLog:       		"Starting High-Throughput eBPF Telemetry & Log Collector Service...",
		KeyTelemetryPPLListening: 		"Telemetry pipeline listening on gRPC port 50052 and connected to ClickHouse buffer",
		KeyShuttingDownCollector: 		"Flushing telemtery ring-buffers and shutting down Collector service...",
		//		cmd/session-manager
		KeyStartingSMAndOrchestrator: 	"Starting Session Manager & Environment Orchestrator Daemon...",
		KeyWarmPoolRegistered:		  	"Warm-Pool environments registered successfully",
		KeyShuttingDownSMAndOrch:	  	"Shutting down Session Manager daemon...",
		//		internal/sessions
		KeyStartingSession:			  	"Sessions successfully created",
		KeyTerminatedSession:		  	"Session terminated and cleaned up",

		// Hacker Trying
		//		internal/protocols/ssh/:
		KeyWantToOpen:   				"Want to open Shell, pty, x11",
		KeyTryingPasswd: 				"Trying Password",
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
