#!/usr/bin/env python3
"""Audit bulanan 52 profil jurnal SINTA yang ada dalam katalog publikasi GARUDA.

Hanya meminta halaman publik resmi SINTA. HTTP 403/429 langsung dihentikan.
Tidak melewati captcha/login, tidak menggunakan proxy, dan tidak mengubah
peringkat jurnal atau peringkat artikel tanpa bukti yang dapat diverifikasi.
"""
import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "data" / "katalog_jurnal_sinta.json"
OUTPUT = ROOT / "hasil" / "status_pemeriksaan_sinta.json"
WAIT_SECONDS = 1.3
TIMEOUT_SECONDS = 17


def normalize(value):
    x = unicodedata.normalize("NFKD", str(value or "").casefold())
    x = "".join(ch for ch in x if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", x).strip()


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignore = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.ignore += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.ignore:
            self.ignore -= 1

    def handle_data(self, value):
        if not self.ignore:
            self.parts.append(value)

    def text(self):
        return " ".join(" ".join(self.parts).split())


def check_one(entry):
    url = str(entry.get("sinta_url") or "")
    host = urlparse(url)
    if (host.scheme != "https" or host.hostname != "sinta.kemdiktisaintek.go.id"
            or not re.fullmatch(r"/journals/profile/\d+", host.path)):
        return {"status": "url_tidak_sah", "http_status": None}
    req = Request(url, headers={
        "User-Agent": "SainsData-Public-SINTA-Audit/1.0",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "id-ID,id;q=0.9",
    })
    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200 or "html" not in response.headers.get("Content-Type", "").lower():
                return {"status": "respons_tidak_valid", "http_status": response.status}
            raw = response.read(500_001)
            if len(raw) > 500_000:
                return {"status": "respons_terlalu_besar", "http_status": 200}
            body = raw.decode("utf-8", "replace")
    except HTTPError as error:
        return {"status": "akses_dibatasi" if error.code in (403,429) else "http_error",
                "http_status": error.code}
    except (URLError, TimeoutError, OSError):
        return {"status": "koneksi_gagal", "http_status": None}

    p = TextExtractor()
    p.feed(body)
    text = p.text()
    # Conservative: name must be explicitly present in the public page.
    title = normalize(entry.get("nama_sinta") or entry.get("nama_garuda"))
    normalized = normalize(text)
    pos = normalized.find(title)
    if pos < 0:
        return {"status": "nama_jurnal_tidak_cocok", "http_status": 200}
    # May not infer ranking if the same page displays related journals.
    window = normalized[max(0, pos-150):pos+450]
    ranks = sorted(set(int(m.group(1)) for m in re.finditer(r"\bsinta\s+([1-6])\b", window)))
    if len(ranks) != 1:
        return {"status": "peringkat_perlu_pemeriksaan_manual", "http_status": 200,
                "peringkat_kandidat": ranks}
    observed = ranks[0]
    recorded = entry.get("peringkat_terkini_diamati")
    return {
        "status": "indikasi_sesuai" if observed == recorded else "indikasi_berubah_perlu_verifikasi",
        "http_status": 200, "peringkat_kandidat": observed,
    }


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    journals = catalog.get("jurnal") or []
    if not isinstance(journals, list) or not journals:
        raise ValueError("Katalog jurnal kosong atau invalid")
    entries = []
    blocked = False
    for index, journal in enumerate(journals):
        item = {
            "nama": journal.get("nama_garuda"),
            "profil_sinta": journal.get("sinta_url"),
            "peringkat_tercatat": journal.get("peringkat_terkini_diamati"),
        }
        if blocked:
            item["status"] = "tidak_diperiksa_karena_pembatasan"
            item["http_status"] = None
        else:
            if index:
                time.sleep(WAIT_SECONDS)
            check = check_one(journal)
            item.update(check)
            if check.get("http_status") in (403,429):
                blocked = True
        entries.append(item)
        print(str(item["nama"]) + ": " + str(item["status"]), flush=True)
    counts = {status:sum(1 for x in entries if x["status"] == status)
              for status in sorted(set(x["status"] for x in entries))}
    output = {
        "versi": 1,
        "diperiksa_utc": datetime.now(timezone.utc).isoformat(),
        "sumber": "Profil jurnal SINTA publik (tanpa autentikasi)",
        "jumlah_katalog": len(journals),
        "jumlah_permintaan": sum(1 for x in entries if x["status"] != "tidak_diperiksa_karena_pembatasan"),
        "akses_dibatasi": blocked,
        "rekap_status": counts,
        "jurnal": entries,
        "catatan": "Peringkat kandidat bukan peringkat terverifikasi tanpa konfirmasi identitas dan bukti akreditasi. Kode tidak mengubah peringkat jurnal saat akses gagal atau tidak meyakinkan.",
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Audit bulanan selesai, tidak ada label SINTA yang ditebak:", json.dumps(counts,ensure_ascii=False))


if __name__ == "__main__":
    main()
