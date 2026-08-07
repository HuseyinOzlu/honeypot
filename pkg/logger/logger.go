package logger

import (
	"log/slog"
	"os"
)

// InitLogger initializes an enterprise JSON structured logger.
func InitLogger(serviceName string, level string) *slog.Logger {
	var logLevel slog.Level
	switch level {
	case "debug":
		logLevel = slog.LevelDebug
	case "warn":
		logLevel = slog.LevelWarn
	case "error":
		logLevel = slog.LevelError
	default:
		logLevel = slog.LevelInfo
	}

	opts := &slog.HandlerOptions{
		Level: logLevel,
	}

	handler := slog.NewJSONHandler(os.Stdout, opts)
	l := slog.New(handler).With("service", serviceName)
	slog.SetDefault(l)
	return l
}
