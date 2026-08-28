package main

//go:generate go run github.com/cilium/ebpf/cmd/bpf2go -cc clang -no-strip bpf bpf.c -- -I/usr/include/bpf

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/cilium/ebpf"
	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/ringbuf"
	"github.com/cilium/ebpf/rlimit"
)

//? Struct method like bpf.c
type bpfEvent struct {
	PID uint32
	Comm [64]byte
}

func main() {
	if err := rlimit.RemoveMemlock(); err != nil {
		log.Fatalf("Hafıza limiti kaldırılmadı: %v", err)
	}

	//? import Go from bpf.c file created objects
	spec, err := loadBpf()
	if err != nil {
		log.Fatalf("Bytecode yüklenemedi: %v", err)
	}
	spec.Programs["handle_execve"].Type = ebpf.TracePoint

	objs := bpfObjects{}
	if err := spec.LoadAndAssign(&objs, nil); err != nil {
		log.Fatalf("eBPF nesneleri atanamadı: %v", err)
	}
	defer objs.Close()

	tp, err := link.Tracepoint("syscalls", "sys_enter_execve", objs.HandleExecve, nil)
	if err != nil {
		log.Fatalf("Tracepoint bağlanamadı: %v",err)
	}
	defer tp.Close()
	log.Println("Ajan kernele sızdı! sys_enter_execve dinleniyor...")

	//? Create reader for reading RingBuffer map in bpf.c
	rd, err := ringbuf.NewReader(objs.Events)
	if err != nil {
		log.Fatalf("RingBuf okuyucusu oluşturlamadı: %v",err)
	}
	defer rd.Close()


	//? Close signal(CTRL+C)
	stopper := make(chan os.Signal, 1)
	signal.Notify(stopper, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-stopper
		log.Println("Ajan kapatılıyor...")
		rd.Close()
		os.Exit(0)
	}()

	log.Println("Komutlar bekleniyor...")

	for {
		record, err := rd.Read()
		if err != nil {
			if err == ringbuf.ErrClosed { break }
			continue
		}

		var event bpfEvent
		if err := binary.Read(bytes.NewReader(record.RawSample), binary.LittleEndian, &event); err != nil {
			continue
		}
		n := bytes.IndexByte(event.Comm[:],0)
		if n == -1 {
			n = len(event.Comm)
		}

		command := string(event.Comm[:n])

		logMsg := fmt.Sprintf("BINGO: [PID: %d] Komut: %s", event.PID, command)
		log.Println("YAKALNDI:", logMsg)

		http.Post("http://gateway:8080/api/telemetry/ebpf", "text/plain", bytes.NewBufferString(logMsg))
	}
}