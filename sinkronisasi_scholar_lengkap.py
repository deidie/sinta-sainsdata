#!/usr/bin/env python3
"""Sinkronisasi Google Scholar lengkap langsung dari SerpApi.

Menggunakan API key dari environment (GitHub Actions secret SERPAPI_KEY).
Profil dan author ID memakai tautan Scholar yang sudah diverifikasi di
hasil/publikasi_scholar.json. Data GARUDA tidak disentuh.

Setiap permintaan mengambil sampai 100 artikel dan dipaginasi sampai selesai.
Jika ada kesalahan, hasil lama tidak ditimpa dan workflow gagal secara eksplisit.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

OUTPUT = Path(__file__).resolve().parent / "hasil" / "publikasi_scholar.json"
SLUGS = ("siddik", "dedi", "rakhmat", "aidil", "ika", "puji")
PER_PAGE = 100
MAX_PAGES_PER_AUTHOR = 20
TIMEOUT_SECONDS = 35


def number(value):
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        f = float(str(value).replace(",", "").strip())
        return int(f) if f.is_integer() and 0 <= f <= 10**10 else None
    except (TypeError, ValueError, OverflowError):
        return None


def https_url(value):
    if not isinstance(value, str):
        return ""
    parsed = urlparse(value.strip())
    return value.strip() if parsed.scheme == "https" and parsed.hostname else ""


def scholar_id_from_url(link):
    parsed = urlparse(link)
    if parsed.scheme != "https" or parsed.hostname != "scholar.google.com":
        raise ValueError("Tautan Google Scholar tidak sah")
    user = parse_qs(parsed.query).get("user", [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,32}", user):
        raise ValueError("Scholar author ID tidak valid")
    return user


def normalize_title(title):
    text = unicodedata.normalize("NFKC", str(title or "")).casefold()
    return re.sub(r"\s+", " ", text).strip()


def get_serpapi(author_id, start, key):
    params = {
        "engine": "google_scholar_author",
        "author_id": author_id,
        "hl": "id",
        "sort": "pubdate",
        "num": PER_PAGE,
        "start": start,
        "api_key": key,
    }
    uri = "https://serpapi.com/search.json?" + urlencode(params)
    req = Request(uri, headers={"Accept": "application/json", "User-Agent": "SainsDataScholarSync/2"})
    # Do not print the request URI: it contains the private API key.
    for attempt in range(2):
        try:
            with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
                if response.status != 200:
                    raise RuntimeError("SerpApi HTTP " + str(response.status))
                raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise RuntimeError("SerpApi response terlalu besar")
            data = json.loads(raw.decode("utf-8-sig"))
            if not isinstance(data, dict):
                raise RuntimeError("Format respons SerpApi tidak sesuai")
            if data.get("error"):
                # Never print API key or sensitive request URL.
                raise RuntimeError("SerpApi: " + str(data["error"])[:180])
            return data
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == 0 and (not isinstance(exc, HTTPError) or exc.code in (429, 500, 502, 503, 504)):
                time.sleep(3)
                continue
            code = getattr(exc, "code", "")
            raise RuntimeError("Permintaan SerpApi gagal (HTTP " + str(code) + ")") from exc


def extract_metrics(data):
    table = ((data.get("cited_by") or {}).get("table") or [])
    if not isinstance(table, list) or not table:
        raise RuntimeError("Statistik profil Scholar tidak tersedia")
    def find(*keys):
        for row in table:
            if isinstance(row, dict):
                for k in keys:
                    if isinstance(row.get(k), dict):
                        return number(row[k].get("all"))
        return None
    metrics = {
        "sitasi": find("citations", "kutipan"),
        "h_index": find("h_index", "indeks_h"),
        "i10_index": find("i10_index", "indeks_i10"),
    }
    if all(v is None for v in metrics.values()):
        raise RuntimeError("Statistik Scholar tidak dapat dibaca")
    graph = {}
    for item in (data.get("cited_by") or {}).get("graph") or []:
        if not isinstance(item, dict):
            continue
        y, c = number(item.get("year")), number(item.get("citations"))
        if y is not None and 1900 <= y <= 2100 and c is not None:
            graph[str(y)] = c
    return metrics, graph


def convert_article(article):
    if not isinstance(article, dict):
        return None
    title = str(article.get("title") or "").strip()
    if not title:
        return None
    year = number(article.get("year"))
    if year is not None and not (1900 <= year <= 2100):
        year = None
    cited_by = article.get("cited_by") or {}
    return {
        "judul": title,
        "tahun": year,
        "jurnal": str(article.get("publication") or ""),
        "penulis": str(article.get("authors") or ""),
        "url": https_url(article.get("link")),
        "sitasi": number(cited_by.get("value")) if isinstance(cited_by, dict) else None,
    }


def refresh_author(previous, api_key):
    author_id = scholar_id_from_url(previous.get("scholar_url") or "")
    papers = []
    seen = set()
    metrics = graph = None
    complete = False
    for page in range(MAX_PAGES_PER_AUTHOR):
        data = get_serpapi(author_id, page * PER_PAGE, api_key)
        if page == 0:
            metrics, graph = extract_metrics(data)
        items = data.get("articles") or []
        if not isinstance(items, list):
            raise RuntimeError("Daftar artikel tidak valid")
        for item in items:
            paper = convert_article(item)
            if paper is None:
                continue
            # Citation ID preferred, otherwise title+year; paper without year is retained.
            cid = str(item.get("citation_id") or "").strip()
            identity = ("id:" + cid) if cid else ("t:" + normalize_title(paper["judul"]) + "|" + str(paper["tahun"]))
            if identity not in seen:
                seen.add(identity)
                papers.append(paper)
        if len(items) < PER_PAGE:
            complete = True
            break
        if page + 1 < MAX_PAGES_PER_AUTHOR:
            time.sleep(0.4)
    if not complete:
        raise RuntimeError("Lebih dari " + str(PER_PAGE * MAX_PAGES_PER_AUTHOR) + " artikel; data tidak dianggap lengkap")
    if not papers:
        raise RuntimeError("Daftar artikel kosong")
    old_count = len(previous.get("artikel_scholar") or [])
    if len(papers) < old_count:
        raise RuntimeError("Jumlah artikel baru lebih kecil dari snapshot lama (" +
                           str(len(papers)) + " < " + str(old_count) + "); data lama dipertahankan")
    result = dict(previous)
    result["artikel_scholar"] = papers
    result["jumlah_artikel_scholar"] = len(papers)
    result["metrik_scholar"] = metrics
    result["sitasi_tahunan"] = graph
    result["scholar_diperbarui"] = datetime.now(timezone.utc).isoformat()
    result["scholar_status"] = "Berhasil (seluruh halaman SerpApi)"
    result["scholar_lengkap"] = True
    return result


def build_snapshot(current, api_key):
    prior = {p.get("slug"): p for p in current.get("dosen") or []
             if isinstance(p, dict) and p.get("slug") in SLUGS}
    if set(prior) != set(SLUGS):
        raise RuntimeError("Konfigurasi profil tidak lengkap; tidak memperbarui data")
    people = []
    for slug in SLUGS:
        row = refresh_author(prior[slug], api_key)
        print(slug + ": " + str(row["jumlah_artikel_scholar"]) + " artikel Scholar")
        people.append(row)
    return {
        "versi": 3,
        "diperbarui_utc": datetime.now(timezone.utc).isoformat(),
        "sumber": "SerpApi Google Scholar Author API (pagination lengkap)",
        "cakupan_dosen": len(people),
        "cakupan_lengkap": True,
        "catatan": "Jumlah artikel Scholar per profil; sitasi profil tidak dideduplikasi antarpenulis. Tahun tanpa metadata tetap disimpan.",
        "dosen": people,
    }


def main():
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GitHub Actions secret SERPAPI_KEY belum tersedia")
    current = json.loads(OUTPUT.read_text(encoding="utf-8"))
    snapshot = build_snapshot(current, api_key)
    # Atomic replace only after all author profiles have completed successfully.
    staged = OUTPUT.with_suffix(".json.new")
    staged.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    staged.replace(OUTPUT)
    print("Berhasil menyimpan publikasi Scholar lengkap, total profil:", len(snapshot["dosen"]))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("GAGAL sinkronisasi penuh: " + str(exc), file=sys.stderr)
        sys.exit(1)
