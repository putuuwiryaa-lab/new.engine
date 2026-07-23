# NEW.ENGINE

Tahap saat ini: **Phase 1 — automatic scraper pipeline**.

Repository menjalankan dua scraper dan menyimpan hasil langsung ke tabel Supabase `markets`:

- `scraper.py` — 58 market.
- `scraper_rajapaito.py` — 13 market.
- `run_scrapers.py` — menjalankan keduanya secara berurutan.

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

## Eksekusi gabungan

Command produksi:

```bash
python run_scrapers.py
```

Runner menjalankan:

```text
scraper.py
→ scraper_rajapaito.py
→ ringkasan 71 market
→ exit code 0 jika seluruh market berhasil
→ exit code 1 jika ada market gagal atau kosong
```

Rajapaito menggunakan nomor urut 59–71 agar tidak bertabrakan dengan 58 market scraper utama.

## Otomatis setiap 6 jam di Render

File `render.yaml` mendefinisikan satu Render Cron Job:

```text
Nama       : new-engine-scrapers
Runtime    : Python
Command    : python run_scrapers.py
Schedule   : 0 */6 * * *
Auto deploy: setiap commit ke branch terhubung
```

Schedule Render menggunakan UTC:

```text
00:00 UTC = 08:00 WITA
06:00 UTC = 14:00 WITA
12:00 UTC = 20:00 WITA
18:00 UTC = 02:00 WITA
```

### Aktivasi satu kali di Render

1. Buka Render Dashboard.
2. Pilih **New → Blueprint**.
3. Hubungkan repository `putuuwiryaa-lab/new.engine` branch `main`.
4. Render membaca `render.yaml` dari root repository.
5. Isi `SUPABASE_URL` dan `SUPABASE_SERVICE_ROLE_KEY` ketika diminta.
6. Terapkan Blueprint.

Setelah aktivasi tersebut, tidak perlu menjalankan scraper dari terminal. Render akan membangun ulang saat repository berubah dan menjalankan scraper setiap enam jam.

Render Cron Job tidak menyediakan paket gratis. Periksa biaya Cron Job pada akun Render sebelum menerapkan Blueprint.

## Instalasi lokal untuk pengembangan

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Smoke test

Smoke test tidak mengakses website asli dan tidak menulis ke Supabase nyata:

```bash
python -m unittest discover -s tests -v
```

Test mencakup:

- default limit 1.200;
- registry 58 dan 13 market;
- parser mempertahankan 1.200 result terbaru;
- scraper utama melakukan 58 upsert;
- Rajapaito melakukan 13 upsert dengan order 59–71;
- runner mengembalikan status berhasil atau gagal dengan benar.

## Status berikutnya

Setelah Cron Job pertama berhasil:

1. periksa 71 baris market pada Supabase;
2. periksa jumlah histori setiap market;
3. periksa result terbaru;
4. tambahkan retry terkontrol;
5. tambahkan validation guard sebelum snapshot lama diganti;
6. tambahkan structured logging dan tabel riwayat eksekusi.
