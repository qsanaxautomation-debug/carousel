# Kredensial

Cara membuat setiap credential yang dibutuhkan, lalu memasangnya ke node.

Credential **tidak** disertakan di repo. Semua blok `credentials` dihapus saat sanitasi, jadi setiap node yang butuh koneksi akan menampilkan peringatan sampai Anda memilih credential.

---

## Daftar Isi

1. [Telegram API](#1-telegram-api)
2. [Google Gemini (PaLM) API](#2-google-gemini-palm-api)
3. [Google Sheets OAuth2](#3-google-sheets-oauth2)
4. [ImgBB](#4-imgbb)
5. [NVIDIA API (Bearer)](#5-nvidia-api-bearer)
6. [Zernio (Header Auth)](#6-zernio-header-auth)
7. [Composio (Custom Auth)](#7-composio-custom-auth)
8. [Tabel Ringkas Node → Credential](#8-tabel-ringkas-node--credential)

---

## 1. Telegram API

### Buat

1. Buka [@BotFather](https://t.me/BotFather) → `/newbot`
2. Simpan token: `<angka>:<string_acak>`

### Isi di n8n

Buat credential **Telegram API**:

| Field | Nilai |
|---|---|
| Access Token | token dari BotFather |

### Dipakai oleh

- `Telegram Bot Trigger` (semua workflow)
- Semua node `n8n-nodes-base.telegram` (kirim pesan, foto, `sendAndWait`)

> **Penting untuk `sendAndWait`.** Tombol persetujuan memakai `chatApproval: true` dan `approverIds` diisi Chat ID admin. Pastikan bot sudah pernah di-`/start` oleh admin, kalau tidak bot tidak bisa mengirim pesan ke chat tersebut.

---

## 2. Google Gemini (PaLM) API

### Buat

1. Buka [Google AI Studio](https://aistudio.google.com/apikey)
2. **Create API key** → salin

### Isi di n8n

Buat credential **Google Gemini(PaLM) Api**:

| Field | Nilai |
|---|---|
| API Key | key dari AI Studio |

### Dipakai oleh

- `Google Gemini Chat Model` di workflow 1, 4 (via AI Agent), dan 5

### Model

Default di workflow: `models/gemini-3.1-flash-lite`.

Bisa diganti di field **Model Name** pada node `Google Gemini Chat Model`. Model yang lebih besar memberi naskah lebih rapi tetapi lebih lambat dan lebih mahal.

---

## 3. Google Sheets OAuth2

### Buat

Cara tercepat (n8n Cloud atau self-hosted dengan redirect URI terdaftar):

1. Di n8n: **Credentials** → **New** → **Google Sheets OAuth2 API**
2. Salin **OAuth Redirect URL** yang ditampilkan n8n
3. Buka [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
4. **Create Credentials** → **OAuth client ID** → tipe **Web application**
5. Tambahkan **Authorized redirect URI** = URL dari langkah 2
6. Salin **Client ID** dan **Client Secret** ke n8n
7. Klik **Connect my account** → izinkan akses

Aktifkan juga **Google Sheets API** di project yang sama lewat **APIs & Services → Library**.

### Dipakai oleh

- `Ambil Baris Pending`, `Tandai Generating`, `Simpan Gambar dan Status image_ready`, `Tandai Posted`, `Tandai Gagal Publish`, `Tandai Gagal Container`, `Tandai Ditolak`, `Tandai Dilewati`, `Tandai Menunggu Persetujuan`, `Tandai Gagal (Error)`, `Ambil Baris Generating`
- `Simpan ke Sheet Carousel` (workflow 1)
- `Isi image_urls di Sheet` (workflow 2)
- `Simpan ke Google Sheet` (workflow 3)

### Izin minimum

Credential butuh akses baca **dan** tulis ke spreadsheet. Pastikan akun yang di-OAuth adalah akun yang punya akses edit ke spreadsheet tersebut (atau spreadsheet dibagikan ke akun itu sebagai Editor).

---

## 4. ImgBB

ImgBB menerima API key sebagai **query parameter**, bukan header. Ada dua cara memasang.

### Cara A — Query parameter langsung di URL (paling sederhana)

Di node **Unggah ke ImgBB** → **Query Parameters** → tambahkan:

| Name | Value |
|---|---|
| `key` | API key ImgBB Anda |
| `expiration` | `86400` (detik, opsional) |

Cara ini dipakai workflow 5. Placeholder `REPLACE_WITH_IMGBB_API_KEY` ada di situ.

### Cara B — Custom Auth credential

Dipakai workflow 2 dan 4 supaya key tidak tertulis di node:

1. **Credentials** → **New** → **Custom Auth**
2. Isi **JSON**:

```json
{
  "headers": {},
  "qs": {
    "key": "API_KEY_IMGBB_ANDA"
  }
}
```

3. Di node **Unggah ke ImgBB**: **Authentication** = `Generic Credential Type`, **Generic Auth Type** = `Custom Auth`, pilih credential tadi

### Dipakai oleh

- `Unggah ke ImgBB` di workflow 2, 4, 5

### Catatan

Gambar dihapus otomatis setelah 24 jam pada paket gratis (`expiration=86400`). Cukup untuk proses posting Instagram, tetapi preview lama akan mati.

---

## 5. NVIDIA API (Bearer)

### Buat

1. Buka [build.nvidia.com](https://build.nvidia.com)
2. Pilih model **FLUX.1-schnell**
3. **Get API Key** → salin (biasanya berawalan `nvapi-`)

### Isi di n8n

Buat credential **Bearer Auth**:

| Field | Nilai |
|---|---|
| Bearer Token | API key NVIDIA |

### Dipakai oleh

- `Buat Gambar NVIDIA` (workflow 2) — endpoint `https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell`

### Catatan

Workflow mengirim `seed: 0` dan `steps: 4` (FLUX.1-schnell dioptimalkan untuk 4 langkah). Header `NVCF-POLL-SECONDS: 120` memberi waktu tunggu generasi hingga 120 detik.

---

## 6. Zernio (Header Auth)

### Buat

1. Daftar di [zernio.com](https://zernio.com)
2. Hubungkan akun Instagram di dashboard
3. Salin API key (`sk_...`)

### Isi di n8n

Buat credential **Header Auth**:

| Field | Nilai |
|---|---|
| Name | `Authorization` |
| Value | `Bearer sk_...` |

### Dipakai oleh

- `POST ke Instagram via Zernio` (workflow 5)
- `Ambil Akun Instagram Zernio` (workflow 5)

### Catatan

Workflow 5 mengambil Account ID otomatis dari `GET https://zernio.com/api/v1/accounts?platform=instagram`. Jadi Anda **tidak** perlu mengisi Account ID manual — cukup API key. Placeholder `REPLACE_WITH_ZERNIO_API_KEY` adalah pengganti nilai header `Authorization`.

---

## 7. Composio (Custom Auth)

### Buat

1. Daftar di [composio.dev](https://composio.dev)
2. Hubungkan akun Instagram di dashboard
3. Catat **Connected Account ID** (dipakai sebagai field `account` di payload)
4. Catat **Instagram User ID** (field `ig_user_id`)
5. Buat API key

### Isi di n8n

Buat credential **Custom Auth**:

```json
{
  "headers": {
    "x-api-key": "API_KEY_COMPOSIO_ANDA"
  }
}
```

> Nama header mengikuti dokumentasi Composio terbaru. Jika request mengembalikan 401, periksa dashboard Composio untuk nama header yang benar.

### Dipakai oleh

- `Buat Container Carousel` (workflow 4)
- `Publish Carousel ke Instagram` (workflow 4)

### Catatan

Composio dipanggil lewat JSON-RPC:

```text
POST https://connect.composio.dev/mcp
Accept: application/json, text/event-stream
```

Dengan tool `COMPOSIO_MULTI_EXECUTE_TOOL`, lalu `INSTAGRAM_CREATE_CAROUSEL_CONTAINER` untuk membuat container, dan `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` untuk menerbitkan.

Respons berbentuk Server-Sent Events (`data: {...}`), itulah sebabnya workflow memakai node **Code** untuk membedah baris `data:` sebelum membaca `creation_id`.

---

## 8. Tabel Ringkas Node → Credential

| Node | Workflow | Credential |
|---|---|---|
| Telegram Bot Trigger | 1, 4, 5 | Telegram API |
| Kirim Pesan Proses | 1, 4, 5 | Telegram API |
| Kirim Hasil Carousel | 1, 5 | Telegram API |
| Kirim Detail Slides | 1, 4, 5 | Telegram API |
| Minta Persetujuan Generate Gambar | 5 | Telegram API |
| Minta Persetujuan Gambar | 4 | Telegram API |
| Kirim Preview Foto | 4 | Telegram API |
| Minta Persetujuan Posting | 4 | Telegram API |
| Minta Akun Ebooks | 4 | Telegram API |
| Kirim Foto ke Telegram | 5 | Telegram API |
| Tanya Post ke Instagram? | 5 | Telegram API |
| Konfirmasi Tersimpan ke Sheet | 1 | Telegram API |
| Notif Gagal Simpan Sheet | 1 | Telegram API |
| Semua node Notif/Tandai di 4 | 4 | Telegram API |
| Google Gemini Chat Model | 1, 4, 5 | Google Gemini (PaLM) API |
| Ambil Baris Pending | 2, 4 | Google Sheets OAuth2 |
| Simpan ke Sheet Carousel | 1 | Google Sheets OAuth2 |
| Isi image_urls di Sheet | 2 | Google Sheets OAuth2 |
| Simpan ke Google Sheet | 3 | Google Sheets OAuth2 |
| Semua node Tandai* / Simpan Gambar* | 4 | Google Sheets OAuth2 |
| Buat Gambar NVIDIA | 2 | Bearer Auth (NVIDIA) |
| Unggah ke ImgBB | 2, 4 | Custom Auth (ImgBB qs) |
| Upload ke ImgBB | 5 | Query param `key` (atau Custom Auth) |
| POST ke Instagram via Zernio | 5 | Header Auth (Zernio) |
| Ambil Akun Instagram Zernio | 5 | Header Auth (Zernio) |
| Buat Container Carousel | 4 | Custom Auth (Composio) |
| Publish Carousel ke Instagram | 4 | Custom Auth (Composio) |
| Simpan Carousel ke Sheet | 5 | — (HTTP ke webhook, tanpa auth) |

---

## Memasang credential ke node

1. Buka node
2. Pada bagian **Credential to connect with**, pilih credential yang sudah dibuat
3. Simpan

Untuk mengganti banyak node sekaligus: klik kanan node → **Copy** → tempel credential dengan **Paste**. Cara lebih cepat: buka **Workflow Settings → Credentials**, atau gunakan **Credential** yang sama di semua node sejenis.

Jika node masih menampilkan ikon merah setelah credential dipilih, biasanya berarti:

- Credential kurang izin (misal OAuth Sheets tanpa scope tulis)
- Spreadsheet tidak dibagikan ke akun OAuth
- Token kedaluwarsa
