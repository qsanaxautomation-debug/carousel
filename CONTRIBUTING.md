# Contributing

Terima kasih sudah ingin berkontribusi. Dokumen ini menjelaskan cara mengubah repo tanpa merusak keamanan atau konsistensi dokumentasi.

---

## Aturan Paling Penting

**Jangan pernah commit data asli.**

Repo ini dipublikasikan. Setiap commit akan terlihat publik. Data yang **tidak boleh** masuk:

- Token bot Telegram
- API key apa pun (Gemini, ImgBB, NVIDIA, Composio, Zernio)
- ID spreadsheet asli
- Chat ID Telegram asli
- Nama domain atau email organisasi asli
- Screenshot yang menampilkan data pelanggan
- Ekspor workflow yang masih punya blok `credentials`

Gunakan placeholder yang sudah ditetapkan:

| Jenis | Placeholder |
|---|---|
| Spreadsheet database | `REPLACE_WITH_CAROUSEL_SHEET_ID` |
| Spreadsheet arsip | `REPLACE_WITH_ARCHIVE_SHEET_ID` |
| Chat ID admin | `REPLACE_WITH_TELEGRAM_ADMIN_CHAT_ID` |
| API key ImgBB | `REPLACE_WITH_IMGBB_API_KEY` |
| API key Zernio | `REPLACE_WITH_ZERNIO_API_KEY` |
| Connected account Composio | `REPLACE_WITH_COMPOSIO_ACCOUNT_ID` |
| Instagram user ID | `REPLACE_WITH_IG_USER_ID` |
| Username Instagram | `REPLACE_WITH_IG_USERNAME` |
| Domain n8n | `YOUR-N8N-HOST` |
| Token Telegram | `<TOKEN_DARI_BOTFATHER>` |

---

## Sebelum Commit

Jalankan dua pemeriksaan ini. Keduanya **wajib lulus**.

```bash
bash scripts/check-secrets.sh
python3 scripts/verify-repo.py
```

`check-secrets.sh` mencari pola data sensitif. `verify-repo.py` memeriksa:

- Semua link internal di markdown menunjuk file yang ada
- Semua anchor `#...` cocok dengan heading di file tujuan
- Setiap file di `workflows/` adalah JSON valid
- Setiap node punya `name` dan `type`
- Target koneksi menunjuk node yang benar-benar ada
- Placeholder wajib benar-benar ada di file yang seharusnya

Kalau salah satu gagal, perbaiki dulu — jangan `git commit --no-verify`.

---

## Mengubah Workflow

### Alur yang benar

1. Ekspor workflow dari n8n: **⋯ → Download**
2. Simpan ke lokasi sementara, **jangan** langsung ke `workflows/`
3. Sanitasi: hapus semua blok `credentials`, ganti nilai asli dengan placeholder
4. Salin hasil bersih ke `workflows/`
5. Jalankan `python3 scripts/verify-repo.py`
6. Jalankan `bash scripts/check-secrets.sh`

### Yang harus dihapus saat sanitasi

```json
"credentials": {
  "telegramApi": { "id": "abc123", "name": "Telegram account" }
}
```

Hapus seluruh objek `credentials` dari setiap node. Alasan: ID credential membocorkan struktur server dan membuat workflow tidak bisa diimpor bersih di instance lain.

### Yang harus diganti

Cari nilai asli di parameter node dan ganti dengan placeholder. Yang paling sering terlewat:

- `chat_id` bernilai angka panjang
- `documentId` / `spreadsheetId` bernilai string 44 karakter
- Query parameter `key` pada ImgBB
- Header `Authorization` berisi `Bearer sk_...`

### Nama file

Ikuti pola yang ada: `NN-nama-singkat.json`, huruf kecil, tanda hubung.

```
01-ai-carousel-telegram-bot.json
02-generate-gambar-nvidia.json
```

Kalau menambah workflow baru, pakai nomor berikutnya dan tambahkan ke tabel di `README.md` serta `docs/04-arsitektur.md`.

---

## Mengubah Dokumentasi

### Bahasa dan gaya

- Bahasa Indonesia, sapaan **"Anda"** (bukan "kamu")
- Kalimat pendek, satu ide per kalimat
- Hindari emoji di dalam dokumen teknis
- Sebut nama node **persis** seperti di n8n, dalam huruf tebal: node **Pilih Baris Terbaru**

### Struktur dokumen

Setiap file `docs/NN-*.md` mengikuti pola:

```markdown
# Judul

Satu paragraf ringkas: dokumen ini untuk apa.

---

## Daftar Isi

1. [Bagian](#1-bagian)

---

## 1. Bagian

...

---

## 2. Bagian
```

Anchor harus cocok dengan heading. Untuk heading `## 1. Instalasi`, anchor-nya `#1-instalasi` — angka, tanda hubung, huruf kecil, tanda baca dibuang. `verify-repo.py` memeriksa ini otomatis.

### Jangan mengklaim yang tidak ada

Kalau menulis "sertakan screenshot", pastikan file gambarnya benar-benar ada di repo. Kalau menulis "mendukung versi X", pastikan sudah diverifikasi. Klaim yang tidak terverifikasi akan ditolak saat review.

### Menambah bagian baru

1. Tambahkan ke Daftar Isi di file itu
2. Tambahkan ke Daftar Isi di `README.md` kalau berupa file baru
3. Perbarui anchor di dokumen lain yang menunjuk ke sana

---

## Format Commit

Gunakan [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipe>(<cakupan>): <ringkasan>

<penjelasan opsional>
```

Tipe yang dipakai:

| Tipe | Untuk |
|---|---|
| `docs` | Perubahan dokumentasi |
| `feat` | Workflow atau kemampuan baru |
| `fix` | Perbaikan bug pada workflow/dokumentasi |
| `chore` | Perkakas, `.gitignore`, skrip |

Contoh:

```
docs(instalasi): tambah langkah aktivasi modul Data Table
fix(workflow): perbaiki parsing respons SSE Composio
chore(scripts): tambah pemeriksa anchor markdown
```

Satu commit = satu perubahan logis. Jangan gabung perbaikan dokumentasi dan perubahan workflow dalam satu commit.

---

## Melaporkan Bug

Sertakan:

1. Versi n8n (`docker exec n8n n8n --version`)
2. Nama workflow dan node yang gagal
3. Pesan error lengkap
4. Output JSON node **sebelum** node yang gagal (sensor data sensitif)
5. Langkah reproduksi

Tanpa poin 3 dan 4, laporan sulit ditindaklanjuti.

---

## Mengajukan Pull Request

1. Fork repo
2. Buat branch: `git checkout -b docs/perbaikan-instalasi`
3. Lakukan perubahan
4. Jalankan kedua pemeriksaan sampai lulus
5. Commit dengan pesan sesuai format
6. Push dan buka PR

Deskripsi PR sebaiknya menyebut:

- Apa yang diubah dan **kenapa**
- Bagian mana yang perlu ditinjau
- Hasil `check-secrets.sh` dan `verify-repo.py`

---

## Hal yang Tidak Diterima

- Commit berisi credential atau data asli
- Klaim fitur yang tidak diimplementasikan
- Perubahan yang hanya mengubah gaya penulisan tanpa memperbaiki isi
- Penambahan dependensi berat tanpa alasan jelas
- Workflow yang hanya berjalan di instance Anda (hardcoded ID, tanpa placeholder)
