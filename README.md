# NEW.ENGINE

Tahap saat ini: **Phase 1 — automatic scraper pipeline**.

Repository menjalankan dua scraper dan menyimpan hasil langsung ke tabel Supabase `markets`:

- `scraper.py` — 58 market;
- `scraper_rajapaito.py` — 13 market;
- `run_scrapers.py` — menjalankan keduanya secara berurutan;
- `scraper_runtime.py` — retry, validasi, dan snapshot replacement guard.

Total registry saat ini adalah **71 market**. Setiap market menyimpan maksimal **1.200 result**, dengan urutan histori lama ke terbaru.

## Environment

Variable wajib:

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

Variable dengan default:

```env
SCRAPE_HISTORY_LIMIT=1200
RAJAPAITO_ORDER_START=59
SCRAPE_RETRY_ATTEMPTS=3
SCRAPE_RETRY_BACKOFF_SECONDS=2,5,10
SCRAPE_RETRY_JITTER_SECONDS=1
SCRAPE_MIN_RESULTS=28
SCRAPE_MIN_RETENTION_RATIO=0.5
```

Jangan commit credential asli atau file `.env`.

## Struktur tabel Supabase

Kedua scraper melakukan upsert ke tabel `markets` dengan kolom:

```text
id           text primary key
name         text
history_data text
order        integer
updated_at   timestamptz
```

`id` harus unik agar setiap eksekusi memperbarui market yang sama dan tidak membuat duplikasi baris.

## Eksekusi produksi

```bash
python run_scrapers.py
```

Runner menjalankan:

```text
scraper.py
→ scraper_rajapaito.py
→ ringkasan 71 market
→ exit code 0 jika seluruh market berhasil
→ exit code 1 jika ada market gagal, kosong, atau ditolak guard
```

Rajapaito menggunakan nomor urut 59–71 agar tidak bertabrakan dengan 58 market scraper utama.

## Retry dan perlindungan data

Setiap HTTP request dicoba maksimal tiga kali untuk network error, HTTP 408, HTTP 429, dan HTTP 5xx. Backoff default adalah 2, 5, dan 10 detik dengan jitter maksimal satu detik.

Snapshot tidak ditulis ke Supabase apabila:

- histori kosong;
- ada token yang bukan empat digit;
- jumlah data kurang dari 28;
- jumlah snapshot baru kurang dari 50% snapshot yang sudah tersimpan.

Contoh log:

```text
OK: market=SINGAPORE total=1200 latest=1234 order=6
REJECT: market=MACAU P1 total=20 reason=insufficient_history:20<28
REJECT: market=JAPAN total=400 reason=suspicious_history_drop:400<600 previous=1200
WARN: request_retry url=... attempt=1/3 delay=2.41s error=...
```

Snapshot lama tetap aman ketika snapshot baru ditolak.

## Otomatis setiap 6 jam di Render

`render.yaml` mendefinisikan satu Render Cron Job:

```text
Nama       : new-engine-scrapers
Runtime    : Python
Command    : python run_scrapers.py
Schedule   : 0 */6 * * *
Auto deploy: setiap commit ke branch terhubung
```

Schedule menggunakan UTC:

```text
00:00 UTC = 08:00 WITA
06:00 UTC = 14:00 WITA
12:00 UTC = 20:00 WITA
18:00 UTC = 02:00 WITA
```

## Smoke test

Smoke test tidak mengakses website asli dan tidak menulis ke Supabase nyata:

```bash
python -m unittest discover -s tests -v
```

Test mencakup:

- default limit dan konfigurasi keamanan;
- registry 58 dan 13 market;
- parser mempertahankan 1.200 result terbaru;
- retry setelah network error sementara;
- penolakan penurunan histori abnormal;
- 58 upsert scraper utama;
- 13 upsert Rajapaito dengan order 59–71;
- status berhasil atau gagal dari runner.

## Status berikutnya

Setelah beberapa siklus Cron stabil:

1. verifikasi konsistensi 71 market;
2. tambahkan structured run history;
3. normalisasi histori menjadi tabel draw per periode jika tanggal dan period tersedia;
4. mulai Phase 2 Adaptive Probability Engine.
