#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct event_t {
    __u32 pid;
    char comm[64];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

struct execve_args {
    unsigned short common_type;
    unsigned char common_flags;
    unsigned char common_preempt_count;
    int common_pid;
    int __syscall_nr;
    const char *filename;
};

SEC("tracepoint/syscalls/sys_enter_execve")
int handle_execve(struct execve_args *ctx) {
    struct event_t *e;
    
    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;
    
    e->pid = bpf_get_current_pid_tgid() >> 32;
    bpf_probe_read_str(e->comm, sizeof(e->comm), ctx->filename);
    
    bpf_ringbuf_submit(e, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";
