package http

import (
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"time"

	"github.com/HuseyinOzlu/honeypot/pkg/telemetry"
)

func StartServer(port string) {
	mux := http.NewServeMux()

	mux.HandleFunc("/", indexHandler)
	mux.HandleFunc("/robots.txt", robotsHandler)
	mux.HandleFunc("/.git/config", gitConfigHandler)
	mux.HandleFunc("/wp-login.php", wpLoginHandler)
	mux.HandleFunc("/admin", adminLoginHandler)
	mux.HandleFunc("/login", adminLoginHandler)
	mux.HandleFunc("/phpmyadmin", pmaLoginHandler)
	mux.HandleFunc("/phpmyadmin/", pmaLoginHandler)

	loggedMux := loggingMiddleware(mux)

	slog.Info("HTTP Honeypot Dinliyor", "port", port)
	err := http.ListenAndServe(":"+port, loggedMux)
	if err != nil {
		slog.Error("HTTP Server Error", "error", err)
	}
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Server", "Apache/2.4.41 (Ubuntu)")

		r.ParseForm()
		payload := r.Form.Encode()
		if payload == "" && r.Body != nil {
			bodyBytes, _ := io.ReadAll(r.Body)
			payload = string(bodyBytes)
		}

		event := telemetry.HTTPEvent{
			IPAddress: r.RemoteAddr,
			Method:    r.Method,
			Path:      r.URL.Path,
			UserAgent: r.UserAgent(),
			Payload:   payload,
			Timestamp: time.Now(),
		}
		telemetry.LogHTTP(event)

		slog.Info("HTTP Isteği", "ip", r.RemoteAddr, "method", r.Method, "path", r.URL.Path)

		next.ServeHTTP(w, r)
	})
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		w.WriteHeader(http.StatusNotFound)
		fmt.Fprintf(w, "<!DOCTYPE html><html><head><title>404 Not Found</title></head><body><h1>Not Found</h1><p>The requested URL was not found on this server.</p><hr><address>Apache/2.4.41 (Ubuntu) Server at localhost Port 8080</address></body></html>")
		return
	}
	html := "<!DOCTYPE html><html><head><title>Apache2 Ubuntu Default Page: It works</title><style>body { font-family: sans-serif; background-color: #f0f0f0; margin: 40px; } .card { background: white; padding: 20px; border: 1px solid #ccc; border-top: 5px solid #2e7d32; } h1 { color: #2e7d32; }</style></head><body><div class=\"card\"><h1>Apache2 Ubuntu Default Page</h1><h3>It works!</h3><p>This is the default welcome page used to test the correct operation of the Apache2 server after installation on Ubuntu systems.</p></div></body></html>"
	w.Write([]byte(html))
}

func robotsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	w.Write([]byte("User-agent: *\nDisallow: /admin\nDisallow: /wp-login.php\nDisallow: /phpmyadmin\nDisallow: /.git\n"))
}

func gitConfigHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	w.Write([]byte("[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n\tlogallrefupdates = true\n[remote \"origin\"]\n\turl = https://github.com/admin/secrets-vault.git\n\tfetch = +refs/heads/*:refs/remotes/origin/*\n[branch \"main\"]\n\tremote = origin\n\tmerge = refs/heads/main\n"))
}

func wpLoginHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodPost {
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte("<!DOCTYPE html><html><head><title>Log In ‹ Test Site — WordPress</title></head><body style=\"font-family: sans-serif; background: #f1f1f1; display: flex; justify-content: center; align-items: center; height: 100vh;\"><div style=\"background: white; padding: 20px; border: 1px solid #ccc; width: 320px; text-align: center;\"><h3 style=\"color: #d63638;\">ERROR: The username or password you entered is incorrect.</h3><p><a href=\"/wp-login.php\">Lost your password?</a></p><p><a href=\"/wp-login.php\">← Go to Test Site</a></p></div></body></html>"))
		return
	}
	w.Write([]byte("<!DOCTYPE html><html><head><title>Log In ‹ Test Site — WordPress</title><style>body { background: #f1f1f1; font-family: sans-serif; } .login-form { background: white; width: 320px; margin: 100px auto; padding: 26px; border: 1px solid #c3c4c7; box-shadow: 0 1px 3px rgba(0,0,0,.04); } .input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #8c8f94; box-sizing: border-box; } .submit { background: #2271b1; border-color: #2271b1; color: #fff; padding: 10px 15px; border-style: solid; border-width: 1px; cursor: pointer; }</style></head><body><div class=\"login-form\"><form method=\"POST\" action=\"/wp-login.php\"><label>Username or Email Address</label><input type=\"text\" name=\"log\" class=\"input\" required><label>Password</label><input type=\"password\" name=\"pwd\" class=\"input\" required><input type=\"submit\" value=\"Log In\" class=\"submit\"></form></div></body></html>"))
}

func adminLoginHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodPost {
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte("<h3 style='color: red;'>Invalid Credentials. Access Denied.</h3><a href='/admin'>Back</a>"))
		return
	}
	w.Write([]byte("<!DOCTYPE html><html><head><title>Admin Portal Login</title><style>body { background: #263238; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; } .login-box { background: #37474f; padding: 40px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); width: 300px; color: white; } .input { width: 100%; padding: 10px; margin: 10px 0; border: none; border-radius: 4px; box-sizing: border-box; } .submit { width: 100%; background: #00bcd4; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer; }</style></head><body><div class=\"login-box\"><h2>Control Panel</h2><form method=\"POST\"><input type=\"text\" name=\"username\" placeholder=\"Username\" class=\"input\" required><input type=\"password\" name=\"password\" placeholder=\"Password\" class=\"input\" required><input type=\"submit\" value=\"Login\" class=\"submit\"></form></div></body></html>"))
}

func pmaLoginHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodPost {
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte("<h3 style='color: red;'>#1045 - Access denied for user.</h3><a href='/phpmyadmin'>Back</a>"))
		return
	}
	w.Write([]byte("<!DOCTYPE html><html><head><title>phpMyAdmin</title><style>body { background: #ebebeb; font-family: sans-serif; } .pma-box { background: white; border: 1px solid #aaa; width: 450px; margin: 100px auto; padding: 20px; border-radius: 5px; } .input { width: 100%; padding: 8px; margin: 8px 0; box-sizing: border-box; } .submit { background: #ff9900; border: 1px solid #ff9900; color: white; padding: 8px 16px; cursor: pointer; }</style></head><body><div class=\"pma-box\"><h2>Welcome to phpMyAdmin</h2><form method=\"POST\"><label>Username:</label><input type=\"text\" name=\"pma_username\" class=\"input\" required><label>Password:</label><input type=\"password\" name=\"pma_password\" class=\"input\"><input type=\"submit\" value=\"Go\" class=\"submit\"></form></div></body></html>"))
}