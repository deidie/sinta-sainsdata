#!/usr/bin/env python3
"""Rekap peringkat jurnal SINTA yang teramati (bukan peringkat artikel historis)."""
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "hasil" / "publikasi_dosen.json"
DEST = ROOT / "hasil" / "rekap_jurnal_sinta_terkini.json"
CSV = ROOT / "hasil" / "rekap_jurnal_sinta_terkini.csv"
FIELDS = ["S"+str(i) for i in range(1,7)] + ["belum_tercocokkan"]


def norm(x):
    s = unicodedata.normalize("NFKD", str(x or "").casefold())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def paper_key(a):
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", str(a.get("doi") or "").lower()).strip()
    if doi.startswith("10."):
        return "doi:" + doi
    return "title:" + norm(a.get("judul")) + ":" + str(a.get("tahun") or "")


def rank_key(article):
    value = article.get("jurnal_sinta_peringkat_terkini")
    if type(value) is int and value in range(1,7) and str(article.get("jurnal_sinta_url") or "").startswith("https://sinta.kemdiktisaintek.go.id/journals/profile/"):
        return "S" + str(value)
    return "belum_tercocokkan"


def totals(articles):
    c=Counter(rank_key(a) for a in articles)
    return {key:c[key] for key in FIELDS}


def by_year(articles):
    grouped = defaultdict(list)
    for a in articles:
        year = a.get("tahun")
        if str(year).isdigit() and 1900 <= int(year) <= 2100:
            grouped[str(year)].append(a)
    return {year:totals(a) for year,a in sorted(grouped.items(),reverse=True)}


def main():
    data=json.loads(SRC.read_text(encoding="utf-8"))
    people = data.get("dosen") or []
    if len(people)!=6:
        raise ValueError("Dosen harus sesuai enam profil")
    lecturers=[]
    allrows=[]
    unique={}
    conflicts=[]
    for p in people:
        rows=p.get("publikasi_garuda") or []
        lecturers.append({"slug":p["slug"],"nama":p["nama"],"rekaman":len(rows),"peringkat_jurnal":totals(rows),"per_tahun":by_year(rows)})
        allrows.extend(rows)
        for a in rows:
            key=paper_key(a)
            prev=unique.get(key)
            if prev is not None:
                old=rank_key(prev); new=rank_key(a)
                if old != new and old != "belum_tercocokkan" and new != "belum_tercocokkan":
                    conflicts.append({"kunci":key,"sebelumnya":old,"lainnya":new})
                if old=="belum_tercocokkan" and new!="belum_tercocokkan":
                    unique[key]=a
            else:
                unique[key]=a
    if conflicts:
        raise ValueError("Ada peringkat jurnal yang bertentangan untuk artikel bersama, verifikasi manual")
    docs=list(unique.values())
    out={
        "diperbarui_utc":datetime.now(timezone.utc).isoformat(),
        "jenis_rekap":"Peringkat terkini jurnal SINTA pada sumber terindeks resmi, BUKAN akreditasi historis artikel",
        "rekaman_per_dosen_dengan_duplikasi_kolaborasi":len(allrows),
        "artikel_unik_prodi":len(docs),
        "rekap_unik_prodi":totals(docs),
        "rekap_tahunan_unik_prodi":by_year(docs),
        "rekap_per_dosen":lecturers,
        "catatan":"S1-S6 pada file ini adalah PERINGKAT JURNAL SAAT TERAMATI. Untuk peringkat ARTIKEL yang memiliki bukti DOI, gunakan hasil/rekap_sinta.json. Artikel bersama dihitung sekali pada rekap unik prodi.",
    }
    DEST.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with CSV.open("w",encoding="utf-8-sig",newline="") as f:
        fields=["level","dosen","tahun","jumlah_rekaman"]+FIELDS
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        def emit(level,name,year,counts):
            writer.writerow({"level":level,"dosen":name,"tahun":year,"jumlah_rekaman":sum(counts.values()),**counts})
        emit("Prodi (unik)","", "Semua tahun",out["rekap_unik_prodi"])
        for year,counts in out["rekap_tahunan_unik_prodi"].items():emit("Prodi (unik)","",year,counts)
        for p in lecturers:
            emit("Dosen",p["nama"],"Semua tahun",p["peringkat_jurnal"])
            for year,counts in p["per_tahun"].items():emit("Dosen",p["nama"],year,counts)
    print(json.dumps({"artikel_unik_prodi":len(docs),"rekaman":len(allrows),"rank_tercocokkan":sum(v for k,v in totals(docs).items() if k!="belum_tercocokkan"),"duplikat_dosen":len(allrows)-len(docs)},ensure_ascii=False))


if __name__=="__main__":main()
