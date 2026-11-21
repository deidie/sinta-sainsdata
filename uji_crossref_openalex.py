#!/usr/bin/env python3
"""Uji DOI GARUDA ke Crossref dan OpenAlex tanpa API berbayar.

Hasil hanya diagnostik. Crossref/OpenAlex TIDAK membuktikan indeksasi Scopus.
Tidak mengubah artikel GARUDA, peringkat SINTA, ataupun status Scopus.
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent
SRC=ROOT/"hasil"/"publikasi_dosen.json"
OUT=ROOT/"hasil"/"diagnostik_crossref_openalex.json"
TARGETS=[
  "10.25126/jtiik.2023107437",      # siddik
  "10.31289/jite.v2i1.1496",        # siddik
  "10.24002/ijis.v7i2.10213",      # dedi
  "10.20895/infotel.v15i1.848",    # dedi
  "10.33558/piksel.v8i2.2291",     # dedi
  "10.21456/vol10iss2pp203-210",   # rakhmat
  "10.24114/cess.v11i1.72110",     # rakhmat
  "10.24114/cess.v2i1.4966",       # aidil
  "10.31602/tji.v14i2.9782",       # aidil
  "10.54209/jatilima.v5i01.395",   # ika
  "10.46880/jmika.Vol6No2.pp239-243", # ika
  "10.53513/jursi.v4i6.9709",      # puji
  "10.53513/jursik.v5i5.12734",    # puji
]

def doi_clean(x):
    return re.sub(r"^https?://(?:dx\.)?doi\.org/","",str(x or "").strip(),flags=re.I).lower()

def get_json(url):
    req=Request(url,headers={
       "User-Agent":"SainsData-UINSU-Metadata-Diagnostic/1.0 (metadata contact: openai-not-provided)",
       "Accept":"application/json"})
    try:
        with urlopen(req,timeout=24) as r:
            raw=r.read(900001)
            if len(raw)>900000: return {"status":"too_large"}
            return {"status":str(r.status),"json":json.loads(raw.decode("utf-8-sig"))}
    except HTTPError as e:
        return {"status":str(e.code)}
    except (URLError,TimeoutError,OSError,ValueError) as e:
        return {"status":type(e).__name__}

def crossref(doi):
    d=get_json("https://api.crossref.org/works/"+quote(doi,safe="/"))
    if d["status"]!="200": return {"http":d["status"]}
    meta=d["json"].get("message",{})
    return {"http":"200","doi":meta.get("DOI"),"judul":(meta.get("title") or [None])[0],
      "jurnal":(meta.get("container-title") or [None])[0],
      "issn":meta.get("ISSN") or [],"sitasi_crossref":meta.get("is-referenced-by-count"),
      "publisher":meta.get("publisher"),"tahun":((meta.get("published") or {}).get("date-parts") or [[None]])[0][0]}
def openalex(doi):
    d=get_json("https://api.openalex.org/works/https://doi.org/"+quote(doi,safe="/"))
    if d["status"]!="200":return {"http":d["status"]}
    meta=d["json"]
    source=((meta.get("primary_location") or {}).get("source") or {})
    ids=meta.get("ids") or {}
    return {"http":"200","doi":meta.get("doi"),"judul":meta.get("display_name"),
      "tahun":meta.get("publication_year"),"sitasi_openalex":meta.get("cited_by_count"),
      "openalex_id":meta.get("id"),"jurnal":source.get("display_name"),
      "issn":source.get("issn") or [],
      "source_openalex_id":source.get("id"),"indexed_in":meta.get("indexed_in"),
      "ids":{k:ids.get(k) for k in ("openalex","doi","mag","pmid","pmcid") if ids.get(k)}}

def main():
    d=json.loads(SRC.read_text(encoding="utf-8"))
    bydoi={}
    for p in d["dosen"]:
        for a in p["publikasi_garuda"]:
            k=doi_clean(a.get("doi"))
            if k and k not in bydoi: bydoi[k]={"dosen":[p["nama"]],"judul":a.get("judul"),"jurnal":a.get("jurnal"),"tahun":a.get("tahun")}
            elif k and p["nama"] not in bydoi[k]["dosen"]:bydoi[k]["dosen"].append(p["nama"])
    seen=set()
    rows=[]
    for doi in TARGETS:
        key=doi_clean(doi)
        if key in seen:continue
        seen.add(key)
        if key not in bydoi:raise RuntimeError("DOI tidak terdapat pada data GARUDA: "+key)
        cr=crossref(key)
        time.sleep(0.3)
        oa=openalex(key)
        rec={"doi":key,"garuda":bydoi[key],"crossref":cr,"openalex":oa,
             "scopus_status":"belum_terverifikasi"}
        rows.append(rec)
        print(f"{key} | Crossref={cr['http']} | OpenAlex={oa['http']} | CR-citations={cr.get('sitasi_crossref')} | OA-citations={oa.get('sitasi_openalex')}",flush=True)
        time.sleep(0.35)
    result={
        "diperiksa_utc":datetime.now(timezone.utc).isoformat(),
        "sumber":"API metadata publik Crossref dan OpenAlex",
        "jumlah_sample":len(rows),
        "crossref_berhasil":sum(1 for r in rows if r["crossref"]["http"]=="200"),
        "openalex_berhasil":sum(1 for r in rows if r["openalex"]["http"]=="200"),
        "scopus_terverifikasi_dari_sumber_ini":None,
        "catatan":"Crossref/OpenAlex tidak menyediakan bukti Scopus EID; keberadaan DOI atau sitasi bukan konfirmasi indeksasi Scopus.",
        "artikel":rows
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("HASIL",json.dumps({k:v for k,v in result.items() if k!="artikel"},ensure_ascii=False),flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("DIAGNOSTIK GAGAL:",str(e)[:250],file=sys.stderr)
        raise
