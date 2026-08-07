package errors

import (
	"log/slog"
)

func LogError(contextMsg string, err error) {
	if err != nil {
		slog.Error("Sistem Hatası Yakalandı",
					"context", contextMsg, "error_detail", err.Error())
	}
}