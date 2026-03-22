# BetonLab — Beton ve Agrega Laboratuvar Takip Sistemi

**TS EN 13515 ve TS EN 12620 standartlarına uygun** haftalık elek analizi ve kirlilik testi takip sistemi.

> Geliştirici: Mehmet MUTLU — TeknoBeton Danışmanlık

---

## Özellikler

| Modül | Açıklama |
|-------|----------|
| **Elek Analizi** | Tane büyüklüğü dağılımı girişi, otomatik TS EN 13515 değerlendirmesi |
| **Kirlilik Testi** | MB, kum eşdeğeri, ince madde, kil topağı — otomatik uyum kontrolü |
| **Beton Reçetesi** | Reçete yönetimi, bileşen takibi |
| **Haftalık Rapor** | Otomatik rapor oluşturma, uygunsuzluk tespiti, öneri sistemi |
| **Trend Grafikleri** | 30/60/90 günlük trend analizi |
| **500+ Kayıt** | SQLite veritabanı, optimize edilmiş indeksler |

---

## Kurulum

### Gereksinimler
- Python 3.10+
- pip

### 1. Repoyu Klonla
```bash
git clone https://github.com/KULLANICI_ADINIZ/betonlab.git
cd betonlab
```

### 2. Sanal Ortam Oluştur
```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
# ya da:
venv\Scripts\activate         # Windows
```

### 3. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 4. (Opsiyonel) Demo Verisi Yükle
```bash
python backend/seed_data.py
# 520+ kayıt otomatik oluşturulur
```

### 5. Sunucuyu Başlat
```bash
python backend/main.py
```

### 6. Tarayıcıda Aç
```
http://localhost:8000          ← Web arayüzü
http://localhost:8000/docs     ← API dokümantasyonu (Swagger)
```

---

## Proje Yapısı

```
betonlab/
├── backend/
│   ├── main.py          # FastAPI uygulaması, tüm API endpoint'leri
│   ├── database.py      # SQLite veritabanı yöneticisi (500+ kayıt)
│   ├── models.py        # Pydantic veri modelleri
│   ├── analysis.py      # TS EN 13515 / TS EN 12620 analiz motoru
│   └── seed_data.py     # Demo veri yükleyici
├── frontend/
│   ├── index.html       # Ana web arayüzü
│   └── static/
│       ├── css/main.css # Arayüz stilleri
│       └── js/app.js    # Tüm frontend mantığı
├── data/
│   └── betonlab.db      # SQLite veritabanı (otomatik oluşur)
├── requirements.txt
└── README.md
```

---

## API Referansı

### Elek Analizi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/sieve-analyses` | Listele (max 500) |
| POST | `/api/sieve-analyses` | Yeni kayıt |
| GET | `/api/sieve-analyses/{id}` | Detay |
| DELETE | `/api/sieve-analyses/{id}` | Sil |

### Kirlilik Testi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/pollution-tests` | Listele |
| POST | `/api/pollution-tests` | Yeni kayıt |
| GET | `/api/pollution-tests/{id}` | Detay |

### Beton Reçetesi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/concrete-recipes` | Listele |
| POST | `/api/concrete-recipes` | Yeni reçete |
| PUT | `/api/concrete-recipes/{id}` | Güncelle |

### Raporlar
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/reports/weekly?week_start=YYYY-MM-DD` | Haftalık rapor oluştur |
| POST | `/api/reports/weekly/save?week_start=YYYY-MM-DD` | Raporu kaydet |

---

## Desteklenen Agrega Sınıfları

| Kod | Tanım | Kategori |
|-----|-------|----------|
| `0-2` | 0-2 mm Doğal Kum | DOĞAL |
| `0-5` | 0-5 mm Kırma Kum | KIRMA |
| `5-12` | 5-12 mm Çakıl/Kırmataş | KIRMA |
| `12-22` | 12-22 mm İri Agrega | KIRMA |
| `0-31.5` | 0-31.5 mm Mıcır | KIRMA |

---

## Standart Referansları

- **TS EN 13515** — Agrega tane büyüklüğü dağılımı sınırları
- **TS EN 12620** — Beton için agregalar, kirlilik limitleri
- **TS EN 206** — Beton — Özellik, performans, üretim ve uygunluk
- **TS EN 197-1** — Çimento kompozisyon ve uygunluk kriterleri

---

## Android / PWA

Bu uygulama Progressive Web App (PWA) olarak kullanılabilir:
1. Telefonda Chrome ile `http://SUNUCU_IP:8000` açın
2. "Ana ekrana ekle" seçeneğiyle yükleyin
3. Uygulama gibi çalışır

---

## Lisans

MIT Lisansı — Ticari kullanım serbesttir.

---

*TeknoBeton Danışmanlık — Mehmet MUTLU*
