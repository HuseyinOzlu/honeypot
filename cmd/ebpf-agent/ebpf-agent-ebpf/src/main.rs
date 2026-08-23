#![no_std]
#![no_main]

use aya_ebpf::{
    macros::tracepoint,
    programs::TracePointContext,
};

#[inline(always)]
unsafe fn bpf_trace_printk(fmt: *const u8, fmt_size: u32) -> i32 {
    let f: unsafe extern "C" fn(*const u8, u32) -> i32 = core::mem::transmute(6usize);
    f(fmt, fmt_size)
}

// sys_enter_execve tetiklendiğinde Kernel bu fonksiyonu çağıracak
#[tracepoint]
pub fn ebpf_agent_ebpf(ctx: TracePointContext) -> u32 {
    match try_ebpf_agent_ebpf(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

fn try_ebpf_agent_ebpf(_ctx: TracePointContext) -> Result<u32, u32> {
    let msg = b"BINGO! Yakalandin!\n\0";
    unsafe {
        bpf_trace_printk(msg.as_ptr(), msg.len() as u32);
    }
    Ok(0)
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}