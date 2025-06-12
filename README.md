# TuneLeap - Müzik Tanıma

Bu proje, ses dosyalarından müzik tanımak, şarkı tavsiyeleri sunmak ve kullanıcıların çalma listelerini yönetmek için geliştirilmiş kapsamlı bir API hizmetidir. Proje, ses parmak izi (audio fingerprinting) ve makine öğrenmesi tekniklerini kullanarak yüksek doğrulukla müzik tanıma ve kişiselleştirilmiş öneriler sunma kapasitesine sahiptir.

## 🚀 Özellikler

* **Müzik Tanıma**: Yüklenen bir ses dosyasını analiz ederek veritabanındaki şarkılarla eşleştirir.
* **Şarkı Tavsiyesi**: Bir şarkıya dayanarak benzer şarkılardan oluşan tavsiyeler sunar.
* **Otomatik Çalma Listesi**: Belirlenen bir şarkıya göre otomatik olarak çalma listeleri oluşturur.
* **Kullanıcı Yönetimi ve Kimlik Doğrulama**: JWT tabanlı güvenli kullanıcı kaydı ve girişi.
* **Kişisel Çalma Listeleri**: Kullanıcılar kendi çalma listelerini oluşturabilir, düzenleyebilir ve şarkı ekleyip çıkarabilirler.
* **Tanıma Geçmişi**: Kullanıcıların daha önce tanıttığı şarkıların kaydını tutar.
* **Arka Plan İşlemleri**: Müzik tanıma gibi yoğun işlemler Celery ve Redis kullanılarak arka planda asenkron olarak yürütülür.
* **Gürültü Azaltma**: Ses dosyalarındaki gürültüyü azaltarak tanıma doğruluğunu artırır.

## 🛠️ Kullanılan Teknolojiler

* **Backend**: FastAPI, Gunicorn, Uvicorn
* **Veritabanı**:
    * **İlişkisel (SQL)**: PostgreSQL (SQLAlchemy ile) - Kullanıcı, şarkı, albüm gibi yapısal veriler için.
    * **NoSQL**: MongoDB (MongoEngine ile) - Ses parmak izleri ve şarkı özellik vektörleri gibi esnek veriler için.
* **Arka Plan İşlemleri (Asenkron)**: Celery, Redis
* **Ses İşleme**: Librosa, NumPy, SciPy, noisereduce
* **Kimlik Doğrulama**: JWT, Passlib, Bcrypt
* **Containerization**: Docker, Docker Compose
* **Test**: Pytest

## 🔧 Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için Docker ve Docker Compose'un kurulu olması gerekmektedir.

1.  **Proje dosyalarını klonlayın (veya indirin).**

2.  **Environment (Ortam) Değişkenleri:**
    Projenin ana dizininde `.env` adında bir dosya oluşturun ve `docker-compose.yml` dosyasında belirtilen veritabanı ve diğer servisler için gerekli ortam değişkenlerini bu dosyaya ekleyin. Örnek bir `.env` dosyası aşağıdaki gibi olabilir:

    ```env
    # PostgreSQL Ayarları
    POSTGRES_USER=myuser
    POSTGRES_PASSWORD=mypassword
    POSTGRES_DB=tunedb
    DATABASE_URL=postgresql://myuser:mypassword@postgres:5432/tunedb

    # MongoDB Ayarları
    MONGODB_URI=mongodb://mongo:27017
    DB_NAME=tuneleap_db

    # Redis (Celery) Ayarları
    CELERY_BROKER_URL=redis://redis:6379/0

    # JWT Ayarları
    SECRET_KEY=COK_GIZLI_BIR_ANAHTAR_BURAYA_YAZILMALI
    ACCESS_TOKEN_EXPIRE_MINUTES=30

    # Sunucu Ayarları
    PORT=8000
    WEB_CONCURRENCY=4
    LOG_LEVEL=info
    ```

3.  **Docker Compose ile projeyi başlatın:**
    Projenin ana dizininde aşağıdaki komutu çalıştırın:

    ```bash
    docker-compose up --build
    ```

    Bu komut, `postgres`, `mongo`, `redis` ve `api` servislerini başlatacaktır. API, `http://localhost:8000` adresinde erişilebilir olacaktır.

4.  **Veritabanı Migration'ları:**
    Veritabanı tablolarını oluşturmak için Alembic migration'larını çalıştırmanız gerekebilir. API container'ı içinden bu komutu çalıştırabilirsiniz:

    ```bash
    docker-compose exec api alembic upgrade head
    ```

## 📚 API Endpoints

Proje, Swagger UI üzerinden interaktif bir API dokümantasyonu sunar. Projeyi çalıştırdıktan sonra `http://localhost:8000/docs` adresini ziyaret edebilirsiniz.

### Ana Endpoints:

* `POST /auth/register`: Yeni kullanıcı kaydı oluşturur.
* `POST /auth/token`: Kullanıcı girişi yaparak JWT token alır.
* `GET /auth/users/me`: Mevcut kullanıcı bilgilerini döndürür.
* `POST /recognize/`: Bir ses dosyası yükleyerek müzik tanıma işlemini başlatır ve bir görev ID'si döndürür.
* `GET /recognize/result/{task_id}`: Başlatılan tanıma görevinin sonucunu sorgular.
* `GET /recommend/{song_id}`: Belirtilen şarkıya benzer şarkıları önerir.
* `POST /me/playlists/`: Mevcut kullanıcı için yeni bir çalma listesi oluşturur.
* `GET /me/playlists/`: Kullanıcının çalma listelerini listeler.
* `POST /me/history/`: Bir tanıma sonucunu kullanıcının geçmişine ekler.
* `GET /me/history/`: Kullanıcının tanıma geçmişini listeler.

## 🧪 Testler

Proje testleri Pytest kullanılarak yazılmıştır. Testleri çalıştırmak için aşağıdaki komutu projenin ana dizininde çalıştırabilirsiniz:

```bash
pytest
```

## 📂 Proje Yapısı

```
/
├── api/                # FastAPI uygulama kodları ve endpointler
│   ├── v1/             # API version 1 endpointleri (auth, playlists, recognition vb.)
│   └── main.py         # Ana FastAPI uygulaması
├── core/               # Ana iş mantığı
│   ├── fingerprint/    # Ses parmak izi çıkarma ve eşleştirme
│   ├── reco/           # Tavsiye motoru ve özellik çıkarma
│   └── repository/     # Veritabanı işlemleri için repository sınıfları
├── db/                 # Veritabanı konfigürasyonları
│   ├── sql/            # SQL (PostgreSQL) modelleri ve ayarları
│   └── nosql/          # NoSQL (MongoDB) koleksiyonları ve ayarları
├── worker/             # Celery worker ve arka plan görevleri
├── tests/              # Pytest test dosyaları
├── alembic/            # Veritabanı migration dosyaları
├── docker-compose.yml  # Docker servis tanımlamaları
├── requirements.txt    # Proje bağımlılıkları
└── run.sh              # Sunucuyu ve Celery worker'ı başlatan betik
```
