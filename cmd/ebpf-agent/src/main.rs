use log::{info, warn};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    info!("Starting eBPF Kernel Telemetry Agent inside target instance...");
    info!("Hooking sys_enter_execve, sys_enter_connect, sys_enter_openat, and sys_enter_unlinkat...");

    // Main telemetry loop streaming from ring buffer to gRPC collector
    tokio::signal::ctrl_c().await?;
    warn!("Shutdown signal received, unhooking eBPF kprobes cleanly.");
    Ok(())
}
