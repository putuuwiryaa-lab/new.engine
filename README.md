# NEW.ENGINE

Tahap saat ini: **Phase 1 — scraper migration and validation**.

Repository ini sementara berisi dua scraper lama yang dipindahkan dari `backup-`:

- `scraper.py` — scraper utama untuk 58 market dan upsert ke Supabase.
- `scraper_rajapaito.py` — scraper Rajapaito untuk 13 market dan output ke console.

Kedua scraper menggunakan maksimal **1.200 result per market**. Nilai tersebut dapat diubah melalui `SCRAPE_HISTORY_LIMIT`.

## Persyaratan

- Python 3.11 atau lebih baru
- Supabase project untuk menjalankan `scraper.py` secara live

## Instalasi

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

## Environment

Salin template:

```bash
cp .env.example .env
```

Isi credential Supabase baru pada `.env`, lalu export sebelum menjalankan scraper:

```bash
set -a
source .env
set +a
```

Variable yang digunakan:

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SCRAPE_HISTORY_LIMIT=1200
```

Jangan commit file `.env` atau service-role key.

## Smoke test

Smoke test tidak mengakses website asli dan tidak menulis ke Supabase. Request HTTP dan client Supabase diganti dengan mock.

```bash
python -m unittest discover -s tests -v
```

Yang diperiksa:

- kedua scraper dapat di-import;
- default limit adalah 1.200;
- registry berisi 58 dan 13 market;
- parser mempertahankan 1.200 result terbaru;
- `scraper.py` melakukan satu upsert untuk setiap market.

## Live test

Jalankan Rajapaito lebih dahulu karena belum menulis ke database:

```bash
python scraper_rajapaito.py
```

Periksa setiap market memiliki:

- `TOTAL` lebih dari nol;
- `LATEST` berupa empat digit;
- urutan histori dari lama ke terbaru.

Setelah environment Supabase terisi, jalankan scraper utama:

```bash
python scraper.py
```

Periksa output terminal dan tabel `markets` di Supabase. Jangan menjalankan scraper utama dengan credential database production lama.

## Status implementasi

Sudah tersedia:

- dua scraper hasil migrasi;
- limit histori configurable dengan default 1.200;
- dependency Python;
- template environment;
- proteksi file secret melalui `.gitignore`;
- smoke test tanpa jaringan dan tanpa database nyata.

Belum tersedia:

- penyimpanan hasil Rajapaito ke Supabase baru;
- retry terkontrol;
- structured logging;
- validation guard sebelum upsert;
- runner gabungan;
- scheduler Render enam jam sekali;
- AI Engine dan dashboard.
