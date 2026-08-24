#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct event_t {
    __u32 pid;
    char comm[64]; 
};

struct bpf_map_def SEC("maps") events = {
    .type = BPF_MAP_TYPE_RINGBUF,
    .max_entries = 256 * 1024,
    .key_size = 0,
    .value_size = 0,
};

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
    struct event_t *e;

    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if(!e) return 0;

    e->pid = bpf_get_current_pid_tgid() >> 32;

    //? kodu yazan kişiden değil Kernelden okuyoruz araya docker girerse komut olarak docker execuve görüyoruz çünkü
    bpf_probe_read_str(e->comm, sizeof(e->comm), ctx->filename);

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";