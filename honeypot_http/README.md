# 🌐 HTTP Web Honeypot Service (`honeypot_http`)

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Flask](https://img.shields.io/badge/Framework-Flask-000000.svg)
![Architecture](https://img.shields.io/badge/Architecture-N--Tier-purple.svg)

`honeypot_http`, internet üzerindeki otomatik zafiyet tarayıcılarını, web botlarını ve siber saldırganları tespit etmek amacıyla geliştirilmiş **Flask tabanlı bir Web Bal Küpü (Honeypot)** servisidir. 

Gelen tüm HTTP isteklerini (GET, POST, PUT, DELETE vb.) yakalar; istek yapılan yolları (paths), HTTP başlıklarını (headers), User-Agent bilgisini ve gönderilen yükleri (payloads) kayıt altına alarak siber tehdit analizi için veri toplar.

---

## ✨ Öne Çıkan Özellikler

- **Her İsteği Yakalama (Catch-All Routing):** Sunucuya yapılan tüm istekler sistem tarafından yakalanır ve sahte web yanıtlarıyla dönülür.
- **Tehdit İstihbaratı Toplama:** Zafiyet tarama araçlarının (Acunetix, Nikto, Nmap, Dirbuster vb.) aradığı hassas dosyalar (ör. `.env`, `wp-admin`, `config.php`, `phpinfo.php`) ve SQL/XSS enjeksiyon denemeleri anında kaydedilir.
- **Katmanlı Modüler Yapı:** Flask uygulama mantığı, loglama servisi ve konfigürasyon birbirinden tamamen ayrılmıştır.

---

## 🛠️ Kullanılan Teknolojiler

- **Python 3.12+**: Temel programlama dili.
- **Flask**: Hafif, esnek ve hızlı WSGI web uygulama çatısı.
- **Python-dotenv**: Ortam değişkenlerinin yönetimi.

---

## 🏛️ Katmanlı Mimari Yapısı

```text
honeypot_http/
├── config/
│   ├── __init__.py
│   └── settings.py          # Host, Port ve ortamsal ayarlar
├── core/
│   ├── __init__.py
│   ├── app.py               # Flask uygulama fabrikası (Application Factory)
│   └── handlers.py          # HTTP rota (route) yönlendiricileri ve istek yakalayıcılar
├── services/
│   ├── __init__.py
│   └── log_service.py       # İstek detaylarını dosyaya ve konsola aktaran log servisi
├── Dockerfile               # Docker imaj yapılandırması
├── requirements.txt         # Bağımlılıklar (Flask, python-dotenv)
└── main.py                  # Uygulama başlatıcısı
```

---

## ⚙️ Kurulum ve Çalıştırma

### 1. Docker ile Çalıştırma
Kök dizindeki `docker-compose.yml` üzerinden tetiklenir veya tek başına derlenebilir:
```bash
docker build -t honeypot-http .
docker run -d -p 8080:80 -v $(pwd)/web.log:/app/web.log honeypot-http
```

### 2. Yerel Ortamda Çalıştırma
```bash
# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Servisi başlatın (Varsayılan port: 8080 veya .env içinde tanımlı port)
python main.py
```

---

## 📊 Log Yapısı (`web.log`)

Yakalanan her HTTP isteği, IP adresi, hedef yol ve User-Agent bilgisiyle birlikte kaydedilir:
```text
[2026-07-02 20:18:12] [WARNING] [HTTP] IP: 192.168.1.100 | Method: GET | Path: /wp-login.php | User-Agent: Mozilla/5.0 Nikto/2.1.6
[2026-07-02 20:18:15] [WARNING] [HTTP] IP: 192.168.1.100 | Method: POST | Path: /api/login | Payload: {'username': 'admin', 'password': 'sql'}
```
