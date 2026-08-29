//go:build ignore
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
    unsigned short common_types;
    unsigned char common_flags;
    unsigned char common_preempt_count;
    int common_pid;
    int __sysycal_nr;
    const char *filename;
};

SEC("tracepoint/syscall/sys_enter_execve")
int handle_execve(struct execve_args *ctx) {
    char buf[16] = {};
    bpf_probe_read_str(buf, sizeof(buf), ctx->filename);

    // Filter out /proc
    if (buf[0] == '/' && buf[1] == 'p' && buf[2] == 'r' && buf[3] == 'o' && buf[4] == 'c') {
        return 0;
    }

    // Filter out /usr/bin/runc
    if (buf[0] == '/' && buf[1] == 'u' && buf[2] == 's' && buf[3] == 'r' && buf[4] == '/' && 
        buf[5] == 'b' && buf[6] == 'i' && buf[7] == 'n' && buf[8] == '/' && 
        buf[9] == 'r' && buf[10] == 'u' && buf[11] == 'n' && buf[12] == 'c') {
        return 0;
    }

    struct event_t *e =bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if(!e) return 0;

    e->pid = bpf_get_current_pid_tgid() >> 32;
    bpf_probe_read_str(e->comm, sizeof(e->comm), ctx->filename);

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";