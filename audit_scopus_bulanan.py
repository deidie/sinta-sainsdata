#!/usr/bin/env python3
"""Audit Scopus artikel GARUDA via Elsevier Scopus Search API.

Tidak memerlukan API key untuk membuat status diagnostik. Bila secret
SCOPUS_API_KEY tersedia, jalankan verifikasi DOI yang sudah diimplementasikan
pada cek_sinta.scopus_main(). Tanpa key, jangan mengubah rekap/label Scopus.
Jangan sebut 'tidak terindeks' berdasarkan tidak ada hasil/akses.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import cek_sinta

ROOT = Path(__file__).resolve().parent
DIR = ROOT / "hasil"
SOURCE = DIR / "publikasi_dosen.json"
STATUS = DIR / "status_pemeriksaan_scopus.json"
RECAP = DIR / "rekap_scopus.json"
DIAG = DIR / "diagnostik_scopus.json"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def count_source():
    data = read_json(SOURCE)
    authors = data.get("dosen") or []
    if len(authors) != 6:
        raise ValueError("Enam profil dosen tidak ditemukan")
    papers = [a for d in authors for a in (d.get("publikasi_garuda") or [])]
    valid_doi = set()
    counts = {}
    for d in authors:
        items = d.get("publikasi_garuda") or []
        n = 0
        for a in items:
            doi = cek_sinta.scopus_doi_key(a.get("doi"))
            if doi:
                valid_doi.add(doi)
                n += 1
        counts[d["slug"]] = {"rekaman_garuda": len(items), "punya_doi": n}
    return len(papers), len(valid_doi), counts


def main():
    total, unique_doi, authors = count_source()
    key = bool(os.getenv("SCOPUS_API_KEY", "").strip())
    result = {
        "versi": 1,
        "diperiksa_utc": datetime.now(timezone.utc).isoformat(),
        "sumber": "Elsevier Scopus Search API, pencocokan DOI dan EID",
        "api_key_tersedia": key,
        "total_rekaman_garuda_per_dosen": total,
        "jumlah_doi_unik_untuk_diperiksa": unique_doi,
        "dosen": authors,
        "status": "belum_dikonfigurasi" if not key else "pemeriksaan_dijalankan",
        "peringatan": "Tanpa verifikasi Scopus, rekaman tidak boleh diberi label 'tidak terindeks'. Pencocokan hanya untuk artikel yang sudah terdapat di GARUDA.",
    }
    if key:
        code = cek_sinta.scopus_main()
        if code not in (0, None):
            raise RuntimeError("Verifikasi Scopus gagal")
        recap = read_json(RECAP)
        diag = read_json(DIAG)
        if int(recap["total_rekaman"]) != total:
            raise ValueError("Jumlah GARUDA berubah selama audit Scopus")
        result.update({
            "status": "akses_terbatas" if diag.get("api_diblokir") else (
                "tidak_ada_permintaan" if int(diag.get("permintaan_api") or 0) == 0 else "sukses_terbatas_kuota"
            ),
            "permintaan_api": int(diag.get("permintaan_api") or 0),
            "api_diblokir": bool(diag.get("api_diblokir")),
            "rekaman_scopus_terverifikasi": int(recap.get("artikel_scopus_terverifikasi") or 0),
            "peristiwa": [str(s)[:160] for s in (diag.get("peristiwa") or [])],
        })
    else:
        # Never manufacture a false zero when authorization is missing.
        result.update({
            "permintaan_api": 0,
            "api_diblokir": None,
            "rekaman_scopus_terverifikasi": None,
            "tindakan": "Konfigurasikan GitHub Secret SCOPUS_API_KEY dengan kunci yang memiliki akses Elsevier Scopus API.",
        })
    STATUS.parent.mkdir(exist_ok=True)
    STATUS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "rekaman_garuda": total,
        "doi_unik": unique_doi,
        "scopus_terverifikasi": result["rekaman_scopus_terverifikasi"],
        "request": result["permintaan_api"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Gagal audit Scopus:", type(exc).__name__, str(exc)[:150], file=sys.stderr)
        sys.exit(1)
