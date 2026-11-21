#!/usr/bin/env python3
"""Uji akses HTML publik SINTA dari GitHub Actions, tanpa login/proxy/captcha.

Tidak mengambil data pribadi atau menyiasati pembatasan akses situs.
"""
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from html.parser import HTMLParser
from datetime import datetime, timezone

SINTA_ID = "6054939"  # Uji satu dosen: Muhammad Dedi Irawan
URL = f"https://sinta.kemdiktisaintek.go.id/authors/profile/{SINTA_ID}"
OUT = Path("hasil/diagnostik_sinta.json")


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignore = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.ignore += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.ignore:
            self.ignore -= 1

    def handle_data(self, data):
        if not self.ignore:
            self.parts.append(data)


result = {
    "sinta_id": SINTA_ID,
    "profile_url": URL,
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "http_status": None,
    "access_ok": False,
    "author_found": False,
    "scopus_section_found": False,
    "html_bytes": 0,
    "note": "Belum diuji",
}

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; SainsData-UINSU-Public-Research-Check/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.7",
}
try:
    req = Request(URL, headers=headers)
    with urlopen(req, timeout=25) as response:
        result["http_status"] = response.status
        body = response.read(3_000_000)
    result["html_bytes"] = len(body)
    parser = TextOnly()
    parser.feed(body.decode("utf-8", errors="replace"))
    text = " ".join(" ".join(parser.parts).split())
    result["author_found"] = "MUHAMMAD DEDI IRAWAN" in text.upper()
    result["scopus_section_found"] = "SCOPUS" in text.upper()
    result["access_ok"] = result["http_status"] == 200 and result["author_found"]
    result["note"] = ("Halaman publik SINTA bisa dibaca dari GitHub; dapat lanjut uji parser publikasi."
                      if result["access_ok"] else
                      "HTTP berhasil tetapi nama peneliti tidak ditemukan; mungkin halaman proteksi atau perubahan HTML.")
except HTTPError as exc:
    result["http_status"] = exc.code
    result["note"] = "SINTA menolak akses otomatis (HTTP %s). Jangan mencoba menghindari pembatasan." % exc.code
except (URLError, TimeoutError, OSError) as exc:
    result["note"] = "Koneksi gagal: " + str(exc)[:200]

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
