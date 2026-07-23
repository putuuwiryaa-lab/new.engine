# NEW.ENGINE

Tahap saat ini: **Phase 2 — Engine Core v0.1 (research only)**.

Repository memiliki tiga komponen:

1. scraper otomatis yang memperbarui histori 71 market di Supabase;
2. engine riset yang menjalankan walk-forward evaluation dan menghasilkan audit probabilitas per posisi digit;
3. mobile-first Next.js research console di folder `web/`.

Engine v0.1 belum menerbitkan BBFS, Angka Ikut, atau prediksi produksi. Seluruh output tetap berstatus `research_only`.

## Phase 1 — Automatic scraper pipeline

Komponen:

- `scraper.py` — 58 market;
- `scraper_rajapaito.py` — 13 market;
- `run_scrapers.py` — menjalankan keduanya secara berurutan;
- `scraper_runtime.py` — retry, validasi, dan snapshot replacement guard.

Total registry adalah **71 market**. Setiap market menyimpan maksimal **1.200 result**, dengan urutan histori lama ke terbaru.

### Eksekusi produksi scraper

```bash
python run_scrapers.py
```

Render menjalankan command tersebut otomatis setiap enam jam melalui `render.yaml`.

## Phase 2 — Engine Core v0.1

Struktur utama:

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
```

Alur engine:

```text
Supabase markets
→ canonical history validation
→ adaptive windows
→ model registry
→ walk-forward evaluation
→ theoretical baseline comparison
→ deterministic candidate selection
→ auditable research output
→ optional Supabase audit persistence
```

### Model awal

- `frequency` — distribusi frekuensi digit per posisi;
- `recency_frequency` — distribusi frekuensi dengan bobot peluruhan berdasarkan usia result.

Keduanya menghasilkan distribusi probabilitas untuk digit 0–9 pada masing-masing posisi:

```text
0 = AS
1 = KOP
2 = KEPALA
3 = EKOR
```

### Walk-forward evaluation

Untuk setiap target historis:

```text
training = hanya data sebelum target
target   = result berikutnya
future data tidak masuk training
```

Kandidat diuji berdasarkan kombinasi:

```text
model × window × evaluation horizon × posisi
```

Default:

```env
ENGINE_WINDOWS=70,150,300,500,700,1000
ENGINE_EVAL_HORIZONS=14,28,56
ENGINE_MIN_HISTORY=70
ENGINE_MIN_TRAIN_SIZE=50
ENGINE_TOP_K=5
ENGINE_RECENT_EVAL_SIZE=14
ENGINE_LAPLACE_ALPHA=1
ENGINE_RECENCY_HALF_LIFE=60
```

Window yang melebihi histori tersedia tidak digunakan. Bila tidak ada window konfigurasi yang memenuhi, engine memakai seluruh training history yang tersedia selama batas minimal training tercapai.

### Metrik audit

Setiap kandidat mencatat:

- sample size;
- hit count dan hit rate;
- theoretical baseline hit rate;
- lift terhadap baseline;
- recent hit rate;
- longest miss streak;
- mean probability untuk digit aktual;
- log loss;
- Brier score.

Pemilihan kandidat menggunakan urutan deterministik, bukan weighted score tersembunyi. Prioritas dimulai dari lift, sample size, recent hit rate, probability quality, log loss, dan Brier score.

### Menjalankan engine

Gunakan environment Supabase yang sama dengan scraper:

```bash
python run_engine.py
```

Untuk membatasi market selama riset:

```env
ENGINE_MARKETS=SINGAPORE,JAPAN
```

Output berupa JSON audit per market dan ringkasan akhir. Contoh status:

```json
{
  "engine_version": "0.1.0",
  "release_status": "research_only"
}
```

Engine belum dimasukkan ke Cron Job Render. Aktivasi otomatis dilakukan setelah persistence dan runtime live diverifikasi.

### Audit persistence

Persistence bersifat opt-in dan default-nya nonaktif:

```env
ENGINE_PERSIST_AUDITS=false
ENGINE_RUN_SOURCE=manual
```

Setelah tabel Supabase dibuat, ubah `ENGINE_PERSIST_AUDITS=true`. Setiap eksekusi akan menyimpan satu record pada `engine_runs` dan satu audit per market pada `engine_market_audits`.

SQL pembuatan tabel tidak disimpan di repository. SQL diberikan langsung melalui chat atau prosedur deployment terkontrol.

## Environment

Variable wajib:

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

Variable scraper:

```env
SCRAPE_HISTORY_LIMIT=1200
RAJAPAITO_ORDER_START=59
SCRAPE_RETRY_ATTEMPTS=3
SCRAPE_RETRY_BACKOFF_SECONDS=2,5,10
SCRAPE_RETRY_JITTER_SECONDS=1
SCRAPE_MIN_RESULTS=28
SCRAPE_MIN_RETENTION_RATIO=0.5
```

Variable engine tersedia di `.env.example` dan seluruhnya memiliki default.

Jangan commit credential asli atau file `.env`.

## Struktur tabel Supabase

Scraper dan engine membaca tabel `markets`:

```text
id           text primary key
name         text
history_data text
order        integer
updated_at   timestamptz
```

Persistence engine menggunakan tabel berikut setelah diaktifkan:

```text
engine_runs
engine_market_audits
```

Kedua tabel tersebut menyimpan audit riset, bukan prediksi produksi.

## Mobile-first web console

Folder `web/` berisi aplikasi Next.js untuk Vercel. UI menampilkan registry market, freshness, history depth, detail result, dan statistik deskriptif. Layout utama menggunakan kartu sentuh pada layar ponsel dan tabel pada desktop.

Web belum menampilkan audit engine sampai persistence live selesai diverifikasi.

## Perlindungan data scraper

Snapshot tidak ditulis ke Supabase apabila:

- histori kosong;
- ada token yang bukan empat digit;
- jumlah data kurang dari 28;
- jumlah snapshot baru kurang dari 50% snapshot yang sudah tersimpan.

Snapshot lama tetap aman ketika snapshot baru ditolak.

## Test

Semua test tidak mengakses website asli dan tidak menulis ke Supabase nyata:

```bash
python -m unittest discover -s tests -v
```

Coverage scraper mencakup parser, retry, guard, upsert, dan runner.

Coverage engine mencakup:

- preservasi duplikasi result;
- adaptive windows;
- normalisasi distribusi probabilitas;
- respons model recency terhadap regime terbaru;
- walk-forward tanpa future leakage;
- pemisahan market invalid;
- output audit berstatus `research_only`;
- lifecycle audit persistence dan status run.

## Batas Phase 2 v0.1

Belum tersedia:

- release gate produksi;
- prediction journal;
- settlement otomatis;
- model transition, delta, motif, cycle, momentum, dan regime;
- ensemble;
- BBFS dan Angka Ikut;
- scheduler engine di Render;
- tampilan audit engine pada web.

Langkah berikutnya adalah membuat dua tabel persistence di Supabase, mengaktifkan persistence untuk satu atau dua market, lalu memeriksa hasil audit sebelum menambahkan scheduler engine.
