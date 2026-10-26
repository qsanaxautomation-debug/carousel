# Google Sheets

Workflow ini memakai Google Sheets sebagai database antrean: satu baris = satu carousel, satu kolom status = posisi carousel dalam pipeline.

Ada **dua** spreadsheet berbeda:

| Spreadsheet | Dipakai | Isi |
|---|---|---|
| **Database Carousel** | WF 1, 2, 4 | Tab `Carousel` — antrean kerja, punya banyak kolom status |
| **Arsip Carousel** | WF 3 | Tab `Sheet1` — arsip ringkas hasil workflow 5 |

---

## Daftar Isi

1. [Spreadsheet Database Carousel](#1-spreadsheet-database-carousel)
2. [Header Wajib](#2-header-wajib)
3. [Arti Tiap Kolom](#3-arti-tiap-kolom)
4. [Spreadsheet Arsip](#4-spreadsheet-arsip)
5. [Contoh Baris](#5-contoh-baris)
6. [Jebakan Umum](#6-jebakan-umum)

---

## 1. Spreadsheet Database Carousel

### Nama tab

Tab **harus** bernama `Carousel` (C besar, sisanya kecil). Node Google Sheets di workflow mencocokkan nama tab **persis**. Kalau tab Anda bernama `carousel` atau `Sheet1`, node akan gagal dengan error `Sheet not found`.

### Buat cepat

1. Buat spreadsheet baru
2. Ganti nama tab default (`Sheet1`) menjadi `Carousel`
3. Tempel header dari [`examples/carousel-sheet-template.csv`](../examples/carousel-sheet-template.csv) ke baris 1
4. Salin Spreadsheet ID dari URL dan tempel ke node (lihat [01 — Instalasi § 4](01-instalasi.md#4-menyiapkan-google-spreadsheet))

---

## 2. Header Wajib

Urutan kolom berikut mengikuti apa yang ditulis node `Siapkan Baris Sheet` (workflow 1) dan dibaca node `Pengaturan` (workflow 4). **Urutan tidak wajib sama**, tetapi nama header **wajib sama persis**.

```text
id
status
topic
cover_title
cover_subtitle
tags
slide_01_title
slide_01_body
slide_01_highlight
slide_02_title
slide_02_body
slide_02_highlight
slide_03_title
slide_03_body
slide_03_highlight
slide_04_title
slide_04_body
slide_04_highlight
slide_05_title
slide_05_body
slide_05_highlight
slide_06_title
slide_06_body
slide_06_highlight
slide_07_title
slide_07_body
slide_07_highlight
slide_08_title
slide_08_body
slide_08_highlight
slide_09_title
slide_09_body
slide_09_highlight
slide_10_title
slide_10_body
slide_10_highlight
caption
scheduled_at
instagram_post_id
published_at
image_urls
watermark
```

Total **42 kolom**.

> **Nama harus huruf kecil semua**, dengan garis bawah. Node Google Sheets memetakan berdasarkan nama header, bukan posisi. Header `Slide_01_Title` atau `slide 1 title` tidak akan cocok.

---

## 3. Arti Tiap Kolom

### Kolom identitas

| Kolom | Diisi oleh | Keterangan |
|---|---|---|
| `id` | Workflow 1 | Format `CRS-yyyyMMdd-HHmmss` (waktu Asia/Jakarta). **Kunci pencocokan** untuk semua operasi update. Jangan diubah. |
| `status` | Semua workflow | Posisi carousel di pipeline. Lihat [05 — Alur Status](05-alur-status.md). |
| `topic` | Workflow 1 | Teks mentah dari Telegram. Jadi konteks tambahan untuk prompt gambar. |

### Kolom cover (slide pertama)

| Kolom | Isi |
|---|---|
| `cover_title` | Judul utama carousel (dari `output.title`) |
| `cover_subtitle` | Hook (dari `output.hook`) |
| `tags` | Maksimal 4 tag, diambil dari hashtag di caption |

Di workflow 4, `cover_title` + `cover_subtitle` menjadi **slide pertama** (latar biru gelap), dan slide terakhir juga memakai gaya cover.

### Kolom slide (10 set)

| Kolom | Isi |
|---|---|
| `slide_NN_title` | Headline slide ke-NN (maks 5–7 kata dari prompt AI) |
| `slide_NN_body` | Body text slide ke-NN (maks 2–3 kalimat) |
| `slide_NN_highlight` | Cadangan untuk penekanan visual. Saat ini **selalu kosong** — workflow 1 mengisinya dengan string kosong. Anda bisa memakainya manual untuk menyorot satu frasa. |

> Template memuat maksimal **10 slide isi**. Workflow 1 mengisi 9 slide pertama dari AI, lalu memakai slot ke-10 untuk closing slide (headline + CTA). Jadi carousel normal = 1 cover + 9 isi + 1 closing.

### Kolom publikasi

| Kolom | Diisi oleh | Keterangan |
|---|---|---|
| `caption` | Workflow 1 | Caption Instagram lengkap dengan hashtag |
| `scheduled_at` | — | Belum dipakai. Disediakan untuk penjadwalan manual. |
| `instagram_post_id` | Workflow 4 | ID media Instagram setelah berhasil publish |
| `published_at` | Workflow 4 | Waktu publish, format `yyyy-MM-dd HH:mm` WIB |
| `image_urls` | Workflow 2, 4 | URL gambar dipisah koma. Wajib publik agar Instagram bisa mengambilnya. |
| `watermark` | Anda (manual) | Teks watermark di setiap slide. Jika kosong, dipakai `@AKUN_UTAMA` (lihat node `Tulis Teks Slide`). |

---

## 4. Spreadsheet Arsip

Dipakai workflow `03-simpan-ke-google-sheet.json` dan menerima data dari workflow 5.

### Nama tab

Tab `Sheet1` (default). Jika Anda mengganti nama, sesuaikan node `Simpan ke Google Sheet`.

### Header (8 kolom)

```text
tanggal
topik
judul
caption
hashtag
slides
gambar_urls
status
```

| Kolom | Isi |
|---|---|
| `tanggal` | `yyyy-MM-dd HH:mm` WIB saat webhook menerima data |
| `topik` | Teks permintaan awal |
| `judul` | Judul carousel |
| `caption` | Caption lengkap |
| `hashtag` | Hashtag dari closing slide |
| `slides` | Semua slide digabung satu sel, dipisah ` \| ` (contoh: `1. Judul - Isi \| 2. Judul - Isi`) |
| `gambar_urls` | URL gambar dipisah koma |
| `status` | Default `draft` |

> Spreadsheet arsip ini **berbeda** dari Database Carousel. Workflow 5 menulis ke arsip lewat webhook, bukan langsung ke Sheets, supaya tidak butuh credential Google di workflow itu.

---

## 5. Contoh Baris

Baris yang dihasilkan workflow 1 untuk permintaan "tips produktivitas WFH, 5 slide":

| Kolom | Nilai |
|---|---|
| `id` | `CRS-20261026-104512` |
| `status` | `pending` |
| `topic` | `topik: tips produktivitas WFH \| slide: 5 \| tone: inspiratif` |
| `cover_title` | `5 Cara Tetap Fokus Kerja dari Rumah` |
| `cover_subtitle` | `90% pekerja remote kehilangan fokus sebelum jam 10 pagi!` |
| `tags` | `produktivitas, wfh, remotework, fokus` |
| `slide_01_title` | `Buat Zona Kerja Terpisah` |
| `slide_01_body` | `Jangan kerja dari kasur. Satu meja khusus membuat otak langsung masuk mode kerja.` |
| `slide_01_highlight` | *(kosong)* |
| `slide_02_title` | … |
| `caption` | `Kerja dari rumah malah makin tidak fokus? … #produktivitas #wfh` |
| `scheduled_at` | *(kosong)* |
| `instagram_post_id` | *(kosong sampai publish)* |
| `published_at` | *(kosong sampai publish)* |
| `image_urls` | *(kosong sampai gambar dibuat)* |
| `watermark` | `@AKUN_UTAMA` |

Setelah workflow 4 selesai, `status` = `posted`, `image_urls` terisi, `instagram_post_id` dan `published_at` terisi.

---

## 6. Jebakan Umum

| Masalah | Sebab | Solusi |
|---|---|---|
| `Sheet not found` | Nama tab bukan `Carousel` | Rename tab persis `Carousel` |
| `Column not found` | Header beda huruf/spasi | Pastikan semua header huruf kecil + garis bawah |
| Update tidak mengena baris mana pun | `id` duplikat atau kosong | `id` harus unik; workflow 1 membuatnya dari timestamp |
| `image_urls` tidak terbaca | Pemisah bukan koma+spasi | Workflow menulis `url1, url2`; jangan ubah format |
| Baris tidak diproses workflow 4 | Umur baris > 120 menit | Node `Pilih Baris Terbaru` menyaring; buat baris baru atau ubah status manual |
| Watermark kosong di gambar | Kolom `watermark` tidak ada | Tambahkan kolom, atau biarkan fallback `@AKUN_UTAMA` |
| Angka `id` berubah format | Google Sheets menganggapnya tanggal | Format kolom `id` sebagai **Plain text** |

> **Selalu format kolom `id` sebagai Plain text.** Kalau Google Sheets mengira isinya tanggal, nilai `CRS-20261026-104512` bisa berubah dan semua operasi `update` akan gagal mencocokkan baris.
