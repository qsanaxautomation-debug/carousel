# FAQ

---

## Umum

### Apa yang perlu saya siapkan untuk mulai?

Minimum untuk mencoba: n8n, bot Telegram, API key Gemini. Sampai di situ Anda sudah bisa membuat naskah carousel (workflow 1). Untuk gambar dan posting, tambah ImgBB dan salah satu penyedia posting.

### Berapa biayanya?

| Komponen | Biaya |
|---|---|
| n8n | Gratis (self-hosted) atau sesuai paket Cloud |
| Telegram Bot | Gratis |
| Google Sheets | Gratis |
| Gemini API | Ada kuota gratis; pemakaian berat berbayar |
| ImgBB | Gratis (gambar dihapus 24 jam) |
| NVIDIA Build | Ada kredit gratis |
| Pollinations | Gratis, tanpa key |
| Composio / Zernio | Tergantung paket layanan |

Satu carousel 10 slide biasanya menghabiskan 1 panggilan Gemini, 11 panggilan gambar, dan 11 unggahan ImgBB.

### Apakah harus pakai Google Sheets?

Tidak. Workflow 5 berjalan penuh tanpa Sheets — hasilnya hanya dicatat ke arsip lewat webhook, dan itu pun opsional. Sheets dipakai kalau Anda ingin antrean berstatus seperti workflow 4.

### Bisakah saya pakai akun Instagram pribadi?

Tidak. API Instagram hanya menerima akun **Business** atau **Creator** yang terhubung ke halaman Facebook atau akun bisnis. Akun personal harus dikonversi dulu di aplikasi Instagram (Pengaturan → Akun → Beralih ke akun profesional).

### Apakah workflow ini bisa dipakai untuk banyak akun?

Ya, dengan cara berbeda per workflow:

- **Workflow 4** — node `Minta Akun Ebooks` memilih akun kedua lewat tombol. Untuk lebih dari dua akun, tambah cabang serupa atau perluas node `Akun Ebooks`.
- **Workflow 5** — `Siapkan Payload Zernio` selalu memakai `accounts[0]`. Untuk multi-akun, ubah baris itu agar memilih berdasarkan input.

---

## Teknis

### Kenapa ada tiga cara membuat gambar yang berbeda?

Karena trade-off-nya berbeda:

| Cara | Kelebihan | Kekurangan |
|---|---|---|
| **NVIDIA FLUX** (WF 2) | Ilustrasi indah, teks dalam prompt | Teks sering salah eja, butuh API key |
| **editImage** (WF 4) | Teks selalu benar, gratis, instan | Tanpa ilustrasi, hanya blok warna |
| **Pollinations** (WF 5) | Tanpa API key sama sekali | Layanan publik, bisa lambat |

Untuk konten edukasi yang banyak teks, workflow 4 paling aman. Untuk konten visual, workflow 2.

### Kenapa caption saya dipotong?

Batas Instagram: **2200 karakter** dan **30 hashtag**. Node `Siapkan Data Post` menerapkan keduanya sebelum mengirim. Kalau caption terpotong di tengah kalimat, perpendek output AI — minta 8–10 hashtag, bukan 15.

### Kenapa maksimal 10 gambar?

Batas carousel Instagram adalah 10 media. Node `Siapkan Data Post` memotong `slice(0, 10)` dan menolak kalau kurang dari 2.

### Kenapa baris lebih tua dari 2 jam dilewati?

Supaya antrean tidak memproses konten basi saat bot mati lama. Kalau Anda ingin jendela lebih lebar, ubah di node `Pilih Baris Terbaru`:

```js
if (umurMenit < -10 || umurMenit > 120) continue;   // 120 = 2 jam
```

### Kenapa ID baru harus dibuat saat mengulang carousel?

Karena `Pilih Baris Terbaru` menyaring berdasarkan umur yang dihitung **dari `id`**, bukan dari kolom waktu. Mengubah `status` kembali ke `pending` tanpa memperbarui `id` akan tetap dilewati.

### Apakah bisa dijalankan tanpa HTTPS?

Untuk uji lokal, Telegram Trigger sulit dipakai karena Telegram harus menghubungi server Anda. Alternatif: pakai tunnel (`ngrok`, `cloudflared`) atau uji node secara manual dengan **Execute step** tanpa mengaktifkan workflow.

### Kenapa gambar ImgBB hilang setelah sehari?

ImgBB paket gratis menghapus gambar sesuai `expiration`. Workflow mengirim `expiration=86400` (24 jam) — cukup untuk satu siklus posting. Untuk arsip permanen, tambahkan node unggah ke Drive/S3.

### Apakah data saya dikirim ke pihak ketiga?

Ya, sesuai desainnya:

| Data | Tujuan |
|---|---|
| Topik & naskah | Google Gemini |
| Prompt gambar | NVIDIA / Pollinations |
| Gambar final | ImgBB |
| Caption & gambar | Instagram (via Composio/Zernio) |
| Hasil naskah | Google Sheets (milik Anda) |

Tidak ada telemetri tambahan dari workflow ini.

---

## Kustomisasi

### Bagaimana mengubah gaya visual slide?

Di workflow 4, tiga tempat:

1. **`Buat Latar`** — `backgroundColor`, `width`, `height`
2. **`Tulis Teks Slide`** — `fontSize`, `fontColor`, posisi
3. **`Susun Prompt Per Slide`** — hanya untuk workflow 2/5 (bagian `style` di prompt)

Contoh palet gelap:

```
background: #0B1F4B (cover) / #111827 (isi)
judul:      #FFFFFF / #F9FAFB
isi:        #DCE6FF / #9CA3AF
aksen:      #FF7A1A
```

### Bagaimana mengubah jumlah slide?

Jumlah slide mengikuti berapa yang dikembalikan AI, dibatasi template Sheets (maks 10 slot):

- **Workflow 1** — ubah kalimat "7 slide" di prompt `AI Agent Pembuat Carousel`
- **Workflow 4** — mengikuti isi kolom `slide_01` … `slide_10`; kosongkan yang tidak dipakai
- **Workflow 5** — ubah angka di prompt, sama seperti workflow 1

### Bagaimana mengganti model AI?

Klik node `Google Gemini Chat Model` → ubah **Model Name**. Untuk model non-Gemini, ganti node model-nya (misal OpenAI Chat Model) dan sesuaikan credential.

### Bagaimana menambah watermark otomatis?

Kolom `watermark` di Sheets sudah dipakai workflow 4. Kalau kosong, fallback `@AKUN_UTAMA` di node `Tulis Teks Slide`. Isi kolom itu per baris untuk watermark berbeda.

### Bagaimana menjadwalkan posting pada jam tertentu?

Kolom `scheduled_at` **belum dipakai** oleh kode mana pun. Untuk mengaktifkannya:

1. Tambah node Schedule Trigger di jam yang diinginkan
2. Filter baris dengan `scheduled_at` hari ini
3. Teruskan ke rantai `Siapkan Data Post`

Atau pakai fitur penjadwalan bawaan Zernio (`publishNow: false` + `scheduledFor`).

### Bagaimana menambah bahasa selain Indonesia?

Ubah prompt AI Agent dan tambahkan field bahasa:

```text
Bahasa output: {{ $json.raw_text.includes('english') ? 'English' : 'Bahasa Indonesia' }}
```

Perhatikan `lineLength` di node `Tulis Teks Slide` — teks Inggris umumnya lebih panjang per kata, jadi turunkan ke 14–16 untuk judul.

---

## Operasional

### Berapa lama satu carousel diproses?

| Tahap | Estimasi |
|---|---|
| Generate naskah (Gemini) | 5–15 detik |
| Generate 11 gambar (NVIDIA) | 30–90 detik |
| Upload ke ImgBB (11 file) | 10–20 detik |
| Proses container + publish | 20–60 detik |

Total sekitar **1–3 menit** setelah Anda menekan tombol persetujuan.

### Apakah bisa jalan di VPS kecil?

Ya. Beban terberat ada di `editImage` (rendering 11 gambar 1080×1080), yang berjalan di memori. RAM 1 GB cukup untuk satu eksekusi; hindari menjalankan beberapa antrean paralel.

### Bagaimana memantau apakah workflow masih sehat?

- Cek **Executions** di n8n — eksekusi `failed` berwarna merah
- Perhatikan Telegram: notifikasi error otomatis dikirim ke admin
- Cek kolom `status` di Sheets — baris yang lama `pending` berarti antrean macet

### Apakah aman menyimpan API key di workflow?

Sebaiknya **jangan**. Simpan di credential n8n, bukan di parameter node. Workflow 5 memang menaruh ImgBB key di query parameter (untuk kesederhanaan) — kalau workflow itu dibagikan, ganti ke Custom Auth seperti di workflow 2 dan 4.

Repo ini sudah menyertakan `scripts/check-secrets.sh` untuk memeriksa kebocoran sebelum commit.

### Bagaimana cara backup konfigurasi?

```bash
# Ekspor semua workflow
curl -H "X-N8N-API-KEY: <KEY>" https://n8n.domain-anda.com/api/v1/workflows > backup.json
```

Untuk database penuh, backup volume Docker:

```bash
docker run --rm -v n8n_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/n8n-data.tar.gz -C /data .
```

Simpan juga daftar credential di tempat aman — nilai credential tidak ikut terekspor.
