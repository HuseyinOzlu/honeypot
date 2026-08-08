package errors

import (
	"log/slog"
	. "github.com/HuseyinOzlu/honeypot/pkg/constants"
)

func LogError(contextMsg string, err error) {
	if err != nil {
		slog.Error(GetMsg(KeyErrorMessage),
					"context", contextMsg, "error_detail", err.Error())
	}
}