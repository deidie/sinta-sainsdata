#!/usr/bin/env python3
"""Ambil naskah berdasarkan 6 Scopus Author ID langsung dari API resmi Elsevier.

Tidak mengganti Scopus Author ID dengan SINTA ID, dan tidak mengasumsikan
semua ID dimiliki dosen tertentu. Bila API key/izin tidak tersedia, data
lama dipertahankan dan status ditandai belum diverifikasi.
"""
from __future__ import annotations
import json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode,urlparse
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parent
CONFIG=ROOT/"data"/"daftar_scopus_author_id.json"
OUTPUT=ROOT/"hasil"/"naskah_scopus_author_id.json"
STATUS=ROOT/"hasil"/"status_scopus_author_id.json"
HOST="api.elsevier.com"
VALID_EID=re.compile(r"^2-s2\.0-\d{7,}$")
VALID_ID=re.compile(r"^\d{10,12}$")
COUNT_PER_PAGE=25
MAX_RESULTS_PER_ID=300
MAX_REQUESTS=120

def load(path,default):
 try:return json.loads(path.read_text(encoding="utf-8"))
 except (OSError,ValueError):return default

def parse_doi(value):
 v=str(value or "").strip().lower()
 v=re.sub(r"^https?://(?:dx\.)?doi\.org/","",v)
 return v if re.fullmatch(r"10\.\d{4,9}/\S+",v) else None

def fetch(api_key,inst,sid,start):
 query=urlencode({"query":f"authid({sid})","count":COUNT_PER_PAGE,"start":start,"view":"STANDARD"})
 uri="https://api.elsevier.com/content/search/scopus?"+query
 headers={"Accept":"application/json","X-ELS-APIKey":api_key,"User-Agent":"SainsData-UINSU-Scopus-Author-Sync/1.0"}
 if inst:headers["X-ELS-Insttoken"]=inst
 req=Request(uri,headers=headers)
 try:
  with urlopen(req,timeout=28) as response:
   if urlparse(response.geturl()).hostname!=HOST:return {"error":"redirect_terlarang"}
   raw=response.read(3000001)
   if len(raw)>3000000:return {"error":"response_terlalu_besar"}
   return {"status":response.status,"data":json.loads(raw.decode("utf-8"))}
 except HTTPError as e:return {"status":e.code,"error":"http_error"}
 except (URLError,TimeoutError,OSError,ValueError) as e:return {"error":type(e).__name__}

def document(entry,sid):
 if not isinstance(entry,dict):return None
 eid=str(entry.get("eid") or "").strip()
 if not VALID_EID.fullmatch(eid):return None
 doi=parse_doi(entry.get("prism:doi"))
 title=str(entry.get("dc:title") or "").strip()
 if not title:return None
 cover=str(entry.get("prism:coverDate") or "").strip()
 year=int(cover[:4]) if re.match(r"^(?:19|20)\d\d",cover) else None
 links=entry.get("link") or []
 scopus_url="https://www.scopus.com/record/display.uri?eid="+eid+"&origin=resultslist"
 return {"scopus_eid":eid,"doi":doi,"judul":title,
   "penulis_utama":str(entry.get("dc:creator") or ""),
   "jurnal":str(entry.get("prism:publicationName") or ""),
   "tahun":year,"tanggal_terbit":cover or None,
   "tipe":entry.get("prism:aggregationType"),
   "sitasi_scopus":int(entry["citedby-count"]) if str(entry.get("citedby-count") or "").isdigit() else None,
   "scopus_bukti_url":scopus_url,
   "scopus_author_ids":[sid],
   "sumber":"Elsevier Scopus Search API, query authid"}

def merge(list_docs):
 merged={}
 for d in list_docs:
  key=("doi:"+d["doi"]) if d.get("doi") else ("eid:"+d["scopus_eid"])
  if key in merged:
   previous=merged[key]
   previous["scopus_author_ids"]=sorted(set(previous["scopus_author_ids"]+d["scopus_author_ids"]))
   if not previous.get("doi") and d.get("doi"):previous["doi"]=d["doi"]
  else:merged[key]=d
 return sorted(merged.values(),key=lambda d:(-(d.get("tahun") or 0),d["judul"].casefold()))

def main():
 config=load(CONFIG,{})
 profiles=config.get("profiles") or []
 ids=[p.get("scopus_author_id") for p in profiles]
 if len(ids)!=6 or len(set(ids))!=6 or any(not VALID_ID.fullmatch(str(x or "")) for x in ids):
  raise ValueError("Harus tepat enam Scopus Author ID yang berbeda")
 now=datetime.now(timezone.utc).isoformat()
 key=os.getenv("SCOPUS_API_KEY","").strip()
 inst=os.getenv("SCOPUS_INST_TOKEN","").strip()
 prior=load(OUTPUT,{"profil":[]})
 old={p.get("scopus_author_id"):p for p in prior.get("profil",[]) if isinstance(p,dict)}
 requests=0
 statuses=[]
 rows=[]
 for p in profiles:
  sid=p["scopus_author_id"]
  saved=old.get(sid,{})
  stored=saved.get("naskah") if isinstance(saved.get("naskah"),list) else []
  state="belum_ada_akses_api" if not key else "akan_diperiksa"
  data=[]
  count_reported=None
  if key:
   state="sukses"
   for offset in range(0,MAX_RESULTS_PER_ID,COUNT_PER_PAGE):
    if requests>=MAX_REQUESTS:
     state="kuota_permintaaan_tercapai";break
    result=fetch(key,inst,sid,offset);requests+=1
    if result.get("status")!=200:
     state="akses_dibatasi" if result.get("status") in (401,403,429) else "error_api"
     break
    payload=result.get("data") or {}
    body=payload.get("search-results") or {}
    if offset==0:
     try:count_reported=int(body.get("opensearch:totalResults") or 0)
     except (ValueError,TypeError):count_reported=None
    entries=body.get("entry") or []
    if not isinstance(entries,list):state="respons_tidak_valid";break
    for e in entries:
     paper=document(e,sid)
     if paper:data.append(paper)
    if len(entries)<COUNT_PER_PAGE or (count_reported is not None and offset+len(entries)>=count_reported):break
    time.sleep(0.4)
   # Preserve previous data when pagination was interrupted.
   if state!="sukses":data=stored
  else:data=stored
  # Verify returned source identities only when API yielded real results.
  if state=="sukses":
   final=merge(data)
  else:final=stored
  rows.append({"scopus_author_id":sid,"scopus_url":p.get("scopus_url"),
    "nama_terverifikasi":p.get("nama_terverifikasi"),
    "slug_dosen":p.get("slug_dosen"),
    "sumber_identitas":p.get("sumber_identitas"),
    "status_pemeriksaan":state,
    "jumlah_dilaporkan_scopus":count_reported if state=="sukses" else saved.get("jumlah_dilaporkan_scopus"),
    "jumlah_naskah_dengan_bukti_api":len(final),
    "naskah":final})
  statuses.append({"scopus_author_id":sid,"status":state,
     "rekaman_tersimpan":len(final),"terlapor":count_reported})
  print(sid,"status=",state,"naskah=",len(final),"permintaan=",requests,flush=True)
  if state=="akses_dibatasi":break
 # If API was rejected during run, copy remaining profiles unchanged, never silently erase.
 for p in profiles[len(rows):]:
  sid=p["scopus_author_id"]
  saved=old.get(sid,{})
  docs=saved.get("naskah") if isinstance(saved.get("naskah"),list) else []
  rows.append({"scopus_author_id":sid,"scopus_url":p.get("scopus_url"),
    "nama_terverifikasi":p.get("nama_terverifikasi"),
    "slug_dosen":p.get("slug_dosen"),
    "sumber_identitas":p.get("sumber_identitas"),
    "status_pemeriksaan":"tidak_diuji_karena_akses_dibatasi",
    "jumlah_dilaporkan_scopus":saved.get("jumlah_dilaporkan_scopus"),
    "jumlah_naskah_dengan_bukti_api":len(docs),"naskah":docs})
  statuses.append({"scopus_author_id":sid,"status":"tidak_diuji_karena_akses_dibatasi","rekaman_tersimpan":len(docs)})
 all_docs=merge([doc for person in rows for doc in person["naskah"]])
 success=any(p["status_pemeriksaan"]=="sukses" for p in rows)
 if success or OUTPUT.exists():
  OUTPUT.parent.mkdir(parents=True,exist_ok=True)
  OUTPUT.write_text(json.dumps({"versi":1,"diperbarui_utc":now,
    "sumber":"Elsevier Scopus Search API berdasarkan Scopus Author ID",
    "peringatan":"Jumlah berasal dari API dan artikel memiliki EID. Nama ID yang belum terverifikasi tidak dikaitkan otomatis dengan dosen lain. Tidak menggunakan GARUDA untuk menyatakan artikel Scopus.",
    "profil":rows,"naskah_unik":all_docs,"jumlah_naskah_unik":len(all_docs)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 STATUS.parent.mkdir(parents=True,exist_ok=True)
 STATUS.write_text(json.dumps({"diperiksa_utc":now,"api_key_tersedia":bool(key),
     "jumlah_author_id":6,"jumlah_permintaan":requests,"status_per_id":statuses,
     "naskah_scopus_tersimpan_total_unik":len(all_docs) if success or OUTPUT.exists() else None,
     "catatan":"Tanpa API key atau akses Elsevier, naskah Scopus tidak dapat dibaca dari enam tautan. Tidak ada naskah fiktif dan tidak ada perubahan daftar GARUDA."},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
 try:main()
 except Exception as e:
  print("GAGAL",type(e).__name__,str(e)[:220],file=sys.stderr)
  sys.exit(1)
