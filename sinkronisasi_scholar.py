#!/usr/bin/env python3
"""Snapshot SerpApi->Google Sheets->Apps Script, tanpa mengubah data GARUDA."""
import json,os,re,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlparse
OUT=Path("hasil/publikasi_scholar.json")
ENDPOINT=os.getenv("SCHOLAR_WEBAPP_URL") or "https://script.google.com/macros/s/AKfycbyZzldxXqRzIW0SKqDcIZLiz3GpIiY2uzAj8IPVRJau-6nM_cK7-OI1xoKA_HFWfm7Q/exec"
SLUGS=("siddik","dedi","rakhmat","aidil","ika","puji")
def num(x):
    try:
        if x is None or x=="" or isinstance(x,bool): return None
        f=float(x)
        return int(f) if f.is_integer() and 0<=f<=1e10 else None
    except (TypeError,ValueError,OverflowError): return None
def url(x):
    if not isinstance(x,str): return ""
    u=urlparse(x)
    return x if u.scheme=="https" and u.hostname else ""
def parse(p):
    slug=str(p.get("slug") or "").strip()
    if slug not in SLUGS: return None
    scholar=p.get("scholar") or {}; metrics=scholar.get("metrics") or {}
    used=set(); papers=[]
    for a in scholar.get("articles") or []:
        if not isinstance(a,dict): continue
        title=str(a.get("title") or "").strip(); y=num(a.get("year"))
        if not title or y is None or not 1900<=y<=2100: continue
        key=(re.sub(r"\W+"," ",title.casefold()).strip(),y)
        if key in used: continue
        used.add(key)
        papers.append({"judul":title,"tahun":y,"jurnal":str(a.get("publication") or ""),"penulis":str(a.get("authors") or ""),"url":url(a.get("url")),"sitasi":num(a.get("citations"))})
    graph={}
    for g in scholar.get("graph") or []:
        if not isinstance(g,dict): continue
        y=num(g.get("year")); v=num(g.get("citations"))
        if y is not None and 1900<=y<=2100 and v is not None: graph[str(y)]=v
    sc=p.get("scopus") or {}; sm=sc.get("metrics") or {}
    scopus=None
    if any(num(sm.get(k)) is not None for k in ("documents","citations","hIndex")):
        scopus={"dokumen":num(sm.get("documents")),"sitasi":num(sm.get("citations")),"h_index":num(sm.get("hIndex")),"sumber":str(sc.get("source") or "Scopus"),"diperbarui":str(sc.get("updated") or "")}
    links=p.get("links") or {}
    return {"slug":slug,"nama":str(p.get("name") or ""),"scholar_url":url(links.get("scholar")),"scopus_url":url(links.get("scopus")),"metrik_scholar":{"sitasi":num(metrics.get("citations")),"h_index":num(metrics.get("hIndex")),"i10_index":num(metrics.get("i10Index"))},"artikel_scholar":papers,"sitasi_tahunan":graph,"scholar_diperbarui":str(scholar.get("updated") or ""),"scholar_status":str(scholar.get("status") or ""),"scopus":scopus}
def main():
    u=urlparse(ENDPOINT)
    if u.scheme!="https" or u.hostname!="script.google.com" or not u.path.endswith("/exec"):
        raise RuntimeError("URL Apps Script tidak sah")
    data=None
    failures=[]
    for view in ("publikasi","portal"):
        try:
            req=Request(ENDPOINT+"?view="+view,headers={"User-Agent":"SainsData-Scholar/1.0","Accept":"application/json"})
            with urlopen(req,timeout=35) as resp: raw=resp.read(3000001)
            if len(raw)>3000000: raise RuntimeError("Respons terlalu besar")
            candidate=json.loads(raw.decode("utf-8-sig"))
            if isinstance(candidate,dict) and not candidate.get("error") and isinstance(candidate.get("profiles"),list):
                data=candidate
                print("Endpoint Google berhasil: view="+view)
                break
            if isinstance(candidate,dict):
                failures.append(view+": "+str(candidate.get("error") or ("fields="+",".join(candidate.keys())))[:240])
            else: failures.append(view+": bukan objek JSON")
        except Exception as exc: failures.append(view+": "+str(exc)[:180])
    if data is None:
        single=[]
        for slug in SLUGS:
            try:
                req=Request(ENDPOINT+"?slug="+slug,headers={"User-Agent":"SainsData-Scholar/1.0","Accept":"application/json"})
                with urlopen(req,timeout=25) as resp: raw=resp.read(3000001)
                if len(raw)>3000000: raise RuntimeError("Respons terlalu besar")
                author=json.loads(raw.decode("utf-8-sig"))
                if not isinstance(author,dict) or author.get("error"):
                    failures.append(slug+": "+str(author.get("error") if isinstance(author,dict) else "JSON salah")[:100])
                    continue
                if isinstance(author.get("scholar"),dict):
                    author.setdefault("slug",slug)
                    single.append(author)
                    continue
                scholar_metrics=author.get("metrics") or {}
                scholarly_articles=author.get("articles") or []
                if not scholar_metrics and not scholarly_articles:
                    failures.append(slug+": tidak ada metrics/articles")
                    continue
                single.append({"slug":slug,"name":author.get("name") or slug,"links":{"scholar":author.get("scholarUrl") or author.get("scholar_url") or ""},"scholar":{"metrics":scholar_metrics,"updated":author.get("updated") or "","status":author.get("status") or "","graph":author.get("graph") or [],"articles":scholarly_articles}})
            except Exception as exc:
                failures.append(slug+": "+str(exc)[:100])
        if single:
            data={"profiles":single}
            print("Endpoint Google berhasil: slug per dosen,",len(single),"profil")
        else: raise RuntimeError("Endpoint Apps Script belum siap; "+"; ".join(failures))
    rows=[r for p in data["profiles"] if isinstance(p,dict) if (r:=parse(p))]
    if not any(p["artikel_scholar"] for p in rows): raise RuntimeError("Artikel Scholar kosong: snapshot sebelumnya dipertahankan")
    old={}
    if OUT.exists():
        try: old={x["slug"]:x for x in json.loads(OUT.read_text(encoding="utf8")).get("dosen",[]) if x.get("slug") in SLUGS}
        except (OSError,ValueError,KeyError,TypeError): pass
    for p in rows: old[p["slug"]]=p
    people=[old[k] for k in SLUGS if k in old]
    payload={"versi":2,"diperbarui_utc":datetime.now(timezone.utc).isoformat(),"sumber":"Google Scholar via SerpApi, Sheets, Apps Script","cakupan_dosen":len(people),"cakupan_lengkap":len(people)==len(SLUGS) and all(x["artikel_scholar"] for x in people),"catatan":"Artikel terdata dari integrasi Scholar, bukan total publikasi profil; sitasi tahunan bukan publikasi tahunan.","dosen":people}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("Sinkronisasi Scholar:",len(people),"profil,",sum(len(p["artikel_scholar"]) for p in people),"artikel terdata")
if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("Gagal: tidak mengubah snapshot",exc,file=sys.stderr)
        sys.exit(1)
