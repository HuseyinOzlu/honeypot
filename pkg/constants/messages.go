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
	//		cmd/gateway/:
	KeyDBFailedFallback				MessageKey = "DB_FAILED_FALLBACK"
	KeyConfigReadFailed				MessageKey = "CONFIG_READ_FAILED"
	//		internal/environments/docker/
	KeyContainerCreationFailed		MessageKey = "CONTAINER_CREATION_FAILED"
	KeyDockerFailedFallbackAI		MessageKey = "DOCKER_FAILED_FALLBACK_AI"
	KeyAIFailedFallbackVFS			MessageKey = "AI_FAILED_FALLBACK_VFS"
	//		internal/protocols/http/
	KeyHTTPServerError				MessageKey = "HTTP_SERVER_ERROR"
	//		pkg/telemetry/clickhouse.go
	KeyEBPFWriteFailed				MessageKey = "EBPF_WRITE_FAILED"
	KeyClickHouseUnreachableFallbackDisk MessageKey = "CLICKHOUSE_UNREACHABLE_FALLBACK_DISK"
	KeyLogsDirCreationFailed		MessageKey = "LOGS_DIR_CREATION_FAILED"
	KeyAllLogWritesFailed			MessageKey = "ALL_LOG_WRITES_FAILED"
	KeyHTTPWriteFailed				MessageKey = "HTTP_WRITE_FAILED"

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
	//		internal/protocols/http/
	KeyHTTPServerListening			MessageKey = "HTTP_SERVER_LISTENING"
	KeyHTTPRequestCatched			MessageKey = "HTTP_REQUEST_CATCHED"
	KeyEBPFLogReceived				MessageKey = "EBPF_LOG_RECEIVED"
	//		internal/environments/docker/
	KeyHackerExitCellDestroyed		MessageKey = "HACKER_EXIT_CELL_DESTROYED"


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
		//		cmd/gateway/:
		KeyDBFailedFallback:			"Veritabanı çöktü, sistem Log kaydına(fallback_logs.json a yazılıyor) ",
		KeyConfigReadFailed:			"Kongigurasyon dosyası okunamadı: ",
		//		internal/environments/docker/
		KeyContainerCreationFailed:		"Konteyner yaratılamadı: %v",
		KeyDockerFailedFallbackAI:		"Docker çalışmıyor (%v), Fallback 1: AI (Gemini) devrede!",
		KeyAIFailedFallbackVFS:			"AI motoru da çöktü (%v), Fallback 2: Python VFS devrede!",
		//		internal/protocols/http/
		KeyHTTPServerError:				"HTTP Server Error",
		//		pkg/telemetry/clickhouse.go
		KeyEBPFWriteFailed:				"EBPF Log ClickHouse'a yazılamadı: %v",
		KeyClickHouseUnreachableFallbackDisk: "ClickHouse'a ulaşılamıyor! Log diske yazılıyor hata: %v",
		KeyLogsDirCreationFailed:		"HATA! logs klasörü oluşturulamadı: %v",
		KeyAllLogWritesFailed:			"HATA! Veriler ClickHouse ve Diske'de yazılamadı: %v",
		KeyHTTPWriteFailed:				"HTTP Log ClickHouse'a yazılamadı: %v",

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
		//		internal/environments/docker/
		KeyHackerExitCellDestroyed:		"Hacker cikti, hucre imha ediliyor: %s",
		//		internal/protocols/http/
		KeyHTTPServerListening:			"HTTP Sunucusu Dinliyor",
		KeyHTTPRequestCatched:			"HTTP Isteği",
		KeyEBPFLogReceived:				"eBPF Ajanından Log Geldi!",

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
		//		cmd/gateway/:
		KeyDBFailedFallback:			"Database crashed, system is writing to fallback_logs.json ",
		KeyConfigReadFailed:			"Failed to read configuration file: ",
		//		internal/environments/docker/
		KeyContainerCreationFailed:		"Failed to create container: %v",
		KeyDockerFailedFallbackAI:		"Docker is not running (%v), Fallback 1: AI (Gemini) active!",
		KeyAIFailedFallbackVFS:			"AI engine also crashed (%v), Fallback 2: Python VFS active!",
		//		internal/protocols/http/
		KeyHTTPServerError:				"HTTP Server Error",
		//		pkg/telemetry/clickhouse.go
		KeyEBPFWriteFailed:				"Failed to write EBPF Log to ClickHouse: %v",
		KeyClickHouseUnreachableFallbackDisk: "ClickHouse is unreachable! Writing log to disk error: %v",
		KeyLogsDirCreationFailed:		"ERROR! Failed to create logs directory: %v",
		KeyAllLogWritesFailed:			"ERROR! Failed to write data to both ClickHouse and Disk: %v",
		KeyHTTPWriteFailed:				"Failed to write HTTP Log to ClickHouse: %v",

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
		//		internal/environments/docker/
		KeyHackerExitCellDestroyed:		"Hacker exited, cell is being destroyed: %s",
		//		internal/protocols/http/
		KeyHTTPServerListening:			"HTTP Server Listening",
		KeyHTTPRequestCatched:			"HTTP Request",
		KeyEBPFLogReceived:				"Log Received from eBPF Agent!",


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
