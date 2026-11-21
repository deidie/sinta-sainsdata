#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Perkaya artikel GARUDA dengan peringkat jurnal SINTA yang teramati.

Sumber:
  data/katalog_jurnal_sinta.json = nama jurnal & peringkat JURNAL saat teramati;
  data/bukti_artikel_sinta.json = peringkat ARTIKEL, hanya dari DOI yang
    secara eksplisit ditampilkan di SINTA beserta bukti URL.
  hasil/publikasi_dosen.json = artikel GARUDA yang sudah dikumpulkan.

Tidak menebak akreditasi artikel dari peringkat jurnal terkini.
Tidak menghapus artikel GARUDA, tidak memanggil SINTA/Scholar/Scopus, dan
tidak mencoba mengatasi HTTP 403.
"""
from __future__ import annotations
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "hasil"
CATALOG = ROOT / "data" / "katalog_jurnal_sinta.json"
PROOF = ROOT / "data" / "bukti_artikel_sinta.json"
PUBLICATIONS = RESULTS / "publikasi_dosen.json"
RECAP = RESULTS / "rekap_sinta.json"
DIAGNOSTIC = RESULTS / "diagnostik_pencocokan_sinta.json"
JOURNAL_RECAP = RESULTS / "katalog_pencocokan_sinta.json"
CSV_ARTICLES = RESULTS / "publikasi_dosen.csv"
CSV_RECAP = RESULTS / "rekap_sinta.csv"
NOW = datetime.now(timezone.utc).isoformat()


def norm(text):
    s = unicodedata.normalize("NFKD", str(text or "").casefold())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def journal_title(value):
    """Hilangkan informasi volume/edisi dari label jurnal GARUDA."""
    s = " ".join(str(value or "").split())
    s = re.split(r"\b(?:vol(?:ume)?\.?\s*\d+)", s, maxsplit=1, flags=re.I)[0]
    s = re.split(r"\b(?:No\.?|Nomor|Issue)\s*\d+\b", s, maxsplit=1, flags=re.I)[0]
    return s.strip(" ,:;-")


def doi_key(value):
    x = str(value or "").lower().strip()
    x = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", x)
    return x.strip(" \t\n\"'<>,;)") if re.match(r"^10\.\d{4,9}/\S+", x) else ""


def url_is_sinta(url):
    try:
        u = urlparse(url)
        return u.scheme == "https" and u.hostname == "sinta.kemdiktisaintek.go.id" and bool(u.path)
    except (ValueError, TypeError):
        return False


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_catalog(raw):
    index = defaultdict(list)
    for item in raw.get("jurnal", []):
        rank = item.get("peringkat_terkini_diamati")
        uri = item.get("sinta_url") or ""
        title = item.get("nama_garuda") or ""
        assert type(rank) is int and 1 <= rank <= 6, "Peringkat katalog harus S1-S6"
        assert re.fullmatch(r"https://sinta\.kemdiktisaintek\.go\.id/journals/profile/\d+", uri), "URL profil SINTA tidak valid"
        assert norm(title), "Nama jurnal kosong"
        for name in [title] + (item.get("alias_garuda") or []):
            key = norm(name)
            if key:
                index[key].append(item)
    # Duplikat nama yang memetakan beberapa ID SINTA otomatis dianggap ambigu.
    return index


def validate_proofs(raw):
    result = {}
    for item in raw.get("artikel", []):
        doi, rank, uri = doi_key(item.get("doi")), item.get("peringkat"), item.get("bukti_url")
        assert doi and type(rank) is int and 1 <= rank <= 6 and url_is_sinta(uri), "Bukti DOI tidak sah"
        if doi in result and result[doi]["peringkat"] != rank:
            raise ValueError("Konflik peringkat untuk DOI " + doi)
        result[doi] = item
    return result


def match_journal(article, index):
    name = journal_title(article.get("jurnal"))
    key = norm(name)
    possible = index.get(key, [])
    if not possible:
        return None, "nama_belum_ditemukan"
    accepted = []
    doi = doi_key(article.get("doi"))
    link = urlparse(str(article.get("url_artikel") or ""))
    for item in possible:
        prefixes = [x.lower().strip() for x in (item.get("doi_prefix_harus_cocok") or [])]
        domain = str(item.get("penerbit_domain") or "").strip().lower()
        if prefixes and not any(doi.startswith(prefix) for prefix in prefixes):
            continue
        if domain and link.hostname and link.hostname != domain:
            continue
        accepted.append(item)
    ids = {str(c["sinta_url"]) for c in accepted}
    if not accepted:
        return None, "nama_ambigu_butuh_doi_penerbit" if possible else "nama_belum_ditemukan"
    if len(ids) != 1:
        return None, "beberapa_profil_sinta_mirip"
    return accepted[0], "profil_sinta_resmi_terindeks"


def enrich(data, catalog, proof):
    index = validate_catalog(catalog)
    verified = validate_proofs(proof)
    people = data.get("dosen") or []
    if not isinstance(people, list) or len(people) != 6:
        raise ValueError("Daftar enam dosen tidak valid")
    journal_hit = 0
    article_hit = 0
    reasons = Counter()
    found_journals = {}
    missing = Counter()
    totals = defaultdict(Counter)
    per_person = []
    for p in people:
        byyear = defaultdict(Counter)
        rankcounts = Counter()
        papers = p.get("publikasi_garuda") or []
        if not isinstance(papers, list) or not papers:
            raise ValueError("Salah satu profil dosen tidak memiliki publikasi")
        for art in papers:
            item, status = match_journal(art, index)
            journalname = journal_title(art.get("jurnal"))
            if item:
                journal_hit += 1
                art["jurnal_sinta_peringkat_terkini"] = item["peringkat_terkini_diamati"]
                art["jurnal_sinta_url"] = item["sinta_url"]
                art["jurnal_sinta_status_verifikasi"] = "profil_jurnal_resmi_terindeks"
                art["jurnal_sinta_diperiksa"] = item.get("ditinjau_tanggal")
                found_journals[norm(journalname)] = {
                    "nama_garuda": journalname,
                    "nama_sinta": item.get("nama_sinta"),
                    "peringkat_jurnal_terkini": item["peringkat_terkini_diamati"],
                    "sinta_url": item["sinta_url"],
                }
            else:
                # Pertahankan rank terkini yang sudah memiliki bukti resmi sebelumnya.
                if not (type(art.get("jurnal_sinta_peringkat_terkini")) is int and url_is_sinta(art.get("jurnal_sinta_url"))):
                    art["jurnal_sinta_peringkat_terkini"] = None
                    art["jurnal_sinta_url"] = None
                art["jurnal_sinta_status_verifikasi"] = status
                missing[journalname] += 1
            reasons[status] += 1

            doi = doi_key(art.get("doi"))
            source = verified.get(doi)
            if source:
                art["peringkat_sinta"] = source["peringkat"]
                art["sinta_status_verifikasi"] = "doi_spesifik_pada_sinta"
                art["sinta_bukti_url"] = source["bukti_url"]
                article_hit += 1
            else:
                # Tidak boleh menurunkan label SINTA artikel dari peringkat jurnal sekarang.
                existingrank = art.get("peringkat_sinta")
                evidence = art.get("sinta_bukti_url")
                if not (type(existingrank) is int and existingrank in range(1, 7) and
                        evidence and str(evidence).startswith("https://")):
                    art["peringkat_sinta"] = None
                    art["sinta_bukti_url"] = None
                    art["sinta_status_verifikasi"] = "belum_terverifikasi"

            label = "S" + str(art["peringkat_sinta"]) if art.get("peringkat_sinta") in range(1, 7) else "belum_terverifikasi"
            rankcounts[label] += 1
            yy = art.get("tahun")
            if yy is not None and str(yy).isdigit() and 1900 <= int(yy) <= 2100:
                byyear[str(yy)][label] += 1
                totals[str(yy)][label] += 1

        p["rekap_sinta"] = {**{"S" + str(i):rankcounts["S" + str(i)] for i in range(1,7)},
                            "belum_terverifikasi":rankcounts["belum_terverifikasi"]}
        per_person.append({
            "slug":p["slug"],"nama":p["nama"],"total":len(papers),
            "peringkat":p["rekap_sinta"],
            "per_tahun":{year:dict(value) for year,value in sorted(byyear.items(), reverse=True)}
        })
    data["sinta_pencocokan_utc"] = NOW
    data["sinta_metode"] = "Peringkat terkini jurnal dari katalog profil SINTA resmi; akreditasi artikel hanya dari bukti DOI spesifik atau SK historis terverifikasi"
    data["catatan_sinta"] = "Peringkat jurnal terkini berbeda dari peringkat saat artikel terbit; tanda belum terverifikasi bukan berarti jurnal tidak terakreditasi."
    recap = {
        "diperbarui_utc":NOW,
        "total_rekaman":sum(len(d["publikasi_garuda"]) for d in people),
        "artikel_sinta_terverifikasi":sum(sum(d["rekap_sinta"]["S" + str(i)] for i in range(1,7)) for d in people),
        "artikel_belum_terverifikasi":sum(d["rekap_sinta"]["belum_terverifikasi"] for d in people),
        "artikel_dengan_peringkat_jurnal_terkini":journal_hit,
        "dosen":per_person,"rekap_tahunan":{year:dict(value) for year,value in sorted(totals.items(), reverse=True)},
        "catatan":"Per dosen memuat publikasi kolaborasi pada tiap profil, sehingga tidak sama dengan jumlah publikasi unik lintas dosen."
    }
    diagnostic = {
        "waktu":NOW,"nama_jurnal_dalam_katalog":len(catalog["jurnal"]),
        "jurnal_unik_tercocokkan":len(found_journals),
        "rekaman_dengan_rank_jurnal_teramati":journal_hit,
        "rekaman_dengan_rank_artikel_terverifikasi":recap["artikel_sinta_terverifikasi"],
        "rekaman_tanpa_rank_jurnal":sum(missing.values()),
        "alasan":dict(reasons),
        "jurnal_belum_tercocokkan":[{"nama":k,"rekaman":v} for k,v in missing.most_common()],
        "catatan":"Jurnal peringkat terkini tidak identik dengan status akreditasi pada tahun artikel."
    }
    journal_recap = {"diperbarui_utc":NOW,"jurnal":list(sorted(found_journals.values(),key=lambda x:x["nama_garuda"].casefold())),"jurnal_tercocokkan":len(found_journals)}
    return data, recap, diagnostic, journal_recap


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def write_csv(data, recap):
    fields = ["dosen","sinta_id","judul","penulis","jurnal","tahun","doi","url_doi",
              "url_garuda","url_artikel","garuda_author_id","peringkat_sinta",
              "sinta_status_verifikasi","sinta_bukti_url",
              "jurnal_sinta_peringkat_terkini","jurnal_sinta_url",
              "jurnal_sinta_status_verifikasi","jurnal_sinta_diperiksa","status_indeks_scopus"]
    with CSV_ARTICLES.open("w", encoding="utf-8-sig", newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        for p in data["dosen"]:
            for a in p["publikasi_garuda"]:
                row = {"dosen":p["nama"],"sinta_id":p.get("sinta_id")}
                row.update({k: a.get(k) for k in fields[2:]})
                writer.writerow({k:"" if row.get(k) is None else row.get(k) for k in fields})
    ranks = ["S" + str(i) for i in range(1,7)]
    with CSV_RECAP.open("w", encoding="utf-8-sig", newline="") as handle:
        fields2 = ["dosen","slug","tahun"] + ranks + ["belum_terverifikasi"]
        writer=csv.DictWriter(handle,fieldnames=fields2)
        writer.writeheader()
        for p in recap["dosen"]:
            for year, counts in p["per_tahun"].items():
                row = {"dosen":p["nama"],"slug":p["slug"],"tahun":year}
                for key in ranks+["belum_terverifikasi"]:row[key]=counts.get(key,0)
                writer.writerow(row)


def main():
    data=read_json(PUBLICATIONS)
    initial_count=sum(len(p.get("publikasi_garuda") or []) for p in data.get("dosen",[]))
    updated,recap,diag,js = enrich(data,read_json(CATALOG),read_json(PROOF))
    if initial_count!=recap["total_rekaman"]:
        raise ValueError("Jumlah artikel GARUDA berubah; batalkan")
    if recap["artikel_sinta_terverifikasi"]+recap["artikel_belum_terverifikasi"]!=initial_count:
        raise ValueError("Rekap rank artikel tidak konsisten; batalkan")
    write_json(PUBLICATIONS,updated)
    write_json(RECAP,recap)
    write_json(DIAGNOSTIC,diag)
    write_json(JOURNAL_RECAP,js)
    write_csv(updated,recap)
    print(json.dumps({"jurnal_cocok":diag["jurnal_unik_tercocokkan"],"rekaman_berperingkat_jurnal":diag["rekaman_dengan_rank_jurnal_teramati"],"rekaman_rank_artikel_bukti_doi":recap["artikel_sinta_terverifikasi"],"rekaman_garuda":initial_count},ensure_ascii=False))


if __name__ == "__main__":
    main()
