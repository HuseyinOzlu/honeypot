'use client';

import { useEffect, useState } from "react";

type SSHData = {
  session_id?: string;
  username: string;
  ip: string;
  command: string;
  output?: string;
}

type HTTPData = {
  ip: string;
  path: string;
  method: string;
  payload: string;
  user_agent: string;
}

type EBPFData = {
  log: string;
}

type LogEvent =
  | { type: "ssh_command"; data: SSHData; timestamp: Date}
  | { type: "http_request"; data: HTTPData; timestamp: Date}
  | { type: "ebpf_event"; data: EBPFData; timestamp: Date}

  const getApiUrl = () => {
    //? Eğer hostname de ip tanımlı ise onu yoksa localhost
    if (typeof window === "undefined") return "http://localhost:8080";

    const host = window.location.hostname;

    //? Eğer localhosttan giriliyosa port 8080 (Geliştirme ortamı portumuz) Eğer gerçek IP ile giriliyosa 80 (Production Gateway port) kullan
    const apiPort = host === "localhost" ? "8080" : "80";
    return `http://${host}:${apiPort}`;
  };
export default function Dashboard() {
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const apiUrl = getApiUrl();

  useEffect(() =>  {

    const eventSource = new EventSource(`${apiUrl}/api/v1/stream/logs`);

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as LogEvent;

        setLogs((prev) => [{ ...parsed, timestamp: new Date() }, ...prev].slice(0, 50));
      } catch (err) {
        console.error("Log Parse hatası: ", err);
      }
    };
    return () => eventSource.close();
  }, []);


  return (
    <div className="min-h-screen bg-[#0d1117] text-gray-300 p-8 font-mono">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-2 tracking-wider">
          <span className="text-red-500">HONEYPOT</span>
        </h1>
        <p className="text-sm text-gray-500 mb-8 border-b border-gray-800 pb-4">
          Gerçek zamanlı tehdit akışı ve sistem logları...
        </p>
        <div className="bg-[#161b22] border border-gray-800 rounded-lg shadow-2xl overflow-hidden">
          {/* Dashboard Başlığı */}
          <div className="bg-gray-900 px-4 py-3 flex gap-2 border-b border-gray-800">
            <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          {/* Akış Ekranı */}
          <div className="p-4 h-[600px] overflow-y-auto flex flex-col gap-3">
            {logs.length === 0 ? (
              <div className="text-center text-gray-600 mt-20 animate-pulse">
                Saldırı bekleniyor... Yayın aktif.
              </div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="p-3 bg-black/40 border-l-4 border-gray-700 rounded text-sm break-all flex flex-col gap-1">

                  {/* Etiketler (Tag) */}
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-xs text-gray-500">
                      [{log.timestamp.toLocaleTimeString()}]
                    </span>
                    {log.type === "ssh_command" && (
                      <span className="px-2 py-0.5 bg-blue-900/50 text-blue-400 rounded-sm font-bold text-xs">SSH</span>
                    )}
                    {log.type === "http_request" && (
                      <span className="px-2 py-0.5 bg-green-900/50 text-green-400 rounded-sm font-bold text-xs">HTTP</span>
                    )}
                    {log.type === "ebpf_event" && (
                      <span className="px-2 py-0.5 bg-purple-900/50 text-purple-400 rounded-sm font-bold text-xs">KERNEL</span>
                    )}
                  </div>
                  {/* Veri İçeriği (Matrix Rengi) */}
                  <div className="text-green-400">
                    {log.type === "ssh_command" ? (
                      <div>
                        <span className="text-yellow-400">{log.data.username}@{log.data.ip}</span>$ {log.data.command}
                        {log.data.output && <div className="text-gray-400 mt-1 pl-4 opacity-80 whitespace-pre-wrap">{log.data.output}</div>}
                      </div>
                    ) : (
                      <span>{JSON.stringify(log.data)}</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}