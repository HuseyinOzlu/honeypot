# 🍯 Multi-Service Honeypot Platform

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)
![Architecture](https://img.shields.io/badge/Architecture-N--Tier%20Monorepo-green.svg)
![License](https://img.shields.io/badge/License-MIT-orange.svg)

Bu proje, olası siber saldırıları tespit etmek, siber saldırganların davranışlarını analiz etmek, kaba kuvvet (brute-force) denemelerini kaydetmek ve otonom tarayıcıları tuzağa düşürmek amacıyla tasarlanmış **katmanlı mimariye (N-Tier Architecture)** sahip modüler bir **Honeypot (Bal Küpü)** sistemidir.

Proje, servis izolasyonunu sağlamak ve yönetimi kolaylaştırmak adına **Monorepo** yapısında kurgulanmış olup **SSH** ve **HTTP** servislerini tek bir orkestrasyon altında birleştirir.

---

## 🏛️ Mimari ve Servisler

| Servis | Dizin | Konteyner Portu | Host Portu | Temel Teknolojiler | Açıklama |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SSH Honeypot** | `honeypot_ssh/` | `2222` | `22` | Python, Paramiko, VFS | Sahte kabuk (Shell) ve sanal dosya sistemi simülasyonu sunan interaktif SSH sunucusu. |
| **HTTP Honeypot** | `honeypot_http/` | `80` | `8080` | Python, Flask | Web tarayıcıları, botlar ve zafiyet tarayıcılarını loglayan sahte web servisi. |

---

## 📂 Monorepo Dizin Yapısı

```text
Honeypot/
├── docker-compose.yml       # Tüm servisleri orkestre eden ana yapılandırma
├── .gitignore               # Kök dizin yoksayma kuralları
├── README.md                # Platform genel dokümantasyonu
├── honeypot_ssh/            # SSH Honeypot Servisi (Katmanlı Mimari)
│   ├── config/              # Ayarlar ve sahte komut tanımları (commands.json)
│   ├── core/                # SSH Sunucu, VFS ve Shell motoru
│   ├── interfaces/          # Sunucu arayüz tanımlamaları
│   ├── services/            # Kimlik doğrulama ve loglama servisleri
│   ├── Dockerfile           # SSH servisi Docker imaj yapılandırması
│   └── main.py              # Giriş noktası
└── honeypot_http/           # HTTP Web Honeypot Servisi (Katmanlı Mimari)
    ├── config/              # Web servis ayarları
    ├── core/                # Flask uygulama fabrikası ve istek yakalayıcılar
    ├── services/            # HTTP loglama servisi
    ├── Dockerfile           # HTTP servisi Docker imaj yapılandırması
    └── main.py              # Giriş noktası
```

---

## 🚀 Hızlı Başlangıç (Docker Compose ile)

Projedeki tüm servisleri izole konteynerler olarak tek komutla ayağa kaldırabilirsiniz:

### 1. Servisleri Başlatın
```bash
docker-compose up -d --build
```

### 2. Durumu Kontrol Edin
```bash
docker-compose ps
```

### 3. Logları İzleyin
Her iki servisin logları Docker hacimleri (volume) sayesinde ana bilgisayarınıza anlık olarak yansıtılır:
- **SSH Saldırı Logları:** `honeypot_ssh/honeypot.log`
- **HTTP İstek Logları:** `honeypot_http/web.log`

Konteyner loglarını terminalden izlemek için:
```bash
docker-compose logs -f
```

---

## 🛠️ Yerel Geliştirme (Local Development)

Servisleri Docker kullanmadan, doğrudan sanal ortam (`venv`) üzerinde çalıştırmak isterseniz:

1. Sanal ortam oluşturun ve aktifleştirin:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   ```
2. İlgili servisin dizinine gidip bağımlılıkları yükleyin ve çalıştırın:
   ```bash
   cd honeypot_ssh
   pip install -r requirements.txt
   python main.py
   ```

---

## 🔒 Güvenlik Notu
Bu sistem siber güvenlik araştırmaları ve tehdit istihbaratı toplama amacıyla geliştirilmiştir. Production (canlı) ağlarda çalıştırılırken log dosyalarının disk alanını doldurmaması için log rotasyonu (log rotation) uygulanması ve izole bir ağ segmentinde (VLAN/DMZ) barındırılması tavsiye edilir.
