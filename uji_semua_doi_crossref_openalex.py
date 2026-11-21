#!/usr/bin/env python3
"""Uji metadata Crossref + OpenAlex untuk seluruh DOI unik GARUDA.

Metadata Crossref/OpenAlex bukan verifikasi indeksasi Scopus.
Tidak mengubah publikasi GARUDA/SINTA/Scopus atau label WordPress.
"""
from __future__ import annotations
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import quote
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"hasil"/"publikasi_dosen.json"
OUTPUT=ROOT/"hasil"/"metadata_crossref_openalex.json"
RECAP=ROOT/"hasil"/"rekap_metadata_crossref_openalex.json"
MAX_WORKERS=5
RETRY_HTTP={429,500,502,503,504}

def norm(x):
    return re.sub(r"[^a-z0-9]+"," ",str(x or "").casefold()).strip()
def doi_key(x):
    s=re.sub(r"^https?://(?:dx\.)?doi\.org/","",str(x or "").strip(),flags=re.I).lower()
    s=s.strip(" ,;.)\"'")
    return s if re.fullmatch(r"10\.\d{4,9}/\S+",s) else None
def api(url):
    req=Request(url,headers={"User-Agent":"SainsData-UINSU-Publication-Metadata-Audit/1.0","Accept":"application/json"})
    for attempt in range(3):
        try:
            with urlopen(req,timeout=18) as resp:
                raw=resp.read(1200001)
                if len(raw)>1200000:return {"http":200,"error":"response_too_large"}
                return {"http":resp.status,"data":json.loads(raw.decode("utf-8-sig"))}
        except HTTPError as exc:
            if exc.code in RETRY_HTTP and attempt<2:
                time.sleep(1.5*(attempt+1))
                continue
            return {"http":exc.code}
        except (URLError,TimeoutError,OSError,ValueError) as exc:
            if attempt<2:
                time.sleep(1.5*(attempt+1))
                continue
            return {"http":None,"error":type(exc).__name__}
    return {"http":None,"error":"exhausted"}

def lookup(doi):
    c=api("https://api.crossref.org/works/"+quote(doi,safe="/"))
    o=api("https://api.openalex.org/works/https://doi.org/"+quote(doi,safe="/"))
    cr={"http":c.get("http")}
    oa={"http":o.get("http")}
    if c.get("http")==200 and isinstance(c.get("data"),dict):
        d=c["data"].get("message") or {}
        cr.update({"judul":(d.get("title") or [None])[0],
                   "jurnal":(d.get("container-title") or [None])[0],
                   "issn":d.get("ISSN") or [],
                   "tahun":((d.get("published") or {}).get("date-parts") or [[None]])[0][0],
                   "sitasi":d.get("is-referenced-by-count"),
                   "publisher":d.get("publisher")})
    if o.get("http")==200 and isinstance(o.get("data"),dict):
        d=o["data"];src=(d.get("primary_location") or {}).get("source") or {}
        oa.update({"judul":d.get("display_name"),
                   "jurnal":src.get("display_name"),
                   "issn":src.get("issn") or [],
                   "tahun":d.get("publication_year"),
                   "sitasi":d.get("cited_by_count"),
                   "openalex_id":d.get("id"),
                   "indexed_in":d.get("indexed_in") or []})
    return doi,cr,oa

def main():
    data=json.loads(SOURCE.read_text(encoding="utf8"))
    source={}
    for p in data.get("dosen") or []:
        for a in p.get("publikasi_garuda") or []:
            doi=doi_key(a.get("doi"))
            if not doi:continue
            if doi not in source:
                source[doi]={"doi":doi,"judul_garuda":a.get("judul"),
                             "tahun_garuda":a.get("tahun"),
                             "jurnal_garuda":a.get("jurnal"),"dosen":[p["slug"]]}
            elif p["slug"] not in source[doi]["dosen"]:
                source[doi]["dosen"].append(p["slug"])
    if len(source)<100:raise ValueError("Kurang dari 100 DOI; validasi sumber sebelum memperbarui hasil")
    # Keep exception/cancellation isolated; do not save partial data as complete.
    enriched={}
    started=time.monotonic()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures={pool.submit(lookup,doi):doi for doi in source}
        for i,f in enumerate(as_completed(futures),1):
            doi=futures[f]
            try:
                _,c,o=f.result()
            except Exception as exc:
                c={"http":None,"error":type(exc).__name__}
                o={"http":None,"error":type(exc).__name__}
            original=source[doi]
            check_title=o.get("judul") or c.get("judul")
            match=round(SequenceMatcher(None,norm(original["judul_garuda"]),norm(check_title)).ratio(),3) if check_title else None
            enriched[doi]={**original,"crossref":c,"openalex":o,"kesamaan_judul":match,
                           "status_scopus":"tidak_diuji_dari_crossref_openalex"}
            if i%50==0 or i==len(source):
                print("PROGRESS",i,"/",len(source), "Crossref 200:",sum(v["crossref"]["http"]==200 for v in enriched.values()),
                      "OpenAlex 200:",sum(v["openalex"]["http"]==200 for v in enriched.values()),flush=True)
    rows=[enriched[k] for k in sorted(enriched)]
    counts={}
    for k in ("crossref","openalex"):
        counts[k]={"berhasil":sum(r[k]["http"]==200 for r in rows),
                   "tidak_ada":sum(r[k]["http"]==404 for r in rows),
                   "gagal_akses":sum(r[k]["http"] not in (200,404) for r in rows)}
    byAuthor={}
    for p in data["dosen"]:
        pid=p["slug"]
        authors=[r for r in rows if pid in r["dosen"]]
        byAuthor[pid]={"doi_unik":len(authors),
                       "crossref_ditemukan":sum(r["crossref"]["http"]==200 for r in authors),
                       "openalex_ditemukan":sum(r["openalex"]["http"]==200 for r in authors)}
    result={"diperiksa_utc":datetime.now(timezone.utc).isoformat(),
            "diperiksa_total_doi_unik":len(rows),
            "sumber":"Crossref REST API + OpenAlex Works API",
            "hasil":counts,
            "per_dosen":byAuthor,
            "jumlah_ketidakcocokan_judul":sum(r["kesamaan_judul"] is not None and r["kesamaan_judul"]<0.72 for r in rows),
            "scopus_terverifikasi":None,
            "catatan":"Crossref/OpenAlex bukan Scopus. Sitasi tiap sumber harus berlabel. DOI yang tidak ada bukan bukti tidak terindeks Scopus.",
            "artikel":rows}
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    {k:result.pop(k) for k in ["artikel"]}
    RECAP.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("RINGKASAN",json.dumps(result,ensure_ascii=False),flush=True)
    print("Durasi perhitungan detik:",int(time.monotonic()-started),flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("GAGAL: ",type(exc).__name__,str(exc)[:200],file=sys.stderr)
        sys.exit(1)
