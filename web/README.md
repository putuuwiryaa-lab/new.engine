# NEW.ENGINE Web

Mobile-first Next.js research console untuk pipeline NEW.ENGINE.

## Arsitektur

```text
Vercel / Next.js mobile web
        ↓ server-side read
Supabase / markets
        ↑ scheduled write
Render / Python scraper + engine
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
- halaman detail, statistik posisi, dan histori responsif;
- metadata mobile web app dan mode standalone.

Tabel registry tetap tersedia untuk tablet dan desktop. Manifest tidak menyediakan offline cache; koneksi tetap diperlukan untuk membaca Supabase.

## Fitur v0.1

- ringkasan jumlah market;
- status freshness data;
- jumlah market dengan 1.200 result;
- pencarian dan filter registry;
- latest result dan timestamp setiap market;
- halaman detail 120 result terbaru;
- statistik frekuensi digit per posisi;
- endpoint health `/api/health`;
- label engine `research_only` dan release gate terkunci.

Statistik frekuensi pada halaman detail bersifat deskriptif. Statistik tersebut bukan prediksi dan bukan keputusan rilis engine.

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

Tidak perlu mengubah konfigurasi Render. Render tetap menjalankan `python run_scrapers.py` setiap enam jam.

## Verifikasi mobile

Periksa deployment pada lebar berikut:

```text
320 × 568
360 × 800
390 × 844
412 × 915
```

Pastikan tidak ada scroll horizontal, header tidak menutupi konten, kartu dapat disentuh dengan nyaman, dan detail market dapat dibuka dari setiap kartu.

## Health check

```text
GET /api/health
```

Status `200` berarti data tersedia dan tidak ada market stale. Status `503` berarti dashboard masih dapat dibuka, tetapi terdapat market stale atau registry kosong. Status `500` berarti konfigurasi atau akses Supabase gagal.
