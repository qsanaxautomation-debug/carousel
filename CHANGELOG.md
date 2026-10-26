# Changelog

Semua perubahan penting pada repo ini dicatat di sini.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.1.0/).
Versi mengikuti [Semantic Versioning](https://semver.org/lang/id/).

---

## [1.0.0] — 2026-10-26

Rilis pertama. Lima workflow carousel Instagram yang sudah disanitasi, dokumentasi lengkap, dan perkakas verifikasi.

### Ditambahkan

**Workflow**

- `01-ai-carousel-telegram-bot.json` — 16 node. Input Telegram → naskah carousel via Gemini → kirim ringkasan + detail slide ke Telegram → simpan baris `pending` ke Google Sheets.
- `02-generate-gambar-nvidia.json` — 12 node. Ambil satu baris pending → susun prompt per slide → generate via NVIDIA FLUX.1-schnell → unggah ke ImgBB → tulis `image_urls` ke Sheets.
- `03-simpan-ke-google-sheet.json` — 3 node. Webhook `POST /webhook/simpan-carousel` → rapikan field → tulis ke spreadsheet arsip.
- `04-antrean-otomatis-composio.json` — 45 node. Jadwal 5 menit → pilih baris terbaru → render gambar dengan `editImage` (teks vektor, bukan difusi) → preview Telegram → dua gerbang persetujuan → publish via Composio → tandai status. Termasuk tiga jalur kegagalan dan Error Trigger.
- `05-ai-carousel-lengkap-zernio.json` — 35 node. Alur penuh tanpa Sheets: Telegram → naskah → generate via Pollinations (tanpa API key) → unggah ImgBB → preview Telegram → publish via Zernio → arsip lewat webhook.

**Dokumentasi**

- `README.md` — ringkasan, diagram alur, tabel perbandingan workflow, quick start, batasan yang diketahui, struktur repo.
- `docs/01-instalasi.md` — 12 bagian, dari prasyarat sampai checklist akhir.
- `docs/02-kredensial.md` — cara membuat dan memasang 7 jenis credential, plus tabel ringkas node → credential.
- `docs/03-google-sheets.md` — 42 header wajib, arti tiap kolom, spreadsheet arsip, jebakan umum.
- `docs/04-arsitektur.md` — alasan desain di balik setiap node, termasuk kenapa gambar dirender lokal di workflow 4.
- `docs/05-alur-status.md` — diagram status, tabel transisi, cara mengulang carousel yang gagal.
- `docs/06-troubleshooting.md` — error umum per komponen dengan penyebab dan solusi.
- `docs/07-faq.md` — pertanyaan umum, kustomisasi, dan operasional.

**Contoh & perkakas**

- `examples/carousel-sheet-template.csv` — header 42 kolom plus satu baris contoh terisi.
- `examples/.env.example` — contoh konfigurasi environment.
- `scripts/check-secrets.sh` — pemeriksa kebocoran data sensitif.
- `scripts/verify-repo.py` — pemeriksa link, anchor, validitas JSON workflow, dan placeholder.

### Keamanan

- Semua blok `credentials` dihapus dari kelima workflow. Pengguna memasang credential sendiri setelah import.
- Semua nilai asli (API key, ID spreadsheet, chat ID, domain, username) diganti placeholder `REPLACE_WITH_*`.
- `.gitignore` memblokir `.env`, `*.key`, `credentials*.json`, `client_secret*.json`, dan workflow hasil edit lokal.

### Catatan

- Node `editImage` (dipakai workflow 4) memerlukan versi n8n yang lebih baru. Perbarui n8n sebelum import.
- Workflow 4 hanya memproses baris berumur 0–120 menit, dihitung dari timestamp di kolom `id`.
- ImgBB paket gratis menghapus gambar setelah 24 jam.
