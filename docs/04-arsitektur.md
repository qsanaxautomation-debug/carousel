# Arsitektur

Penjelasan alasan di balik setiap keputusan desain. Berguna kalau Anda ingin memodifikasi workflow, bukan sekadar memakainya.

---

## Daftar Isi

1. [Peta Workflow](#1-peta-workflow)
2. [Workflow 1 — Telegram → Naskah](#2-workflow-1--telegram--naskah)
3. [Workflow 2 — Naskah → Gambar (NVIDIA)](#3-workflow-2--naskah--gambar-nvidia)
4. [Workflow 3 — Webhook Arsip](#4-workflow-3--webhook-arsip)
5. [Workflow 4 — Antrean Produksi (Composio)](#5-workflow-4--antrean-produksi-composio)
6. [Workflow 5 — Alur Penuh (Zernio)](#6-workflow-5--alur-penuh-zernio)
7. [Keputusan Desain](#7-keputusan-desain)

---

## 1. Peta Workflow

| # | Nama | Trigger | Sumber gambar | Posting | State |
|---|---|---|---|---|---|
| 1 | AI Carousel Instagram - Telegram Bot | Telegram | — | — | Sheets `pending` |
| 2 | Generate Gambar Carousel Pending | Manual | NVIDIA FLUX.1-schnell | — | Sheets `image_urls` |
| 3 | Simpan Carousel ke Google Sheet | Webhook | — | — | Sheet arsip |
| 4 | Antrean Carousel Otomatis | Schedule 5 menit | n8n `editImage` (kanvas lokal) | Composio | Sheets, 8 status |
| 5 | AI Carousel + Gambar + Post | Telegram | Pollinations (GET) | Zernio | Stateless |

Ketiganya **berdiri sendiri**. Anda tidak harus memakai semuanya. Kombinasi yang masuk akal:

- **Uji cepat:** hanya 1
- **Kontrol manual:** 1 → 2 → posting manual
- **Produksi berstatus:** 1 → 4
- **Produksi tanpa Sheets:** 5
- **Arsip semua hasil:** 5 → 3

---

## 2. Workflow 1 — Telegram → Naskah

```
Telegram Bot Trigger
  └─> Kirim Pesan Proses          (balas "sedang diproses")
  └─> Parse Input Telegram        (chat_id, user_name, raw_text)
  └─> AI Agent Pembuat Carousel   (Gemini + prompt terstruktur)
        ├─ Google Gemini Chat Model
        └─ Parser Carousel JSON   (output parser terstruktur)
  └─> Format Pesan Telegram ──> Kirim Hasil Carousel
  └─> Format Detail Slides  ──> Kirim Detail Slides
  └─> Siapkan Baris Sheet         (Code: 42 kolom)
        ├─> Simpan ke Sheet Carousel ──> Konfirmasi Tersimpan ke Sheet
        └─> (error) ──> Notif Gagal Simpan Sheet
```

### Kenapa output parser, bukan JSON.parse

Node `Parser Carousel JSON` memakai **Structured Output Parser** dengan `jsonSchemaExample`. Gemini dipaksa mengikuti bentuk JSON yang sama, sehingga tidak perlu regex atau `JSON.parse` yang rapuh terhadap pagar ```` ```json ```` atau teks pembuka.

### Kenapa ID berbentuk `CRS-yyyyMMdd-HHmmss`

Tiga alasan:

1. **Unik** tanpa perlu database.
2. **Sortable** — carousel terbaru selalu menang saat diurutkan.
3. **Menyimpan waktu** — node `Pilih Baris Terbaru` bisa menghitung umur baris tanpa kolom tambahan.

Formatnya dibangkitkan dengan `$now.setZone('Asia/Jakarta').toFormat(...)`, jadi jam di ID adalah WIB, bukan UTC.

### Kenapa slide dibatasi 9 + 1 closing

Template Sheets punya slot `slide_01` … `slide_10`. Node Code memotong `slides.slice(0, 9)`, lalu mendorong `closing_slide` ke slot ke-10. Jadi:

- AI boleh membalas 7 slide (default di prompt)
- Slot 8–9 kosong
- Slot 10 = closing

Tanpa pemotongan ini, AI yang membalas 12 slide akan menimpa isi kolom secara acak.

### Kenapa `tags` diambil dari caption

Caption sudah berisi hashtag hasil generate AI. Mengambil 4 hashtag pertama dari caption lebih konsisten daripada meminta AI mengisi field `tags` terpisah — satu sumber kebenaran, tidak mungkin bertentangan.

---

## 3. Workflow 2 — Naskah → Gambar (NVIDIA)

```
Mulai Manual
 └─> Ambil Baris Pending           (Sheets: semua baris)
 └─> Hanya Yang Belum Ada Gambar   (filter image_urls kosong)
 └─> Batasi 1 Baris                (limit 1)
 └─> Susun Prompt Per Slide        (Code: cover + 10 slide → N item)
 └─> Buat Gambar NVIDIA            (POST flux.1-schnell)
 └─> Ubah Base64 ke Gambar         (Code: base64 → binary)
 └─> Unggah ke ImgBB               (multipart, querystring key)
 └─> Kumpulkan Semua Hasil Unggahan (aggregate)
 └─> Susun Daftar URL              (Code: gabung + validasi)
 └─> Isi image_urls di Sheet       (update by id)
```

### Kenapa NVIDIA FLUX.1-schnell

- **Cepat** — 4 langkah sampling, bukan 20–50
- **Murah/gratis** lewat kredit NVIDIA Build
- **Menerima teks dalam prompt** — bisa menulis judul slide langsung di gambar

Batasnya: teks panjang sering salah eja. Karena itu workflow 4 lebih memilih merender teks sendiri (lihat bagian 5).

### Kenapa `seed: 0` dan `steps: 4`

FLUX.1-schnell dioptimalkan untuk 4 langkah; menaikkan `steps` tidak memperbaiki kualitas secara berarti tetapi memperlambat. `seed: 0` membuat variasi antar generate tetap terjadi — kalau Anda ingin hasil reprodusibel, ganti ke angka tetap.

### Kenapa `Ubah Base64 ke Gambar` ada di antara

Respons NVIDIA mengembalikan `artifacts[0].base64`, bukan binary. Node HTTP Request berikutnya (ImgBB) butuh binary. Node Code ini menjembatani dengan `this.helpers.prepareBinaryData(...)`.

Kalau bentuk respons berbeda (misal `data[0].b64_json`), node ini sudah punya tiga fallback:

```js
(j.artifacts && j.artifacts[0] && j.artifacts[0].base64) || j.image || (j.data && j.data[0] && j.data[0].b64_json)
```

### Kenapa ImgBB

Instagram Graph API hanya menerima **URL publik**, tidak bisa menerima upload langsung. ImgBB memberi URL tanpa perlu storage sendiri. Paket gratis menghapus gambar setelah 24 jam — cukup untuk satu siklus posting, tidak cukup untuk arsip (gunakan Drive/S3 kalau butuh permanen).

---

## 4. Workflow 3 — Webhook Arsip

```
Terima Data Carousel   (POST /webhook/simpan-carousel, responseMode: onReceived)
 └─> Rapikan Data Carousel  (Set: tanggal WIB + field tetap)
 └─> Simpan ke Google Sheet
```

### Kenapa webhook, bukan Google Sheets node langsung

Workflow 5 tidak punya credential Google. Memanggil webhook membuat workflow 5 tetap ringan: satu node HTTP tanpa OAuth. Konsekuensinya workflow 3 **harus aktif** dan URL-nya benar.

`responseMode: onReceived` dipilih agar pemanggil tidak menunggu penulisan Sheets selesai — respons langsung `200` begitu data diterima. Cocok karena workflow 5 tidak butuh hasilnya.

### Kenapa `tanggal` dibuat di sini

`$now.setZone('Asia/Jakarta')` dijalankan di sisi penerima, jadi format waktunya konsisten walaupun pemanggil mengirim dari timezone berbeda.

---

## 5. Workflow 4 — Antrean Produksi (Composio)

Ini workflow paling kompleks: **45 node**, 8 status, 3 jalur kegagalan.

```
Setiap 5 Menit
 └─> Ambil Baris Pending
 └─> Pengaturan (chat_id, connected_account_id, ig_user_id, ig_username)
 └─> Pilih Baris Terbaru          (Code: saring umur 0–120 menit)
 └─> Tandai Generating
 └─> Susun Prompt Per Slide       (Code: buang emoji, tandai cover/isi)
 └─> Buat Latar                   (editImage create 1080×1080)
 └─> Tulis Teks Slide             (editImage multiStep: nomor, judul, isi, watermark)
 └─> Unggah ke ImgBB              (multipart)
 └─> Kumpulkan Hasil Unggahan ──> Susun Daftar URL
 └─> Simpan Gambar dan Status image_ready
 └─> Siapkan Preview ──> Kirim Preview Foto (tiap gambar)
 └─> Kumpulkan Preview ──> Minta Persetujuan Posting (sendAndWait)
 └─> Disetujui? ──┬─ tidak ──> Tandai Ditolak ──> Notif Dibatalkan
                  └─ ya
                     └─> Minta Akun Ebooks (sendAndWait)
                          └─> Akun Ebooks (Set: akun kedua)
                          └─> Siapkan Data Post (Code: caption ≤2200, ≤30 tag, ≤10 URL)
                          └─> Buat Container Carousel (JSON-RPC)
                          └─> Cek Container (Code: bedah SSE)
                          └─> Container OK? ── tidak ──> Notif/Tandai Gagal Container
                               └─ ya
                                  └─> Publish Carousel (JSON-RPC)
                                  └─> Baca Hasil Publish
                                  └─> Publish Berhasil? ── tidak ──> Notif/Tandai Gagal Publish
                                       └─ ya ──> Tandai Posted ──> Notif Sukses

Saat Antrean Gagal (Error Trigger)
 └─> Notif Error Antrean ──> Ambil Baris Generating ──> Tandai Gagal (Error)
```

### Kenapa gambar dibuat lokal, bukan dengan AI

Node `editImage` menggambar kanvas 1080×1080 dengan warna blok dan teks vektor. Keuntungannya:

- **Teks selalu benar** — tidak ada salah eja seperti model difusi
- **Gratis dan instan** — tidak ada API call
- **Konsisten** — semua carousel punya identitas visual sama

Kekurangannya: tidak ada ilustrasi. Ini pilihan sadar dengan trade-off "selalu rapi" di atas "kadang indah, kadang salah tulis".

### Kenapa `Pilih Baris Terbaru` memakai jendela 0–120 menit

Tanpa batas umur, satu baris `pending` lama akan diproses berulang tiap 5 menit selamanya — membanjiri Telegram. Jendela 120 menit memastikan hanya konten segar yang diproses; baris lebih tua harus di-`pending`-kan ulang (lihat [05 — Alur Status](05-alur-status.md)).

Toleransi `-10` menit mengakomodasi selisih jam antara server n8n dan waktu pembuatan ID.

### Kenapa emoji dibuang sebelum render

`editImage` merender teks dengan font sistem yang sering tidak punya glyph emoji. Alih-alih kotak kosong, node Code menghapus rentang Unicode emoji:

```js
/[\\u{1F000}-\\u{1FFFF}\\u{2600}-\\u{27BF}\\u{2B00}-\\u{2BFF}\\u{FE0F}\\u{200D}]/gu
```

### Kenapa Composio, bukan Instagram Graph API langsung

Instagram Graph API butuh **App Review** Meta untuk izin `instagram_content_publish`, plus App Secret dan token jangka panjang. Composio menyediakan koneksi OAuth yang sudah disetujui, diakses lewat satu endpoint MCP.

Trade-off: Anda bergantung pada pihak ketiga dan format responsnya (`Server-Sent Events`, bukan JSON biasa). Itulah sebabnya ada dua node Code (`Cek Container`, `Baca Hasil Publish`) yang khusus membedah `data: {...}`.

### Kenapa ada node `Akun Ebooks`

Akun Instagram kedua (untuk produk e-book) dipilih lewat tombol Telegram sebelum posting. Nilainya ditimpa ke `connected_account_id` / `ig_user_id` di node `Siapkan Data Post` dengan `try/catch` — kalau admin tidak memilih, akun utama dari `Pengaturan` yang dipakai.

### Kenapa dua tombol persetujuan

1. **Sebelum generate** — hemat biaya kalau naskah ternyata jelek
2. **Sebelum posting** — gambar sudah terlihat, ini gerbang terakhir

Keduanya `sendAndWait`. **Batas tunggu belum diaktifkan** (`limitWaitTime` = `null` di workflow yang dirilis), jadi satu node yang menunggu akan menggantung eksekusi sampai ada jawaban. Aktifkan **Options → Limit Wait Time** kalau Anda ingin eksekusi berhenti sendiri saat tidak ada respons.

---

## 6. Workflow 5 — Alur Penuh (Zernio)

```
Telegram Bot Trigger
 └─> Parse Input Telegram ──> AI Agent ──> Parser Carousel JSON
 └─> Format Pesan Telegram ──> Kirim Hasil Carousel
 └─> Format Detail Slides ──> Kirim Detail Slides
 └─> Minta Persetujuan Generate Gambar (sendAndWait)
 └─> Disetujui? ──┬─ tidak ──> Kirim Pesan Ditolak
                  └─ ya
                     └─> Kirim Notif Mulai Generate
                     └─> Siapkan Data Slides ──> Split Tiap Slide
                     └─> Generate Gambar Pollinations (GET, tanpa auth)
                     └─> Upload ke ImgBB (query key)
                     └─> Kirim Foto ke Telegram
                     └─> Kumpulkan Semua URL Gambar ──> Kirim Pesan Selesai
                     └─> Tanya Post ke Instagram? (sendAndWait)
                     └─> Mau Post Instagram? ──┬─ tidak ──> Kirim Pesan Skip
                                               └─ ya
                          └─> Ambil Akun Instagram Zernio (GET accounts)
                          └─> Siapkan Payload Zernio (Code)
                          └─> POST ke Instagram via Zernio
                          └─> Kirim Notif Sukses Instagram
                          └─> Siapkan Data Sheet ──> Simpan Carousel ke Sheet (webhook)
```

### Kenapa Pollinations di sini, bukan NVIDIA

Pollinations bisa dipanggil dengan **GET biasa tanpa API key**, jadi workflow 5 bisa dicoba tanpa mendaftar apa pun. Cocok untuk demo dan pemakaian pribadi.

Kelemahannya: layanan publik, bisa lambat atau membatasi permintaan, dan URL-nya panjang. Untuk produksi yang andal, ganti node ini dengan `Buat Gambar NVIDIA` dari workflow 2 (tambah credential Bearer, ubah method ke POST).

### Kenapa `Ambil Akun Instagram Zernio` dipanggil dulu

Zernio membutuhkan `accountId` internal mereka (`accounts[0]._id`), bukan username. Mengambilnya saat runtime berarti Anda tidak perlu menyimpan ID yang bisa berubah saat akun di-reconnect.

### Kenapa gambar diunggah ulang ke ImgBB

Pollinations mengembalikan URL gambar, tapi URL itu bisa kedaluwarsa dan tidak selalu bisa diakses Instagram. Mengunggah ulang ke ImgBB memberi URL stabil 24 jam yang diterima Graph API.

---

## 7. Keputusan Desain

### Kenapa banyak node Code, bukan ekspresi

Logika seperti pemotongan caption 2200 karakter, pembatasan 30 hashtag, penyaringan umur baris, dan pembedahan SSE terlalu panjang untuk satu ekspresi `{{ }}`. Node Code lebih mudah dibaca, diberi komentar, dan diuji ulang.

### Kenapa tidak memakai Queue mode n8n

Antrean sudah dikelola oleh kolom `status` di Sheets. Menambah Redis + worker hanya masuk akal kalau volume lebih dari puluhan carousel per jam.

### Kenapa tidak ada retry otomatis

Retry otomatis pada posting Instagram berisiko **double post** — container yang timeout bisa saja sudah terbit. Lebih aman menandai `failed`, memberi tahu admin, dan membiarkan manusia memutuskan.

### Kenapa credential dihapus dari JSON

Blok `credentials` menyimpan **ID credential di server**, bukan nilainya. Tetap saja, membagikan ID itu membocorkan struktur infrastruktur dan membuat workflow tidak bisa diimpor bersih di instance lain. Semua blok dihapus; pengguna memilih credential sendiri.

### Kenapa placeholder bukan nilai contoh yang "kelihatan asli"

Nilai seperti `YOUR-API-KEY` mudah tertinggal tanpa disadari. Placeholder `REPLACE_WITH_*` bisa dideteksi otomatis:

```bash
grep -rn "REPLACE_WITH_" workflows/
```

Kalau perintah itu masih mengeluarkan hasil, konfigurasi belum lengkap.
