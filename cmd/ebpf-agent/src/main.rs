use aya::{Bpf, programs::TracePoint};
use tokio::signal;
use env_logger;
use log::{info, error};
use std::fs::File;
use std::io::{BufRead, BufReader};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    info!("eBPF Ajanı baslatiliyor...");

    let bpf_path = "./ebpf-agent-ebpf/target/bpfel-unknown-none/release/ebpf-agent-ebpf";

    let mut bpf = match Bpf::load_file(bpf_path) {
        Ok(bpf) => bpf,
        Err(e) => {
            error!("Bytecode yuklenmedi: {}", e);
            return Ok(());
        }
    };

    info!("Bytecode Kernel'e basariyla yuklendi.");

    let mut program_name = String::new();
    for (name, _) in bpf.programs() {
        program_name = name.to_string();
        break;
    }

    let program: &mut TracePoint = bpf.program_mut(&program_name).unwrap().try_into()?;
    program.load()?;
    program.attach("syscalls", "sys_enter_execve")?;

    info!("Kanca basariyla takildi!");
    
    // Asenkron olarak trace_pipe oku
    tokio::spawn(async move {
        if let Ok(file) = File::open("/sys/kernel/debug/tracing/trace_pipe") {
            let reader = BufReader::new(file);
            for line in reader.lines() {
                if let Ok(l) = line {
                    if l.contains("BINGO") {
                        println!("🚨 YAKALANDI: {}", l);
                        use std::io::Write;
                        use std::net::TcpStream;
                        if let Ok(mut stream) = TcpStream::connect("gateway:8080") {
                            let request = format!("POST /api/telemetry/ebpf HTTP/1.1\r\nHost: gateway:8080\r\nContent-Length: {}\r\n\r\n{}", l.len(), l);
                            let _ = stream.write_all(request.as_bytes());
                        }
                    }
                }
            }
        }
    });

    info!("Kapatmak icin CTRL+C'ye basin.");
    signal::ctrl_c().await?;
    info!("Cikis yapiliyor...");
    
    Ok(())
}
