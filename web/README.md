# NEW.ENGINE Web

Mobile-first Next.js research console untuk pipeline NEW.ENGINE.

## Arsitektur

```text
Vercel / Next.js mobile web
        ↓ server-side read
Supabase / markets + engine audits
        ↑ scheduled write
Render / Python full pipeline
```

Web ditempatkan di Vercel. Scraper dan engine Python tetap berjalan di Render karena keduanya merupakan scheduled/background compute, bukan request web interaktif.

## Mobile-first

Antarmuka dirancang untuk penggunaan utama pada layar ponsel 320–430 px:

- safe-area untuk notch dan home indicator;
- header ringkas dan sticky;
- kartu market sebagai pengganti tabel horizontal;
- target sentuh minimal sekitar 44 px;
- pencarian dan filter berukuran penuh;
- kartu metrik 2×2;
- pipeline dapat digeser horizontal;
- halaman detail, statistik posisi, histori, dan audit responsif;
- metadata mobile web app dan mode standalone.

Tabel registry tetap tersedia untuk tablet dan desktop. Manifest tidak menyediakan offline cache; koneksi tetap diperlukan untuk membaca Supabase.

## Fitur

Data console:

- ringkasan jumlah market;
- status freshness data;
- jumlah market dengan 1.200 result;
- pencarian dan filter registry;
- latest result dan timestamp setiap market;
- halaman detail 120 result terbaru;
- statistik frekuensi digit per posisi;
- endpoint health `/api/health`.

Engine audit console:

- halaman `/engine` untuk run terbaru;
- status run, sumber, durasi, jumlah evaluated market, validation error, dan engine error;
- konfigurasi window, horizon, top-k, minimum training, dan recency half-life;
- pencarian dan filter audit seluruh market;
- kandidat terbaik AS, KOP, KEPALA, dan EKOR;
- top digit, model, window, horizon, lift, dan recent hit rate;
- halaman detail audit per market;
- hit rate, baseline, sample size, miss streak, mean actual probability, log loss, dan Brier score;
- distribusi probabilitas digit 0–9;
- navigasi dua arah antara snapshot data dan audit engine.

Seluruh audit tetap diberi label `research_only`. Statistik deskriptif dan output audit bukan prediksi produksi.

## Environment

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
DASHBOARD_STALE_HOURS=8
```

`SUPABASE_SERVICE_ROLE_KEY` hanya digunakan oleh Server Components dan Route Handler. Jangan menggunakan prefix `NEXT_PUBLIC_` dan jangan memindahkan key tersebut ke komponen client.

## Development

```bash
cd web
npm install
npm run dev
```

Type check dan production build:

```bash
npm run typecheck
npm run build
```

## Deploy ke Vercel

1. Import repository `putuuwiryaa-lab/new.engine`.
2. Set **Root Directory** menjadi `web`.
3. Framework Preset akan terdeteksi sebagai **Next.js**.
4. Tambahkan environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `DASHBOARD_STALE_HOURS=8`
5. Deploy.

Tidak perlu mengubah konfigurasi Render. Render menjalankan `python run_pipeline.py` setiap enam jam dan mengisi tabel market serta audit engine.

## Verifikasi mobile

Periksa deployment pada lebar berikut:

```text
320 × 568
360 × 800
390 × 844
412 × 915
```

Pastikan tidak ada scroll horizontal, header tidak menutupi konten, kartu dapat disentuh dengan nyaman, dan halaman `/engine` serta detail audit dapat dibuka dari ponsel.

## Health check

```text
GET /api/health
```

Status `200` berarti data tersedia dan tidak ada market stale. Status `503` berarti dashboard masih dapat dibuka, tetapi terdapat market stale atau registry kosong. Status `500` berarti konfigurasi atau akses Supabase gagal.
