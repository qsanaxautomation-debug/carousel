# Instalasi

Panduan lengkap dari nol sampai carousel pertama terbit. Estimasi **60–90 menit** untuk pertama kali.

---

## Daftar Isi

1. [Prasyarat](#1-prasyarat)
2. [Menyiapkan n8n](#2-menyiapkan-n8n)
3. [Menyiapkan Bot Telegram](#3-menyiapkan-bot-telegram)
4. [Menyiapkan Google Spreadsheet](#4-menyiapkan-google-spreadsheet)
5. [Menyiapkan Google Gemini API](#5-menyiapkan-google-gemini-api)
6. [Menyiapkan ImgBB](#6-menyiapkan-imgbb)
7. [Menyiapkan Penyedia Posting (opsional)](#7-menyiapkan-penyedia-posting-opsional)
8. [Import Workflow](#8-import-workflow)
9. [Mengganti Placeholder](#9-mengganti-placeholder)
10. [Memasang Credential](#10-memasang-credential)
11. [Uji Coba](#11-uji-coba)
12. [Checklist Akhir](#12-checklist-akhir)

---

## 1. Prasyarat

- [ ] Instance n8n yang dapat diakses via HTTPS publik (self-hosted atau Cloud)
- [ ] Akun Telegram
- [ ] Akun Google (Sheets + Gemini API)
- [ ] Akun ImgBB
- [ ] Akun Instagram **Business/Creator** yang terhubung ke salah satu penyedia posting
- [ ] Hak admin pada instance n8n

> **Kenapa HTTPS wajib?** Telegram memanggil webhook n8n, dan OAuth Google melakukan callback. Keduanya menolak `http://` atau `localhost` dari luar.

---

## 2. Menyiapkan n8n

### 2.1 Cek versi

```bash
docker exec -it <nama_container_n8n> n8n --version
```

Perbarui jika node gagal dikenali saat import:

```bash
docker pull n8nio/n8n:latest
docker stop <nama_container_n8n>
docker rm <nama_container_n8n>
docker run -d --name n8n -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

### 2.2 Set timezone

Workflow mencatat waktu dengan `Asia/Jakarta`. Samakan timezone container agar timestamp konsisten:

```bash
docker run -d --name n8n -p 5678:5678 \
  -e GENERIC_TIMEZONE="Asia/Jakarta" \
  -e TZ="Asia/Jakarta" \
  -e WEBHOOK_URL="https://n8n.domain-anda.com/" \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

`WEBHOOK_URL` harus domain publik, bukan `localhost`, agar webhook Telegram bekerja.

### 2.3 HTTPS

Gunakan reverse proxy (Nginx/Caddy/Traefik) atau tunnel. Pastikan `https://domain-anda.com/webhook/...` bisa dibuka dari luar tanpa login.

---

## 3. Menyiapkan Bot Telegram

### 3.1 Buat bot

1. Buka [@BotFather](https://t.me/BotFather) di Telegram
2. Kirim `/newbot`
3. Isi nama dan username bot
4. BotFather membalas token:

```
<TOKEN_DARI_BOTFATHER>
```

Bentuknya deretan angka, tanda titik dua, lalu string acak panjang. Jangan bagikan token ini.

### 3.2 Ambil Chat ID admin

1. Kirim pesan apa pun ke bot Anda
2. Buka:

```
https://api.telegram.org/bot<TOKEN_ANDA>/getUpdates
```

3. Cari `"chat":{"id":123456789` — angka itulah **Chat ID** Anda.

> Untuk grup, Chat ID biasanya negatif (misal `-1001234567890`).

---

## 4. Menyiapkan Google Spreadsheet

### 4.1 Buat spreadsheet

Buat satu spreadsheet bernama bebas (misal **Database Carousel**), lalu buat tab bernama **`Carousel`** (huruf besar C, sisanya kecil — nama tab dicocokkan persis oleh node).

### 4.2 Isi header

Salin baris pertama dari [`examples/carousel-sheet-template.csv`](../examples/carousel-sheet-template.csv), atau ketik manual dengan urutan berikut:

```
id, status, topic, cover_title, cover_subtitle, tags,
slide_01_title, slide_01_body, slide_01_highlight,
...
slide_10_title, slide_10_body, slide_10_highlight,
caption, scheduled_at, instagram_post_id, published_at, image_urls, watermark
```

Rincian tiap kolom ada di [03 — Google Sheets](03-google-sheets.md).

### 4.3 Salin Spreadsheet ID

Dari URL:

```
https://docs.google.com/spreadsheets/d/ ID_SPREADSHEET_ANDA /edit
                                      └────── GANTI INI ──────┘
```

---

## 5. Menyiapkan Google Gemini API

1. Buka [Google AI Studio](https://aistudio.google.com/apikey)
2. **Create API key**
3. Salin key

Model default di workflow: `models/gemini-3.1-flash-lite`. Anda bisa menggantinya di node **Google Gemini Chat Model** (misal ke model yang lebih kuat untuk kualitas naskah lebih baik).

---

## 6. Menyiapkan ImgBB

1. Daftar di [api.imgbb.com](https://api.imgbb.com)
2. Salin **API key**

Dipakai di node **Unggah ke ImgBB** dengan query parameter `key=<API_KEY>`.

> Gambar di ImgBB otomatis dihapus setelah 24 jam pada paket gratis. Itu cukup untuk proses posting, tetapi preview lama akan mati.

---

## 7. Menyiapkan Penyedia Posting (opsional)

Anda hanya butuh **salah satu**, tergantung workflow yang dipakai.

### 7.1 Composio (workflow 4)

1. Daftar di [composio.dev](https://composio.dev)
2. Hubungkan akun Instagram di dashboard
3. Catat **Connected Account ID** dan **Instagram User ID**
4. Buat API key

Composio dipanggil lewat JSON-RPC ke `https://connect.composio.dev/mcp` dengan tool `INSTAGRAM_CREATE_CAROUSEL_CONTAINER` lalu `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`.

### 7.2 Zernio (workflow 5)

1. Daftar di [zernio.com](https://zernio.com)
2. Connect akun Instagram
3. Salin API key (`Bearer sk_...`)

Workflow 5 mengambil Account ID otomatis dari `GET https://zernio.com/api/v1/accounts?platform=instagram`.

> Karena Account ID diambil otomatis, workflow 5 **tidak** punya placeholder untuk itu — cukup API key.

---

## 8. Import Workflow

Untuk setiap file di folder `workflows/`:

1. Buka n8n → **Workflows** → **Add workflow** → menu **⋯** → **Import from File**
2. Pilih file JSON
3. Simpan (**Ctrl/Cmd + S**)

Urutan yang disarankan:

| Urutan | File | Alasan |
|---|---|---|
| 1 | `03-simpan-ke-google-sheet.json` | Target webhook untuk workflow 5; harus aktif lebih dulu |
| 2 | `01-ai-carousel-telegram-bot.json` | Paling sederhana, untuk uji coba cepat |
| 3 | `02-generate-gambar-nvidia.json` | Uji pembuatan gambar manual |
| 4 | `04-antrean-otomatis-composio.json` | Produksi terjadwal |
| 5 | `05-ai-carousel-lengkap-zernio.json` | Alternatif produksi via Telegram |

> **Jangan aktifkan dulu.** Aktifkan setelah credential dan placeholder selesai, karena workflow aktif yang salah konfigurasi bisa membanjiri Telegram dengan error.

---

## 9. Mengganti Placeholder

Semua data sensitif sudah dihapus dari repo. Cari dan ganti placeholder berikut.

| Placeholder | Ganti dengan | Muncul di |
|---|---|---|
| `REPLACE_WITH_CAROUSEL_SHEET_ID` | ID spreadsheet database carousel | WF 1, 2, 4 |
| `REPLACE_WITH_ARCHIVE_SHEET_ID` | ID spreadsheet arsip | WF 3 |
| `REPLACE_WITH_TELEGRAM_ADMIN_CHAT_ID` | Chat ID admin | WF 4 |
| `REPLACE_WITH_IMGBB_API_KEY` | API key ImgBB | WF 5 |
| `REPLACE_WITH_ZERNIO_API_KEY` | API key Zernio | WF 5 |
| `REPLACE_WITH_COMPOSIO_ACCOUNT_ID` | Connected Account ID Composio | WF 4 |
| `REPLACE_WITH_IG_USER_ID` | Instagram Business User ID | WF 1, 4 |
| `REPLACE_WITH_IG_USERNAME` | Username akun utama | WF 4 |
| `REPLACE_WITH_IG_USERNAME_2` | Username akun kedua | WF 4 |
| `YOUR-N8N-HOST` | Domain publik n8n | WF 5 |
| `@AKUN_UTAMA` / `@AKUN_KEDUA` | Username di label tombol Telegram dan fallback watermark | WF 4 |

> Tiga nilai terakhir bukan variabel — `@AKUN_UTAMA` dan `@AKUN_KEDUA` tertulis di label tombol node `Minta Persetujuan Posting` dan `Minta Akun Ebooks`. Ganti dengan username Anda agar tombol menampilkan akun yang benar. Watermark punya fallback yang sama di node `Tulis Teks Slide`.

### Cara 1 — Edit di n8n (disarankan)

Buka tiap node yang mengandung placeholder, ganti nilainya, simpan.

### Cara 2 — Find & replace di file JSON

Sebelum import:

```bash
cd workflows
sed -i 's/REPLACE_WITH_CAROUSEL_SHEET_ID/ID_ASLI_ANDA/g' *.json
```

Ulangi untuk setiap placeholder. **Jangan commit file hasil edit** — `.gitignore` sudah mengecualikan `workflows/*-local.json`.

---

## 10. Memasang Credential

Semua blok `credentials` sengaja dihapus dari workflow. Setiap node yang butuh koneksi akan menampilkan peringatan merah sampai Anda memilih credential.

Ringkasnya:

| Node | Jenis credential |
|---|---|
| Telegram Trigger, semua node Telegram | Telegram API |
| Google Gemini Chat Model | Google Gemini (PaLM) API |
| Google Sheets (semua) | Google Sheets OAuth2 |
| Upload ke ImgBB | Generic (query param `key`) atau Custom Auth |
| Buat Gambar NVIDIA | Bearer Auth |
| POST ke Instagram via Zernio | Header Auth (`Authorization: Bearer ...`) |
| Buat/Publish Container Carousel | Custom Auth (Composio API key) |

Langkah detail per credential: [02 — Kredensial](02-kredensial.md).

---

## 11. Uji Coba

### 11.1 Uji workflow paling sederhana dulu

1. Buka workflow `01-ai-carousel-telegram-bot.json`
2. Aktifkan (**Active** toggle)
3. Kirim ke bot:

```
topik: 5 cara menjaga fokus saat kerja remote | slide: 5 | tone: santai | niche: produktivitas
```

4. Tunggu ~10–30 detik. Bot harus membalas dua pesan: ringkasan dan detail slide.
5. Cek tab `Carousel` di spreadsheet — harus ada satu baris baru dengan `status = pending`.

Jika berhasil, fondasi (Telegram + Gemini + Sheets) sudah benar.

### 11.2 Uji pembuatan gambar

1. Buka workflow `02-generate-gambar-nvidia.json`
2. Klik **Execute Workflow**
3. Tunggu. Node **Ambil Baris Pending** mengambil baris `pending` hasil langkah 11.1.
4. Setelah selesai, kolom `image_urls` harus terisi dan gambar bisa dibuka di browser.

### 11.3 Uji alur penuh

1. Buka workflow `05-ai-carousel-lengkap-zernio.json` (tanpa Sheets) **atau** `04-antrean-otomatis-composio.json` (terjadwal)
2. Aktifkan
3. Ikuti tombol persetujuan yang muncul di Telegram

---

## 12. Checklist Akhir

- [ ] n8n dapat diakses via HTTPS publik, `WEBHOOK_URL` sudah benar
- [ ] Timezone container `Asia/Jakarta`
- [ ] Bot Telegram dibuat, token tersimpan, Chat ID admin diketahui
- [ ] Tab `Carousel` ada dengan header lengkap (termasuk kolom `watermark`)
- [ ] Spreadsheet ID sudah diganti di semua node Sheets
- [ ] Gemini API key aktif
- [ ] ImgBB API key terpasang
- [ ] Semua placeholder `REPLACE_WITH_*` sudah hilang (`grep -r REPLACE_WITH workflows/`)
- [ ] Semua node yang butuh credential sudah hijau (tidak ada ikon merah)
- [ ] Uji workflow 1 berhasil: bot membalas dan baris masuk Sheets
- [ ] Uji workflow 2 berhasil: `image_urls` terisi
- [ ] Uji alur penuh: carousel berhasil terbit di Instagram
- [ ] `bash scripts/check-secrets.sh` lulus sebelum commit/push
