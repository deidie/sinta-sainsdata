#!/usr/bin/env python3
"""Uji resolusi enam Scopus Author ID ke OpenAlex, tanpa menyimpulkan artikel Scopus.

ID yang tidak bisa diresolusikan tetap dibiarkan 'belum_dikonfirmasi'.
"""
import json, os, re, time
from urllib.error import HTTPError,URLError
from urllib.parse import quote
from urllib.request import Request,urlopen
from datetime import datetime,timezone
from pathlib import Path

IDS=["58996427700","57214153048","60570206100","57222343067","60904491000","58190434200"]
KNOWN={
 "58996427700":{"nama":"Muhammad Dedi Irawan","slug":"dedi","sumber":"https://jurnal.unimed.ac.id/2012/index.php/cess/id/about/editorialHistory"},
 "57222343067":{"nama":"Puji Sari Ramadhan","slug":"puji","sumber":"https://jurnal.ilmubersama.com/index.php/hello_world/Reviewer"},
 "58190434200":{"nama":"Rakhmat Kurniawan R","slug":"rakhmat","sumber":"https://si.uinsu.ac.id/organisasi"}
}
OUT=Path("hasil/diagnostik_enam_author_id_scopus.json")
def read(url):
 req=Request(url,headers={"Accept":"application/json","User-Agent":"SainsData-UINSU-Author-ID-Audit/1.0"})
 try:
  with urlopen(req,timeout=22) as r:return r.status,json.loads(r.read(900000).decode("utf-8-sig"))
 except HTTPError as e:return e.code,{"error":str(e.reason)}
 except (URLError,TimeoutError,OSError,ValueError) as e:return None,{"error":type(e).__name__}

def main():
 rows=[]
 for sid in IDS:
  trials=[]
  for path in ["scopus:"+sid,"https://www.scopus.com/authid/detail.uri?authorId="+sid]:
   status,payload=read("https://api.openalex.org/authors/"+quote(path,safe=":/?="))
   trials.append({"format":path if path.startswith("scopus:") else "profile_url","http":status})
   if status==200 and isinstance(payload,dict) and payload.get("id"):
    ids=payload.get("ids") or {}
    linked=ids.get("scopus") or ""
    match=bool(re.search(r"(?<!\d)"+re.escape(sid)+r"(?!\d)",str(linked)))
    rows.append({"scopus_author_id":sid,"sumber_identitas":KNOWN.get(sid),
       "status":"terpaut_scopus_id" if match else "identitas_openalex_butuh_verifikasi",
       "openalex_id":payload.get("id"),"nama_openalex":payload.get("display_name"),
       "works_count_openalex":payload.get("works_count"),
       "openalex_scopus_external_id":linked,"scopus_id_tercantum_di_openalex":match,
       "percobaan":trials})
    break
  else:
   rows.append({"scopus_author_id":sid,"sumber_identitas":KNOWN.get(sid),
     "status":"akses_atau_kecocokan_belum_tersedia","percobaan":trials})
  print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
  time.sleep(.25)
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps({"diperiksa_utc":datetime.now(timezone.utc).isoformat(),
 "sumber":"OpenAlex Author ID alias scopus:... dan profil institusi",
 "peringatan":"OpenAlex bukan rekaman Scopus; identitas penulis dan daftar karya harus dibedakan dari rekaman Scopus resmi.",
 "profil":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
