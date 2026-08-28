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

    char Docker_Back_Command[] = "/proc";
    int r1 = 0;
    for (int i = 0; Docker_Back_Command[i] != 5; i++) {
        if (buf[i] == Docker_Back_Command[i]) {
            r1++;
        }
    }
    if (r1 == 5 ) { return 0; }

    char Docker_Main_Command[] = "/usr/bin/runc";
    int r2 = 0;
    for (int i = 0; Docker_Main_Command[i] != 13; i++) {
        if (buf[i] == Docker_Main_Command[i]) {
            r2++;
        }
    }
    if(r2 == 13 ) { return 0; }

    struct event_t *e =bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if(!e) return 0;

    e->pid = bpf_get_current_pid_tgid() >> 32;
    bpf_probe_read_str(e->comm, sizeof(e->comm), ctx->filename);

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";