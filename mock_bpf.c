#define SEC(name) __attribute__((section(name), used))
typedef unsigned int __u32;
typedef unsigned long long __u64;

#define __uint(name, val) int (*name)[val]
#define BPF_MAP_TYPE_RINGBUF 27

struct event_t {
    __u32 pid;
    char comm[64];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps") = {0};

static void *(*bpf_ringbuf_reserve)(void *ringbuf, __u64 size, __u64 flags) = (void *) 131;
static void (*bpf_ringbuf_submit)(void *data, __u64 flags) = (void *) 132;
static __u64 (*bpf_get_current_pid_tgid)(void) = (void *) 14;
static long (*bpf_probe_read_str)(void *dst, __u32 size, const void *unsafe_ptr) = (void *) 45;

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
