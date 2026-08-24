package main
//go:generate go run github.com/cilium/ebpf/cmd/bpf2go@v0.16.0 -cc clang bpf test_bpf.c -- -I/usr/include/bpf
