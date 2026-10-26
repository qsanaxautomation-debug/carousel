# Alur Status

Satu baris di tab `Carousel` bergerak melewati serangkaian status. Dokumen ini menjelaskan setiap status, siapa yang mengubahnya, dan apa yang terjadi kalau macet.

---

## Diagram Status

```
                      (workflow 1 / input manual)
                                │
                                ▼
                          ┌──────────┐
                          │ pending  │
                          └────┬─────┘
                               │ workflow 4: tiap 5 menit,
                               │ hanya baris < 120 menit
                               ▼
                ┌────────────────────────────────┐
                │ menunggu_persetujuan_gambar    │
                └───────┬─────────────┬──────────┘
                        │             │
              [🎨 Ya]   │             │   [⏭️ Lewati]
                        ▼             ▼
                 ┌────────────┐   ┌──────────┐
                 │ generating │   │ skipped  │  ← akhir
                 └─────┬──────┘   └──────────┘
                       │ gambar selesai + upload ImgBB
                       ▼
                 ┌──────────────┐
                 │ image_ready  │
                 └──────┬───────┘
                        │ preview dikirim, minta persetujuan posting
                        ▼
              ┌──────────────────────┐
              │ minta_persetujuan    │
              │ (menunggu tombol)    │
              └───┬──────────┬───────┘
                  │          │
        [📲 Post] │          │ [↪️ Akun lain / Batal]
                  ▼          ▼
            ┌─────────┐  ┌──────────┐
            │ posted  │  │ rejected │  ← akhir
            └─────────┘  └──────────┘
                 ▲
                 │ gagal di titik mana pun
            ┌─────────┐
            │ failed  │  ← akhir (bisa diulang manual)
            └─────────┘
```

---

## Tabel Status

| Status | Diubah oleh | Arti | Aksi berikutnya |
|---|---|---|---|
| `pending` | Workflow 1 (`Siapkan Baris Sheet`) atau Anda manual | Carousel baru, belum disentuh | Workflow 4 mengambilnya dalam ≤ 5 menit |
| `menunggu_persetujuan_gambar` | `Tandai Menunggu Persetujuan` | Bot sudah kirim tombol "Buat gambar?" dan menunggu admin | Tekan tombol di Telegram |
| `generating` | `Tandai Generating` | Gambar sedang dibuat, satu per satu | Tunggu; jangan edit baris |
| `image_ready` | `Simpan Gambar dan Status image_ready` | Semua gambar jadi dan sudah di ImgBB | Otomatis lanjut ke preview |
| `posted` | `Tandai Posted` | Berhasil terbit di Instagram | Selesai |
| `failed` | `Tandai Gagal Publish` / `Tandai Gagal Container` / `Tandai Gagal (Error)` | Gagal di salah satu tahap | Perbaiki penyebab, ubah status ke `pending` untuk mengulang |
| `rejected` | `Tandai Ditolak` | Admin menolak posting | Selesai; ubah ke `pending` bila ingin mencoba lagi |
| `skipped` | `Tandai Dilewati` | Admin melewati pembuatan gambar | Selesai; ubah ke `pending` untuk mengulang |

---

## Detail Tiap Transisi

### `pending` → `menunggu_persetujuan_gambar`

Node `Ambil Baris Pending` memfilter `status = pending`. Lalu `Pilih Baris Terbaru` (node Code) memilih **satu** baris dengan aturan:

- `id` harus cocok pola `CRS-yyyyMMdd-HHmmss`
- Umur baris antara **-10 menit** (toleransi jam) sampai **120 menit**
- Baris termuda menang

Baris lebih tua dari 120 menit **dilewati tanpa notifikasi**. Ini disengaja agar antrean tidak memproses konten basi. Konsekuensinya: kalau bot mati lebih dari 2 jam, baris lama harus di-`pending`-kan ulang manual.

### `menunggu_persetujuan_gambar` → `generating` atau `skipped`

Node `Minta Persetujuan Gambar` memakai `sendAndWait` dengan tombol `🎨 Ya, Buat Gambar` / `⏭️ Lewati`.

**Batas tunggu belum diaktifkan.** Di workflow yang dirilis, `limitWaitTime` bernilai `null`, artinya eksekusi menunggu jawaban tanpa batas waktu. Selama menunggu, baris tetap `menunggu_persetujuan_gambar` dan eksekusi menggantung.

Kalau Anda ingin ada batas (disarankan), buka node itu → **Options** → **Limit Wait Time** → isi `24` hour. Dengan begitu, tidak ada jawaban dalam 24 jam berarti cabang **tidak disetujui** dijalankan dan status menjadi `skipped`.

### `generating` → `image_ready`

Untuk setiap slide:

1. `Buat Latar` — kanvas 1080×1080, latar `#0B1F4B` (gelap) untuk cover, `#FFFFFF` (putih) untuk slide isi
2. `Tulis Teks Slide` — menulis nomor slide (`1/8`), judul, isi, dan watermark
3. `Unggah ke ImgBB` — dapat URL publik
4. `Kumpulkan Hasil Unggahan` → `Susun Daftar URL` — gabung semua URL

Jika tidak satu pun URL berhasil, node Code melempar error dan baris ditandai `failed`.

### `image_ready` → `minta_persetujuan` (implisit)

Setelah `image_ready`, workflow mengirim semua slide sebagai foto (`Kirim Preview Foto`) lalu `Minta Persetujuan Posting`.

Status Sheet **tidak** berubah pada tahap ini — tetap `image_ready`. Status persetujuan posting tidak punya kolom sendiri. Kalau Anda ingin melacaknya, tambahkan kolom dan node update.

### Menuju `posted`

1. `Siapkan Data Post` — ambil `connected_account_id`, `ig_user_id`, `caption` (dipotong 2200 karakter, maks 30 hashtag), dan maksimal 10 URL gambar (minimal 2)
2. `Buat Container Carousel` — JSON-RPC ke Composio
3. `Cek Container` — bedah respons SSE, ambil `creation_id`
4. `Publish Carousel ke Instagram` — publish
5. `Baca Hasil Publish` → `Publish Berhasil?`
6. `Tandai Posted` — isi `instagram_post_id` + `published_at`

### Menuju `failed`

Tiga jalur berbeda:

| Jalur | Node | Kapan |
|---|---|---|
| Container gagal | `Notif Gagal Container` → `Tandai Gagal Container` | Composio tidak mengembalikan `creation_id` |
| Publish gagal | `Notif Gagal Publish` → `Tandai Gagal Publish` | Container ada tapi publish gagal |
| Error tak tertangkap | `Saat Antrean Gagal` (Error Trigger) → `Ambil Baris Generating` → `Tandai Gagal (Error)` | Exception di node mana pun |

Jalur ketiga mencari baris yang masih `generating` lalu menandainya `failed`, jadi baris tidak tertinggal dalam status "sedang diproses" selamanya.

---

## Mengulang Carousel yang Gagal

Karena `failed`, `skipped`, dan `rejected` adalah status akhir, mengulang cukup dengan:

1. Perbaiki penyebab (lihat [06 — Troubleshooting](06-troubleshooting.md))
2. Ubah `status` kembali ke `pending`
3. **Perbarui `id`** agar timestamp-nya baru — kalau tidak, node `Pilih Baris Terbaru` akan menganggapnya terlalu tua dan melewatinya

Contoh `id` baru: `CRS-20261026-143000`.

> Alternatif: buat baris baru dengan mengetik ulang topik ke bot, lalu biarkan workflow 1 mengisi baris dengan `id` segar.

---

## Status di Workflow 5 (tanpa Sheets)

Workflow `05-ai-carousel-lengkap-zernio.json` **tidak** memakai kolom status. Alurnya dikendalikan sepenuhnya oleh tombol Telegram, dan hasil akhirnya hanya dicatat sebagai satu baris `draft` di spreadsheet arsip.

Kalau Anda ingin pipeline berstatus, pakai workflow 4.
