#!/usr/bin/env python3
"""Diagnostic of Elsevier's official public Scopus title lists (no API key)."""
import io,json,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

SOURCES={
 "serial_scopus_oct_2026":"https://downloads.ctfassets.net/o78em1y1w4i4/7xtaTxNiNcWRTeZkV86eNy/a88a2798510dc7f7888e80dc03ec0779/ext_list_Oct_2026.xlsx",
 "book_scopus":"https://downloads.ctfassets.net/o78em1y1w4i4/2uPDv7HcQRnPoxj5xyGhBS/62cc5084eb5566e942271f09e37ccf80/Scopus_book_list_Q2.xlsx",
}
NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships","p":"http://schemas.openxmlformats.org/package/2006/relationships"}
OUT=Path("hasil/diagnostik_sumber_resmi_scopus.json")

def fetch(uri):
 req=Request(uri,headers={"User-Agent":"SainsData-UINSU-Scopus-Source-Checker/1.0","Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"})
 with urlopen(req,timeout=70) as resp:
  # An Elsevier content-asset link should not redirect to unrelated sites.
  hostname=urlparse(resp.geturl()).hostname
  if hostname not in {"downloads.ctfassets.net","assets.ctfassets.net"}:
   raise RuntimeError("Host unduhan tidak dipercaya: "+str(hostname))
  body=resp.read(50000001)
  if len(body)>50000000:raise RuntimeError("XLSX melebihi batas 50MB")
 return body

def cell_text(c,strings):
 t=c.get("t");v=c.find("m:v",NS)
 if t=="inlineStr":return "".join(node.text or "" for node in c.findall(".//m:t",NS))
 if v is None:return ""
 raw=v.text or ""
 if t=="s" and raw.isdigit():
  idx=int(raw)
  return strings[idx] if idx<len(strings) else ""
 return raw

def inspect_xlsx(body):
 z=zipfile.ZipFile(io.BytesIO(body))
 if z.testzip():raise ValueError("Arsip XLSX rusak")
 w=ET.fromstring(z.read("xl/workbook.xml"))
 rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
 link={i.get("Id"):i.get("Target") for i in rel}
 strings=[]
 if "xl/sharedStrings.xml" in z.namelist():
  for _,el in ET.iterparse(z.open("xl/sharedStrings.xml"),events=("end",)):
   if el.tag.endswith("}si"):
    strings.append("".join(t.text or "" for t in el.findall(".//m:t",NS)));el.clear()
 tabs=[]
 for sh in w.findall(".//m:sheets/m:sheet",NS):
  name=sh.get("name");target=link.get(sh.get("{"+NS["r"]+"}id"),"")
  p=target.lstrip("/") if target.startswith("/") else ("xl/"+target.lstrip("/"))
  if p.startswith("xl/xl/"):p=p[3:]
  if p not in z.namelist():
   tabs.append({"sheet":name,"error":"sheet_path_not_found"});continue
  headers=[]
  with z.open(p) as f:
   for _,e in ET.iterparse(f,events=("end",)):
    if e.tag.endswith("}row"):
     vals=[cell_text(c,strings) for c in e.findall("m:c",NS)]
     if any(v.strip() for v in vals):headers.append(vals[:25])
     e.clear()
     if len(headers)>=10:break
  tabs.append({"sheet":name,"top_rows":headers})
 return {"bytes":len(body),"sheets":tabs}

def main():
 results={}
 for key,url in SOURCES.items():
  try:
   d=inspect_xlsx(fetch(url))
   results[key]={"download_ok":True,"url":url,**d}
  except Exception as e:
   results[key]={"download_ok":False,"url":url,"error_type":type(e).__name__,"error":str(e)[:250]}
  print(key,results[key]["download_ok"],results[key].get("bytes"),results[key].get("error"),flush=True)
  for sheet in results[key].get("sheets",[]):print("SHEET",sheet["sheet"],json.dumps(sheet.get("top_rows",[])[:3],ensure_ascii=False)[:800],flush=True)
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps({"diperiksa_utc":datetime.now(timezone.utc).isoformat(),"hasil":results},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
if __name__=="__main__":main()
