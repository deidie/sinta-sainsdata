#!/usr/bin/env python3
"""Buat indeks kecil label SINTA/Scopus bagi halaman Scholar WordPress."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "hasil" / "publikasi_dosen.json"
DEST = ROOT / "hasil" / "label_publikasi.json"


def norm_title(text):
    s = unicodedata.normalize("NFKD", str(text or "")).casefold()
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def web_url(value):
    if not isinstance(value, str):
        return None
    try:
        url = urlsplit(value)
        return value if url.scheme == "https" and url.hostname else None
    except ValueError:
        return None


def year(value):
    try:
        result = int(value)
        return result if 1900 <= result <= 2100 else None
    except (TypeError, ValueError):
        return None


def sinta_rank(value):
    try:
        n = int(value)
        return n if str(value).strip() == str(n) and 1 <= n <= 6 else None
    except (TypeError, ValueError):
        return None


def build(data):
    by_person = {}
    count = 0
    for person in data.get("dosen", []):
        slug = str(person.get("slug", "")).strip()
        if not re.fullmatch(r"[a-z0-9_-]+", slug):
            continue
        records = []
        used = set()
        for article in person.get("publikasi_garuda", []):
            title = norm_title(article.get("judul"))
            publication_year = year(article.get("tahun"))
            if not title or not publication_year:
                continue

            srank = sinta_rank(article.get("peringkat_sinta"))
            sproof = web_url(article.get("sinta_bukti_url"))
            if not sproof:
                srank = None

            sc_verified = (
                article.get("status_indeks_scopus") == "terindeks"
                and article.get("scopus_status_verifikasi") == "terindeks_terverifikasi"
            )
            sc_proof = web_url(article.get("scopus_bukti_url") or article.get("scopus_url")) if sc_verified else None
            sc_verified = bool(sc_proof)

            q = str(article.get("scopus_quartile") or article.get("quartile_scopus") or "").strip().upper()
            q_proof = web_url(article.get("scopus_quartile_bukti_url") or article.get("quartile_bukti_url"))
            if not (sc_verified and re.fullmatch(r"Q[1-4]", q) and q_proof):
                q, q_proof = None, None

            if not srank and not sc_verified:
                continue
            key = (title, publication_year)
            if key in used:
                continue
            used.add(key)
            label = {"judul_key": title, "tahun": publication_year}
            if srank:
                label.update(sinta=srank, sinta_bukti=sproof)
            if sc_verified:
                label.update(scopus=True, scopus_bukti=sc_proof)
            if q:
                label.update(quartile=q, quartile_bukti=q_proof)
            records.append(label)
            count += 1
        by_person[slug] = records
    return {
        "versi": 1,
        "diperbarui_utc": data.get("sinta_pencocokan_utc") or data.get("diperbarui_utc"),
        "sumber": "Bukti indeksasi pada publikasi_dosen.json",
        "dosen": by_person,
        "jumlah_label_terverifikasi": count,
        "catatan": "Penanda hanya dari bukti; quartile Q1-Q4 membutuhkan sumber kuartil tersendiri."
    }


def main():
    source = json.loads(DATA.read_text(encoding="utf-8"))
    index = build(source)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("Indeks label:", index["jumlah_label_terverifikasi"], "artikel berlabel;", DEST.stat().st_size, "byte")


if __name__ == "__main__":
    main()
