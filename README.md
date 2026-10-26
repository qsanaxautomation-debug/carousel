# AI Carousel Instagram — Telegram → Gambar → Posting Otomatis

Otomasi produksi konten **carousel Instagram** end-to-end dengan [n8n](https://n8n.io): kirim topik lewat Telegram, AI menyusun hook + slide + caption, gambar dibuat otomatis, Anda menyetujui lewat tombol di Telegram, lalu carousel diposting ke Instagram.

Dibangun dengan n8n + Google Gemini + Google Sheets + Telegram, dengan opsi pembuatan gambar (NVIDIA FLUX, Pollinations) dan opsi posting (Composio, Zernio).

```
Topik via Telegram
        │
        ▼
  AI Agent (Gemini) ──► Hook + 7-10 slide + caption + hashtag
        │
        ▼
  Preview di Telegram  ──►  [🎨 Buat Gambar]  /  [⏭️ Lewati]
        │
        ▼
  Gambar per slide (1080×1080, teks + watermark)
        │
        ▼
  Upload ke host publik (ImgBB)
        │
        ▼
  Preview foto  ──►  [📲 Posting]  /  [❌ Batal]
        │
        ▼
  Instagram carousel (Composio / Zernio)
        │
        ▼
  Status tercatat di Google Sheets
```

---

## Daftar Isi

- [Fitur](#fitur)
- [Lima Workflow](#lima-workflow)
- [Kebutuhan Sistem](#kebutuhan-sistem)
- [Instalasi Cepat](#instalasi-cepat)
- [Cara Pakai](#cara-pakai)
- [Struktur Repositori](#struktur-repositori)
- [Batasan yang Diketahui](#batasan-yang-diketahui)
- [Dokumentasi Lanjutan](#dokumentasi-lanjutan)
- [Lisensi](#lisensi)

---

## Fitur

| Fitur | Keterangan |
|---|---|
| Input lewat Telegram | Kirim topik bebas, bot menyusun carousel |
| Struktur konten konsisten | Output parser memaksa JSON: title, hook, slides[], closing_slide, caption |
| Human-in-the-loop 2 lapis | Persetujuan sebelum buat gambar, dan sebelum posting |
| Dua mesin gambar | NVIDIA FLUX.1-schnell (kualitas tinggi) atau Pollinations FLUX (gratis) |
| Teks di atas gambar | Node Edit Image menulis nomor slide, judul, isi, dan watermark langsung ke kanvas 1080×1080 |
| Antrean terjadwal | Workflow antrean berjalan tiap 5 menit memproses baris `pending` di Sheets |
| Dua akun Instagram | Cabang persetujuan memungkinkan posting ke akun kedua |
| Pelacakan status | Kolom `status` di Sheets: `pending` → `posted` / `failed` / `rejected` / `skipped` |
| Notifikasi kegagalan | Error Trigger memberi tahu node mana yang gagal dan menandai baris `failed` |
| Watermark per baris | Kolom `watermark` di Sheets, fallback `@AKUN_UTAMA` |

---

## Lima Workflow

Repo ini memuat lima workflow yang bisa dipakai terpisah atau dirangkai.

### 1. `01-ai-carousel-telegram-bot.json`

**Inti paling sederhana: teks saja, tanpa gambar.**

Telegram Trigger → kirim pesan "sedang dibuat" → AI Agent (Gemini + structured output parser) → format ringkasan + detail slide → kirim ke Telegram → simpan satu baris ke tab `Carousel` dengan status `pending`.

Cocok kalau Anda hanya butuh naskah carousel dan desain dikerjakan manual (Canva/Figma).

### 2. `02-generate-gambar-nvidia.json`

**Pembuat gambar batch, dipicu manual.**

Ambil baris `pending` yang `image_urls` masih kosong → batasi 1 baris → susun prompt per slide → NVIDIA FLUX.1-schnell → ubah base64 jadi binary → upload ImgBB → tulis `image_urls` ke Sheets.

Naikkan batas di node **Batasi 1 Baris** setelah uji coba pertama berhasil.

### 3. `03-simpan-ke-google-sheet.json`

**Webhook arsip.** Menerima `POST /webhook/simpan-carousel` lalu append satu baris ke spreadsheet arsip (tab `Sheet1`). Dipakai workflow 5 sebagai tujuan penyimpanan.

### 4. `04-antrean-otomatis-composio.json`

**Produksi penuh, terjadwal, 45 node — workflow utama.**

Schedule tiap 5 menit → ambil baris `pending` → pilih hanya baris berumur < 120 menit → minta persetujuan buat gambar → gambar dirangkai dengan node Edit Image (latar + teks + watermark) → ImgBB → `image_ready` → kirim semua foto sebagai preview → minta persetujuan posting → buat container carousel di Instagram via Composio → publish → `posted`.

Termasuk cabang akun kedua (`@AKUN_KEDUA`), penanganan gagal container/publish, penolakan, dan Error Trigger.

### 5. `05-ai-carousel-lengkap-zernio.json`

**Produksi penuh, dipicu Telegram, tanpa Sheets.**

Telegram Trigger → AI Agent → preview teks → persetujuan buat gambar → Pollinations FLUX per slide → kirim foto satu per satu ke Telegram → persetujuan posting → Zernio (`/api/v1/posts`) → simpan ke Sheets lewat webhook workflow 3.

Paling cepat dicoba karena tidak butuh Google Sheets untuk berjalan.

---

## Kebutuhan Sistem

| Komponen | Keterangan |
|---|---|
| n8n | Self-hosted atau Cloud. Workflow dibuat pada instance yang mendukung node versi terbaru (Telegram `sendAndWait`, **Edit Image** `multiStep`, HTTP Request 4.5, Google Sheets 4.7). Pakai rilis stabil terbaru. |
| Google Gemini API | Key dari [Google AI Studio](https://aistudio.google.com/apikey). Model default `models/gemini-3.1-flash-lite`. |
| Bot Telegram | Dibuat via [@BotFather](https://t.me/BotFather) |
| Google Sheets | Dengan OAuth2 credential di n8n (workflow 1, 2, 4, 5) |
| ImgBB | API key gratis dari [api.imgbb.com](https://api.imgbb.com) — gambar dihapus otomatis 24 jam |
| NVIDIA API | Opsional, untuk workflow 2 ([build.nvidia.com](https://build.nvidia.com)) |
| Composio | Opsional, untuk workflow 4 ([composio.dev](https://composio.dev)) |
| Zernio | Opsional, untuk workflow 5 ([zernio.com](https://zernio.com)) |
| HTTPS publik | Wajib untuk webhook Telegram dan callback OAuth |

> **Catatan versi.** Belum ada satu nomor versi minimum yang diverifikasi untuk kelima workflow ini. Yang pasti: node **Edit Image** dipakai dengan operasi `multiStep`, dan Telegram `sendAndWait` dipakai untuk tombol persetujuan. Keduanya tersedia di rilis n8n modern. Jika ada node yang tidak dikenali saat import, perbarui n8n.

---

## Instalasi Cepat

Panduan lengkap: [`docs/01-instalasi.md`](docs/01-instalasi.md).

```text
1. Import workflow JSON ke n8n
2. Buat credential (Telegram, Gemini, Google Sheets, ImgBB, opsional NVIDIA/Composio/Zernio)
3. Ganti semua placeholder REPLACE_WITH_* di setiap node
4. Siapkan spreadsheet + tab Carousel dengan header yang benar
5. Pasang credential ke tiap node (credential sengaja dikosongkan di repo)
6. Uji: kirim pesan ke bot Telegram
7. Aktifkan workflow
```

Placeholder yang harus diganti:

| Placeholder | Arti |
|---|---|
| `REPLACE_WITH_CAROUSEL_SHEET_ID` | ID spreadsheet database carousel |
| `REPLACE_WITH_ARCHIVE_SHEET_ID` | ID spreadsheet arsip (workflow 3) |
| `REPLACE_WITH_TELEGRAM_ADMIN_CHAT_ID` | Chat ID admin penerima approval |
| `REPLACE_WITH_IMGBB_API_KEY` | API key ImgBB |
| `REPLACE_WITH_ZERNIO_API_KEY` | API key Zernio (`Bearer sk_...`) |
| `REPLACE_WITH_COMPOSIO_ACCOUNT_ID` | ID akun Instagram terhubung di Composio |
| `REPLACE_WITH_IG_USER_ID` | Instagram Business User ID |
| `REPLACE_WITH_IG_USERNAME` | Username akun utama (tanpa `@`) |
| `REPLACE_WITH_IG_USERNAME_2` | Username akun kedua |
| `YOUR-N8N-HOST` | Domain publik instance n8n Anda |

---

## Cara Pakai

### Mode teks saja (workflow 1)

Kirim ke bot:

```
topik: Tips produktivitas WFH | slide: 7 | tone: inspiratif | niche: lifestyle
```

Atau bebas:

```
Buatkan carousel tentang tips diet sehat untuk 8 slide dengan tone santai
```

Bot membalas dua pesan: ringkasan (hook + caption + closing) dan detail semua slide.

### Mode produksi penuh (workflow 4)

1. Isi satu baris baru di tab `Carousel` dengan `status = pending`
2. Tunggu maksimal 5 menit
3. Bot mengirim tombol **🎨 Ya, Buat Gambar** / **⏭️ Lewati**
4. Setelah gambar jadi, bot mengirim semua slide sebagai foto
5. Tekan **📲 Ya** untuk posting, atau **↪️ Akun lain / Batal**
6. Status baris berubah menjadi `posted`

---

## Struktur Repositori

```
carousel-instagram/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
├── .gitignore
├── workflows/
│   ├── 01-ai-carousel-telegram-bot.json
│   ├── 02-generate-gambar-nvidia.json
│   ├── 03-simpan-ke-google-sheet.json
│   ├── 04-antrean-otomatis-composio.json
│   └── 05-ai-carousel-lengkap-zernio.json
├── docs/
│   ├── 01-instalasi.md
│   ├── 02-kredensial.md
│   ├── 03-google-sheets.md
│   ├── 04-arsitektur.md
│   ├── 05-alur-status.md
│   ├── 06-troubleshooting.md
│   └── 07-faq.md
├── examples/
│   ├── carousel-sheet-template.csv
│   └── .env.example
└── scripts/
    ├── check-secrets.sh
    └── verify-repo.py
```

---

## Batasan yang Diketahui

| Batasan | Detail |
|---|---|
| Credential dikosongkan | Semua node tanpa credential. Wajib dipasang ulang setelah import — ini sengaja, agar repo aman dipublikasikan. |
| Hanya baris < 120 menit diproses | Node **Pilih Baris Terbaru** (workflow 4) menyaring baris berdasarkan timestamp di `id` (`CRS-yyyyMMdd-HHmmss`). Baris lebih tua dilewati tanpa notifikasi. Jangan set interval jadwal > 2 jam. |
| Workflow 2 tidak mengubah status | Node **Isi image_urls di Sheet** hanya mengisi kolom gambar; `status` tetap `pending`. Ubah manual ke `image_ready` bila ingin melanjutkan ke posting. |
| ImgBB menghapus gambar 24 jam | Wajib: Instagram memproses container lebih cepat dari itu, tetapi preview lama akan mati. Untuk arsip permanen, ganti dengan S3/Cloudinary. |
| Instagram butuh gambar publik | URL ImgBB harus bisa diakses publik. Instagram menolak URL lokal, `localhost`, atau yang butuh login. |
| Batas 10 gambar per carousel | Instagram membatasi 2–10 item. Node **Siapkan Data Post** memotong di 10 dan gagal jika < 2. |
| Caption dipotong 2200 karakter | Batas Instagram. Hashtag dibatasi 30. |
| Watermark fallback | Jika kolom `watermark` kosong, dipakai `@AKUN_UTAMA`. |
| Pollinations gratis = lambat | Batch interval 16 detik per gambar (workflow 5). Untuk 10 slide, siapkan ~3 menit. |
| Persetujuan tanpa batas waktu | Node `sendAndWait` di workflow 4 dan 5 tidak punya `limitWaitTime`. Eksekusi menunggu sampai tombol ditekan. Aktifkan **Options → Limit Wait Time** bila perlu batas. |
| Retry hanya di sebagian node | `retryOnFail` aktif pada node Telegram, ImgBB, dan Gemini. Node `Buat Gambar NVIDIA`, `Buat Container Carousel`, dan `Publish Carousel` **tidak** di-retry — sengaja, agar tidak terjadi double post. |

---

## Dokumentasi Lanjutan

- [01 — Instalasi](docs/01-instalasi.md): langkah demi langkah, dari nol sampai carousel pertama
- [02 — Kredensial](docs/02-kredensial.md): cara membuat tiap credential
- [03 — Google Sheets](docs/03-google-sheets.md): struktur kolom dan header wajib
- [04 — Arsitektur](docs/04-arsitektur.md): alasan di balik setiap node
- [05 — Alur Status](docs/05-alur-status.md): siklus hidup satu baris carousel
- [06 — Troubleshooting](docs/06-troubleshooting.md): error umum dan solusinya
- [07 — FAQ](docs/07-faq.md): pertanyaan yang sering muncul

---

## Lisensi

[MIT](LICENSE) — bebas dipakai, diubah, dan didistribusikan.
