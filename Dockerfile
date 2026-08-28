FROM golang:alpine AS builder

WORKDIR /app

RUN apk add --no-cache git build-base

COPY go.mod go.sum* ./
RUN go mod download || true

COPY . .

#? For Swagger
RUN go install github.com/swaggo/swag/cmd/swag@latest
RUN swag init -d cmd/gateway,internal/api/handlers,pkg/telemetry

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o /bin/gateway ./cmd/gateway
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o /bin/session-manager ./cmd/session-manager || true
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o /bin/telemetry-collector ./cmd/telemetry-collector || true

FROM alpine:3.19 AS gateway
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata
COPY --from=builder /bin/gateway /usr/local/bin/gateway
EXPOSE 2222 8080
ENTRYPOINT ["/usr/local/bin/gateway"]

FROM alpine:3.19 AS session-manager
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata iproute2 iptables
COPY --from=builder /bin/session-manager /usr/local/bin/session-manager
EXPOSE 50051
ENTRYPOINT ["/usr/local/bin/session-manager"]

FROM alpine:3.19 AS telemetry-collector
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata
COPY --from=builder /bin/telemetry-collector /usr/local/bin/telemetry-collector
EXPOSE 50052
ENTRYPOINT ["/usr/local/bin/telemetry-collector"]
