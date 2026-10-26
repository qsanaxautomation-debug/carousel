# Troubleshooting

Error yang paling sering muncul, penyebabnya, dan cara memperbaikinya.

---

## Daftar Isi

1. [Import & Node Merah](#1-import--node-merah)
2. [Telegram](#2-telegram)
3. [Google Sheets](#3-google-sheets)
4. [Gemini](#4-gemini)
5. [Pembuatan Gambar](#5-pembuatan-gambar)
6. [ImgBB](#6-imgbb)
7. [Posting Instagram](#7-posting-instagram)
8. [Antrean Tidak Jalan](#8-antrean-tidak-jalan)
9. [Cara Debug Umum](#9-cara-debug-umum)

---

## 1. Import & Node Merah

### "Unrecognized node type: n8n-nodes-base.editImage"

| | |
|---|---|
| **Sebab** | Versi n8n terlalu lama; node `editImage` belum ada |
| **Solusi** | Perbarui n8n ke versi terbaru, lalu import ulang |

```bash
docker pull n8nio/n8n:latest
docker stop n8n && docker rm n8n
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
```

Node `editImage` baru tersedia pada rilis n8n yang lebih baru. Kalau Anda tidak bisa memperbarui, pakai workflow 5 (Pollinations) yang tidak memakai node tersebut.

### Semua node koneksi berwarna merah

| | |
|---|---|
| **Sebab** | Blok `credentials` sengaja dihapus saat sanitasi |
| **Solusi** | Buat credential lalu pilih di tiap node — lihat [02 — Kredensial](02-kredensial.md) |

Ini **normal**, bukan kerusakan. Buka node, pilih credential di bagian **Credential to connect with**.

### "Cannot find workflow with id ..."

| | |
|---|---|
| **Sebab** | JSON berisi referensi `workflowId` dari instance asal |
| **Solusi** | Import ulang; node seperti `Execute Workflow` perlu diarahkan ke workflow lokal |

---

## 2. Telegram

### Bot tidak merespons sama sekali

Cek berurutan:

1. **Workflow aktif?** Toggle di kanan atas harus hijau
2. **Webhook terdaftar?** Buka `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
   - `"url"` harus menunjuk domain n8n Anda
   - `"last_error_message"` memberi petunjuk
3. **HTTPS publik?** `WEBHOOK_URL` harus domain nyata, bukan `localhost`
4. **Firewall?** Pastikan port 443 terbuka dari internet

Hapus webhook lama yang menempel:

```bash
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook?drop_pending_updates=true"
```

Lalu matikan-nyalakan workflow agar n8n mendaftarkan ulang.

### "Bad Request: chat not found"

| | |
|---|---|
| **Sebab** | Bot belum pernah di-`/start` oleh penerima, atau Chat ID salah |
| **Solusi** | Kirim `/start` ke bot dari akun penerima, lalu ambil ulang Chat ID dari `getUpdates` |

Untuk grup: masukkan bot ke grup dulu, kirim satu pesan, baru baca Chat ID (bernilai negatif).

### Tombol persetujuan tidak muncul

| | |
|---|---|
| **Sebab** | `sendAndWait` butuh `approverIds` berisi Chat ID yang valid, dan bot harus bisa mengirim pesan ke chat itu |
| **Solusi** | Isi `chat_id` di node `Pengaturan` dengan Chat ID admin; pastikan admin sudah `/start` bot |

### "message is too long"

Caption Telegram dibatasi 1024 karakter untuk media, 4096 untuk teks. Node `Format Detail Slides` menggabungkan semua slide sehingga bisa melewati batas pada carousel 10 slide dengan teks panjang.

Solusi: potong di node Code, atau kirim per 5 slide.

---

## 3. Google Sheets

### "Sheet not found" / "Unable to parse range"

| | |
|---|---|
| **Sebab** | Nama tab bukan `Carousel` (atau `Sheet1` untuk arsip) |
| **Solusi** | Rename tab persis sesuai huruf besar-kecil |

Cek cepat: nama tab di URL Spreadsheet adalah bagian setelah `/d/<id>/edit#gid=0`, bukan nama. Klik kanan tab → **Rename**.

### Kolom tidak terisi / "Column not found"

| | |
|---|---|
| **Sebab** | Nama header beda (huruf besar, spasi, atau typo) |
| **Solusi** | Bandingkan dengan [03 — Google Sheets § 2](03-google-sheets.md). Semua header huruf kecil + garis bawah |

Node Google Sheets memetakan berdasarkan **nama header**, bukan posisi kolom. Jadi `Slide_01_Title` tidak akan cocok dengan `slide_01_title`.

### Update tidak mengubah baris mana pun

| | |
|---|---|
| **Sebab** | Kolom `id` dianggap tanggal oleh Sheets, sehingga nilai `CRS-20261026-104512` berubah |
| **Solusi** | Format kolom `id` sebagai **Plain text**, lalu isi ulang nilainya |

Tanda-tandanya: sel menampilkan sesuatu seperti `####` atau tanggal, bukan teks `CRS-...`.

### "The caller does not have permission"

| | |
|---|---|
| **Sebab** | Spreadsheet tidak dibagikan ke akun yang dipakai OAuth |
| **Solusi** | Bagikan spreadsheet ke alamat Gmail akun OAuth tersebut sebagai **Editor** |

### Data tidak masuk ke spreadsheet arsip

| | |
|---|---|
| **Sebab** | Workflow 3 tidak aktif, atau `YOUR-N8N-HOST` belum diganti |
| **Solusi** | Aktifkan workflow 3, ganti URL di node `Simpan Carousel ke Sheet` jadi domain n8n Anda |

Cek manual:

```bash
curl -X POST https://n8n.domain-anda.com/webhook/simpan-carousel \
  -H "Content-Type: application/json" \
  -d '{"topik":"tes","judul":"Tes","status":"draft"}'
```

Harus membalas `200` dengan body yang menandakan workflow jalan.

---

## 4. Gemini

### "API key not valid"

| | |
|---|---|
| **Sebab** | Key salah, atau API belum diaktifkan untuk project |
| **Solusi** | Buat key baru di [AI Studio](https://aistudio.google.com/apikey) |

### "Model not found" / "models/gemini-3.1-flash-lite is not supported"

| | |
|---|---|
| **Sebab** | Nama model tidak tersedia di region/akun Anda |
| **Solusi** | Ganti **Model Name** di node `Google Gemini Chat Model` ke model yang tersedia di akun Anda |

Daftar model yang bisa dipakai akun Anda:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models?key=<API_KEY>"
```

### "Failed to parse structured output"

| | |
|---|---|
| **Sebab** | Model membalas teks di luar skema, biasanya karena prompt terlalu rumit |
| **Solusi** | Sederhanakan `raw_text`, atau ganti ke model yang lebih besar |

Coba satu kali manual di AI Studio dengan prompt yang sama untuk memastikan modelnya sanggup.

### Naskah terjemahan aneh / campur bahasa

Tambahkan penegasan di node `AI Agent Pembuat Carousel`:

```text
WAJIB seluruh output dalam Bahasa Indonesia. Jangan menerjemahkan nama merek.
```

---

## 5. Pembuatan Gambar

### NVIDIA: "401 Unauthorized"

| | |
|---|---|
| **Sebab** | Bearer token salah atau kedaluwarsa |
| **Solusi** | Buat ulang key di [build.nvidia.com](https://build.nvidia.com), perbarui credential Bearer Auth |

### NVIDIA: "404" atau "model not found"

Endpoint `flux.1-schnell` bisa berubah. Periksa halaman model di build.nvidia.com dan sesuaikan URL node `Buat Gambar NVIDIA`.

### NVIDIA: "Respons NVIDIA tidak berisi gambar"

Node `Ubah Base64 ke Gambar` melempar error ini kalau tidak menemukan field gambar. Cek output mentah node `Buat Gambar NVIDIA`:

- Kalau ada `artifacts[0].base64` → normal
- Kalau ada field lain (misal `data[0].b64_json`) → sudah ditangani fallback; kalau tetap gagal, kirim isi respons untuk disesuaikan

Penyebab umum: request kena rate limit sehingga respons berisi pesan error, bukan gambar.

### Gambar tidak muncul di Telegram

`Kirim Foto ke Telegram` mengirim binary. Kalau ImgBB gagal, node sebelumnya tidak menghasilkan binary. Cek node `Upload ke ImgBB` dulu.

### Teks di gambar salah eja

Itu batasan model difusi (workflow 2 dan 5). Solusinya pindah ke workflow 4, yang merender teks dengan node `editImage` sehingga ejaan dijamin benar.

### `editImage`: "No binary data found"

| | |
|---|---|
| **Sebab** | Node `Buat Latar` (operation `create`) tidak meneruskan binary, atau urutan node terputus |
| **Solusi** | Pastikan `Buat Latar` terhubung **sebelum** `Tulis Teks Slide`, dan `Tulis Teks Slide` memakai operation `multiStep` |

### Tulisan terpotong di tepi kanvas

`lineLength` mengatur pembungkusan baris dalam **karakter**, bukan piksel. Untuk judul panjang:

| Field | Nilai sekarang | Saran untuk judul panjang |
|---|---|---|
| Judul `lineLength` | 18 | 14 |
| Judul `fontSize` | 84 | 64 |
| Isi `lineLength` | 28 | 24 |
| Isi `fontSize` | 52 | 44 |

### Watermark menampilkan `@AKUN_UTAMA`

Kolom `watermark` kosong. Isi kolom itu di Sheets, atau ganti fallback di node `Tulis Teks Slide`:

```js
{{ $('Pengaturan').first().json.watermark || '@akun_anda' }}
```

---

## 6. ImgBB

### "Invalid API key"

Key dikirim sebagai **query parameter** `key`, bukan header. Kalau memakai Custom Auth, pastikan JSON-nya:

```json
{ "headers": {}, "qs": { "key": "API_KEY_ANDA" } }
```

### "Image upload failed" / 400

Pastikan:

- Body memakai `multipart/form-data`, bukan JSON
- Field bernama `image`
- `inputDataFieldName` cocok dengan nama binary dari node sebelumnya (`data`)

### URL gambar 404 setelah beberapa jam

Normal pada paket gratis — ImgBB menghapus gambar setelah 24 jam. Untuk arsip permanen, unggah juga ke Google Drive atau S3.

---

## 7. Posting Instagram

### "Carousel Instagram butuh minimal 2 gambar"

Node `Siapkan Data Post` memvalidasi `urls.length >= 2`. Penyebab:

- Node `Susun Daftar URL` gagal mengumpulkan (`uploads` kosong)
- Semua unggahan ImgBB ditolak

Cek node `Kumpulkan Hasil Unggahan` — kalau `uploads` kosong, akar masalahnya di ImgBB, bukan di Instagram.

### Container dibuat tapi `creation_id` kosong

Node `Cek Container` membedah respons SSE. Kalau Composio mengubah format, parsing gagal. Periksa output mentah node `Buat Container Carousel` dan cari `creation_id` di dalam baris yang dimulai `data: `.

### "Media processing failed" saat publish

Instagram butuh waktu memproses container. Workflow sudah mengirim `max_wait_seconds: 120`. Kalau tetap gagal:

- Gambar mungkin belum bisa diakses publik (cek URL di browser mode incognito)
- Rasio bukan 1:1 — workflow 4 selalu 1080×1080, workflow 2/5 mengandalkan provider
- Jumlah gambar > 10 (dipotong otomatis oleh `Siapkan Data Post`)

### Caption terpotong di tengah hashtag

Caption dipotong `slice(0, 2200)` setelah filter 30 hashtag. Kalau kalimat terakhir terpotong, perpendek caption di prompt AI (kurangi dari "10-15 hashtag" menjadi "8-10").

### "Tidak ada akun Instagram yang terhubung di Zernio"

Buka dashboard Zernio dan hubungkan akun Instagram Business/Creator. Akun personal tidak bisa dipakai API.

### Posting berhasil tapi `instagram_post_id` kosong

Node `Baca Hasil Publish` tidak menemukan ID di respons. Statusnya tetap `posted` (karena publish sukses), hanya ID-nya hilang. Cek respons mentah untuk menyesuaikan parsing.

---

## 8. Antrean Tidak Jalan

### Baris `pending` tidak pernah diproses

Cek berurutan:

1. **Workflow 4 aktif?** Schedule trigger hanya jalan saat aktif
2. **Umur baris > 120 menit?** `Pilih Baris Terbaru` melewatinya — ubah `id` jadi timestamp baru (lihat [05](05-alur-status.md))
3. **Format `id` salah?** Harus persis `CRS-yyyyMMdd-HHmmss` (14 digit + tanda hubung)
4. **Lebih dari satu baris `pending`?** Hanya yang termuda diproses; sisanya menunggu siklus berikutnya

### Baris nyangkut di `generating`

Workflow mati di tengah proses. Error Trigger hanya berjalan kalau workflow masih aktif. Perbaiki manual:

1. Set `status` = `failed` untuk membersihkan
2. Set `status` = `pending` + perbarui `id` untuk mengulang

### "Baris ... punya kurang dari 2 slide"

Node `Susun Prompt Per Slide` melempar error ini kalau `cover_title` kosong **dan** semua `slide_NN` kosong. Berarti baris dibuat tanpa data — periksa apakah workflow 1 berhasil menyimpan, atau hapus baris tersebut.

### Telegram dibanjiri notifikasi error tiap 5 menit

Satu baris rusak diproses berulang. Segera set `status` = `failed` pada baris itu. Kalau tidak tahu baris mana, lihat `id` di pesan error.

---

## 9. Cara Debug Umum

### Lihat data di antara node

Di editor n8n, klik node → tab **Output** → **JSON**. Kalau node belum jalan, klik **Execute step** (atau **Test step**).

### Jalankan satu node saja

Klik kanan node → **Execute step**. Node sebelumnya harus punya data; kalau tidak, jalankan dari awal lewat **Execute Workflow**.

### Cek log container

```bash
docker logs --tail 200 -f n8n
```

Atau `docker logs n8n 2>&1 | grep -i error`.

### Uji endpoint tanpa n8n

```bash
# ImgBB
curl -F "image=@slide.jpg" "https://api.imgbb.com/1/upload?key=<API_KEY>"

# Model Gemini yang tersedia
curl "https://generativelanguage.googleapis.com/v1beta/models?key=<API_KEY>"

# Webhook arsip
curl -X POST https://n8n.domain-anda.com/webhook/simpan-carousel \
  -H "Content-Type: application/json" -d '{"topik":"tes"}'
```

### Minta bantuan

Saat melaporkan masalah, sertakan:

- Versi n8n (`n8n --version`)
- Nama workflow dan node yang gagal
- **Pesan error lengkap** (bukan hanya "tidak jalan")
- Output JSON node **sebelum** node yang gagal
- Sudah/belum mengganti semua placeholder (`grep -rn REPLACE_WITH_ workflows/`)

Jangan sertakan token, API key, atau isi spreadsheet asli.
