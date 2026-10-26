#!/usr/bin/env python3
"""Verifikasi repo carousel: link internal, anchor, JSON workflow, placeholder."""
import json
import re
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
errors = []
warnings = []


def check_links():
    """Cek setiap link relatif .md menunjuk ke file yang benar-benar ada."""
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for md in ROOT.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for label, target in link_re.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part = target.split("#")[0]
            if not path_part:
                continue
            dest = (md.parent / path_part).resolve()
            if not dest.exists():
                errors.append(f"{md.relative_to(ROOT)}: link rusak -> {target} ({label})")


def check_anchors():
    """Cek anchor internal (#...) ada di heading file target."""
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]*#[^)]+)\)")
    slug_cache = {}

    def slugs(path):
        if path in slug_cache:
            return slug_cache[path]
        out = set()
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^#{1,6}\s+(.*)$", line)
                if m:
                    h = m.group(1).strip().lower()
                    h = re.sub(r"[`*_]", "", h)
                    h = re.sub(r"[^\w\s-]", "", h)   # buang em dash, titik, dll
                    h = re.sub(r"\s", "-", h)        # tiap spasi jadi satu hyphen
                    out.add(h)
        slug_cache[path] = out
        return out

    for md in ROOT.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for label, target in link_re.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            path_part, _, anchor = target.partition("#")
            dest = (md.parent / path_part).resolve() if path_part else md
            if anchor and anchor not in slugs(dest):
                warnings.append(
                    f"{md.relative_to(ROOT)}: anchor mungkin tidak ada -> #{anchor}")


def check_workflows():
    for f in sorted((ROOT / "workflows").glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{f.name}: JSON tidak valid — {e}")
            continue
        nodes = d.get("nodes", [])
        conns = d.get("connections", {})
        names = {n["name"] for n in nodes}
        if not nodes:
            errors.append(f"{f.name}: tidak ada node")
        # setiap target koneksi harus ada
        for src, v in conns.items():
            if src not in names:
                errors.append(f"{f.name}: sumber koneksi tidak ada — {src}")
            for out in v.get("main", []) or []:
                for c in out or []:
                    if c["node"] not in names:
                        errors.append(f"{f.name}: target koneksi tidak ada — {c['node']}")
        # node wajib punya type & position
        for n in nodes:
            for k in ("name", "type", "typeVersion", "position"):
                if k not in n:
                    errors.append(f"{f.name}: node '{n.get('name','?')}' tanpa '{k}'")
        # credential id wajib sudah hilang
        for n in nodes:
            if n.get("credentials"):
                errors.append(
                    f"{f.name}: blok credentials belum dihapus di '{n['name']}'")
        # nama dokumen spreadsheet tidak boleh membocorkan nama asli
        for n in nodes:
            doc = n.get("parameters", {}).get("documentId")
            if isinstance(doc, dict) and doc.get("cachedResultName"):
                errors.append(
                    f"{f.name}: cachedResultName membocorkan nama sheet di '{n['name']}'")
        print(f"  {f.name}: {len(nodes)} node, {len(conns)} koneksi, OK")
    return {f.name: json.loads(f.read_text(encoding="utf-8"))
            for f in sorted((ROOT / "workflows").glob("*.json"))}


def check_placeholders(workflows):
    required = [
        "REPLACE_WITH_CAROUSEL_SHEET_ID",
        "REPLACE_WITH_ARCHIVE_SHEET_ID",
        "REPLACE_WITH_TELEGRAM_ADMIN_CHAT_ID",
        "REPLACE_WITH_IMGBB_API_KEY",
        "REPLACE_WITH_ZERNIO_API_KEY",
        "REPLACE_WITH_COMPOSIO_ACCOUNT_ID",
        "REPLACE_WITH_IG_USER_ID",
        "REPLACE_WITH_IG_USERNAME",
        "REPLACE_WITH_IG_USERNAME_2",
        "YOUR-N8N-HOST",
    ]
    blob = "".join(json.dumps(d, ensure_ascii=False) for d in workflows.values())
    for ph in required:
        n = blob.count(ph)
        print(f"  {ph}: {n} kemunculan")
        if n == 0:
            errors.append(f"placeholder hilang: {ph}")


def check_sheet_headers():
    """Header CSV harus 42 kolom dan cocok dengan docs/03."""
    import csv
    f = ROOT / "examples" / "carousel-sheet-template.csv"
    if not f.exists():
        errors.append("examples/carousel-sheet-template.csv tidak ada")
        return
    with f.open(encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    header = rows[0]
    print(f"  template header: {len(header)} kolom, {len(rows)} baris")
    if len(header) != 42:
        errors.append(f"header CSV {len(header)} kolom, seharusnya 42")
    # kolom wajib yang dibaca node
    wajib = ["id", "status", "topic", "cover_title", "cover_subtitle", "tags",
             "caption", "scheduled_at", "instagram_post_id", "published_at",
             "image_urls", "watermark"]
    for w in wajib:
        if w not in header:
            errors.append(f"header CSV tanpa kolom wajib: {w}")
    for i in range(1, 11):
        for suf in ("title", "body", "highlight"):
            c = f"slide_{i:02d}_{suf}"
            if c not in header:
                errors.append(f"header CSV tanpa kolom: {c}")
    # dokumen harus menyebut 42 kolom
    doc = (ROOT / "docs" / "03-google-sheets.md").read_text(encoding="utf-8")
    if "42 kolom" not in doc:
        warnings.append("docs/03 tidak menyebut jumlah kolom 42")
    # setiap baris punya jumlah kolom sama
    for idx, r in enumerate(rows[1:], start=2):
        if r and len(r) not in (0, len(header)):
            errors.append(f"CSV baris {idx}: {len(r)} kolom, seharusnya {len(header)}")


def check_docs_exist():
    expected = ["README.md", "LICENSE", "CONTRIBUTING.md", "CHANGELOG.md",
                ".gitignore", "examples/.env.example",
                "examples/carousel-sheet-template.csv",
                "scripts/check-secrets.sh", "scripts/verify-repo.py"]
    expected += [f"docs/{n}" for n in sorted(p.name for p in (ROOT / "docs").glob("*.md"))]
    for e in expected:
        if not (ROOT / e).exists():
            errors.append(f"file tidak ada: {e}")
    # README harus merujuk setiap dokumen
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for p in sorted((ROOT / "docs").glob("*.md")):
        if f"docs/{p.name}" not in readme:
            errors.append(f"README tidak merujuk {p.name}")


def main():
    print("== Struktur ==")
    check_docs_exist()
    print("  selesai")
    print("\n== Link internal ==")
    check_links()
    check_anchors()
    print("  selesai")
    print("\n== Workflow JSON ==")
    wfs = check_workflows()
    print("\n== Placeholder ==")
    check_placeholders(wfs)
    print("\n== Google Sheets template ==")
    check_sheet_headers()

    print("\n" + "=" * 56)
    if warnings:
        print(f"PERINGATAN ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print(f"ERROR ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("SEMUA PEMERIKSAAN LULUS")


if __name__ == "__main__":
    main()
