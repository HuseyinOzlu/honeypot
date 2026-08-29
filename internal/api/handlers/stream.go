package handlers

import (
	"fmt"
	"net/http"
	"github.com/HuseyinOzlu/honeypot/pkg/telemetry"
)
func StreamLogs(w http.ResponseWriter, r *http.Request) {
	//? Request access to 3000 port as CORS for React/Next.js
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	w.Header().Set("Content-Type","text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	broker := telemetry.GetBroker()
	clientChan := broker.Subscribe()
	defer broker.Unsubscribe(clientChan)

	if f, ok := w.(http.Flusher); ok {
		f.Flush()
	}

	notify := r.Context().Done()

	for {
		select {
		case <- notify:
			return // Closed WebSite and Stopping Data
		case msg := <-clientChan:
			fmt.Fprintf(w, "data: %s\n\n", msg)
			if f, ok := w.(http.Flusher); ok {
				f.Flush() // Send to data with TCP/HTTP
			}
		}
	}

}