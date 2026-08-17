

CREATE DATABASE IF NOT EXISTS honeypot_telemetry;

-- 1. sessions: Tracks end-to-end attacker sessions across all protocols (SSH, HTTP)
CREATE TABLE IF NOT EXISTS honeypot_telemetry.sessions (
    session_id UUID,
    protocol LowCardinality(String),
    attacker_ip IPv4,
    attacker_port UInt16,
    environment_type LowCardinality(String),
    vm_id String,
    auth_username String,
    auth_password String,
    auth_status LowCardinality(String),
    start_time DateTime64(3, 'UTC'),
    end_time Nullable(DateTime64(3, 'UTC')),
    duration_ms UInt64,
    client_version String,
    hassh_fingerprint String
) ENGINE = ReplacingMergeTree(start_time)
PARTITION BY toYYYYMM(start_time)
ORDER BY (protocol, attacker_ip, start_time, session_id)
SETTINGS index_granularity = 8192;

-- 2. commands: Captured terminal inputs (PTY) and eBPF kernel `execve` events
CREATE TABLE IF NOT EXISTS honeypot_telemetry.commands (
    event_id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    vm_id String,
    pid UInt32,
    ppid UInt32,
    uid UInt32,
    command_raw String,
    binary_path String,
    arguments Array(String),
    environment_vars Map(String, String),
    execution_time DateTime64(3, 'UTC'),
    exit_code Int32,
    source LowCardinality(String) -- 'PTY_INPUT' or 'eBPF_EXECVE'
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(execution_time)
ORDER BY (session_id, execution_time, pid)
SETTINGS index_granularity = 8192;

-- 3. files: File system manipulation events (open, create, unlink, rename, chmod)
CREATE TABLE IF NOT EXISTS honeypot_telemetry.files (
    event_id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    vm_id String,
    pid UInt32,
    operation LowCardinality(String), -- 'OPEN', 'CREATE', 'UNLINK', 'RENAME', 'CHMOD'
    file_path String,
    old_file_path Nullable(String),
    flags String,
    file_mode UInt32,
    event_time DateTime64(3, 'UTC')
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (session_id, file_path, event_time)
SETTINGS index_granularity = 8192;

-- 4. network_events: Socket connections captured via eBPF kprobes (`connect`, `bind`, `accept`)
CREATE TABLE IF NOT EXISTS honeypot_telemetry.network_events (
    event_id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    vm_id String,
    pid UInt32,
    process_name String,
    direction LowCardinality(String), -- 'INBOUND', 'OUTBOUND'
    transport_proto LowCardinality(String), -- 'TCP', 'UDP'
    src_ip IPv4,
    src_port UInt16,
    dst_ip IPv4,
    dst_port UInt16,
    bytes_sent UInt64,
    bytes_recv UInt64,
    event_time DateTime64(3, 'UTC')
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (session_id, dst_ip, dst_port, event_time)
SETTINGS index_granularity = 8192;

-- 5. artifacts: Captured malware binaries, dropped ELF files and scripts stored in S3/MinIO
CREATE TABLE IF NOT EXISTS honeypot_telemetry.artifacts (
    artifact_id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    vm_id String,
    sha256 String,
    md5 String,
    file_name String,
    file_path_in_vm String,
    file_size_bytes UInt64,
    mime_type LowCardinality(String),
    storage_path String, -- 's3://bucket/sha256...'
    captured_at DateTime64(3, 'UTC'),
    vt_positives UInt16,
    vt_total UInt16,
    is_rootkit Boolean DEFAULT false
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(captured_at)
ORDER BY (sha256, captured_at, session_id)
SETTINGS index_granularity = 8192;

-- 6. alerts: Real-time threat intelligence detection engine output & MITRE ATT&CK mapping
CREATE TABLE IF NOT EXISTS honeypot_telemetry.alerts (
    alert_id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    alert_type LowCardinality(String), -- 'CRITICAL_KERNEL_EXPLOIT', 'C2_COMMUNICATION', 'ROOTKIT_LOAD'
    severity LowCardinality(String), -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    rule_name String,
    mitre_tactic LowCardinality(String), -- e.g. 'TA0004 - Privilege Escalation'
    mitre_technique LowCardinality(String), -- e.g. 'T1068 - Exploitation for Privilege Escalation'
    description String,
    raw_event_payload String,
    created_at DateTime64(3, 'UTC')
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (severity, created_at, session_id)
SETTINGS index_granularity = 8192;
