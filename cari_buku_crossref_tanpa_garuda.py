#!/usr/bin/env python3
"""Find independently published books and chapters by six faculty authors in Crossref.

Source does not use GARUDA. Matching author names on Crossref does not prove
Scopus indexing; accepted records become CANDIDATES for official title/ISBN lookup.
"""
import json,re,sys,time
from datetime import datetime,timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

ROOT=Path(__file__).resolve().parent
SCHOLAR=ROOT/"hasil"/"publikasi_scholar.json"
OUT=ROOT/"hasil"/"kandidat_buku_scopus_crossref.json"
ALLOWED_TYPES=("book-chapter","book")
def norm(s):
 return re.sub(r"[^a-z0-9]+"," ",str(s or "").casefold()).strip()
def author_ok(candidate,search):
 c=norm(candidate);s=norm(search)
 if not c or not s:return False
 if c==s:return True
 return SequenceMatcher(None,c,s).ratio()>=.89 and len(c.split())>=2
def fetch(name,kind):
 qs=urlencode({"query.author":name,"filter":"type:"+kind,"rows":100,"select":"DOI,title,author,ISBN,container-title,type,published,issued"})
 req=Request("https://api.crossref.org/works?"+qs,headers={"Accept":"application/json","User-Agent":"SainsData-UINSU-Book-Discovery/1.0"})
 try:
  with urlopen(req,timeout=25) as r:return r.status,json.loads(r.read(2500001).decode("utf-8"))
 except HTTPError as e:return e.code,None
 except (URLError,TimeoutError,OSError,ValueError) as e:return type(e).__name__,None
def main():
 d=json.loads(SCHOLAR.read_text(encoding="utf-8"))
 names=[(p["slug"],p["nama"]) for p in d.get("dosen",[]) if p.get("slug") and p.get("nama")]
 if len(names)!=6:raise ValueError("Dibutuhkan enam profil penulis Scholar")
 unique={}
 results=[]
 for slug,name in names:
  for kind in ALLOWED_TYPES:
   status,payload=fetch(name,kind)
   returned=(payload or {}).get("message",{}).get("items",[]) if status==200 else []
   found=0
   for p in returned:
    pnames=[" ".join((a.get("given") or "",a.get("family") or "")).strip() for a in p.get("author",[]) if isinstance(a,dict)]
    if not any(author_ok(n,name) for n in pnames):continue
    title=(p.get("title") or [None])[0]
    doi=p.get("DOI")
    if not doi or not title:continue
    yearvals=((p.get("published") or p.get("issued") or {}).get("date-parts") or [[None]])
    yr=yearvals[0][0]
    key=doi.lower()
    if key not in unique:
     unique[key]={"judul":title,"doi":doi,"tahun":yr,
       "jurnal":(p.get("container-title") or [None])[0] or "",
       "isbn":p.get("ISBN") or [],"dosen":[],"jenis_crossref":p.get("type"),
       "bukti_crossref":"https://doi.org/"+doi}
    if slug not in unique[key]["dosen"]:unique[key]["dosen"].append(slug)
    found+=1
   results.append({"slug":slug,"type":kind,"http":status,"returned":len(returned),"matched_author_exact":found})
   print("AUTHOR",slug,kind,"http",status,"retrieved",len(returned),"author_match",found,flush=True)
   time.sleep(.25)
 payload={"diperbarui_utc":datetime.now(timezone.utc).isoformat(),
          "sumber":"Crossref query.author and filter book/book-chapter (bukan bukti indeksasi Scopus)",
          "diagnostik":results,"jumlah_kandidat":len(unique),
          "publikasi":sorted(unique.values(),key=lambda x:(-(int(x.get("tahun") or 0)),x["judul"]))}
 OUT.parent.mkdir(exist_ok=True)
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("BUKU_BAB_BUKU",len(unique),flush=True)
if __name__=="__main__":
 try:main()
 except Exception as e:
  print("GAGAL",type(e).__name__,str(e)[:200],file=sys.stderr)
  sys.exit(1)
