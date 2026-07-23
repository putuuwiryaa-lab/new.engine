# NEW.ENGINE

Tahap saat ini: **Phase 2 — automated research engine pipeline + mobile audit console**.

NEW.ENGINE terdiri dari tiga komponen:

1. scraper Python untuk 71 market;
2. Engine Core v0.1 untuk walk-forward probability audit;
3. mobile-first Next.js research console pada folder `web/`.

Seluruh output engine masih berstatus `research_only`. Sistem belum menerbitkan BBFS, Angka Ikut, atau prediksi produksi.

## Production pipeline

Render menjalankan satu Cron Job setiap enam jam:

```text
python run_pipeline.py
```

Alur lengkap:

```text
scraper utama (58 market)
→ scraper Rajapaito (13 market)
→ validation dan snapshot guard
→ Engine Core untuk seluruh market valid
→ walk-forward evaluation
→ audit persistence ke Supabase
→ final pipeline status
```

Engine tetap dijalankan menggunakan snapshot lama yang valid apabila sebagian scraper gagal. Namun Cron Job tetap keluar dengan status gagal agar masalah ingest terlihat pada monitoring.

Konfigurasi produksi berada di `render.yaml`:

```text
Schedule   : 0 */6 * * *
Command    : python run_pipeline.py
Markets    : seluruh registry, tanpa ENGINE_MARKETS filter
Persistence: aktif
```

Schedule menggunakan UTC:

```text
00:00 UTC = 08:00 WITA
06:00 UTC = 14:00 WITA
12:00 UTC = 20:00 WITA
18:00 UTC = 02:00 WITA
```

## Scraper

Komponen:

```text
scraper.py
scraper_rajapaito.py
scraper_runtime.py
run_scrapers.py
```

Perlindungan data:

- retry untuk network error, HTTP 408, 429, dan 5xx;
- setiap result harus empat digit;
- snapshot minimal 28 result;
- snapshot baru ditolak bila jumlahnya turun di bawah 50% snapshot lama;
- maksimal 1.200 result per market.

## Engine Core v0.1

Struktur:

```text
engine/
  config.py
  data_loader.py
  validator.py
  windows.py
  baselines.py
  evaluator.py
  registry.py
  output_builder.py
  persistence.py
  runner.py
  models/
    frequency.py
    recency_frequency.py
run_engine.py
run_pipeline.py
```

Model awal:

- `frequency`;
- `recency_frequency`.

Kandidat diuji untuk posisi AS, KOP, KEPALA, dan EKOR menggunakan kombinasi:

```text
model × window × evaluation horizon × posisi
```

Default produksi:

```env
ENGINE_WINDOWS=70,150,300,500,700,1000
ENGINE_EVAL_HORIZONS=14,28,56
ENGINE_MIN_HISTORY=70
ENGINE_MIN_TRAIN_SIZE=50
ENGINE_TOP_K=5
ENGINE_RECENT_EVAL_SIZE=14
ENGINE_LAPLACE_ALPHA=1
ENGINE_RECENCY_HALF_LIFE=60
ENGINE_PERSIST_AUDITS=true
ENGINE_RUN_SOURCE=render_cron_full
```

Walk-forward selalu menggunakan data sebelum target. Target dan data masa depan tidak masuk training.

Metrik audit:

- sample size;
- hit count dan hit rate;
- theoretical baseline;
- lift;
- recent hit rate;
- longest miss streak;
- mean actual probability;
- log loss;
- Brier score.

## Supabase

Tabel ingest:

```text
markets
```

Tabel audit engine:

```text
engine_runs
engine_market_audits
```

Setiap full run membuat satu record `engine_runs` dan satu `engine_market_audits` untuk setiap market yang berhasil dievaluasi. Status run dapat berupa `running`, `succeeded`, `partial`, atau `failed`.

SQL schema tidak disimpan dalam repository. SQL diberikan langsung melalui prosedur deployment terkontrol.

## Mobile-first web console

Aplikasi Next.js berada di `web/` dan ditujukan untuk Vercel.

```text
Vercel / Next.js
        ↓ server-side read
Supabase
        ↑ scheduled write
Render / Python pipeline
```

Fitur saat ini:

- registry 71 market;
- freshness dan history depth;
- latest result;
- pencarian dan filter;
- halaman detail market;
- statistik deskriptif posisi digit;
- mobile card layout dan desktop table;
- web-app manifest dan safe-area support;
- halaman `/engine` untuk run audit terbaru;
- pencarian dan filter kualitas audit market;
- ringkasan kandidat terbaik AS, KOP, KEPALA, dan EKOR;
- detail model, window, horizon, lift, hit rate, sample size, miss streak, log loss, Brier score, top digit, dan distribusi probabilitas;
- navigasi dua arah antara snapshot data dan audit engine.

Audit yang tampil tetap berstatus `research_only` dan tidak boleh diperlakukan sebagai prediksi produksi.

## Environment lokal

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SCRAPE_HISTORY_LIMIT=1200
RAJAPAITO_ORDER_START=59
SCRAPE_RETRY_ATTEMPTS=3
SCRAPE_RETRY_BACKOFF_SECONDS=2,5,10
SCRAPE_RETRY_JITTER_SECONDS=1
SCRAPE_MIN_RESULTS=28
SCRAPE_MIN_RETENTION_RATIO=0.5
ENGINE_WINDOWS=70,150,300,500,700,1000
ENGINE_EVAL_HORIZONS=14,28,56
ENGINE_MIN_HISTORY=70
ENGINE_MIN_TRAIN_SIZE=50
ENGINE_TOP_K=5
ENGINE_RECENT_EVAL_SIZE=14
ENGINE_LAPLACE_ALPHA=1
ENGINE_RECENCY_HALF_LIFE=60
ENGINE_MARKETS=
ENGINE_PERSIST_AUDITS=false
ENGINE_RUN_SOURCE=manual
```

Jangan commit credential asli atau file `.env`.

## Test

```bash
python -m unittest discover -s tests -v
```

Coverage mencakup scraper parser, retry, guard, Supabase upsert, engine validation, adaptive windows, probability models, anti-future-leakage walk-forward, audit persistence, dan orchestration full pipeline.

Web CI menjalankan TypeScript typecheck dan production build untuk folder `web/`.

## Batas saat ini

Belum tersedia:

- release gate produksi;
- prediction journal;
- automatic settlement;
- transition, delta, motif, cycle, momentum, dan regime models;
- ensemble;
- BBFS, Angka Ikut, angka mati, confidence, dan risk output.

Langkah berikutnya adalah membangun release gate berbasis evidence yang menahan kandidat lemah sebelum prediction journal diperkenalkan.
