#!/usr/bin/env python3
"""Cari cakupan SUMBER Scopus dari daftar resmi Elsevier; tidak butuh Scopus API/GARUDA.

Input independen:
 * data/kandidat_publikasi_scopus.json: DOI, ISSN, ISBN, judul (opsional)
 * hasil/publikasi_scholar.json: kandidat dari Scholar (opsional)
 * hasil/naskah_scopus_author_id.json: EID hasil Scopus API jika tersedia (opsional)
 * hasil/metadata_crossref_openalex.json: seed metadata DOI lama (opsional,
   tidak diwajibkan dan tidak dapat dipakai membuktikan artikel Scopus).

Aturan: SOURCE matching != artikel Scopus terindeks. Book list includes a
book record, but not necessarily a chapter. Reject uncertain matches.
"""
import io,json,re,sys,zipfile,html
from collections import Counter,defaultdict
from datetime import datetime,timezone
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlparse
from urllib.request import Request,urlopen
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/"hasil"/"pemeriksaan_scopus_tanpa_api.json"
SUMMARY=ROOT/"hasil"/"rekap_scopus_tanpa_api.json"
INPUT=ROOT/"data"/"kandidat_publikasi_scopus.json"
CURRENT="https://www.elsevier.com/products/scopus/content"
OFFICIAL={
 "sources":"https://downloads.ctfassets.net/o78em1y1w4i4/7xtaTxNiNcWRTeZkV86eNy/a88a2798510dc7f7888e80dc03ec0779/ext_list_Oct_2026.xlsx",
 "books":"https://downloads.ctfassets.net/o78em1y1w4i4/2uPDv7HcQRnPoxj5xyGhBS/62cc5084eb5566e942271f09e37ccf80/Scopus_book_list_Q2.xlsx",
}
NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
MAX_BYTES=50000000
MAX_WORKS=1500

def read(path,default):
 try:return json.loads(path.read_text(encoding="utf8"))
 except (OSError,ValueError):return default
def title_norm(s):
 return re.sub(r"[^a-z0-9]+"," ",str(s or "").casefold()).strip()
def sim(a,b):
 a,b=title_norm(a),title_norm(b)
 return round(SequenceMatcher(None,a,b).ratio(),3) if a and b else 0
def issn(s):
 s=re.sub(r"[^0-9X]+","",str(s or "").upper())
 return s if re.fullmatch(r"\d{7}[\dX]",s) else None
def isbn(s):
 s=re.sub(r"[^0-9X]+","",str(s or "").upper())
 return s if (len(s) in (10,13) and s[:-1].isdigit()) else None
def doi(s):
 s=re.sub(r"^https?://(?:dx\.)?doi\.org/","",str(s or "").strip().lower())
 return s if re.fullmatch(r"10\.\d{4,9}/\S+",s) else None
def many(v,formatter):
 vals=v if isinstance(v,list) else [v]
 return sorted({w for x in vals if (w:=formatter(x))})
def year(s):
 try:
  y=int(s)
  return y if 1900<=y<=2100 else None
 except (ValueError,TypeError):return None

def candidates():
 works={}
 def insert(key,title,source,yr=None,issns=None,isbns=None,doi_value=None,eid=None,author_slugs=None):
  if not key or not title:return
  x=works.setdefault(key,{"id_kandidat":key,"judul":title,"jurnal_atau_buku":source or "",
    "tahun":year(yr),"doi":doi(doi_value),"issn":[],"isbn":[],"scopus_eid":eid,
    "dosen":[],"asal_kandidat":[]})
  if not x["tahun"]:x["tahun"]=year(yr)
  if not x["doi"]:x["doi"]=doi(doi_value)
  if not x["scopus_eid"]:x["scopus_eid"]=eid
  for field,vals in (("issn",many(issns or [],issn)),("isbn",many(isbns or [],isbn)),
                      ("dosen",author_slugs or []),("asal_kandidat",[source_type])):
   x[field]=sorted(set(x[field]+vals))
 def seed(source_type,record):
  title=record.get("judul") or record.get("judul_garuda") or record.get("title")
  if not title:return
  doi_value=doi(record.get("doi"))
  eid=str(record.get("scopus_eid") or "").strip() or None
  candidate_id=("eid:"+eid) if eid else (("doi:"+doi_value) if doi_value else
        "judul:"+title_norm(title)[:140]+":"+str(year(record.get("tahun") or record.get("tahun_garuda")) or "?"))
  insert(candidate_id,title,record.get("jurnal") or record.get("jurnal_garuda") or
         record.get("sumber") or "",record.get("tahun") or record.get("tahun_garuda"),
         record.get("issn") or record.get("eissn") or [],record.get("isbn") or [],
         doi_value,eid,record.get("dosen") or [])
  x=works[candidate_id]
  x["asal_kandidat"]=sorted(set(x["asal_kandidat"]+[source_type]))
  if source_type=="manual" and record.get("scopus_bukti_url"):
   x["bukti_scopus_url_manually"]=record["scopus_bukti_url"]

 # DOI metadata from Crossref/OpenAlex may have originated from GARUDA
 # but neither GARUDA nor any earlier metadata is REQUIRED for this job.
 old=read(ROOT/"hasil"/"metadata_crossref_openalex.json",{})
 for obj in old.get("artikel",[]):
  c=obj.get("crossref") or {};o=obj.get("openalex") or {}
  name=c.get("judul") or o.get("judul") or obj.get("judul_garuda")
  source=c.get("jurnal") or o.get("jurnal") or obj.get("jurnal_garuda")
  item={"judul":name,"jurnal":source,"tahun":c.get("tahun") or o.get("tahun") or obj.get("tahun_garuda"),
        "doi":obj.get("doi"),"issn":list(set((c.get("issn") or [])+(o.get("issn") or []))),
        "dosen":obj.get("dosen") or []}
  seed("metadata_doi_crossref_openalex",item)
 scholar=read(ROOT/"hasil"/"publikasi_scholar.json",{})
 for p in scholar.get("dosen",[]):
  for a in p.get("artikel_scholar",[]):
   seed("scholar_judul_tanpa_keharusan_doi",{"judul":a.get("judul"),
    "jurnal":a.get("jurnal"),"tahun":a.get("tahun"),"dosen":[p.get("slug")]})
 scopus=read(ROOT/"hasil"/"naskah_scopus_author_id.json",{})
 for p in scopus.get("profil",[]):
  for a in p.get("naskah",[]):
   seed("scopus_api_eid",{"judul":a.get("judul"),"jurnal":a.get("jurnal"),
    "tahun":a.get("tahun"),"doi":a.get("doi"),"issn":a.get("issn") or [],
    "isbn":a.get("isbn") or [],"scopus_eid":a.get("scopus_eid"),"dosen":[p.get("slug_dosen")] if p.get("slug_dosen") else []})
 manual=read(INPUT,{"publikasi":[]})
 for a in manual.get("publikasi",[]):seed("manual",a)
 if len(works)>MAX_WORKS:raise ValueError("Terlalu banyak kandidat: "+str(len(works)))
 # Canonicalize by DOI when a work appears in Scholar + Crossref with same DOI only.
 return list(works.values())

class OfficialLinks(HTMLParser):
 def __init__(self):
  super().__init__();self.active=None;self.links={}
 def handle_starttag(self,tag,attrs):
  if tag=="a":self.active=dict(attrs).get("href")
 def handle_data(self,data):
  if not self.active:return
  if "download the source title list" in data.lower():self.links["sources"]=self.active
  if "download the book title list" in data.lower():self.links["books"]=self.active
 def handle_endtag(self,tag):
  if tag=="a":self.active=None

def download(url):
 req=Request(url,headers={"User-Agent":"SainsData-UINSU-Public-Scopus-Source-Checker/1.0",
   "Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"})
 with urlopen(req,timeout=70) as res:
  hostname=urlparse(res.geturl()).hostname
  if hostname not in {"downloads.ctfassets.net","assets.ctfassets.net"}:
   raise ValueError("Unknown source download domain: "+str(hostname))
  b=res.read(MAX_BYTES+1)
  if len(b)>MAX_BYTES:raise ValueError("Official file too large")
  return b

def official_urls():
 try:
  req=Request(CURRENT,headers={"User-Agent":"Mozilla/5.0 ScopusSourceAudit/1.0"})
  with urlopen(req,timeout=15) as r:
   if urlparse(r.geturl()).hostname not in {"www.elsevier.com","elsevier.com"}:raise ValueError("Unexpected redirect")
   s=r.read(1200000).decode("utf-8","replace")
  doc=OfficialLinks();doc.feed(s)
  urls={}
  for key,url in doc.links.items():
   full=urljoin(CURRENT,html.unescape(url))
   if urlparse(full).hostname in {"downloads.ctfassets.net","assets.ctfassets.net"}:urls[key]=full
  return urls,"ditemukan_dari_halaman_resmi"
 except Exception:return {},"tautan_resmi_persisten"
def workbook_stream(body,required_sheet):
 z=zipfile.ZipFile(io.BytesIO(body))
 if z.testzip() is not None:raise RuntimeError("Official XLSX corrupt")
 w=ET.fromstring(z.read("xl/workbook.xml"));rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
 refs={r.get("Id"):r.get("Target") for r in rels}
 ss=[]
 if "xl/sharedStrings.xml" in z.namelist():
  with z.open("xl/sharedStrings.xml") as f:
   for _,elem in ET.iterparse(f,events=("end",)):
    if elem.tag.endswith("}si"):
     ss.append("".join(t.text or "" for t in elem.findall(".//m:t",NS)))
     elem.clear()
 sheet_name=None;sheet_path=None
 for e in w.findall(".//m:sheets/m:sheet",NS):
  name=e.get("name","")
  if required_sheet(name):
   sheet_name=name
   target=refs.get(e.get("{"+NS["r"]+"}id"),"")
   sheet_path=target.lstrip("/") if target.startswith("/") else "xl/"+target.lstrip("/")
   if sheet_path.startswith("xl/xl/"):sheet_path=sheet_path[3:]
   break
 if not sheet_path or sheet_path not in z.namelist():raise ValueError("Required worksheet missing: "+str(sheet_name))
 def rows():
  with z.open(sheet_path) as f:
   for _,elem in ET.iterparse(f,events=("end",)):
    if elem.tag.endswith("}row"):
     items={}
     for c in elem.findall("m:c",NS):
      letter=re.match(r"[A-Z]+",c.get("r",""))
      if not letter:continue
      col=0
      for ch in letter.group():col=col*26+ord(ch)-64
      v=c.find("m:v",NS)
      if c.get("t")=="inlineStr":raw="".join(t.text or "" for t in c.findall(".//m:t",NS))
      elif v is not None:
       raw=v.text or ""
       if c.get("t")=="s" and raw.isdigit():
        i=int(raw);raw=ss[i] if i<len(ss) else ""
      else:raw=""
      items[col-1]=raw.strip()
     if items:yield [items.get(i,"") for i in range(max(items)+1)]
     elem.clear()
 return sheet_name, rows()

def normalize_header(s):
 return title_norm(s).replace(" ","_")
def source_index(worksheet,works):
 lookup=defaultdict(list)
 wanted={x for w in works for x in w["issn"]}
 rows_checked=0
 it=iter(worksheet)
 header=next(it,[])
 names={normalize_header(v):i for i,v in enumerate(header)}
 needed=["sourcerecord_id","source_title","issn","eissn","active_or_inactive","coverage","titles_discontinued_by_scopus","source_type"]
 if any(x not in names for x in needed):raise RuntimeError("Unrecognized official source-list headers: "+str(sorted(names)[:12]))
 def val(row,key):
  i=names.get(key)
  return row[i] if i is not None and i<len(row) else ""
 for row in it:
  rows_checked+=1
  source_issns={x for key in ("issn","eissn") if (x:=issn(val(row,key)))}
  shared=wanted.intersection(source_issns)
  if not shared:continue
  item={"id_sumber_scopus":val(row,"sourcerecord_id"),
     "nama_sumber":val(row,"source_title"),
     "issn":sorted(source_issns),
     "status_sumber":val(row,"active_or_inactive"),
     "cakupan_tahun":val(row,"coverage"),
     "discontinued":val(row,"titles_discontinued_by_scopus"),
     "tipe_sumber":val(row,"source_type"),
     "sumber_bukti":"https://www.scopus.com/sourceid/"+val(row,"sourcerecord_id")}
  for v in shared:lookup[v].append(item)
 return lookup,rows_checked

def book_index(worksheet,works):
 wanted_isbn={x for w in works for x in w["isbn"]}
 wanted_titles={title_norm(w["judul"]) for w in works if w["judul"]}
 items_by_isbn=defaultdict(list);items_by_title=defaultdict(list)
 checked=0
 it=iter(worksheet);header=next(it,[])
 cols={normalize_header(v):i for i,v in enumerate(header)}
 if not {"title","print_isbn","electronic_isbn","scopus_id"}.issubset(cols):
  raise RuntimeError("Unexpected official Scopus book list headers "+str(cols))
 def val(r,k):return r[cols[k]] if cols[k]<len(r) else ""
 for r in it:
  checked+=1
  title=val(r,"title")
  ids=set()
  for key in ("print_isbn","electronic_isbn"):
   for v in re.split(r"[;, ]+",val(r,key)):
    if (item:=isbn(v)):ids.add(item)
  norm_title=title_norm(title)
  if not ids.intersection(wanted_isbn) and norm_title not in wanted_titles:continue
  item={"judul_buku":title,"isbn":sorted(ids),"id_buku_scopus":val(r,"scopus_id"),
    "tahun_buku":year(val(r,"publication_year")) if "publication_year" in cols else None,
    "penerbit":val(r,"publisher") if "publisher" in cols else "",
    "sumber_bukti":CURRENT}
  for x in ids.intersection(wanted_isbn):items_by_isbn[x].append(item)
  if norm_title in wanted_titles:items_by_title[norm_title].append(item)
 return items_by_isbn,items_by_title,checked

def parse_ranges(s):
 out=set()
 for part in re.split(r"[;,]",str(s or "")):
  x=re.search(r"\b(18\d\d|19\d\d|20\d\d)(?:\s*-\s*(18\d\d|19\d\d|20\d\d))?\b",part)
  if x:
   a=int(x.group(1));b=int(x.group(2) or x.group(1))
   if b>=a and b-a<300:out.update(range(a,b+1))
 return out
def status_serial(w,index):
 matches=[]
 for n in w["issn"]:matches.extend(index.get(n,[]))
 matches=list({(r["id_sumber_scopus"],r["nama_sumber"]):r for r in matches}.values())
 if not matches:return None
 best=sorted(matches,key=lambda r:sim(r["nama_sumber"],w["jurnal_atau_buku"]),reverse=True)
 choice=best[0]
 # A single source matched by ISSN is sufficient for source identity;
 # if different source IDs share an ISSN and titles disagree, flag review.
 if len(best)>1 and sim(best[0]["nama_sumber"],w["jurnal_atau_buku"])<0.6:
  return {"status":"perlu_review_issn_berbagi","candidates":best[:5]}
 coverage=parse_ranges(choice["cakupan_tahun"])
 yr=w.get("tahun")
 note=("tahun_masuk_daftar_cakupan" if yr in coverage else
       "tahun_tidak_ada_pada_daftar_cakupan" if yr and coverage else "tahun_tidak_dapat_dipastikan")
 return {"status":"jurnal_atau_seri_ada_di_daftar_scopus","cakupan_pada_tahun":note,
   "kecocokan_nama":sim(choice["nama_sumber"],w["jurnal_atau_buku"]),
   "data_sumber":choice}

def status_book(w,books_by_isbn,books_by_title):
 matches=[]
 for num in w["isbn"]:matches.extend(books_by_isbn.get(num,[]))
 if not matches:
  matches=books_by_title.get(title_norm(w["judul"]),[])
  # Title alone is not proof: require exact title + matching year if known.
  matches=[b for b in matches if w.get("tahun") is not None and b["tahun_buku"]==w["tahun"]]
  method="judul_dan_tahun"
 else:method="isbn"
 unique=list({(m["id_buku_scopus"],m["judul_buku"]):m for m in matches}.values())
 if not unique:return None
 if len(unique)!=1:return {"status":"perlu_review_kecocokan_buku","jumlah_kandidat":len(unique)}
 match=unique[0]
 if method=="isbn" and w.get("tahun") and match.get("tahun_buku") and abs(w["tahun"]-match["tahun_buku"])>2:
  return {"status":"perlu_review_isbn_tahun_berbeda","data_buku":match}
 return {"status":"buku_tercantum_di_daftar_scopus","metode":method,
    "data_buku":match,"catatan":"Daftar buku membuktikan judul buku dalam cakupan sumber. Bab buku individual belum otomatis terverifikasi tanpa EID."}

def main():
 works=candidates()
 if not works:raise RuntimeError("Tidak ada kandidat DOI/ISBN/judul")
 urls,source_mode=official_urls()
 urls={**OFFICIAL,**urls}
 report={"diperiksa_utc":datetime.now(timezone.utc).isoformat(),
   "sumber_daftar":"Daftar sumber dan buku resmi Elsevier",
   "tautan_sumber":urls,"mode_penemuan_tautan":source_mode,
   "kandidat":len(works),"scopus_eid_tersedia":sum(bool(w.get("scopus_eid")) for w in works),
   "catatan":"Tidak memerlukan GARUDA. Daftar sumber terindeks dan daftar buku tidak menyatakan semua artikel/bab buku otomatis ada sebagai dokumen Scopus."}
 try:
  serial=download(urls["sources"])
 except Exception as e:
  # Fail visibly; don't overwrite previous successful results.
  raise RuntimeError("Gagal mengakses daftar serial Scopus resmi: "+str(e)) from e
 sheet,rows=workbook_stream(serial,lambda s:s.lower().startswith("scopus sources"))
 indexed,nserial=source_index(rows,works)
 del serial
 print("SERIAL:",sheet,"rows:",nserial,"matched ISSNs:",len(indexed),flush=True)
 try:
  bookblob=download(urls["books"])
 except Exception as e:
  raise RuntimeError("Gagal mengakses daftar buku Scopus resmi: "+str(e)) from e
 booksheet,rows=workbook_stream(bookblob,lambda s:"book list" in s.lower())
 isbn_idx,title_idx,nbooks=book_index(rows,works)
 del bookblob
 print("BUKU:",booksheet,"rows:",nbooks,"matched ISBN:",len(isbn_idx),"matched titles:",len(title_idx),flush=True)
 counts=Counter();by_author=defaultdict(Counter)
 for work in works:
  doc_eid=work.get("scopus_eid")
  work["hasil_jurnal_seri"]=status_serial(work,indexed)
  work["hasil_buku"]=status_book(work,isbn_idx,title_idx)
  verified=bool(doc_eid and re.fullmatch(r"2-s2\.0-\d{7,}",doc_eid))
  if verified:
   state="dokumen_scopus_ber_eid"
  elif work["hasil_buku"] and work["hasil_buku"]["status"]=="buku_tercantum_di_daftar_scopus":
   state="sumber_buku_scopus_cocok_belum_bukti_dokumen"
  elif work["hasil_jurnal_seri"] and work["hasil_jurnal_seri"]["status"]=="jurnal_atau_seri_ada_di_daftar_scopus":
   state="sumber_jurnal_scopus_cocok_belum_bukti_dokumen"
  elif work["hasil_jurnal_seri"] or work["hasil_buku"]:
   state="perlu_review"
  else:
   state="belum_terverifikasi_bukan_berarti_tidak_terindeks"
  work["status_pemeriksaan_scopus"]=state
  counts[state]+=1
  for user in work.get("dosen",[]):by_author[user][state]+=1
 report.update({
  "sumber_serial_sheet":sheet,"jumlah_sumber_serial_diperiksa":nserial,
  "sumber_buku_sheet":booksheet,"jumlah_judul_buku_diperiksa":nbooks,
  "jumlah_kandidat_dengan_issn":sum(bool(w["issn"]) for w in works),
  "jumlah_kandidat_dengan_isbn":sum(bool(w["isbn"]) for w in works),
  "rekap_status":dict(counts),
  "rekap_per_dosen":{k:dict(v) for k,v in by_author.items()},
  "peringatan":"Data indeksasi SUMBER, bukan jumlah ARTIKEL terindeks Scopus; kuartil Q1-Q4 belum dapat ditentukan dari daftar ini."
 })
 OUTPUT.parent.mkdir(parents=True,exist_ok=True)
 OUTPUT.write_text(json.dumps({**report,"publikasi":works},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 SUMMARY.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("HASIL",json.dumps({k:v for k,v in report.items() if k in
 ["kandidat","jumlah_kandidat_dengan_issn","jumlah_kandidat_dengan_isbn","rekap_status","jumlah_sumber_serial_diperiksa","jumlah_judul_buku_diperiksa"]},ensure_ascii=False),flush=True)
if __name__=="__main__":
 try:main()
 except Exception as e:
  print("GAGAL",type(e).__name__,str(e)[:300],file=sys.stderr)
  sys.exit(1)
