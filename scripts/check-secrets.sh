#!/usr/bin/env bash
# ===================================================================
# Pemeriksa data sensitif pada workflow dan dokumentasi.
# Jalankan sebelum commit: bash scripts/check-secrets.sh
# Exit code 1 bila ditemukan data sensitif.
# ===================================================================

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

FOUND=0

report() {
  printf '  %s\n' "$1"
  FOUND=1
}

echo "Memeriksa data sensitif di: $ROOT"
echo

# --- 1. Token JWT / n8n API key ---
echo "[1] Token JWT / API key n8n"
if grep -rnE 'eyJhbGciOi[A-Za-z0-9_-]{10,}' \
    --include='*.json' --include='*.md' --include='*.example' --include='*.sh' . 2>/dev/null; then
  report "Ditemukan token JWT"
else
  echo "  OK — tidak ada token"
fi
echo

# --- 2. Token bot Telegram ---
echo "[2] Token bot Telegram"
if grep -rnE '[0-9]{8,12}:[A-Za-z0-9_-]{30,}' \
    --include='*.json' --include='*.md' --include='*.example' --include='*.csv' . 2>/dev/null; then
  report "Ditemukan token bot Telegram"
else
  echo "  OK — tidak ada token bot"
fi
echo

# --- 3. API key Google ---
echo "[3] API key Google"
if grep -rnE 'AIza[A-Za-z0-9_-]{30,}' \
    --include='*.json' --include='*.md' --include='*.example' . 2>/dev/null; then
  report "Ditemukan API key Google"
else
  echo "  OK — tidak ada API key"
fi
echo

# --- 4. OAuth client secret ---
echo "[4] OAuth client secret"
if grep -rnE 'GOCSPX-[A-Za-z0-9_-]{10,}' \
    --include='*.json' --include='*.md' --include='*.example' . 2>/dev/null; then
  report "Ditemukan client secret"
else
  echo "  OK — tidak ada client secret"
fi
echo

# --- 5. API key pihak ketiga dengan pola khas ---
echo "[5] API key pihak ketiga (ImgBB, NVIDIA, Zernio)"
# ImgBB: 32 karakter hex
if grep -rnE --exclude='check-secrets.sh' '\b[0-9a-f]{32}\b' \
    --include='*.json' --include='*.md' --include='*.example' . 2>/dev/null; then
  report "Ditemukan string 32 hex (kemungkinan API key ImgBB)"
else
  echo "  OK — tidak ada key ImgBB"
fi
# NVIDIA
if grep -rnE 'nvapi-[A-Za-z0-9_-]{20,}' \
    --include='*.json' --include='*.md' --include='*.example' . 2>/dev/null; then
  report "Ditemukan API key NVIDIA"
else
  echo "  OK — tidak ada key NVIDIA"
fi
# Zernio
if grep -rnE --exclude='check-secrets.sh' 'Bearer sk_[A-Za-z0-9]{12,}' \
    --include='*.json' --include='*.md' --include='*.example' . 2>/dev/null; then
  report "Ditemukan token Zernio"
else
  echo "  OK — tidak ada token Zernio"
fi
echo

# --- 6. ID asli dari instalasi sumber ---
# Deteksi generik, BUKAN daftar literal.
# Jangan menaruh ID asli di skrip ini: itu sendiri merupakan kebocoran
# dan akan ikut terpublikasikan ke dalam git history.
echo "[6] ID internal yang tidak sengaja tertinggal"
# Chat ID Telegram: 9-10 digit berdiri sendiri sebagai nilai JSON
if grep -rnE --exclude='check-secrets.sh' '"(chat_id|chatId)"\s*:\s*"[0-9]{6,}"' \
    --include='*.json' . 2>/dev/null; then
  report "Ditemukan chat ID numerik di workflow"
else
  echo "  OK — tidak ada chat ID numerik"
fi
# Google Sheet ID: 44 karakter base64url di parameter documentId
if grep -rnE --exclude='check-secrets.sh' '"value"\s*:\s*"[A-Za-z0-9_-]{40,}"' \
    --include='*.json' workflows/ 2>/dev/null | grep -v 'REPLACE_WITH'; then
  report "Ditemukan nilai panjang menyerupai Sheet ID"
else
  echo "  OK — tidak ada Sheet ID"
fi
# Domain internal dan nama akun bisnis.
# Pola ditulis generik supaya skrip ini tidak sendiri memuat nama akun asli.
for pat in 'komdigi\.go\.id' 'mail\.komdigi\.' '@[A-Za-z0-9._-]*qsanax[A-Za-z0-9._-]*'; do
  if grep -rnE --exclude='check-secrets.sh' "$pat" \
       --include='*.json' --include='*.md' --include='*.example' --include='*.csv' . 2>/dev/null; then
    report "Ditemukan pola internal: $pat"
  fi
done
echo

# --- 7. Alamat email asli ---
echo "[7] Alamat email asli"
if grep -rnoE --exclude='check-secrets.sh' '[A-Za-z0-9._%+-]+@(komdigi\.go\.id|gmail\.com|qsanax[a-z]*)' \
    --include='*.json' --include='*.md' --include='*.example' --include='*.csv' . 2>/dev/null; then
  report "Ditemukan alamat email asli"
else
  echo "  OK — hanya alamat contoh"
fi
echo

# --- 8. Blok credentials yang belum dihapus ---
echo "[8] Blok credentials di workflow"
if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY'
import json, pathlib, sys
bad = 0
for f in sorted(pathlib.Path('workflows').glob('*.json')):
    d = json.loads(f.read_text())
    for n in d.get('nodes', []):
        if n.get('credentials'):
            print(f"  {f.name}: node '{n['name']}' masih punya credentials")
            bad += 1
sys.exit(1 if bad else 0)
PY
  if [ $? -ne 0 ]; then report "Ada blok credentials yang belum dihapus"; else echo "  OK — tidak ada credentials"; fi
else
  echo "  SKIP — python3 tidak tersedia"
fi
echo

# --- 9. Validitas JSON workflow ---
echo "[9] Validitas JSON workflow"
if command -v python3 >/dev/null 2>&1; then
  for f in workflows/*.json; do
    [ -e "$f" ] || continue
    if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
      echo "  OK — $f"
    else
      report "JSON tidak valid: $f"
    fi
  done
else
  echo "  SKIP — python3 tidak tersedia"
fi
echo

# --- 10. Placeholder wajib ada ---
echo "[10] Placeholder wajib"
REQ=(
  REPLACE_WITH_CAROUSEL_SHEET_ID
  REPLACE_WITH_TELEGRAM_ADMIN_CHAT_ID
  REPLACE_WITH_IMGBB_API_KEY
  REPLACE_WITH_ZERNIO_API_KEY
  REPLACE_WITH_COMPOSIO_ACCOUNT_ID
  REPLACE_WITH_IG_USER_ID
  YOUR-N8N-HOST
)
for ph in "${REQ[@]}"; do
  if grep -rq -- "$ph" workflows/ 2>/dev/null; then
    echo "  OK — $ph ditemukan"
  else
    report "Placeholder hilang: $ph"
  fi
done
echo

# --- Kesimpulan ---
echo "======================================================"
if [ "$FOUND" -eq 0 ]; then
  echo "LULUS — tidak ada data sensitif ditemukan."
  exit 0
else
  echo "GAGAL — bersihkan temuan di atas sebelum commit."
  exit 1
fi
